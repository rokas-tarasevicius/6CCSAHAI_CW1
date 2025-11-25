"""Question caching for faster generation."""
from typing import Optional, Dict
from functools import lru_cache
from backend.quiz_service.models.question import MultipleChoiceQuestion
from backend.quiz_service.models.question import DifficultyLevel
import hashlib
import json


class QuestionCache:
    """Cache for generated questions to avoid regenerating."""
    
    def __init__(self, max_size: int = 50):
        """Initialize cache.
        
        Args:
            max_size: Maximum number of questions to cache
        """
        self.cache: Dict[str, MultipleChoiceQuestion] = {}
        self.max_size = max_size
    
    def _generate_key(
        self,
        topic: str,
        subtopic: str,
        concept_name: str,
        difficulty: DifficultyLevel
    ) -> str:
        """Generate cache key from question parameters.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept_name: Concept name
            difficulty: Difficulty level
            
        Returns:
            Cache key string
        """
        key_data = {
            "topic": topic,
            "subtopic": subtopic,
            "concept": concept_name,
            "difficulty": difficulty.value
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(
        self,
        topic: str,
        subtopic: str,
        concept_name: str,
        difficulty: DifficultyLevel
    ) -> Optional[MultipleChoiceQuestion]:
        """Get cached question if available.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept_name: Concept name
            difficulty: Difficulty level
            
        Returns:
            Cached question or None
        """
        key = self._generate_key(topic, subtopic, concept_name, difficulty)
        return self.cache.get(key)
    
    def set(
        self,
        topic: str,
        subtopic: str,
        concept_name: str,
        difficulty: DifficultyLevel,
        question: MultipleChoiceQuestion
    ):
        """Cache a question.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept_name: Concept name
            difficulty: Difficulty level
            question: Question to cache
        """
        key = self._generate_key(topic, subtopic, concept_name, difficulty)
        
        # Remove oldest entry if cache is full
        if len(self.cache) >= self.max_size:
            # Remove first item (FIFO)
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        self.cache[key] = question
    
    def clear(self):
        """Clear all cached questions."""
        self.cache.clear()


# Global cache instance
_question_cache = QuestionCache(max_size=50)


def get_cache() -> QuestionCache:
    """Get the global question cache instance.
    
    Returns:
        QuestionCache instance
    """
    return _question_cache

