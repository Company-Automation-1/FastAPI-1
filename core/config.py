from pathlib import Path
from datetime import datetime, timedelta, timezone

PROJECT_DIR = Path(__file__).parent.parent
UPLOAD_DIR = PROJECT_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    DEBUG = True
    TIMEZONE = timezone(timedelta(hours=8))  # 修改为timezone对象
    SCHEDULER_TIMEZONE = timezone(timedelta(hours=8))  # 修改为timezone对象
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB