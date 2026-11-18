"""LLM 预标注脚本 — 用豆包给 repo_meta 的 5 个字段做预标注。

思路：规则初标 → LLM 复核 → 人工只看"两者不一致"的少量条目。
    - source='manual' 的记录永不覆盖（人工优先）
    - LLM 不可用 / 输出不合法时保持原标注，不写脏数据
    - 跑完自动导出 eval/annotate_conflicts.csv，只列冲突项

用法：
    python scripts/llm_annotate.py --dry-run          # 只打印，不写库（建议先用 --limit 5 试）
    python scripts/llm_annotate.py --limit 5
    python scripts/llm_annotate.py                    # 全量

前置条件：.env 里配置 LLM_ENABLED=true、ARK_API_KEY、ARK_MODEL（或 ARK_ENDPOINT_ID）。
"""

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

import httpx

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
from services.llm.ark_client import call_ark  # noqa: E402
from services.llm.config import build_config  # noqa: E402

CONFLICT_PATH = Path(__file__).resolve().parent.parent / "eval" / "annotate_conflicts.csv"

FIELDS = ("difficulty", "setup_cost", "run_mode", "needs_gpu", "category")
VALID = {
    "difficulty": DIFFICULTY_VALUES,
    "setup_cost": SETUP_COST_VALUES,
    "run_mode": RUN_MODE_VALUES,
    "needs_gpu": NEEDS_GPU_VALUES,
    "category": CATEGORY_VALUES,
}

_SYSTEM_PROMPT = "你是开源 AI 项目的标注员。只输出一个 JSON 对象，不要输出解释、不要加代码块。"

_USER_PROMPT = """给下面这个 GitHub 项目打 5 个标签，用于给初学者推荐项目。

项目：{full_name}
简介：{description}
语言：{language}
star：{stars}
原始 topics：{topics}

字段取值（必须严格用下列英文枚举值）：
- difficulty（上手难度）：beginner / intermediate / advanced
  beginner=照着 README 十几分钟能跑起来；intermediate=要装依赖、配环境、有一定调试；advanced=要读源码、改结构、理解论文或分布式
- setup_cost（环境搭建成本）：low / medium / high
  low=一条命令或直接打开网页；medium=要装依赖或申请 API key；high=要 GPU、大模型权重、集群或复杂配置
- run_mode（主要运行方式）：local / demo / api-service / research
  local=本地跑起来；demo=在线体验或示例页；api-service=对外提供 API 服务；research=论文复现/训练实验
- needs_gpu（GPU 依赖）：no / optional / required
- category（主要用途）：framework / tool / model / tutorial / platform
  framework=给人搭应用的框架；tool=解决具体问题的工具；model=模型或权重；tutorial=教程/课程/资料合集；platform=完整平台或产品

输出格式（只输出这一个 JSON）：
{{"difficulty": "...", "setup_cost": "...", "run_mode": "...", "needs_gpu": "...", "category": "...", "confidence": 0.0, "reason": "20 字以内中文理由"}}

confidence 表示你对这次标注的整体把握，0 到 1 之间。"""

_RETRY_HINT = "上一次输出不是合法 JSON 或取值不在枚举内。请只输出一个严格符合格式的 JSON 对象。"


def _load_targets(limit: int) -> list[dict]:
    """读取待标注仓库（跳过 source=manual）。"""
    items: list[dict] = []
    with get_db_session() as session:
        rows = (
            session.query(Repo, RepoMeta)
            .join(RepoMeta, RepoMeta.repo_id == Repo.id)
            .order_by(Repo.stars.desc())
            .all()
        )
        for repo, meta in rows:
            if meta.source == "manual":
                continue
            try:
                topics = ", ".join(json.loads(repo.github_topics or "[]")[:12])
            except (ValueError, TypeError):
                topics = ""
            items.append({
                "repo_id": repo.id,
                "full_name": repo.full_name,
                "description": (repo.description or "").strip(),
                "language": repo.language or "未知",
                "stars": repo.stars or 0,
                "topics": topics or "无",
                "current": {field: getattr(meta, field) for field in FIELDS},
                "source": meta.source,
            })
            if limit and len(items) >= limit:
                break
    return items


def _build_messages(item: dict) -> list[dict]:
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _USER_PROMPT.format(**item)},
    ]


def _parse_payload(raw: str) -> tuple[dict | None, str]:
    """解析模型输出；返回 (payload, 错误原因)。"""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None, "输出里没有 JSON 对象"
    try:
        data = json.loads(text[start:end + 1])
    except ValueError as exc:
        return None, f"JSON 解析失败：{exc}"
    if not isinstance(data, dict):
        return None, "输出不是 JSON 对象"

    cleaned: dict = {}
    for field in FIELDS:
        value = str(data.get(field, "")).strip().lower()
        if value not in VALID[field]:
            return None, f"{field}={value!r} 不在枚举内"
        cleaned[field] = value

    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    cleaned["confidence"] = min(max(confidence, 0.0), 1.0)
    cleaned["reason"] = str(data.get("reason", "")).strip()[:80]
    return cleaned, ""


