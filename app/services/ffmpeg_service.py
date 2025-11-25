"""
FFmpeg service - Video/audio processing
NO AI features (transcription, captioning removed)
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.config import settings
from app.utils import generate_filename

class FFmpegService:
    """Local FFmpeg video/audio processing"""
    
    def __init__(self):
        self.threads = settings.FFMPEG_THREADS
        self.preset = settings.FFMPEG_PRESET
    
    def get_media_info(self, file_path: Path) -> Dict:
        """Get detailed media information using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            
            # Extract key info
            format_info = data.get('format', {})
            streams = data.get('streams', [])
            
            video_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in streams if s['codec_type'] == 'audio'), None)
            
            return {
                "success": True,
                "duration": float(format_info.get('duration', 0)),
                "size": int(format_info.get('size', 0)),
                "bit_rate": int(format_info.get('bit_rate', 0)),
                "format": format_info.get('format_name'),
                "video": {
                    "codec": video_stream.get('codec_name') if video_stream else None,
                    "width": video_stream.get('width') if video_stream else None,
                    "height": video_stream.get('height') if video_stream else None,
                    "fps": eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else None
                } if video_stream else None,
                "audio": {
                    "codec": audio_stream.get('codec_name') if audio_stream else None,
                    "sample_rate": audio_stream.get('sample_rate') if audio_stream else None,
                    "channels": audio_stream.get('channels') if audio_stream else None
                } if audio_stream else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def trim_video(
        self,
        input_path: Path,
        start_time: float,
        end_time: Optional[float] = None,
        duration: Optional[float] = None
    ) -> Tuple[bool, Path, str]:
        """
        Trim video
        Use either end_time OR duration, not both
        """
        output_path = settings.OUTPUT_DIR / generate_filename("mp4")
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-ss', str(start_time),
            '-threads', str(self.threads)
        ]
        
        if duration:
            cmd.extend(['-t', str(duration)])
        elif end_time:
            cmd.extend(['-to', str(end_time)])
        
        cmd.extend([
            '-c', 'copy',  # Copy without re-encoding (fast)
            '-y',
            str(output_path)
        ])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True, output_path, "Video trimmed successfully"
        except subprocess.CalledProcessError as e:
            return False, None, f"FFmpeg error: {e.stderr.decode()}"
    
    def merge_videos(self, input_paths: List[Path]) -> Tuple[bool, Path, str]:
        """Merge multiple videos"""
        # Create concat file
        concat_file = settings.TEMP_DIR / generate_filename("txt")
        with open(concat_file, 'w') as f:
            for path in input_paths:
                f.write(f"file '{path.absolute()}'\n")
        
        output_path = settings.OUTPUT_DIR / generate_filename("mp4")
        
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            '-threads', str(self.threads),
            '-y',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            concat_file.unlink()  # Cleanup
            return True, output_path, f"Merged {len(input_paths)} videos"
        except subprocess.CalledProcessError as e:
            return False, None, f"FFmpeg error: {e.stderr.decode()}"
    
    def resize_video(
        self,
        input_path: Path,
        width: int,
        height: int,
        maintain_aspect: bool = True
    ) -> Tuple[bool, Path, str]:
        """Resize video"""
        output_path = settings.OUTPUT_DIR / generate_filename("mp4")
        
        if maintain_aspect:
            scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease"
        else:
            scale_filter = f"scale={width}:{height}"
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-vf', scale_filter,
            '-c:v', 'libx264',
            '-preset', self.preset,
            '-c:a', 'copy',
            '-threads', str(self.threads),
            '-y',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True, output_path, f"Resized to {width}x{height}"
        except subprocess.CalledProcessError as e:
            return False, None, f"FFmpeg error: {e.stderr.decode()}"
    
    def compress_video(
        self,
        input_path: Path,
        crf: int = 23,  # 0-51, lower = better quality
        max_bitrate: Optional[str] = None
    ) -> Tuple[bool, Path, str]:
        """
        Compress video
        crf: 18 = high quality, 23 = default, 28 = lower quality
        """
        output_path = settings.OUTPUT_DIR / generate_filename("mp4")
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-crf', str(crf),
            '-preset', self.preset,
            '-c:a', 'aac',
            '-b:a', '128k',
            '-threads', str(self.threads)
        ]
        
        if max_bitrate:
            cmd.extend(['-maxrate', max_bitrate, '-bufsize', max_bitrate])
        
        cmd.extend(['-y', str(output_path)])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Get size reduction
            original_size = input_path.stat().st_size
            new_size = output_path.stat().st_size
            reduction = (1 - new_size / original_size) * 100
            
            return True, output_path, f"Compressed {reduction:.1f}% smaller"
        except subprocess.CalledProcessError as e:
            return False, None, f"FFmpeg error: {e.stderr.decode()}"
    
    def extract_audio(
        self,
        input_path: Path,
        format: str = "mp3",
        bitrate: str = "192k"
    ) -> Tuple[bool, Path, str]:
        """Extract audio from video"""
        output_path = settings.OUTPUT_DIR / generate_filename(format)
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-vn',  # No video
            '-acodec', 'libmp3lame' if format == 'mp3' else 'copy',
            '-b:a', bitrate,
            '-threads', str(self.threads),
            '-y',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True, output_path, "Audio extracted"
        except subprocess.CalledProcessError as e:
            return False, None, f"FFmpeg error: {e.stderr.decode()}"
    
    def generate_thumbnail(
        self,
        input_path: Path,
        timestamp: float = 1.0,
        width: int = 640
    ) -> Tuple[bool, Path, str]:
        """Generate thumbnail from video"""
        output_path = settings.OUTPUT_DIR / generate_filename("jpg")
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-ss', str(timestamp),
            '-vframes', '1',
            '-vf', f'scale={width}:-1',
            '-y',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True, output_path, "Thumbnail generated"
        except subprocess.CalledProcessError as e:
            return False, None, f"FFmpeg error: {e.stderr.decode()}"
    
    def convert_format(
        self,
        input_path: Path,
        output_format: str,
        codec: Optional[str] = None
    ) -> Tuple[bool, Path, str]:
        """Convert video to different format"""
        output_path = settings.OUTPUT_DIR / generate_filename(output_format)
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-threads', str(self.threads)
        ]
        
        if codec:
            cmd.extend(['-c:v', codec])
        
        cmd.extend(['-y', str(output_path)])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True, output_path, f"Converted to {output_format}"
        except subprocess.CalledProcessError as e:
            return False, None, f"FFmpeg error: {e.stderr.decode()}"

# Singleton instance
ffmpeg_service = FFmpegService()
