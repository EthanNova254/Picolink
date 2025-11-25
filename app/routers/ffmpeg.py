"""
FFmpeg router - Video/audio processing endpoints
NO AI features (transcription/captioning removed)
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from app.services.ffmpeg_service import ffmpeg_service
from app.utils import save_upload_file, cleanup_file, VIDEO_TYPES, AUDIO_TYPES

router = APIRouter(prefix="/ffmpeg", tags=["Video/Audio Processing"])

@router.post("/info")
async def get_media_info(file: UploadFile = File(...)):
    """
    Get detailed media information
    
    **Returns:**
    - Duration, size, bitrate
    - Video: codec, resolution, fps
    - Audio: codec, sample rate, channels
    
    **Use cases:**
    - Validate video before processing
    - Get video metadata
    - Check compatibility
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/ffmpeg/info",
      "body": {
        "file": "@video.mp4"
      }
    }
    ```
    """
    file_path, mime = await save_upload_file(file, VIDEO_TYPES | AUDIO_TYPES)
    
    try:
        result = ffmpeg_service.get_media_info(file_path)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    finally:
        cleanup_file(file_path)

@router.post("/trim")
async def trim_video(
    file: UploadFile = File(...),
    start_time: float = Form(...),
    end_time: Optional[float] = Form(None),
    duration: Optional[float] = Form(None)
):
    """
    Trim video to specific timeframe
    
    **Parameters:**
    - file: Video file
    - start_time: Start timestamp (seconds)
    - end_time: End timestamp OR
    - duration: Duration from start
    
    **Use either end_time OR duration, not both**
    
    **Use cases:**
    - Cut video clips
    - Remove unwanted sections
    - Extract highlights
    
    **Speed:** Very fast (no re-encoding)
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/ffmpeg/trim",
      "body": {
        "file": "@video.mp4",
        "start_time": 10.5,
        "duration": 30
      }
    }
    ```
    
    **Response:** Returns trimmed video file
    """
    if not end_time and not duration:
        raise HTTPException(
            status_code=400,
            detail="Must provide either end_time or duration"
        )
    
    if end_time and duration:
        raise HTTPException(
            status_code=400,
            detail="Provide only end_time OR duration, not both"
        )
    
    file_path, mime = await save_upload_file(file, VIDEO_TYPES)
    
    try:
        success, output_path, message = ffmpeg_service.trim_video(
            file_path,
            start_time,
            end_time,
            duration
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"trimmed_{output_path.name}"
        )
    
    finally:
        cleanup_file(file_path)

@router.post("/merge")
async def merge_videos(files: List[UploadFile] = File(...)):
    """
    Merge multiple videos into one
    
    **Parameters:**
    - files: List of video files (must be same codec/resolution)
    
    **Requirements:**
    - All videos must have same:
      - Resolution
      - Codec
      - Frame rate
    
    **Use cases:**
    - Combine video clips
    - Join split files
    - Create compilations
    
    **Limits:**
    - Max 20 videos per request
    
    **n8n example:**
    Upload multiple videos with field name "files"
    """
    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Too many files. Max 20 videos per request"
        )
    
    saved_paths = []
    
    try:
        for file in files:
            file_path, mime = await save_upload_file(file, VIDEO_TYPES)
            saved_paths.append(file_path)
        
        success, output_path, message = ffmpeg_service.merge_videos(saved_paths)
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"merged_{output_path.name}"
        )
    
    finally:
        for path in saved_paths:
            cleanup_file(path)

@router.post("/resize")
async def resize_video(
    file: UploadFile = File(...),
    width: int = Form(...),
    height: int = Form(...),
    maintain_aspect: bool = Form(True)
):
    """
    Resize video to specific dimensions
    
    **Parameters:**
    - width: Target width (pixels)
    - height: Target height (pixels)
    - maintain_aspect: Keep aspect ratio
    
    **Common sizes:**
    - 1920x1080: Full HD
    - 1280x720: HD
    - 854x480: SD
    - 640x360: Mobile
    
    **Use cases:**
    - Reduce video size
    - Prepare for specific platforms
    - Standardize dimensions
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/ffmpeg/resize",
      "body": {
        "file": "@video.mp4",
        "width": 1280,
        "height": 720,
        "maintain_aspect": true
      }
    }
    ```
    """
    file_path, mime = await save_upload_file(file, VIDEO_TYPES)
    
    try:
        success, output_path, message = ffmpeg_service.resize_video(
            file_path,
            width,
            height,
            maintain_aspect
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"resized_{output_path.name}"
        )
    
    finally:
        cleanup_file(file_path)

@router.post("/compress")
async def compress_video(
    file: UploadFile = File(...),
    crf: int = Form(23),
    max_bitrate: Optional[str] = Form(None)
):
    """
    Compress video to reduce file size
    
    **Parameters:**
    - crf: Constant Rate Factor (0-51)
      - 18: High quality (large file)
      - 23: Default (balanced)
      - 28: Lower quality (small file)
    - max_bitrate: Optional max bitrate (e.g., "1M", "500k")
    
    **Use cases:**
    - Reduce file size for storage
    - Optimize for web
    - Email-friendly videos
    
    **Typical compression:**
    - CRF 23: 40-60% reduction
    - CRF 28: 60-80% reduction
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/ffmpeg/compress",
      "body": {
        "file": "@video.mp4",
        "crf": 28,
        "max_bitrate": "1M"
      }
    }
    ```
    """
    if crf < 0 or crf > 51:
        raise HTTPException(
            status_code=400,
            detail="CRF must be between 0 and 51"
        )
    
    file_path, mime = await save_upload_file(file, VIDEO_TYPES)
    
    try:
        success, output_path, message = ffmpeg_service.compress_video(
            file_path,
            crf,
            max_bitrate
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename=f"compressed_{output_path.name}"
        )
    
    finally:
        cleanup_file(file_path)

@router.post("/extract-audio")
async def extract_audio(
    file: UploadFile = File(...),
    format: str = Form("mp3"),
    bitrate: str = Form("192k")
):
    """
    Extract audio from video
    
    **Parameters:**
    - format: mp3, wav, ogg
    - bitrate: Audio bitrate (e.g., "128k", "192k", "320k")
    
    **Use cases:**
    - Get audio track
    - Create podcasts from videos
    - Extract music
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/ffmpeg/extract-audio",
      "body": {
        "file": "@video.mp4",
        "format": "mp3",
        "bitrate": "192k"
      }
    }
    ```
    """
    if format not in ["mp3", "wav", "ogg"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Use: mp3, wav, or ogg"
        )
    
    file_path, mime = await save_upload_file(file, VIDEO_TYPES)
    
    try:
        success, output_path, message = ffmpeg_service.extract_audio(
            file_path,
            format,
            bitrate
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        audio_mime = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg"
        }[format]
        
        return FileResponse(
            path=output_path,
            media_type=audio_mime,
            filename=f"audio_{output_path.name}"
        )
    
    finally:
        cleanup_file(file_path)

@router.post("/thumbnail")
async def generate_thumbnail(
    file: UploadFile = File(...),
    timestamp: float = Form(1.0),
    width: int = Form(640)
):
    """
    Generate thumbnail image from video
    
    **Parameters:**
    - timestamp: Time to capture (seconds)
    - width: Thumbnail width (height auto-scaled)
    
    **Use cases:**
    - Video previews
    - Gallery thumbnails
    - Social media images
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/ffmpeg/thumbnail",
      "body": {
        "file": "@video.mp4",
        "timestamp": 5.0,
        "width": 1280
      }
    }
    ```
    """
    file_path, mime = await save_upload_file(file, VIDEO_TYPES)
    
    try:
        success, output_path, message = ffmpeg_service.generate_thumbnail(
            file_path,
            timestamp,
            width
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return FileResponse(
            path=output_path,
            media_type="image/jpeg",
            filename=f"thumb_{output_path.name}"
        )
    
    finally:
        cleanup_file(file_path)

@router.post("/convert")
async def convert_format(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    codec: Optional[str] = Form(None)
):
    """
    Convert video to different format
    
    **Parameters:**
    - output_format: mp4, webm, avi, mkv, mov
    - codec: Optional codec (e.g., libx264, libvpx)
    
    **Common conversions:**
    - To MP4: output_format=mp4, codec=libx264
    - To WebM: output_format=webm, codec=libvpx
    
    **Use cases:**
    - Format compatibility
    - Platform requirements
    - Codec changes
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/ffmpeg/convert",
      "body": {
        "file": "@video.avi",
        "output_format": "mp4",
        "codec": "libx264"
      }
    }
    ```
    """
    valid_formats = ["mp4", "webm", "avi", "mkv", "mov"]
    if output_format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Use: {', '.join(valid_formats)}"
        )
    
    file_path, mime = await save_upload_file(file, VIDEO_TYPES)
    
    try:
        success, output_path, message = ffmpeg_service.convert_format(
            file_path,
            output_format,
            codec
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return FileResponse(
            path=output_path,
            media_type=f"video/{output_format}",
            filename=f"converted_{output_path.name}"
        )
    
    finally:
        cleanup_file(file_path)