async def _annotate_one(item: dict, cfg, client: httpx.AsyncClient) -> dict:
    """单条标注；不合法重试一次，仍失败则保留原标注。"""
    result = {
        "repo_id": item["repo_id"],
        "full_name": item["full_name"],
        "before": item["current"],
        "after": None,
        "confidence": 0.0,
        "reason": "",
        "error": "",
    }

    messages = _build_messages(item)
    for attempt in range(2):
        resp = await call_ark(
            messages,
            json_mode=True,
            max_tokens=300,
            temperature=0.0,
            cfg=cfg,
            client=client,
        )
        if not resp.ok:
            result["error"] = f"调用失败：{resp.error_kind}"
            return result

        payload, err = _parse_payload(resp.raw_text)
        if payload is not None:
            result["after"] = {field: payload[field] for field in FIELDS}
            result["confidence"] = payload["confidence"]
            result["reason"] = payload["reason"]
            return result

        if attempt == 1:
            result["error"] = err
            return result
        messages = messages + [
            {"role": "assistant", "content": resp.raw_text[:400]},
            {"role": "user", "content": _RETRY_HINT},
        ]

    return result


def _write_results(results: list[dict], dry_run: bool) -> dict:
    stats = {"updated": 0, "skipped": 0, "failed": 0}
    if dry_run:
        for item in results:
            stats["updated" if item["after"] else "failed"] += 1
        return stats

    with get_db_session() as session:
        for item in results:
            if not item["after"]:
                stats["failed"] += 1
                continue
            meta = (
                session.query(RepoMeta)
                .filter(RepoMeta.repo_id == item["repo_id"])
                .first()
            )
            if meta is None or meta.source == "manual":
                stats["skipped"] += 1
                continue
            for field in FIELDS:
                setattr(meta, field, item["after"][field])
            meta.source = "llm"
            meta.notes = f"LLM(conf={item['confidence']:.2f}): {item['reason']}"
            stats["updated"] += 1
    return stats


def _export_conflicts(results: list[dict], path: Path = CONFLICT_PATH) -> int:
    """只导出 LLM 与原有标注不一致的行，作为人工复核清单。"""
    rows = [
        item for item in results
        if item["after"] and any(
            item["before"][field] != item["after"][field] for field in FIELDS
        )
    ]
    if not rows:
        print("没有冲突项，无需人工复核")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["repo_id", "full_name"]
    for field in FIELDS:
        columns += [f"{field}_old", f"{field}_new"]
    columns += ["confidence", "reason"]

    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for item in rows:
            row = {"repo_id": item["repo_id"], "full_name": item["full_name"]}
            for field in FIELDS:
                row[f"{field}_old"] = item["before"][field]
                row[f"{field}_new"] = item["after"][field]
            row["confidence"] = f"{item['confidence']:.2f}"
            row["reason"] = item["reason"]
            writer.writerow(row)

    print(f"冲突项 {len(rows)} 条 → {path}（人工只需复核这张表）")
    return len(rows)


async def _run(items: list[dict], cfg, concurrency: int) -> list[dict]:
    sem = asyncio.Semaphore(max(concurrency, 1))
    timeout = httpx.Timeout(
        connect=cfg.timeout_connect, read=cfg.timeout_read, write=10.0, pool=5.0
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        async def worker(item: dict) -> dict:
            async with sem:
                return await _annotate_one(item, cfg, client)

        return list(await asyncio.gather(*(worker(i) for i in items)))


def _print_results(results: list[dict]) -> None:
    """dry-run 时逐条打印标注结果，便于人工判断质量。"""
    for item in results:
        after = item["after"]
        if not after:
            print(f"\n{item['full_name']}  [失败] {item['error']}")
            continue
        print(f"\n{item['full_name']}  conf={item['confidence']:.2f}")
        for field in FIELDS:
            old = item["before"][field]
            new = after[field]
            mark = "  ≠" if old != new else ""
            print(f"  {field:<12} {old:<13} → {new}{mark}")
        if item["reason"]:
            print(f"  reason       {item['reason']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="用 LLM 给仓库做 5 字段预标注")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 条（按 star 降序）")
    parser.add_argument("--concurrency", type=int, default=4, help="并发数，默认 4")
    parser.add_argument("--dry-run", action="store_true", help="不写库，只打印结果")
    parser.add_argument("--file", default=str(CONFLICT_PATH), help="冲突表路径")
    args = parser.parse_args()

    init_db()

    items = _load_targets(args.limit)
    if not items:
        print("没有待标注仓库（可能全部已是 manual）")
        return 0

    cfg = build_config()
    if not cfg.is_usable:
        print(
            "LLM 不可用：请检查 .env 中的 LLM_ENABLED / ARK_API_KEY / ARK_MODEL。\n"
            "未配置时不会调用模型，也不会修改任何标注。"
        )
        return 1

    print(f"待标注 {len(items)} 条，模型 {cfg.model_ref}，并发 {args.concurrency}")
    results = asyncio.run(_run(items, cfg, args.concurrency))

    ok = sum(1 for r in results if r["after"])
    print(f"模型返回合法标注 {ok}/{len(results)} 条")
    for item in results:
        if item["error"]:
            print(f"  - {item['full_name']}: {item['error']}")

    if args.dry_run:
        _print_results(results)

    stats = _write_results(results, dry_run=args.dry_run)
    prefix = "[dry-run] " if args.dry_run else ""
    print(
        f"{prefix}写库：更新 {stats['updated']} | 跳过 {stats['skipped']} | "
        f"失败 {stats['failed']}"
    )

    if not args.dry_run:
        _export_conflicts(results, Path(args.file))
    else:
        conflicts = sum(
            1 for item in results
            if item["after"] and any(
                item["before"][f] != item["after"][f] for f in FIELDS
            )
        )
        print(f"[dry-run] 预计产生冲突项 {conflicts} 条")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
