"""仓库标注脚本 — 为规则推荐引擎生成 5 个标注字段。

标注字段（全部非空，供推荐引擎直接使用）：
    difficulty    上手难度   beginner / intermediate / advanced
    setup_cost    搭建成本   low / medium / high
    run_mode      运行方式   local / demo / api-service / research
    needs_gpu     GPU 依赖   no / optional / required
    category      主要用途   framework / tool / model / tutorial / platform

采用确定性关键词规则初标，幂等执行：
    - 默认只补充缺失标注，不覆盖已有记录
    - 加 --force 可全量重算（人工校对过的 manual 记录仍会保留，除非一并加 --force-manual）

用法：
    python scripts/annotate_repos.py
    python scripts/annotate_repos.py --force
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.database import get_db_session, init_db  # noqa: E402
from models.repo import Repo  # noqa: E402
from models.repo_meta import RepoMeta  # noqa: E402

# ── 关键词规则表（顺序即优先级，命中即停）────────────────

_CATEGORY_RULES = [
    ("tutorial", (
        "awesome", "tutorial", "course", "book", "guide", "handbook",
        "learning", "roadmap", "cheatsheet", "papers", "curated list",
        "from scratch", "examples", "cookbook",
    )),
    ("platform", (
        "platform", "cloud", "dashboard", "web ui", "studio", "console",
        "saas", "workflow builder", "low-code", "no-code",
    )),
    ("model", (
        "model", "weights", "checkpoint", "pretrained", "pre-trained",
        "diffusion", "llm", "gpt", "llama", "bert", "whisper", "stable diffusion",
    )),
    ("framework", (
        "framework", "engine", "runtime", "orchestrat", "pipeline",
        "agent", "rag", "serving", "inference server", "library",
    )),
]

_DIFFICULTY_BEGINNER = (
    "awesome", "tutorial", "course", "beginner", "simple", "minimal",
    "easy", "getting started", "quickstart", "demo", "playground", "guide",
)
_DIFFICULTY_ADVANCED = (
    "distributed", "kubernetes", "cluster", "from scratch", "production",
    "enterprise", "large-scale", "research", "training", "infrastructure",
    "compiler", "kernel", "high-performance",
)

_SETUP_HIGH = (
    "kubernetes", "cluster", "cuda", "gpu", "train", "distributed",
    "multi-node", "hadoop", "spark", "docker swarm", "terraform",
)
_SETUP_LOW = (
    "awesome", "tutorial", "course", "book", "curated", "papers",
    "roadmap", "cheatsheet",
)

_RUN_MODE_DEMO = (
    "demo", "playground", "web ui", "gradio", "streamlit", "notebook",
    "colab", "interactive", "chat ui",
)
_RUN_MODE_API = (
    "api", "server", "service", "serving", "endpoint", "proxy",
    "gateway", "backend", "openai-compatible",
)
_RUN_MODE_RESEARCH = (
    "research", "paper", "benchmark", "dataset", "experiment", "reproduce",
)

_GPU_REQUIRED = (
    "cuda only", "gpu required", "requires gpu", "pre-train", "pretraining",
    "train from scratch", "multi-gpu", "distributed training",
)
_GPU_OPTIONAL = (
    "cuda", "gpu", "inference", "llm", "diffusion", "llama", "transformer",
    "vllm", "quantization",
)


def _text_of(repo: Repo) -> str:
    """拼接用于规则匹配的文本（名称 + 描述 + topics）。"""
    topics = ""
    if repo.github_topics:
        try:
            topics = " ".join(json.loads(repo.github_topics))
        except (ValueError, TypeError):
            topics = repo.github_topics
    return f"{repo.full_name} {repo.name} {repo.description or ''} {topics}".lower()


def _first_match(text: str, rules, default: str) -> str:
    """返回第一条命中的规则值，都不命中时返回默认值。"""
    for value, keywords in rules:
        if any(k in text for k in keywords):
            return value
    return default


def _has(text: str, keywords) -> bool:
    return any(k in text for k in keywords)


def annotate_repo(repo: Repo) -> dict:
    """对单个仓库执行规则标注，返回 5 个字段的字典。"""
    text = _text_of(repo)

    category = _first_match(text, _CATEGORY_RULES, "tool")

    if _has(text, _DIFFICULTY_BEGINNER) or category == "tutorial":
        difficulty = "beginner"
    elif _has(text, _DIFFICULTY_ADVANCED):
        difficulty = "advanced"
    else:
        difficulty = "intermediate"

    if _has(text, _SETUP_HIGH):
        setup_cost = "high"
    elif _has(text, _SETUP_LOW):
        setup_cost = "low"
    else:
        setup_cost = "medium"

    if _has(text, _RUN_MODE_DEMO):
        run_mode = "demo"
    elif _has(text, _RUN_MODE_API):
        run_mode = "api-service"
    elif _has(text, _RUN_MODE_RESEARCH):
        run_mode = "research"
    else:
        run_mode = "local"

    if _has(text, _GPU_REQUIRED):
        needs_gpu = "required"
    elif _has(text, _GPU_OPTIONAL):
        needs_gpu = "optional"
    else:
        needs_gpu = "no"

    return {
        "difficulty": difficulty,
        "setup_cost": setup_cost,
        "run_mode": run_mode,
        "needs_gpu": needs_gpu,
        "category": category,
    }


def run_annotate(force: bool = False, force_manual: bool = False) -> dict:
    """遍历全部仓库执行标注。

    Args:
        force: 是否覆盖已有的规则标注
        force_manual: 是否连人工校对（source=manual）的记录一起覆盖

    Returns:
        统计信息 {"total": n, "created": n, "updated": n, "skipped": n}
    """
    init_db()
    stats = {"total": 0, "created": 0, "updated": 0, "skipped": 0}

    with get_db_session() as session:
        repos = session.query(Repo).all()
        stats["total"] = len(repos)

        for repo in repos:
            values = annotate_repo(repo)
            meta = (
                session.query(RepoMeta)
                .filter(RepoMeta.repo_id == repo.id)
                .first()
            )

            if meta is None:
                session.add(RepoMeta(repo_id=repo.id, source="rule", **values))
                stats["created"] += 1
                continue

            if meta.source == "manual" and not force_manual:
                stats["skipped"] += 1
                continue

            if not force:
                stats["skipped"] += 1
                continue

            for key, value in values.items():
                setattr(meta, key, value)
            if meta.source == "manual" and force_manual:
                meta.source = "rule"
            stats["updated"] += 1

    print(
        f"标注完成：共 {stats['total']} 条 | "
        f"新建 {stats['created']} | 更新 {stats['updated']} | 跳过 {stats['skipped']}"
    )
    return stats


def main():
    parser = argparse.ArgumentParser(description="为仓库生成 5 个标注字段")
    parser.add_argument("--force", action="store_true", help="覆盖已有规则标注")
    parser.add_argument(
        "--force-manual", action="store_true", help="连人工标注一起覆盖"
    )
    args = parser.parse_args()
    run_annotate(force=args.force, force_manual=args.force_manual)


if __name__ == "__main__":
    main()
