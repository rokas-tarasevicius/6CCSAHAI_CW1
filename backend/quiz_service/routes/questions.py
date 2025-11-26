"""Question API routes - File-based quiz only."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import json
import random
from pathlib import Path

router = APIRouter()

# Calculate backend root
BACKEND_ROOT = Path(__file__).parent.parent.parent


class AnswerOption(BaseModel):
    text: str
    is_correct: bool
    explanation: str = ""


class QuestionResponse(BaseModel):
    question_text: str
    answers: List[AnswerOption]
    topic: str
    subtopic: str
    concepts: List[str]
    difficulty: str
    explanation: str


class FileQuizRequest(BaseModel):
    file_paths: List[str]


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
        random.shuffle(combined_questions)
        
        print(f"Created file-based quiz with {len(combined_questions)} questions from {len(request.file_paths)} files")
        
        return combined_questions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file-based quiz: {str(e)}")


