from pydantic import BaseModel, Field, validator
from typing import List, Optional
import base64

class FileBase64(BaseModel):
    filename: str
    data: str

    @validator('data')
    def validate_base64(cls, v):
        try:
            base64.b64decode(v.encode(), validate=True)
            return v
        except Exception as e:
            raise ValueError("Invalid Base64 data") from e

class UploadRequest(BaseModel):
    device_name: str = Field(..., min_length=2, max_length=50)
    timestamp: int = Field(..., gt=0)
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, max_length=1000)
    files: List[FileBase64]