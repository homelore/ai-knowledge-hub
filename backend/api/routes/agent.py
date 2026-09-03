"""Agent 手动触发 API 路由。"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("ai-hub.api.agent")


class FetchResponse(BaseModel):
    status: str
    message: str


@router.post("/fetch", response_model=FetchResponse)
def trigger_fetch():
    """手动触发 GitHub 拉取任务。

    同步执行，拉取完成后返回结果。
    """
    try:
        from agent.fetcher import fetch_weekly_trending
        result = fetch_weekly_trending()
        logger.info(f"手动拉取完成: {result}")

        if result.get("status") == "failed":
            return FetchResponse(
                status="failed",
                message=f"拉取失败：{result.get('error', '未知错误')}",
            )

        return FetchResponse(
            status="success",
            message=f"拉取完成：{result.get('total_fetched', 0)} 个仓库，"
                    f"新增 {result.get('new_count', 0)}，"
                    f"更新 {result.get('updated_count', 0)}",
        )
    except Exception as e:
        logger.error(f"手动拉取失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"拉取失败: {str(e)}")


@router.get("/status")
def agent_status():
    """Agent 调度器状态。"""
    from config import SCHEDULER_ENABLED
    from agent.scheduler import _scheduler

    running = _scheduler is not None and _scheduler.running if _scheduler else False
    return {
        "scheduler_enabled": SCHEDULER_ENABLED,
        "scheduler_running": running,
    }
