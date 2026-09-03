// Mock 数据 - 主题
export const mockTopics = [
  {
    name: 'llm',
    display_name: '大语言模型',
    description: '从 Transformer 到 GPT，探索语言模型的演进与应用',
    color: '#a78bfa',
    icon: '🧠',
    sort_order: 1,
    repo_count: 42
  },
  {
    name: 'rag',
    display_name: '检索增强生成',
    description: '让大模型接入外部知识，回答更精准更可靠',
    color: '#34d399',
    icon: '🔍',
    sort_order: 2,
    repo_count: 28
  },
  {
    name: 'agent',
    display_name: 'AI 智能体',
    description: '能自主规划、调用工具的 AI Agent 框架与实践',
    color: '#60a5fa',
    icon: '🤖',
    sort_order: 3,
    repo_count: 35
  },
  {
    name: 'transformer',
    display_name: 'Transformer',
    description: 'Attention is All You Need — 现代 AI 的核心架构',
    color: '#fbbf24',
    icon: '⚡',
    sort_order: 4,
    repo_count: 19
  },
  {
    name: 'diffusion',
    display_name: '扩散模型',
    description: '从噪声中生成图像与视频的生成式 AI 技术',
    color: '#f472b6',
    icon: '🎨',
    sort_order: 5,
    repo_count: 24
  },
  {
    name: 'mlops',
    display_name: 'MLOps',
    description: '机器学习模型的部署、监控与运维最佳实践',
    color: '#c084fc',
    icon: '⚙️',
    sort_order: 6,
    repo_count: 16
  }
]

