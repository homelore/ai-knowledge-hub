"""科普文章 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_db, pagination
from services import article_service

router = APIRouter()


def _format_article(a, include_html=False):
    """将 Article ORM 对象转为前端友好的字典。"""
    data = {
        "id": a.id,
        "slug": a.slug,
        "title": a.title,
        "summary": a.summary,
        "difficulty": a.difficulty,
        "read_time": a.read_time,
        "tags": a.tags or [],
        "published": a.published,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
    if include_html:
        data["content"] = article_service.render_article(a)
    return data


@router.get("")
def list_articles(
    topic: str | None = Query(None, description="按标签筛选"),
    difficulty: str | None = Query(None, description="按难度筛选"),
    db: Session = Depends(get_db),
    page: dict = Depends(pagination),
):
    """文章列表。"""
    all_articles = article_service.get_articles(
        db,
        topic=topic,
        difficulty=difficulty,
        limit=100,
    )
    total = len(all_articles)
    offset = (page["page"] - 1) * page["page_size"]
    items = all_articles[offset : offset + page["page_size"]]
    return {
        "items": [_format_article(a) for a in items],
        "total": total,
        "page": page["page"],
        "page_size": page["page_size"],
    }


@router.get("/{slug}")
def get_article(slug: str, db: Session = Depends(get_db)):
    """文章详情（含渲染后的 HTML 正文 + 相关文章）。"""
    article = article_service.get_article_by_slug(db, slug)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    related = article_service.get_related_articles(db, article, limit=3)

    return {
        **_format_article(article, include_html=True),
        "related": [_format_article(a) for a in related],
    }
