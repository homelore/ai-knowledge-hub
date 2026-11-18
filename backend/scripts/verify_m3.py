"""M3 验收脚本 — LLM 编排的故障注入与幻觉拦截。

覆盖三类故障：
    1. 无 key（LLM_ENABLED=true 但 ARK_API_KEY 为空）
    2. URL 不可达（base_url 指向无服务端口）
    3. 返回非 JSON（模型输出自由文本）

外加一类安全项：
    4. 幻觉 repo_id 拦截率 100%

任一场景都要求：接口 200 + 恰好 5 条合法推荐（repo_id 必须存在于库中）。

用法：
    python scripts/verify_m3.py
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("SCHEDULER_ENABLED", "false")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from models.database import SessionLocal  # noqa: E402
from models.repo import Repo  # noqa: E402
from services.llm.ark_client import LLMResult  # noqa: E402
from services.llm.config import LLMConfig  # noqa: E402
import services.llm.recommend_llm as recommend_llm  # noqa: E402
import services.recommend.llm_orchestrator as orch  # noqa: E402
from services.recommend.cache import get_cache  # noqa: E402

PROFILE = {"topics": ["llm", "rag"], "level": "beginner", "preference": "runnable"}


def _valid_repo_ids() -> set[int]:
    session = SessionLocal()
    try:
        return {row[0] for row in session.query(Repo.id).all()}
    finally:
        session.close()


def _check(name: str, resp, valid_ids: set[int]) -> bool:
    if resp.status_code != 200:
        print(f"  {name:<22}: HTTP {resp.status_code} ❌")
        return False
    data = resp.json()
    recs = data.get("recommendations") or []
    ids = [r.get("repo_id") for r in recs]
    ok = (
        len(recs) == 5
        and all(i in valid_ids for i in ids)
        and len(set(ids)) == 5
    )
    print(
        f"  {name:<22}: engine={data.get('engine'):<4} "
        f"error={str(data.get('error_kind')):<18} "
        f"条数={len(recs)} ids合法={all(i in valid_ids for i in ids)} "
        f"{'✅' if ok else '❌'}"
    )
    return ok


def main() -> int:
    client = TestClient(app)
    valid_ids = _valid_repo_ids()
    results: list[bool] = []

    print("=" * 60)
    print("M3 LLM 编排验收（故障注入）")
    print("=" * 60)

    # ── 场景 1：无 key ────────────────────────────────────
    get_cache().clear()
    orch.LLM_ENABLED = True
    orch.get_config = lambda: LLMConfig(
        enabled=True, api_key="", base_url="https://ark.example.com/api/v3",
        endpoint_id="ep-test",
    )
    results.append(_check(
        "无 key", client.post("/api/recommend", json={"profile": PROFILE}), valid_ids
    ))

    # ── 场景 2：URL 不可达 ────────────────────────────────
    get_cache().clear()
    orch.get_config = lambda: LLMConfig(
        enabled=True, api_key="test-key", base_url="http://127.0.0.1:9/api/v3",
        endpoint_id="ep-test", timeout_connect=0.5, timeout_read=0.5, max_retries=0,
    )
    results.append(_check(
        "URL 不可达", client.post("/api/recommend", json={"profile": PROFILE}), valid_ids
    ))

    # ── 场景 3：返回非 JSON ───────────────────────────────
    get_cache().clear()
    orch.get_config = lambda: LLMConfig(
        enabled=True, api_key="test-key", base_url="https://ark.example.com/api/v3",
        endpoint_id="ep-test",
    )

    async def _bad_json(*_args, **_kwargs):
        return LLMResult(ok=True, raw_text="抱歉，我无法按要求输出 JSON。")

    recommend_llm.call_ark = _bad_json
    results.append(_check(
        "返回非 JSON", client.post("/api/recommend", json={"profile": PROFILE}), valid_ids
    ))

    # ── 场景 4：幻觉 repo_id 拦截 ─────────────────────────
    get_cache().clear()
    real_ids = sorted(valid_ids)[:2]

    async def _hallucinated(messages, **_kwargs):
        payload = (
            '{"items": ['
            '{"repo_id": 999999999, "why": "很适合入门", "first_step": "先看示例"},'
            '{"repo_id": 888888888, "why": "文档齐全", "first_step": "读 README"},'
            f'{{"repo_id": {real_ids[0]}, "why": "方向匹配", "first_step": "跑最小示例"}},'
            f'{{"repo_id": {real_ids[1]}, "why": "上手很快", "first_step": "克隆后运行"}}'
            "]}"
        )
        return LLMResult(ok=True, raw_text=payload)

    recommend_llm.call_ark = _hallucinated
    resp = client.post("/api/recommend", json={"profile": PROFILE})
    body = resp.json()
    returned_ids = {r["repo_id"] for r in body.get("recommendations") or []}
    hallucination_blocked = (
        999999999 not in returned_ids
        and 888888888 not in returned_ids
        and len(returned_ids) == 5
    )
    print(
        f"  {'幻觉 repo_id 拦截':<20}: 返回 {len(returned_ids)} 条 | "
        f"幻觉 id 存在={bool({999999999, 888888888} & returned_ids)} "
        f"{'✅' if hallucination_blocked else '❌'}"
    )
    results.append(hallucination_blocked)

    print("=" * 60)
    passed = all(results)
    print("结论:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
