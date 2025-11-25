"""Feedback loop for adaptive question difficulty."""
from backend.quiz_service.models.question import DifficultyLevel
from backend.quiz_service.models.user_state import UserPerformance, ConceptScore
from typing import Optional


class FeedbackLoop:
    """Adaptive feedback mechanism for question difficulty."""
    
    @staticmethod
    def calculate_next_difficulty(
        concept_score: Optional[ConceptScore],
        current_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    ) -> DifficultyLevel:
        """Calculate appropriate difficulty for next question.
        
        Args:
            concept_score: Performance data for the concept
            current_difficulty: Current difficulty level
            
        Returns:
            Recommended difficulty level
        """
        if concept_score is None or concept_score.attempts == 0:
            # Start with medium for new concepts
            return DifficultyLevel.MEDIUM
        
        accuracy = concept_score.accuracy
        attempts = concept_score.attempts
        
        # Need at least 2 attempts to adapt
        if attempts < 2:
            return current_difficulty
        
        # Adapt based on performance
        if accuracy >= 80:
            # High accuracy - increase difficulty
            if current_difficulty == DifficultyLevel.EASY:
                return DifficultyLevel.MEDIUM
            elif current_difficulty == DifficultyLevel.MEDIUM:
                return DifficultyLevel.HARD
            else:
                return DifficultyLevel.HARD
        elif accuracy >= 60:
            # Medium accuracy - maintain or slightly adjust
            if current_difficulty == DifficultyLevel.EASY:
                return DifficultyLevel.MEDIUM
            else:
                return current_difficulty
        else:
            # Low accuracy - decrease difficulty
            if current_difficulty == DifficultyLevel.HARD:
                return DifficultyLevel.MEDIUM
            elif current_difficulty == DifficultyLevel.MEDIUM:
                return DifficultyLevel.EASY
            else:
                return DifficultyLevel.EASY
    
    @staticmethod
    def should_move_to_new_concept(
        concept_score: Optional[ConceptScore],
        min_attempts: int = 3,
        mastery_threshold: float = 80.0
    ) -> bool:
        """Determine if user should move to a new concept.
        
        Args:
            concept_score: Performance data for the concept
            min_attempts: Minimum attempts before moving on
            mastery_threshold: Accuracy threshold for mastery
            
        Returns:
            True if should move to new concept
        """
        if concept_score is None:
            return False
        
        # Not enough attempts yet
        if concept_score.attempts < min_attempts:
            return False
        
        # Check if mastered
        if concept_score.accuracy >= mastery_threshold:
            return True
        
        # If many attempts with low accuracy, might also move on
        # to avoid frustration, but mark as weak area
        if concept_score.attempts >= min_attempts * 2 and concept_score.accuracy < 50:
            return True
        
        return False
    
    @staticmethod
    def calculate_review_priority(performance: UserPerformance) -> list[tuple[str, str, str, float]]:
        """Calculate which concepts need review most urgently.
        
        Args:
            performance: User performance data
            
        Returns:
            List of (topic, subtopic, concept, urgency_score) tuples
            Higher urgency score = more urgent
        """
        priorities = []
        
        for topic_name, topic_score in performance.topic_scores.items():
            for subtopic_name, subtopic_score in topic_score.subtopic_scores.items():
                for concept_name, concept_score in subtopic_score.concept_scores.items():
                    if concept_score.attempts == 0:
                        continue
                    
                    # Calculate urgency based on:
                    # 1. Low accuracy (high urgency)
                    # 2. Recent attempts (slightly lower urgency)
                    # 3. Multiple incorrect attempts (high urgency)
                    
                    accuracy_urgency = (100 - concept_score.accuracy) / 100.0  # 0-1
                    attempt_factor = min(concept_score.attempts / 3.0, 1.5)  # More attempts = higher urgency
                    
                    urgency = accuracy_urgency * attempt_factor
                    
                    # Weak concepts get boosted urgency
                    if concept_score.is_weak:
                        urgency *= 1.5
                    
                    priorities.append((topic_name, subtopic_name, concept_name, urgency))
        
        # Sort by urgency (highest first)
        priorities.sort(key=lambda x: x[3], reverse=True)
        return priorities

