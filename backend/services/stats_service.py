"""统计数据聚合业务逻辑。

提供全局概览统计与各主题下的仓库数量统计，供首页/关于页统计面板使用。
所有函数接收 db: Session 作为第一个参数，返回简单字典或字典列表。
"""

from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.repo import Repo
from models.topic import Topic, RepoTopic
from models.fetch_log import FetchLog
from models.article import Article


def get_summary(db: Session) -> Dict:
    """获取全局统计概览。

    Args:
        db: 数据库会话

    Returns:
        {
            "total_repos": 仓库总数,
            "total_articles": 已发布文章数,
            "total_topics": 主题总数,
            "last_fetch_time": 最近一次拉取完成时间,
            "last_fetch_week": 最近一次拉取的周标识（如 "2026-W34"）,
        }
    """
    # 仓库总数
    total_repos = db.query(func.count(Repo.id)).scalar() or 0

    # 已发布文章数
    total_articles = (
        db.query(func.count(Article.id))
        .filter(Article.published == True)  # noqa: E712
        .scalar()
        or 0
    )

    # 主题总数
    total_topics = db.query(func.count(Topic.id)).scalar() or 0

    # 最近一次拉取日志（按开始时间降序取第一条）
    last_log = (
        db.query(FetchLog)
        .order_by(FetchLog.started_at.desc().nullslast())
        .first()
    )
    # 优先用完成时间，未完成则回退到开始时间
    last_fetch_time = None
    last_fetch_week = None
    weekly_new_repos = 0
    if last_log:
        last_fetch_time = last_log.finished_at or last_log.started_at
        last_fetch_week = last_log.fetch_week
        weekly_new_repos = last_log.new_count or 0

    return {
        "total_repos": total_repos,
        "total_articles": total_articles,
        "total_topics": total_topics,
        "last_fetch_time": last_fetch_time,
        "last_fetch_week": last_fetch_week,
        "weekly_new_repos": weekly_new_repos,
    }


def get_topic_stats(db: Session) -> List[Dict]:
    """统计每个主题下的仓库数量。

    使用左连接（LEFT JOIN），确保没有仓库的主题也会返回（count 为 0）。
    结果按 sort_order 升序，与主题预定义顺序一致。

    Args:
        db: 数据库会话

    Returns:
        [{"name": "llm", "display_name": "大语言模型", "color": "#a78bfa", "count": 12}, ...]
    """
    results = (
        db.query(
            Topic.name,
            Topic.display_name,
            Topic.color,
            Topic.icon,
            Topic.description,
            Topic.sort_order,
            func.count(RepoTopic.repo_id).label("count"),
        )
        .outerjoin(RepoTopic, RepoTopic.topic_id == Topic.id)
        .group_by(Topic.id, Topic.name, Topic.display_name, Topic.color, Topic.icon, Topic.description, Topic.sort_order)
        .order_by(Topic.sort_order.asc(), Topic.name.asc())
        .all()
    )

    return [
        {
            "name": name,
            "display_name": display_name,
            "color": color,
            "icon": icon,
            "description": description,
            "sort_order": sort_order,
            "repo_count": count,
        }
        for name, display_name, color, icon, description, sort_order, count in results
    ]
