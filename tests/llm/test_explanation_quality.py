"""DeepEval tests for explanation quality."""
import pytest
from deepeval import assert_test
from deepeval.metrics import ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase
from src.services.llm.mistral_client import MistralClient
from src.services.llm.prompts import EXPLANATION_CHAT_PROMPT


@pytest.fixture
def mistral_client():
    """Create Mistral client for testing."""
    return MistralClient()


class TestExplanationRelevancy:
    """Test explanation relevancy using DeepEval."""
    
    @pytest.mark.skip(reason="Requires API calls - run manually")
    def test_explanation_maintains_context(self, mistral_client):
        """Test that AI explanation maintains context from question."""
        # Sample question context
        question_text = "What is a variable in Python?"
        correct_answer = "A container for storing data values"
        student_answer = "A container for storing data values"
        
        # Generate explanation response
        response = mistral_client.generate_with_template(
            EXPLANATION_CHAT_PROMPT,
            question_text=question_text,
            correct_answer=correct_answer,
            student_answer=student_answer,
            was_correct="True",
            topic="Python Basics",
            subtopic="Variables",
            concepts="Variables",
            explanation="Variables are containers that store data values.",
            student_question="Can you give me an example?"
        )
        
        # Create test case
        test_case = LLMTestCase(
            input="Can you give me an example?",
            actual_output=response,
            retrieval_context=[
                question_text,
                "Variables are containers that store data values."
            ]
        )
        
        # Test contextual relevancy
        metric = ContextualRelevancyMetric(threshold=0.7)
        assert_test(test_case, [metric])


class TestExplanationClarity:
    """Test explanation clarity and helpfulness."""
    
    def test_explanation_is_not_empty(self, mistral_client):
        """Test that explanations are not empty."""
        response = mistral_client.generate(
            "Explain what a variable is in one sentence.",
            system_message="You are a helpful tutor."
        )
        
        assert response, "Explanation should not be empty"
        assert len(response) > 20, "Explanation should be substantial"

