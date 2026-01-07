"""Results retrieval API endpoint."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, Response
from app.models.results import ResultsResponse
from app.models.video import ProcessingStatus
from app.storage import jobs_db
from app.config import settings

router = APIRouter(prefix="/api", tags=["results"])


def _format_timestamp(seconds: float) -> str:
    """Format seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _load_results_data(job_id: str) -> dict:
    """Load results data from file."""
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
    
    results_dir = Path(settings.results_dir)
    results_file = results_dir / f"{job_id}_results.json"
    
    if not results_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Results file not found for job {job_id}"
        )
    
    with open(results_file, "r") as f:
        return json.load(f)


def _format_results_as_txt(results_data: dict) -> str:
    """Format results as plain text."""
    lines = []
    lines.append("=" * 80)
    lines.append("MEETING SUMMARY")
    lines.append("=" * 80)
    lines.append("")
    
    summary = results_data.get("summary", {})
    if summary:
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(summary.get("executive_summary", ""))
        lines.append("")
        
        decisions = summary.get("decisions", [])
        if decisions:
            lines.append("DECISIONS")
            lines.append("-" * 80)
            for i, decision in enumerate(decisions, 1):
                lines.append(f"{i}. {decision}")
            lines.append("")
        
        action_items = summary.get("action_items", [])
        if action_items:
            lines.append("ACTION ITEMS")
            lines.append("-" * 80)
            for i, item in enumerate(action_items, 1):
                lines.append(f"{i}. {item}")
            lines.append("")
        
        key_topics = summary.get("key_topics", [])
        if key_topics:
            lines.append("KEY TOPICS")
            lines.append("-" * 80)
            for i, topic in enumerate(key_topics, 1):
                lines.append(f"{i}. {topic}")
            lines.append("")
    
    slides = results_data.get("slides", [])
    if slides:
        lines.append("=" * 80)
        lines.append("SLIDES")
        lines.append("=" * 80)
        lines.append("")
        
        for slide in slides:
            lines.append(f"Slide {slide.get('slide_id', 'Unknown')}")
            lines.append("-" * 80)
            
            appearances = slide.get("appearances", [])
            if appearances:
                app_str = ", ".join([
                    f"{app.get('start', '')} - {app.get('end', '')}"
                    for app in appearances
                ])
                lines.append(f"Appearances: {app_str}")
            
            ocr_text = slide.get("ocr_text", "")
            if ocr_text:
                lines.append(f"Content: {ocr_text[:200]}{'...' if len(ocr_text) > 200 else ''}")
            
            discussion_summary = slide.get("discussion_summary")
            if discussion_summary:
                lines.append(f"Discussion Summary: {discussion_summary}")
            
            lines.append("")
    
    transcript = results_data.get("transcript", [])
    if transcript:
        lines.append("=" * 80)
        lines.append("FULL TRANSCRIPT")
        lines.append("=" * 80)
        lines.append("")
        
        for segment in transcript:
            timestamp = _format_timestamp(segment.get("start", 0))
            speaker = segment.get("speaker")
            speaker_str = f"Speaker {speaker}: " if speaker is not None else ""
            text = segment.get("text", "")
            lines.append(f"[{timestamp}] {speaker_str}{text}")
            lines.append("")
    
    return "\n".join(lines)


@router.get("/results/{job_id}", response_model=ResultsResponse)
async def get_results(job_id: str):
    """
    Get the final processing results for a completed job.
    
    Returns meeting summary, deduplicated slides, and full transcript.
    """
    results_data = _load_results_data(job_id)
    
    # Ensure transcript field exists (for backward compatibility with old results)
    if "transcript" not in results_data:
        results_data["transcript"] = None
    
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
    results_data = _load_results_data(job_id)
    
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


@router.get("/results/{job_id}/download/txt")
async def download_results_txt(job_id: str):
    """
    Download results as a plain text file.
    """
    results_data = _load_results_data(job_id)
    txt_content = _format_results_as_txt(results_data)
    
    return Response(
        content=txt_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="meeting_summary_{job_id}.txt"'
        }
    )


