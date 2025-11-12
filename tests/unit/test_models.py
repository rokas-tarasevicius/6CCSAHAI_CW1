"""Unit tests for data models."""
import pytest
from datetime import datetime
from src.models.course import Concept, Subtopic, Topic, CourseStructure
from src.models.question import Answer, MultipleChoiceQuestion, DifficultyLevel
from src.models.user_state import ConceptScore, SubtopicScore, TopicScore, UserPerformance


class TestCourseModels:
    """Test course-related models."""
    
    def test_concept_creation(self):
        """Test creating a concept."""
        concept = Concept(
            name="Variables",
            description="Variables store data",
            keywords=["storage", "data"]
        )
        assert concept.name == "Variables"
        assert len(concept.keywords) == 2
    
    def test_course_get_all_concepts(self):
        """Test getting all concepts from course."""
        course = CourseStructure(
            title="Test Course",
            description="Test",
            topics=[
                Topic(
                    name="Topic1",
                    description="Test topic",
                    subtopics=[
                        Subtopic(
                            name="Subtopic1",
                            description="Test subtopic",
                            concepts=[
                                Concept(name="Concept1", description="Test", keywords=[]),
                                Concept(name="Concept2", description="Test", keywords=[])
                            ]
                        )
                    ]
                )
            ]
        )
        
        all_concepts = course.get_all_concepts()
        assert len(all_concepts) == 2


class TestQuestionModels:
    """Test question-related models."""
    
    def test_multiple_choice_question(self):
        """Test creating a multiple choice question."""
        question = MultipleChoiceQuestion(
            question_text="What is Python?",
            answers=[
                Answer(text="A programming language", is_correct=True),
                Answer(text="A snake", is_correct=False),
                Answer(text="A framework", is_correct=False)
            ],
            topic="Python Basics",
            subtopic="Introduction",
            difficulty=DifficultyLevel.EASY
        )
        
        assert len(question.answers) == 3
        assert question.get_correct_answer_index() == 0
        assert question.get_correct_answer().text == "A programming language"
    
    def test_no_correct_answer(self):
        """Test question with no correct answer."""
        question = MultipleChoiceQuestion(
            question_text="Test?",
            answers=[
                Answer(text="A", is_correct=False),
                Answer(text="B", is_correct=False)
            ],
            topic="Test",
            subtopic="Test"
        )
        
        assert question.get_correct_answer_index() == -1
        assert question.get_correct_answer() is None


class TestUserStateModels:
    """Test user state models."""
    
    def test_concept_score_accuracy(self):
        """Test concept score accuracy calculation."""
        score = ConceptScore(
            concept_name="Variables",
            attempts=10,
            correct=7,
            incorrect=3
        )
        
        assert score.accuracy == 70.0
        assert not score.is_weak
    
    def test_weak_concept_detection(self):
        """Test weak concept detection."""
        score = ConceptScore(
            concept_name="Loops",
            attempts=5,
            correct=2,
            incorrect=3
        )
        
        assert score.accuracy == 40.0
        assert score.is_weak
    
    def test_user_performance_overall_accuracy(self):
        """Test overall accuracy calculation."""
        performance = UserPerformance(
            total_questions_answered=20,
            total_correct=15,
            total_incorrect=5
        )
        
        assert performance.overall_accuracy == 75.0
    
    def test_user_performance_get_weak_concepts(self):
        """Test getting weak concepts from performance."""
        performance = UserPerformance()
        performance.topic_scores["Python"] = TopicScore(topic_name="Python")
        performance.topic_scores["Python"].subtopic_scores["Variables"] = SubtopicScore(
            subtopic_name="Variables"
        )
        performance.topic_scores["Python"].subtopic_scores["Variables"].concept_scores["Assignment"] = ConceptScore(
            concept_name="Assignment",
            attempts=5,
            correct=2,
            incorrect=3
        )
        
        weak_concepts = performance.get_all_weak_concepts()
        assert len(weak_concepts) == 1
        assert weak_concepts[0] == ("Python", "Variables", "Assignment")

