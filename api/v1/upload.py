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
from core.tasks import execute_immediate_tasks, execute_scheduled_tasks
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
    设备上传数据接口
    1. 处理文件上传请求
    2. 执行立即任务
    3. 创建定时任务
    """
    # 处理上传
    response_data = await handle_upload(request)
    
    # 执行立即任务
    await execute_immediate_task(request)
    
    # 创建定时任务
    await create_scheduled_task(request)
    
    return response_data

async def handle_upload(request: UploadRequest) -> dict:
    """处理文件上传请求"""
    try:
        return await process_upload(request)
    except Exception as e:
        logger.error("Upload failed: %s", str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Upload failed")

async def execute_immediate_task(request: UploadRequest):
    """执行立即任务"""
    try:
        await execute_immediate_tasks(
            device_name=request.device_name,
            upload_time=request.timestamp
        )
    except Exception as e:
        logger.error("Immediate task failed: %s", str(e))
        # 这里我们不抛出异常，因为这是次要任务，不应影响上传响应
        
async def create_scheduled_task(request: UploadRequest):
    """创建定时任务"""
    try:
        # 使用上海时区
        shanghai_tz = timezone(timedelta(hours=8))
        trigger_time = datetime.fromtimestamp(request.timestamp, tz=timezone.utc)
        trigger_time_shanghai = trigger_time.astimezone(shanghai_tz)
        
        add_job(
            execute_scheduled_tasks,
            trigger_time_shanghai,
            device_name=request.device_name,
            task_time=request.timestamp
        )
    except Exception as e:
        logger.error("Task scheduling failed: %s", str(e))
        # 这里我们不抛出异常，因为这是次要任务，不应影响上传响应