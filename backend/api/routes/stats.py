"""统计 API 路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from api.deps import get_db
from services import stats_service
from models.fetch_log import FetchLog

router = APIRouter()


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """统计摘要（总数、最近拉取时间）。"""
    return stats_service.get_summary(db)


@router.get("/topics")
def topic_stats(db: Session = Depends(get_db)):
    """各主题下的仓库数量。"""
    return stats_service.get_topic_stats(db)


@router.get("/last-fetch")
def last_fetch(db: Session = Depends(get_db)):
    """最近一次拉取日志。"""
    log = (
        db.query(FetchLog)
        .order_by(desc(FetchLog.started_at))
        .first()
    )
    if not log:
        return None
    return {
        "id": log.id,
        "fetch_week": log.fetch_week,
        "total_fetched": log.total_fetched,
        "new_count": log.new_count,
        "updated_count": log.updated_count,
        "status": log.status,
        "error_message": log.error_message,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "finished_at": log.finished_at.isoformat() if log.finished_at else None,
    }
