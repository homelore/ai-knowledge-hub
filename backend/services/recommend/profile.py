"""用户画像 Schema 与固定 3 问 — 无 LLM 时也能完成完整对话。

对话分三轮，全部为结构化选项，前端直接渲染选项即可：
    1. 方向   topics     多选（config.FETCH_TOPICS）
    2. 水平   level      beginner / intermediate / advanced
    3. 偏好   preference easy / runnable / documented / research

同时提供 rule_parse()：当用户输入自由文本（而非选项）时，用关键词兜底推断，
保证无 LLM 时对话不会卡死。
"""

from dataclasses import dataclass, field, asdict
from typing import Optional

from config import FETCH_TOPICS

LEVEL_VALUES = ("beginner", "intermediate", "advanced")
PREFERENCE_VALUES = ("easy", "runnable", "documented", "research")

LEVEL_LABELS = {
    "beginner": "刚入门，能跑通示例就行",
    "intermediate": "写过一些代码，想动手改点东西",
    "advanced": "有经验，想看架构和进阶用法",
}

PREFERENCE_LABELS = {
    "easy": "最容易上手",
    "runnable": "能立刻跑起来看到效果",
    "documented": "文档和教程齐全",
    "research": "偏前沿研究、能学到新东西",
}


@dataclass
class UserProfile:
    """推荐所需的最小用户画像。"""

    topics: list[str] = field(default_factory=list)
    level: str = "beginner"
    preference: str = "easy"
    languages: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        return bool(self.topics) and self.level in LEVEL_VALUES \
            and self.preference in PREFERENCE_VALUES

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "UserProfile":
        data = data or {}
        topics = [t for t in (data.get("topics") or []) if t]
        level = data.get("level") if data.get("level") in LEVEL_VALUES else "beginner"
        pref = data.get("preference")
        preference = pref if pref in PREFERENCE_VALUES else "easy"
        return cls(
            topics=topics,
            level=level,
            preference=preference,
            languages=list(data.get("languages") or []),
            keywords=list(data.get("keywords") or []),
        )


def next_question(profile: UserProfile, answered: set[str]) -> Optional[dict]:
    """基于已作答的问题集合，返回下一个待答问题；全部答完返回 None。"""
    if "topics" not in answered or not profile.topics:
        return _topic_question()
    if "level" not in answered:
        return {
            "id": "level",
            "type": "single",
            "text": "你的编程经验大概是什么水平？",
            "options": [
                {"value": k, "label": LEVEL_LABELS[k], "description": ""}
                for k in LEVEL_VALUES
            ],
        }
    if "preference" not in answered:
        return {
            "id": "preference",
            "type": "single",
            "text": "你更看重哪一点？",
            "options": [
                {"value": k, "label": PREFERENCE_LABELS[k], "description": ""}
                for k in PREFERENCE_VALUES
            ],
        }
    return None


def _topic_question() -> dict:
    return {
        "id": "topics",
        "type": "multi",
        "text": "你最想了解哪个方向？（可多选）",
        "options": [
            {
                "value": t["name"],
                "label": f"{t.get('icon', '')} {t['display_name']}".strip(),
                "description": t.get("description", ""),
            }
            for t in FETCH_TOPICS
        ],
    }


# ── 自由文本兜底解析（无 LLM 时使用）─────────────────────

_TOPIC_KEYWORDS = {
    "llm": ("大模型", "语言模型", "llm", "gpt", "llama", "对话", "提示词", "prompt"),
    "rag": ("rag", "检索", "知识库", "向量", "embedding", "检索增强"),
    "agent": ("agent", "智能体", "自动化", "工具调用", "多智能体"),
    "transformer": ("transformer", "注意力", "attention", "架构原理"),
    "diffusion": ("diffusion", "扩散", "画图", "图像生成", "stable diffusion"),
    "mlops": ("mlops", "部署", "运维", "监控", "推理服务"),
}

_LEVEL_KEYWORDS = {
    "beginner": ("零基础", "入门", "刚开始", "新手", "没写过", "初学"),
    "intermediate": ("写过", "做过项目", "有点基础", "熟悉", "中等"),
    "advanced": ("资深", "有经验", "架构", "进阶", "高级"),
}

_PREFERENCE_KEYWORDS = {
    "easy": ("简单", "容易", "上手", "快速"),
    "runnable": ("跑起来", "能用", "效果", "直接", "立刻"),
    "documented": ("文档", "教程", "例子", "示例"),
    "research": ("研究", "前沿", "论文", "原理", "深入"),
}


def rule_parse(message: str) -> dict:
    """从自由文本中做关键词兜底解析，返回部分画像字段。"""
    text = (message or "").lower()
    result: dict = {}

    topics = [
        name for name, words in _TOPIC_KEYWORDS.items()
        if any(w in text for w in words)
    ]
    if topics:
        result["topics"] = topics

    for level, words in _LEVEL_KEYWORDS.items():
        if any(w in text for w in words):
            result["level"] = level
            break

    for pref, words in _PREFERENCE_KEYWORDS.items():
        if any(w in text for w in words):
            result["preference"] = pref
            break

    return result
