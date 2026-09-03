"""APScheduler 定时调度 — 每周一 09:00 (Asia/Shanghai) 自动拉取 GitHub 趋势仓库。

提供 start_scheduler() / stop_scheduler() 两个函数，由 FastAPI 启停事件调用。
调度器实例保存在全局变量 _scheduler 中，避免重复创建。
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import (
    SCHEDULER_ENABLED,
    CRON_DAY_OF_WEEK,
    CRON_HOUR,
    CRON_MINUTE,
)
from agent.fetcher import fetch_weekly_trending

logger = logging.getLogger("ai-hub.scheduler")

# 全局调度器实例（None 表示未启动）
_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    """启动后台调度器并添加定时任务。

    - 若 SCHEDULER_ENABLED 为 False，直接 return，不启动调度器。
    - 若调度器已在运行，跳过重复启动。
    - 定时任务：每周 {CRON_DAY_OF_WEEK} {CRON_HOUR}:{CRON_MINUTE} (Asia/Shanghai) 执行 fetch_weekly_trending。
    """
    global _scheduler

    # 配置禁用调度器 → 直接返回
    if not SCHEDULER_ENABLED:
        logger.info("调度器已禁用 (SCHEDULER_ENABLED=False)，跳过启动")
        return

    # 避免重复启动
    if _scheduler is not None:
        logger.warning("调度器已在运行，跳过重复启动")
        return

    try:
        # 创建后台调度器，指定时区为 Asia/Shanghai
        _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

        # 构造 Cron 触发器
        trigger = CronTrigger(
            day_of_week=CRON_DAY_OF_WEEK,
            hour=CRON_HOUR,
            minute=CRON_MINUTE,
            timezone="Asia/Shanghai",
        )

        # 添加定时任务（replace_existing=True 确保幂等）
        _scheduler.add_job(
            func=fetch_weekly_trending,
            trigger=trigger,
            id="fetch_weekly_trending",
            name="每周拉取 GitHub 趋势仓库",
            replace_existing=True,
        )

        _scheduler.start()
        logger.info(
            f"调度器已启动，定时任务: 每周{CRON_DAY_OF_WEEK} "
            f"{CRON_HOUR:02d}:{CRON_MINUTE:02d} (Asia/Shanghai) → fetch_weekly_trending"
        )

    except Exception as exc:
        logger.exception(f"启动调度器失败: {exc}")
        _scheduler = None


def stop_scheduler() -> None:
    """关闭调度器，释放资源。

    - 若调度器未启动（_scheduler 为 None），直接返回。
    - 调用 shutdown(wait=False) 立即关闭，不等待正在执行的任务完成。
    """
    global _scheduler

    if _scheduler is None:
        return

    try:
        _scheduler.shutdown(wait=False)
        logger.info("调度器已停止")
    except Exception as exc:
        logger.error(f"停止调度器时出错: {exc}")
    finally:
        _scheduler = None
