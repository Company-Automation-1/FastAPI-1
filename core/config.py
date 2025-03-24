"""
核心配置模块

该模块定义了应用程序的核心配置参数，包括：
1. 项目路径配置
2. 上传目录设置
3. 时区设置
4. 设备映射配置
"""

from pathlib import Path
from datetime import datetime, timedelta, timezone

# 项目路径配置
PROJECT_DIR = Path(__file__).parent.parent
UPLOAD_DIR = PROJECT_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    """
    应用程序配置类

    属性:
        DEBUG (bool): 调试模式开关
        TIMEZONE (timezone): 应用程序时区（上海，UTC+8）
        SCHEDULER_TIMEZONE (timezone): 调度器时区设置
        MAX_FILE_SIZE (int): 最大文件大小限制（100MB）
    """
    DEBUG = True
    TIMEZONE = timezone(timedelta(hours=8))  # 上海时区
    SCHEDULER_TIMEZONE = timezone(timedelta(hours=8))  # 调度器使用上海时区
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    # 设备映射配置
    DEVICE_MAPPING = {
        "deviceA": "XPL5T19A28003051",
        "deviceB": "EFGH5678",
        "deviceC": "IJKL9012"
    }