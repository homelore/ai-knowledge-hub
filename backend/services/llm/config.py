"""LLM 接入配置。

环境变量统一在 backend/config.py 里读取（那里已执行 load_dotenv），
本模块只负责组装成不可变的 LLMConfig，并提供：
- model_ref：ARK_ENDPOINT_ID → ARK_MODEL 的回落链
- is_usable：是否具备真正发起调用的条件

配置在进程内只解析一次（get_config 带缓存），请求期不再读环境变量，
避免同一会话中途切换引擎导致理由风格突变、评测数据失真。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

from config import (
    ARK_ALLOW_FULL_CATALOG,
    ARK_API_KEY,
    ARK_BASE_URL,
    ARK_DAILY_CALL_LIMIT,
    ARK_DAILY_TOKEN_LIMIT,
    ARK_ENDPOINT_ID,
    ARK_MAX_RETRIES,
    ARK_MODEL,
    ARK_TEMPERATURE,
    ARK_THINKING,
    ARK_TIMEOUT_CONNECT,
    ARK_TIMEOUT_READ,
    LLM_ENABLED,
)

logger = logging.getLogger(__name__)

# thinking 只允许这三个取值，非法值一律回落 disabled（默认必须关闭推理）
_VALID_THINKING = {"disabled", "enabled", "auto"}


@dataclass(frozen=True)
class LLMConfig:
    """LLM 调用所需的全部配置（不可变）。"""

    enabled: bool = LLM_ENABLED
    api_key: str = ARK_API_KEY
    base_url: str = ARK_BASE_URL
    endpoint_id: str = ARK_ENDPOINT_ID
    model: str = ARK_MODEL
    thinking: str = ARK_THINKING
    temperature: float = ARK_TEMPERATURE
    timeout_connect: float = ARK_TIMEOUT_CONNECT
    timeout_read: float = ARK_TIMEOUT_READ
    max_retries: int = ARK_MAX_RETRIES
    daily_call_limit: int = ARK_DAILY_CALL_LIMIT
    daily_token_limit: int = ARK_DAILY_TOKEN_LIMIT
    allow_full_catalog: bool = ARK_ALLOW_FULL_CATALOG

    def __post_init__(self) -> None:
        thinking = (self.thinking or "").strip().lower()
        if thinking not in _VALID_THINKING:
            thinking = "disabled"
        object.__setattr__(self, "thinking", thinking)
        # base_url 去掉尾部斜杠，避免拼出 //chat/completions
        object.__setattr__(self, "base_url", (self.base_url or "").rstrip("/"))
        object.__setattr__(self, "endpoint_id", (self.endpoint_id or "").strip())
        object.__setattr__(self, "model", (self.model or "").strip())
        object.__setattr__(self, "api_key", (self.api_key or "").strip())

    @property
    def model_ref(self) -> str:
        """模型标识：优先接入点 ID，其次模型名直调。"""
        return self.endpoint_id or self.model

    @property
    def is_usable(self) -> bool:
        """是否具备真正发起调用的条件。开关关闭 / 缺 key / 缺模型标识都不可用。"""
        return bool(self.enabled and self.api_key and self.model_ref)

    def status_warnings(self) -> list[str]:
        """返回配置层面的告警文案（调用方在启动时打日志用）。"""
        if not self.enabled:
            return []  # 主动关闭是正常配置，不告警
        warnings: list[str] = []
        if not self.api_key:
            warnings.append("LLM_ENABLED=true 但 ARK_API_KEY 为空，已自动降级为规则路径")
        if not self.model_ref:
            warnings.append("ARK_ENDPOINT_ID 与 ARK_MODEL 均为空，已自动降级为规则路径")
        if self.thinking != "disabled":
            warnings.append(f"ARK_THINKING={self.thinking}，本场景建议保持 disabled 以降低首字延迟与成本")
        if self.max_retries > 1:
            warnings.append(f"ARK_MAX_RETRIES={self.max_retries}，用户等待路径上重试过多会显著拉高 P95")
        return warnings


def build_config() -> LLMConfig:
    """按当前环境变量构造配置（测试可直接调用，不受缓存影响）。"""
    return LLMConfig()


@lru_cache(maxsize=1)
def get_config() -> LLMConfig:
    """进程内单例配置；首次调用时打印一次配置告警。"""
    cfg = build_config()
    for message in cfg.status_warnings():
        logger.warning(message)
    if cfg.is_usable:
        logger.info("LLM 已启用：model=%s thinking=%s", cfg.model_ref, cfg.thinking)
    return cfg


def reset_config_cache() -> None:
    """清空配置缓存（测试或多环境切换时使用）。"""
    get_config.cache_clear()
