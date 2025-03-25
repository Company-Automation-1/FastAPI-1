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
from typing import List, Set, Optional, Dict, Union
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
        self.connected_devices: Set[str] = set()
        
        # 启动ADB服务器并初始化设备列表
        self._start_adb_server()
        self.update_connected_devices()
    
    def _start_adb_server(self) -> None:
        """启动ADB服务器"""
        try:
            subprocess.run(
                [self.adb_path, 'start-server'], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=10
            )
            logger.info("ADB服务器已启动")
        except Exception as e:
            logger.error(f"启动ADB服务器失败: {str(e)}")
    
    def update_connected_devices(self) -> Set[str]:
        """
        更新已连接的设备列表
        
        Returns:
            包含设备ID的集合
        """
        try:
            result = subprocess.run(
                [self.adb_path, 'devices'], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=10
            )

            # 解析ADB输出
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            self.connected_devices = {
                line.split()[0] for line in lines 
                if line.strip() and 'device' in line  # 过滤掉未授权设备
            }
            
            logger.info(f"当前连接的设备: {self.connected_devices}")
            return self.connected_devices

        except Exception as e:
            logger.error(f"获取设备列表失败: {str(e)}")
            self.connected_devices = set()
            return set()
    
    def _get_device_id(self, device_name: str) -> str:
        """
        从设备名称获取设备ID
        
        Args:
            device_name: 设备名称或别名
            
        Returns:
            设备ID
        """
        return self.device_mapping.get(device_name, device_name)
    
    async def get_connected_devices_async(self) -> Set[str]:
        """
        异步获取已连接的设备列表
        
        Returns:
            包含设备ID的集合
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.update_connected_devices)
    
    async def is_device_connected_async(self, device_name: str) -> bool:
        """
        异步检查指定设备是否在线
        
        Args:
            device_name: 设备名称或别名
            
        Returns:
            设备是否连接
        """
        devices = await self.get_connected_devices_async()
        device_id = self._get_device_id(device_name)
        return device_id in devices
    
    async def connect_device_async(self, device_name: str) -> bool:
        """
        异步连接指定设备
        
        Args:
            device_name: 设备名称或别名
            
        Returns:
            连接是否成功
        """
        device_id = self._get_device_id(device_name)
        
        # 检查设备是否已连接
        if await self.is_device_connected_async(device_name):
            logger.info(f"设备已连接: {device_id}")
            return True
        
        try:
            result = await self.execute_adb_command_async(['connect', device_id])
            success = "connected to" in result or "already connected" in result
            
            if success:
                logger.info(f"成功连接到设备: {device_id}")
                await self.get_connected_devices_async()  # 更新设备列表
                return True
            else:
                logger.error(f"连接设备失败: {device_id}, 输出: {result}")
                return False
        except Exception as e:
            logger.error(f"连接设备时发生错误: {str(e)}")
            return False
    
    async def execute_adb_command_async(self, command_args: List[str]) -> str:
        """
        异步执行ADB命令
        
        Args:
            command_args: ADB命令参数列表
            
        Returns:
            命令执行结果
            
        Raises:
            ADBException: 命令执行失败
        """
        cmd = [self.adb_path] + command_args
        return await self._run_command_async(cmd)
    
    async def execute_device_command_async(self, device_name: str, command_args: List[str]) -> str:
        """
        异步执行设备命令
        
        Args:
            device_name: 设备名称或别名
            command_args: 命令参数列表
            
        Returns:
            命令执行结果
            
        Raises:
            ADBException: 命令执行失败
        """
        device_id = self._get_device_id(device_name)
        cmd = [self.adb_path, '-s', device_id] + command_args
        return await self._run_command_async(cmd)
    
    async def _run_command_async(self, cmd: List[str]) -> str:
        """
        异步执行命令的核心实现
        
        Args:
            cmd: 完整命令列表
            
        Returns:
            命令执行结果
            
        Raises:
            ADBException: 命令执行失败
        """
        cmd_str = ' '.join(cmd)
        logger.info(f"执行命令: {cmd_str}")
        
        try:
            # 在异步环境中运行同步代码
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            ))
            
            # 检查命令执行结果
            if result.returncode != 0:
                error_output = result.stderr or result.stdout or f"命令执行失败，返回码: {result.returncode}"
                logger.error(f"命令执行失败: {error_output}")
                raise ADBException(f"命令执行失败: {error_output}")
                
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            error_msg = f"命令执行超时: {cmd_str}"
            logger.error(error_msg)
            raise ADBException(error_msg)
        except ADBException:
            raise
        except Exception as e:
            error_msg = str(e) or f"未知错误 (类型: {type(e).__name__})"
            logger.error(f"执行命令时发生错误: {error_msg}, 命令: {cmd_str}", exc_info=True)
            raise ADBException(f"执行命令时出错: {error_msg}")
    
    async def push_file_async(self, device_name: str, local_path: str, remote_path: str) -> bool:
        """
        推送文件到设备
        
        Args:
            device_name: 设备名称或别名
            local_path: 本地文件路径
            remote_path: 设备上的目标路径
            
        Returns:
            推送是否成功
        """
        try:
            await self.execute_device_command_async(device_name, ['push', local_path, remote_path])
            return True
        except Exception as e:
            logger.error(f"推送文件失败: {str(e)}")
            return False
    
    async def create_remote_directory_async(self, device_name: str, remote_dir: str) -> bool:
        """
        在设备上创建目录
        
        Args:
            device_name: 设备名称或别名
            remote_dir: 设备上的目录路径
            
        Returns:
            创建是否成功
        """
        try:
            await self.execute_device_command_async(device_name, ['shell', f'mkdir -p {remote_dir}'])
            return True
        except Exception as e:
            logger.error(f"创建远程目录失败: {str(e)}")
            return False

# 创建全局ADB接口实例
adb = ADBInterface() 