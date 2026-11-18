"""M5 评测脚本 — 24 条 golden set 一键出报告。

指标：
    nDCG@5    分级相关度（0-1，越高越好）
    Recall@5  相关仓库（rel≥2）的召回率
    理由支持率  推荐理由里出现的数字是否都能在仓库事实上找到依据

用法：
    python scripts/eval_recommend.py
    python scripts/eval_recommend.py --limit 5 --out eval/report_recommend.json
"""

import argparse
import asyncio
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.database import SessionLocal  # noqa: E402
from models.repo import Repo  # noqa: E402
from services.llm.config import get_config  # noqa: E402
from services.recommend import engine as rule_engine  # noqa: E402
from services.recommend.llm_orchestrator import recommend as llm_recommend  # noqa: E402
from services.recommend.profile import UserProfile  # noqa: E402

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "eval" / "golden_recommend.json"

TARGET_NDCG = 0.70
TARGET_RECALL = 0.60
TARGET_UNSUPPORTED = 0.05
LLM_GAIN_RATIO = 1.10

_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _dcg(gains: list[int]) -> float:
    return sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(gains))


def _ndcg(predicted: list[int], all_grades: list[int]) -> float:
    ideal = sorted(all_grades, reverse=True)[:len(predicted)]
    idcg = _dcg(ideal)
    return _dcg(predicted) / idcg if idcg else 0.0


def _reason_supported(reason: str, item: dict) -> bool:
    """校验理由中的数字是否有事实依据（排除仓库名本身含的数字）。"""
    text = reason.replace(item.get("full_name") or "", "")
    facts = {
        float(item.get("stars") or 0),
        float(item.get("forks") or 0),
        float(item.get("pushed_days") or 0),
        float(item.get("weekly_star_gain") or 0),
    }
    for token in _NUM_RE.findall(text):
        try:
            value = float(token.replace(",", ""))
        except ValueError:
            continue
        if value not in facts:
            return False
    return True


def _evaluate(results_by_query: dict, queries: list[dict],
              name_to_id: dict[str, int]) -> dict:
    """计算整体指标。"""
    ndcgs: list[float] = []
    recalls: list[float] = []
    unsupported = 0
    total_items = 0
    details = []

    for query in queries:
        relevant = query["relevant"]
        results = results_by_query.get(query["id"], [])
        grades = [int(relevant.get(r["full_name"], 0)) for r in results]
        all_grades = [int(g) for g in relevant.values()]

        ndcg = _ndcg(grades, all_grades)
        ndcgs.append(ndcg)

        relevant_set = {n for n, g in relevant.items() if int(g) >= 2}
        hit = {r["full_name"] for r in results} & relevant_set
        recall = len(hit) / len(relevant_set) if relevant_set else 0.0
        recalls.append(recall)

        bad = 0
        for item in results:
            total_items += 1
            if not _reason_supported(item.get("reason") or "", item):
                bad += 1
                unsupported += 1

        details.append({
            "id": query["id"],
            "profile": query["profile"],
            "ndcg@5": round(ndcg, 4),
            "recall@5": round(recall, 4),
            "retrieved": [r["full_name"] for r in results],
            "grades": grades,
            "unsupported_reasons": bad,
        })

    return {
        "queries": len(queries),
        "ndcg@5": round(sum(ndcgs) / len(ndcgs), 4) if ndcgs else 0.0,
        "recall@5": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
        "unsupported_reason_rate": round(unsupported / total_items, 4) if total_items else 0.0,
        "details": details,
    }


def _run_rule(db, queries: list[dict]) -> dict:
    outputs = {}
    for query in queries:
        profile = UserProfile.from_dict(query["profile"])
        outputs[query["id"]] = rule_engine.recommend(db, profile, set())
    return outputs


def _run_llm(db, queries: list[dict]) -> dict:
    outputs = {}
    for query in queries:
        profile = UserProfile.from_dict(query["profile"])
        outcome = asyncio.run(
            llm_recommend(db, profile, set(), use_cache=False)
        )
        outputs[query["id"]] = outcome["recommendations"]
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="推荐效果评测")
    parser.add_argument("--out", default="eval/report_recommend.json")
    parser.add_argument("--skip-llm", action="store_true", help="只评测规则版")
    args = parser.parse_args()

    data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    queries = data["queries"]
    name_to_id = {}

    db = SessionLocal()
    try:
        name_to_id = {name: rid for rid, name in db.query(Repo.id, Repo.full_name)}
        unknown = {
            name for q in queries for name in q["relevant"]
            if name not in name_to_id
        }
        if unknown:
            print(f"[WARN] golden set 中 {len(unknown)} 个仓库不在库中，将被忽略：")
            for name in sorted(unknown):
                print("   -", name)

        rule_result = _evaluate(_run_rule(db, queries), queries, name_to_id)

        llm_result = None
        cfg = get_config()
        if not args.skip_llm and cfg.is_usable:
            print("[INFO] 检测到可用 LLM 配置，同时评测 LLM 版…")
            llm_result = _evaluate(_run_llm(db, queries), queries, name_to_id)
    finally:
        db.close()

    print("=" * 56)
    print("M5 推荐效果评测（24 条 golden set）")
    print("=" * 56)
    print(f"{'指标':<18}{'规则版':<12}{'LLM 版':<12}")
    print(f"{'nDCG@5':<18}{rule_result['ndcg@5']:<12}"
          f"{(llm_result['ndcg@5'] if llm_result else '—'):<12}")
    print(f"{'Recall@5':<18}{rule_result['recall@5']:<12}"
          f"{(llm_result['recall@5'] if llm_result else '—'):<12}")
    print(f"{'理由不支持率':<16}{rule_result['unsupported_reason_rate']:<12}"
          f"{(llm_result['unsupported_reason_rate'] if llm_result else '—'):<12}")

    passed = (
        rule_result["ndcg@5"] >= TARGET_NDCG
        and rule_result["recall@5"] >= TARGET_RECALL
        and rule_result["unsupported_reason_rate"] <= TARGET_UNSUPPORTED
    )

    print("-" * 56)
    if llm_result:
        if llm_result["ndcg@5"] >= rule_result["ndcg@5"] * LLM_GAIN_RATIO:
            print("结论：LLM 版 nDCG 提升 ≥10%，保留 LLM 精排 ✅")
        else:
            print("结论：LLM 版提升不足 10%，建议关闭 LLM 精排（LLM_ENABLED=false）")
    elif not args.skip_llm:
        print("结论：未配置可用的 LLM key，本次仅评测规则版；"
              "配置后重跑再决定是否开启 LLM")

    print("规则版基线:", "PASS" if passed else "FAIL")

    report = {
        "rule": rule_result,
        "llm": llm_result,
        "targets": {
            "ndcg@5": TARGET_NDCG,
            "recall@5": TARGET_RECALL,
            "unsupported_reason_rate": TARGET_UNSUPPORTED,
            "llm_gain_ratio": LLM_GAIN_RATIO,
        },
        "passed": passed,
    }
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parent.parent / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"报告已写入：{out_path}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
