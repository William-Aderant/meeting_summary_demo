"""Audio extraction service using FFmpeg."""
import subprocess
from pathlib import Path
from typing import Optional


class AudioExtractor:
    """Extracts audio track from video files using FFmpeg."""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable."""
        try:
            result = subprocess.run(
                ["which", "ffmpeg"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try common paths
            common_paths = [
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "ffmpeg"  # Assume it's in PATH
            ]
            for path in common_paths:
                try:
                    subprocess.run([path, "-version"], capture_output=True, check=True)
                    return path
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def has_audio_stream(self, video_path: str) -> bool:
        """
        Check if video file has an audio stream using ffprobe.
        
        Args:
            video_path: Path to input video file
        
        Returns:
            True if audio stream exists, False otherwise
        """
        try:
            # Try to find ffprobe (usually in same location as ffmpeg)
            ffprobe_path = self.ffmpeg_path.replace("ffmpeg", "ffprobe")
            if not Path(ffprobe_path).exists():
                # Try common paths
                for path in ["ffprobe", "/usr/bin/ffprobe", "/usr/local/bin/ffprobe"]:
                    try:
                        subprocess.run([path, "-version"], capture_output=True, check=True)
                        ffprobe_path = path
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    # Fallback: use ffmpeg to check
                    return self._check_audio_with_ffmpeg(video_path)
            
            # Use ffprobe to list streams
            result = subprocess.run(
                [
                    ffprobe_path,
                    "-v", "error",
                    "-select_streams", "a",  # Select audio streams only
                    "-show_entries", "stream=codec_type",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path)
                ],
                capture_output=True,
                text=True,
                check=False
            )
            # If we get any output, there's an audio stream
            return bool(result.stdout.strip())
        except Exception:
            return self._check_audio_with_ffmpeg(video_path)
    
    def _check_audio_with_ffmpeg(self, video_path: str) -> bool:
        """Fallback method to check for audio using ffmpeg."""
        try:
            result = subprocess.run(
                [
                    self.ffmpeg_path,
                    "-i", str(video_path),
                    "-hide_banner"
                ],
                capture_output=True,
                text=True,
                stderr=subprocess.STDOUT
            )
            # Check if output contains audio stream info
            output = result.stdout + result.stderr
            # Look for audio stream indicators
            return "Audio:" in output or ("Stream #" in output and "Audio" in output)
        except Exception:
            return False
    
    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        format: str = "wav"
    ) -> Optional[str]:
        """
        Extract audio track from video file.
        
        Args:
            video_path: Path to input video file
            output_path: Path for output audio file (optional)
            format: Audio format (wav, mp3, etc.)
        
        Returns:
            Path to extracted audio file, or None if no audio stream exists
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Check if video has audio stream
        if not self.has_audio_stream(str(video_path)):
            return None
        
        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_audio.{format}"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # FFmpeg command to extract audio
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
            "-ar", "16000",  # Sample rate for speech recognition
            "-ac", "1",  # Mono channel
            "-y",  # Overwrite output file
            str(output_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return str(output_path)
        except subprocess.CalledProcessError as e:
            # Check if error is due to no audio stream
            error_output = e.stderr.lower()
            if "does not contain any stream" in error_output or "no audio stream" in error_output:
                return None
            raise RuntimeError(
                f"Failed to extract audio: {e.stderr}"
            ) from e

