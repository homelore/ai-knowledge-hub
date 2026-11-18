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

### 🎯 对话式项目推荐
- 3 轮对话采集画像（感兴趣主题 / 当前水平 / 上手偏好），无 LLM key 也能跑通
- 规则引擎打分 + 多样性硬约束：主题至少 3 种、owner 不重复、10 万 star 以上最多 1 个、2 万 star 以下至少 2 个
- 每条结果附可核查的推荐理由、第一步上手建议、相关科普文章
- 支持「不感兴趣」与「换一批」，会话内自动去重

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
│   │   └── routes/         # repos / releases / topics / articles / stats / agent / recommend
│   ├── models/             # SQLAlchemy 数据模型（8 张表）
│   ├── services/           # 业务逻辑层
│   │   ├── recommend/      # 推荐：profile 画像 / engine 打分与约束 / store 会话 / cache / llm_orchestrator
│   │   └── llm/            # 火山方舟接入：config / ark_client / recommend_llm / guard
│   ├── eval/               # golden set 与评测报告
│   ├── scripts/            # seed / annotate_repos / llm_annotate / verify_m1~m3 / eval_recommend
│   ├── config.py           # 环境配置
│   ├── main.py             # FastAPI 入口
│   └── requirements.txt    # Python 依赖
├── frontend/              # Nuxt 4 前端
│   ├── app/
│   │   ├── pages/          # 文件路由（首页、仓库列表、推荐、文章详情等）
│   │   ├── components/     # UI 组件
│   │   ├── composables/    # 组合式函数（useApi、useFormat、useRecommend）
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

### 5. 标注仓库（推荐功能必需）

推荐引擎只从 `repo_meta` 已标注的仓库里选，未标注的不进候选池：

```bash
cd backend

# 规则初标：幂等，不覆盖人工标注
python scripts/annotate_repos.py

# 可选：用豆包预标注，需 ARK_API_KEY
python scripts/llm_annotate.py

# 验收：标注数、空值数、原始 topics 覆盖率
python scripts/verify_m1.py
```

## 📊 数据库说明

### 表结构（8 张表）

| 表名 | 用途 |
|------|------|
| `repos` | GitHub 热门仓库信息（含 `pushed_at` / `open_issues` / `size` / `github_topics`） |
| `repo_meta` | 仓库标注：difficulty / setup_cost / run_mode / needs_gpu / category，推荐引擎的数据基础 |
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
| POST | `/api/recommend/chat` | 对话式推荐：回答一轮 → 下一问或推荐结果 |
| POST | `/api/recommend/action` | 结果反馈：`skip` 不感兴趣 / `refresh` 换一批 |
| POST | `/api/recommend` | 无状态推荐：给定画像直接返回（评测脚本使用） |
| POST | `/api/recommend/event` | 前端埋点上报 |

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

# 跨域，逗号分隔
CORS_ORIGINS=http://localhost:3000

# 推荐精排用的 LLM（火山方舟 / 豆包）
# 默认关闭：M5 评测显示 LLM 精排 nDCG 低于规则版，按验收标准停用
# 打开后若缺 key 或模型标识，会自动降级为规则路径
LLM_ENABLED=false
ARK_API_KEY=
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=doubao-seed-1-6-flash-250828
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

## 🤖 推荐系统

### 处理流程

1. **画像采集** — 固定 3 问（感兴趣主题 / 当前水平 / 上手偏好）；无 LLM key 时用关键词规则解析
2. **候选打分** — 主题命中 +30、关键词 +6、水平匹配 +15、偏好属性、新鲜度、热度、语言
3. **多样性硬约束** — DFS 剪枝选出 Top5，同时满足：主题至少 3 种、owner 不重复、>10 万 star 至多 1 个、<2 万 star 至少 2 个
4. **结果组装** — 每条含理由、第一步建议、相关科普文章

### 评测

`backend/eval/golden_recommend.json` 为 24 条 query（6 主题 × 4 画像）的 golden set，可一键复现：

```bash
cd backend
python scripts/build_golden_set.py   # 按 rubric 生成/刷新标注
python scripts/eval_recommend.py     # 输出 eval/report_recommend.json
```

| 指标 | 规则版 | 阈值 |
|------|--------|------|
| nDCG@5 | 0.7723 | ≥ 0.70 |
| Recall@5 | 0.7049 | ≥ 0.60 |
| 理由不支持率 | 0% | ≤ 5% |

> 口径说明：golden set 的 rubric 与规则引擎打分同源（主题 / 水平 / 偏好），对规则版有利。LLM 版 nDCG 为 0.7255，未达「比规则版高 ≥10%」的阈值，故默认关闭；这组数字只能说明 LLM 未在规则的目标函数上占优，不等于人工体验更差。

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
