"""Video generation API routes."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from backend.video_service_v2.models.video import VideoGenerateRequest, VideoGenerateResponse
from backend.video_service_v2.services.video_generator import VideoGenerator
from backend.video_service_v2.services.script_service import ScriptService

router = APIRouter()


def _get_backend_root() -> Path:
    """Get backend root directory."""
    return Path(__file__).parent.parent.parent.parent


def _get_output_dir() -> Path:
    """Get output directory for videos."""
    output_dir = _get_backend_root() / "video_service_v2" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """Generate video for a concept.
    
    Args:
        request: Video generation request
        
    Returns:
        Video generation response
    """
    try:
        output_dir = _get_output_dir()
        generator = VideoGenerator()
        video_path, audio_path, script, duration = generator.generate(
            request.topic,
            request.subtopic,
            request.concept,
            str(output_dir)
        )
        
        return VideoGenerateResponse(
            video_path=video_path,
            audio_path=audio_path,
            script=script,
            duration_seconds=duration,
            topic=request.topic,
            subtopic=request.subtopic,
            concept=request.concept.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")


@router.post("/generate-random", response_model=VideoGenerateResponse)
async def generate_random_video():
    """Generate video for a randomly selected concept.
    
    Returns:
        Video generation response
    """
    try:
        script_service = ScriptService()
        topic, subtopic, concept = script_service.select_random()
        
        output_dir = _get_output_dir()
        generator = VideoGenerator()
        video_path, audio_path, script, duration = generator.generate(
            topic,
            subtopic,
            concept,
            str(output_dir),
            force_regenerate=True
        )
        
        return VideoGenerateResponse(
            video_path=video_path,
            audio_path=audio_path,
            script=script,
            duration_seconds=duration,
            topic=topic,
            subtopic=subtopic,
            concept=concept.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")


@router.get("/cached", response_model=List[VideoGenerateResponse])
async def list_cached_videos():
    """List all cached videos.
    
    Returns:
        List of cached video responses
    """
    try:
        cache_dir = _get_backend_root() / "video_service_v2" / "cache"
        generator = VideoGenerator()
        cached_videos = generator.list_cached_videos(cache_dir)
        
        # Convert to VideoGenerateResponse format
        responses = []
        for video in cached_videos:
            # Handle old cached videos that might not have topic/subtopic/concept
            topic = video.get('topic', 'Unknown Topic')
            subtopic = video.get('subtopic', 'Unknown Subtopic')
            concept = video.get('concept', 'Unknown Concept')
            cache_key = video.get('cache_key', '')
            
            responses.append(VideoGenerateResponse(
                video_path=video['video_path'],
                audio_path="",  # Not stored separately
                script=video.get('script', ''),
                duration_seconds=video.get('duration_seconds', 0.0),
                topic=topic,
                subtopic=subtopic,
                concept=concept,
                cache_key=cache_key
            ))
        
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cached videos: {str(e)}")


@router.get("/file/{filename}")
async def serve_video_file(filename: str):
    """Serve video or audio files with full streaming support.
    
    Args:
        filename: Name of the file to serve (e.g., final_video.mp4, combined_audio.mp3)
        
    Returns:
        File response that streams the entire file
    """
    try:
        backend_root = _get_backend_root()
        file_path = backend_root / "video_service_v2" / "output" / filename
        
        if not file_path.exists():
            file_path = backend_root / "video_service_v2" / "cache" / filename
        
        # Security: prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Handle empty files
        if file_size == 0:
            raise HTTPException(status_code=404, detail=f"File is empty: {filename}")
        
        # Determine media type
        media_type = "video/mp4" if filename.endswith(".mp4") else "audio/mpeg"
        
        # Use FileResponse which automatically handles range requests
        # When no Range header is present, it streams the full file (200 OK)
        # When Range header is present, it handles partial content (206) for seeking
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
            headers={"Accept-Ranges": "bytes"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")

