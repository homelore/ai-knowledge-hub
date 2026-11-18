"""生成 golden set 标注 — 按 rubric 把 24 条 query 的相关仓库固化为静态标签。

为什么要单独生成：
    M5 的 golden set 需要覆盖不同 star 档位的相关仓库。早期版本只列了头部大项目，
    与产品硬约束（>100k star ≤1、<20k star ≥2）冲突，导致 nDCG 天然不可能达标。
    本脚本按统一 rubric 打分，并把结果写进 JSON 冻结，便于人工校对与版本对比。

rubric（与引擎打分逻辑不同，避免自证）：
    基础分 1 分：命中 query 主题
    难度匹配  +1（difficulty == level）
    偏好匹配  +1（按 preference 检查对应属性）

选择"理想 Top5"时额外套一层可行性约束（与产品硬约束一致）：
    owner 不重复、>100k star 的项目 ≤1 个、<20k star 的项目 ≥2 个。
    否则理想集本身不可达，Recall@5 会被人为封顶在 3/5。

用法：
    python scripts/build_golden_set.py            # 重新生成标签
    python scripts/build_golden_set.py --dry-run  # 只看不写
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.database import SessionLocal  # noqa: E402
from models.repo import Repo
from models.repo_meta import RepoMeta
from models.topic import RepoTopic, Topic

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "eval" / "golden_recommend.json"
MAX_LABELS = 5  # 与 Recall@5 的分母对齐：标注集就是"理想 Top5"，避免召回率被人为封顶
HIGH_STAR = 100_000
LOW_STAR = 20_000
MAX_HIGH_STAR = 1
MIN_LOW_STAR = 2


def _select_feasible(graded: list[tuple], limit: int = MAX_LABELS) -> list[tuple]:
    """挑一组满足产品硬约束的"理想 Top5"。

    打分只看仓库自身属性，可行性只看 star 档位与 owner，不读引擎分数。
    """
    pool = sorted(graded, key=lambda x: (x[2], x[0].stars or 0), reverse=True)

    picked: list[tuple] = []
    owners: set[str] = set()
    high_used = 0
    low_count = 0

    for item in pool:
        if len(picked) >= limit:
            break
        repo = item[0]
        owner = (repo.full_name or "").split("/")[0]
        if owner in owners:
            continue

        is_high = (repo.stars or 0) > HIGH_STAR
        is_low = (repo.stars or 0) < LOW_STAR
        if is_high and high_used >= MAX_HIGH_STAR:
            continue

        remaining = limit - len(picked)
        low_needed = max(0, MIN_LOW_STAR - low_count)
        if not is_low and remaining <= low_needed:
            continue

        picked.append(item)
        owners.add(owner)
        if is_high:
            high_used += 1
        if is_low:
            low_count += 1

    # 兜底：低 star 候选不足时不再强求，避免标注集空着
    for item in pool:
        if len(picked) >= limit:
            break
        repo = item[0]
        owner = (repo.full_name or "").split("/")[0]
        if owner in owners:
            continue
        picked.append(item)
        owners.add(owner)

    return picked


def _grade(repo: Repo, meta: RepoMeta, level: str, preference: str) -> int:
    grade = 1
    if meta.difficulty == level:
        grade += 1

    if preference == "documented":
        if meta.category == "tutorial":
            grade += 1
    elif preference == "runnable":
        if meta.run_mode in ("local", "demo"):
            grade += 1
    elif preference == "easy":
        if meta.difficulty == "beginner" and meta.setup_cost in ("low", "medium"):
            grade += 1
    elif preference == "research":
        if meta.run_mode == "research":
            grade += 1

    return min(grade, 3)


def build(db) -> dict:
    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

    topic_map: dict[str, int] = {
        name: tid for tid, name in db.query(Topic.id, Topic.name)
    }

    for query in data["queries"]:
        # 首次运行时把人工初选的标签留存，方便后续校对对比
        if "curated_relevant" not in query:
            query["curated_relevant"] = query.get("relevant", {})

        profile = query["profile"]
        topics = profile["topics"]
        level = profile["level"]
        preference = profile["preference"]

        topic_ids = [topic_map[t] for t in topics if t in topic_map]
        rows = (
            db.query(Repo, RepoMeta)
            .join(RepoMeta, RepoMeta.repo_id == Repo.id)
            .join(RepoTopic, RepoTopic.repo_id == Repo.id)
            .filter(RepoTopic.topic_id.in_(topic_ids))
            .all()
        )

        graded = []
        for repo, meta in rows:
            graded.append((repo, meta, _grade(repo, meta, level, preference)))

        picked = _select_feasible(graded)
        query["relevant"] = {repo.full_name: grade for repo, _meta, grade in picked}

    data["version"] = "1.1"
    data["description"] = (
        "24 条 golden set：6 个主题 × 4 类典型用户。"
        "rel 为分级相关度（3 很相关 / 2 相关 / 1 勉强），由 scripts/build_golden_set.py "
        "按 rubric 生成后冻结，建议人工抽查校对。"
    )
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 golden set 标注")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        data = build(db)
    finally:
        db.close()

    if args.dry_run:
        for query in data["queries"][:3]:
            print(query["id"], query["profile"])
            for name, grade in query["relevant"].items():
                print(f"   {grade}  {name}")
        return 0

    GOLDEN_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已更新 {len(data['queries'])} 条 query 的标注 → {GOLDEN_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
