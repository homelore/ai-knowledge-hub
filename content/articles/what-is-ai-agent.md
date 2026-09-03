---
title: AI Agent 是什么？从概念到实践
slug: what-is-ai-agent
summary: 理解 AI Agent 的核心概念、架构和主流框架
difficulty: intermediate
read_time: 7
tags: ["agent", "llm"]
---

# AI Agent 是什么？

**AI Agent（智能体）** 是一个能感知环境、自主决策、执行行动来完成目标的 AI 系统。当 Agent 由大语言模型驱动时，它能在自然语言指令下自主规划任务、调用工具、与环境交互。

## Agent 的核心要素

```
用户目标 → [LLM 大脑] → 规划 → 工具调用 → 观察结果 → 思考 → 行动 → 目标达成
```

一个完整的 Agent 系统包含：

1. **大脑（LLM）**：负责理解、推理、决策
2. **记忆**：短期记忆（对话上下文）+ 长期记忆（向量存储）
3. **工具**：搜索引擎、代码执行、API 调用、数据库查询
4. **规划**：将复杂目标拆解为可执行的子任务

## ReAct 模式

ReAct（Reasoning + Acting）是最流行的 Agent 范式：

```text
Thought: 用户想查询上海明天天气，我需要调用天气 API
Action: search_weather("上海", "tomorrow")
Observation: 上海明天多云，最高 32°C，最低 25°C
Thought: 我拿到了天气信息，可以回答用户了
Answer: 上海明天多云，气温 25-32°C，适合外出。
```

## 主流框架对比

| 框架 | 开发方 | 特点 |
|------|--------|------|
| LangGraph | LangChain | 图结构编排，支持复杂流程 |
| AutoGPT | 开源社区 | 早期自主 Agent，全自动化 |
| CrewAI | 开源社区 | 多 Agent 协作框架 |
| OpenAI Assistants | OpenAI | 官方 API，开箱即用 |
| MetaGPT | 开源社区 | 模拟软件公司角色分工 |

## 代码示例（LangGraph）

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain.tools import tool

@tool
def search(query: str) -> str:
    """搜索网络获取信息"""
    # 实际调用搜索 API
    return "搜索结果..."

@tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    return str(eval(expression))

# 构建工作流图
graph = StateGraph(dict)
graph.add_node("agent", call_llm)
graph.add_node("tools", ToolNode([search, calculator]))
graph.add_edge("agent", "tools")
graph.add_edge("tools", "agent")
app = graph.compile()
```

## Agent 的挑战

- **可靠性**：LLM 幻觉可能导致工具误调用
- **成本**：多轮推理消耗大量 token
- **延迟**：多步推理导致响应时间较长
- **调试**：复杂决策链难以追踪和复现

## 应用场景

- **自动化办公**：日程管理、邮件处理
- **数据分析**：自然语言查询数据库、生成报告
- **编程助手**：自动写代码、修 bug、跑测试
- **客服**：多轮对话解决复杂问题

## 总结

AI Agent 代表了 LLM 从"对话工具"到"自主执行者"的进化。虽然仍面临可靠性挑战，但它是通向通用人工智能的重要一步。
