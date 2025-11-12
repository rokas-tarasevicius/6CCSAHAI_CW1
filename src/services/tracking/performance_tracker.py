"""Performance tracking service for user progress."""
from datetime import datetime
from typing import Optional
from src.models.user_state import UserPerformance, TopicScore, SubtopicScore, ConceptScore


class PerformanceTracker:
    """Track user performance across topics, subtopics, and concepts."""
    
    def __init__(self, performance: Optional[UserPerformance] = None):
        """Initialize performance tracker.
        
        Args:
            performance: Optional existing UserPerformance instance
        """
        self.performance = performance or UserPerformance()
    
    def record_answer(
        self,
        topic: str,
        subtopic: str,
        concept: str,
        is_correct: bool
    ) -> None:
        """Record a user's answer.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept name
            is_correct: Whether the answer was correct
        """
        # Update overall stats
        self.performance.total_questions_answered += 1
        if is_correct:
            self.performance.total_correct += 1
            self.performance.trophy_score += 10
        else:
            self.performance.total_incorrect += 1
            self.performance.trophy_score = max(0, self.performance.trophy_score - 5)
        
        # Ensure topic exists
        if topic not in self.performance.topic_scores:
            self.performance.topic_scores[topic] = TopicScore(topic_name=topic)
        
        topic_score = self.performance.topic_scores[topic]
        
        # Ensure subtopic exists
        if subtopic not in topic_score.subtopic_scores:
            topic_score.subtopic_scores[subtopic] = SubtopicScore(subtopic_name=subtopic)
        
        subtopic_score = topic_score.subtopic_scores[subtopic]
        
        # Ensure concept exists
        if concept not in subtopic_score.concept_scores:
            subtopic_score.concept_scores[concept] = ConceptScore(concept_name=concept)
        
        concept_score = subtopic_score.concept_scores[concept]
        
        # Update concept stats
        concept_score.attempts += 1
        concept_score.last_attempted = datetime.now()
        if is_correct:
            concept_score.correct += 1
        else:
            concept_score.incorrect += 1
    
    def get_weak_areas(self, min_attempts: int = 2) -> list[tuple[str, str, str, float]]:
        """Get weak areas (< 60% accuracy with minimum attempts).
        
        Args:
            min_attempts: Minimum attempts required to consider
            
        Returns:
            List of (topic, subtopic, concept, accuracy) tuples
        """
        weak_areas = []
        
        for topic_name, topic_score in self.performance.topic_scores.items():
            for subtopic_name, subtopic_score in topic_score.subtopic_scores.items():
                for concept_name, concept_score in subtopic_score.concept_scores.items():
                    if concept_score.attempts >= min_attempts and concept_score.accuracy < 60.0:
                        weak_areas.append((
                            topic_name,
                            subtopic_name,
                            concept_name,
                            concept_score.accuracy
                        ))
        
        # Sort by accuracy (lowest first)
        weak_areas.sort(key=lambda x: x[3])
        return weak_areas
    
    def get_untried_concepts(
        self,
        all_concepts: list[tuple[str, str, str]]
    ) -> list[tuple[str, str, str]]:
        """Get concepts that haven't been attempted yet.
        
        Args:
            all_concepts: List of (topic, subtopic, concept) tuples from course
            
        Returns:
            List of untried (topic, subtopic, concept) tuples
        """
        untried = []
        
        for topic, subtopic, concept in all_concepts:
            # Check if concept has been attempted
            if topic not in self.performance.topic_scores:
                untried.append((topic, subtopic, concept))
                continue
            
            topic_score = self.performance.topic_scores[topic]
            if subtopic not in topic_score.subtopic_scores:
                untried.append((topic, subtopic, concept))
                continue
            
            subtopic_score = topic_score.subtopic_scores[subtopic]
            if concept not in subtopic_score.concept_scores:
                untried.append((topic, subtopic, concept))
        
        return untried
    
    def get_concept_performance(
        self,
        topic: str,
        subtopic: str,
        concept: str
    ) -> Optional[ConceptScore]:
        """Get performance data for a specific concept.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept name
            
        Returns:
            ConceptScore or None if not found
        """
        if topic not in self.performance.topic_scores:
            return None
        
        topic_score = self.performance.topic_scores[topic]
        if subtopic not in topic_score.subtopic_scores:
            return None
        
        subtopic_score = topic_score.subtopic_scores[subtopic]
        return subtopic_score.concept_scores.get(concept)
    
    def get_summary(self) -> dict:
        """Get a summary of performance.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            "total_questions": self.performance.total_questions_answered,
            "correct": self.performance.total_correct,
            "incorrect": self.performance.total_incorrect,
            "accuracy": self.performance.overall_accuracy,
            "trophy_score": self.performance.trophy_score,
            "topics_covered": len(self.performance.topic_scores),
            "weak_areas_count": len(self.get_weak_areas())
        }

