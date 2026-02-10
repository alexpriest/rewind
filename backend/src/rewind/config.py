import os
from pathlib import Path


class Settings:
    DATA_DIR: Path = Path.home() / "Code" / "projects" / "rewind" / "data"
    DB_PATH: Path = DATA_DIR / "rewind.db"
    PHOTOS_DIR: Path = DATA_DIR / "photos"
    THUMBNAILS_DIR: Path = DATA_DIR / "thumbnails"
    ANTHROPIC_API_KEY: str | None = os.environ.get("ANTHROPIC_API_KEY")


settings = Settings()

settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
settings.THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
