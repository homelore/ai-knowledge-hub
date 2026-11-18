"""推荐接口 — 规则版对话式推荐（M2）。

接口一览：
    POST /api/recommend/chat    对话式推荐：回答问题 → 拿到下一问或推荐结果
    POST /api/recommend/action  结果操作：skip（不感兴趣）/ refresh（换一批）
    POST /api/recommend         无状态直接推荐，供评测脚本与调试使用

无 LLM key 也能完整跑通，engine 固定为 rule。
"""

import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_db
from services.recommend.engine import RESULT_SIZE
from services.recommend.llm_orchestrator import elicit_step, recommend as recommend_async
from services.recommend.profile import (
    PREFERENCE_VALUES,
    LEVEL_VALUES,
    UserProfile,
    rule_parse,
)
from services.recommend.store import get, get_or_create

router = APIRouter()
logger = logging.getLogger(__name__)


# ── 请求体 ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: Optional[str] = None
    answers: Optional[dict] = None


class ActionRequest(BaseModel):
    session_id: str
    action: str
    repo_id: Optional[int] = None
    repo_ids: Optional[list[int]] = None


class DirectRequest(BaseModel):
    profile: dict = Field(default_factory=dict)
    limit: int = RESULT_SIZE


class EventRequest(BaseModel):
    session_id: Optional[str] = None
    event: str
    payload: dict = Field(default_factory=dict)


# ── 内部工具 ─────────────────────────────────────────────

def _apply_answers(profile: UserProfile, answered: set[str], answers: dict) -> None:
    """把结构化答案写入画像，并记录已作答的问题。"""
    if answers.get("topics"):
        topics = [t for t in answers["topics"] if isinstance(t, str)]
        if topics:
            profile.topics = topics
            answered.add("topics")

    level = answers.get("level")
    if level in LEVEL_VALUES:
        profile.level = level
        answered.add("level")

    pref = answers.get("preference")
    if pref in PREFERENCE_VALUES:
        profile.preference = pref
        answered.add("preference")

    if isinstance(answers.get("languages"), list):
        profile.languages = [str(x) for x in answers["languages"]]
    if isinstance(answers.get("keywords"), list):
        profile.keywords = [str(x) for x in answers["keywords"]]


def _apply_message(profile: UserProfile, answered: set[str], message: str) -> None:
    """无 LLM 时的自由文本兜底：能解析多少算多少。"""
    parsed = rule_parse(message)
    if parsed.get("topics"):
        profile.topics = parsed["topics"]
        answered.add("topics")
    if parsed.get("level"):
        profile.level = parsed["level"]
        answered.add("level")
    if parsed.get("preference"):
        profile.preference = parsed["preference"]
        answered.add("preference")


async def _result_payload(db: Session, sess, started: float) -> dict:
    """执行推荐并组装响应（LLM 可选，永远返回 5 条合法推荐）。"""
    outcome = await recommend_async(db, sess.profile, sess.excluded_ids())
    results = outcome["recommendations"]
    sess.shown_ids |= {r["repo_id"] for r in results}
    return {
        "session_id": sess.session_id,
        "stage": "result",
        "engine": outcome["engine"],
        **outcome,
        "profile": sess.profile.to_dict(),
        "meta": outcome.get("meta") or {
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }


# ── 接口 ─────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """对话式推荐：一次调用对应一轮对话。"""
    started = time.perf_counter()
    sess = get_or_create(req.session_id)

    if req.answers:
        _apply_answers(sess.profile, sess.answered, req.answers)
    if req.message:
        _apply_message(sess.profile, sess.answered, req.message)

    question, engine_used = await elicit_step(sess.profile, sess.answered)
    if question is not None:
        return {
            "session_id": sess.session_id,
            "stage": "question",
            "engine": engine_used,
            "profile": sess.profile.to_dict(),
            "question": question,
            "recommendations": [],
            "meta": {"elapsed_ms": round((time.perf_counter() - started) * 1000, 2)},
        }

    return await _result_payload(db, sess, started)


@router.post("/action")
async def action(req: ActionRequest, db: Session = Depends(get_db)):
    """结果反馈：skip 标记不感兴趣，refresh 换一批。"""
    started = time.perf_counter()
    sess = get(req.session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    if req.action == "skip":
        if req.repo_id is None:
            raise HTTPException(status_code=400, detail="skip 需要提供 repo_id")
        sess.skipped_ids.add(req.repo_id)
        sess.shown_ids.add(req.repo_id)
    elif req.action == "refresh":
        if req.repo_ids:
            sess.shown_ids |= set(req.repo_ids)
    else:
        raise HTTPException(status_code=400, detail="action 仅支持 skip / refresh")

    return await _result_payload(db, sess, started)


@router.post("")
async def direct(req: DirectRequest, db: Session = Depends(get_db)):
    """无状态推荐：给定画像直接返回结果（评测脚本使用）。"""
    started = time.perf_counter()
    profile = UserProfile.from_dict(req.profile)
    outcome = await recommend_async(db, profile, set(), limit=req.limit)
    return {
        "stage": "result",
        **outcome,
        "profile": profile.to_dict(),
        "meta": outcome.get("meta") or {
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }


@router.post("/event")
def track(req: EventRequest):
    """前端埋点落日志，便于观察完成率与调权效果（不影响主流程）。"""
    logger.info(
        "recommend_event session=%s event=%s payload=%s",
        req.session_id, req.event,
        json.dumps(req.payload, ensure_ascii=False),
    )
    return {"ok": True}

