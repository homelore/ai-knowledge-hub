"""火山方舟 Ark 传输层：一次性薄封装，不做任何 provider 抽象。

只负责四件事：拼 payload、发请求、分类失败、把响应拆成纯文本 + usage。
不解析 JSON、不做业务校验、不抛异常——把确定性的事留给上层。

关键约定：
- payload 里显式带 thinking.type（默认 disabled），否则混合推理模型会先吐
  reasoning token，首字延迟和费用都会明显变差。
- 全部非流式：澄清应答极短、精排结果必须收全才能校验，流式没有收益。
- model 字段走 ARK_ENDPOINT_ID → ARK_MODEL 回落链，由 LLMConfig.model_ref 提供。
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from services.llm.config import LLMConfig, get_config
from services.llm.guard import LLMGuard, get_guard

logger = logging.getLogger(__name__)

_CHAT_PATH = "/chat/completions"

# 内容审核相关关键词：命中后不重试（重试仍会被拦），直接降级
_MODERATION_KEYS = ("sensitive", "contentfilter", "content_filter", "moderation", "risk", "policy")
# 欠费/额度类关键词：不可重试，且熔断冷却更久。
# 注意不要把 "exceeded" 单独放进来：RateLimitExceeded 属于限流而非欠费。
_QUOTA_KEYS = ("quota", "arrear", "overdue", "balance", "insufficient")


@dataclass
class LLMResult:
    """传输层结果。ok=False 时 data 为 None，上层据此降级。"""

    ok: bool
    data: dict | None = None
    raw_text: str = ""
    usage: dict = field(default_factory=dict)
    latency_ms: int = 0
    error_kind: Optional[str] = None
    status_code: Optional[int] = None
    detail: str = ""


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _fail(kind: str, started: float, *, status: Optional[int] = None, detail: str = "") -> LLMResult:
    return LLMResult(
        ok=False,
        latency_ms=_elapsed_ms(started),
        error_kind=kind,
        status_code=status,
        detail=detail,
    )


def build_payload(
    cfg: LLMConfig,
    messages: list[dict],
    *,
    json_mode: bool = True,
    max_tokens: int = 800,
    temperature: Optional[float] = None,
) -> dict:
    """构造请求体。测试可直接断言这里的字段。"""
    payload: dict = {
        "model": cfg.model_ref,
        "messages": messages,
        "stream": False,  # 全非流式
        "temperature": cfg.temperature if temperature is None else temperature,
        "max_tokens": max_tokens,
        # 显式关闭思考：不加这一行，seed-1.6 系列可能默认先输出推理过程
        "thinking": {"type": cfg.thinking},
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


def _response_json(resp: httpx.Response) -> dict | None:
    try:
        data = resp.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _error_blob(data: dict | None) -> str:
    if not data:
        return ""
    err = data.get("error")
    if isinstance(err, dict):
        return f"{err.get('code', '')} {err.get('message', '')}".strip().lower()
    if isinstance(err, str):
        return err.lower()
    return str(data.get("message", "")).lower()


def classify_status(status_code: int, data: dict | None) -> str:
    """把 HTTP 状态 + 错误体映射成有限的错误类型。"""
    blob = _error_blob(data)
    if status_code == 429:
        return "quota" if any(k in blob for k in _QUOTA_KEYS) else "rate_limit"
    if status_code in (401, 403):
        return "quota" if any(k in blob for k in _QUOTA_KEYS) else "auth"
    if status_code == 400:
        return "moderation" if any(k in blob for k in _MODERATION_KEYS) else "invalid_request"
    if status_code >= 500:
        return "server"
    return "http_error"


def _extract_usage(data: dict) -> dict:
    usage = data.get("usage") or {}
    details = usage.get("prompt_tokens_details") or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
        "cached_tokens": int(details.get("cached_tokens") or 0),
    }


def _extract_content(data: dict) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):  # 少数情况下 content 是分段数组
        return "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    return str(content or "")


def _retry_delay(resp: httpx.Response, kind: str) -> float | None:
    """返回重试前应等待的秒数；返回 None 表示不值得重试。"""
    if kind == "server":
        return 0.5
    raw = resp.headers.get("Retry-After", "")
    try:
        delay = float(raw)
    except (TypeError, ValueError):
        delay = 0.5
    # 等待太久就不重试了：用户在等结果，降级比等待更快
    return delay if delay <= 2.0 else None


async def call_ark(
    messages: list[dict],
    *,
    json_mode: bool = True,
    max_tokens: int = 800,
    temperature: Optional[float] = None,
    timeout_read: Optional[float] = None,
    cfg: Optional[LLMConfig] = None,
    guard: Optional[LLMGuard] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> LLMResult:
    """发一次 chat/completions 请求。任何失败都返回 ok=False，不抛异常。"""
    cfg = cfg or get_config()
    guard = guard or get_guard()
    started = time.perf_counter()

    if not cfg.is_usable:
        return _fail("disabled", started, detail="配置不完整（开关/密钥/模型标识）")

    decision = guard.before_call()
    if not decision.allowed:
        guard.skip(decision.reason)
        return _fail(decision.reason, started)

    payload = build_payload(
        cfg, messages, json_mode=json_mode, max_tokens=max_tokens, temperature=temperature
    )
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    url = f"{cfg.base_url}{_CHAT_PATH}"
    timeout = httpx.Timeout(
        connect=cfg.timeout_connect,
        read=timeout_read or cfg.timeout_read,
        write=10.0,
        pool=5.0,
    )

    own_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=timeout)

    try:
        for attempt in range(max(cfg.max_retries, 0) + 1):
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.TimeoutException:
                guard.after_failure("timeout")
                return _fail("timeout", started)
            except httpx.HTTPError as exc:
                guard.after_failure("network")
                return _fail("network", started, detail=type(exc).__name__)

            if resp.status_code == 200:
                data = _response_json(resp)
                if data is None:
                    guard.after_failure("bad_response")
                    return _fail("bad_response", started, status=200)
                usage = _extract_usage(data)
                guard.after_success(usage)
                content = _extract_content(data)
                if not content.strip():
                    # 模型正常响应但没有正文（被安全策略静默截断等）
                    return LLMResult(
                        ok=False,
                        raw_text="",
                        usage=usage,
                        latency_ms=_elapsed_ms(started),
                        error_kind="empty_content",
                        status_code=200,
                    )
                return LLMResult(
                    ok=True,
                    raw_text=content,
                    usage=usage,
                    latency_ms=_elapsed_ms(started),
                    status_code=200,
                )

            data = _response_json(resp)
            kind = classify_status(resp.status_code, data)
            if kind in {"rate_limit", "server"} and attempt < cfg.max_retries:
                delay = _retry_delay(resp, kind)
                if delay is not None:
                    await asyncio.sleep(delay)
                    continue

            guard.after_failure(kind)
            detail = _error_blob(data)[:200]
            logger.warning("Ark 调用失败 status=%s kind=%s detail=%s", resp.status_code, kind, detail)
            return _fail(kind, started, status=resp.status_code, detail=detail)
    finally:
        if own_client:
            await client.aclose()

    # 理论上不可达
    return _fail("http_error", started)
