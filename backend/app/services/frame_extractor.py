"""Frame extraction service using FFmpeg."""
import subprocess
from pathlib import Path
from typing import List, Optional, Callable
from app.models.video import FrameData, SceneBoundary
from app.config import settings


class FrameExtractor:
    """Extracts frames from video at specified timestamps."""
    
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
            common_paths = [
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "ffmpeg"
            ]
            for path in common_paths:
                try:
                    subprocess.run([path, "-version"], capture_output=True, check=True)
                    return path
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries",
                    "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path)
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0
    
    def extract_frame_at_time(
        self,
        video_path: str,
        timestamp: float,
        output_path: str,
        quality: int = 2
    ) -> Optional[str]:
        """
        Extract a single frame at a specific timestamp.
        
        Args:
            video_path: Path to input video
            timestamp: Timestamp in seconds
            output_path: Path for output frame image
            quality: JPEG quality (1-31, lower is better)
        
        Returns:
            Path to extracted frame, or None if extraction fails
        """
        # Get video duration and ensure timestamp is valid
        duration = self._get_video_duration(video_path)
        if duration > 0 and timestamp >= duration - 0.5:  # Safety margin: don't extract within 0.5s of end
            # Try to extract at a slightly earlier time
            timestamp = max(0.0, duration - 1.0)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use better FFmpeg parameters for frame extraction
        cmd = [
            self.ffmpeg_path,
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", str(quality),
            "-f", "image2",
            "-y",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            # Verify the file was actually created
            if output_path.exists() and output_path.stat().st_size > 0:
                return str(output_path)
            else:
                return None
        except subprocess.CalledProcessError as e:
            # Log error but don't fail completely - return None to allow continuation
            print(f"Warning: Failed to extract frame at {timestamp}s: {e.stderr[:200]}")
            return None
    
    def extract_frames_at_scenes(
        self,
        video_path: str,
        scene_boundaries: List[SceneBoundary],
        output_dir: str,
        frame_number: int = 0
    ) -> List[FrameData]:
        """
        Extract frames at scene boundaries.
        
        Args:
            video_path: Path to input video
            scene_boundaries: List of scene boundaries
            output_dir: Directory for output frames
            frame_number: Starting frame number
        
        Returns:
            List of FrameData objects
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        frames = []
        current_frame_number = frame_number
        
        for scene in scene_boundaries:
            # Extract frame at start of scene
            frame_path = output_dir / f"frame_{current_frame_number:06d}.jpg"
            extracted_path = self.extract_frame_at_time(
                video_path,
                scene.start_time,
                str(frame_path)
            )
            
            # Only add frame if extraction succeeded
            if extracted_path:
                frames.append(FrameData(
                    frame_path=extracted_path,
                    timestamp=scene.start_time,
                    frame_number=current_frame_number
                ))
                current_frame_number += 1
        
        return frames
    
    def extract_frames_periodic(
        self,
        video_path: str,
        interval: float,
        output_dir: str,
        start_frame_number: int = 0
    ) -> List[FrameData]:
        """
        Extract frames at regular intervals.
        
        Args:
            video_path: Path to input video
            interval: Interval in seconds between frames
            output_dir: Directory for output frames
            start_frame_number: Starting frame number
        
        Returns:
            List of FrameData objects
        """
        # Get video duration
        duration = self._get_video_duration(video_path)
        
        if duration <= 0:
            return []
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        frames = []
        current_time = 0.0
        frame_number = start_frame_number
        
        # Stop extracting frames 1 second before the end to avoid edge cases
        max_time = duration - 1.0
        
        while current_time < max_time:
            frame_path = output_dir / f"frame_{frame_number:06d}.jpg"
            extracted_path = self.extract_frame_at_time(
                video_path,
                current_time,
                str(frame_path)
            )
            
            # Only add frame if extraction succeeded
            if extracted_path:
                frames.append(FrameData(
                    frame_path=extracted_path,
                    timestamp=current_time,
                    frame_number=frame_number
                ))
                frame_number += 1
            
            current_time += interval
        
        return frames
    
    def extract_frames(
        self,
        video_path: str,
        scene_boundaries: Optional[List[SceneBoundary]] = None,
        output_dir: str = "./temp/frames",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[FrameData]:
        """
        Extract frames from video at scene boundaries and periodic intervals.
        
        Args:
            video_path: Path to input video
            scene_boundaries: Optional list of scene boundaries
            output_dir: Directory for output frames
        
        Returns:
            List of FrameData objects
        """
        all_frames = []
        
        # Estimate total frames
        duration = self._get_video_duration(video_path)
        scene_count = len(scene_boundaries) if scene_boundaries else 0
        periodic_count = int((duration - 1.0) / settings.frame_extraction_interval) if duration > 0 else 0
        total_estimate = scene_count + periodic_count
        
        # Extract frames at scene boundaries
        if scene_boundaries:
            scene_frames = self.extract_frames_at_scenes(
                video_path,
                scene_boundaries,
                output_dir,
                frame_number=0
            )
            all_frames.extend(scene_frames)
            if progress_callback:
                progress_callback(len(all_frames), total_estimate)
        
        # Also extract frames at regular intervals for comprehensive coverage
        # Update progress during periodic extraction
        # Skip periodic extraction if configured (faster but may miss slides)
        if duration > 0 and not settings.skip_periodic_extraction:
            # Extract periodic frames with progress updates
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            
            current_time = 0.0
            frame_number = len(all_frames)
            max_time = duration - 1.0
            interval = settings.frame_extraction_interval
            
            while current_time < max_time:
                frame_path = output_dir_path / f"frame_{frame_number:06d}.jpg"
                extracted_path = self.extract_frame_at_time(
                    video_path,
                    current_time,
                    str(frame_path)
                )
                
                if extracted_path:
                    all_frames.append(FrameData(
                        frame_path=extracted_path,
                        timestamp=current_time,
                        frame_number=frame_number
                    ))
                    frame_number += 1
                    if progress_callback:
                        progress_callback(len(all_frames), total_estimate)
                
                current_time += interval
        else:
            periodic_frames = self.extract_frames_periodic(
                video_path,
                settings.frame_extraction_interval,
                output_dir,
                start_frame_number=len(all_frames)
            )
            all_frames.extend(periodic_frames)
            if progress_callback:
                progress_callback(len(all_frames), total_estimate)
        
        # Remove duplicates (same timestamp)
        seen_timestamps = set()
        unique_frames = []
        for frame in all_frames:
            rounded_time = round(frame.timestamp, 1)
            if rounded_time not in seen_timestamps:
                seen_timestamps.add(rounded_time)
                unique_frames.append(frame)
        
        return unique_frames

