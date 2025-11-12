"""Adaptive question selection algorithm."""
import random
from typing import Optional, Tuple
from src.models.course import CourseStructure, Concept
from src.models.user_state import UserPerformance
from src.models.question import DifficultyLevel
from src.services.tracking.performance_tracker import PerformanceTracker
from src.services.tracking.feedback_loop import FeedbackLoop
from src.services.tracking.analytics import PerformanceAnalytics


class QuestionAdapter:
    """Select questions adaptively based on user performance."""
    
    def __init__(
        self,
        course: CourseStructure,
        performance_tracker: PerformanceTracker
    ):
        """Initialize question adapter.
        
        Args:
            course: Course structure
            performance_tracker: Performance tracker instance
        """
        self.course = course
        self.tracker = performance_tracker
        self.performance = performance_tracker.performance
    
    def select_next_concept(self) -> Tuple[str, str, Concept, DifficultyLevel]:
        """Select the next concept to quiz on.
        
        Returns:
            Tuple of (topic_name, subtopic_name, concept, difficulty)
        """
        # Get all concepts from course
        all_concepts = self.course.get_all_concepts()
        
        if not all_concepts:
            raise ValueError("No concepts available in course")
        
        # Strategy 1: Review weak areas (40% of time if weak areas exist)
        weak_areas = self.tracker.get_weak_areas(min_attempts=2)
        if weak_areas and random.random() < 0.4:
            return self._select_from_weak_areas(weak_areas)
        
        # Strategy 2: Focus on priority concepts from analytics (40% of time)
        priorities = PerformanceAnalytics.get_concept_priorities(self.performance)
        if priorities and random.random() < 0.67:  # 0.4 / (1-0.4) ≈ 0.67
            return self._select_from_priorities(priorities, all_concepts)
        
        # Strategy 3: Try untried concepts (remaining time)
        untried = self.tracker.get_untried_concepts([
            (topic, subtopic, concept.name) 
            for topic, subtopic, concept in all_concepts
        ])
        
        if untried:
            return self._select_untried_concept(untried, all_concepts)
        
        # Fallback: random selection from all concepts
        return self._select_random_concept(all_concepts)
    
    def _select_from_weak_areas(
        self,
        weak_areas: list[tuple[str, str, str, float]]
    ) -> Tuple[str, str, Concept, DifficultyLevel]:
        """Select from weak areas.
        
        Args:
            weak_areas: List of weak areas with accuracy
            
        Returns:
            Tuple of (topic_name, subtopic_name, concept, difficulty)
        """
        # Pick the weakest area (lowest accuracy)
        topic_name, subtopic_name, concept_name, _ = weak_areas[0]
        
        # Find the concept object
        concept = self._find_concept(topic_name, subtopic_name, concept_name)
        
        # Get current performance
        concept_score = self.tracker.get_concept_performance(topic_name, subtopic_name, concept_name)
        
        # Calculate difficulty
        difficulty = FeedbackLoop.calculate_next_difficulty(concept_score, DifficultyLevel.EASY)
        
        return topic_name, subtopic_name, concept, difficulty
    
    def _select_from_priorities(
        self,
        priorities: list[tuple[str, str, str, float]],
        all_concepts: list[tuple[str, str, Concept]]
    ) -> Tuple[str, str, Concept, DifficultyLevel]:
        """Select from priority concepts.
        
        Args:
            priorities: List of prioritized concepts
            all_concepts: All available concepts
            
        Returns:
            Tuple of (topic_name, subtopic_name, concept, difficulty)
        """
        # Select from top 3 priorities randomly
        top_n = min(3, len(priorities))
        topic_name, subtopic_name, concept_name, _ = random.choice(priorities[:top_n])
        
        # Find the concept object
        concept = self._find_concept(topic_name, subtopic_name, concept_name)
        
        # Get current performance
        concept_score = self.tracker.get_concept_performance(topic_name, subtopic_name, concept_name)
        
        # Calculate difficulty
        difficulty = FeedbackLoop.calculate_next_difficulty(concept_score)
        
        return topic_name, subtopic_name, concept, difficulty
    
    def _select_untried_concept(
        self,
        untried: list[tuple[str, str, str]],
        all_concepts: list[tuple[str, str, Concept]]
    ) -> Tuple[str, str, Concept, DifficultyLevel]:
        """Select an untried concept.
        
        Args:
            untried: List of untried concept identifiers
            all_concepts: All available concepts
            
        Returns:
            Tuple of (topic_name, subtopic_name, concept, difficulty)
        """
        # Pick a random untried concept
        topic_name, subtopic_name, concept_name = random.choice(untried)
        
        # Find the concept object
        concept = self._find_concept(topic_name, subtopic_name, concept_name)
        
        # Start with medium difficulty for new concepts
        return topic_name, subtopic_name, concept, DifficultyLevel.MEDIUM
    
    def _select_random_concept(
        self,
        all_concepts: list[tuple[str, str, Concept]]
    ) -> Tuple[str, str, Concept, DifficultyLevel]:
        """Select a random concept.
        
        Args:
            all_concepts: All available concepts
            
        Returns:
            Tuple of (topic_name, subtopic_name, concept, difficulty)
        """
        topic_name, subtopic_name, concept = random.choice(all_concepts)
        
        # Get current performance
        concept_score = self.tracker.get_concept_performance(topic_name, subtopic_name, concept.name)
        
        # Calculate difficulty
        difficulty = FeedbackLoop.calculate_next_difficulty(concept_score)
        
        return topic_name, subtopic_name, concept, difficulty
    
    def _find_concept(self, topic_name: str, subtopic_name: str, concept_name: str) -> Concept:
        """Find a concept object by name.
        
        Args:
            topic_name: Topic name
            subtopic_name: Subtopic name
            concept_name: Concept name
            
        Returns:
            Concept object
            
        Raises:
            ValueError: If concept not found
        """
        for topic in self.course.topics:
            if topic.name == topic_name:
                for subtopic in topic.subtopics:
                    if subtopic.name == subtopic_name:
                        for concept in subtopic.concepts:
                            if concept.name == concept_name:
                                return concept
        
        raise ValueError(f"Concept not found: {topic_name}/{subtopic_name}/{concept_name}")

