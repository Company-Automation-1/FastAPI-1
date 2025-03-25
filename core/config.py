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
import os

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

    # ADB配置
    ADB_PATH = "adb"  # 如果 adb 在系统 PATH 中
    # 或者使用绝对路径
    # ADB_PATH = r"E:\Program Files (x86)\adb\adb.exe"  # Windows 示例

    # 设备映射配置
    # 设备映射配置
    DEVICE_MAPPING = {
        "deviceA": "XPL5T19A28003051",
        "deviceA_sys2": "XPL5T19A28003051",  # 同一设备的第二个系统
        "deviceB": "r8yhge69x8u8lzv8",
        "deviceC": "IJKL9012"
    }

    # 设备配置详情
    DEVICE_CONFIG = {
        "deviceA": {
            "storage_path": "/storage/emulated/0/Pictures/",
            "lock_password": "000000",
            "app_package": "com.xingin.xhs",
            "wait_timeout": 10
        },
        "deviceA_sys2": {  # 同一设备的第二个系统配置
            "storage_path": "/storage/emulated/0/Pictures/",
            "lock_password": "123456",
            "app_package": "com.xingin.xhs",
            "wait_timeout": 10
        },
        "deviceB": {
            "storage_path": "/storage/emulated/0/DCIM/Camera/",
            "lock_password": "666666",
            "app_package": "com.xingin.xhs",
            "wait_timeout": 10
        },
        "deviceC": {
            "storage_path": "/storage/emulated/0/Pictures",
            "lock_password": "888888",
            "app_package": "com.xingin.xhs",
            "wait_timeout": 10
        }
    }

    # 基础自动化配置（默认值）
    AUTOMATION_CONFIG = {
        'APP_PACKAGE': 'com.xingin.xhs',
        'WAIT_TIMEOUT': 10
    } 