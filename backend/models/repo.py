"""仓库表模型。"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from models.database import Base


class Repo(Base):
    __tablename__ = "repos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(Text)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    language = Column(String(100))
    license = Column(String(100))
    weekly_star_gain = Column(Integer, default=0)
    github_updated_at = Column(DateTime)
    # ── M1 新增：GitHub 响应中已有但此前未取的字段（零额外请求）──
    pushed_at = Column(DateTime)          # 最后一次代码推送时间
    open_issues = Column(Integer, default=0)   # 未关闭 issue 数
    size = Column(Integer, default=0)          # 仓库体积（KB）
    github_topics = Column(Text)               # 原始 topics，JSON 数组字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    releases = relationship("Release", back_populates="repo", cascade="all, delete-orphan")
    star_history = relationship("RepoStarHistory", back_populates="repo", cascade="all, delete-orphan")
    topics = relationship("RepoTopic", back_populates="repo", cascade="all, delete-orphan")
    meta = relationship(
        "RepoMeta", back_populates="repo", uselist=False, cascade="all, delete-orphan"
    )
