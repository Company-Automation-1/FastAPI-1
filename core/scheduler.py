"""
任务调度器模块

该模块提供任务调度功能，负责管理和执行定时任务，包括：
1. 初始化和管理调度器
2. 添加定时任务
3. 处理任务的生命周期

主要功能：
- 启动和停止调度器
- 添加定时任务
- 处理任务调度异常
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import logging
from core.config import Settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone=Settings.SCHEDULER_TIMEZONE)

def start_scheduler():
    """
    启动调度器

    如果调度器未运行，则启动它并设置正确的时区
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started with timezone: %s", Settings.SCHEDULER_TIMEZONE)

def stop_scheduler():
    """
    停止调度器

    安全地关闭正在运行的调度器
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

def add_job(func, run_time: datetime, *args, **kwargs):
    """
    添加定时任务

    Args:
        func: 要执行的函数
        run_time (datetime): 任务执行时间
        *args: 传递给任务函数的位置参数
        **kwargs: 传递给任务函数的关键字参数

    Returns:
        Job: 已创建的任务对象，如果创建失败则返回None

    注意:
        - 如果执行时间早于当前时间，任务将不会被添加
        - 任务默认有120秒的容错时间
    """
    if run_time < datetime.now(tz=Settings.SCHEDULER_TIMEZONE):
        logger.warning("Attempted to schedule job in the past: %s", run_time)
        return None
    
    # 确保时区信息正确
    if run_time.tzinfo is None:
        run_time = run_time.replace(tzinfo=Settings.SCHEDULER_TIMEZONE)
    
    job = scheduler.add_job(
        func,
        DateTrigger(run_date=run_time, timezone=Settings.SCHEDULER_TIMEZONE),
        args=args,
        kwargs=kwargs,
        misfire_grace_time=120,  # 任务最大延迟执行时间（秒）
        coalesce=True  # 如果错过了执行时间，只执行一次
    )
    logger.info("Scheduled job %s for %s", job.id, run_time)
    return job