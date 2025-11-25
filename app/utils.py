"""
Utility functions for file handling, validation, and common operations
"""
import os
import uuid
import magic
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from app.config import settings

# Allowed file types
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heif", "image/heic"}
PDF_TYPES = {"application/pdf"}
VIDEO_TYPES = {"video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/webm"}
AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/webm"}

def generate_filename(extension: str = "") -> str:
    """Generate unique filename with UUID"""
    unique_id = uuid.uuid4().hex[:12]
    if extension and not extension.startswith("."):
        extension = f".{extension}"
    return f"{unique_id}{extension}"

def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

async def save_upload_file(
    upload_file: UploadFile,
    allowed_types: set,
    max_size_mb: Optional[int] = None
) -> Tuple[Path, str]:
    """
    Save uploaded file with validation
    Returns: (file_path, mime_type)
    """
    # Read file content
    content = await upload_file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    # Check size
    max_size = max_size_mb or settings.MAX_UPLOAD_SIZE
    if file_size_mb > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {max_size}MB"
        )
    
    # Detect MIME type
    mime = magic.from_buffer(content, mime=True)
    
    # Validate type
    if mime not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Generate filename with proper extension
    ext = upload_file.filename.split(".")[-1] if "." in upload_file.filename else ""
    filename = generate_filename(ext)
    file_path = settings.UPLOAD_DIR / filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path, mime

def cleanup_file(file_path: Path) -> None:
    """Safely delete file"""
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except Exception:
        pass  # Silent fail

def get_file_extension(mime_type: str) -> str:
    """Get file extension from MIME type"""
    mime_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/heif": "heif",
        "image/heic": "heic",
        "application/pdf": "pdf",
        "video/mp4": "mp4",
        "video/mpeg": "mpeg",
        "video/quicktime": "mov",
        "video/webm": "webm",
        "audio/mpeg": "mp3",
        "audio/wav": "wav",
        "audio/ogg": "ogg",
    }
    return mime_map.get(mime_type, "bin")

def validate_url(url: str) -> bool:
    """Basic URL validation"""
    return url.startswith(("http://", "https://"))

def format_bytes(bytes_count: int) -> str:
    """Format bytes to human readable"""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_count < 1024:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.2f} TB"
