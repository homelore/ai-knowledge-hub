"""仓库相关 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_db, pagination
from services import repo_service

router = APIRouter()


def _format_repo(repo):
    """将 Repo ORM 对象转为前端友好的字典，topics 提取为字符串数组。"""
    topic_names = []
    # repo.topics 是 RepoTopic 列表，每个有 .topic → Topic
    for rt in getattr(repo, "topics", []):
        if rt.topic:
            topic_names.append(rt.topic.name)

    return {
        "id": repo.id,
        "github_id": repo.github_id,
        "full_name": repo.full_name,
        "name": repo.name,
        "description": repo.description,
        "url": repo.url,
        "stars": repo.stars,
        "forks": repo.forks,
        "language": repo.language,
        "license": repo.license,
        "weekly_star_gain": repo.weekly_star_gain or 0,
        "topics": topic_names,
        "github_updated_at": repo.github_updated_at.isoformat() if repo.github_updated_at else None,
    }


@router.get("")
def list_repos(
    topic: str | None = Query(None, description="主题筛选"),
    language: str | None = Query(None, description="编程语言筛选"),
    sort: str = Query("stars", description="排序: stars / weekly_star_gain / updated_at"),
    db: Session = Depends(get_db),
    page: dict = Depends(pagination),
):
    """仓库列表（分页+筛选+排序）。"""
    # 前端可能传 weekly_gain / updated，做映射
    sort_map = {"weekly_gain": "weekly_star_gain", "updated": "updated_at"}
    sort_key = sort_map.get(sort, sort)

    items, total = repo_service.get_repos(
        db,
        page=page["page"],
        page_size=page["page_size"],
        topic=topic,
        language=language,
        sort=sort_key,
    )
    return {
        "items": [_format_repo(r) for r in items],
        "total": total,
        "page": page["page"],
        "page_size": page["page_size"],
        "total_pages": (total + page["page_size"] - 1) // page["page_size"] if total else 0,
    }


@router.get("/languages")
def list_languages(db: Session = Depends(get_db)):
    """获取所有可用编程语言（筛选器用）。"""
    return repo_service.get_languages(db)


@router.get("/hot")
def hot_repos(db: Session = Depends(get_db)):
    """本周热门仓库（按 weekly_star_gain 降序）。"""
    repos = repo_service.get_weekly_hot_repos(db, limit=6)
    return [_format_repo(r) for r in repos]


@router.get("/{repo_id}")
def get_repo(repo_id: int, db: Session = Depends(get_db)):
    """仓库详情。"""
    repo = repo_service.get_repo_by_id(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    data = _format_repo(repo)
    # 附加最近 releases
    releases = repo_service.get_releases_by_repo(db, repo_id, limit=5)
    data["releases"] = [_format_release(r) for r in releases]
    return data


def _format_release(r):
    return {
        "id": r.id,
        "repo_id": r.repo_id,
        "tag_name": r.tag_name,
        "release_name": r.release_name,
        "body": r.body,
        "url": r.url,
        "is_prerelease": r.is_prerelease,
        "published_at": r.published_at.isoformat() if r.published_at else None,
    }


@router.get("/{repo_id}/releases")
def repo_releases(repo_id: int, db: Session = Depends(get_db)):
    """仓库的 Release 列表。"""
    releases = repo_service.get_releases_by_repo(db, repo_id, limit=5)
    return [_format_release(r) for r in releases]


@router.get("/{repo_id}/star-history")
def star_history(
    repo_id: int,
    weeks: int = Query(12, ge=1, le=52),
    db: Session = Depends(get_db),
):
    """仓库 Star 趋势历史数据。"""
    history = repo_service.get_star_history(db, repo_id, weeks=weeks)
    return [{"week": w, "stars": s} for w, s in history]
