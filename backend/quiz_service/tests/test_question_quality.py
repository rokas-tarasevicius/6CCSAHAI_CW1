"""DeepEval tests for question generation quality."""
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from backend.quiz_service.services.question.generator import QuestionGenerator
from backend.shared.services.llm.mistral_client import MistralClient
from backend.course_service.models.course import Concept
from backend.quiz_service.models.question import DifficultyLevel


@pytest.fixture
def question_generator():
    """Create question generator for testing."""
    return QuestionGenerator()


@pytest.fixture
def sample_concept():
    """Create a sample concept for testing."""
    return Concept(
        name="Variables",
        description="Variables are containers for storing data values in Python. "
                   "They are created when you assign a value to them.",
        keywords=["assignment", "data", "storage", "naming"]
    )


class TestQuestionRelevancy:
    """Test question relevancy using DeepEval."""
    
    @pytest.mark.skip(reason="Requires API calls - run manually")
    def test_question_matches_concept(self, question_generator, sample_concept):
        """Test that generated question is relevant to the concept."""
        # Generate a question
        question = question_generator.generate_question(
            topic="Python Basics",
            subtopic="Variables and Data Types",
            concept=sample_concept,
            difficulty=DifficultyLevel.MEDIUM
        )
        
        # Create test case
        test_case = LLMTestCase(
            input=f"Generate a question about: {sample_concept.description}",
            actual_output=question.question_text,
            retrieval_context=[sample_concept.description]
        )
        
        # Test relevancy
        metric = AnswerRelevancyMetric(threshold=0.7)
        assert_test(test_case, [metric])
    
    @pytest.mark.skip(reason="Requires API calls - run manually")
    def test_explanation_is_faithful(self, question_generator, sample_concept):
        """Test that explanation is grounded in course material."""
        # Generate a question
        question = question_generator.generate_question(
            topic="Python Basics",
            subtopic="Variables and Data Types",
            concept=sample_concept,
            difficulty=DifficultyLevel.MEDIUM
        )
        
        # Create test case for explanation
        test_case = LLMTestCase(
            input=question.question_text,
            actual_output=question.explanation,
            retrieval_context=[sample_concept.description]
        )
        
        # Test faithfulness
        metric = FaithfulnessMetric(threshold=0.7)
        assert_test(test_case, [metric])


class TestQuestionStructure:
    """Test question structure and format."""
    
    def test_question_has_correct_answer(self, question_generator, sample_concept):
        """Test that generated question has exactly one correct answer."""
        question = question_generator.generate_question(
            topic="Python Basics",
            subtopic="Variables and Data Types",
            concept=sample_concept
        )
        
        correct_answers = [ans for ans in question.answers if ans.is_correct]
        assert len(correct_answers) == 1, "Question must have exactly one correct answer"
    
    def test_question_has_multiple_answers(self, question_generator, sample_concept):
        """Test that question has multiple answer options."""
        question = question_generator.generate_question(
            topic="Python Basics",
            subtopic="Variables and Data Types",
            concept=sample_concept
        )
        
        assert len(question.answers) >= 2, "Question must have at least 2 answers"
        assert len(question.answers) <= 6, "Question must have at most 6 answers"
    
    def test_question_has_text(self, question_generator, sample_concept):
        """Test that question has non-empty text."""
        question = question_generator.generate_question(
            topic="Python Basics",
            subtopic="Variables and Data Types",
            concept=sample_concept
        )
        
        assert question.question_text, "Question text must not be empty"
        assert len(question.question_text) > 10, "Question text must be substantial"

