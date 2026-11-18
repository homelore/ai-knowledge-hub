"""人工标注辅助脚本 — CSV 导出 / 导入，用于校对 repo_meta 的 5 个标注字段。

流程：
    1. python scripts/manual_annotate.py --export
       生成 eval/annotate_sheet.csv（UTF-8 BOM，Excel 打开不乱码）
    2. 在 Excel 里改 difficulty / setup_cost / run_mode / needs_gpu / category
       如果某行标注本来就对、无需修改，就把 reviewed 列填 y，表示"已校对"
    3. python scripts/manual_annotate.py --import
       校验取值后回写，并把 source 置为 manual
       （之后 annotate_repos.py --force 不会覆盖人工标注）

合法取值：
    difficulty   beginner / intermediate / advanced
    setup_cost   low / medium / high
    run_mode     local / demo / api-service / research
    needs_gpu    no / optional / required
    category     framework / tool / model / tutorial / platform

用法：
    python scripts/manual_annotate.py --export
    python scripts/manual_annotate.py --import
    python scripts/manual_annotate.py --import --dry-run
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.database import get_db_session, init_db  # noqa: E402
from models.repo import Repo  # noqa: E402
from models.repo_meta import (  # noqa: E402
    CATEGORY_VALUES,
    DIFFICULTY_VALUES,
    NEEDS_GPU_VALUES,
    RUN_MODE_VALUES,
    SETUP_COST_VALUES,
    RepoMeta,
)

SHEET_PATH = Path(__file__).resolve().parent.parent / "eval" / "annotate_sheet.csv"

FIELDS = ("difficulty", "setup_cost", "run_mode", "needs_gpu", "category")
VALID = {
    "difficulty": DIFFICULTY_VALUES,
    "setup_cost": SETUP_COST_VALUES,
    "run_mode": RUN_MODE_VALUES,
    "needs_gpu": NEEDS_GPU_VALUES,
    "category": CATEGORY_VALUES,
}

COLUMNS = (
    "repo_id", "full_name", "stars", "language",
    *FIELDS,
    "reviewed", "source", "notes", "description",
)

_YES = {"y", "yes", "1", "true", "是", "已校对"}


def export_rows(path: Path) -> int:
    """把全部仓库及其标注导出为 CSV，便于 Excel 校对。"""
    path.parent.mkdir(parents=True, exist_ok=True)

    with get_db_session() as session:
        rows = (
            session.query(Repo, RepoMeta)
            .join(RepoMeta, RepoMeta.repo_id == Repo.id)
            .order_by(Repo.stars.desc())
            .all()
        )

        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=COLUMNS)
            writer.writeheader()
            for repo, meta in rows:
                writer.writerow({
                    "repo_id": repo.id,
                    "full_name": repo.full_name,
                    "stars": repo.stars or 0,
                    "language": repo.language or "",
                    **{field: getattr(meta, field) for field in FIELDS},
                    "reviewed": "y" if meta.source == "manual" else "",
                    "source": meta.source,
                    "notes": meta.notes or "",
                    "description": (repo.description or "").replace("\n", " "),
                })

    print(f"已导出 {len(rows)} 条 → {path}")
    print("改完执行：python scripts/manual_annotate.py --import")
    return len(rows)


def import_rows(path: Path, dry_run: bool = False) -> int:
    """把 CSV 中的标注回写到 repo_meta，source 置为 manual。"""
    if not path.exists():
        print(f"[ERROR] 找不到文件：{path}，先执行 --export")
        return 1

    changed = created = same = 0
    errors: list[str] = []

    with path.open("r", encoding="utf-8-sig", newline="") as fh, \
            get_db_session() as session:
        for lineno, row in enumerate(csv.DictReader(fh), start=2):
            raw_id = (row.get("repo_id") or "").strip()
            if not raw_id.isdigit():
                errors.append(f"第 {lineno} 行：repo_id 非法（{raw_id!r}）")
                continue
            repo_id = int(raw_id)

            values = {}
            bad = False
            for field in FIELDS:
                value = (row.get(field) or "").strip()
                if value not in VALID[field]:
                    errors.append(
                        f"第 {lineno} 行：{field}={value!r} 不合法，"
                        f"可选 {'/'.join(VALID[field])}"
                    )
                    bad = True
                values[field] = value
            if bad:
                continue

            meta = (
                session.query(RepoMeta)
                .filter(RepoMeta.repo_id == repo_id)
                .first()
            )
            notes = (row.get("notes") or "").strip() or None
            reviewed = (row.get("reviewed") or "").strip().lower() in _YES

            if meta is None:
                if not session.get(Repo, repo_id):
                    errors.append(f"第 {lineno} 行：repo_id={repo_id} 不存在")
                    continue
                session.add(RepoMeta(repo_id=repo_id, source="manual",
                                     notes=notes, **values))
                created += 1
                continue

            diff = [f for f in FIELDS if getattr(meta, f) != values[f]]
            if not diff and not reviewed:
                # 值没改也没打 reviewed 标记，视为未校对，保持规则标注不动
                same += 1
                continue

            for field in FIELDS:
                setattr(meta, field, values[field])
            meta.source = "manual"
            meta.notes = notes
            changed += 1

        if dry_run:
            session.rollback()

    prefix = "[dry-run] " if dry_run else ""
    print(
        f"{prefix}导入完成：修改 {changed} | 新建 {created} | 未变化 {same} | "
        f"错误 {len(errors)}"
    )
    if errors:
        print("以下行被跳过：")
        for msg in errors[:30]:
            print("  -", msg)
        if len(errors) > 30:
            print(f"  … 另有 {len(errors) - 30} 条")

    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="人工校对 repo_meta 标注")
    parser.add_argument("--export", action="store_true", help="导出 CSV")
    parser.add_argument("--import", dest="do_import", action="store_true",
                        help="从 CSV 导入并置 source=manual")
    parser.add_argument("--file", default=str(SHEET_PATH), help="CSV 路径")
    parser.add_argument("--dry-run", action="store_true", help="只校验不回写")
    args = parser.parse_args()

    if not args.export and not args.do_import:
        parser.print_help()
        return 1

    init_db()
    path = Path(args.file)
    if args.export:
        export_rows(path)
    if args.do_import:
        return import_rows(path, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
