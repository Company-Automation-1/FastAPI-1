"""
设备信息API模块

该模块提供设备相关的API接口，包括：
1. 获取设备列表
2. 设备信息查询
"""

from fastapi import APIRouter
from core.config import Settings

# 修改路由前缀，使用复数形式
router = APIRouter(prefix="/api/v1/devices", tags=["Device Info"])

@router.get("/list")
async def get_device_list():
    """
    获取所有设备名称列表
    
    Returns:
        dict: {
            "code": 1,
            "status": "success",
            "data": {
                "devices": ["deviceA", "deviceB", "deviceC"]
            }
        }
    """
    devices = list(Settings.DEVICE_MAPPING.keys())  # 只获取设备名称列表
    
    return {
        "code": 1,
        "status": "success",
        "data": {
            "devices": devices
        }
    } 