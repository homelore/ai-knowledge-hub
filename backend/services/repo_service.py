"""仓库查询业务逻辑。

提供仓库列表分页筛选、详情、Release 列表、Star 历史、热门仓库、语言列表等查询。
所有函数接收 db: Session 作为第一个参数，返回 SQLAlchemy 对象或简单元组。
"""

from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from models.repo import Repo
from models.release import Release
from models.topic import Topic, RepoTopic
from models.repo_star_history import RepoStarHistory

# 排序字段映射：外部传入的排序标识 → 对应的 Repo 列
_SORT_MAP = {
    "stars": Repo.stars,
    "weekly_star_gain": Repo.weekly_star_gain,
    "updated_at": Repo.updated_at,
}


def get_repos(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    topic: Optional[str] = None,
    language: Optional[str] = None,
    sort: str = "stars",
) -> Tuple[List[Repo], int]:
    """分页查询仓库列表，支持按主题/语言筛选与排序。

    Args:
        db: 数据库会话
        page: 页码，从 1 开始
        page_size: 每页数量
        topic: 主题名称（如 "llm"），为 None 时不筛选
        language: 编程语言（如 "Python"），为 None 时不筛选
        sort: 排序方式，可选 stars / weekly_star_gain / updated_at，默认 stars

    Returns:
        (items, total) —— 当前页仓库列表与符合条件的总数
    """
    query = db.query(Repo)

    # 按主题筛选：经 repo_topics 关联表连接到 topics，匹配主题名
    if topic:
        query = (
            query.join(RepoTopic, RepoTopic.repo_id == Repo.id)
            .join(Topic, Topic.id == RepoTopic.topic_id)
            .filter(Topic.name == topic)
        )

    # 按编程语言筛选
    if language:
        query = query.filter(Repo.language == language)

    # 统计总数（在分页前，包含筛选条件）
    total = query.count()

    # 排序：未识别的排序标识回退到 stars，统一降序
    sort_col = _SORT_MAP.get(sort, Repo.stars)
    query = query.order_by(sort_col.desc())

    # 分页
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return items, total


def get_repo_by_id(db: Session, repo_id: int) -> Optional[Repo]:
    """根据内部 ID 查询单个仓库详情，预加载主题关联与 Release 列表。

    Args:
        db: 数据库会话
        repo_id: 仓库内部主键 id

    Returns:
        Repo 对象（含 topics、releases 关系数据），不存在则返回 None
    """
    return (
        db.query(Repo)
        .options(
            selectinload(Repo.topics),    # 预加载主题关联（RepoTopic 列表）
            selectinload(Repo.releases),  # 预加载 Release 列表
        )
        .filter(Repo.id == repo_id)
        .first()
    )


def get_releases_by_repo(db: Session, repo_id: int, limit: int = 5) -> List[Release]:
    """查询指定仓库的 Release 列表，按发布时间降序。

    Args:
        db: 数据库会话
        repo_id: 仓库内部主键 id
        limit: 最多返回条数，默认 5

    Returns:
        Release 列表（最新在前）
    """
    return (
        db.query(Release)
        .filter(Release.repo_id == repo_id)
        .order_by(Release.published_at.desc().nullslast())
        .limit(limit)
        .all()
    )


def get_star_history(db: Session, repo_id: int, weeks: int = 12) -> List[Tuple[str, int]]:
    """查询指定仓库最近 N 周的 Star 历史，用于趋势图。

    Args:
        db: 数据库会话
        repo_id: 仓库内部主键 id
        weeks: 取最近多少周的记录，默认 12

    Returns:
        [(week, stars), ...] 按时间升序排列（便于折线图从左到右绘制）
    """
    # 先取最近 N 条（降序），再反转为升序，保证不足 N 周时也能完整展示
    latest = (
        db.query(RepoStarHistory)
        .filter(RepoStarHistory.repo_id == repo_id)
        .order_by(RepoStarHistory.recorded_at.desc())
        .limit(weeks)
        .all()
    )
    latest.reverse()
    return [(h.recorded_week, h.stars) for h in latest]


def get_weekly_hot_repos(db: Session, limit: int = 6) -> List[Repo]:
    """获取本周热门仓库，按 weekly_star_gain 降序。

    Args:
        db: 数据库会话
        limit: 返回条数，默认 6（首页热门卡片区）

    Returns:
        Repo 列表（本周 Star 增长最多者在前）
    """
    return (
        db.query(Repo)
        .order_by(Repo.weekly_star_gain.desc())
        .limit(limit)
        .all()
    )


def get_languages(db: Session) -> List[str]:
    """去重获取所有仓库的编程语言列表，用于筛选器。

    Args:
        db: 数据库会话

    Returns:
        去重后的语言名称列表（按字母升序，已排除空值）
    """
    rows = (
        db.query(Repo.language)
        .filter(Repo.language.isnot(None), Repo.language != "")
        .distinct()
        .order_by(Repo.language)
        .all()
    )
    return [row[0] for row in rows]
