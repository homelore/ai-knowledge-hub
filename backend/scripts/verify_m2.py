"""M2 验收脚本 — 规则推荐引擎。

验收项：
    1. 无 LLM key 下跑通完整三轮对话
    2. 全部画像组合的硬约束通过率 100%
    3. 接口 P95 响应时间 < 100ms

用法：
    python scripts/verify_m2.py
"""

import itertools
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SCHEDULER_ENABLED", "false")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from config import FETCH_TOPICS  # noqa: E402
from services.recommend.profile import (  # noqa: E402
    LEVEL_VALUES, PREFERENCE_VALUES,
)

LATENCY_TARGET_MS = 100.0


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(int(round(0.95 * len(ordered))) - 1, 0)
    return ordered[idx]


def main() -> int:
    client = TestClient(app)

    print("=" * 56)
    print("M2 规则推荐引擎验收")
    print("=" * 56)

    # ── 1. 完整三轮对话（无 LLM）──────────────────────────
    resp = client.post("/api/recommend/chat", json={})
    body = resp.json()
    session_id = body.get("session_id")
    stages = [body.get("stage")]

    resp = client.post("/api/recommend/chat", json={
        "session_id": session_id,
        "answers": {"topics": ["llm", "rag"]},
    })
    stages.append(resp.json().get("stage"))

    resp = client.post("/api/recommend/chat", json={
        "session_id": session_id,
        "answers": {"level": "beginner"},
    })
    stages.append(resp.json().get("stage"))

    resp = client.post("/api/recommend/chat", json={
        "session_id": session_id,
        "answers": {"preference": "runnable"},
    })
    final = resp.json()
    stages.append(final.get("stage"))

    chat_ok = (
        stages == ["question", "question", "question", "result"]
        and len(final.get("recommendations") or []) == 5
    )
    print(f"三轮对话阶段流转        : {' → '.join(stages)}  "
          f"{'✅' if chat_ok else '❌'}")

    # ── 2. 全画像组合约束通过率 ──────────────────────────
    failures = []
    latencies: list[float] = []
    total = 0

    topic_names = [t["name"] for t in FETCH_TOPICS]
    for topics, level, pref in itertools.product(
        ([t] for t in topic_names), LEVEL_VALUES, PREFERENCE_VALUES
    ):
        total += 1
        started = time.perf_counter()
        resp = client.post("/api/recommend", json={
            "profile": {
                "topics": list(topics),
                "level": level,
                "preference": pref,
            }
        })
        latencies.append((time.perf_counter() - started) * 1000)

        data = resp.json()
        constraints = data.get("constraints") or {}
        if resp.status_code != 200 or not constraints.get("passed"):
            failures.append({
                "topics": list(topics), "level": level, "preference": pref,
                "checks": constraints.get("checks"),
            })

    pass_rate = (total - len(failures)) / total if total else 0
    print(f"画像组合数              : {total}")
    print(f"硬约束通过率            : {pass_rate:.1%}  "
          f"{'✅' if pass_rate == 1.0 else '❌'}")

    p95 = _p95(latencies)
    print(f"接口 P95 延迟           : {p95:.1f} ms  "
          f"{'✅' if p95 < LATENCY_TARGET_MS else '❌'}")

    if failures:
        print("\n失败样例（最多 3 条）:")
        for item in failures[:3]:
            print("  ", item)

    print("=" * 56)
    print("结论:", "PASS" if (chat_ok and pass_rate == 1.0 and p95 < 100) else "FAIL")
    return 0 if (chat_ok and pass_rate == 1.0 and p95 < 100) else 1


if __name__ == "__main__":
    sys.exit(main())