// Mock 数据 - 仓库
export const mockRepos = [
  {
    id: 1,
    github_id: 457175892,
    full_name: 'langchain-ai/langchain',
    name: 'langchain',
    description: 'Build context-aware reasoning applications with LLMs through composable chains and agents',
    url: 'https://github.com/langchain-ai/langchain',
    stars: 92456,
    forks: 14231,
    language: 'Python',
    license: 'MIT',
    weekly_star_gain: 1287,
    topics: ['llm', 'agent'],
    github_updated_at: '2026-08-20T10:30:00Z'
  },
  {
    id: 2,
    github_id: 762481328,
    full_name: 'microsoft/graphrag',
    name: 'graphrag',
    description: 'A modular graph-based Retrieval-Augmented Generation (RAG) system',
    url: 'https://github.com/microsoft/graphrag',
    stars: 18934,
    forks: 2156,
    language: 'Python',
    license: 'MIT',
    weekly_star_gain: 2341,
    topics: ['rag', 'llm'],
    github_updated_at: '2026-08-21T08:15:00Z'
  },
  {
    id: 3,
    github_id: 597489281,
    full_name: 'anthropics/claude-code',
    name: 'claude-code',
    description: 'An interactive agent that writes and runs code in your terminal',
    url: 'https://github.com/anthropics/claude-code',
    stars: 15678,
    forks: 1823,
    language: 'TypeScript',
    license: 'MIT',
    weekly_star_gain: 892,
    topics: ['agent', 'llm'],
    github_updated_at: '2026-08-19T14:45:00Z'
  },
  {
    id: 4,
    github_id: 634789215,
    full_name: 'stanfordnlp/dspy',
    name: 'dspy',
    description: 'Programming with Foundation Models — Declarative, Self-improving Modules',
    url: 'https://github.com/stanfordnlp/dspy',
    stars: 17234,
    forks: 2087,
    language: 'Python',
    license: 'MIT',
    weekly_star_gain: 567,
    topics: ['llm', 'rag'],
    github_updated_at: '2026-08-20T16:20:00Z'
  },
  {
    id: 5,
    github_id: 712893456,
    full_name: 'comfyanonymous/ComfyUI',
    name: 'ComfyUI',
    description: 'A powerful and modular stable diffusion GUI and backend with a node-based interface',
    url: 'https://github.com/comfyanonymous/ComfyUI',
    stars: 54321,
    forks: 7823,
    language: 'Python',
    license: 'GPL-3.0',
    weekly_star_gain: 1023,
    topics: ['diffusion'],
    github_updated_at: '2026-08-21T11:00:00Z'
  },
  {
    id: 6,
    github_id: 489321765,
    full_name: 'huggingface/transformers',
    name: 'transformers',
    description: 'State-of-the-art Machine Learning for Pytorch, TensorFlow, and JAX',
    url: 'https://github.com/huggingface/transformers',
    stars: 134567,
    forks: 25678,
    language: 'Python',
    license: 'Apache-2.0',
    weekly_star_gain: 456,
    topics: ['transformer', 'llm'],
    github_updated_at: '2026-08-21T09:30:00Z'
  },
  {
    id: 7,
    github_id: 823456128,
    full_name: 'mlflow/mlflow',
    name: 'mlflow',
    description: 'Open source platform for the machine learning lifecycle',
    url: 'https://github.com/mlflow/mlflow',
    stars: 18923,
    forks: 4567,
    language: 'Python',
    license: 'Apache-2.0',
    weekly_star_gain: 178,
    topics: ['mlops'],
    github_updated_at: '2026-08-20T13:15:00Z'
  },
  {
    id: 8,
    github_id: 789234561,
    full_name: 'langgenius/dify',
    name: 'dify',
    description: 'LLM application development platform — visual workflow, RAG, and agent orchestration',
    url: 'https://github.com/langgenius/dify',
    stars: 48932,
    forks: 7234,
    language: 'TypeScript',
    license: 'MIT',
    weekly_star_gain: 1567,
    topics: ['llm', 'agent'],
    github_updated_at: '2026-08-21T07:45:00Z'
  },
  {
    id: 9,
    github_id: 678912345,
    full_name: 'run-llama/llama_index',
    name: 'llama_index',
    description: 'A data framework for building LLM applications over your data',
    url: 'https://github.com/run-llama/llama_index',
    stars: 34567,
    forks: 5123,
    language: 'Python',
    license: 'MIT',
    weekly_star_gain: 723,
    topics: ['rag', 'llm'],
    github_updated_at: '2026-08-20T12:00:00Z'
  },
  {
    id: 10,
    github_id: 543219876,
    full_name: 'openai/swarm',
    name: 'swarm',
    description: 'Educational framework exploring ergonomic, lightweight multi-agent orchestration',
    url: 'https://github.com/openai/swarm',
    stars: 21345,
    forks: 2876,
    language: 'Python',
    license: 'MIT',
    weekly_star_gain: 345,
    topics: ['agent', 'llm'],
    github_updated_at: '2026-08-19T15:30:00Z'
  },
  {
    id: 11,
    github_id: 923456781,
    full_name: 'AUTOMATIC1111/stable-diffusion-webui',
    name: 'stable-diffusion-webui',
    description: 'Stable Diffusion web UI with a vast extension ecosystem',
    url: 'https://github.com/AUTOMATIC1111/stable-diffusion-webui',
    stars: 142345,
    forks: 27890,
    language: 'Python',
    license: 'AGPL-3.0',
    weekly_star_gain: 234,
    topics: ['diffusion'],
    github_updated_at: '2026-08-21T10:00:00Z'
  },
  {
    id: 12,
    github_id: 345678912,
    full_name: 'pytorch/pytorch',
    name: 'pytorch',
    description: 'Tensors and Dynamic neural networks in Python with strong GPU acceleration',
    url: 'https://github.com/pytorch/pytorch',
    stars: 82345,
    forks: 19234,
    language: 'Python',
    license: 'BSD-3-Clause',
    weekly_star_gain: 189,
    topics: ['transformer', 'mlops'],
    github_updated_at: '2026-08-21T05:00:00Z'
  }
]

