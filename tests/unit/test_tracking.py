"""Unit tests for tracking services."""
import pytest
from src.models.user_state import UserPerformance, ConceptScore
from src.models.question import DifficultyLevel
from src.services.tracking.performance_tracker import PerformanceTracker
from src.services.tracking.feedback_loop import FeedbackLoop
from src.services.tracking.analytics import PerformanceAnalytics


class TestPerformanceTracker:
    """Test performance tracking."""
    
    def test_record_correct_answer(self):
        """Test recording a correct answer."""
        tracker = PerformanceTracker()
        
        tracker.record_answer("Python", "Variables", "Assignment", is_correct=True)
        
        assert tracker.performance.total_questions_answered == 1
        assert tracker.performance.total_correct == 1
        assert tracker.performance.trophy_score == 10
    
    def test_record_incorrect_answer(self):
        """Test recording an incorrect answer."""
        tracker = PerformanceTracker()
        
        tracker.record_answer("Python", "Variables", "Assignment", is_correct=False)
        
        assert tracker.performance.total_questions_answered == 1
        assert tracker.performance.total_incorrect == 1
        assert tracker.performance.trophy_score == 0
    
    def test_get_weak_areas(self):
        """Test getting weak areas."""
        tracker = PerformanceTracker()
        
        # Create weak area
        for _ in range(5):
            tracker.record_answer("Python", "Variables", "Assignment", is_correct=False)
        
        weak_areas = tracker.get_weak_areas(min_attempts=2)
        assert len(weak_areas) == 1
        assert weak_areas[0][2] == "Assignment"


class TestFeedbackLoop:
    """Test feedback loop."""
    
    def test_calculate_difficulty_for_new_concept(self):
        """Test difficulty calculation for new concept."""
        difficulty = FeedbackLoop.calculate_next_difficulty(None)
        assert difficulty == DifficultyLevel.MEDIUM
    
    def test_increase_difficulty_for_high_accuracy(self):
        """Test increasing difficulty for high accuracy."""
        concept_score = ConceptScore(
            concept_name="Test",
            attempts=3,
            correct=3,
            incorrect=0
        )
        
        difficulty = FeedbackLoop.calculate_next_difficulty(
            concept_score,
            DifficultyLevel.EASY
        )
        
        assert difficulty == DifficultyLevel.MEDIUM
    
    def test_decrease_difficulty_for_low_accuracy(self):
        """Test decreasing difficulty for low accuracy."""
        concept_score = ConceptScore(
            concept_name="Test",
            attempts=5,
            correct=1,
            incorrect=4
        )
        
        difficulty = FeedbackLoop.calculate_next_difficulty(
            concept_score,
            DifficultyLevel.HARD
        )
        
        assert difficulty == DifficultyLevel.MEDIUM
    
    def test_should_move_to_new_concept(self):
        """Test determining if should move to new concept."""
        # Mastered concept
        mastered = ConceptScore(
            concept_name="Test",
            attempts=3,
            correct=3,
            incorrect=0
        )
        
        assert FeedbackLoop.should_move_to_new_concept(mastered)
        
        # Not enough attempts
        new_concept = ConceptScore(
            concept_name="Test",
            attempts=1,
            correct=1,
            incorrect=0
        )
        
        assert not FeedbackLoop.should_move_to_new_concept(new_concept)


class TestPerformanceAnalytics:
    """Test performance analytics."""
    
    def test_get_mastery_level_beginner(self):
        """Test mastery level for beginner."""
        performance = UserPerformance(
            total_questions_answered=3,
            total_correct=2,
            total_incorrect=1
        )
        
        level = PerformanceAnalytics.get_mastery_level(performance)
        assert level == "Beginner"
    
    def test_get_mastery_level_advanced(self):
        """Test mastery level for advanced."""
        performance = UserPerformance(
            total_questions_answered=20,
            total_correct=18,
            total_incorrect=2
        )
        
        level = PerformanceAnalytics.get_mastery_level(performance)
        assert level == "Advanced"
    
    def test_generate_insights(self):
        """Test insight generation."""
        performance = UserPerformance(
            total_questions_answered=10,
            total_correct=8,
            total_incorrect=2
        )
        
        insights = PerformanceAnalytics.generate_insights(performance)
        assert len(insights) > 0
        assert any("80" in insight for insight in insights)

