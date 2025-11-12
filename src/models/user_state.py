"""User performance and session state models."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ConceptScore(BaseModel):
    """Score tracking for a specific concept."""
    concept_name: str
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0
    last_attempted: Optional[datetime] = None
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        if self.attempts == 0:
            return 0.0
        return (self.correct / self.attempts) * 100
    
    @property
    def is_weak(self) -> bool:
        """Determine if this is a weak concept (< 60% accuracy with at least 2 attempts)."""
        return self.attempts >= 2 and self.accuracy < 60.0


class SubtopicScore(BaseModel):
    """Score tracking for a subtopic."""
    subtopic_name: str
    concept_scores: Dict[str, ConceptScore] = Field(default_factory=dict)
    
    @property
    def overall_accuracy(self) -> float:
        """Calculate overall accuracy for this subtopic."""
        if not self.concept_scores:
            return 0.0
        total_correct = sum(cs.correct for cs in self.concept_scores.values())
        total_attempts = sum(cs.attempts for cs in self.concept_scores.values())
        if total_attempts == 0:
            return 0.0
        return (total_correct / total_attempts) * 100
    
    def get_weak_concepts(self) -> List[str]:
        """Get list of weak concept names."""
        return [name for name, score in self.concept_scores.items() if score.is_weak]


class TopicScore(BaseModel):
    """Score tracking for a topic."""
    topic_name: str
    subtopic_scores: Dict[str, SubtopicScore] = Field(default_factory=dict)
    
    @property
    def overall_accuracy(self) -> float:
        """Calculate overall accuracy for this topic."""
        if not self.subtopic_scores:
            return 0.0
        accuracies = [ss.overall_accuracy for ss in self.subtopic_scores.values() 
                     if sum(cs.attempts for cs in ss.concept_scores.values()) > 0]
        if not accuracies:
            return 0.0
        return sum(accuracies) / len(accuracies)


class UserPerformance(BaseModel):
    """Complete user performance tracking."""
    total_questions_answered: int = 0
    total_correct: int = 0
    total_incorrect: int = 0
    trophy_score: int = 0
    topic_scores: Dict[str, TopicScore] = Field(default_factory=dict)
    
    @property
    def overall_accuracy(self) -> float:
        """Calculate overall accuracy."""
        if self.total_questions_answered == 0:
            return 0.0
        return (self.total_correct / self.total_questions_answered) * 100
    
    def get_all_weak_concepts(self) -> List[tuple[str, str, str]]:
        """Get all weak concepts as (topic, subtopic, concept) tuples."""
        weak_concepts = []
        for topic_name, topic_score in self.topic_scores.items():
            for subtopic_name, subtopic_score in topic_score.subtopic_scores.items():
                for concept_name in subtopic_score.get_weak_concepts():
                    weak_concepts.append((topic_name, subtopic_name, concept_name))
        return weak_concepts
