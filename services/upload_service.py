import base64
import aiofiles
from pathlib import Path
from hashlib import sha256
import uuid
from datetime import datetime
from models.request import UploadRequest
from core.config import UPLOAD_DIR
from utils.file_utils import generate_unique_filename

async def process_upload(request: UploadRequest) -> dict:
    # 仅用于创建目录结构时转换时间戳
    dir_time = datetime.fromtimestamp(request.timestamp)
    time_dir = dir_time.strftime("%Y%m%d%H%M%S")
    device_dir = UPLOAD_DIR / request.device_name / time_dir
    (device_dir / "imgs").mkdir(parents=True, exist_ok=True)

    # 保存文本内容
    content_path = device_dir / "content.txt"
    async with aiofiles.open(content_path, "w", encoding='utf-8') as f:
        await f.write(f"Title: {request.title or ''}\nContent: {request.content or ''}")

    # 处理文件
    file_metas = []
    for file in request.files:
        file_data = base64.b64decode(file.data.encode())
        unique_filename = generate_unique_filename(file.filename)
        save_path = device_dir / "imgs" / unique_filename
        
        # 计算哈希
        hash_sha256 = sha256()
        hash_sha256.update(file_data)
        file_size = len(file_data)
        
        async with aiofiles.open(save_path, "wb") as f:
            await f.write(file_data)
        
        file_metas.append({
            "original_name": file.filename,
            "saved_path": str(save_path.relative_to(UPLOAD_DIR)),
            "sha256": hash_sha256.hexdigest(),
            "size": file_size
        })

    return {
        "code": 1,
        "status": "success",
        "device_name": request.device_name,
        "timestamp": request.timestamp,  # 使用原始时间戳
        "files_count": len(file_metas),
    }