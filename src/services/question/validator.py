"""Question validation utilities."""
from src.models.question import MultipleChoiceQuestion


class QuestionValidator:
    """Validate generated questions for quality and format."""
    
    @staticmethod
    def validate(question: MultipleChoiceQuestion) -> tuple[bool, list[str]]:
        """Validate a question.
        
        Args:
            question: Question to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check question text
        if not question.question_text or len(question.question_text.strip()) < 10:
            errors.append("Question text is too short or empty")
        
        # Check answers
        if len(question.answers) < 2:
            errors.append("Must have at least 2 answers")
        
        if len(question.answers) > 6:
            errors.append("Too many answers (max 6)")
        
        # Check for correct answer
        correct_answers = [ans for ans in question.answers if ans.is_correct]
        if len(correct_answers) == 0:
            errors.append("No correct answer specified")
        elif len(correct_answers) > 1:
            errors.append("Multiple correct answers specified (only one allowed)")
        
        # Check answer text
        for idx, answer in enumerate(question.answers):
            if not answer.text or len(answer.text.strip()) < 1:
                errors.append(f"Answer {idx + 1} is empty")
        
        # Check for duplicate answers
        answer_texts = [ans.text.lower().strip() for ans in question.answers]
        if len(answer_texts) != len(set(answer_texts)):
            errors.append("Duplicate answers found")
        
        # Check for generic/opinion-based answers that cannot be objectively evaluated
        forbidden_patterns = [
            "this is not the correct",
            "this is an unrelated",
            "none of the above",
            "all of the above",
            "cannot be determined",
            "depends on",
            "this is incorrect",
            "this is wrong",
            "not applicable"
        ]
        
        for idx, answer in enumerate(question.answers):
            answer_lower = answer.text.lower().strip()
            for pattern in forbidden_patterns:
                if pattern in answer_lower:
                    errors.append(
                        f"Answer {idx + 1} contains generic/opinion-based text: '{answer.text}'. "
                        "All answers must be concrete, factual statements."
                    )
                    break
        
        # Check that answers are substantial (not just placeholders)
        for idx, answer in enumerate(question.answers):
            if len(answer.text.strip()) < 10:
                errors.append(f"Answer {idx + 1} is too short to be meaningful")
        
        # Check metadata
        if not question.topic:
            errors.append("Topic not specified")
        
        if not question.subtopic:
            errors.append("Subtopic not specified")
        
        return len(errors) == 0, errors

