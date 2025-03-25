"""
ADB调试桥模块

该模块提供与安卓设备通信的核心功能：
1. 设备连接管理
2. ADB命令执行
3. 异步通信支持
"""

import subprocess
import asyncio
import logging
import os
from typing import List
from core.config import Settings

logger = logging.getLogger(__name__)

class ADBException(Exception):
    """ADB操作异常"""
    pass

class ADBInterface:
    """
    ADB调试桥接口类
    
    提供设备通信的核心功能，包括连接管理和命令执行。
    """
    
    def __init__(self):
        """初始化ADB接口"""
        self.adb_path = Settings.ADB_PATH or "adb"
        self.device_mapping = Settings.DEVICE_MAPPING

        self.connected_devices = set()  # 已连接设备集合
        
        # 确保ADB服务器启动
        subprocess.run([self.adb_path, 'start-server'], capture_output=True, text=True)
        
        self.update_connected_devices() # 初始化设备列表

    
    def update_connected_devices(self):
        """更新已连接的设备列表"""
        try:
            result = subprocess.run(
                [self.adb_path, 'devices'], 
                capture_output=True, 
                text=True, 
                check=True
            )

            # 解析ADB输出
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            self.connected_devices = {
                line.split()[0] for line in lines 
                if line.strip() and 'device' in line  # 过滤掉未授权设备
            }
            
            logger.info(f"当前连接的设备: {self.connected_devices}")
            return self.connected_devices

        except subprocess.CalledProcessError as e:
            logger.error(f"获取设备列表失败: {str(e)}")
            self.connected_devices = set()
            return set()
            
    # def is_device_connected(self, device_id):
    #     """检查指定设备是否在线"""
    #     self.update_connected_devices()  # 每次检查前更新状态
    #     return device_id in self.connected_devices
    
    def _get_device_id(self, device_name):
        """从设备名称获取设备ID"""
        if device_name in self.device_mapping:
            return self.device_mapping[device_name]
        # 如果找不到映射，假设设备名称就是设备ID
        return device_name
    
    async def is_device_connected_async(self, device_name):
        """异步检查指定设备是否在线"""
        devices = await self.get_connected_devices_async()
        device_id = self._get_device_id(device_name)
        return device_id in devices
    
    async def connect_device_async(self, device_id):
        """异步连接指定设备"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.adb_path, 'connect', device_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore').strip()
            
            if "connected to" in output:
                logger.info(f"成功连接到设备: {device_id}")
                return True
            else:
                logger.error(f"连接设备失败: {device_id}, 输出: {output}")
                return False
        except Exception as e:
            logger.error(f"连接设备时发生错误: {str(e)}")
            return False
        
    async def get_connected_devices_async(self) -> List[str]:
        """获取已连接的设备列表"""
        try:
            # 获取设备列表
            result = subprocess.run(
                [self.adb_path, 'devices'],  # 使用self.adb_path替代ADB_COMMAND
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # 解析ADB输出
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            self.connected_devices = {
                line.split()[0] for line in lines 
                if line.strip() and 'device' in line  # 过滤掉未授权设备
            }
            
            logger.info(f"当前连接的设备: {self.connected_devices}")
            return self.connected_devices
            
        except subprocess.CalledProcessError as e:
            logger.error(f"获取设备列表失败: {str(e)}")
            self.connected_devices = set()
            return set()
            
    async def execute_device_command_async(self, device_name, command_args):
        """
        异步执行设备命令
        
        Args:
            device_name: 设备名称
            command_args: 命令参数列表
        """
        device_id = None
        cmd = []
        
        try:
            # 获取设备ID
            device_id = self._get_device_id(device_name)
            
            # 构建完整的命令
            cmd = [self.adb_path, '-s', device_id] + command_args
            cmd_str = ' '.join(cmd)
            logger.info(f"执行命令: {cmd_str}")
            
            # 在异步环境中运行同步代码
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # 不抛出异常，我们手动处理错误
                timeout=30  # 设置超时防止命令卡住
            ))
            
            # 检查命令执行结果
            if result.returncode != 0:
                error_output = result.stderr or result.stdout or f"命令执行失败，返回码: {result.returncode}"
                logger.error(f"ADB命令执行失败: {error_output}")
                raise ADBException(f"命令执行失败: {error_output}")
                
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            error_msg = f"命令执行超时: {' '.join(cmd) if cmd else '未知'}"
            logger.error(error_msg)
            raise ADBException(error_msg)
        except ADBException:
            # 重新抛出ADBException
            raise
        except Exception as e:
            error_msg = str(e)
            # 记录完整的错误信息，包括命令和设备ID
            cmd_info = f"设备: {device_name}({device_id if device_id else '未知'}), 命令: {' '.join(cmd) if cmd else '未知'}"
            logger.error(f"执行ADB命令时发生未预期的错误: {error_msg}, {cmd_info}", exc_info=True)
            raise ADBException(f"执行ADB命令时出错: {error_msg}")

    async def ensure_adb_server_running(self):
        """确保ADB服务器正在运行"""
        try:
            result = subprocess.run(
                [self.adb_path, 'start-server'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("ADB服务器已启动")
            return True
        except Exception as e:
            logger.error(f"启动ADB服务器失败: {str(e)}")
            return False

# 创建全局ADB接口实例
adb = ADBInterface() 