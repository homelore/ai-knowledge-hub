"""Release 动态 API 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from api.deps import get_db, pagination
from models.release import Release
from models.repo import Repo

router = APIRouter()


@router.get("")
def list_releases(
    db: Session = Depends(get_db),
    page: dict = Depends(pagination),
):
    """最新 Release 列表（跨仓库，按发布时间降序）。"""
    offset = (page["page"] - 1) * page["page_size"]
    query = (
        db.query(Release, Repo.full_name, Repo.name.label("repo_name"))
        .join(Repo, Release.repo_id == Repo.id)
        .order_by(desc(Release.published_at).nullslast())
    )
    total = query.count()
    results = query.offset(offset).limit(page["page_size"]).all()

    items = []
    for release, full_name, repo_name in results:
        items.append({
            "id": release.id,
            "repo_id": release.repo_id,
            "repo_full_name": full_name,
            "repo_name": repo_name,
            "tag_name": release.tag_name,
            "release_name": release.release_name,
            "url": release.url,
            "is_prerelease": release.is_prerelease,
            "published_at": release.published_at.isoformat() if release.published_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page["page"],
        "page_size": page["page_size"],
    }
