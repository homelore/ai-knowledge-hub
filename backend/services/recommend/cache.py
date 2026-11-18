"""推荐结果缓存 — 相同画像 + 相同排除集在 TTL 内直接复用。

LLM 调用是最贵的一环，学生反复点"换一批"时命中缓存可以显著降本提速。
键里带上 excluded_ids，保证"换一批"不会拿到上一批结果。
"""

import hashlib
import json
import threading
import time
from typing import Optional

DEFAULT_TTL_SECONDS = 600
DEFAULT_MAX_ENTRIES = 256


class ResultCache:
    """带 TTL 的线程安全 LRU 缓存。"""

    def __init__(self, ttl: int = DEFAULT_TTL_SECONDS,
                 max_entries: int = DEFAULT_MAX_ENTRIES):
        self.ttl = ttl
        self.max_entries = max_entries
        self._store: dict[str, tuple[float, dict]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def make_key(profile: dict, excluded_ids: set[int], limit: int,
                 engine_tag: str) -> str:
        raw = json.dumps(
            {
                "profile": profile,
                "excluded": sorted(int(i) for i in excluded_ids),
                "limit": limit,
                "engine": engine_tag,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at < time.time():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: dict) -> None:
        with self._lock:
            if len(self._store) >= self.max_entries:
                # 简单淘汰：先清过期，再删最早写入的一条
                now = time.time()
                expired = [k for k, (exp, _) in self._store.items() if exp < now]
                for k in expired:
                    self._store.pop(k, None)
                if len(self._store) >= self.max_entries:
                    oldest = min(self._store.items(), key=lambda kv: kv[1][0])[0]
                    self._store.pop(oldest, None)
            self._store[key] = (time.time() + self.ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


_cache = ResultCache()


def get_cache() -> ResultCache:
    return _cache
