from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import logging
from core.config import Settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone=Settings.SCHEDULER_TIMEZONE)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started with timezone: %s", Settings.SCHEDULER_TIMEZONE)

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

def add_job(func, run_time: datetime, *args, **kwargs):
    if run_time < datetime.now(tz=Settings.SCHEDULER_TIMEZONE):
        logger.warning("Attempted to schedule job in the past: %s", run_time)
        return None
    
    # 确保传入的 run_time 有时区信息
    if run_time.tzinfo is None:
        run_time = run_time.replace(tzinfo=Settings.SCHEDULER_TIMEZONE)
    
    job = scheduler.add_job(
        func,
        DateTrigger(run_date=run_time, timezone=Settings.SCHEDULER_TIMEZONE),
        args=args,
        kwargs=kwargs,
        misfire_grace_time=120,
        coalesce=True
    )
    logger.info("Scheduled job %s for %s", job.id, run_time)
    return job