@router.get("/results/{job_id}/download/pdf")
async def download_results_pdf(job_id: str):
    """
    Download results as a PDF file.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from io import BytesIO
        from PIL import Image as PILImage
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PDF generation requires reportlab and Pillow. Install with: pip install reportlab pillow"
        )
    
    results_data = _load_results_data(job_id)
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#000000',
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#333333',
        spaceAfter=8,
        spaceBefore=12
    )
    
    # Title
    story.append(Paragraph("MEETING SUMMARY", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Summary section
    summary = results_data.get("summary", {})
    if summary:
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        story.append(Paragraph(summary.get("executive_summary", "").replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        decisions = summary.get("decisions", [])
        if decisions:
            story.append(Paragraph("DECISIONS", heading_style))
            for i, decision in enumerate(decisions, 1):
                story.append(Paragraph(f"{i}. {decision}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        action_items = summary.get("action_items", [])
        if action_items:
            story.append(Paragraph("ACTION ITEMS", heading_style))
            for i, item in enumerate(action_items, 1):
                story.append(Paragraph(f"{i}. {item}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        key_topics = summary.get("key_topics", [])
        if key_topics:
            story.append(Paragraph("KEY TOPICS", heading_style))
            for i, topic in enumerate(key_topics, 1):
                story.append(Paragraph(f"{i}. {topic}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
    
    # Slides section
    slides = results_data.get("slides", [])
    if slides:
        story.append(PageBreak())
        story.append(Paragraph("SLIDES", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        for slide in slides:
            slide_id = slide.get('slide_id', 'Unknown')
            story.append(Paragraph(f"Slide {slide_id}", heading_style))
            
            appearances = slide.get("appearances", [])
            if appearances:
                app_str = ", ".join([
                    f"{app.get('start', '')} - {app.get('end', '')}"
                    for app in appearances
                ])
                story.append(Paragraph(f"<b>Appearances:</b> {app_str}", styles['Normal']))
            
            # Add slide image
            image_url = slide.get("image_url", "")
            if image_url:
                # Use the same path resolution as get_slide_image endpoint
                image_path = Path(image_url)
                
                # If path doesn't exist as-is, try relative to backend root
                if not image_path.exists():
                    backend_root = Path(__file__).parent.parent.parent
                    image_path = backend_root / image_url
                
                if image_path.exists():
                    try:
                        # Get image dimensions to scale appropriately
                        with PILImage.open(image_path) as img:
                            img_width, img_height = img.size
                        
                        # Calculate dimensions to fit page width (with margins)
                        page_width = letter[0] - 2 * inch  # Account for margins
                        max_height = 5 * inch  # Maximum height for images
                        
                        # Calculate scaling to fit width
                        scale_ratio = min(page_width / img_width, max_height / img_height)
                        scaled_width = img_width * scale_ratio
                        scaled_height = img_height * scale_ratio
                        
                        # Add image to PDF
                        pdf_image = Image(str(image_path), width=scaled_width, height=scaled_height)
                        story.append(Spacer(1, 0.1 * inch))
                        story.append(pdf_image)
                        story.append(Spacer(1, 0.1 * inch))
                    except Exception as e:
                        # If image can't be loaded, just skip it
                        story.append(Paragraph(f"<i>Image unavailable: {str(e)}</i>", styles['Normal']))
                        story.append(Spacer(1, 0.1 * inch))
                else:
                    story.append(Paragraph("<i>Image file not found</i>", styles['Normal']))
                    story.append(Spacer(1, 0.1 * inch))
            
            ocr_text = slide.get("ocr_text", "")
            if ocr_text:
                truncated = ocr_text[:300] + "..." if len(ocr_text) > 300 else ocr_text
                story.append(Paragraph(f"<b>Content:</b> {truncated.replace('<', '&lt;').replace('>', '&gt;')}", styles['Normal']))
            
            discussion_summary = slide.get("discussion_summary")
            if discussion_summary:
                story.append(Paragraph(f"<b>Discussion Summary:</b> {discussion_summary.replace('<', '&lt;').replace('>', '&gt;')}", styles['Normal']))
            
            story.append(Spacer(1, 0.3 * inch))
    
    # Transcript section
    transcript = results_data.get("transcript", [])
    if transcript:
        story.append(PageBreak())
        story.append(Paragraph("FULL TRANSCRIPT", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        for segment in transcript:
            timestamp = _format_timestamp(segment.get("start", 0))
            speaker = segment.get("speaker")
            speaker_str = f"Speaker {speaker}: " if speaker is not None else ""
            text = segment.get("text", "").replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"<b>[{timestamp}]</b> {speaker_str}{text}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="meeting_summary_{job_id}.pdf"'
        }
    )

