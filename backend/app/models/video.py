"""Video processing data models."""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Processing job status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


class ProcessingOptions(BaseModel):
    """Processing options for video analysis."""
    enable_transcription: bool = True
    enable_slide_detection: bool = True
    enable_summarization: bool = True
    enable_slide_summaries: bool = False  # Generate individual summaries for each slide
    return_transcript: bool = True
    return_slides: bool = True
    deduplication_method: str = "both"  # "both", "text_only", "visual_only"
    
    class Config:
        json_schema_extra = {
            "example": {
                "enable_transcription": True,
                "enable_slide_detection": True,
                "enable_summarization": True,
                "enable_slide_summaries": False,
                "return_transcript": True,
                "return_slides": True,
                "deduplication_method": "both"
            }
        }


class VideoUploadRequest(BaseModel):
    """Video upload request model."""
    filename: str
    content_type: str
    processing_options: Optional[ProcessingOptions] = None


class VideoUploadResponse(BaseModel):
    """Video upload response model."""
    job_id: str
    status: ProcessingStatus
    message: str


class ProcessingStep(BaseModel):
    """Individual processing step with progress."""
    name: str
    progress: float  # 0-100
    status: str  # "pending", "in_progress", "complete", "error"
    details: Optional[str] = None


class ProcessingStatusResponse(BaseModel):
    """Processing status response model."""
    job_id: str
    status: ProcessingStatus
    progress: Optional[float] = None
    current_step: Optional[str] = None
    steps: Optional[List[ProcessingStep]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SceneBoundary(BaseModel):
    """Scene boundary detection result."""
    start_time: float  # seconds
    end_time: float  # seconds
    type: str  # "SHOT" or "CONTENT_CHANGE"


class FrameData(BaseModel):
    """Frame extraction data."""
    frame_path: str
    timestamp: float  # seconds
    frame_number: int


class SlideFingerprint(BaseModel):
    """Slide fingerprint data."""
    embedding: List[float]  # CLIP embedding vector
    text_hash: str  # Normalized OCR text hash
    ocr_text: str  # Full OCR text
    timestamp: float  # seconds
    frame_path: str


class SlideAppearance(BaseModel):
    """Slide appearance timestamp."""
    start: float  # seconds
    end: float  # seconds


class UniqueSlide(BaseModel):
    """Deduplicated unique slide."""
    slide_id: str
    image_url: str
    appearances: List[SlideAppearance]
    ocr_text: str
    discussion_summary: Optional[str] = None


class TranscriptWord(BaseModel):
    """Word-level transcript data."""
    word: str
    start: float  # seconds
    end: float  # seconds
    speaker: Optional[int] = None


class TranscriptSegment(BaseModel):
    """Transcript segment."""
    text: str
    start: float  # seconds
    end: float  # seconds
    words: List[TranscriptWord]
    speaker: Optional[int] = None


class MeetingSummary(BaseModel):
    """Meeting summary data."""
    executive_summary: str
    decisions: List[str]
    action_items: List[str]
    key_topics: List[str]


class ProcessingResults(BaseModel):
    """Final processing results."""
    job_id: str
    summary: Optional[MeetingSummary] = None
    slides: List[UniqueSlide] = []
    transcript: List[TranscriptSegment] = []
    video_duration: float  # seconds
    processed_at: datetime



