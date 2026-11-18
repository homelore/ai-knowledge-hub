"""推荐领域层：把候选仓库交给豆包精排并生成理由，失败则回落模板。

对外只有一个入口 rerank_and_explain，它保证：
1. 任何失败都不抛异常，返回结构完全一致的 RecommendationOutcome；
2. items 里的 repo_id 一定来自传入的候选集（业务校验层拦截幻觉 id）；
3. 理由里出现的任何阿拉伯数字必须在事实块内（业务校验层拦截编造数字）。

约定候选 dict 的字段（缺失会被容错跳过或降级展示）：
    id / repo_id, full_name / name, cn_summary / description,
    language, stars, forks, topics(list[str]),
    days_since_push, difficulty(1~3), runnable(bool)
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from services.llm.ark_client import LLMResult, call_ark
from services.llm.config import LLMConfig, get_config
from services.llm.guard import LLMGuard, get_guard

logger = logging.getLogger(__name__)

_MAX_WHY = 40          # 理由字数上限
_MAX_FIRST_STEP = 30   # 第一步建议字数上限
_MAX_JSON_ATTEMPTS = 2  # 非法 JSON 只重试一次

_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

_DIFFICULTY_LABEL = {
    1: "入门就能跑",
    2: "需要读文档",
    3: "适合读源码",
}

_GOAL_LABEL = {
    "job": "找工作",
    "course_project": "做课程项目",
    "competition": "打比赛",
    "explore": "纯兴趣探索",
}

SYSTEM_PROMPT = """你是给中国大学生推荐 GitHub 项目的助手。

必须遵守：
1. 只能从用户给的候选列表里挑选，repo_id 必须原样取自列表，绝不能虚构。
2. why 与 first_step 中不要出现任何阿拉伯数字（不要写 star 数、天数、年份）。
   要表达热度就用「很受欢迎」「更新很勤」这类描述。
3. why 用中文说明「为什么适合这个学生」，不超过 40 个汉字，要具体、不要空话。
4. first_step 给一个 30 字以内的起手动作（比如先跑哪个示例、先读哪个目录）。
5. 只输出 JSON，不要 Markdown 代码块，不要任何解释文字。

