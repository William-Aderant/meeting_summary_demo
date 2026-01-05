"""Processing status API endpoint."""
from fastapi import APIRouter, HTTPException, status
from app.models.video import ProcessingStatusResponse, ProcessingStatus, ProcessingStep
from app.storage import jobs_db
from datetime import datetime

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status/{job_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(job_id: str):
    """
    Get the processing status of a video job.
    
    Returns current status, progress, and any errors.
    """
    if job_id not in jobs_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs_db[job_id]
    
    # Get current status from processor if available
    status_obj = job.get("status", ProcessingStatus.QUEUED)
    progress = job.get("progress", None)
    current_step = job.get("current_step", None)
    error = job.get("error", None)
    created_at = job.get("created_at", datetime.now())
    updated_at = job.get("updated_at", datetime.now())
    
    # Parse steps if available
    steps_data = job.get("steps", None)
    steps = None
    if steps_data:
        steps = [ProcessingStep(**step) if isinstance(step, dict) else step for step in steps_data]
    
    return ProcessingStatusResponse(
        job_id=job_id,
        status=status_obj,
        progress=progress,
        current_step=current_step,
        steps=steps,
        error=error,
        created_at=created_at,
        updated_at=updated_at
    )

