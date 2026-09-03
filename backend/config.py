"""应用配置 — 从环境变量读取，带合理默认值。"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── 路径 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # 项目根目录
BACKEND_DIR = BASE_DIR / "backend"
CONTENT_DIR = BASE_DIR / "content"                          # Markdown 文章目录
ARTICLES_DIR = CONTENT_DIR / "articles"
DB_PATH = BACKEND_DIR / "data" / "ai_hub.db"
DB_URL = f"sqlite:///{DB_PATH}"

# ── GitHub ─────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"

# ── Agent 拉取策略 ────────────────────────────────────
# 预定义的 AI 主题（GitHub topic 关键词）
FETCH_TOPICS = [
    {"name": "llm",          "display_name": "大语言模型",   "color": "#a78bfa", "icon": "🧠", "description": "从 Transformer 到 GPT，探索语言模型的演进与应用"},
    {"name": "rag",           "display_name": "检索增强生成",   "color": "#60a5fa", "icon": "🔍", "description": "让大模型接入外部知识，回答更精准更可靠"},
    {"name": "agent",        "display_name": "AI 智能体",     "color": "#34d399", "icon": "🤖", "description": "能自主规划、调用工具的 AI Agent 框架与实践"},
    {"name": "transformer",  "display_name": "Transformer",  "color": "#f472b6", "icon": "⚡", "description": "Attention is All You Need — 现代 AI 的核心架构"},
    {"name": "diffusion",    "display_name": "扩散模型",      "color": "#fbbf24", "icon": "🎨", "description": "从噪声中生成图像与视频的生成式 AI 技术"},
    {"name": "mlops",        "display_name": "MLOps",        "color": "#c084fc", "icon": "⚙️", "description": "机器学习模型的部署、监控与运维最佳实践"},
]

MIN_STARS = 500                # star 最低阈值
MAX_REPOS_PER_TOPIC = 30       # 每个主题最多拉取仓库数
MAX_RELEASES_PER_REPO = 5      # 每个仓库最多拉取 Release 数
TOP_REPO_RELEASE_COUNT = 50    # 对前 N 个仓库拉取 Release

# ── 定时任务 ──────────────────────────────────────────
SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
# 每周一 09:00 (Asia/Shanghai)
CRON_DAY_OF_WEEK = "mon"
CRON_HOUR = 9
CRON_MINUTE = 0

# ── 服务 ──────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
