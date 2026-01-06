"""Video upload API endpoint."""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.models.video import VideoUploadResponse, ProcessingStatus, ProcessingOptions
from app.storage import jobs_db

router = APIRouter(prefix="/api", tags=["upload"])

# Initialize S3 client if credentials are available
s3_client = None
# #region agent log
try:
    import json as json_module
    log_data = {
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "S3_INIT_A",
        "location": "upload.py:s3_client_init",
        "message": "Checking AWS credentials for S3 client initialization",
        "data": {
            "has_access_key_id": bool(settings.aws_access_key_id),
            "access_key_id_length": len(settings.aws_access_key_id) if settings.aws_access_key_id else 0,
            "access_key_id_preview": settings.aws_access_key_id[:8] + "..." if settings.aws_access_key_id and len(settings.aws_access_key_id) > 8 else (settings.aws_access_key_id if settings.aws_access_key_id else None),
            "has_secret_access_key": bool(settings.aws_secret_access_key),
            "secret_key_length": len(settings.aws_secret_access_key) if settings.aws_secret_access_key else 0,
            "has_session_token": bool(settings.aws_session_token),
            "aws_region": settings.aws_region,
            "s3_bucket_name": settings.s3_bucket_name
        },
        "timestamp": int(__import__("time").time() * 1000)
    }
    with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
        f.write(json_module.dumps(log_data) + "\n")
except Exception:
    pass
# #endregion
if settings.aws_access_key_id and settings.aws_secret_access_key:
    # #region agent log
    try:
        import json as json_module
        log_data = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "S3_INIT_B",
            "location": "upload.py:s3_client_creating",
            "message": "Creating S3 client with credentials",
            "data": {
                "region": settings.aws_region,
                "access_key_id_preview": settings.aws_access_key_id[:8] + "..." if len(settings.aws_access_key_id) > 8 else settings.aws_access_key_id,
                "access_key_id_length": len(settings.aws_access_key_id),
                "secret_key_length": len(settings.aws_secret_access_key) if settings.aws_secret_access_key else 0,
                "has_session_token": bool(settings.aws_session_token),
                "session_token_included": bool(settings.aws_session_token)
            },
            "timestamp": int(__import__("time").time() * 1000)
        }
        with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
            f.write(json_module.dumps(log_data) + "\n")
    except Exception:
        pass
    # #endregion
    client_kwargs = {
        'aws_access_key_id': settings.aws_access_key_id,
        'aws_secret_access_key': settings.aws_secret_access_key,
        'region_name': settings.aws_region
    }
    if settings.aws_session_token:
        client_kwargs['aws_session_token'] = settings.aws_session_token
    s3_client = boto3.client('s3', **client_kwargs)
    # #region agent log
    try:
        import json as json_module
        log_data = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "S3_INIT_C",
            "location": "upload.py:s3_client_created",
            "message": "S3 client created successfully",
            "data": {
                "client_created": True,
                "region": settings.aws_region,
                "session_token_included": bool(settings.aws_session_token)
            },
            "timestamp": int(__import__("time").time() * 1000)
        }
        with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
            f.write(json_module.dumps(log_data) + "\n")
    except Exception:
        pass
    # #endregion
else:
    # #region agent log
    try:
        import json as json_module
        log_data = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "S3_INIT_D",
            "location": "upload.py:s3_client_skipped",
            "message": "S3 client not created - missing credentials",
            "data": {
                "has_access_key_id": bool(settings.aws_access_key_id),
                "has_secret_access_key": bool(settings.aws_secret_access_key)
            },
            "timestamp": int(__import__("time").time() * 1000)
        }
        with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
            f.write(json_module.dumps(log_data) + "\n")
    except Exception:
        pass
    # #endregion


