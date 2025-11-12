"""Performance tracking API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.tracking.performance_tracker import PerformanceTracker
from src.models.user_state import UserPerformance

router = APIRouter()


class RecordAnswerRequest(BaseModel):
    """Record answer request."""
    performance_data: dict
    topic: str
    subtopic: str
    concept: str
    is_correct: bool


class PerformanceResponse(BaseModel):
    """Performance response."""
    total_questions_answered: int
    total_correct: int
    total_incorrect: int
    trophy_score: int
    overall_accuracy: float
    topic_scores: Dict[str, dict]


@router.post("/record-answer", response_model=PerformanceResponse)
async def record_answer(request: RecordAnswerRequest):
    """Record an answer and update performance."""
    try:
        performance = UserPerformance(**request.performance_data)
        tracker = PerformanceTracker(performance)
        
        tracker.record_answer(
            topic=request.topic,
            subtopic=request.subtopic,
            concept=request.concept,
            is_correct=request.is_correct
        )
        
        return PerformanceResponse(
            total_questions_answered=tracker.performance.total_questions_answered,
            total_correct=tracker.performance.total_correct,
            total_incorrect=tracker.performance.total_incorrect,
            trophy_score=tracker.performance.trophy_score,
            overall_accuracy=tracker.performance.overall_accuracy,
            topic_scores={
                topic_name: {
                    "overall_accuracy": topic_score.overall_accuracy,
                    "subtopic_scores": {
                        st_name: {
                            "overall_accuracy": st_score.overall_accuracy,
                            "concept_scores": {
                                c_name: {
                                    "attempts": c_score.attempts,
                                    "correct": c_score.correct,
                                    "incorrect": c_score.incorrect,
                                    "accuracy": c_score.accuracy,
                                    "is_weak": c_score.is_weak
                                }
                                for c_name, c_score in st_score.concept_scores.items()
                            }
                        }
                        for st_name, st_score in topic_score.subtopic_scores.items()
                    }
                }
                for topic_name, topic_score in tracker.performance.topic_scores.items()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record answer: {str(e)}")


@router.post("/weak-areas")
async def get_weak_areas(performance_data: dict, min_attempts: int = 2):
    """Get weak areas from performance."""
    try:
        performance = UserPerformance(**performance_data)
        tracker = PerformanceTracker(performance)
        
        weak_areas = tracker.get_weak_areas(min_attempts=min_attempts)
        
        return {
            "weak_areas": [
                {
                    "topic": topic,
                    "subtopic": subtopic,
                    "concept": concept,
                    "accuracy": accuracy
                }
                for topic, subtopic, concept, accuracy in weak_areas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weak areas: {str(e)}")


@router.post("/summary")
async def get_performance_summary(performance_data: dict):
    """Get performance summary."""
    try:
        performance = UserPerformance(**performance_data)
        tracker = PerformanceTracker(performance)
        
        summary = tracker.get_summary()
        
        from src.services.tracking.analytics import PerformanceAnalytics
        insights = PerformanceAnalytics.generate_insights(performance)
        mastery = PerformanceAnalytics.get_mastery_level(performance)
        
        return {
            **summary,
            "insights": insights,
            "mastery_level": mastery
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


