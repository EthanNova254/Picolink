"""
Health check and system info endpoints
"""
import subprocess
import psutil
from fastapi import APIRouter
from app.config import settings
from app.services.ocr_service import ocr_service

router = APIRouter(tags=["System"])

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns service status and availability
    """
    return {
        "status": "healthy",
        "service": "all-in-one-api",
        "version": "1.0.0"
    }

@router.get("/info")
async def system_info():
    """
    Get system information and capabilities
    
    **Returns:**
    - Service versions
    - Resource usage
    - Available features
    - Configuration
    """
    # Get FFmpeg version
    try:
        ffmpeg_result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True
        )
        ffmpeg_version = ffmpeg_result.stdout.split('\n')[0]
    except:
        ffmpeg_version = "Not available"
    
    # Get Tesseract version
    try:
        tess_result = subprocess.run(
            ['tesseract', '--version'],
            capture_output=True,
            text=True
        )
        tess_version = tess_result.stdout.split('\n')[0]
    except:
        tess_version = "Not available"
    
    # Get system resources
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    return {
        "service": "All-in-One API Service",
        "version": "1.0.0",
        "components": {
            "crawl4ai": "0.3.74",
            "tesseract": tess_version,
            "ffmpeg": ffmpeg_version,
            "pdf_generation": "Multiple libraries"
        },
        "capabilities": {
            "web_scraping": True,
            "ocr": True,
            "pdf_generation": True,
            "video_processing": True,
            "audio_extraction": True
        },
        "resources": {
            "cpu_usage_percent": cpu_percent,
            "memory_total_mb": memory.total / (1024**2),
            "memory_available_mb": memory.available / (1024**2),
            "memory_used_percent": memory.percent
        },
        "configuration": {
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE,
            "max_crawl_pages": settings.MAX_CRAWL_PAGES,
            "max_pdf_pages": settings.MAX_PDF_PAGES,
            "cleanup_hours": settings.CLEANUP_HOURS
        },
        "ocr_languages": ocr_service.get_available_languages()
    }

@router.get("/")
async def root():
    """
    Root endpoint - API documentation link
    """
    return {
        "message": "All-in-One API Service",
        "documentation": "/docs",
        "health": "/health",
        "info": "/info",
        "endpoints": {
            "web_scraping": "/crawl/*",
            "ocr": "/ocr/*",
            "pdf_generation": "/pdf/*",
            "video_processing": "/ffmpeg/*"
        }
    }
