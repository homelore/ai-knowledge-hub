"""Star 历史表模型（趋势图数据源）。"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base


class RepoStarHistory(Base):
    __tablename__ = "repo_star_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repos.id", ondelete="CASCADE"), nullable=False, index=True)
    stars = Column(Integer, nullable=False)
    recorded_week = Column(String(20), nullable=False)      # "2026-W34"
    recorded_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    repo = relationship("Repo", back_populates="star_history")
