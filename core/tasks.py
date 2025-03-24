import datetime
import logging
from apscheduler.jobstores.base import JobLookupError

logger = logging.getLogger(__name__)

async def device_upload_task(device_name: str, task_time: int):
    try:
        # 仅在日志显示时转换时间戳
        logger.info("Executing task for device [%s] scheduled at [%s]", 
                   device_name, datetime.fromtimestamp(task_time))
        # 实际操作中使用 task_time 原始时间戳
        # 这里可以添加实际任务逻辑：
        # 1. 数据清理
        # 2. 数据分析
        # 3. 发送通知
        # 4. 调用第三方API
    except Exception as e:
        logger.error("Task execution failed: %s", str(e), exc_info=True)