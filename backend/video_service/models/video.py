"""Video content data models."""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class VideoMetadata(BaseModel):
    """Metadata for a generated video."""
    topic: str
    subtopic: str
    concept: str
    duration_seconds: float
    created_at: datetime
    script: str
    audio_path: Optional[str] = None
    video_path: Optional[str] = None


class VideoContent(BaseModel):
    """Complete video content package."""
    metadata: VideoMetadata
    script: str
    relevance_score: float = 1.0  # How relevant to user's weak areas
    
    def __lt__(self, other):
        """Compare videos by relevance score for sorting."""
        return self.relevance_score > other.relevance_score  # Higher score = higher priority

