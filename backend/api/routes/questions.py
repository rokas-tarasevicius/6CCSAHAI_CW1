"""Question generation API routes."""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from functools import partial
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.question.generator import QuestionGenerator
from src.services.question.adapter import QuestionAdapter
from src.services.tracking.performance_tracker import PerformanceTracker
from src.services.llm.mistral_client import MistralClient
from src.utils.course_loader import CourseLoader
from src.models.question import DifficultyLevel

router = APIRouter()

# Global instances (in production, use dependency injection)
_mistral_client = None
_question_generator = None
_course = None


def get_mistral_client():
    """Get or create Mistral client."""
    global _mistral_client
    if _mistral_client is None:
        _mistral_client = MistralClient()
    return _mistral_client


def get_question_generator():
    """Get or create question generator."""
    global _question_generator
    if _question_generator is None:
        _question_generator = QuestionGenerator(get_mistral_client())
    return _question_generator


def get_course():
    """Get or load course."""
    global _course
    if _course is None:
        # Resolve path relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        course_path = project_root / "data" / "course_material.json"
        _course = CourseLoader.load_from_file(str(course_path))
    return _course


class AnswerOption(BaseModel):
    """Answer option model."""
    text: str
    is_correct: bool
    explanation: Optional[str] = None


class QuestionResponse(BaseModel):
    """Question response model."""
    question_text: str
    answers: List[AnswerOption]
    topic: str
    subtopic: str
    concepts: List[str]
    difficulty: str
    explanation: str


class AnswerSubmission(BaseModel):
    """Answer submission model."""
    question_id: Optional[str] = None
    selected_answer_index: int
    topic: str
    subtopic: str
    concept: str


class AnswerResult(BaseModel):
    """Answer result model."""
    is_correct: bool
    correct_answer_index: int
    explanation: str
    trophy_score_change: int


@router.post("/generate", response_model=QuestionResponse)
async def generate_question(
    request: Optional[dict] = Body(default=None)
):
    """Generate a new adaptive question."""
    try:
        course = get_course()
        generator = get_question_generator()
        
        # Create performance tracker from provided data or empty
        from src.models.user_state import UserPerformance
        
        # Extract performance_data from request body
        if request and isinstance(request, dict):
            performance_data = request.get('performance_data')
        else:
            performance_data = None
        
        if performance_data and isinstance(performance_data, dict) and len(performance_data) > 0:
            try:
                performance = UserPerformance(**performance_data)
            except Exception as e:
                # If performance data is invalid, use empty performance
                print(f"Warning: Invalid performance data: {e}")
                performance = UserPerformance()
        else:
            performance = UserPerformance()
        
        tracker = PerformanceTracker(performance)
        adapter = QuestionAdapter(course, tracker)
        
        # Select next concept
        topic, subtopic, concept, difficulty = adapter.select_next_concept()
        
        # Get content context (optimized lookup)
        content_context = ""
        # Cache topic/subtopic lookup for faster access
        topic_obj = next((t for t in course.topics if t.name == topic), None)
        if topic_obj:
            subtopic_obj = next((st for st in topic_obj.subtopics if st.name == subtopic), None)
            if subtopic_obj:
                content_context = subtopic_obj.content or ""
        
        # Generate question
        question = generator.generate_question(
            topic=topic,
            subtopic=subtopic,
            concept=concept,
            difficulty=difficulty,
            content_context=content_context
        )
        
        return QuestionResponse(
            question_text=question.question_text,
            answers=[
                AnswerOption(
                    text=ans.text,
                    is_correct=ans.is_correct,
                    explanation=ans.explanation
                )
                for ans in question.answers
            ],
            topic=question.topic,
            subtopic=question.subtopic,
            concepts=question.concepts,
            difficulty=question.difficulty.value,
            explanation=question.explanation
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating question: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate question: {str(e)}"
        )


@router.post("/submit-answer", response_model=AnswerResult)
async def submit_answer(submission: AnswerSubmission):
    """Submit an answer and get result."""
    try:
        # This would typically use the question_id to retrieve the question
        # For now, we'll return a basic result
        # In production, store questions temporarily or regenerate
        
        # The frontend should have the question data, so we'll trust it
        # and just return the result structure
        return AnswerResult(
            is_correct=False,  # Will be calculated by frontend
            correct_answer_index=0,
            explanation="",
            trophy_score_change=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")


@router.post("/explain")
async def get_explanation(
    question_text: str,
    correct_answer: str,
    student_answer: str,
    was_correct: bool,
    topic: str,
    subtopic: str,
    concepts: List[str],
    explanation: str,
    student_question: str
):
    """Get AI explanation for follow-up question."""
    try:
        client = get_mistral_client()
        from src.services.llm.prompts import EXPLANATION_CHAT_PROMPT
        
        response = client.generate_with_template(
            EXPLANATION_CHAT_PROMPT,
            question_text=question_text,
            correct_answer=correct_answer,
            student_answer=student_answer,
            was_correct=str(was_correct),
            topic=topic,
            subtopic=subtopic,
            concepts=", ".join(concepts),
            explanation=explanation,
            student_question=student_question
        )
        
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


