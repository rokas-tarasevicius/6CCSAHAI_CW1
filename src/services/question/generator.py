"""Question generation service using Mistral."""
import random
from typing import Optional
from src.models.question import MultipleChoiceQuestion, Answer, DifficultyLevel
from src.models.course import Concept
from src.services.llm.mistral_client import MistralClient
from src.services.llm.prompts import QUESTION_GENERATION_PROMPT
from src.utils.config import Config


class QuestionGenerator:
    """Generate questions using AI based on course material."""
    
    def __init__(self, mistral_client: Optional[MistralClient] = None):
        """Initialize question generator.
        
        Args:
            mistral_client: Optional MistralClient instance
        """
        self.client = mistral_client or MistralClient()
    
    def generate_question(
        self,
        topic: str,
        subtopic: str,
        concept: Concept,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        content_context: str = "",
        num_answers: int = 4
    ) -> MultipleChoiceQuestion:
        """Generate a multiple choice question for a specific concept.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept object
            difficulty: Question difficulty level
            content_context: Additional content context
            num_answers: Number of answer options (2-5)
            
        Returns:
            Generated MultipleChoiceQuestion
        """
        num_answers = max(Config.MIN_ANSWERS, min(Config.MAX_ANSWERS, num_answers))
        
        # Prepare the prompt
        prompt_vars = {
            "topic": topic,
            "subtopic": subtopic,
            "concept_name": concept.name,
            "concept_description": concept.description,
            "content_context": f"Additional context: {content_context}" if content_context else "",
            "difficulty": difficulty.value,
            "num_answers": num_answers
        }
        
        # Generate question using LLM
        try:
            response = self.client.generate_with_template(
                QUESTION_GENERATION_PROMPT,
                **prompt_vars
            )
            
            # Parse the response as JSON
            import json
            # Try to extract JSON from the response
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
                question_data = json.loads(json_str)
            elif "{" in response:
                # Find the JSON object in the response
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                question_data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            # Validate and create question
            answers = [Answer(**ans) for ans in question_data["answers"]]
            
            # Ensure at least one correct answer
            if not any(ans.is_correct for ans in answers):
                answers[0].is_correct = True
            
            # Ensure only one correct answer
            correct_count = sum(1 for ans in answers if ans.is_correct)
            if correct_count > 1:
                first_correct_found = False
                for ans in answers:
                    if ans.is_correct and not first_correct_found:
                        first_correct_found = True
                    elif ans.is_correct:
                        ans.is_correct = False
            
            question = MultipleChoiceQuestion(
                question_text=question_data["question_text"],
                answers=answers,
                topic=topic,
                subtopic=subtopic,
                concepts=[concept.name],
                difficulty=difficulty,
                explanation=question_data.get("explanation", "")
            )
            
            return question
            
        except Exception as e:
            # Fallback: generate a simple question
            return self._generate_fallback_question(topic, subtopic, concept, difficulty)
    
    def _generate_fallback_question(
        self,
        topic: str,
        subtopic: str,
        concept: Concept,
        difficulty: DifficultyLevel
    ) -> MultipleChoiceQuestion:
        """Generate a fallback question if AI generation fails.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept object
            difficulty: Difficulty level
            
        Returns:
            Simple MultipleChoiceQuestion
        """
        question_text = f"Which of the following best describes {concept.name}?"
        
        answers = [
            Answer(text=concept.description, is_correct=True),
            Answer(text="This is not the correct definition", is_correct=False),
            Answer(text="This is an unrelated concept", is_correct=False),
            Answer(text="None of the above", is_correct=False)
        ]
        
        # Shuffle answers
        random.shuffle(answers)
        
        return MultipleChoiceQuestion(
            question_text=question_text,
            answers=answers,
            topic=topic,
            subtopic=subtopic,
            concepts=[concept.name],
            difficulty=difficulty,
            explanation=f"{concept.name}: {concept.description}"
        )

