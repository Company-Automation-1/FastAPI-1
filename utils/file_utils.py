import uuid
from pathlib import Path

def generate_unique_filename(original_name: str) -> str:
    ext = Path(original_name).suffix
    return f"{uuid.uuid4().hex}{ext}"