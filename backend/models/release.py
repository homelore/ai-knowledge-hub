"""发布动态表模型。"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base


class Release(Base):
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repos.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_name = Column(String(100), nullable=False)
    release_name = Column(String(500))
    body = Column(Text)
    url = Column(Text)
    is_prerelease = Column(Boolean, default=False)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    repo = relationship("Repo", back_populates="releases")
