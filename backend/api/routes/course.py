"""Course material API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.utils.course_loader import CourseLoader
from src.models.course import CourseStructure

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
        course = CourseLoader.load_from_file("data/course_material.json")
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


