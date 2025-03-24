"""
上传服务处理模块

该模块负责处理设备上传的具体业务逻辑，包括：
1. 文件系统操作（创建目录、保存文件）
2. 文本内容处理
3. 图片文件处理
4. 生成响应数据

主要功能：
- 创建基于时间戳的目录结构
- 保存设备上传的文本内容
- 处理并保存图片文件
- 生成文件元数据
"""

import base64
import aiofiles
from pathlib import Path
from hashlib import sha256
from datetime import datetime
from models.request import UploadRequest
from core.config import UPLOAD_DIR
from utils.file_utils import generate_unique_filename

async def process_upload(request: UploadRequest) -> dict:
    """
    处理设备上传请求的主函数

    处理流程：
    1. 创建设备专属的目录结构
    2. 保存上传的文本内容
    3. 处理并保存图片文件
    4. 生成处理结果响应

    Args:
        request (UploadRequest): 包含上传数据的请求对象

    Returns:
        dict: 包含处理结果的响应数据
    """
    # 创建目录结构
    device_dir = create_directory_structure(request)
    
    # 保存文本内容
    await save_text_content(device_dir, request)
    
    # 处理图片文件
    file_metas = await process_image_files(device_dir, request.files)
    return create_response(request, len(file_metas))

def create_directory_structure(request: UploadRequest) -> Path:
    """
    创建基于时间戳的目录结构

    目录结构：uploads/设备名称/时间戳/imgs/

    Args:
        request (UploadRequest): 包含设备信息的请求对象

    Returns:
        Path: 创建的目录路径
    """
    dir_time = datetime.fromtimestamp(request.timestamp)
    time_dir = dir_time.strftime("%Y%m%d%H%M%S")
    device_dir = UPLOAD_DIR / request.device_name / time_dir
    (device_dir / "imgs").mkdir(parents=True, exist_ok=True)
    return device_dir

async def save_text_content(device_dir: Path, request: UploadRequest):
    """
    保存上传的文本内容

    将标题和内容保存到content.txt文件中

    Args:
        device_dir (Path): 设备目录路径
        request (UploadRequest): 包含文本内容的请求对象
    """
    content_path = device_dir / "content.txt"
    async with aiofiles.open(content_path, "w", encoding='utf-8') as f:
        await f.write(f"Title: {request.title or ''}\nContent: {request.content or ''}")

async def process_image_files(device_dir: Path, files) -> list:
    """
    处理上传的图片文件列表

    Args:
        device_dir (Path): 设备目录路径
        files (List): 图片文件列表

    Returns:
        list: 包含所有文件元数据的列表
    """
    file_metas = []
    for file in files:
        file_meta = await save_single_file(device_dir, file)
        file_metas.append(file_meta)
    return file_metas

async def save_single_file(device_dir: Path, file) -> dict:
    """
    保存单个图片文件

    处理流程：
    1. 解码Base64数据
    2. 生成唯一文件名
    3. 计算文件哈希值
    4. 保存文件
    5. 生成文件元数据

    Args:
        device_dir (Path): 设备目录路径
        file: 包含文件数据的对象

    Returns:
        dict: 文件的元数据信息
    """
    file_data = base64.b64decode(file.data.encode())
    unique_filename = generate_unique_filename(file.filename)
    save_path = device_dir / "imgs" / unique_filename
    
    # 计算文件哈希
    hash_sha256 = sha256()
    hash_sha256.update(file_data)
    
    # 保存文件
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(file_data)
    
    return {
        "original_name": file.filename,
        "saved_path": str(save_path.relative_to(UPLOAD_DIR)),
        "sha256": hash_sha256.hexdigest(),
        "size": len(file_data)
    }

def create_response(request: UploadRequest, files_count: int) -> dict:
    """
    创建上传处理的响应数据

    Args:
        request (UploadRequest): 上传请求对象
        files_count (int): 处理的文件数量

    Returns:
        dict: 标准化的响应数据
    """
    return {
        "code": 1,
        "status": "success",
        "device_name": request.device_name,
        "timestamp": request.timestamp,
        "files_count": files_count,
    }