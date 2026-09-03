---
title: 大语言模型（LLM）入门：从 GPT 到开源生态
slug: llm-explained
summary: 理解大语言模型的基本原理、训练方式和应用场景
difficulty: beginner
read_time: 6
tags: ["llm", "transformer"]
---

# 大语言模型入门

**大语言模型（Large Language Model, LLM）** 是基于 Transformer 架构、在海量文本上训练的神经网络，能够理解和生成人类语言。

## 基本原理

LLM 的核心思想是**下一个 token 预测**：给定前面的文字，预测下一个最可能出现的词。通过在数万亿 token 的语料上反复训练，模型学会了语言的结构、知识和推理能力。

### Transformer 架构

```
输入 → [Embedding] → [位置编码] → [自注意力层 ×N] → [前馈网络] → 输出
```

**自注意力机制（Self-Attention）** 是 Transformer 的灵魂：它让模型在处理每个词时，能够"看到"句子中所有其他词，并根据相关性分配不同权重。

## 训练流程

LLM 的训练通常分三个阶段：

1. **预训练（Pre-training）**：在海量无标注文本上学习语言模式
2. **指令微调（Instruction Tuning）**：用问答对数据让模型学会遵循指令
3. **人类反馈强化学习（RLHF）**：通过人类偏好反馈优化输出质量

## 主流模型

| 模型 | 开发方 | 是否开源 |
|------|--------|----------|
| GPT-4 | OpenAI | 闭源 |
| Claude | Anthropic | 闭源 |
| Llama 3 | Meta | 开源 |
| Qwen | 阿里 | 开源 |
| DeepSeek | 深度求索 | 开源 |

## 应用场景

- **对话助手**：ChatGPT、客服机器人
- **代码生成**：GitHub Copilot、Cursor
- **文档摘要**：自动生成摘要、会议纪要
- **内容创作**：文案、报告、邮件生成
- **知识问答**：结合 RAG 构建企业知识库

## 如何选择？

- **需要极致效果**：选 GPT-4 / Claude
- **需要本地部署**：选 Llama 3 / Qwen / DeepSeek
- **需要中文优化**：选 Qwen / DeepSeek
- **成本敏感**：选开源模型 + 自部署

## 总结

大语言模型正在改变人与软件的交互方式。理解它的原理和边界，是有效利用这项技术的前提。
