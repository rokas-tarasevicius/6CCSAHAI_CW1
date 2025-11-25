"""Performance tracking API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
# Path setup handled by main.py

from backend.quiz_service.services.tracking.performance_tracker import PerformanceTracker
from backend.quiz_service.models.user_state import ConceptScore, SubtopicScore, TopicScore, UserPerformance

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


def _serialize_concept_score(concept_name: str, concept_score: ConceptScore) -> dict:
    """Serialize a ConceptScore including metadata that the frontend can re-send."""
    return {
        "concept_name": concept_name,
        "attempts": concept_score.attempts,
        "correct": concept_score.correct,
        "incorrect": concept_score.incorrect,
        "accuracy": concept_score.accuracy,
        "is_weak": concept_score.is_weak,
        "last_attempted": concept_score.last_attempted.isoformat()
        if concept_score.last_attempted
        else None,
    }


def _serialize_subtopic_score(
    subtopic_name: str, subtopic_score: SubtopicScore
) -> dict:
    """Serialize a SubtopicScore with its name and child concept data."""
    return {
        "subtopic_name": subtopic_name,
        "overall_accuracy": subtopic_score.overall_accuracy,
        "concept_scores": {
            concept_name: _serialize_concept_score(concept_name, concept_score)
            for concept_name, concept_score in subtopic_score.concept_scores.items()
        },
    }


def _serialize_topic_score(topic_name: str, topic_score: TopicScore) -> dict:
    """Serialize a TopicScore with its name and child subtopic data."""
    return {
        "topic_name": topic_name,
        "overall_accuracy": topic_score.overall_accuracy,
        "subtopic_scores": {
            subtopic_name: _serialize_subtopic_score(subtopic_name, subtopic_score)
            for subtopic_name, subtopic_score in topic_score.subtopic_scores.items()
        },
    }


def _serialize_topic_scores(performance: UserPerformance) -> Dict[str, dict]:
    """Serialize the nested topic scores dictionary including metadata."""
    return {
        topic_name: _serialize_topic_score(topic_name, topic_score)
        for topic_name, topic_score in performance.topic_scores.items()
    }


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
            topic_scores=_serialize_topic_scores(tracker.performance),
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
        
        from backend.quiz_service.services.tracking.analytics import PerformanceAnalytics
        insights = PerformanceAnalytics.generate_insights(performance)
        mastery = PerformanceAnalytics.get_mastery_level(performance)
        
        return {
            **summary,
            "insights": insights,
            "mastery_level": mastery
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


