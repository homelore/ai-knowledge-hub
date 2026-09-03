"""SQLAlchemy 引擎与会话管理。"""

from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from config import DB_URL, DB_PATH

# 确保数据目录存在
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

# SQLite 性能优化
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _conn_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

Base = declarative_base()


def init_db():
    """创建所有表（幂等操作）。"""
    # 确保所有模型已被导入，Base.metadata 才能注册
    from models import repo, release, topic, fetch_log, repo_star_history, article  # noqa: F401
    Base.metadata.create_all(engine)


@contextmanager
def get_db_session():
    """上下文管理器：自动提交/回滚/关闭。"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
