"""M3 编排层 — 澄清 + 精排 + 理由 + 校验 + 降级 + 缓存。

设计原则：LLM 永远是"加分项"而不是"必经路径"。
    1. 规则引擎先产出 5 条满足硬约束的候选（M2 的成果）
    2. LLM 只在候选范围内重排序并改写理由，不允许引入新 repo_id
    3. 任何异常 / 超时 / 非法 JSON / 幻觉 id 都回落规则结果
    4. 接口永远返回 200 + 5 条合法推荐
"""

import json
import logging
import time
from typing import Optional

from sqlalchemy.orm import Session

from config import LLM_ENABLED
from services.llm.ark_client import call_ark
from services.llm.config import LLMConfig, get_config
from services.llm.guard import get_guard
from services.llm.recommend_llm import (
    RecommendationOutcome,
    parse_json_ladder,
    rerank_and_explain,
)
from services.recommend import engine as rule_engine
from services.recommend.cache import get_cache
from services.recommend.profile import UserProfile, next_question

logger = logging.getLogger(__name__)

_DIFFICULTY_INT = {"beginner": 1, "intermediate": 2, "advanced": 3}

_ELICIT_PROMPT = """你在帮中国大学生挑选 GitHub 学习项目。请根据当前画像，把下一个澄清问题改写得自然一点。

必须遵守：
1. 只输出 JSON，不要 Markdown 代码块。
2. 不要改变问题的选项含义与可选值，只改写 text。
3. text 不超过 30 个汉字，口语化，不要出现"画像""字段""参数"等术语。

输出格式：{"text": "..."}"""


def _days_since_push(result: dict) -> int:
    days = result.get("pushed_days")
    return int(days) if days is not None else 999


def _to_llm_candidate(result: dict) -> dict:
    """把规则结果转成 recommend_llm 需要的候选字段。"""
    return {
        "id": result["repo_id"],
        "full_name": result.get("full_name"),
        "description": (result.get("description") or "")[:160],
        "language": result.get("language"),
        "stars": result.get("stars") or 0,
        "forks": result.get("forks") or 0,
        "topics": result.get("topics") or [],
        "days_since_push": _days_since_push(result),
        "difficulty": _DIFFICULTY_INT.get(result.get("difficulty"), 2),
        "runnable": result.get("run_mode") in ("local", "demo"),
    }


async def elicit_step(
    profile: UserProfile,
    answered: set[str],
    *,
    cfg: Optional[LLMConfig] = None,
    client=None,
) -> tuple[Optional[dict], str]:
    """返回下一个澄清问题。

    LLM 可用时只改写问题文案（选项与取值保持不变），失败一律回落固定问题。
    返回 (question, engine)；没有待问问题时返回 (None, engine)。
    """
    base = next_question(profile, answered)
    if base is None:
        return None, "rule"
    if not LLM_ENABLED:
        return base, "rule"

    cfg = cfg or get_config()
    if not cfg.is_usable:
        return base, "rule"

    messages = [
        {"role": "system", "content": _ELICIT_PROMPT},
        {
            "role": "user",
            "content": (
                f"当前画像：{json.dumps(profile.to_dict(), ensure_ascii=False)}\n"
                f"下一问原始文案：{base['text']}\n"
                f"问题 id：{base['id']}，可选项："
                f"{json.dumps([o['value'] for o in base['options']], ensure_ascii=False)}"
            ),
        },
    ]

    try:
        result = await call_ark(
            messages, json_mode=True, max_tokens=120,
            temperature=0.2, cfg=cfg, guard=get_guard(), client=client,
        )
        if not result.ok:
            return base, "rule"
        data, _how = parse_json_ladder(result.raw_text)
        text = str((data or {}).get("text") or "").strip()
        if not text or len(text) > 40:
            return base, "rule"
        return {**base, "text": text}, "llm"
    except Exception as exc:  # noqa: BLE001 - 澄清失败不能影响对话
        logger.warning("elicit_step 降级：%s", exc)
        return base, "rule"


def _merge(
    base_results: list[dict],
    outcome: RecommendationOutcome,
) -> list[dict]:
    """把 LLM 的重排与理由合并回规则结果，严格限定在候选集合内。"""
    by_id = {r["repo_id"]: r for r in base_results}
    merged: list[dict] = []
    seen: set[int] = set()

    for item in outcome.items:
        repo_id = item.get("repo_id")
        if repo_id not in by_id or repo_id in seen:
            # 幻觉 id 或重复：直接丢弃（拦截率 100%）
            logger.info("丢弃非法 repo_id：%s", repo_id)
            continue
        source = dict(by_id[repo_id])
        why = str(item.get("why") or "").strip()
        first_step = str(item.get("first_step") or "").strip()
        if why:
            source["reason"] = why
        if first_step:
            source["first_step"] = first_step
        merged.append(source)
        seen.add(repo_id)

    # LLM 给少了就用规则结果按原顺序补齐，保证永远是 5 条
    for result in base_results:
        if result["repo_id"] in seen:
            continue
        merged.append(result)
        seen.add(result["repo_id"])

    return merged


async def recommend(
    db: Session,
    profile: UserProfile,
    excluded_ids: set[int],
    limit: int = rule_engine.RESULT_SIZE,
    *,
    cfg: Optional[LLMConfig] = None,
    client=None,
    use_cache: bool = True,
) -> dict:
    """执行推荐（LLM 可选），返回与接口同构的结果字典。

    该函数不会向上抛异常：任何 LLM 环节失败都回落到规则结果。
    """
    started = time.perf_counter()
    cache = get_cache()
    cfg = cfg or get_config()
    cache_key = cache.make_key(
        profile.to_dict(), excluded_ids, limit, "llm" if cfg.is_usable else "rule"
    )

    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return {**cached, "cached": True, "meta": {
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                "cache": "hit",
            }}

    # 1. 规则引擎先保证约束与条数
    base_results = rule_engine.recommend(db, profile, excluded_ids, limit=limit)
    engine_used = "rule"
    error_kind: Optional[str] = None
    llm_latency = 0

    # 2. LLM 在候选范围内精排 + 改写理由
    if cfg.is_usable and base_results:
        candidates = [_to_llm_candidate(r) for r in base_results]
        try:
            outcome = await rerank_and_explain(
                profile.to_dict(), candidates,
                top_k=len(candidates), cfg=cfg, client=client,
            )
            llm_latency = outcome.latency_ms
            error_kind = outcome.error_kind
            merged = _merge(base_results, outcome)
            engine_used = outcome.engine
            results = merged[:limit]
        except Exception as exc:  # noqa: BLE001 - 任何异常都不影响主流程
            logger.warning("LLM 精排异常，回落规则结果：%s", exc)
            error_kind = "exception"
            results = base_results
    else:
        results = base_results

    payload = {
        "engine": engine_used,
        "recommendations": results,
        "constraints": rule_engine.check_constraints(results),
        "error_kind": error_kind,
        "llm_latency_ms": llm_latency,
    }

    if use_cache:
        cache.set(cache_key, payload)

    return {
        **payload,
        "cached": False,
        "meta": {
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "cache": "miss",
        },
    }
