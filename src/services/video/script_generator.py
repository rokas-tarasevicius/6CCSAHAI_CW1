"""Video script generation using Mistral."""
from typing import Optional
from src.services.llm.mistral_client import MistralClient
from src.services.llm.prompts import VIDEO_SCRIPT_PROMPT
from src.models.course import Concept


class ScriptGenerator:
    """Generate video scripts using AI."""
    
    def __init__(self, mistral_client: Optional[MistralClient] = None):
        """Initialize script generator.
        
        Args:
            mistral_client: Optional MistralClient instance
        """
        self.client = mistral_client or MistralClient()
    
    def generate_script(
        self,
        topic: str,
        subtopic: str,
        concept: Concept
    ) -> str:
        """Generate a video script for a concept.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept object
            
        Returns:
            Generated script text
        """
        try:
            script = self.client.generate_with_template(
                VIDEO_SCRIPT_PROMPT,
                topic=topic,
                subtopic=subtopic,
                concept_name=concept.name,
                concept_description=concept.description
            )
            
            return script.strip()
            
        except Exception as e:
            # Fallback script
            return self._generate_fallback_script(topic, subtopic, concept)
    
    def _generate_fallback_script(
        self,
        topic: str,
        subtopic: str,
        concept: Concept
    ) -> str:
        """Generate a simple fallback script.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept object
            
        Returns:
            Fallback script text
        """
        return f"""
Hello! Today we're learning about {concept.name}.

{concept.description}

This concept is part of {subtopic}, which falls under the topic of {topic}.

Understanding {concept.name} is important because it helps you build a strong foundation in this subject.

Let's break it down step by step and make sure you understand it clearly.

Remember, practice makes perfect. Keep working on this concept and you'll master it in no time!
"""
    
    def estimate_duration(self, script: str, words_per_minute: int = 150) -> float:
        """Estimate video duration based on script.
        
        Args:
            script: Script text
            words_per_minute: Average speaking rate
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(script.split())
        minutes = word_count / words_per_minute
        return minutes * 60.0

