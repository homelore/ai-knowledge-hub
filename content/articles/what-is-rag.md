---
title: 什么是 RAG？检索增强生成完全指南
slug: what-is-rag
summary: 从原理到实践，理解 RAG 如何让大语言模型"查资料"再回答
difficulty: intermediate
read_time: 8
tags: ["rag", "llm"]
---

# 什么是 RAG？

**RAG（Retrieval-Augmented Generation，检索增强生成）** 是一种将外部知识检索与大语言模型生成相结合的技术架构。它让模型能够"查阅资料"后再回答，而非仅依赖训练时记住的知识。

## 为什么需要 RAG？

大语言模型（LLM）存在几个固有局限：

1. **知识截止**：模型训练数据有截止日期，无法获取最新信息
2. **幻觉问题**：模型可能生成看似合理但实际错误的内容
3. **领域盲区**：对私有数据、内部文档等训练集外内容缺乏了解

RAG 通过引入外部知识源，有效缓解了这些问题。

## RAG 的工作流程

```
用户提问 → 向量化 → 检索相关文档 → 拼接提示词 → LLM 生成回答
```

### 步骤详解

1. **文档预处理**：将知识库文档切分为语义完整的文本块（chunk）
2. **向量化**：用 Embedding 模型将文本块转为高维向量
3. **向量存储**：将向量存入向量数据库（如 FAISS、Chroma、Pinecone）
4. **检索**：用户提问同样向量化，通过相似度搜索找到最相关的文档块
5. **生成**：将检索到的文档块拼接到提示词中，交给 LLM 生成最终回答

## 代码示例

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

# 1. 文档切分
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# 2. 向量化 + 存储
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 3. 构建检索链
qa = RetrievalQA.from_chain_type(
    llm=OpenAI(temperature=0),
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3},
)

# 4. 提问
answer = qa.run("什么是注意力机制？")
```

## RAG vs 微调

| 维度 | RAG | 微调 |
|------|-----|------|
| 知识更新 | 实时更新，改数据库即可 | 需重新训练 |
| 计算成本 | 低（检索+推理） | 高（训练成本） |
| 可解释性 | 高（可溯源到文档） | 低（知识内化在权重中） |
| 适用场景 | 事实性问答、文档检索 | 风格模仿、特定任务 |

## 总结

RAG 是目前让 LLM 接入外部知识最实用的方案。它平衡了成本与效果，是构建企业级 AI 应用的首选架构。
