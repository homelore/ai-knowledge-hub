"""文章元数据表模型。"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy import JSON
from models.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(200), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    difficulty = Column(String(30), default="beginner")    # beginner / intermediate / advanced
    read_time = Column(Integer, default=5)
    tags = Column(JSON, default=list)                        # ["llm", "rag"]
    file_path = Column(Text)
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