def validate_video_file(filename: str) -> bool:
    """Validate video file format."""
    allowed_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
    return Path(filename).suffix.lower() in allowed_extensions


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    enable_transcription: bool = Form(True),
    enable_slide_detection: bool = Form(True),
    enable_summarization: bool = Form(True),
    enable_slide_summaries: bool = Form(False),
    return_transcript: bool = Form(True),
    return_slides: bool = Form(True),
    deduplication_method: str = Form("both")
):
    """
    Upload a video file for processing.
    
    Accepts multipart file uploads, validates format, stores in S3 or local storage,
    and returns a job ID for status tracking.
    
    Processing options:
    - enable_transcription: Enable audio transcription (default: True)
    - enable_slide_detection: Enable slide detection and extraction (default: True)
    - enable_summarization: Enable meeting summary generation (default: True)
    - enable_slide_summaries: Generate individual summaries for each slide based on its text and discussion (default: False)
    - return_transcript: Include transcript in results (default: True)
    - return_slides: Include slides in results (default: True)
    - deduplication_method: "both", "text_only", or "visual_only" (default: "both")
    """
    # #region agent log
    try:
        import json as json_module
        log_data = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "UPLOAD_ENTRY",
            "location": "upload.py:upload_video",
            "message": "Upload endpoint called",
            "data": {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": file.size if hasattr(file, 'size') else None,
                "enable_transcription": enable_transcription,
                "enable_slide_detection": enable_slide_detection,
                "enable_summarization": enable_summarization,
                "enable_slide_summaries": enable_slide_summaries
            },
            "timestamp": int(__import__("time").time() * 1000)
        }
        with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
            f.write(json_module.dumps(log_data) + "\n")
    except Exception:
        pass
    # #endregion
    
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
    
    # Save file locally (video is not uploaded to S3 to save storage and costs)
    # Only the extracted audio file will be uploaded to S3 for transcription
    local_file_path = upload_dir / f"{job_id}_{file.filename}"
    
    try:
        # Save file locally
        with open(local_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Skip video upload to S3 - we'll only upload audio for transcription
        # This saves storage space, upload time, and S3 costs
        # Scene detection will use local video file (has fallback if S3 not available)
        s3_key = None
        print(f"Video saved locally at {local_file_path}. Video will not be uploaded to S3 to save costs.")
        print("Only the extracted audio file (.wav) will be uploaded to S3 for transcription.")
        
        # #region agent log
        try:
            import json as json_module
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "UPLOAD_A",
                "location": "upload.py:create_options",
                "message": "Received processing options from frontend",
                "data": {
                    "enable_transcription": enable_transcription,
                    "enable_transcription_type": str(type(enable_transcription).__name__),
                    "enable_slide_detection": enable_slide_detection,
                    "enable_slide_detection_type": str(type(enable_slide_detection).__name__),
                    "enable_summarization": enable_summarization,
                    "enable_summarization_type": str(type(enable_summarization).__name__),
                    "enable_slide_summaries": enable_slide_summaries,
                    "enable_slide_summaries_type": str(type(enable_slide_summaries).__name__),
                    "return_transcript": return_transcript,
                    "return_transcript_type": str(type(return_transcript).__name__),
                    "return_slides": return_slides,
                    "return_slides_type": str(type(return_slides).__name__),
                    "deduplication_method": deduplication_method
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except Exception:
            pass
        # #endregion
        
        # Create processing options
        processing_options = ProcessingOptions(
            enable_transcription=enable_transcription,
            enable_slide_detection=enable_slide_detection,
            enable_summarization=enable_summarization,
            enable_slide_summaries=enable_slide_summaries,
            return_transcript=return_transcript,
            return_slides=return_slides,
            deduplication_method=deduplication_method
        )
        
        # #region agent log
        try:
            import json as json_module
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "UPLOAD_B",
                "location": "upload.py:options_created",
                "message": "ProcessingOptions object created",
                "data": {
                    "enable_slide_summaries": processing_options.enable_slide_summaries,
                    "enable_slide_summaries_type": str(type(processing_options.enable_slide_summaries).__name__)
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except Exception:
            pass
        # #endregion
        
        # Store job metadata
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        try:
            processing_options_dict = processing_options.model_dump()
        except AttributeError:
            processing_options_dict = processing_options.dict()
        
        jobs_db[job_id] = {
            "job_id": job_id,
            "filename": file.filename,
            "local_path": str(local_file_path),
            "s3_key": s3_key,
            "status": ProcessingStatus.QUEUED,
            "processing_options": processing_options_dict,
            "created_at": None,
            "updated_at": None
        }
        
        # Start processing in background (for now, synchronous)
        # In production, this would be async with Celery/Redis
        from datetime import datetime
        jobs_db[job_id]["created_at"] = datetime.now()
        jobs_db[job_id]["updated_at"] = datetime.now()
        
        # Start processing (import here to avoid circular dependency)
        # #region agent log
        try:
            import json as json_module
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "UPLOAD_C",
                "location": "upload.py:before_processor_call",
                "message": "About to call process_video_async",
                "data": {
                    "job_id": job_id,
                    "video_path": str(local_file_path),
                    "has_processing_options": processing_options is not None,
                    "processing_options_type": str(type(processing_options).__name__) if processing_options else None
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except Exception:
            pass
        # #endregion
        from app.services.video_processor import VideoProcessor
        processor = VideoProcessor()
        # #region agent log
        try:
            import json as json_module
            import inspect
            sig = inspect.signature(processor.process_video_async)
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "UPLOAD_D",
                "location": "upload.py:processor_created",
                "message": "VideoProcessor created, checking method signature",
                "data": {
                    "method_name": "process_video_async",
                    "signature": str(sig),
                    "parameters": list(sig.parameters.keys()),
                    "num_parameters": len(sig.parameters),
                    "will_call_with_args": 3,
                    "mismatch": len(sig.parameters) != 3
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except Exception as e:
            try:
                import json as json_module
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "UPLOAD_D_ERROR",
                    "location": "upload.py:processor_created_error",
                    "message": "Error checking processor signature",
                    "data": {
                        "error_type": str(type(e).__name__),
                        "error_message": str(e)
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json_module.dumps(log_data) + "\n")
            except Exception:
                pass
        # #endregion
        # #region agent log
        try:
            import json as json_module
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "UPLOAD_E",
                "location": "upload.py:before_async_call",
                "message": "Immediately before process_video_async call",
                "data": {
                    "arg1_job_id": job_id,
                    "arg2_video_path": str(local_file_path),
                    "arg3_processing_options": str(processing_options) if processing_options else None,
                    "num_args": 3
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except Exception:
            pass
        # #endregion
        processor.process_video_async(job_id, str(local_file_path), processing_options)
        # #region agent log
        try:
            import json as json_module
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "UPLOAD_F",
                "location": "upload.py:after_async_call",
                "message": "Successfully called process_video_async",
                "data": {
                    "call_succeeded": True
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except Exception:
            pass
        # #endregion
        
        return VideoUploadResponse(
            job_id=job_id,
            status=ProcessingStatus.QUEUED,
            message="Video uploaded successfully. Processing started."
        )
    
    except Exception as e:
        # #region agent log
        try:
            import json as json_module
            import traceback
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "UPLOAD_ERROR",
                "location": "upload.py:exception_handler",
                "message": "Upload endpoint exception caught",
                "data": {
                    "error_type": str(type(e).__name__),
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                    "filename": file.filename if file else None,
                    "local_file_path": str(local_file_path) if 'local_file_path' in locals() else None
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except Exception:
            pass
        # #endregion
        
        # Clean up on error
        if 'local_file_path' in locals() and local_file_path.exists():
            local_file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}"
        )


@router.post("/resume/{job_id}", response_model=VideoUploadResponse)
async def resume_processing(job_id: str):
    """
    Resume processing for a job that was interrupted.
    
    This endpoint checks for existing checkpoints and resumes processing
    from the last completed step. If no checkpoints exist, it will start
    processing from the beginning.
    """
    # Check if job exists
    if job_id not in jobs_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job_data = jobs_db[job_id]
    local_path = job_data.get("local_path")
    
    if not local_path or not Path(local_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video file not found for job {job_id}"
        )
    
    # Restore processing options
    try:
        processing_options = ProcessingOptions(**job_data.get("processing_options", {}))
    except Exception:
        # Fallback to defaults if options can't be restored
        processing_options = ProcessingOptions()
    
    # Update job status
    from datetime import datetime
    jobs_db[job_id]["status"] = ProcessingStatus.QUEUED
    jobs_db[job_id]["updated_at"] = datetime.now()
    jobs_db[job_id]["error"] = None  # Clear any previous errors
    
    # Start processing (will automatically resume from checkpoints)
    from app.services.video_processor import VideoProcessor
    processor = VideoProcessor()
    processor.process_video_async(job_id, local_path, processing_options)
    
    return VideoUploadResponse(
        job_id=job_id,
        status=ProcessingStatus.QUEUED,
        message="Processing resumed. Will continue from last checkpoint if available."
    )

