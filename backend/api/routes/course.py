"""Course material API routes."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import tempfile
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.utils.course_loader import CourseLoader
from src.models.course import CourseStructure
from src.services.document import parse_files
from llama_cloud_services import LlamaParse

router = APIRouter()


class CourseResponse(BaseModel):
    """Course structure response."""
    title: str
    description: str
    topics: List[dict]


@router.get("/", response_model=CourseResponse)
async def get_course():
    """Get course material."""
    try:
        # Resolve path relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        course_path = project_root / "data" / "course_material.json"
        course = CourseLoader.load_from_file(str(course_path))
        return CourseResponse(
            title=course.title,
            description=course.description,
            topics=[
                {
                    "name": topic.name,
                    "description": topic.description,
                    "subtopics": [
                        {
                            "name": subtopic.name,
                            "description": subtopic.description,
                            "concepts": [
                                {
                                    "name": concept.name,
                                    "description": concept.description,
                                    "keywords": concept.keywords
                                }
                                for concept in subtopic.concepts
                            ],
                            "content": subtopic.content
                        }
                        for subtopic in topic.subtopics
                    ]
                }
                for topic in course.topics
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load course: {str(e)}")


class UploadResponse(BaseModel):
    """PDF upload response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and parse a PDF file."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    # Get API key
    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
    if not LLAMA_CLOUD_API_KEY:
        raise HTTPException(status_code=500, detail="LLAMA_CLOUD_API_KEY environment variable not set")
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name
    
    try:
        # Initialize parser (reduce workers for single file)
        parser = LlamaParse(
            api_key=LLAMA_CLOUD_API_KEY,
            num_workers=1,  # Use 1 worker for single file uploads
            verbose=True,
            language="en"
        )
        
        # Parse the file with timeout (5 minutes max)
        try:
            result = await asyncio.wait_for(
                parse_files([tmp_path], parser),
                timeout=300.0  # 5 minutes timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504, 
                detail="PDF parsing timed out. The file may be too large or complex. Please try a smaller file."
            )
        
        # Extract the parsed data (result is a dict with file path as key)
        parsed_data = result.get(tmp_path)
        
        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse PDF - no data returned")
        
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
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


