"""Question generation service using Mistral."""
import random
from typing import Optional
from backend.quiz_service.models.question import MultipleChoiceQuestion, Answer, DifficultyLevel
from backend.course_service.models.course import Concept
from backend.shared.services.llm.mistral_client import MistralClient
from backend.shared.services.llm.prompts import QUESTION_GENERATION_PROMPT, CHOICE_GENERATION_PROMPT
from backend.shared.services.llm.mcq_prompts import KNOWLEDGE_LEVEL_MCQ_SYSTEM_INSTRUCTION, ANSWER_GENERATION_SYSTEM_INSTRUCTION
from backend.quiz_service.services.question.cache import get_cache
from backend.shared.utils.config import Config


class QuestionGenerator:
    """Generate questions using AI based on course material."""
    
    def __init__(self, mistral_client: Optional[MistralClient] = None):
        """Initialize question generator.
        
        Args:
            mistral_client: Optional MistralClient instance
        """
        # Use smaller max_tokens for faster question generation
        if mistral_client is None:
            from backend.shared.utils.config import Config
            self.client = MistralClient(max_tokens=Config.QUESTION_MAX_TOKENS)
        else:
            self.client = mistral_client
    
    def generate_question(
        self,
        topic: str,
        subtopic: str,
        concept: Concept,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        content_context: str = "",
        num_answers: int = 4,
        use_cache: bool = True
    ) -> MultipleChoiceQuestion:
        """Generate a multiple choice question for a specific concept.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept object
            difficulty: Question difficulty level
            content_context: Additional content context
            num_answers: Number of answer options (2-5)
            use_cache: Whether to use cached questions
            
        Returns:
            Generated MultipleChoiceQuestion
        """
        # Check cache first
        if use_cache:
            cache = get_cache()
            cached_question = cache.get(topic, subtopic, concept.name, difficulty)
            if cached_question:
                return cached_question
        
        num_answers = max(Config.MIN_ANSWERS, min(Config.MAX_ANSWERS, num_answers))
        
        # Prepare the prompt
        common_prompt_vars = {
            "topic": topic,
            "subtopic": subtopic,
            "concept_name": concept.name,
            "concept_description": concept.description,
            "content_context": f"Additional context: {content_context}" if content_context else "",
            "difficulty": difficulty.value,
        }
        question_prompt_vars = {
            "system_instruction": KNOWLEDGE_LEVEL_MCQ_SYSTEM_INSTRUCTION,
            **common_prompt_vars
        }
        choice_prompt_vars = {
            "system_instruction": ANSWER_GENERATION_SYSTEM_INSTRUCTION,
            **common_prompt_vars,
        }
        
        # Generate question using LLM
        try:
            question_response = self.client.generate_with_template(
                QUESTION_GENERATION_PROMPT,
                **question_prompt_vars
            )

            print(f"Raw question response: {question_response}")

            # Parse the response as JSON
            import json
            # Try to extract JSON from the response
            if "```json" in question_response:
                start = question_response.find("```json") + 7
                end = question_response.find("```", start)
                json_str = question_response[start:end].strip()
                question_data = json.loads(json_str)
            elif "{" in question_response:
                # Find the JSON object in the response
                start = question_response.find("{")
                end = question_response.rfind("}") + 1
                json_str = question_response[start:end]
                question_data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            print(f"Generated question data: {question_data}")

            choices_response = self.client.generate_with_template(
                CHOICE_GENERATION_PROMPT,
                question=question_data["question"],
                **choice_prompt_vars,
            )
            print(f"Raw choices response: {choices_response}")
            # Parse choices response
            if "```json" in choices_response:
                start = choices_response.find("```json") + 7
                end = choices_response.find("```", start)
                json_str = choices_response[start:end].strip()
                choices_data = json.loads(json_str)
            elif "{" in choices_response:
                start = choices_response.find("{")
                end = choices_response.rfind("}") + 1
                json_str = choices_response[start:end]
                choices_data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in choices response")
            
            print(f"Generated choices data: {choices_data}")

            
            # Validate and create question
            answers = [Answer(**ans) for ans in choices_data["answers"]]
            
            # Ensure at least one correct answer
            if not any(ans.is_correct for ans in answers):
                answers[0].is_correct = True # TODO: Set first answer as correct arbitrarily (NEEDS BETTER HANDLING)
            
            # Ensure only one correct answer TODO: Sets first correct answer as correct, others as false (NEEDS BETTER HANDLING)
            correct_count = sum(1 for ans in answers if ans.is_correct)
            if correct_count > 1:
                first_correct_found = False
                for ans in answers:
                    if ans.is_correct and not first_correct_found:
                        first_correct_found = True
                    elif ans.is_correct:
                        ans.is_correct = False
            
            question = MultipleChoiceQuestion(
                question_text=question_data["question"],
                answers=answers,
                topic=topic,
                subtopic=subtopic,
                concepts=[concept.name],
                difficulty=difficulty,
                explanation="", # question_data.get("explanation", "")
            )
            
            # Validate the generated question
            from backend.quiz_service.services.question.validator import QuestionValidator
            is_valid, validation_errors = QuestionValidator.validate(question)
            
            if not is_valid:
                # If validation fails, log and use fallback
                print(f"Generated question failed validation: {validation_errors}")
                return self._generate_fallback_question(topic, subtopic, concept, difficulty)
            
            # Cache the question
            if use_cache:
                cache = get_cache()
                cache.set(topic, subtopic, concept.name, difficulty, question)
            
            return question
            
        except Exception as e:
            # Fallback: generate a simple question
            # Log error but don't fail - use fallback
            print(f"Question generation error: {e}, using fallback")
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
            Simple MultipleChoiceQuestion with concrete, factual answers
        """
        question_text = f"Which of the following best describes {concept.name}?"
        
        # Create concrete, factual alternatives based on common programming concepts
        # These are better than generic placeholders - they're actual concepts students might confuse
        alternatives = [
            "A data structure used for storing collections of items",
            "A control structure that executes code conditionally",
            "A function that performs mathematical operations",
            "A variable that holds multiple values",
            "A loop that repeats code a specific number of times",
            "A method for organizing related code together",
            "A type of error handling mechanism",
            "A way to import external libraries"
        ]
        
        # Select 3 random alternatives that are different from the concept description
        selected_alternatives = []
        for alt in alternatives:
            if alt.lower() != concept.description.lower()[:50]:  # Avoid duplicates
                selected_alternatives.append(alt)
                if len(selected_alternatives) >= 3:
                    break
        
        # Ensure we have enough alternatives
        while len(selected_alternatives) < 3:
            selected_alternatives.append(f"A programming concept related to {subtopic.lower()}")
        
        answers = [
            Answer(text=concept.description, is_correct=True),
        ]
        
        # Add concrete alternatives
        for alt in selected_alternatives[:3]:
            answers.append(Answer(text=alt, is_correct=False))
        
        # Shuffle answers
        random.shuffle(answers)
        
        return MultipleChoiceQuestion(
            question_text=question_text,
            answers=answers[:4],
            topic=topic,
            subtopic=subtopic,
            concepts=[concept.name],
            difficulty=difficulty,
            explanation=f"{concept.name}: {concept.description}"
        )

