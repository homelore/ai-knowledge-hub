"""拉取日志表模型。"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from models.database import Base


class FetchLog(Base):
    __tablename__ = "fetch_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fetch_week = Column(String(20), nullable=False)         # "2026-W34"
    total_fetched = Column(Integer, default=0)
    new_count = Column(Integer, default=0)
    updated_count = Column(Integer, default=0)
    status = Column(String(20), default="running")          # running / success / failed
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
