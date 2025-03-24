"""
设备数据上传API模块

该模块提供设备数据上传的API接口，主要功能包括：
1. 接收并处理设备上传的文件和文本数据
2. 创建相应的定时任务进行后续处理
3. 处理上传过程中的异常情况

主要组件：
- upload_endpoint: 主上传接口
- handle_upload: 处理文件上传逻辑
- create_scheduled_task: 创建定时任务
"""

from fastapi import APIRouter, HTTPException, status
from core.tasks import device_upload_task
from models.request import UploadRequest
from services.upload_service import process_upload
from core.scheduler import add_job
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/upload", tags=["Device Upload"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_endpoint(request: UploadRequest):
    """
    设备数据上传的主接口

    处理流程：
    1. 接收并验证上传请求
    2. 处理文件上传
    3. 创建后续处理的定时任务

    Args:
        request (UploadRequest): 包含设备名称、时间戳、文件等信息的请求对象

    Returns:
        dict: 上传处理的结果信息

    Raises:
        HTTPException: 当上传处理或任务调度失败时抛出
    """
    # 处理上传
    response_data = await handle_upload(request)
    
    # 创建定时任务
    await create_scheduled_task(request)
    return response_data

async def handle_upload(request: UploadRequest) -> dict:
    """
    处理文件上传请求

    Args:
        request (UploadRequest): 上传请求对象

    Returns:
        dict: 包含上传结果的响应数据

    Raises:
        HTTPException: 当上传处理失败时抛出500错误
    """
    try:
        return await process_upload(request)
    except Exception as e:
        logger.error("Upload failed: %s", str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Upload failed")

async def create_scheduled_task(request: UploadRequest):
    """
    创建数据处理的定时任务

    Args:
        request (UploadRequest): 包含任务相关信息的请求对象

    Raises:
        HTTPException: 当任务调度失败时抛出503错误
    """
    try:
        shanghai_tz = timezone(timedelta(hours=8))
        trigger_time = datetime.fromtimestamp(request.timestamp, tz=timezone.utc)
        trigger_time_shanghai = trigger_time.astimezone(shanghai_tz)
        
        add_job(
            device_upload_task,
            trigger_time_shanghai,
            device_name=request.device_name,
            task_time=request.timestamp
        )
    except Exception as e:
        logger.error("Task scheduling failed: %s", str(e))
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Scheduling failed")