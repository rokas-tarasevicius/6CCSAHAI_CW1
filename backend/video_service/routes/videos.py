"""Video generation API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent  # Project root for absolute paths

from backend.video_service.services.video.content_recommender import ContentRecommender
from backend.video_service.services.video.script_generator import ScriptGenerator
from backend.video_service.services.video.tts_service import TTSService
from backend.video_service.services.video.video_assembler import VideoAssembler
from backend.shared.services.llm.mistral_client import MistralClient
from backend.course_service.models.course import CourseStructure, Topic, Subtopic, Concept
from backend.shared.utils.config import Config

router = APIRouter()

# Global course cache
_course = None


def get_course(force_reload: bool = False):
    """Get or load course from parsed_data.json.
    
    Args:
        force_reload: If True, reload the course even if already loaded
    """
    global _course
    if _course is None or force_reload:
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            # Return empty course structure if no parsed data
            _course = CourseStructure(
                title="No Course Material",
                description="Upload PDF files to generate course material",
                topics=[]
            )
            return _course
        
        # Load parsed data
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        # Convert parsed data to CourseStructure
        topics = []
        for file_path, file_data in parsed_data.items():
            file_name = file_data["metadata"]["file_name"]
            content = file_data["content"]
            
            # Extract topic name from file name (remove .pdf extension)
            topic_name = file_name.replace('.pdf', '').replace('_', ' ').title()
            
            # Use more content for better context (up to 20000 chars)
            content_preview = content[:20000] if len(content) > 20000 else content
            
            # Create a single subtopic for the entire PDF content
            subtopic = Subtopic(
                name="Main Content",
                description=f"Content from {file_name}",
                concepts=[
                    Concept(
                        name=topic_name,
                        description=f"Key concepts from {file_name}. Content length: {len(content)} characters.",
                        keywords=[]
                    )
                ],
                content=content_preview
            )
            
            topic = Topic(
                name=topic_name,
                description=f"Material from {file_name}",
                subtopics=[subtopic]
            )
            
            topics.append(topic)
        
        _course = CourseStructure(
            title="Parsed Course Material",
            description="Course material extracted from uploaded PDF files",
            topics=topics
        )
    
    return _course


class VideoRecommendation(BaseModel):
    """Video recommendation model."""
    topic: str
    subtopic: str
    concept: str
    relevance_score: float


class VideoRecommendationsRequest(BaseModel):
    """Video recommendations request."""
    max_videos: int = 5


class VideoGenerateRequest(BaseModel):
    """Video generation request."""
    topic: str
    subtopic: str
    concept: str
    relevance_score: float = 1.0


class VideoContentResponse(BaseModel):
    """Video content response."""
    topic: str
    subtopic: str
    concept: str
    script: str
    duration_seconds: float
    relevance_score: float
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None


@router.post("/recommendations")
async def get_video_recommendations(request: VideoRecommendationsRequest):
    """Get video recommendations from course content."""
    try:
        course = get_course()
        
        script_gen = ScriptGenerator(MistralClient())
        tts_service = TTSService()
        video_assembler = VideoAssembler()
        
        recommender = ContentRecommender(
            course,
            script_gen,
            tts_service,
            video_assembler
        )
        
        recommendations = recommender.recommend_videos(request.max_videos)
        
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


@router.post("/generate", response_model=VideoContentResponse)
async def generate_video_content(request: VideoGenerateRequest):
    """Generate video content for a concept."""
    try:
        course = get_course()
        
        # Check if course has any topics
        if not course.topics:
            raise HTTPException(
                status_code=404,
                detail="No course material available. Please upload PDF files first."
            )
        
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
            request.topic,
            request.subtopic,
            request.concept,
            request.relevance_score
        )
        
        # Generate video URL if video path exists
        video_url = None
        if video_content.metadata.video_path:
            # Convert file path to URL (relative to API base)
            video_filename = Path(video_content.metadata.video_path).name
            video_url = f"/api/videos/file/{video_filename}"
        
        # Generate audio URL if audio path exists
        audio_url = None
        if video_content.metadata.audio_path:
            # Convert file path to URL (relative to API base)
            audio_filename = Path(video_content.metadata.audio_path).name
            audio_url = f"/api/videos/file/{audio_filename}"
        
        return VideoContentResponse(
            topic=video_content.metadata.topic,
            subtopic=video_content.metadata.subtopic,
            concept=video_content.metadata.concept,
            script=video_content.script,
            duration_seconds=video_content.metadata.duration_seconds,
            relevance_score=video_content.relevance_score,
            audio_path=video_content.metadata.audio_path,
            video_path=video_content.metadata.video_path,
            audio_url=audio_url,
            video_url=video_url
        )
    except HTTPException:
        raise
    except ValueError as e:
        # Concept not found or similar validation error
        raise HTTPException(status_code=404, detail=f"Concept not found: {str(e)}")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Video generation error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")



@router.get("/file/{filename}")
async def serve_video_file(filename: str):
    """Serve video or audio files.
    
    Args:
        filename: Name of the file to serve
        
    Returns:
        File response
    """
    from fastapi.responses import FileResponse
    
    # Determine file type and directory
    if filename.endswith('.mp4'):
        file_path = BACKEND_ROOT / "video_service" / "assets" / "video" / filename
    elif filename.endswith('.mp3'):
        file_path = BACKEND_ROOT / "video_service" / "assets" / "audio" / filename
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is empty (0 bytes) - common for dummy videos
    file_size = file_path.stat().st_size
    if file_size == 0:
        raise HTTPException(
            status_code=503, 
            detail="Video file is empty. Video generation may still be in progress or failed."
        )
    
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4" if filename.endswith('.mp4') else "audio/mpeg",
        filename=filename
    )


