"""Results response models."""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class SlideAppearance(BaseModel):
    """Slide appearance timestamp."""
    start: str  # Format: "HH:MM:SS"
    end: str  # Format: "HH:MM:SS"


class UniqueSlideResponse(BaseModel):
    """Unique slide response model."""
    slide_id: str
    image_url: str
    appearances: list[SlideAppearance]
    ocr_text: str
    discussion_summary: Optional[str] = None


class MeetingSummaryResponse(BaseModel):
    """Meeting summary response model."""
    executive_summary: str
    decisions: list[str]
    action_items: list[str]
    key_topics: Optional[list[str]] = None


class TranscriptWordResponse(BaseModel):
    """Word-level transcript response."""
    word: str
    start: float
    end: float
    speaker: Optional[int] = None


class TranscriptSegmentResponse(BaseModel):
    """Transcript segment response."""
    text: str
    start: float
    end: float
    speaker: Optional[int] = None
    words: List[TranscriptWordResponse] = []


class ResultsResponse(BaseModel):
    """Final results response model."""
    summary: Optional[MeetingSummaryResponse] = None
    slides: Optional[list[UniqueSlideResponse]] = None
    transcript: Optional[List[TranscriptSegmentResponse]] = None



