"""Video generation request/response models."""
from pydantic import BaseModel
from backend.course_service.models.course import Concept


class VideoGenerateRequest(BaseModel):
    """Request to generate a video."""
    concept: Concept
    topic: str
    subtopic: str


class VideoGenerateResponse(BaseModel):
    """Response from video generation."""
    video_path: str
    audio_path: str
    script: str
    duration_seconds: float
    topic: str
    subtopic: str
    concept: str
    cache_key: str | None = None  # Optional cache key for cached videos

