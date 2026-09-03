"""主题表 + 仓库主题关联表模型。"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100))
    description = Column(Text)
    color = Column(String(20))
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)

    # 关系
    repo_topics = relationship("RepoTopic", back_populates="topic", cascade="all, delete-orphan")


class RepoTopic(Base):
    """仓库-主题 多对多关联表。"""
    __tablename__ = "repo_topics"

    repo_id = Column(Integer, ForeignKey("repos.id", ondelete="CASCADE"), primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)

    # 关系
    repo = relationship("Repo", back_populates="topics")
    topic = relationship("Topic", back_populates="repo_topics")
