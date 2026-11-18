"""仓库标注表模型 — 承接规则推荐所需的 5 个人工/半自动标注字段。

这些字段无法从 GitHub API 直接获得，需要按规则初标 + 人工校对。
所有字段均为 NOT NULL，保证推荐引擎不会拿到空值。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base


class RepoMeta(Base):
    """仓库标注元数据（与 repos 一对一）。"""

    __tablename__ = "repo_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(
        Integer,
        ForeignKey("repos.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ① 上手难度：beginner / intermediate / advanced
    difficulty = Column(String(20), nullable=False)
    # ② 环境搭建成本：low / medium / high
    setup_cost = Column(String(20), nullable=False)
    # ③ 运行方式：local / demo / api-service / research
    run_mode = Column(String(20), nullable=False)
    # ④ GPU 依赖：no / optional / required
    needs_gpu = Column(String(10), nullable=False)
    # ⑤ 主要用途：framework / tool / model / tutorial / platform
    category = Column(String(20), nullable=False)

    # 初标来源：rule=规则生成，manual=人工校对
    source = Column(String(20), nullable=False, default="rule")
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repo = relationship("Repo", back_populates="meta")


# 字段合法取值，供脚本与接口校验使用
DIFFICULTY_VALUES = ("beginner", "intermediate", "advanced")
SETUP_COST_VALUES = ("low", "medium", "high")
RUN_MODE_VALUES = ("local", "demo", "api-service", "research")
NEEDS_GPU_VALUES = ("no", "optional", "required")
CATEGORY_VALUES = ("framework", "tool", "model", "tutorial", "platform")
