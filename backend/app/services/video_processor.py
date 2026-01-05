"""Main video processing orchestrator."""
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, List

from app.config import settings
from app.models.video import ProcessingStatus, ProcessingResults, ProcessingStep
from app.storage import jobs_db
from app.services.audio_extractor import AudioExtractor
from app.services.scene_detector import SceneDetector
from app.services.frame_extractor import FrameExtractor
from app.services.slide_fingerprint import SlideFingerprinter
from app.services.deduplicator import SlideDeduplicator
from app.services.transcriber import Transcriber
from app.services.summarizer import Summarizer


class VideoProcessor:
    """Orchestrates the entire video processing pipeline."""
    
    def __init__(self):
        self.audio_extractor = AudioExtractor()
        self.scene_detector = SceneDetector()
        self.frame_extractor = FrameExtractor()
        self.slide_fingerprinter = SlideFingerprinter()
        self.deduplicator = SlideDeduplicator()
        self.transcriber = None
        self.summarizer = None
        
        # Initialize optional services
        try:
            self.transcriber = Transcriber()
        except Exception as e:
            print(f"Warning: Transcriber not available: {e}")
        
        try:
            self.summarizer = Summarizer()
        except Exception as e:
            print(f"Warning: Summarizer not available: {e}")
    
    def update_job_status(
        self,
        job_id: str,
        status: ProcessingStatus,
        progress: Optional[float] = None,
        current_step: Optional[str] = None,
        steps: Optional[List[ProcessingStep]] = None,
        error: Optional[str] = None
    ):
        """Update job status in the database."""
        if job_id in jobs_db:
            jobs_db[job_id]["status"] = status
            jobs_db[job_id]["updated_at"] = datetime.now()
            if progress is not None:
                jobs_db[job_id]["progress"] = progress
            if current_step:
                jobs_db[job_id]["current_step"] = current_step
            if steps is not None:
                jobs_db[job_id]["steps"] = [step.dict() for step in steps]
            if error:
                jobs_db[job_id]["error"] = error
    
    def process_video_async(self, job_id: str, video_path: str):
        """Start video processing in a background thread."""
        thread = threading.Thread(
            target=self.process_video,
            args=(job_id, video_path),
            daemon=True
        )
        thread.start()
    
    def process_video(self, job_id: str, video_path: str):
        """
        Process video through the entire pipeline.
        
        Steps:
        1. Extract audio track
        2. Detect scene changes
        3. Extract frames at scene boundaries + periodic sampling
        4. Fingerprint slides (CLIP + OCR)
        5. Deduplicate slides
        6. Transcribe audio
        7. Generate summary
        8. Align slides with transcript timestamps
        9. Save results
        """
        # Define all processing steps
        all_steps = [
            ProcessingStep(name="Initializing", progress=0.0, status="in_progress"),
            ProcessingStep(name="Extracting audio", progress=0.0, status="pending"),
            ProcessingStep(name="Detecting scene changes", progress=0.0, status="pending"),
            ProcessingStep(name="Extracting frames", progress=0.0, status="pending"),
            ProcessingStep(name="Fingerprinting slides", progress=0.0, status="pending"),
            ProcessingStep(name="Deduplicating slides", progress=0.0, status="pending"),
            ProcessingStep(name="Transcribing audio", progress=0.0, status="pending"),
            ProcessingStep(name="Generating summary", progress=0.0, status="pending"),
            ProcessingStep(name="Saving results", progress=0.0, status="pending"),
        ]
        
        def update_step_progress(step_name: str, progress: float, details: Optional[str] = None):
            """Helper to update a specific step's progress."""
            for step in all_steps:
                if step.name == step_name:
                    step.progress = progress
                    if progress > 0:
                        step.status = "in_progress"
                    if progress >= 100:
                        step.status = "complete"
                    if details:
                        step.details = details
                    break
            
            # Calculate overall progress
            total_progress = sum(step.progress for step in all_steps) / len(all_steps)
            current_active = next((s for s in all_steps if s.status == "in_progress"), None)
            current_step_name = current_active.name if current_active else None
            
            self.update_job_status(
                job_id,
                ProcessingStatus.PROCESSING,
                progress=total_progress,
                current_step=current_step_name,
                steps=all_steps
            )
        
        try:
            update_step_progress("Initializing", 100.0)
            
            video_path = Path(video_path)
            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Create temp directories
            temp_dir = Path(settings.temp_dir) / job_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            frames_dir = temp_dir / "frames"
            frames_dir.mkdir(exist_ok=True)
            
            results_dir = Path(settings.results_dir)
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Extract audio (if available)
            update_step_progress("Extracting audio", 0.0)
            audio_path = self.audio_extractor.extract_audio(
                str(video_path),
                str(temp_dir / "audio.wav")
            )
            update_step_progress("Extracting audio", 100.0, "Audio extracted" if audio_path else "No audio stream found")
            if audio_path is None:
                print("Warning: Video has no audio stream. Skipping transcription.")
            
            # Step 2: Detect scene changes
            update_step_progress("Detecting scene changes", 0.0)
            s3_bucket = settings.s3_bucket_name
            s3_key = jobs_db.get(job_id, {}).get("s3_key")
            scene_boundaries = self.scene_detector.detect_scenes(
                str(video_path),
                s3_bucket=s3_bucket,
                s3_key=s3_key
            )
            update_step_progress("Detecting scene changes", 100.0, f"Found {len(scene_boundaries)} scene boundaries")
            
            # Step 3: Extract frames
            update_step_progress("Extracting frames", 0.0)
            # Add progress callback for frame extraction
            import subprocess
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
                duration = 900.0  # Default estimate
            
            total_frames_estimate = len(scene_boundaries) + int((duration - 1.0) / settings.frame_extraction_interval)
            
            def frame_progress_callback(current: int, total: int):
                progress = min(100.0, (current / max(total, 1)) * 100)
                update_step_progress("Extracting frames", progress, f"Extracted {current}/{total} frames")
            
            frames = self.frame_extractor.extract_frames(
                str(video_path),
                scene_boundaries=scene_boundaries,
                output_dir=str(frames_dir),
                progress_callback=frame_progress_callback
            )
            update_step_progress("Extracting frames", 100.0, f"Extracted {len(frames)} frames")
            
            # Step 4: Fingerprint slides
            update_step_progress("Fingerprinting slides", 0.0)
            fingerprints_progress = [0]
            
            def fingerprint_progress_callback(current: int, total: int):
                fingerprints_progress[0] = current
                progress = min(100.0, (current / max(total, 1)) * 100)
                update_step_progress("Fingerprinting slides", progress, f"Processing frame {current}/{total}")
            
            fingerprints = self.slide_fingerprinter.fingerprint_frames(
                frames,
                progress_callback=fingerprint_progress_callback if hasattr(self.slide_fingerprinter, 'fingerprint_frames') else None
            )
            update_step_progress("Fingerprinting slides", 100.0, f"Fingerprinted {len(fingerprints)} frames")
            
            # Step 5: Deduplicate slides
            update_step_progress("Deduplicating slides", 0.0)
            unique_slides = self.deduplicator.deduplicate_slides(fingerprints)
            update_step_progress("Deduplicating slides", 100.0, f"Found {len(unique_slides)} unique slides")
            
            # Step 6: Transcribe audio (if available)
            transcript = []
            if audio_path and self.transcriber:
                update_step_progress("Transcribing audio", 0.0, "Sending audio to Deepgram...")
                transcript = self.transcriber.transcribe_audio(str(audio_path))
                update_step_progress("Transcribing audio", 100.0, f"Transcribed {len(transcript)} segments")
            elif not audio_path:
                update_step_progress("Transcribing audio", 100.0, "Skipped (no audio)")
                print("Warning: No audio stream in video. Skipping transcription.")
            else:
                update_step_progress("Transcribing audio", 100.0, "Skipped (transcriber unavailable)")
                print("Warning: Transcriber not available, skipping transcription")
            
            # Step 7: Generate summary
            summary = None
            if self.summarizer and transcript:
                update_step_progress("Generating summary", 0.0, "Sending to Claude...")
                summary = self.summarizer.generate_summary(transcript, unique_slides)
                update_step_progress("Generating summary", 100.0, "Summary generated")
            else:
                print("Warning: Summarizer not available or no transcript, creating placeholder summary")
                from app.models.video import MeetingSummary
                if not transcript:
                    summary = MeetingSummary(
                        executive_summary="No audio track found in video. Summary based on slides only.",
                        decisions=[],
                        action_items=[],
                        key_topics=[]
                    )
                else:
                    summary = MeetingSummary(
                        executive_summary="Summary generation unavailable. Please check configuration.",
                        decisions=[],
                        action_items=[],
                        key_topics=[]
                    )
                update_step_progress("Generating summary", 100.0, "Placeholder summary created")
            
            # Step 8: Get video duration
            import subprocess
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
                video_duration = float(result.stdout.strip())
            except Exception:
                video_duration = 0.0
            
            # Step 9: Format results and save
            update_step_progress("Saving results", 0.0)
            
            # Convert slides to response format
            slides_response = []
            for slide in unique_slides:
                appearances_formatted = [
                    {
                        "start": self._format_timestamp(app.start),
                        "end": self._format_timestamp(app.end)
                    }
                    for app in slide.appearances
                ]
                
                slides_response.append({
                    "slide_id": slide.slide_id,
                    "image_url": slide.image_url,
                    "appearances": appearances_formatted,
                    "ocr_text": slide.ocr_text,
                    "discussion_summary": slide.discussion_summary
                })
            
            # Format summary
            summary_response = {
                "executive_summary": summary.executive_summary,
                "decisions": summary.decisions,
                "action_items": summary.action_items,
                "key_topics": summary.key_topics
            }
            
            # Save results
            results_data = {
                "summary": summary_response,
                "slides": slides_response
            }
            
            results_file = results_dir / f"{job_id}_results.json"
            with open(results_file, "w") as f:
                json.dump(results_data, f, indent=2)
            
            # Mark all steps as complete
            for step in all_steps:
                if step.status != "complete":
                    step.status = "complete"
                    step.progress = 100.0
            
            # Update job status
            self.update_job_status(
                job_id,
                ProcessingStatus.COMPLETE,
                progress=100.0,
                current_step="Complete",
                steps=all_steps
            )
        
        except Exception as e:
            error_msg = str(e)
            print(f"Error processing video {job_id}: {error_msg}")
            self.update_job_status(
                job_id,
                ProcessingStatus.ERROR,
                error=error_msg
            )
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

