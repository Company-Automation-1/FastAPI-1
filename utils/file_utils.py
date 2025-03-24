"""
文件工具模块

该模块提供文件处理相关的工具函数，包括：
1. 生成唯一文件名
2. 文件扩展名处理
3. 其他文件相关的实用函数

主要功能：
- 生成基于UUID的唯一文件名
- 保持原始文件扩展名
"""

import uuid
from pathlib import Path

def generate_unique_filename(original_name: str) -> str:
    """
    生成唯一的文件名

    使用UUID生成唯一标识符，并保留原始文件的扩展名

    Args:
        original_name (str): 原始文件名

    Returns:
        str: 生成的唯一文件名（UUID + 原始扩展名）

    示例:
        >>> generate_unique_filename('test.jpg')
        '123e4567-e89b-12d3-a456-426614174000.jpg'
    """
    ext = Path(original_name).suffix
    return f"{uuid.uuid4().hex}{ext}"