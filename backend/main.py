"""FastAPI 入口 — 启动服务、注册路由、初始化数据库。"""

import sys
import logging
from pathlib import Path

# 确保 backend 目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import API_HOST, API_PORT, CORS_ORIGINS, SCHEDULER_ENABLED
from models import init_db

# ── 日志配置 ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai-hub")

# ── FastAPI 应用 ──────────────────────────────────────
app = FastAPI(
    title="AI Knowledge Hub API",
    description="AI 知识网页后端 — 科普文章 + GitHub 每周动态",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 启动事件 ──────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("初始化数据库...")
    init_db()

    # 预填充主题数据
    from scripts.seed_data import seed_topics
    seed_topics()

    # 同步 Markdown 文章到数据库
    from services.article_service import sync_articles
    from models.database import get_db_session
    with get_db_session() as session:
        sync_articles(session)

    # 启动定时调度器
    if SCHEDULER_ENABLED:
        from agent.scheduler import start_scheduler
        start_scheduler()
        logger.info("APScheduler 已启动")

    logger.info("AI Knowledge Hub 后端启动完成")


@app.on_event("shutdown")
async def shutdown():
    if SCHEDULER_ENABLED:
        from agent.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("APScheduler 已停止")


# ── 注册路由 ──────────────────────────────────────────
from api.routes import repos, releases, topics, articles, stats, agent  # noqa: E402

app.include_router(repos.router,        prefix="/api/repos",     tags=["repos"])
app.include_router(releases.router,     prefix="/api/releases",  tags=["releases"])
app.include_router(topics.router,       prefix="/api/topics",    tags=["topics"])
app.include_router(articles.router,     prefix="/api/articles",  tags=["articles"])
app.include_router(stats.router,        prefix="/api/stats",     tags=["stats"])
app.include_router(agent.router,         prefix="/api/agent",     tags=["agent"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ai-knowledge-hub"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
