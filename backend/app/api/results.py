"""Results retrieval API endpoint."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.models.results import ResultsResponse
from app.models.video import ProcessingStatus
from app.storage import jobs_db
from app.config import settings

router = APIRouter(prefix="/api", tags=["results"])


@router.get("/results/{job_id}", response_model=ResultsResponse)
async def get_results(job_id: str):
    """
    Get the final processing results for a completed job.
    
    Returns meeting summary and deduplicated slides.
    """
    if job_id not in jobs_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs_db[job_id]
    
    if job.get("status") != ProcessingStatus.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is not complete. Status: {job.get('status')}"
        )
    
    # Load results from file
    results_dir = Path(settings.results_dir)
    results_file = results_dir / f"{job_id}_results.json"
    
    if not results_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Results file not found for job {job_id}"
        )
    
    with open(results_file, "r") as f:
        results_data = json.load(f)
    
    return ResultsResponse(**results_data)


@router.get("/results/{job_id}/slide/{slide_id}")
async def get_slide_image(job_id: str, slide_id: str):
    """
    Get a slide image by job ID and slide ID.
    """
    if job_id not in jobs_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Load results to find slide path
    results_dir = Path(settings.results_dir)
    results_file = results_dir / f"{job_id}_results.json"
    
    if not results_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Results file not found"
        )
    
    with open(results_file, "r") as f:
        results_data = json.load(f)
    
    # Find the slide (check if slides exist in results)
    slides = results_data.get("slides", [])
    slide = next((s for s in slides if s["slide_id"] == slide_id), None)
    
    if not slide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slide {slide_id} not found"
        )
    
    # Return the image file
    image_path = Path(slide["image_url"])
    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slide image not found"
        )
    
    return FileResponse(image_path)

