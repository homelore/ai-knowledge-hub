"""推荐会话状态 — 进程内保存画像与已展示/已跳过仓库。

单实例部署场景够用；重启会丢会话，属于设计内可接受的降级。
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from services.recommend.profile import UserProfile

SESSION_TTL_SECONDS = 3600


@dataclass
class Session:
    session_id: str
    profile: UserProfile = field(default_factory=UserProfile)
    answered: set[str] = field(default_factory=set)
    shown_ids: set[int] = field(default_factory=set)
    skipped_ids: set[int] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    touched_at: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.touched_at = time.time()

    def excluded_ids(self) -> set[int]:
        return self.shown_ids | self.skipped_ids


_sessions: dict[str, Session] = {}


def _cleanup() -> None:
    now = time.time()
    expired = [
        sid for sid, sess in _sessions.items()
        if now - sess.touched_at > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _sessions.pop(sid, None)


def get_or_create(session_id: Optional[str]) -> Session:
    """获取会话；session_id 为空时新建。"""
    _cleanup()
    if session_id and session_id in _sessions:
        sess = _sessions[session_id]
        sess.touch()
        return sess

    new_id = session_id or f"s{int(time.time() * 1000)}"
    sess = Session(session_id=new_id)
    _sessions[new_id] = sess
    return sess


def get(session_id: str) -> Optional[Session]:
    return _sessions.get(session_id)
