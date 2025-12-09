"""User profile model."""
from typing import List
from pydantic import BaseModel, Field


class IncorrectConceptRef(BaseModel):
    """Reference to a concept answered incorrectly."""
    topic: str
    subtopic: str
    concept: str = Field(description="Concept name matching course structure")


class UserProfile(BaseModel):
    """User profile data stored in session."""
    rating: float = Field(default=1000.0, ge=0.0, description="User rating points (default: 1000)")
    incorrect_concepts: List[IncorrectConceptRef] = Field(
        default_factory=list,
        description="Concepts the user answered incorrectly in the latest quiz"
    )

