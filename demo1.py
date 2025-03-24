from typing import List, Optional
from datetime import datetime
from pathlib import Path
import aiofiles
import hashlib
import uuid
import base64
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="设备数据上报接口",
    redoc_url=None
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FileBase64(BaseModel):
    filename: str
    data: str  # Base64 encoded string

    @validator('data')
    def validate_base64(cls, v):
        try:
            base64.b64decode(v, validate=True)
            return v
        except Exception as e:
            raise ValueError("Invalid Base64 data") from e

class UploadRequest(BaseModel):
    device_name: str = Field(..., min_length=2, max_length=50)
    timestamp: int = Field(..., gt=0)
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, max_length=1000)
    files: List[FileBase64]

class FileMeta(BaseModel):
    filename: str
    saved_path: str
    sha256: str
    size: int

class PostResponse(BaseModel):
    device_name: str
    timestamp: datetime
    content_path: str
    images: List[FileMeta]

@app.post("/upload/", 
          response_model=PostResponse, 
          status_code=status.HTTP_201_CREATED,
          tags=["Device Data"])
async def upload_data(request: UploadRequest):
    try:
        # 验证时间戳
        try:
            post_time = datetime.fromtimestamp(request.timestamp)
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timestamp: {request.timestamp}"
            ) from e

        # 创建存储路径
        time_dir = post_time.strftime("%Y%m%d%H%M%S")
        base_path = UPLOAD_DIR / request.device_name / time_dir
        img_dir = base_path / "imgs"
        img_dir.mkdir(parents=True, exist_ok=True)

        # 保存文本内容
        content_text = f"Title: {request.title or ''}\nContent: {request.content or ''}"
        content_path = base_path / "content.txt"
        async with aiofiles.open(content_path, "w", encoding='utf-8') as f:
            await f.write(content_text)

        # 处理Base64文件
        file_metas = []
        for file in request.files:
            # 解码Base64数据
            try:
                file_data = base64.b64decode(file.data)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Base64 decode failed for {file.filename}: {str(e)}"
                ) from e

            # 生成唯一文件名
            original_filename = Path(file.filename).name
            file_ext = Path(original_filename).suffix
            unique_name = f"{uuid.uuid4().hex}{file_ext}"
            save_path = img_dir / unique_name

            # 计算哈希和保存文件
            sha256 = hashlib.sha256()
            sha256.update(file_data)
            size = len(file_data)
            
            async with aiofiles.open(save_path, "wb") as buffer:
                await buffer.write(file_data)

            file_metas.append(FileMeta(
                filename=original_filename,
                saved_path=str(save_path.relative_to(UPLOAD_DIR)),
                sha256=sha256.hexdigest(),
                size=size
            ))

        return {
            "device_name": request.device_name,
            "timestamp": post_time,
            "content_path": str(content_path.relative_to(UPLOAD_DIR)),
            "images": file_metas
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        ) from e

@app.get("/demo/", tags=["Test"])
def demo_endpoint():
    return {"status": "active", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)