"""Question generation service using Mistral."""
import random
import json
import re
from typing import Optional, List, Dict, Any
from backend.quiz_service.models.question import MultipleChoiceQuestion, Answer, DifficultyLevel
from backend.course_service.models.course import Concept
from backend.shared.services.llm.mistral_client import MistralClient
from backend.shared.services.llm.prompts import (
    QUESTION_GENERATION_PROMPT,
    COURSE_RELEVANCE_PROMPT,
    CHOICE_GENERATION_PROMPT
)
from backend.shared.services.llm.mcq_prompts import (
    KNOWLEDGE_LEVEL_MCQ_SYSTEM_INSTRUCTION,
    COURSE_RELEVANCE_SYSTEM_INSTRUCTION,
    ANSWER_GENERATION_SYSTEM_INSTRUCTION,
)
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

    def _parse_json_response(self, response:str) -> List[Dict[Any, Any]]:
        """
        Tries to parse a JSON response from the LLM output.

        - The expected input should be a list of dictionaries in JSON format.
        E.g., 
        [
            {"question": "What is ...?", "answers": [...]},
            {"question": "How does ...?", "answers": [...]}
        ]

        Or any arbitrary list of JSON objects.

        Args:
            response (str): Response from LLM.

        Returns:
            List[Dict[Any, Any]]: Parsed list of dictionaries.
        """
        # Parse the response as JSON
        json_match = re.search(r"\[.*\]|\{.*\}", response, re.DOTALL) # List of JSON objects
        if not json_match:
            raise ValueError("No JSON found in response")

        json_str = json_match.group(0)
        parsed_data = json.loads(json_str)

        if isinstance(parsed_data, dict): # Single question object
            parsed_data = [parsed_data]
        return parsed_data
    
    def _generate_llm_response_json(self, prompt_vars:Dict[str, Any], prompt_template:str) -> List[Dict[str, Any]]:
        """
        Generates a JSON response from the LLM based on the provided prompt template and variables.

        Args:
            prompt_vars (Dict[str, Any]): Variables to fill in the prompt template.
            prompt_template (str): The prompt template to use.
        Returns:
            List[Dict[str, Any]]: Parsed JSON response from the LLM.
        """
        response = self.client.generate_with_template(
            prompt_template,
            **prompt_vars
        )
        data = self._parse_json_response(response=response)
        return data
    
    def generate_questions(
        self,
        topic: str,
        subtopic: str,
        concept: Concept,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        content_context: str = "",
        num_answers: int = 4,
    ) -> list[MultipleChoiceQuestion]:
        """Generates 1 or more multiple choice question for a specific concept.
        
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
        common_prompt_vars = {
            "topic": topic,
            "subtopic": subtopic,
            "concept_name": concept.name,
            "concept_description": concept.description, # Is a summary 
            "content_context": f"Additional context: {content_context}" if content_context else "",
            "difficulty": difficulty.value,
        }
        question_prompt_vars = {
            "system_instruction": KNOWLEDGE_LEVEL_MCQ_SYSTEM_INSTRUCTION,
            **common_prompt_vars
        }
        question_course_relevance_prompt_vars = {
            "system_instruction": COURSE_RELEVANCE_SYSTEM_INSTRUCTION,
            **common_prompt_vars
        }
        choice_prompt_vars = {
            "system_instruction": ANSWER_GENERATION_SYSTEM_INSTRUCTION,
            **common_prompt_vars,
        }
        
        # Generate question using LLM
        try:
            question_data = self._generate_llm_response_json(
                prompt_vars=question_prompt_vars,
                prompt_template=QUESTION_GENERATION_PROMPT
            )

            print(f"Generated question data: {json.dumps(question_data, indent=4)}")

            # Check these questions for course relevance, it 
            question_course_relevance_prompt_vars["generated_questions"] = json.dumps(question_data)
            relevance_data = self._generate_llm_response_json(
                prompt_vars=question_course_relevance_prompt_vars,
                prompt_template=COURSE_RELEVANCE_PROMPT
            )
            print(f"Relevance data: {json.dumps(relevance_data, indent=4)}")

            # Filter out question stems that are not relevant to the course.
            try:
                relevant_questions = [
                    q for q, r in zip(question_data, relevance_data)
                    if r["is_relevant"]
                ]
                question_data = relevant_questions # Re-assign to only relevant questions
            except Exception as e:
                print(f"Error filtering relevant questions: {e}, proceeding with all questions")
                raise e

            # Generate answer choices for each question stem.
            choices = []

            for idx in range(len(question_data)):
                choices_data = self._generate_llm_response_json(
                    prompt_vars={
                        "question": question_data[idx]["question"],
                        **choice_prompt_vars,
                    },
                    prompt_template=CHOICE_GENERATION_PROMPT
                )
                
                
                choices_data = choices_data[0] # Extract the first element which contains the answers list (to convert back to a list of dicts/JSON objects)
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

                choices.append(answers)

            # Convert to List of MultipleChoiceQuestion
            multiple_choice_questions = []
            for i, (answers, question_dict) in enumerate(zip(choices, question_data)):
                print("Question dict:", question_dict)
                question = MultipleChoiceQuestion(
                    question_text=question_dict["question"],
                    answers=answers,
                    topic=topic,
                    subtopic=subtopic,
                    concepts=[concept.name],
                    difficulty=difficulty,
                    explanation="", # question_dict.get("explanation", "")
                )
                
                # Validate the generated question
                from backend.quiz_service.services.question.validator import QuestionValidator
                is_valid, validation_errors = QuestionValidator.validate(question)
                
                if not is_valid:
                    # If validation fails, skip this question
                    print(f"Generated question failed validation: {validation_errors}")
                    continue
                
                multiple_choice_questions.append(question)
            
            print(f"Generated {len(multiple_choice_questions)} questions for concept '{concept.name}'")
            return multiple_choice_questions
            
        except Exception as e:
            # Fallback: Return nothing
            print(f"Question generation error: {e}, returning empty list")
            return []