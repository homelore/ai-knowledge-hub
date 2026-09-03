"""主题 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_db, pagination
from models.topic import Topic
from services import repo_service
from services.stats_service import get_topic_stats

router = APIRouter()


@router.get("")
def list_topics(db: Session = Depends(get_db)):
    """所有主题列表（含仓库数量统计）。"""
    return get_topic_stats(db)


@router.get("/{topic_name}")
def get_topic(topic_name: str, db: Session = Depends(get_db)):
    """主题详情（含仓库数量统计）。"""
    topic = db.query(Topic).filter_by(name=topic_name).first()
    if not topic:
        raise HTTPException(status_code=404, detail="主题不存在")

    # 查询该主题下的仓库数量
    from models.topic import RepoTopic
    repo_count = (
        db.query(RepoTopic)
        .filter(RepoTopic.topic_id == topic.id)
        .count()
    )

    return {
        "name": topic.name,
        "display_name": topic.display_name,
        "description": topic.description,
        "color": topic.color,
        "icon": topic.icon,
        "sort_order": topic.sort_order,
        "repo_count": repo_count,
    }


@router.get("/{topic_name}/repos")
def topic_repos(
    topic_name: str,
    db: Session = Depends(get_db),
    page: dict = Depends(pagination),
):
    """主题下的仓库列表。"""
    items, total = repo_service.get_repos(
        db,
        page=page["page"],
        page_size=page["page_size"],
        topic=topic_name,
    )
    from api.routes.repos import _format_repo
    return {
        "items": [_format_repo(r) for r in items],
        "total": total,
        "page": page["page"],
        "page_size": page["page_size"],
    }
