"""回填仓库字段脚本 — 补齐 M1 新增字段，不产生额外的按仓库请求。

复用与每周拉取完全相同的 6 次主题搜索请求，把响应里已存在但历史上没入库的
字段补到 repos 表：
    github_topics（原始 topics）、pushed_at、open_issues、size

只更新为空/缺失的记录，幂等可重复执行。

用法：
    python scripts/backfill_repo_fields.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import FETCH_TOPICS, MAX_REPOS_PER_TOPIC  # noqa: E402
from models.database import get_db_session, init_db  # noqa: E402
from models.repo import Repo  # noqa: E402
from agent.github_client import GitHubClient  # noqa: E402
from agent.filter import map_repo  # noqa: E402


def backfill() -> dict:
    """执行字段回填，返回统计信息。"""
    init_db()

    client = GitHubClient()
    raw_by_full_name: dict[str, dict] = {}

    try:
        for topic_config in FETCH_TOPICS:
            topic_name = topic_config["name"]
            try:
                items = client.search_repositories(
                    topic=topic_name,
                    sort="stars",
                    per_page=min(MAX_REPOS_PER_TOPIC, 100),
                    max_results=MAX_REPOS_PER_TOPIC,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] 主题 {topic_name} 拉取失败: {exc}")
                continue
            print(f"[INFO] 主题 {topic_name}: {len(items)} 个仓库")
            for item in items:
                full_name = item.get("full_name")
                if full_name:
                    raw_by_full_name[full_name] = item
    finally:
        client.close()

    stats = {"total": 0, "topics_filled": 0, "fields_filled": 0, "unmatched": 0}

    with get_db_session() as session:
        repos = session.query(Repo).all()
        stats["total"] = len(repos)

        for repo in repos:
            raw = raw_by_full_name.get(repo.full_name)
            if raw is None:
                stats["unmatched"] += 1
                continue

            mapped = map_repo(raw)
            changed = False

            # topics 缺失或为空数组时回填
            if not repo.github_topics or repo.github_topics in ("[]", "null"):
                topics = mapped.get("github_topics") or "[]"
                if json.loads(topics):
                    repo.github_topics = topics
                    stats["topics_filled"] += 1
                    changed = True

            # 其余字段仅在为空时补齐，避免覆盖更新的数据
            if repo.pushed_at is None and mapped.get("pushed_at") is not None:
                repo.pushed_at = mapped["pushed_at"]
                changed = True
            if not repo.open_issues and mapped.get("open_issues"):
                repo.open_issues = mapped["open_issues"]
                changed = True
            if not repo.size and mapped.get("size"):
                repo.size = mapped["size"]
                changed = True

            if changed:
                stats["fields_filled"] += 1

    filled = stats["topics_filled"]
    total = stats["total"] or 1
    print(
        f"回填完成：共 {stats['total']} 条 | "
        f"topics 补全 {filled} 条（{filled / total:.1%}）| "
        f"其他字段更新 {stats['fields_filled']} 条 | "
        f"未匹配 {stats['unmatched']} 条"
    )
    return stats


if __name__ == "__main__":
    backfill()
