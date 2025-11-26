"""Question generation API routes."""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from functools import partial
import sys
import json
from pathlib import Path

from backend.quiz_service.services.question.generator import QuestionGenerator
from backend.quiz_service.services.question.adapter import QuestionAdapter
from backend.quiz_service.services.tracking.performance_tracker import PerformanceTracker
from backend.shared.services.llm.mistral_client import MistralClient
from backend.course_service.models.course import CourseStructure, Topic, Subtopic, Concept
from backend.quiz_service.models.question import DifficultyLevel

router = APIRouter()

# Calculate backend root
BACKEND_ROOT = Path(__file__).parent.parent.parent

# Global instances (in production, use dependency injection)
_mistral_client = None
_question_generator = None
_course = None


def get_mistral_client():
    """Get or create Mistral client."""
    global _mistral_client
    if (_mistral_client is None):
        _mistral_client = MistralClient()
    return _mistral_client


def get_question_generator():
    """Get or create question generator."""
    global _question_generator
    if (_question_generator is None):
        _question_generator = QuestionGenerator(get_mistral_client())
    return _question_generator


def get_course(force_reload: bool = False):
    """Get or load course from parsed_data.json.
    
    Args:
        force_reload: If True, reload the course even if already loaded
    """
    global _course
    if (_course is None or force_reload):
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
            # Split content into chunks to create multiple concepts if content is long
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
                content=content_preview  # Use more content for better context
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


class FileQuizRequest(BaseModel):
    """Request model for file-based quiz."""
    file_paths: List[str]


@router.post("/generate", response_model=QuestionResponse)
async def generate_question(
    request: Optional[dict] = Body(default=None)
):
    """Generate a new adaptive question."""
    try:
        course = get_course()
        generator = get_question_generator()
        
        # Create performance tracker from provided data or empty
        from backend.quiz_service.models.user_state import UserPerformance
        
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
        # topic, subtopic, concept, difficulty = adapter._select_random_concept(all_concepts=adapter.course.get_all_concepts()) # TODO: For testing use random
        print(f"Selected concept: Topic='{topic}', Subtopic='{subtopic}', Concept='{concept.name}', Difficulty='{difficulty}'")

        # Get content context from parsed data
        content_context = ""
        topic_obj = next((t for t in course.topics if t.name == topic), None)
        if topic_obj:
            subtopic_obj = next((st for st in topic_obj.subtopics if st.name == subtopic), None)
            if subtopic_obj:
                content_context = subtopic_obj.content or ""
            
            # If no content in subtopic, try to get from parsed_data.json directly
            if not content_context:
                parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
                if parsed_data_file.exists():
                    with open(parsed_data_file, 'r', encoding='utf-8') as f:
                        parsed_data = json.load(f)
                    
                    # Find matching file by topic name
                    for file_path, file_data in parsed_data.items():
                        file_name = file_data["metadata"]["file_name"]
                        if topic.lower() in file_name.lower() or file_name.lower().replace('.pdf', '') in topic.lower():
                            # Use more content for better question generation (up to 20000 chars)
                            full_content = file_data["content"]
                            content_context = full_content[:20000] if len(full_content) > 20000 else full_content
                            break
        
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
        from backend.shared.services.llm.prompts import EXPLANATION_CHAT_PROMPT
        
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


@router.post("/start-file-quiz", response_model=List[QuestionResponse])
async def start_file_based_quiz(request: FileQuizRequest):
    """Start a quiz using questions from selected files.
    
    Args:
        request: File paths to include in the quiz
        
    Returns:
        Combined list of quiz questions from selected files
    """
    try:
        # Load parsed_data.json to get quiz questions
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        # Collect questions from selected files
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
            
            # Convert each question to QuestionResponse format
            for question_data in quiz_questions:
                try:
                    # Convert answers to AnswerOption format
                    answer_options = []
                    for answer in question_data.get("answers", []):
                        answer_options.append(AnswerOption(
                            text=answer.get("text", ""),
                            is_correct=answer.get("is_correct", False),
                            explanation=answer.get("explanation", "")
                        ))
                    
                    # Create QuestionResponse object
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
        
        # Shuffle questions for variety
        import random
        random.shuffle(combined_questions)
        
        print(f"Created file-based quiz with {len(combined_questions)} questions from {len(request.file_paths)} files")
        
        return combined_questions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file-based quiz: {str(e)}")


