"""Question and answer data models."""
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Answer(BaseModel):
    """A single answer option."""
    text: str
    is_correct: bool
    explanation: Optional[str] = None


class MultipleChoiceQuestion(BaseModel):
    """A multiple choice question."""
    question_text: str
    answers: List[Answer] = Field(min_length=2, max_length=6)
    topic: str
    subtopic: str
    concepts: List[str] = Field(default_factory=list)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    explanation: str = ""
    
    def get_correct_answer_index(self) -> int:
        """Get the index of the correct answer."""
        for idx, answer in enumerate(self.answers):
            if answer.is_correct:
                return idx
        return -1
    
    def get_correct_answer(self) -> Optional[Answer]:
        """Get the correct answer object."""
        for answer in self.answers:
            if answer.is_correct:
                return answer
        return None

