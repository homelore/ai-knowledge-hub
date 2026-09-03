# AI 知识网页设计文档

> **项目名称**：AI Knowledge Hub（ai-knowledge-hub）
> **文档版本**：v1.0
> **创建日期**：2026-08-22
> **状态**：待审核

---

## 目录

1. [项目概述](#1-项目概述)
2. [目标受众与内容策略](#2-目标受众与内容策略)
3. [技术栈选型](#3-技术栈选型)
4. [视觉设计规范](#4-视觉设计规范)
5. [项目结构设计](#5-项目结构设计方案a模块化单体)
6. [数据模型设计](#6-数据模型设计)
7. [页面路由设计](#7-页面路由设计)
8. [Agent 工作流设计](#8-agent-工作流设计)
9. [错误处理策略](#9-错误处理策略)
10. [部署策略](#10-部署策略)
11. [预留扩展空间](#11-预留扩展空间)
12. [附录 A：方案 B 架构文档（归档）](#附录-a方案-b-架构文档归档)

---

## 1. 项目概述

### 1.1 项目目标

构建一个 AI 知识网页，包含两大核心功能：

- **AI 科普知识**（纯前端）：展示 AI 相关科普文章，面向初学者和开发者混合受众，内容分层展示
- **GitHub 每周技术动态**（后端 Agent）：通过后端 Agent 每周定时拉取 GitHub trending 仓库，判断依据为 star 数量，展示最新 AI 技术趋势

### 1.2 核心价值

- 一站式追踪 AI 世界：从科普知识到 GitHub 趋势
- 数据驱动：以 star 数量为客观指标筛选热门项目
- 分层受众：初学者看科普，开发者看技术动态

---

## 2. 目标受众与内容策略

### 2.1 目标受众

**混合受众**——同时服务 AI 初学者和开发者：

- **初学者/爱好者**：对 AI 感兴趣但未必有技术背景，内容通俗易懂，科普为主
- **开发者/技术人员**：有编程经验，可包含技术细节、代码示例、API 参考

### 2.2 内容策略

内容分层展示，从科普到技术深入：

| 内容类型 | 面向 | 来源 | 管理方式 |
|----------|------|------|----------|
| AI 科普文章 | 初学者为主 | 人工编写 | 静态 Markdown 文件 |
| GitHub 仓库动态 | 开发者为主 | Agent 自动拉取 | SQLite 存储 |
| 主题分类筛选 | 全部受众 | 预定义主题表 | 数据库管理 |
| 项目发布动态 | 开发者为主 | Agent 拉取 releases | SQLite 存储 |

### 2.3 科普内容管理

采用**静态 Markdown** 方案：

- 用 Markdown 文件编写科普文章，存放在 `content/articles/` 目录
- 后端读取 Markdown 文件并渲染为 HTML 返回前端
- 数据库只存文章元数据（标题、难度、标签等），正文在文件中
- 更新内容只需修改 Markdown 文件，无需数据库操作

---

## 3. 技术栈选型

### 3.1 前端技术栈

| 技术 | 用途 | 选型理由 |
|------|------|----------|
| Vue 3 | 前端框架 | 响应式编程，组件生态丰富 |
| Nuxt 3 | 元框架 | 文件路由、SSR/SSG、SEO 友好 |
| Tailwind CSS | 样式框架 | 原子化 CSS，快速实现暗色渐变主题 |
| HTML/CSS | 科普页面 | 轻量展示，与 Vue 组件共存 |
| Shiki | 代码高亮 | 与暗色主题匹配，性能优秀 |

### 3.2 后端技术栈

| 技术 | 用途 | 选型理由 |
|------|------|----------|
| Python 3.11+ | 运行时 | AI 领域生态丰富 |
| FastAPI | Web 框架 | 异步高性能，自动生成 API 文档 |
| SQLAlchemy / SQLModel | ORM | 类型安全，支持 SQLite 和未来迁移 PostgreSQL |
| APScheduler | 定时任务 | 轻量级，进程内运行，无需额外中间件 |
| httpx | HTTP 客户端 | 异步调用 GitHub API |
| markdown / mistune | Markdown 渲染 | 后端将科普文章转为 HTML |
| bleach | HTML 消毒 | 清洗 GitHub README 中的不安全 HTML |

### 3.3 数据存储

| 存储 | 用途 | 选型理由 |
|------|------|----------|
| SQLite | 结构化数据 | 零配置，文件存储，本地开发友好 |
| Markdown 文件 | 科普文章正文 | 编辑器直接编写，版本管理友好 |

---

## 4. 视觉设计规范

### 4.1 设计方向

**暗色渐变混搭风**——融合"暗色极客风"与"渐变活泼风"两种方向：

- 保留暗色背景的科技感和极客审美
- 融入柔和渐变色彩和圆角卡片的友好感
- 适合混合受众：开发者觉得专业，初学者觉得友好

### 4.2 色彩规范

| 用途 | 色值 | 说明 |
|------|------|------|
| 主背景 | `#0f172a` | 深蓝灰底，保留极客感 |
| 卡片背景 | 半透明渐变 | `rgba(99,102,241,0.08)` → `rgba(52,211,153,0.05)` |
| 渐变文字 | 紫→蓝→绿 | `#a78bfa` → `#60a5fa` → `#34d399` |
| 主点缀色-紫 | `#a78bfa` | 主题标签、标题装饰 |
| 主点缀色-蓝 | `#60a5fa` | 链接、交互元素 |
| 主点缀色-绿 | `#34d399` | 增长数据、成功状态 |
| 强调色-金 | `#fbbf24` | star 数量、热门标记 |
| 文字-主 | `#e2e8f0` | 正文文字 |
| 文字-次 | `#94a3b8` | 描述、辅助文字 |
| 文字-弱 | `#64748b` | 注释、占位文字 |
| 边框 | `rgba(148,163,184,0.15)` | 卡片边框，低对比度 |

### 4.3 组件视觉规范

- **圆角**：卡片 14px，标签 20px（胶囊形），按钮 8px
- **渐变**：标题文字用三色渐变（紫→蓝→绿），背景用径向渐变光晕
- **标签**：渐变胶囊样式，如 LLM 用 `#6366f1→#8b5cf6`，RAG 用 `#34d399→#10b981`
- **卡片**：半透明渐变背景 + 1px 低对比度边框
- **Hero 区**：径向渐变光晕从顶部散开，打破纯黑死沉

---

## 5. 项目结构设计（方案A：模块化单体）

### 5.1 架构概述

采用**模块化单体（Modular Monolith）**架构：

- 前后端单仓库，目录分离
- 后端为单个 FastAPI 进程，内部按职责分模块
- 模块间通过 Python 函数直接调用，零网络开销
- 模块边界清晰，后期可平滑拆分为微服务

### 5.2 目录结构

```
ai-knowledge-hub/
├── frontend/                          # Vue 3 + Nuxt 前端
│   ├── nuxt.config.ts                 # Nuxt 配置（SSR/SSG、模块、CSS）
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js             # 暗色渐变主题色板
│   │
│   ├── pages/                          # 基于文件的路由
│   │   ├── index.vue                   # 首页：Hero + 本周热门 + 科普推荐
│   │   ├── repos/
│   │   │   ├── index.vue               # GitHub 仓库列表（分页+筛选）
│   │   │   └── [id].vue                # 仓库详情（README、Release动态）
│   │   ├── topics/
│   │   │   └── [topic].vue             # 主题分类页（llm/rag/agent...）
│   │   ├── articles/
│   │   │   └── [slug].vue              # 科普文章页（渲染 Markdown）
│   │   └── about.vue                   # 关于页面
│   │
│   ├── components/                     # 复用组件
│   │   ├── RepoCard.vue                # 仓库卡片（渐变标签+star+增长）
│   │   ├── ArticleCard.vue             # 科普文章卡片
│   │   ├── TopicFilter.vue             # 主题筛选器
│   │   ├── NavBar.vue                  # 顶部导航栏
│   │   ├── RepoChart.vue               # star趋势图
│   │   └── MarkdownRender.vue          # Markdown 渲染组件
│   │
│   ├── composables/                    # 组合式函数
│   │   ├── useApi.ts                   # 封装后端 API 调用
│   │   └── useFormat.ts                # 日期/数字格式化
│   │
│   └── assets/                         # 静态资源 + 全局 CSS
│
├── backend/                           # Python FastAPI 后端
│   ├── main.py                         # FastAPI 入口 + APScheduler 启动
│   ├── config.py                       # 配置（GitHub Token、DB路径、定时规则）
│   ├── requirements.txt
│   │
│   ├── api/                            # REST API 路由
│   │   ├── routes/
│   │   │   ├── repos.py                # GET /api/repos, /api/repos/:id
│   │   │   ├── releases.py             # GET /api/releases
│   │   │   ├── topics.py               # GET /api/topics, /api/topics/:name
│   │   │   ├── articles.py             # GET /api/articles/:slug
│   │   │   └── stats.py               # GET /api/stats/summary
│   │   └── deps.py                     # 依赖注入（数据库会话等）
│   │
│   ├── agent/                          # GitHub Agent 模块
│   │   ├── github_client.py            # GitHub API 封装
│   │   ├── fetcher.py                  # 拉取 trending + releases
│   │   ├── filter.py                   # star 筛选 + 主题分类
│   │   └── scheduler.py                # APScheduler 定时任务
│   │
│   ├── models/                         # 数据模型
│   │   ├── database.py                 # SQLite 连接 + ORM 基类
│   │   ├── repo.py                     # Repo 模型
│   │   ├── release.py                  # Release 模型
│   │   ├── topic.py                    # Topic 模型
│   │   ├── fetch_log.py                # FetchLog 模型
│   │   └── article.py                  # Article 元数据模型
│   │
│   └── services/                       # 业务逻辑层
│       ├── repo_service.py             # 仓库查询逻辑
│       ├── article_service.py          # 文章读取+渲染逻辑
│       └── stats_service.py            # 统计数据逻辑
│
├── content/
│   └── articles/                       # 科普文章 Markdown 源文件
│       ├── what-is-rag.md
│       ├── llm-explained.md
│       └── ...
│
├── docs/                              # 项目文档
│   └── 2026-08-22-ai-knowledge-hub-design.md
│
├── .env.example                        # 环境变量模板
├── .gitignore
└── README.md
```

### 5.3 模块间依赖关系

```
前端 (Vue/Nuxt)
    │
    │ HTTP API 调用
    ▼
后端 api/routes/  ──调用──►  services/  ──调用──►  models/ (数据库)
    │                                                        ▲
    │                                                        │
    │              agent/  ──写入──►  models/ (数据库) ─────┘
    │
    │ GitHub API (外部)
```

- `api/routes/` 调用 `services/` 获取数据，只做参数校验和响应格式化
- `services/` 调用 `models/` 做数据库操作，隔离业务逻辑
- `agent/` 独立运行，通过 `models/` 写入数据库表
- 前端通过 HTTP 调用 `api/routes/` 暴露的接口

---

## 6. 数据模型设计

### 6.1 ER 图概览

共 7 张表，SQLite 存储，SQLAlchemy / SQLModel 作为 ORM：

- `repos` — 仓库表（核心）
- `releases` — 发布动态表
- `topics` — 主题表
- `repo_topics` — 仓库主题关联表（M:N）
- `fetch_logs` — 拉取日志表
- `repo_star_history` — Star 历史表（趋势图数据源）
- `articles` — 文章元数据表

### 6.2 repos（仓库表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINC | 内部主键 |
| `github_id` | INTEGER | UQ | GitHub 仓库 ID，用于去重 |
| `full_name` | TEXT | | "owner/repo" 格式 |
| `name` | TEXT | | 仓库名 |
| `description` | TEXT | | 仓库描述 |
| `url` | TEXT | | GitHub 链接 |
| `stars` | INTEGER | | star 数量（排序依据） |
| `forks` | INTEGER | | fork 数量 |
| `language` | TEXT | | 主要编程语言 |
| `license` | TEXT | | 开源协议 |
| `weekly_star_gain` | INTEGER | | 本周 star 增长（计算字段） |
| `github_updated_at` | DATETIME | | GitHub 上的更新时间 |
| `created_at` | DATETIME | | 内部创建时间 |
| `updated_at` | DATETIME | | 内部更新时间 |

**设计说明**：
- 用 `github_id` 而非 `full_name` 做去重——仓库名可能因转移而变更
- `weekly_star_gain` 存为字段而非实时计算——避免每次查询做差值运算
- Agent 每次拉取时对比上次 `stars` 值计算增长

### 6.3 releases（发布动态表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINC | 内部主键 |
| `repo_id` | INTEGER | FK → repos.id | 关联仓库 |
| `tag_name` | TEXT | | 版本号 "v2.0.1" |
| `release_name` | TEXT | | Release 标题 |
| `body` | TEXT | | 更新日志内容 |
| `url` | TEXT | | Release 链接 |
| `is_prerelease` | BOOLEAN | | 是否预发布 |
| `published_at` | DATETIME | | 发布时间 |
| `created_at` | DATETIME | | 内部创建时间 |

**关系**：`repos` 1:N `releases`（一个仓库有多个 Release）

**设计说明**：Agent 拉取时只插入新出现的 `tag_name`，避免重复。

### 6.4 topics（主题表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINC | 内部主键 |
| `name` | TEXT | UQ | 主题标识 "llm" |
| `display_name` | TEXT | | 中文展示名 "大语言模型" |
| `description` | TEXT | | 主题描述 |
| `color` | TEXT | | UI 标签颜色 "#a78bfa" |
| `icon` | TEXT | | 图标标识 |
| `sort_order` | INTEGER | | 排序权重 |

**设计说明**：预定义的 AI 主题分类，`color` 字段与前端渐变配色呼应。

### 6.5 repo_topics（仓库主题关联表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `repo_id` | INTEGER | PK, FK → repos.id | 仓库 ID |
| `topic_id` | INTEGER | PK, FK → topics.id | 主题 ID |

**关系**：`repos` M:N `topics`（复合主键）

**设计说明**：一个仓库可属于多个主题（如 langgraph 同时属于 `llm` 和 `agent`），一个主题下有多个仓库。Agent 拉取时先删除旧关联再重新插入。

### 6.6 fetch_logs（拉取日志表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINC | 内部主键 |
| `fetch_week` | TEXT | | 拉取周标识 "2026-W34" |
| `total_fetched` | INTEGER | | 拉取总数 |
| `new_count` | INTEGER | | 新增仓库数 |
| `updated_count` | INTEGER | | 更新仓库数 |
| `status` | TEXT | | success / failed / running |
| `error_message` | TEXT | nullable | 错误信息 |
| `started_at` | DATETIME | | 开始时间 |
| `finished_at` | DATETIME | | 完成时间 |

**设计说明**：Agent 每次执行记录一条日志，用于追踪拉取状态和前端展示"最近更新时间"。

### 6.7 repo_star_history（Star 历史表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINC | 内部主键 |
| `repo_id` | INTEGER | FK → repos.id | 关联仓库 |
| `stars` | INTEGER | | 当时的 star 数量 |
| `recorded_week` | TEXT | | 记录周标识 "2026-W34" |
| `recorded_at` | DATETIME | | 记录时间 |

**关系**：`repos` 1:N `repo_star_history`（一个仓库有多条历史记录）

**设计说明**：Agent 每次拉取时，除更新 `repos.stars` 外，同时在此表插入一条历史快照。仓库详情页的 Star 趋势图通过查询此表最近 12 周数据绘制。若历史数据不足 12 周，图表显示已有周数即可。

### 6.8 articles（文章元数据表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTOINC | 内部主键 |
| `slug` | TEXT | UQ | URL 标识 "what-is-rag" |
| `title` | TEXT | | 文章标题 |
| `summary` | TEXT | | 摘要 |
| `difficulty` | TEXT | | beginner / intermediate / advanced |
| `read_time` | INTEGER | | 阅读时间（分钟） |
| `tags` | JSON | | 标签 ["llm","rag"] |
| `file_path` | TEXT | | Markdown 文件路径 |
| `published` | BOOLEAN | | 是否发布 |
| `created_at` | DATETIME | | 创建时间 |

**设计说明**：实际正文内容存在 `content/articles/*.md` 文件中，数据库只存元数据用于索引和筛选。文件方便用编辑器直接编写，数据库提供快速查询。

---

## 7. 页面路由设计

### 7.1 路由总览

基于 Nuxt 文件路由自动生成，共 6 个页面：

| # | 页面 | 文件 | 路由 | 主功能 |
|---|------|------|------|--------|
| 1 | 首页 | `index.vue` | `/` | Hero + 本周热门6卡 + 科普推荐3篇 + 主题导航 |
| 2 | 仓库列表 | `repos/index.vue` | `/repos` | 筛选（主题/语言/排序）+ 无限滚动 |
| 3 | 仓库详情 | `repos/[id].vue` | `/repos/:id` | README渲染 + Star趋势图 + Release时间线 |
| 4 | 主题分类 | `topics/[topic].vue` | `/topics/:topic` | 主题下仓库列表 + 相关主题 + 相关文章 |
| 5 | 科普文章 | `articles/[slug].vue` | `/articles/:slug` | Markdown渲染 + 代码高亮 + 上下篇导航 |
| 6 | 关于 | `about.vue` | `/about` | 项目介绍 + 更新机制 + 统计面板 |

### 7.2 各页面详细设计

#### 页面 1：首页 `index.vue`

**区块布局**：
- Hero 区：渐变标题 + 副文案 + 本周编号（如 "2026 · WEEK 34"）
- 本周热门：TOP 6 仓库卡片网格，按 `weekly_star_gain` 排序
- 科普推荐：最新 3 篇入门（beginner）文章
- 主题导航：6 个主题圆形入口

**API 调用**：
- `GET /api/repos?sort=weekly_gain&limit=6`
- `GET /api/articles?difficulty=beginner&limit=3`
- `GET /api/topics`

**复用组件**：RepoCard × 6, ArticleCard × 3, TopicBadge × 6

#### 页面 2：仓库列表 `repos/index.vue`

**区块布局**：
- 筛选栏：主题多选 + 语言筛选 + 排序方式（stars/gain/updated）
- 仓库卡片网格：无限滚动加载
- 空状态：无数据时友好提示
- 最近更新时间：读取 `fetch_logs` 最近一条

**API 调用**：
- `GET /api/repos?page=1&topic=llm&sort=stars`
- `GET /api/repos?language=python&sort=gain`
- `GET /api/fetch-logs/last`

**复用组件**：RepoCard, TopicFilter, LoadMore

#### 页面 3：仓库详情 `repos/[id].vue`

**区块布局**：
- 头部：仓库名 · star · fork · 语言标签
- README 渲染：后端转 HTML（bleach 消毒）
- Star 趋势图：最近 12 周数据折线图
- Release 动态：最近 5 条版本发布时间线
- 外链：GitHub 原仓库链接

**API 调用**：
- `GET /api/repos/:id`
- `GET /api/repos/:id/releases?limit=5`
- `GET /api/repos/:id/stargazers?weeks=12`

**复用组件**：RepoChart, ReleaseTimeline

#### 页面 4：主题分类 `topics/[topic].vue`

**区块布局**：
- 主题头部：图标 + 名称 + 描述 + 仓库数
- 仓库列表：该主题下所有仓库（按 star 排序）
- 相关主题：推荐其他相似主题
- 相关文章：该主题的科普文章

**API 调用**：
- `GET /api/topics/:name/repos`
- `GET /api/topics/:name`
- `GET /api/articles?tag=llm`

**复用组件**：RepoCard, TopicBadge, ArticleCard

#### 页面 5：科普文章 `articles/[slug].vue`

**区块布局**：
- 文章头部：标题 · 难度标签 · 阅读时间
- 正文：Markdown 渲染（后端转 HTML）
- 代码高亮：Shiki 语法高亮
- 标签栏：主题标签可点击跳转
- 上下篇导航：相关文章推荐

**API 调用**：
- `GET /api/articles/:slug`
- `GET /api/articles/:slug/related`

**复用组件**：MarkdownRender, CodeBlock, TopicBadge

#### 页面 6：关于 `about.vue`

**区块布局**：
- 项目介绍：目标 · 技术栈 · 数据来源
- 更新机制说明：Agent 每周拉取流程图
- 统计面板：仓库总数 · 文章数 · 周更新量
- 技术栈展示：Vue · Nuxt · FastAPI · SQLite

**API 调用**：
- `GET /api/stats/summary`
- `GET /api/fetch-logs?limit=4`

**复用组件**：StatCard, TechStack, UpdateFlow

### 7.3 全局组件

| 组件 | 位置 | 说明 |
|------|------|------|
| `NavBar.vue` | `app.vue` 全局布局 | 顶部导航 · 渐变 Logo · 路由链接 · 订阅按钮 |

### 7.4 SSR 首屏渲染

所有页面使用 Nuxt 的 `useAsyncData` 在服务端预取数据，首屏直出 HTML，对 SEO 友好。客户端导航时自动切换为 SPA 模式。

### 7.5 组件复用策略

- `RepoCard` — 首页、仓库列表、主题页都用，通过 props 控制紧凑/完整模式
- `ArticleCard` — 首页、主题页复用
- `TopicBadge` — 全局复用的主题标签，颜色从 `topics.color` 字段读取
- `NavBar` — 全局布局组件，在 `app.vue` 中包裹所有页面

### 7.6 API 调用封装

`composables/useApi.ts` 统一封装 fetch 请求：
- 处理 loading 状态
- 错误重试
- baseURL 切换（开发/生产环境）
- 类型安全的响应推断

### 7.7 交互设计

- 仓库列表用无限滚动替代分页，滚动到底部自动加载下一页
- 仓库详情的 Star 趋势图用轻量图表库（Chart.js / unplot）
- 文章页代码块用 Shiki 做语法高亮，与暗色主题匹配

---

## 8. Agent 工作流设计

### 8.1 工作流概览

Agent 每周定时执行 6 步流程，从 GitHub 拉取数据、转换筛选、写入数据库：

```
1.定时触发 → 2.初始化日志 → 3.拉取GitHub数据 → 4.数据转换筛选 → 5.写入数据库 → 6.更新日志
```

### 8.2 步骤详解

#### 步骤 1：定时触发

- **模块**：`agent/scheduler.py`
- **机制**：APScheduler `CronTrigger`
- **定时规则**：每周一 09:00（Asia/Shanghai），cron 表达式 `0 9 * * 1`
- **手动触发**：`POST /api/agent/fetch`（开发调试或需要即时更新时用）

#### 步骤 2：初始化拉取日志

- 在 `fetch_logs` 表插入一条 `status=running` 记录
- 生成 `fetch_week`（如 `2026-W34`，基于 ISO 周计算）
- 记录 `started_at` 时间戳
- 用途：前端展示"最近更新时间"和拉取状态

#### 步骤 3：拉取 GitHub 数据（核心步骤）

**3a. 仓库搜索**：
- 遍历预定义主题列表 `[llm, rag, agent, transformer, diffusion, mlops]`
- 逐个调用 GitHub Search API：`GET /search/repositories?q=topic:llm+stars:>1000+created:>2026-08-14&sort=stars`
- `created` 参数限定本周创建的仓库，`sort=stars` 按 star 排序

**3b. Release 拉取**：
- 对 Top 50 仓库逐一调用 `GET /repos/{owner}/{repo}/releases?per_page=5`
- 获取最近 5 条版本发布，用于"项目发布动态"展示

**3c. 限流与重试**：
- GitHub API 限制：5000 req/h（有 Token），60 req/h（无 Token）
- 使用 Token Bucket 算法控制请求速率
- 失败时指数退避重试：2s → 4s → 8s，最多 3 次
- 监控 `X-RateLimit-Remaining` 响应头，接近限制时主动等待

#### 步骤 4：数据转换与筛选

**4a. 字段映射**：
- GitHub JSON 字段映射到内部模型
- `id` → `github_id`, `stargazers_count` → `stars`, `forks_count` → `forks` 等

**4b. 去重**：
- 按 `github_id` 去重
- 同一仓库被多个主题命中时只保留首次出现

**4c. star 筛选**：
- 阈值：`stars >= 500`
- 取每周增长 TOP 50 仓库

**4d. 主题分类**：
- GitHub 仓库自带的 `topics` 字段映射到预定义 `topics` 表
- 建立 M:N 关联（写入 `repo_topics` 表）

**weekly_star_gain 计算**：
- 本次拉取的 `stars` - 数据库中上次记录的 `stars`
- 新仓库（库中不存在）的 `gain = stars`
- 用于"本周增长榜"排序

#### 步骤 5：写入数据库

- **`repos` 表**：UPSERT 语义（存在则更新 stars/forks/description，不存在则插入）
- **`repo_star_history` 表**：插入一条本周 star 快照记录（repo_id + stars + recorded_week）
- **`releases` 表**：只插入新的 `tag_name`，避免重复
- **`repo_topics` 表**：先删除该仓库旧关联，再重新插入，保证主题准确
- **事务**：全部在单事务中 COMMIT，失败则 ROLLBACK，保留上次数据不损坏

#### 步骤 6：更新日志与完成

- `fetch_logs` 更新为 `status=success`
- 记录 `total_fetched`（拉取总数）、`new_count`（新增数）、`updated_count`（更新数）
- 记录 `finished_at` 时间戳
- 前端可通过 `GET /api/fetch-logs/last` 展示"最近更新: 2026-W34 · 新增 12 个仓库"

### 8.3 预定义主题列表

初始 6 个主题，从 `config.py` 读取，可扩展：

| name | display_name | color | 搜索关键词 |
|------|-------------|-------|-----------|
| `llm` | 大语言模型 | `#a78bfa` | topic:llm |
| `rag` | 检索增强生成 | `#34d399` | topic:rag |
| `agent` | AI 智能体 | `#60a5fa` | topic:ai-agent |
| `transformer` | Transformer | `#fbbf24` | topic:transformer |
| `diffusion` | 扩散模型 | `#f472b6` | topic:diffusion-model |
| `mlops` | MLOps | `#c084fc` | topic:mlops |

---

## 9. 错误处理策略

| 错误类型 | 处理方式 | 影响范围 |
|----------|----------|----------|
| GitHub API 限流 (429) | 读取 `X-RateLimit-Reset` 头，等待后重试 | 暂停拉取，不影响已有数据 |
| 网络超时 | 指数退避重试 3 次（2s/4s/8s） | 跳过当前仓库，继续处理其他 |
| 数据格式异常 | 跳过该条，记录 warning 日志 | 不影响其他数据处理 |
| 致命错误 | `fetch_logs` 标记 `status=failed`，记录 `error_message` | 保留上次数据，前端展示失败状态 |
| 数据库写入失败 | 事务 ROLLBACK | 数据库保持上次一致状态 |

---

## 10. 部署策略

### 10.1 当前阶段：本地开发

- 前端 Vue 开发服务器 + 后端 Python FastAPI 本地运行
- 数据库用 SQLite（零配置，文件存储）
- 先把功能跑通，部署留到后面再决定
- Agent 定时任务需要本地常驻运行

### 10.2 未来部署选项

#### 选项 A：云平台免费层

- 前端：Vercel/Netlify 免费层，git push 后自动部署，自带全球 CDN
- 后端 Agent：Vercel Serverless Functions 或 AWS Lambda，按调用次数计费
- 数据库：Supabase / PlanetScale / MongoDB Atlas 的免费层（500MB-1GB）
- 优点：零成本起步，自动扩缩容
- 缺点：免费层有流量限制，Serverless 冷启动有延迟

#### 选项 B：Docker 容器化

- 前端构建为静态文件用 Nginx 托管，后端 Python FastAPI 打包为 Docker 镜像
- 用 `docker-compose` 一键编排前端 + 后端 + 数据库
- 可本地运行，也可推送到任意 VPS
- 优点：环境一致性，完全可控，迁移方便
- 缺点：需要一台服务器（VPS 月费约几十元），需自行维护

#### 选项 C：方案 B 微服务架构

详见附录 A。

---

## 11. 预留扩展空间

### 11.1 GitHub 数据扩展

当前版本实现"主题分类筛选"和"项目发布动态"两项，架构预留以下扩展：

- **热门仓库列表**：扩展步骤 3 的搜索条件，不限主题，按全站 star 排序
- **本周增长榜**：按 `weekly_star_gain` 排序，突出新晋热门项目
- **贡献者数量**：拉取仓库 contributors 数量，作为活跃度指标

### 11.2 功能扩展

- **Webhook/邮件通知**：步骤 6 完成后触发，通知新仓库上架
- **主题列表可配置化**：从 `config.py` 读取，方便增减主题
- **AI 生成内容摘要**：未来可用模型分析仓库内容生成摘要（此时考虑迁移方案 B）
- **用户订阅功能**：订阅特定主题，有新仓库时推送通知

### 11.3 架构迁移路径

方案 A 的模块已按职责分好（`api/`、`agent/`、`models/`、`services/`），如将来需要拆成方案 B 的微服务：

- `agent/` 可独立成 Celery Worker 服务
- `api/` 可独立成 API 服务
- `models/` 可独立为共享库
- 迁移成本较低，反方向迁移更难

---

## 附录 A：方案 B 架构文档（归档）

> 此方案为备选架构，当前不采用，保留供未来参考。

### A.1 架构概述

**前后端分离 + 微服务架构**：将 Agent、API、内容管理拆分为独立服务，通过 API 网关统一路由，使用消息队列做异步通信。

### A.2 架构组成

| 组件 | 技术 | 端口 | 说明 |
|------|------|------|------|
| 前端 | Vue 3 + Nuxt | - | 独立部署到 Vercel/Netlify CDN |
| API 网关 | Nginx / Traefik | 80/443 | 路由分发、负载均衡、CORS |
| API 服务 | FastAPI | 8001 | 对前端提供 REST API |
| Agent 服务 | Celery Worker | 8002 | GitHub 数据拉取，真正异步 |
| 内容服务 | FastAPI | 8003 | Markdown 读取和渲染 |
| 消息队列 | Redis / RabbitMQ | 6379 | 任务分发，Agent 异步通信 |
| 数据库 | PostgreSQL | 5432 | 结构化数据存储 |
| Markdown 存储 | 文件系统 / 对象存储 | - | 科普文章源文件 |

### A.3 数据流

```
浏览器用户
    │
    ▼
API 网关 (Nginx/Traefik)
    │
    ├──► API 服务 (FastAPI :8001) ──► PostgreSQL
    │
    ├──► 内容服务 (FastAPI :8003) ──► Markdown 存储
    │
    └──► Agent 服务 (Celery Worker :8002)
            │
            ├──► Redis/RabbitMQ (消息队列)
            ├──► GitHub API (外部)
            └──► PostgreSQL (写入)
```

### A.4 优缺点对比

| 维度 | 方案 A（当前采用） | 方案 B（归档） |
|------|------|------|
| 进程数 | 1 个 FastAPI 进程 | 3+ 服务 + Redis + Nginx |
| 仓库结构 | 单仓库 | 可拆为 3-4 个独立仓库 |
| 本地启动 | 2 个进程 | 5+ 个进程 |
| 服务间通信 | Python 函数直接调用 | HTTP/RPC 跨进程调用 |
| Agent 异步 | APScheduler 进程内 | Celery Worker 真正异步 |
| 数据库 | SQLite 零配置 | PostgreSQL 需配置 |
| 消息队列 | 不需要 | 需要 Redis/RabbitMQ |
| API 网关 | 不需要 | 需要 Nginx/Traefik |
| 部署复杂度 | Docker 单容器 | 每个服务独立 Docker + 编排 |
| 调试难度 | 单进程断点 | 跨服务断点困难 |
| 扩展性 | 水平扩展受限 | 各服务独立扩展 |
| 适合阶段 | 现在：功能验证 | 未来：高并发、团队协作 |

### A.5 迁移条件

当满足以下条件之一时，考虑迁移到方案 B：

1. Agent 涉及大量 AI 模型处理（如用模型分析仓库内容生成摘要），计算密集型任务需要独立 Worker
2. 网站流量增长到单进程无法承载
3. 团队多人协作，需要各模块独立开发部署
4. 需要各服务独立水平扩展

### A.6 迁移路径

方案 A 的模块边界已按方案 B 的服务划分设计：

- `backend/agent/` → 独立 Celery Worker 服务
- `backend/api/` → 独立 API 服务
- `backend/services/` → 拆分到各服务内部
- `backend/models/` → 独立为共享库（shared package）
- SQLite → 迁移到 PostgreSQL（SQLAlchemy ORM 兼容）
- APScheduler → 替换为 Celery Beat

迁移成本较低，每个模块可独立成服务，无需重写业务逻辑。

---

## 文档变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-08-22 | v1.0 | 初始版本，完整设计文档 |