输出格式：
{"items": [{"repo_id": 123, "why": "...", "first_step": "..."}]}"""


@dataclass
class RecommendationOutcome:
    """上层拿到的最终结果，llm 与 rule 两条路径结构完全一致。"""

    engine: str                                  # llm | rule
    items: list[dict] = field(default_factory=list)
    filled: int = 0                              # 由模板补齐的条数
    raw_text: str = ""
    usage: dict = field(default_factory=dict)
    latency_ms: int = 0
    error_kind: Optional[str] = None


# ── 候选与事实块 ──────────────────────────────────────

def _cid(candidate: dict) -> Optional[int]:
    for key in ("id", "repo_id"):
        value = candidate.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _display_name(candidate: dict) -> str:
    return str(
        candidate.get("cn_summary")
        or candidate.get("full_name")
        or candidate.get("name")
        or "该项目"
    )


def _display_desc(candidate: dict) -> str:
    text = str(candidate.get("description") or candidate.get("desc") or "")
    return text[:80]


def _topics_text(candidate: dict) -> str:
    topics = candidate.get("topics") or []
    if isinstance(topics, str):
        topics = [topics]
    return ",".join(str(t) for t in topics[:3])


def _fact_lines(candidates: list[dict]) -> list[str]:
    """紧凑事实块：一行一个候选，比 JSON 省大量 token。"""
    lines: list[str] = []
    for candidate in candidates:
        repo_id = _cid(candidate)
        if repo_id is None:
            continue
        parts = [
            str(repo_id),
            _display_name(candidate),
            str(candidate.get("language") or "未知语言"),
            f"{int(candidate.get('stars') or 0)}star",
            _topics_text(candidate) or "无标签",
            f"{int(candidate.get('days_since_push') or 0)}天前更新",
            _DIFFICULTY_LABEL.get(int(candidate.get("difficulty") or 2), "需要读文档"),
        ]
        desc = _display_desc(candidate)
        if desc:
            parts.append(desc)
        lines.append("|".join(parts))
    return lines


def _number_forms(value) -> set[str]:
    """一个数值的多种写法，模型无论用哪种都必须被判为合法。"""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return set()
    return {
        str(number),
        f"{number:,}",
        f"{number / 1000:.0f}",
        f"{number / 1000:.1f}",
        f"{number / 1000:g}",
    }


def _allowed_numbers(candidates: list[dict]) -> set[str]:
    allowed: set[str] = set()
    for candidate in candidates:
        for key in ("stars", "forks", "days_since_push", "difficulty"):
            allowed |= _number_forms(candidate.get(key))
    return allowed


def _normalize_number(token: str) -> str:
    token = token.replace(",", "").strip()
    if token.endswith(".0"):
        token = token[:-2]
    return token.rstrip(".")


def _numbers_in(text: str) -> set[str]:
    return {_normalize_number(t) for t in _NUM_RE.findall(text or "")}


# ── JSON 解析阶梯 ─────────────────────────────────────

def _strip_fence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    lines = cleaned.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_balanced(text: str) -> Optional[str]:
    """从任意文本里截出第一个括号平衡的 {...}，跳过字符串内的括号。"""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def parse_json_ladder(text: str) -> tuple[Optional[dict], str]:
    """四层解析：直接解析 → 去代码围栏 → 截平衡括号 → 失败。"""
    if not text:
        return None, "empty"
    for label, candidate_text in (
        ("direct", text),
        ("fence", _strip_fence(text)),
        ("balanced", _extract_balanced(text) or ""),
    ):
        if not candidate_text:
            continue
        try:
            data = json.loads(candidate_text)
        except (ValueError, TypeError):
            continue
        if isinstance(data, dict):
            return data, label
    return None, "unparsed"


# ── 业务校验 ─────────────────────────────────────────

def _pick_items(data: dict) -> list:
    items = data.get("items")
    if isinstance(items, list):
        return items
    # 模型偶尔多包一层，例如 {"result": {"items": [...]}}
    for value in data.values():
        if isinstance(value, dict) and isinstance(value.get("items"), list):
            return value["items"]
    return []


def _validate_items(
    data: dict,
    candidates: list[dict],
    allowed_numbers: set[str],
    top_k: int,
) -> list[dict]:
    by_id = {_cid(c): c for c in candidates if _cid(c) is not None}
    result: list[dict] = []
    seen: set[int] = set()

    for raw in _pick_items(data):
        if not isinstance(raw, dict):
            continue
        try:
            repo_id = int(raw.get("repo_id"))
        except (TypeError, ValueError):
            continue
        if repo_id not in by_id or repo_id in seen:
            continue  # 幻觉 id / 重复
        why = str(raw.get("why") or "").strip()
        first_step = str(raw.get("first_step") or "").strip()
        if not why:
            continue
        # 理由里的数字必须来自事实块，否则视为编造
        if not (_numbers_in(why) | _numbers_in(first_step)) <= allowed_numbers:
            logger.info("丢弃含未授权数字的理由：repo_id=%s why=%s", repo_id, why)
            continue
        seen.add(repo_id)
        result.append(
            {
                "repo_id": repo_id,
                "why": why[:_MAX_WHY],
                "first_step": first_step[:_MAX_FIRST_STEP],
            }
        )
        if len(result) >= top_k:
            break
    return result


# ── 模板兜底 ─────────────────────────────────────────

def _template_reason(profile: dict, candidate: dict) -> dict:
    goal = _GOAL_LABEL.get(str(profile.get("goal") or "explore"), "纯兴趣探索")
    difficulty = _DIFFICULTY_LABEL.get(int(candidate.get("difficulty") or 2), "需要读文档")
    language = str(candidate.get("language") or "多种语言")
    stars = int(candidate.get("stars") or 0)
    topics = _topics_text(candidate) or "AI"
    return {
        "repo_id": _cid(candidate),
        "why": f"{language} 的 {topics} 项目，{stars} star，{difficulty}，适合你{goal}。",
        "first_step": "先看 README 的 Quick Start，跑通最小示例。",
    }


def template_recommendations(
    profile: dict,
    candidates: list[dict],
    *,
    top_k: int = 5,
    exclude_ids: Optional[set[int]] = None,
) -> list[dict]:
    """纯模板推荐。无 key、模型不可用、结果不可信时都走这里。"""
    exclude_ids = exclude_ids or set()
    items: list[dict] = []
    for candidate in candidates:
        repo_id = _cid(candidate)
        if repo_id is None or repo_id in exclude_ids:
            continue
        items.append(_template_reason(profile, candidate))
        if len(items) >= top_k:
            break
    return items


# ── 请求与编排 ───────────────────────────────────────

def _build_messages(profile: dict, candidates: list[dict], top_k: int) -> list[dict]:
    profile_text = json.dumps(profile, ensure_ascii=False, sort_keys=True)
    facts = "\n".join(_fact_lines(candidates))
    user_content = (
        f"学生画像：{profile_text}\n\n"
        f"候选仓库（每行：repo_id|名称|语言|热度|标签|更新时间|难度|简介）：\n{facts}\n\n"
        f"请从中选出最合适的 {top_k} 个，按推荐优先级排序。"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


async def _request_json(
    messages: list[dict],
    *,
    cfg: LLMConfig,
    guard: LLMGuard,
    client: Optional[httpx.AsyncClient],
    max_tokens: int,
) -> tuple[Optional[dict], LLMResult]:
    """请求并解析 JSON；解析失败只重试一次，且第二次降低温度。"""
    result: Optional[LLMResult] = None
    current_messages = messages
    for attempt in range(_MAX_JSON_ATTEMPTS):
        temperature = cfg.temperature if attempt == 0 else 0.1
        result = await call_ark(
            current_messages,
            json_mode=True,
            max_tokens=max_tokens,
            temperature=temperature,
            cfg=cfg,
            guard=guard,
            client=client,
        )
        if not result.ok:
            return None, result
        data, how = parse_json_ladder(result.raw_text)
        if data is not None:
            if how != "direct":
                logger.info("JSON 通过 %s 层解析成功", how)
            return data, result
        logger.warning("模型返回非法 JSON（attempt=%s），重试一次", attempt + 1)
        current_messages = messages + [
            {"role": "user", "content": "上一次输出不是合法 JSON。请只输出 JSON 对象，不要任何其他文字。"}
        ]
    if result is None:
        return None, LLMResult(ok=False, error_kind="bad_json")
    result.error_kind = "bad_json"
    result.ok = False
    return None, result


async def rerank_and_explain(
    profile: dict,
    candidates: list[dict],
    *,
    top_k: int = 5,
    cfg: Optional[LLMConfig] = None,
    guard: Optional[LLMGuard] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> RecommendationOutcome:
    """候选精排 + 理由生成。永不抛异常，失败自动回落模板。"""
    started = time.perf_counter()
    cfg = cfg or get_config()
    guard = guard or get_guard()

    if not candidates:
        return RecommendationOutcome(engine="rule", items=[], error_kind="no_candidates",
                                     latency_ms=int((time.perf_counter() - started) * 1000))

    if not cfg.is_usable:
        return RecommendationOutcome(
            engine="rule",
            items=template_recommendations(profile, candidates, top_k=top_k),
            latency_ms=int((time.perf_counter() - started) * 1000),
            error_kind="disabled",
        )

    messages = _build_messages(profile, candidates, top_k)
    data, result = await _request_json(
        messages, cfg=cfg, guard=guard, client=client, max_tokens=800
    )

    if data is None:
        logger.warning("LLM 精排失败（%s），回落模板理由", result.error_kind)
        return RecommendationOutcome(
            engine="rule",
            items=template_recommendations(profile, candidates, top_k=top_k),
            raw_text=result.raw_text,
            usage=result.usage,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error_kind=result.error_kind or "bad_json",
        )

    allowed = _allowed_numbers(candidates)
    items = _validate_items(data, candidates, allowed, top_k)

    # 不足 top_k 时用模板补齐：宁可理由朴素，也不返回缺条的结果
    filled = 0
    if len(items) < top_k:
        used = {item["repo_id"] for item in items}
        for extra in template_recommendations(profile, candidates, top_k=top_k, exclude_ids=used):
            items.append(extra)
            filled += 1
            if len(items) >= top_k:
                break

    engine = "llm" if items and filled < len(items) else "rule"
    error_kind = None
    if engine == "rule":
        error_kind = "validation_empty"
    elif filled:
        error_kind = "partial_fallback"

    return RecommendationOutcome(
        engine=engine,
        items=items,
        filled=filled,
        raw_text=result.raw_text,
        usage=result.usage,
        latency_ms=int((time.perf_counter() - started) * 1000),
        error_kind=error_kind,
    )
