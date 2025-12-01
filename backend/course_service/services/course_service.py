"""Course service helper functions."""
from typing import List, Dict, Any
import json
from backend.quiz_service.services.question.generator import QuestionGenerator
from backend.shared.services.llm.mistral_client import MistralClient
from backend.course_service.models.course import Concept
from backend.quiz_service.models.question import DifficultyLevel
from backend.shared.services.llm.pdf_summary import PDF_SUMMARY_SYSTEM_INSTRUCTION


async def generate_quiz_for_file(
    file_name: str, 
    content: str, 
    summary: str, 
    num_questions: int = 5
) -> List[Dict[str, Any]]:
    """Generate a quiz for a specific file content.
    
    Args:
        file_name: Name of the file
        content: The text content of the file
        summary: A summary of the contents of the file
        num_questions: The number of questions to generate
        
    Returns:
        List of generated questions
    """
    try:
        # Initialize question generator
        mistral_client = MistralClient()
        generator = QuestionGenerator(mistral_client)
        
        # Create a concept from the file content
        topic_name = file_name.replace('.pdf', '').replace('_', ' ').title()
        
        # Use first 5000 chars for concept creation to avoid token limits
        content_preview = content[:5000] if len(content) > 5000 else content
        
        concept = Concept(
            name=topic_name,  # TODO: Need to generate concept name
            description=f"Key concepts from {file_name}",
            keywords=[]
        )

        difficulties = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]

        from backend.quiz_service.models.question import MultipleChoiceQuestion
        print(f"Start generating questions")
        questions: List[MultipleChoiceQuestion] = generator.generate_questions(
            topic=topic_name,  # Need to generate topic name
            subtopic="Main Content",  # TODO: Need to generate subtopic
            concept=concept,
            difficulty=difficulties[0],
            content_context=content_preview,
            num_answers=4
        )

        formatted_questions: List[Dict[str, Any]] = []
        for question in questions:
            # Convert to dict format for JSON storage
            question_dict = {
                "question_text": question.question_text,
                "answers": [
                    {
                        "text": answer.text,
                        "is_correct": answer.is_correct,
                        "explanation": answer.explanation
                    }
                    for answer in question.answers
                ],
                "topic": question.topic,
                "subtopic": question.subtopic,
                "concepts": question.concepts,
                "difficulty": question.difficulty.value,
                "explanation": question.explanation
            }
            
            formatted_questions.append(question_dict)
            
        return formatted_questions
        
    except Exception as e:
        print(f"Error generating quiz for {file_name}: {str(e)}")
        # Return empty quiz if generation fails
        return []


async def generate_pdf_summary_for_file(
    file_name: str, 
    prompt_data: Dict[str, Any]
) -> str:
    """Generate a summary for a specific PDF file content.
    
    Args:
        file_name: Name of the file
        prompt_data: File content and metadata
        
    Returns:
        Generated summary string
    """
    try:
        mistral_client = MistralClient()
        
        response = mistral_client.generate(
            prompt=json.dumps(prompt_data, indent=4),
            system_message=PDF_SUMMARY_SYSTEM_INSTRUCTION
        )
        print(f"Generated summary for {file_name}: {response.strip()}")
        
        return response.strip()
    except Exception as e:
        print(f"Error generating summary for {file_name}: {str(e)}")
        return "No summary available."