// Mock 数据 - Release
export const mockReleases = [
  {
    id: 1,
    repo_id: 1,
    tag_name: 'v0.3.10',
    release_name: 'LangChain v0.3.10',
    body: '## What\'s new\n- Added new tool calling abstractions\n- Improved agent memory management\n- Fixed streaming issues with certain providers\n- Performance optimizations for document loading',
    url: 'https://github.com/langchain-ai/langchain/releases/tag/v0.3.10',
    is_prerelease: false,
    published_at: '2026-08-18T12:00:00Z'
  },
  {
    id: 2,
    repo_id: 1,
    tag_name: 'v0.3.9',
    release_name: 'LangChain v0.3.9',
    body: '## What\'s new\n- New integrations with multiple LLM providers\n- Enhanced RAG pipeline support\n- Bug fixes for callback system',
    url: 'https://github.com/langchain-ai/langchain/releases/tag/v0.3.9',
    is_prerelease: false,
    published_at: '2026-08-10T09:30:00Z'
  },
  {
    id: 3,
    repo_id: 5,
    tag_name: 'v0.2.5',
    release_name: 'ComfyUI v0.2.5',
    body: '## Features\n- New sampler nodes\n- Improved memory management\n- Better batch processing support\n- Updated extension API',
    url: 'https://github.com/comfyanonymous/ComfyUI/releases/tag/v0.2.5',
    is_prerelease: false,
    published_at: '2026-08-15T14:20:00Z'
  },
  {
    id: 4,
    repo_id: 8,
    tag_name: 'v1.2.0',
    release_name: 'Dify v1.2.0',
    body: '## Highlights\n- Workflow designer 2.0 with new node types\n- Native support for multimodal models\n- Enhanced RAG with knowledge graph\n- New plugin marketplace',
    url: 'https://github.com/langgenius/dify/releases/tag/v1.2.0',
    is_prerelease: false,
    published_at: '2026-08-20T08:00:00Z'
  }
]

// Mock 数据 - Star 历史（按周）
export const mockStarHistory = {
  1: [
    { week: '2026-W29', stars: 88200 },
    { week: '2026-W30', stars: 89100 },
    { week: '2026-W31', stars: 89950 },
    { week: '2026-W32', stars: 90650 },
    { week: '2026-W33', stars: 91169 },
    { week: '2026-W34', stars: 92456 }
  ],
  2: [
    { week: '2026-W29', stars: 11200 },
    { week: '2026-W30', stars: 13100 },
    { week: '2026-W31', stars: 14800 },
    { week: '2026-W32', stars: 16200 },
    { week: '2026-W33', stars: 16593 },
    { week: '2026-W34', stars: 18934 }
  ],
  5: [
    { week: '2026-W29', stars: 50200 },
    { week: '2026-W30', stars: 51000 },
    { week: '2026-W31', stars: 51800 },
    { week: '2026-W32', stars: 52500 },
    { week: '2026-W33', stars: 53298 },
    { week: '2026-W34', stars: 54321 }
  ]
}

