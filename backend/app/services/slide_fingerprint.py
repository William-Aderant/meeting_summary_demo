"""Slide fingerprinting service using CLIP embeddings and OCR."""
import hashlib
import re
from pathlib import Path
from typing import List, Optional, Callable, Set
import numpy as np
from PIL import Image
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.config import settings
from app.models.video import SlideFingerprint, FrameData


class SlideFingerprinter:
    """Fingerprints slides using CLIP embeddings and OCR text."""
    
    def __init__(self):
        self.clip_model = None
        self.rekognition_client = None
        self.ocr_disabled = False  # Track if OCR should be disabled due to credential errors
        self.ocr_error_count = 0  # Count consecutive OCR errors
        self.max_ocr_errors = 3  # Disable OCR after this many consecutive errors
        
        # Initialize CLIP model
        self._init_clip_model()
        
        # Initialize AWS Rekognition for OCR
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
                self.ocr_disabled = True
    
    def _init_clip_model(self):
        """Initialize CLIP model for image embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            # Use CLIP model (ViT-B/32)
            self.clip_model = SentenceTransformer('clip-ViT-B-32')
            print("CLIP model loaded successfully")
            # #region agent log
            try:
                import json as json_module
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "CLIP_INIT",
                    "location": "slide_fingerprint.py:_init_clip_model",
                    "message": "CLIP model initialized successfully",
                    "data": {"success": True},
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json_module.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
        except ImportError:
            print("Warning: sentence-transformers not installed. CLIP embeddings will not work.")
            print("  Install with: pip install sentence-transformers")
            print("  Slide deduplication will use text-only method when CLIP is unavailable.")
            self.clip_model = None
            # #region agent log
            try:
                import json as json_module
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "CLIP_INIT_FAILED",
                    "location": "slide_fingerprint.py:_init_clip_model",
                    "message": "CLIP model initialization failed - ImportError",
                    "data": {
                        "error_type": "ImportError",
                        "error_message": "sentence-transformers not installed",
                        "impact": "CLIP embeddings unavailable, will use text-only deduplication"
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json_module.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
        except Exception as e:
            print(f"Warning: Failed to load CLIP model: {e}")
            self.clip_model = None
            # #region agent log
            try:
                import json as json_module
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "CLIP_INIT_FAILED",
                    "location": "slide_fingerprint.py:_init_clip_model",
                    "message": "CLIP model initialization failed",
                    "data": {
                        "error_type": str(type(e).__name__),
                        "error_message": str(e),
                        "impact": "CLIP embeddings unavailable"
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("/Users/william.holden/Documents/GitHub/meeting_summary_demo/.cursor/debug.log", "a") as f:
                    f.write(json_module.dumps(log_data) + "\n")
            except Exception:
                pass
            # #endregion
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase, remove special characters, normalize whitespace
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _text_hash(self, text: str) -> str:
        """Create hash of normalized text."""
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _perceptual_hash(self, image_path: str) -> Optional[str]:
        """
        Generate a fast perceptual hash for quick similarity checking.
        Uses average hash (aHash) algorithm - very fast but less accurate than CLIP.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Perceptual hash string or None if failed
        """
        try:
            # Load and resize image to 8x8 (64 pixels total)
            image = Image.open(image_path).convert('L').resize((8, 8), Image.Resampling.LANCZOS)
            pixels = np.array(image)
            
            # Calculate average pixel value
            avg = pixels.mean()
            
            # Create hash: 1 if pixel > average, 0 otherwise
            hash_bits = (pixels > avg).flatten()
            
            # Convert to hex string
            hash_int = int(''.join(['1' if bit else '0' for bit in hash_bits]), 2)
            return format(hash_int, '016x')
        except Exception as e:
            print(f"Perceptual hash error: {e}")
            return None
    
    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hashes."""
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 64  # Max distance
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def extract_ocr_text(self, image_path: str) -> str:
        """
        Extract text from image using AWS Rekognition OCR.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Extracted text string
        """
        # Skip OCR if disabled due to credential errors
        if self.ocr_disabled or not self.rekognition_client:
            return ""
        
        try:
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            response = self.rekognition_client.detect_text(
                Image={'Bytes': image_bytes}
            )
            
            # Reset error count on success
            self.ocr_error_count = 0
            
            # Extract all detected text
            text_detections = response.get('TextDetections', [])
            text_lines = []
            
            for detection in text_detections:
                if detection['Type'] == 'LINE':
                    text_lines.append(detection['DetectedText'])
            
            return ' '.join(text_lines)
        
        except (ClientError, BotoCoreError) as e:
            self.ocr_error_count += 1
            
            # Check if this is a credential error
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
            if 'UnrecognizedClientException' in str(e) or 'InvalidClientTokenId' in error_code:
                # Credential error - disable OCR after a few attempts
                if self.ocr_error_count >= self.max_ocr_errors and not self.ocr_disabled:
                    self.ocr_disabled = True
                    print(f"Warning: AWS credentials invalid. Disabling OCR after {self.max_ocr_errors} failed attempts. Processing will continue with CLIP embeddings only.")
                elif self.ocr_error_count == 1:
                    # Only log the first credential error to reduce noise
                    print(f"Warning: AWS Rekognition credential error detected. Will disable OCR after {self.max_ocr_errors} failed attempts.")
            else:
                # Other errors - log but don't disable
                if self.ocr_error_count <= 3:  # Only log first few errors
                    print(f"Rekognition OCR error: {e}")
            
            return ""
        except Exception as e:
            self.ocr_error_count += 1
            if self.ocr_error_count <= 3:  # Only log first few errors
                print(f"OCR extraction error: {e}")
            return ""
    
    def get_clip_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """
        Get CLIP embedding for an image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            CLIP embedding vector (512-dim) or None if model not available
        """
        if not self.clip_model:
            return None
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Get embedding
            embedding = self.clip_model.encode(image, convert_to_numpy=True)
            
            return embedding
        except Exception as e:
            print(f"CLIP embedding error: {e}")
            return None
    
    def fingerprint_frame(self, frame_data: FrameData) -> SlideFingerprint:
        """
        Create fingerprint for a single frame.
        
        Args:
            frame_data: FrameData object with frame path and timestamp
        
        Returns:
            SlideFingerprint object
        """
        frame_path = Path(frame_data.frame_path)
        if not frame_path.exists():
            raise FileNotFoundError(f"Frame not found: {frame_path}")
        
        # Extract OCR text
        ocr_text = self.extract_ocr_text(str(frame_path))
        text_hash = self._text_hash(ocr_text) if ocr_text else ""
        
        # Get CLIP embedding
        embedding = self.get_clip_embedding(str(frame_path))
        embedding_list = embedding.tolist() if embedding is not None else []
        
        return SlideFingerprint(
            embedding=embedding_list,
            text_hash=text_hash,
            ocr_text=ocr_text,
            timestamp=frame_data.timestamp,
            frame_path=str(frame_path)
        )
    
    def fingerprint_frames(
        self, 
        frames: List[FrameData],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[SlideFingerprint]:
        """
        Create fingerprints for multiple frames with fast pre-filtering.
        
        Uses fast perceptual hash to skip frames that are very similar to recently
        processed frames, avoiding expensive CLIP/OCR operations.
        
        Args:
            frames: List of FrameData objects
            progress_callback: Optional callback function(current, total) for progress updates
        
        Returns:
            List of SlideFingerprint objects
        """
        fingerprints = []
        total = len(frames)
        skipped_count = 0
        
        # Fast pre-filtering: track recent perceptual hashes
        recent_hashes: List[tuple[str, float]] = []  # (hash, timestamp)
        max_recent_hashes = 10  # Keep last 10 hashes for comparison
        hash_similarity_threshold = 4  # Hamming distance threshold (0-64, lower = more strict)
        
        for i, frame in enumerate(frames):
            try:
                # Fast pre-filter: skip if very similar to recent frame
                if settings.use_fast_prefilter:
                    frame_hash = self._perceptual_hash(frame.frame_path)
                    
                    if frame_hash:
                        # Check against recent hashes
                        should_skip = False
                        for recent_hash, recent_time in recent_hashes:
                            distance = self._hamming_distance(frame_hash, recent_hash)
                            # Skip if very similar (low Hamming distance) and within 5 seconds
                            if distance <= hash_similarity_threshold and abs(frame.timestamp - recent_time) < 5.0:
                                should_skip = True
                                skipped_count += 1
                                break
                        
                        if should_skip:
                            if progress_callback:
                                progress_callback(i + 1, total)
                            continue
                        
                        # Add to recent hashes
                        recent_hashes.append((frame_hash, frame.timestamp))
                        if len(recent_hashes) > max_recent_hashes:
                            recent_hashes.pop(0)  # Remove oldest
                
                # Full fingerprinting (CLIP + OCR) - expensive operation
                fingerprint = self.fingerprint_frame(frame)
                fingerprints.append(fingerprint)
                
                if progress_callback:
                    progress_callback(i + 1, total)
            except Exception as e:
                print(f"Error fingerprinting frame {frame.frame_path}: {e}")
                if progress_callback:
                    progress_callback(i + 1, total)
                continue
        
        if skipped_count > 0:
            print(f"Fast pre-filter skipped {skipped_count} similar frames (saved ~{skipped_count * 2:.1f}s)")
        
        return fingerprints

