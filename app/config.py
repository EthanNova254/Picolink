"""
Configuration module for All-in-One API Service
Optimized for Koyeb free tier constraints
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "2"))
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "100"))  # MB
    
    # Storage paths
    BASE_DIR: Path = Path("/app")
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    OUTPUT_DIR: Path = STORAGE_DIR / "outputs"
    TEMP_DIR: Path = STORAGE_DIR / "temp"
    
    # Cleanup
    CLEANUP_HOURS: int = int(os.getenv("CLEANUP_HOURS", "24"))
    
    # Resource limits (Koyeb free tier: 2GB RAM, 2 cores)
    MAX_CONCURRENT_REQUESTS: int = 10
    MAX_CRAWL_PAGES: int = 50  # Per request
    MAX_PDF_PAGES: int = 500
    MAX_VIDEO_DURATION: int = 600  # 10 minutes
    
    # Crawl4AI
    CRAWL_TIMEOUT: int = 60  # seconds
    CRAWL_USER_AGENT: str = "Mozilla/5.0 (compatible; AllInOneService/1.0)"
    
    # OCR
    TESSERACT_LANG: str = "eng"  # Default language
    OCR_DPI: int = 300
    
    # PDF
    PDF_PAGE_SIZE: str = "A4"
    PDF_MARGIN: int = 36  # points (0.5 inch)
    
    # FFmpeg
    FFMPEG_THREADS: int = 2
    FFMPEG_PRESET: str = "medium"  # ultrafast, fast, medium, slow
    
    class Config:
        case_sensitive = True

settings = Settings()

# Ensure directories exist
for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
