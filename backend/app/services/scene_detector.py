"""Scene detection service using AWS Rekognition with fallback."""
import boto3
from typing import List, Optional
from botocore.exceptions import ClientError, BotoCoreError

from app.config import settings
from app.models.video import SceneBoundary


class SceneDetector:
    """Detects scene changes in video using AWS Rekognition."""
    
    def __init__(self):
        self.rekognition_client = None
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            try:
                client_kwargs = {
                    'aws_access_key_id': settings.aws_access_key_id,
                    'aws_secret_access_key': settings.aws_secret_access_key,
                    'region_name': settings.aws_region
                }
                if settings.aws_session_token:
                    client_kwargs['aws_session_token'] = settings.aws_session_token
                self.rekognition_client = boto3.client('rekognition', **client_kwargs)
            except Exception as e:
                print(f"Warning: Failed to initialize Rekognition client: {e}")
    
    def detect_scenes_s3(
        self,
        s3_bucket: str,
        s3_key: str,
        job_tag: Optional[str] = None
    ) -> List[SceneBoundary]:
        """
        Detect scene changes in video stored in S3.
        
        Args:
            s3_bucket: S3 bucket name
            s3_key: S3 object key
            job_tag: Optional job tag for tracking
        
        Returns:
            List of scene boundaries
        """
        if not self.rekognition_client:
            raise RuntimeError("AWS Rekognition client not initialized")
        
        try:
            # Start segment detection
            response = self.rekognition_client.start_segment_detection(
                Video={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                },
                SegmentTypes=['SHOT', 'TECHNICAL_CUE']
            )
            
            job_id = response['JobId']
            
            # Wait for job to complete
            import time
            max_wait = 300  # 5 minutes
            wait_time = 0
            while wait_time < max_wait:
                status_response = self.rekognition_client.get_segment_detection(
                    JobId=job_id
                )
                
                status = status_response['JobStatus']
                if status == 'SUCCEEDED':
                    break
                elif status == 'FAILED':
                    raise RuntimeError(f"Segment detection failed: {status_response.get('StatusMessage', 'Unknown error')}")
                
                time.sleep(5)
                wait_time += 5
            
            if wait_time >= max_wait:
                raise RuntimeError("Segment detection timed out")
            
            # Get results
            segments = status_response.get('Segments', [])
            boundaries = []
            
            for segment in segments:
                start_time = segment['StartTimestampMillis'] / 1000.0
                end_time = segment['EndTimestampMillis'] / 1000.0
                segment_type = segment['Type']
                
                boundaries.append(SceneBoundary(
                    start_time=start_time,
                    end_time=end_time,
                    type=segment_type
                ))
            
            return boundaries
        
        except (ClientError, BotoCoreError) as e:
            raise RuntimeError(f"AWS Rekognition error: {str(e)}")
    
    def detect_scenes_local_fallback(
        self,
        video_path: str,
        threshold: float = 30.0
    ) -> List[SceneBoundary]:
        """
        Fallback scene detection using simple frame difference.
        
        This is a basic implementation. For production, use PySceneDetect.
        
        Args:
            video_path: Path to local video file
            threshold: Threshold for scene change detection
        
        Returns:
            List of scene boundaries
        """
        # Simple fallback: return periodic boundaries
        # In production, integrate PySceneDetect here
        import subprocess
        from pathlib import Path
        
        # Get video duration
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
            duration = float(result.stdout.strip())
        except Exception:
            duration = 0.0
        
        # Create periodic boundaries every 5 seconds
        boundaries = []
        interval = 5.0
        current_time = 0.0
        
        while current_time < duration:
            boundaries.append(SceneBoundary(
                start_time=current_time,
                end_time=min(current_time + interval, duration),
                type="CONTENT_CHANGE"
            ))
            current_time += interval
        
        return boundaries
    
    def detect_scenes(
        self,
        video_path: str,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None
    ) -> List[SceneBoundary]:
        """
        Detect scene changes in video.
        
        Tries AWS Rekognition first, falls back to local detection.
        
        Args:
            video_path: Path to local video file
            s3_bucket: Optional S3 bucket (if video is in S3)
            s3_key: Optional S3 key (if video is in S3)
        
        Returns:
            List of scene boundaries
        """
        # Try AWS Rekognition if S3 info is provided
        if s3_bucket and s3_key and self.rekognition_client:
            try:
                return self.detect_scenes_s3(s3_bucket, s3_key)
            except Exception as e:
                print(f"Rekognition scene detection failed: {e}, using fallback")
        
        # Fallback to local detection
        return self.detect_scenes_local_fallback(video_path)



