"""
ADB调试桥模块

该模块提供与安卓设备交互的基础功能，包括：
1. 设备连接状态检查和重连尝试
2. ADB命令执行的封装
3. 基础设备通信功能

主要用途：
- 检查设备连接状态
- 连接和管理多个设备
- 封装和执行ADB命令
- 提供底层设备通信能力
"""

import subprocess
import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Union, Set
from core.config import Settings

logger = logging.getLogger(__name__)

class ADBException(Exception):
    """ADB操作异常"""
    pass

class ADBInterface:
    """
    ADB调试桥接口类
    
    提供设备连接检查、连接多设备和ADB命令执行的封装功能。
    作为底层模块使用，不直接提供交互功能。
    
    设备名称与设备ID的对应关系存储在配置中(Settings.DEVICE_MAPPING)，
    其中设备名称是人类可读的标识，而设备ID是ADB实际使用的设备标识符。
    """
    
    def __init__(self, adb_path: str = "adb", max_retry: int = 3, retry_interval: int = 2):
        """
        初始化ADB接口
        
        Args:
            adb_path: ADB可执行文件的路径，默认直接使用系统PATH中的adb
            max_retry: 命令执行最大重试次数
            retry_interval: 重试间隔(秒)
        """
        self.adb_path = adb_path
        self.device_mapping = Settings.DEVICE_MAPPING  # 设备名到设备ID的映射
        self.max_retry = max_retry
        self.retry_interval = retry_interval
        self.last_connected_devices: Set[str] = set()  # 记录上次连接的设备ID集合
    
    def _run_command(self, command: List[str], retry: bool = True) -> str:
        """
        同步执行ADB命令，支持自动重试
        
        Args:
            command: 要执行的ADB命令列表
            retry: 是否在失败时重试
            
        Returns:
            str: 命令执行结果
            
        Raises:
            ADBException: 命令执行失败且重试后仍失败
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= (self.max_retry if retry else 0):
            try:
                cmd = [self.adb_path] + command
                logger.debug(f"执行ADB命令: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                error_msg = f"ADB命令失败: {e.stderr}"
                logger.warning(f"{error_msg} (尝试 {retry_count+1}/{self.max_retry if retry else 1})")
                last_error = ADBException(error_msg)
                if retry:
                    retry_count += 1
                    time.sleep(self.retry_interval)
                else:
                    raise last_error
            except Exception as e:
                error_msg = f"ADB操作异常: {str(e)}"
                logger.error(error_msg)
                raise ADBException(error_msg)
        
        # 所有重试都失败
        if last_error:
            raise last_error
    
    async def _run_command_async(self, command: List[str], retry: bool = True) -> str:
        """
        异步执行ADB命令，支持自动重试
        
        Args:
            command: 要执行的ADB命令列表
            retry: 是否在失败时重试
            
        Returns:
            str: 命令执行结果
            
        Raises:
            ADBException: 命令执行失败且重试后仍失败
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= (self.max_retry if retry else 0):
            try:
                cmd = [self.adb_path] + command
                logger.debug(f"异步执行ADB命令: {' '.join(cmd)}")
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode != 0:
                    error_msg = f"ADB命令失败: {stderr.decode()}"
                    logger.warning(f"{error_msg} (尝试 {retry_count+1}/{self.max_retry if retry else 1})")
                    last_error = ADBException(error_msg)
                    if retry:
                        retry_count += 1
                        await asyncio.sleep(self.retry_interval)
                        continue
                    else:
                        raise last_error
                    
                return stdout.decode().strip()
            except Exception as e:
                if isinstance(e, ADBException):
                    raise e
                error_msg = f"异步ADB操作异常: {str(e)}"
                logger.error(error_msg)
                raise ADBException(error_msg)
        
        # 所有重试都失败
        if last_error:
            raise last_error
    
    def _get_device_id(self, device_name: str) -> str:
        """
        根据设备名称获取设备ID（设备号）
        
        设备名称是人类可读的标识，设备ID是ADB实际使用的设备标识符。
        
        Args:
            device_name: 设备名称（用户定义的易读标识）
            
        Returns:
            str: 设备ID（ADB使用的实际设备标识符）
            
        Raises:
            ADBException: 设备名称未在配置中找到
        """
        if device_name not in self.device_mapping:
            raise ADBException(f"未配置的设备名称: {device_name}")
        return self.device_mapping[device_name]
    
    def get_device_name_by_id(self, device_id: str) -> Optional[str]:
        """
        根据设备ID获取设备名称
        
        Args:
            device_id: 设备ID
            
        Returns:
            Optional[str]: 对应的设备名称，如果未找到则返回None
        """
        for name, device_id_in_map in self.device_mapping.items():
            if device_id_in_map == device_id:
                return name
        return None
    
    def get_connected_devices(self) -> List[str]:
        """
        获取当前已连接的所有设备ID
        
        Returns:
            List[str]: 已连接设备ID列表
        """
        try:
            output = self._run_command(["devices"])
            devices = []
            for line in output.splitlines():
                if "\t" in line and "device" in line:
                    device_id = line.split("\t")[0].strip()
                    devices.append(device_id)
            
            # 更新上次连接的设备集合
            self.last_connected_devices = set(devices)
            return devices
        except ADBException as e:
            logger.error(f"获取已连接设备失败: {str(e)}")
            return []
    
    async def get_connected_devices_async(self) -> List[str]:
        """
        异步获取当前已连接的所有设备ID
        
        Returns:
            List[str]: 已连接设备ID列表
        """
        try:
            output = await self._run_command_async(["devices"])
            devices = []
            for line in output.splitlines():
                if "\t" in line and "device" in line:
                    device_id = line.split("\t")[0].strip()
                    devices.append(device_id)
            
            # 更新上次连接的设备集合
            self.last_connected_devices = set(devices)
            return devices
        except ADBException as e:
            logger.error(f"异步获取已连接设备失败: {str(e)}")
            return []
    
    def get_connected_device_names(self) -> List[str]:
        """
        获取当前已连接的所有设备名称
        
        Returns:
            List[str]: 已连接设备名称列表
        """
        connected_ids = self.get_connected_devices()
        connected_names = []
        
        for device_id in connected_ids:
            name = self.get_device_name_by_id(device_id)
            if name:
                connected_names.append(name)
        
        return connected_names
    
    async def get_connected_device_names_async(self) -> List[str]:
        """
        异步获取当前已连接的所有设备名称
        
        Returns:
            List[str]: 已连接设备名称列表
        """
        connected_ids = await self.get_connected_devices_async()
        connected_names = []
        
        for device_id in connected_ids:
            name = self.get_device_name_by_id(device_id)
            if name:
                connected_names.append(name)
        
        return connected_names
    
    def is_device_connected(self, device_name: str) -> bool:
        """
        检查设备是否已连接
        
        Args:
            device_name: 设备名称
            
        Returns:
            bool: 设备是否已连接
        """
        try:
            device_id = self._get_device_id(device_name)
            connected_devices = self.get_connected_devices()
            return device_id in connected_devices
        except ADBException:
            return False
    
    async def is_device_connected_async(self, device_name: str) -> bool:
        """
        异步检查设备是否已连接
        
        Args:
            device_name: 设备名称
            
        Returns:
            bool: 设备是否已连接
        """
        try:
            device_id = self._get_device_id(device_name)
            connected_devices = await self.get_connected_devices_async()
            return device_id in connected_devices
        except ADBException:
            return False
    
    def connect_device(self, device_id: str) -> bool:
        """
        直接使用设备ID连接设备
        
        Args:
            device_id: 设备ID（设备号）
            
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info(f"尝试连接设备ID: {device_id}")
            self._run_command(["connect", device_id])
            
            # 验证连接是否成功
            connected_devices = self.get_connected_devices()
            connected = device_id in connected_devices
            logger.info(f"设备ID {device_id} 连接{'成功' if connected else '失败'}")
            return connected
        except ADBException as e:
            logger.error(f"连接设备ID {device_id} 失败: {str(e)}")
            return False
    
    async def connect_device_async(self, device_id: str) -> bool:
        """
        异步直接使用设备ID连接设备
        
        Args:
            device_id: 设备ID（设备号）
            
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info(f"异步尝试连接设备ID: {device_id}")
            await self._run_command_async(["connect", device_id])
            
            # 验证连接是否成功
            connected_devices = await self.get_connected_devices_async()
            connected = device_id in connected_devices
            logger.info(f"设备ID {device_id} 异步连接{'成功' if connected else '失败'}")
            return connected
        except ADBException as e:
            logger.error(f"异步连接设备ID {device_id} 失败: {str(e)}")
            return False
    
    def connect_all_devices(self) -> Dict[str, bool]:
        """
        连接配置中的所有设备
        
        Returns:
            Dict[str, bool]: 设备连接结果，键为设备名称，值为是否连接成功
        """
        results = {}
        for device_name, device_id in self.device_mapping.items():
            try:
                logger.info(f"尝试连接设备: {device_name} (ID: {device_id})")
                connected = self.connect_device(device_id)
                results[device_name] = connected
            except Exception as e:
                logger.error(f"连接设备 {device_name} (ID: {device_id}) 时发生错误: {str(e)}")
                results[device_name] = False
        return results
    
    async def connect_all_devices_async(self) -> Dict[str, bool]:
        """
        异步连接配置中的所有设备
        
        Returns:
            Dict[str, bool]: 设备连接结果，键为设备名称，值为是否连接成功
        """
        results = {}
        for device_name, device_id in self.device_mapping.items():
            try:
                logger.info(f"异步尝试连接设备: {device_name} (ID: {device_id})")
                connected = await self.connect_device_async(device_id)
                results[device_name] = connected
            except Exception as e:
                logger.error(f"异步连接设备 {device_name} (ID: {device_id}) 时发生错误: {str(e)}")
                results[device_name] = False
        return results
    
    def execute_device_command(self, device_name: str, command: List[str], retry: bool = True) -> str:
        """
        对特定设备执行ADB命令
        
        Args:
            device_name: 设备名称
            command: 要执行的命令列表
            retry: 是否在失败时重试
            
        Returns:
            str: 命令执行结果
            
        Raises:
            ADBException: 命令执行失败且重试后仍失败
        """
        device_id = self._get_device_id(device_name)
        device_command = ["-s", device_id] + command
        
        try:
            return self._run_command(device_command, retry)
        except ADBException as e:
            # 如果执行失败，尝试检查设备连接状态
            if not self.is_device_connected(device_name):
                logger.warning(f"设备 {device_name} (ID: {device_id}) 未连接，无法执行命令")
            raise e
    
    async def execute_device_command_async(self, device_name: str, command: List[str], retry: bool = True) -> str:
        """
        异步对特定设备执行ADB命令
        
        Args:
            device_name: 设备名称
            command: 要执行的命令列表
            retry: 是否在失败时重试
            
        Returns:
            str: 命令执行结果
            
        Raises:
            ADBException: 命令执行失败且重试后仍失败
        """
        device_id = self._get_device_id(device_name)
        device_command = ["-s", device_id] + command
        
        try:
            return await self._run_command_async(device_command, retry)
        except ADBException as e:
            # 如果执行失败，尝试检查设备连接状态
            if not await self.is_device_connected_async(device_name):
                logger.warning(f"设备 {device_name} (ID: {device_id}) 未连接，无法执行命令")
            raise e

# 创建一个默认的ADB接口实例，可以在其他模块中直接使用
adb = ADBInterface() 