// Mock 数据 - 科普文章
export const mockArticles = [
  {
    id: 1,
    slug: 'what-is-rag',
    title: '什么是 RAG？检索增强生成入门指南',
    summary: 'RAG 是让大语言模型接入外部知识的关键技术，本文带你从零理解它的原理、流程和应用场景。',
    difficulty: 'beginner',
    read_time: 8,
    tags: ['rag', 'llm'],
    published: true,
    created_at: '2026-08-01T00:00:00Z',
    content: `# 什么是 RAG？

**RAG（Retrieval-Augmented Generation，检索增强生成）** 是一种让大语言模型（LLM）接入外部知识的技术方案。

## 为什么需要 RAG？

大语言模型虽然强大，但有两个天然局限：

1. **知识截止日期**：模型的训练数据有截止时间，之后发生的事情它不知道
2. **私有知识盲区**：企业内部文档、个人笔记等私有数据，模型不可能学到

RAG 通过"先检索，再生成"的方式解决了这两个问题。

## RAG 的工作流程

一个典型的 RAG 系统分为三个阶段：

### 1. 索引阶段（Indexing）

将文档切分成小块（chunk），通过 Embedding 模型转换成向量，存入向量数据库。

\`\`\`
文档 → 切分 → Embedding → 向量数据库
\`\`\`

### 2. 检索阶段（Retrieval）

用户提问时，将问题也转换成向量，在向量数据库中找到最相似的几个文档块。

\`\`\`
问题 → Embedding → 相似度搜索 → Top-K 文档块
\`\`\`

### 3. 生成阶段（Generation）

将检索到的文档块和用户问题一起拼入 Prompt，让 LLM 基于参考资料回答问题。

\`\`\`
[参考资料] + [用户问题] → LLM → 答案
\`\`\`

## RAG 的优势

- **时效性强**：知识可以随时更新，不需要重新训练模型
- **成本低廉**：相比微调，RAG 的实施成本低得多
- **可解释性**：答案可以追溯到具体的参考来源
- **数据安全**：敏感数据不需要喂给模型训练

## 常见应用场景

- 企业知识库问答
- 客服机器人
- 文档摘要与对比
- 代码助手

## 小结

RAG 是目前最实用、成本最低的 LLM 落地方式之一。如果你想让 AI 基于你的私有数据回答问题，RAG 几乎是标配。`
  },
  {
    id: 2,
    slug: 'llm-explained',
    title: '大语言模型是怎么工作的？从 Transformer 说起',
    summary: '一文读懂大语言模型的核心原理：注意力机制、Transformer 架构、预训练与微调。',
    difficulty: 'beginner',
    read_time: 12,
    tags: ['llm', 'transformer'],
    published: true,
    created_at: '2026-07-15T00:00:00Z',
    content: `# 大语言模型是怎么工作的？

大语言模型（Large Language Model, LLM）是当前 AI 浪潮的核心驱动力。它到底是怎么工作的？

## 一句话原理

**大语言模型本质上是一个"下一个词预测器"**——给定前面的文字，预测下一个最可能出现的词是什么。

听起来很简单，但当模型足够大、数据足够多时，它会"涌现"出令人惊讶的能力。

## 核心架构：Transformer

所有现代大语言模型都基于 **Transformer** 架构，它的核心是 **自注意力机制（Self-Attention）**。

### 自注意力机制

自注意力让模型在处理每个词时，都能"看到"句子中其他所有词，并判断哪些词和它关系最密切。

比如在句子"动物没有穿过街道，因为它太累了"中：

- 模型需要知道"它"指的是"动物"而不是"街道"
- 自注意力机制会给"动物"这个词更高的权重

### Transformer 的结构

\`\`\`
输入 → 嵌入层 → [编码器层 × N] → [解码器层 × N] → 输出层 → 预测下一个词
           ↑                    ↑
        自注意力            自注意力 + 交叉注意力
\`\`\`

现代 LLM 大多只用解码器部分（Decoder-only），比如 GPT 系列。

## 训练的三个阶段

### 1. 预训练（Pre-training）

用海量文本数据（互联网书籍、文章、代码等）训练模型，让它学会语言规律和世界知识。

- 数据量：万亿级 token
- 计算量：数千张 GPU 训练数月
- 这是最烧钱的阶段

### 2. 监督微调（SFT）

用高质量的对话数据进一步训练，让模型学会"好好说话"。

### 3. 人类反馈强化学习（RLHF）

通过人类对模型回答的打分，训练一个奖励模型，再用强化学习让模型生成更符合人类偏好的回答。

## 为什么越大越好？

模型参数量越大、训练数据越多，能力通常越强。这被称为 **Scaling Law（缩放定律）**。

- **7B 参数**：能做基础对话、写简单代码
- **70B 参数**：接近 GPT-3.5 水平，复杂推理能力强
- **GPT-4 级别**：专家级能力，能处理复杂多步任务

## 小结

大语言模型的原理并不复杂——就是预测下一个词。但当规模足够大时，简单的机制会涌现出复杂的智能。这正是 AI 最迷人的地方。`
  },
  {
    id: 3,
    slug: 'agent-intro',
    title: 'AI Agent 入门：让大模型学会"做事"',
    summary: '从 ReAct 到多 Agent 协作，了解 AI 智能体的核心概念、主流框架和典型应用。',
    difficulty: 'intermediate',
    read_time: 10,
    tags: ['agent', 'llm'],
    published: true,
    created_at: '2026-08-10T00:00:00Z',
    content: `# AI Agent 入门

AI Agent（智能体）是大语言模型之后的下一个热点——让 AI 不只是"说话"，而是真正"做事"。

## 什么是 AI Agent？

AI Agent 是一个能**自主感知环境、做出决策、并采取行动**的 AI 系统。

和普通的 LLM 对话相比，Agent 多了三个关键能力：

1. **工具使用**：能调用外部工具（搜索引擎、计算器、API、代码执行等）
2. **规划能力**：能把复杂任务拆解成多个步骤
3. **记忆能力**：能记住之前的操作和结果，动态调整策略

## Agent 的核心循环

\`\`\`
思考（Thought） → 行动（Action） → 观察（Observation） → 再思考 → ...
\`\`\`

这个循环被称为 **ReAct 模式**（Reasoning + Acting）。Agent 每一步都会：

1. 分析当前状态，决定下一步做什么
2. 调用工具执行行动
3. 观察行动结果
4. 重复，直到任务完成

## 主流 Agent 框架

### LangChain / LangGraph

最流行的 Agent 框架，支持多种工具集成和工作流编排。LangGraph 专门用于构建有状态的多步骤 Agent。

### AutoGen

微软推出的多 Agent 框架，擅长多个 Agent 之间的协作对话。

### CrewAI

面向"团队协作"的 Agent 框架，每个 Agent 有不同角色（研究员、作家、分析师等）。

### Dify

低代码平台，可视化拖拽设计 Agent 工作流。

## 典型应用场景

- **研究助手**：自动搜索资料、整理报告
- **代码 Agent**：自动编写、调试、部署代码
- **数据分析师**：自动查询数据库、生成图表、撰写分析报告
- **客服 Agent**：调用内部系统处理用户问题
- **内容创作团队**：多个 Agent 分工协作（策划→写作→编辑→发布）

## 挑战与局限

- **可靠性**：Agent 可能在循环中"迷路"，需要精心设计提示词和错误处理
- **成本**：多轮推理消耗大量 token，成本较高
- **安全**：Agent 调用工具可能带来安全风险，需要权限控制
- **评估困难**：Agent 的表现难以量化评估

## 小结

AI Agent 是 LLM 从"对话工具"进化为"生产力工具"的关键一步。虽然还不成熟，但潜力巨大，值得每一个关注 AI 的人深入了解。`
  },
  {
    id: 4,
    slug: 'diffusion-basics',
    title: '扩散模型原理：AI 画图是怎么做到的？',
    summary: '从噪声到图像，理解 Stable Diffusion 等生成式 AI 背后的数学原理。',
    difficulty: 'intermediate',
    read_time: 15,
    tags: ['diffusion'],
    published: true,
    created_at: '2026-07-28T00:00:00Z',
    content: `# 扩散模型原理

你可能用过 Stable Diffusion、Midjourney 或 DALL·E 来生成图片。这些 AI 画图工具背后的核心技术就是 **扩散模型（Diffusion Model）**。

## 核心思想

扩散模型的灵感来自热力学中的扩散现象：

- **前向过程**：往一张图片中逐步加入噪声，直到图片变成完全随机的噪声
- **反向过程**：从完全随机的噪声出发，逐步去除噪声，还原出一张清晰的图片

\`\`\`
清晰图片 → 加噪 → 加噪 → ... → 纯噪声（前向过程）
纯噪声 → 去噪 → 去噪 → ... → 清晰图片（反向过程）
\`\`\`

训练模型就是学习这个反向去噪的过程。

## 为什么叫"扩散"？

想象一滴墨水滴入清水中——墨水会逐渐扩散开来，直到均匀分布。这个过程是不可逆的（墨水不会自己重新聚成一滴）。

但扩散模型反其道而行之：训练一个神经网络，学习如何"逆转"这个扩散过程。

## 技术演进

### DDPM (Denoising Diffusion Probabilistic Models)

扩散模型的开山之作，2020 年提出。效果好但速度慢——生成一张图片需要一步步去噪上千次。

### DDIM / 加速采样

通过数学优化，将采样步数从 1000 步减少到 50 步甚至更少，大大提升了生成速度。

### Stable Diffusion

2022 年发布，在潜空间（Latent Space）中做扩散，大幅降低了计算量，让消费级显卡也能跑起来。

### Sora / 视频扩散

扩散模型不仅能生成图片，还能生成视频。Sora 就是大规模扩散模型在视频领域的应用。

## 关键组件

### UNet

扩散模型的"主力"网络，负责预测噪声。它是一种 U 型的卷积神经网络，能同时捕捉细节和全局信息。

### 文本编码器

把文字提示（Prompt）转换成向量，指导图像生成。常用的有 CLIP Text Encoder、T5 等。

### VAE（变分自编码器）

Stable Diffusion 特有，负责在像素空间和潜空间之间转换——编码时压缩图片，解码时还原图片。

## 小结

扩散模型用"逐步去噪"的方式生成图像，原理优雅、效果惊艳。从图像到视频、从 2D 到 3D，扩散模型正在持续扩展它的边界。`
  }
]

// Mock 数据 - 统计
export const mockStats = {
  total_repos: 156,
  total_articles: 4,
  total_topics: 6,
  weekly_new_repos: 12,
  total_stars: 523456,
  last_fetch_week: '2026-W34',
  last_fetch_time: '2026-08-19T01:00:00Z'
}
