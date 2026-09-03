"""FastAPI 依赖注入 — 数据库会话、分页参数。"""

from typing import Generator, Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session

from models.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """提供数据库会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def pagination(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """分页参数依赖。"""
    return {"page": page, "page_size": page_size}
