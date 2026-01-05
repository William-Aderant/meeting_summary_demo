"""Slide deduplication service."""
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
from difflib import SequenceMatcher

from app.config import settings
from app.models.video import SlideFingerprint, UniqueSlide, SlideAppearance


class SlideDeduplicator:
    """Deduplicates slides based on CLIP similarity and OCR text matching."""
    
    def __init__(self):
        self.clip_threshold = settings.clip_similarity_threshold
        self.text_threshold = settings.ocr_text_similarity_threshold
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher."""
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def are_slides_similar(
        self,
        fingerprint1: SlideFingerprint,
        fingerprint2: SlideFingerprint
    ) -> bool:
        """
        Determine if two slides are similar (duplicates).
        
        Slides are considered duplicates if:
        - CLIP cosine similarity exceeds threshold, OR
        - OCR text similarity exceeds threshold, OR
        - Text hash matches exactly
        """
        # Exact text hash match
        if fingerprint1.text_hash and fingerprint2.text_hash:
            if fingerprint1.text_hash == fingerprint2.text_hash:
                return True
        
        # CLIP embedding similarity
        if fingerprint1.embedding and fingerprint2.embedding:
            clip_sim = self.cosine_similarity(
                fingerprint1.embedding,
                fingerprint2.embedding
            )
            if clip_sim >= self.clip_threshold:
                return True
        
        # OCR text similarity
        if fingerprint1.ocr_text and fingerprint2.ocr_text:
            text_sim = self.text_similarity(
                fingerprint1.ocr_text,
                fingerprint2.ocr_text
            )
            if text_sim >= self.text_threshold:
                return True
        
        return False
    
    def deduplicate_slides(
        self,
        fingerprints: List[SlideFingerprint]
    ) -> List[UniqueSlide]:
        """
        Deduplicate slides and group appearances.
        
        Args:
            fingerprints: List of slide fingerprints
        
        Returns:
            List of unique slides with appearance metadata
        """
        if not fingerprints:
            return []
        
        # Group similar slides
        slide_groups: Dict[int, List[int]] = defaultdict(list)
        processed = set()
        group_id = 0
        
        for i, fp1 in enumerate(fingerprints):
            if i in processed:
                continue
            
            # Start a new group
            slide_groups[group_id].append(i)
            processed.add(i)
            
            # Find similar slides
            for j, fp2 in enumerate(fingerprints[i+1:], start=i+1):
                if j in processed:
                    continue
                
                if self.are_slides_similar(fp1, fp2):
                    slide_groups[group_id].append(j)
                    processed.add(j)
            
            group_id += 1
        
        # Create unique slides
        unique_slides = []
        
        for group_id, indices in slide_groups.items():
            # Use the first occurrence as the representative slide
            representative_idx = indices[0]
            representative = fingerprints[representative_idx]
            
            # Collect all appearances
            appearances = []
            for idx in indices:
                fp = fingerprints[idx]
                # Create appearance with start and end time
                # For now, use timestamp as both start and end
                # In production, you might want to detect when slide disappears
                appearances.append(SlideAppearance(
                    start=fp.timestamp,
                    end=fp.timestamp + 5.0  # Assume 5 second duration
                ))
            
            # Sort appearances by timestamp
            appearances.sort(key=lambda x: x.start)
            
            # Merge overlapping appearances
            merged_appearances = self._merge_appearances(appearances)
            
            # Create unique slide
            slide_id = f"slide_{group_id:03d}"
            unique_slide = UniqueSlide(
                slide_id=slide_id,
                image_url=representative.frame_path,
                appearances=merged_appearances,
                ocr_text=representative.ocr_text,
                discussion_summary=None  # Will be filled later
            )
            
            unique_slides.append(unique_slide)
        
        return unique_slides
    
    def _merge_appearances(self, appearances: List[SlideAppearance]) -> List[SlideAppearance]:
        """Merge overlapping or adjacent appearances."""
        if not appearances:
            return []
        
        # Sort by start time
        sorted_apps = sorted(appearances, key=lambda x: x.start)
        merged = [sorted_apps[0]]
        
        for current in sorted_apps[1:]:
            last = merged[-1]
            
            # If current overlaps or is adjacent to last, merge them
            if current.start <= last.end + 1.0:  # 1 second gap tolerance
                merged[-1] = SlideAppearance(
                    start=last.start,
                    end=max(last.end, current.end)
                )
            else:
                merged.append(current)
        
        return merged



