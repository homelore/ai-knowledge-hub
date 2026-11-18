"""豆包（火山方舟 Ark）LLM 接入层。

对外只暴露三样东西，上层不需要了解 HTTP 细节：
- get_config / LLMConfig：配置与可用性判定
- call_ark：传输层（不抛异常，失败一律返回 LLMResult）
- rerank_and_explain：领域函数（失败自动回落模板理由，永远返回同构结果）
"""

from services.llm.ark_client import LLMResult, call_ark
from services.llm.config import LLMConfig, get_config, reset_config_cache
from services.llm.guard import LLMGuard, get_guard
from services.llm.recommend_llm import (
    RecommendationOutcome,
    rerank_and_explain,
    template_recommendations,
)

__all__ = [
    "LLMConfig",
    "get_config",
    "reset_config_cache",
    "LLMResult",
    "call_ark",
    "LLMGuard",
    "get_guard",
    "RecommendationOutcome",
    "rerank_and_explain",
    "template_recommendations",
]
