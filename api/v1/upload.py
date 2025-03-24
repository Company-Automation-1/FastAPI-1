from fastapi import APIRouter, HTTPException, status
from core.tasks import device_upload_task
from models.request import UploadRequest
from services.upload_service import process_upload
from core.scheduler import add_job
from datetime import datetime, timezone
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/upload", tags=["Device Upload"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_endpoint(request: UploadRequest):
    # 处理文件上传
    try:
        response_data = await process_upload(request)
    except Exception as e:
        logger.error("Upload processing failed: %s", str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Upload failed")

    # 添加调度任务
    try:
        # 直接使用原始时间戳，不进行转换
        logger.info("Raw timestamp: %s", request.timestamp)
        
        # 仅在需要显示日志时转换时间戳
        trigger_time = datetime.fromtimestamp(request.timestamp, tz=timezone.utc)
        logger.info("Trigger time (UTC): %s", trigger_time)
        
        # 转换为上海时区仅用于显示日志
        shanghai_tz = timezone(timedelta(hours=8))
        trigger_time_shanghai = trigger_time.astimezone(shanghai_tz)
        logger.info("Trigger time (Shanghai): %s", trigger_time_shanghai)
        
        add_job(
            device_upload_task,
            trigger_time_shanghai,
            device_name=request.device_name,
            task_time=request.timestamp  # 传递原始时间戳
        )
    except Exception as e:
        logger.error("Task scheduling failed: %s", str(e), exc_info=True)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Scheduling failed")

    return response_data