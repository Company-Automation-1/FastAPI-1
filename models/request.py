"""
请求模型定义模块

该模块定义了API请求中使用的数据模型，包括：
1. 文件上传的Base64编码模型
2. 设备上传请求的完整模型

主要功能：
- 定义请求数据的结构
- 提供数据验证规则
- 处理Base64编码的文件数据
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
import base64

class FileBase64(BaseModel):
    """
    Base64编码的文件数据模型

    属性:
        filename (str): 原始文件名
        data (str): Base64编码的文件内容
    """
    filename: str
    data: str

    @validator('data')
    def validate_base64(cls, v):
        """
        验证Base64数据的有效性

        Args:
            v (str): Base64编码字符串

        Returns:
            str: 验证通过的Base64字符串

        Raises:
            ValueError: 当Base64数据无效时抛出
        """
        try:
            base64.b64decode(v.encode(), validate=True)
            return v
        except Exception as e:
            raise ValueError("Invalid Base64 data") from e

class UploadRequest(BaseModel):
    """
    设备上传请求的数据模型

    属性:
        device_name (str): 设备名称，2-50个字符
        timestamp (int): 上传时间戳，必须大于0
        title (Optional[str]): 可选的标题，最大100个字符
        content (Optional[str]): 可选的内容，最大1000个字符
        files (List[FileBase64]): Base64编码的文件列表
    """
    device_name: str = Field(..., min_length=2, max_length=50)
    timestamp: int = Field(..., gt=0)
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, max_length=1000)
    files: List[FileBase64]