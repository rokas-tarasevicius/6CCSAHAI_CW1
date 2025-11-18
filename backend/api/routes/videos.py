"""Video generation API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.video.content_recommender import ContentRecommender
from src.services.video.script_generator import ScriptGenerator
from src.services.video.tts_service import TTSService
from src.services.video.video_assembler import VideoAssembler
from src.services.llm.mistral_client import MistralClient
from src.utils.course_loader import CourseLoader
from src.models.user_state import UserPerformance

router = APIRouter()


class VideoRecommendation(BaseModel):
    """Video recommendation model."""
    topic: str
    subtopic: str
    concept: str
    relevance_score: float


class VideoContentResponse(BaseModel):
    """Video content response."""
    topic: str
    subtopic: str
    concept: str
    script: str
    duration_seconds: float
    relevance_score: float


@router.post("/recommendations")
async def get_video_recommendations(
    performance_data: dict,
    max_videos: int = 5
):
    """Get personalized video recommendations."""
    try:
        # Resolve path relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        course_path = project_root / "data" / "course_material.json"
        course = CourseLoader.load_from_file(str(course_path))
        performance = UserPerformance(**performance_data)
        
        script_gen = ScriptGenerator(MistralClient())
        tts_service = TTSService()
        video_assembler = VideoAssembler()
        
        recommender = ContentRecommender(
            course,
            script_gen,
            tts_service,
            video_assembler
        )
        
        recommendations = recommender.recommend_videos(performance, max_videos)
        
        return {
            "recommendations": [
                {
                    "topic": topic,
                    "subtopic": subtopic,
                    "concept": concept,
                    "relevance_score": score
                }
                for topic, subtopic, concept, score in recommendations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.post("/generate")
async def generate_video_content(
    topic: str,
    subtopic: str,
    concept: str,
    relevance_score: float = 1.0
):
    """Generate video content for a concept."""
    try:
        # Resolve path relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        course_path = project_root / "data" / "course_material.json"
        course = CourseLoader.load_from_file(str(course_path))
        script_gen = ScriptGenerator(MistralClient())
        tts_service = TTSService()
        video_assembler = VideoAssembler()
        
        recommender = ContentRecommender(
            course,
            script_gen,
            tts_service,
            video_assembler
        )
        
        video_content = recommender.generate_video_content(
            topic,
            subtopic,
            concept,
            relevance_score
        )
        
        return VideoContentResponse(
            topic=video_content.metadata.topic,
            subtopic=video_content.metadata.subtopic,
            concept=video_content.metadata.concept,
            script=video_content.script,
            duration_seconds=video_content.metadata.duration_seconds,
            relevance_score=video_content.relevance_score
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")


