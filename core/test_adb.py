"""
ADB模块测试脚本

用于测试ADB连接和基本功能是否正常工作
"""

import asyncio
import logging
from core.adb import adb, ADBException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_adb_connection():
    """测试ADB连接功能"""
    logger.info("=== 开始ADB连接测试 ===")

    # 测试获取已连接设备列表
    connected_devices = adb.update_connected_devices()
    logger.info(f"当前连接的设备: {connected_devices}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_adb_connection()) 