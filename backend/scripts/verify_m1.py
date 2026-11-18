"""M1 验收脚本 — 校验数据地基是否达标。

验收项：
    1. repo_meta 记录数 = repos 记录数（155）
    2. 5 个标注字段无空值
    3. 原始 topics 覆盖率 ≥ 80%
    4. pushed_at / open_issues / size 填充情况

用法：
    python scripts/verify_m1.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func  # noqa: E402

from models.database import SessionLocal  # noqa: E402
from models.repo import Repo  # noqa: E402
from models.repo_meta import RepoMeta  # noqa: E402

TOPIC_COVERAGE_TARGET = 0.80


def main() -> int:
    session = SessionLocal()
    try:
        repo_count = session.query(func.count(Repo.id)).scalar() or 0
        meta_count = session.query(func.count(RepoMeta.id)).scalar() or 0

        null_count = (
            session.query(func.count(RepoMeta.id))
            .filter(
                (RepoMeta.difficulty.is_(None))
                | (RepoMeta.setup_cost.is_(None))
                | (RepoMeta.run_mode.is_(None))
                | (RepoMeta.needs_gpu.is_(None))
                | (RepoMeta.category.is_(None))
            )
            .scalar()
            or 0
        )

        repos = session.query(Repo).all()
        with_topics = 0
        with_pushed = 0
        with_size = 0
        for repo in repos:
            try:
                topics = json.loads(repo.github_topics or "[]")
            except (ValueError, TypeError):
                topics = []
            if topics:
                with_topics += 1
            if repo.pushed_at is not None:
                with_pushed += 1
            if repo.size:
                with_size += 1

        total = repo_count or 1
        coverage = with_topics / total

        print("=" * 52)
        print("M1 数据地基验收")
        print("=" * 52)
        print(f"repos 记录数              : {repo_count}")
        print(f"repo_meta 记录数          : {meta_count}  "
              f"{'✅' if meta_count == repo_count else '❌ 不相等'}")
        print(f"标注字段空值数            : {null_count}  "
              f"{'✅' if null_count == 0 else '❌ 存在空值'}")
        print(f"原始 topics 覆盖          : {with_topics}/{repo_count} "
              f"({coverage:.1%})  "
              f"{'✅' if coverage >= TOPIC_COVERAGE_TARGET else '❌ 低于 80%'}")
        print(f"pushed_at 填充            : {with_pushed}/{repo_count}")
        print(f"size 填充                 : {with_size}/{repo_count}")
        print("=" * 52)

        passed = (
            meta_count == repo_count
            and null_count == 0
            and coverage >= TOPIC_COVERAGE_TARGET
        )
        print("结论:", "PASS" if passed else "FAIL")
        return 0 if passed else 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
