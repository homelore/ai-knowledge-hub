"""种子数据 — 预填充主题表。"""

import logging
from models.database import get_db_session
from models.topic import Topic
from config import FETCH_TOPICS

logger = logging.getLogger("ai-hub.seed")


def seed_topics():
    """幂等插入预定义主题。"""
    with get_db_session() as session:
        for idx, t in enumerate(FETCH_TOPICS):
            existing = session.query(Topic).filter_by(name=t["name"]).first()
            if existing:
                # 更新所有字段
                existing.display_name = t["display_name"]
                existing.color = t["color"]
                existing.icon = t.get("icon", "")
                existing.description = t.get("description", "")
                existing.sort_order = idx
            else:
                session.add(Topic(
                    name=t["name"],
                    display_name=t["display_name"],
                    color=t["color"],
                    icon=t.get("icon", ""),
                    description=t.get("description", ""),
                    sort_order=idx,
                ))
    logger.info(f"主题数据已预填充 ({len(FETCH_TOPICS)} 个)")


if __name__ == "__main__":
    seed_topics()
