"""FastAPI backend server for Adaptive Learning Platform."""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys
import json
import os
import tempfile
import asyncio
import random

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Calculate backend root
BACKEND_ROOT = Path(__file__).parent.parent

# Import services
from backend.course_service.services.document.parser import parse_files
from backend.course_service.services.course_service import (
    generate_quiz_for_file,
    generate_pdf_summary_for_file
)
from backend.quiz_service.services.question.generator import QuestionGenerator
from backend.shared.services.llm.mistral_client import MistralClient
from backend.video_service_v2.services.video_generator import VideoGenerator
from backend.video_service_v2.services.script_service import ScriptService

# Import models
from backend.course_service.models.course import CourseStructure, Topic, Subtopic, Concept
from backend.quiz_service.models.question import DifficultyLevel
from backend.video_service_v2.models.video import VideoGenerateRequest, VideoGenerateResponse
from llama_cloud_services import LlamaParse

app = FastAPI(
    title="Adaptive Learning Platform API",
    description="Backend API for AI-powered adaptive learning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lock for JSON file operations to prevent race conditions
_json_file_lock = asyncio.Lock()

# ============================================================================
# Request/Response Models
# ============================================================================

class ParsedFileMetadata(BaseModel):
    """Metadata for a parsed file."""
    file_name: str
    file_type: str
    content_length: int
    language: str
    extraction_timestamp: str
    timezone: str


class ParsedFileData(BaseModel):
    """Data structure for a parsed file."""
    metadata: ParsedFileMetadata
    content: str
    summary: Optional[str] = None
    quiz: Optional[List[Dict[str, Any]]] = None


class ParsedDataResponse(BaseModel):
    """Response model for parsed data."""
    files: Dict[str, ParsedFileData]


class UploadResponse(BaseModel):
    """PDF upload response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class AnswerOption(BaseModel):
    text: str
    is_correct: bool
    explanation: str = ""
    
    @field_validator('explanation', mode='before')
    @classmethod
    def validate_explanation(cls, v):
        return v if v is not None else ""


class QuestionResponse(BaseModel):
    question_text: str
    answers: List[AnswerOption]
    topic: str
    subtopic: str
    concepts: List[str]
    difficulty: str
    explanation: str
    
    @field_validator('explanation', mode='before')
    @classmethod
    def validate_explanation(cls, v):
        return v if v is not None else ""


class FileQuizRequest(BaseModel):
    file_paths: List[str]
    max_questions: Optional[int] = None


# ============================================================================
# Helper Functions
# ============================================================================

def _get_video_service_dir() -> Path:
    """Get video_service_v2 package directory."""
    return BACKEND_ROOT / "video_service_v2"


def _get_output_dir() -> Path:
    """Get output directory for videos."""
    output_dir = _get_video_service_dir() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _get_cache_dir() -> Path:
    """Get cache directory for videos."""
    cache_dir = _get_video_service_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


# ============================================================================
# Course Routes
# ============================================================================

@app.get("/api/course/", response_model=ParsedDataResponse)
async def get_course():
    """Get parsed course material from PDF files."""
    try:
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        files = {}
        for file_path, file_data in parsed_data.items():
            files[file_path] = ParsedFileData(
                metadata=ParsedFileMetadata(**file_data["metadata"]),
                content=file_data["content"],
                summary=file_data.get("summary"),
                quiz=file_data.get("quiz")
            )
        
        return ParsedDataResponse(files=files)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load parsed data: {str(e)}")


@app.post("/api/course/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and parse a PDF file."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_content = await file.read()
    if len(file_content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")

    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
    if not LLAMA_CLOUD_API_KEY:
        raise HTTPException(status_code=500, detail="LLAMA_CLOUD_API_KEY environment variable not set")

    parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
    file_key = f"data/raw/{file.filename}"
    
    async with _json_file_lock:
        if parsed_data_file.exists():
            def read_json_file():
                with open(parsed_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            existing_data = await asyncio.to_thread(read_json_file)
            
            if file_key in existing_data:
                raise HTTPException(
                    status_code=409, 
                    detail=f"This file has already been uploaded and processed. Please use a different filename or delete the existing file first."
                )
    
    original_file_name = file.filename
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name

    try:
        print(LLAMA_CLOUD_API_KEY)
        print("path", tmp_path)
        parser = LlamaParse(
            api_key=LLAMA_CLOUD_API_KEY,
            num_workers=1,
            verbose=True,
            language="en"
        )

        try:
            print(f"Started parsing")
            file_names: List[str] = [tmp_path]
            result = await asyncio.wait_for(
                parse_files(file_names, parser),
                timeout=300.0
            )
            print(f"Result: {result}")
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="PDF parsing timed out. The file may be too large or complex. Please try a smaller file."
            )

        parsed_data = result.get(tmp_path)

        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse PDF - no data returned")
        
        parsed_data["metadata"]["file_name"] = original_file_name
        file_contents = parsed_data["content"]

        print(f"Generating summary for {original_file_name}...")
        pdf_summary_prompt_data = {
            "file_name": original_file_name,
            "raw_text": file_contents,
            "topic": "",
            "subtopic": ""
        }
        
        pdf_summary = await generate_pdf_summary_for_file(
            file_name=original_file_name,
            prompt_data=pdf_summary_prompt_data,
        )
        
        parsed_data["summary"] = pdf_summary

        print(f"Generating quiz for {original_file_name}...")
        num_questions = 5
        quiz_questions = await generate_quiz_for_file(
            file_name=original_file_name,
            content=file_contents,
            summary=pdf_summary,
            num_questions=num_questions
        )
        
        parsed_data["quiz"] = quiz_questions
        print(f"Generated {len(quiz_questions)} quiz questions and summary for {original_file_name}")

        async with _json_file_lock:
            parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
            
            def read_json_file():
                if parsed_data_file.exists():
                    with open(parsed_data_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return {}
            
            def write_json_file(data):
                with open(parsed_data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
            
            existing_data = await asyncio.to_thread(read_json_file)
            file_key = f"data/raw/{file.filename}"
            existing_data[file_key] = parsed_data
            await asyncio.to_thread(write_json_file, existing_data)

        return UploadResponse(
            success=True,
            message=f"Successfully parsed {file.filename}",
            data=parsed_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/api/course/generate-quiz/{file_key:path}", response_model=UploadResponse)
async def generate_quiz_for_existing_file(file_key: str, num_questions: int = 5):
    """Generate or regenerate a quiz for an existing parsed file."""
    try:
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        if file_key not in existing_data:
            raise HTTPException(status_code=404, detail=f"File {file_key} not found in parsed data")
        
        file_data = existing_data[file_key]
        file_name = file_data["metadata"]["file_name"]
        content = file_data["content"]
        summary = file_data["summary"] 
        
        print(f"Regenerating quiz for {file_name}...")
        quiz_questions = await generate_quiz_for_file(
            file_name=file_name,
            content=content,
            summary=summary,
            num_questions=num_questions
        )
        
        existing_data[file_key]["quiz"] = quiz_questions
        
        with open(parsed_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        
        print(f"Successfully regenerated {len(quiz_questions)} quiz questions for {file_name}")
        
        return UploadResponse(
            success=True,
            message=f"Successfully generated {len(quiz_questions)} quiz questions for {file_name}",
            data={"quiz": quiz_questions}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@app.delete("/api/course/{file_key:path}", response_model=UploadResponse)
async def delete_course(file_key: str):
    """Delete a course file from parsed_data.json."""
    try:
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        if file_key not in existing_data:
            raise HTTPException(status_code=404, detail=f"File {file_key} not found in parsed data")
        
        file_name = existing_data[file_key]["metadata"]["file_name"]
        del existing_data[file_key]
        
        with open(parsed_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        
        print(f"Successfully deleted {file_name} from parsed data")
        
        return UploadResponse(
            success=True,
            message=f"Successfully deleted {file_name}",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete course: {str(e)}")


# ============================================================================
# Questions Routes
# ============================================================================

@app.post("/api/questions/start-file-quiz", response_model=List[QuestionResponse])
async def start_file_based_quiz(request: FileQuizRequest):
    """Start a quiz using questions from selected files."""
    try:
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        combined_questions = []
        
        for file_path in request.file_paths:
            if file_path not in parsed_data:
                print(f"Warning: File {file_path} not found in parsed data")
                continue
                
            file_data = parsed_data[file_path]
            quiz_questions = file_data.get("quiz", [])
            
            if not quiz_questions:
                print(f"Warning: No quiz questions found for file {file_path}")
                continue
            
            for question_data in quiz_questions:
                try:
                    answer_options = []
                    for answer in question_data.get("answers", []):
                        answer_options.append(AnswerOption(
                            text=answer.get("text", ""),
                            is_correct=answer.get("is_correct", False),
                            explanation=answer.get("explanation", "")
                        ))

                    random.shuffle(answer_options)
                    
                    question_response = QuestionResponse(
                        question_text=question_data.get("question_text", ""),
                        answers=answer_options,
                        topic=question_data.get("topic", ""),
                        subtopic=question_data.get("subtopic", ""),
                        concepts=question_data.get("concepts", []),
                        difficulty=question_data.get("difficulty", "medium"),
                        explanation=question_data.get("explanation", "")
                    )
                    
                    combined_questions.append(question_response)
                    
                except Exception as e:
                    print(f"Error processing question from {file_path}: {str(e)}")
                    continue
        
        if not combined_questions:
            raise HTTPException(status_code=404, detail="No valid quiz questions found in selected files")
        
        random.shuffle(combined_questions)
        
        if request.max_questions and request.max_questions > 0:
            original_count = len(combined_questions)
            if original_count > request.max_questions:
                combined_questions = combined_questions[:request.max_questions]
                print(f"Limited quiz to {request.max_questions} questions (randomly selected from {original_count} available)")
        
        print(f"Created file-based quiz with {len(combined_questions)} questions from {len(request.file_paths)} files")
        
        return combined_questions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file-based quiz: {str(e)}")


# ============================================================================
# Video Routes
# ============================================================================

@app.post("/api/videos/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """Generate video for a concept."""
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


@app.post("/api/videos/generate-random", response_model=VideoGenerateResponse)
async def generate_random_video():
    """Generate video for a randomly selected concept."""
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


@app.get("/api/videos/cached", response_model=List[VideoGenerateResponse])
async def list_cached_videos():
    """List all cached videos."""
    try:
        cache_dir = _get_cache_dir()
        generator = VideoGenerator()
        cached_videos = generator.list_cached_videos(cache_dir)
        
        responses = []
        for video in cached_videos:
            topic = video.get('topic', 'Unknown Topic')
            subtopic = video.get('subtopic', 'Unknown Subtopic')
            concept = video.get('concept', 'Unknown Concept')
            cache_key = video.get('cache_key', '')
            
            responses.append(VideoGenerateResponse(
                video_path=video['video_path'],
                audio_path="",
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


@app.get("/api/videos/file/{filename}")
async def serve_video_file(filename: str):
    """Serve video or audio files with full streaming support."""
    try:
        video_service_dir = _get_video_service_dir()
        file_path = video_service_dir / "output" / filename
        
        if not file_path.exists():
            file_path = video_service_dir / "cache" / filename
        
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        file_size = file_path.stat().st_size
        
        if file_size == 0:
            raise HTTPException(status_code=404, detail=f"File is empty: {filename}")
        
        media_type = "video/mp4" if filename.endswith(".mp4") else "audio/mpeg"
        
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


# ============================================================================
# Root Routes
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Adaptive Learning Platform API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


