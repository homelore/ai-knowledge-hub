"""LLM 调用护栏：进程内熔断 + 每日调用/token 配额。

设计取舍：
- 熔断用进程内内存态即可（单人项目、单进程），多 worker 时最坏是每个 worker
  各计一份，可接受；不为此引入 Redis。
- 配额落 SQLite 的 llm_usage 表，按自然日累计。表在首次使用时 lazy 建，
  不改动任何已有表结构。
- 所有 DB 操作失败都只记日志，绝不向上抛异常：护栏坏了也必须能出推荐。
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Optional

from config import DB_PATH

from services.llm.config import LLMConfig, get_config

logger = logging.getLogger(__name__)

# 熔断阈值：连续失败多少次后打开
_FAIL_THRESHOLD = 3
# 普通故障的打开时长（秒）
_OPEN_SECONDS = 60.0
# 鉴权/欠费类故障的打开时长（秒）：这类问题重试无意义，冷却更久
_OPEN_SECONDS_FATAL = 600.0

_FATAL_KINDS = {"auth", "quota"}


def _today() -> str:
    return date.today().isoformat()


@dataclass
class GuardDecision:
    """一次调用前的放行判定。"""

    allowed: bool
    reason: str = "ok"  # ok | circuit_open | daily_calls | daily_tokens


class CircuitBreaker:
    """连续失败计数 + 冷却期熔断，冷却结束后放一个请求试探（半开）。"""

    def __init__(
        self,
        threshold: int = _FAIL_THRESHOLD,
        open_seconds: float = _OPEN_SECONDS,
        open_seconds_fatal: float = _OPEN_SECONDS_FATAL,
    ) -> None:
        self._threshold = threshold
        self._open_seconds = open_seconds
        self._open_seconds_fatal = open_seconds_fatal
        self._failures = 0
        self._opened_at: Optional[float] = None
        self._open_until: float = 0.0
        self._lock = threading.Lock()

    @property
    def is_open(self) -> bool:
        with self._lock:
            return time.monotonic() < self._open_until

    def allow(self) -> bool:
        with self._lock:
            return time.monotonic() >= self._open_until

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None
            self._open_until = 0.0

    def record_failure(self, error_kind: str) -> None:
        with self._lock:
            self._failures += 1
            if self._failures < self._threshold:
                return
            seconds = self._open_seconds_fatal if error_kind in _FATAL_KINDS else self._open_seconds
            self._open_until = time.monotonic() + seconds
            self._opened_at = time.monotonic()
            self._failures = 0
            logger.warning("LLM 熔断打开 %ss（error_kind=%s）", int(seconds), error_kind)

    def reset(self) -> None:
        self.record_success()


class QuotaStore:
    """每日调用数与 token 用量的 SQLite 存储。"""

    _DDL = """
    CREATE TABLE IF NOT EXISTS llm_usage (
        day        TEXT PRIMARY KEY,
        calls      INTEGER NOT NULL DEFAULT 0,
        tokens_in  INTEGER NOT NULL DEFAULT 0,
        tokens_out INTEGER NOT NULL DEFAULT 0
    )
    """

    def __init__(self, db_path=DB_PATH) -> None:
        self._db_path = str(db_path)
        self._ready = False
        self._lock = threading.Lock()

    def _connect(self) -> sqlite3.Connection:
        # 目录不存在时先补上，否则 sqlite 会以 "unable to open database file" 静默失败
        parent = os.path.dirname(self._db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        conn = sqlite3.connect(self._db_path, timeout=5.0)
        conn.execute("PRAGMA busy_timeout=5000")
        if not self._ready:
            conn.execute(self._DDL)
            conn.commit()
            self._ready = True
        return conn

    def snapshot(self, day: Optional[str] = None) -> tuple[int, int]:
        """返回 (当日调用次数, 当日 token 总量)。"""
        day = day or _today()
        with self._lock:
            try:
                conn = self._connect()
                try:
                    row = conn.execute(
                        "SELECT calls, tokens_in + tokens_out FROM llm_usage WHERE day = ?",
                        (day,),
                    ).fetchone()
                finally:
                    conn.close()
            except sqlite3.Error as exc:  # 护栏自身故障不影响主流程
                logger.warning("读取 LLM 配额失败：%s", exc)
                return (0, 0)
        return (int(row[0]), int(row[1])) if row else (0, 0)

    def record(self, tokens_in: int, tokens_out: int, day: Optional[str] = None) -> None:
        day = day or _today()
        with self._lock:
            try:
                conn = self._connect()
                try:
                    conn.execute(
                        """
                        INSERT INTO llm_usage (day, calls, tokens_in, tokens_out)
                        VALUES (?, 1, ?, ?)
                        ON CONFLICT(day) DO UPDATE SET
                            calls      = calls + 1,
                            tokens_in  = tokens_in + excluded.tokens_in,
                            tokens_out = tokens_out + excluded.tokens_out
                        """,
                        (day, max(0, int(tokens_in)), max(0, int(tokens_out))),
                    )
                    conn.commit()
                finally:
                    conn.close()
            except sqlite3.Error as exc:
                logger.warning("记录 LLM 配额失败：%s", exc)


class LLMGuard:
    """把熔断与配额组合成一次「调用前判定 + 调用后记账」。"""

    def __init__(
        self,
        cfg: Optional[LLMConfig] = None,
        store: Optional[QuotaStore] = None,
        breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self.cfg = cfg or get_config()
        self.store = store or QuotaStore()
        self.breaker = breaker or CircuitBreaker()

    def before_call(self) -> GuardDecision:
        if not self.breaker.allow():
            return GuardDecision(False, "circuit_open")

        calls, tokens = self.store.snapshot()
        if self.cfg.daily_call_limit > 0 and calls >= self.cfg.daily_call_limit:
            return GuardDecision(False, "daily_calls")
        if self.cfg.daily_token_limit > 0 and tokens >= self.cfg.daily_token_limit:
            return GuardDecision(False, "daily_tokens")
        return GuardDecision(True)

    def after_success(self, usage: Optional[dict] = None) -> None:
        self.breaker.record_success()
        usage = usage or {}
        tokens_in = int(usage.get("prompt_tokens") or 0)
        tokens_out = int(usage.get("completion_tokens") or 0)
        self.store.record(tokens_in, tokens_out)

    def after_failure(self, error_kind: str) -> None:
        # 配额超限不是服务故障，不应触发熔断
        if error_kind in {"daily_calls", "daily_tokens"}:
            return
        self.breaker.record_failure(error_kind)

    def skip(self, reason: str) -> None:
        """记录一次因护栏原因未发起的调用（不计数、不熔断）。"""
        logger.info("LLM 调用被护栏跳过：%s", reason)


@lru_cache(maxsize=1)
def get_guard() -> LLMGuard:
    return LLMGuard()
