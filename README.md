# AI Knowledge Hub

> 一站式 AI 知识平台 — 从科普知识到 GitHub 热门项目，追踪人工智能前沿动态

![Nuxt](https://img.shields.io/badge/Nuxt-4-00DC82?style=flat-square&logo=nuxt.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

## ✨ 项目特性

### 📚 AI 科普知识
- 精选 AI 科普文章，从入门到进阶分层阅读
- Markdown 驱动，支持代码高亮、表格、目录
- 难度标签（beginner / intermediate / advanced）+ 主题标签

### 🔥 GitHub 每周技术动态
- 后端 Agent 每周自动拉取 GitHub 热门仓库
- 6 大 AI 主题：LLM、RAG、Agent、Transformer、扩散模型、MLOps
- 按 star 数排序，实时追踪周增长榜
- 项目 Release 版本动态

### 🎨 暗色渐变设计
- 深蓝灰背景 + 紫蓝绿三色渐变
- 圆角卡片 + 半透明玻璃态效果
- 响应式布局，移动端友好

## 🏗️ 技术栈

### 前端
- **Nuxt 4** (Vue 3) — 元框架，文件路由，SSR 友好
- **Tailwind CSS 3** — 原子化 CSS，暗色渐变主题
- **TypeScript** — 类型安全

### 后端
- **FastAPI** — 异步高性能 Web 框架，自动生成 API 文档
- **SQLAlchemy 2.x** — ORM，支持 SQLite / PostgreSQL 迁移
- **APScheduler** — 定时任务，进程内运行
- **httpx** — HTTP 客户端，内置限流控制与指数退避重试
- **python-markdown + Pygments** — Markdown 渲染 + 代码高亮

### 数据存储
- **SQLite** — 零配置文件型数据库
- **Markdown 文件** — 科普文章源文件，版本管理友好

## 📁 项目结构

```
ai-knowledge-hub/
├── backend/                # FastAPI 后端
│   ├── agent/              # GitHub Agent（定时拉取任务）
│   │   ├── github_client.py # GitHub API 客户端（限流 + 重试）
│   │   ├── fetcher.py      # 拉取主流程
│   │   ├── filter.py       # 数据映射与筛选
│   │   └── scheduler.py     # APScheduler 定时调度
│   ├── api/                # API 路由
│   │   └── routes/         # repos / releases / topics / articles / stats / agent
│   ├── models/             # SQLAlchemy 数据模型（7 张表）
│   ├── services/           # 业务逻辑层
│   ├── scripts/            # 种子数据等脚本
│   ├── config.py           # 环境配置
│   ├── main.py             # FastAPI 入口
│   └── requirements.txt    # Python 依赖
├── frontend/              # Nuxt 4 前端
│   ├── app/
│   │   ├── pages/          # 文件路由（首页、仓库列表、文章详情等）
│   │   ├── components/     # UI 组件
│   │   ├── composables/    # 组合式函数（useApi、useFormat）
│   │   └── assets/css/     # 全局样式
│   ├── nuxt.config.ts      # Nuxt 配置（含 API 代理）
│   └── tailwind.config.js  # Tailwind 主题配置
├── content/
│   └── articles/           # Markdown 科普文章源文件
├── docs/                   # 设计文档
├── .env.example            # 环境变量模板
└── LOCAL_SETUP_GUIDE.md    # 本地运行指南
```

## 🚀 快速开始

### 环境要求

| 工具 | 最低版本 |
|------|----------|
| Node.js | ≥ 22.19.0 |
| Python | ≥ 3.10 |
| Git | 任意版本 |

### 1. 克隆项目

```bash
git clone https://github.com/homelore/ai-knowledge-hub.git
cd ai-knowledge-hub
```

### 2. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env，填入 GITHUB_TOKEN

# 启动服务
python main.py
```

后端启动后访问：http://localhost:8000/docs 查看 API 文档

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后访问：http://localhost:3000

### 4. 触发 GitHub 数据拉取

首次运行数据库为空，需要手动触发一次拉取：

```bash
# 方法 1：Swagger UI
# 浏览器打开 http://localhost:8000/docs
# 找到 POST /api/agent/fetch，点击 "Try it out" → "Execute"

# 方法 2：curl
curl -X POST http://localhost:8000/api/agent/fetch
```

> 拉取约 1~2 分钟，无 Token 也能拉取（60 次/小时限额），配置 `GITHUB_TOKEN` 可提升到 5000 次/小时。

## 📊 数据库说明

### 表结构（7 张表）

| 表名 | 用途 |
|------|------|
| `repos` | GitHub 热门仓库信息 |
| `releases` | 仓库 Release 版本记录 |
| `repo_topics` | 仓库与主题多对多关联 |
| `topics` | 预定义主题（6 个） |
| `articles` | AI 科普文章元数据 |
| `repo_star_history` | Star 历史快照 |
| `fetch_logs` | 拉取日志 |

### 幂等设计

- `create_all()` 只建不删，表已存在则跳过
- `seed_topics()` 主题存在则更新、不存在则插入
- `sync_articles()` 按 slug 去重，已存在则更新内容

## 🔧 API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/stats/summary` | 统计概览 |
| GET | `/api/repos` | 仓库列表（分页、筛选、排序） |
| GET | `/api/repos/{id}` | 仓库详情（含 Release） |
| GET | `/api/topics` | 主题列表 |
| GET | `/api/topics/{name}` | 主题详情 |
| GET | `/api/articles` | 文章列表 |
| GET | `/api/articles/{slug}` | 文章详情（预渲染 HTML） |
| POST | `/api/agent/fetch` | 手动触发 GitHub 拉取 |

完整 API 文档：http://localhost:8000/docs

## 📝 添加新科普文章

在 `content/articles/` 目录下创建 `.md` 文件：

```markdown
---
title: 文章标题
summary: 一句话摘要
difficulty: beginner|intermediate|advanced
tags: [llm, rag, agent]
read_time: 10
---

正文内容（Markdown）...
```

后端启动时自动同步到数据库，无需手动操作。

## ⚙️ 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并修改：

```env
# GitHub Token（可选，提高 API 限额到 5000 次/小时）
GITHUB_TOKEN=ghp_your_token_here

# Agent 定时拉取（默认每周一 09:00 北京时间）
SCHEDULER_ENABLED=true
CRON_HOUR=9
CRON_DAY_OF_WEEK=mon
```

### Agent 拉取策略

- 6 大主题：llm、rag、agent、transformer、diffusion、mlops
- 每主题最多拉取 30 个仓库
- Star 阈值：≥ 500
- 对 Top 50 仓库拉取 Release（每仓库最多 5 条）
- 每周一 09:00 (Asia/Shanghai) 自动执行

## 🎯 架构设计

**模块化单体（Modular Monolith）**：

- 前后端单仓库，目录分离
- 后端单 FastAPI 进程，内部按职责分模块
- 模块间 Python 函数直接调用，零网络开销
- 模块边界清晰，后期可平滑拆分为微服务

详细设计文档见 [`docs/2026-08-22-ai-knowledge-hub-design.md`](docs/2026-08-22-ai-knowledge-hub-design.md)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 — 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 数据来源：[GitHub API](https://docs.github.com/en/rest)
- 前端框架：[Nuxt](https://nuxt.com/) / [Vue.js](https://vuejs.org/)
- 后端框架：[FastAPI](https://fastapi.tiangolo.com/)
- UI 样式：[Tailwind CSS](https://tailwindcss.com/)

---

**如果这个项目对你有帮助，欢迎点个 ⭐ Star 支持一下！**
