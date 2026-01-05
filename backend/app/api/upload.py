"""Video upload API endpoint."""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.models.video import VideoUploadResponse, ProcessingStatus
from app.storage import jobs_db

router = APIRouter(prefix="/api", tags=["upload"])

# Initialize S3 client if credentials are available
s3_client = None
if settings.aws_access_key_id and settings.aws_secret_access_key:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region
    )


def validate_video_file(filename: str) -> bool:
    """Validate video file format."""
    allowed_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
    return Path(filename).suffix.lower() in allowed_extensions


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file for processing.
    
    Accepts multipart file uploads, validates format, stores in S3 or local storage,
    and returns a job ID for status tracking.
    """
    # Validate file format
    if not validate_video_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid video format. Allowed: mp4, mov, avi, mkv, webm, m4v"
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file locally or to S3
    local_file_path = upload_dir / f"{job_id}_{file.filename}"
    
    try:
        # Save file locally
        with open(local_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Upload to S3 if configured
        s3_key = None
        if s3_client and settings.s3_bucket_name:
            try:
                s3_key = f"videos/{job_id}/{file.filename}"
                s3_client.upload_file(
                    str(local_file_path),
                    settings.s3_bucket_name,
                    s3_key
                )
            except ClientError as e:
                # Log error but continue with local storage
                print(f"Failed to upload to S3: {e}")
        
        # Store job metadata
        jobs_db[job_id] = {
            "job_id": job_id,
            "filename": file.filename,
            "local_path": str(local_file_path),
            "s3_key": s3_key,
            "status": ProcessingStatus.QUEUED,
            "created_at": None,
            "updated_at": None
        }
        
        # Start processing in background (for now, synchronous)
        # In production, this would be async with Celery/Redis
        from datetime import datetime
        jobs_db[job_id]["created_at"] = datetime.now()
        jobs_db[job_id]["updated_at"] = datetime.now()
        
        # Start processing (import here to avoid circular dependency)
        from app.services.video_processor import VideoProcessor
        processor = VideoProcessor()
        processor.process_video_async(job_id, str(local_file_path))
        
        return VideoUploadResponse(
            job_id=job_id,
            status=ProcessingStatus.QUEUED,
            message="Video uploaded successfully. Processing started."
        )
    
    except Exception as e:
        # Clean up on error
        if local_file_path.exists():
            local_file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}"
        )

