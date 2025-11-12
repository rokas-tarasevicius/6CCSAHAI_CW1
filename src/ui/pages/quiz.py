"""Quiz page with adaptive questions."""
import streamlit as st
from src.models.user_state import UserPerformance
from src.services.tracking.performance_tracker import PerformanceTracker
from src.services.question.generator import QuestionGenerator
from src.services.question.adapter import QuestionAdapter
from src.services.llm.mistral_client import MistralClient
from src.utils.course_loader import CourseLoader
from src.ui.components.question_card import render_question_card, render_question_result
from src.ui.components.progress_display import render_compact_stats
from src.ui.components.chat_widget import render_chat_widget, clear_chat_history


def initialize_quiz_state():
    """Initialize quiz-related session state."""
    if not st.session_state.get("initialized", False):
        st.session_state.performance = UserPerformance()
        st.session_state.tracker = PerformanceTracker(st.session_state.performance)
        st.session_state.initialized = True
    
    if "course" not in st.session_state:
        # Load course material
        try:
            st.session_state.course = CourseLoader.load_from_file("data/course_material.json")
        except:
            # Fallback to sample course
            st.session_state.course = CourseLoader.create_sample_course()
    
    if "mistral_client" not in st.session_state:
        st.session_state.mistral_client = MistralClient()
    
    if "question_generator" not in st.session_state:
        st.session_state.question_generator = QuestionGenerator(st.session_state.mistral_client)
    
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    
    if "question_answered" not in st.session_state:
        st.session_state.question_answered = False
    
    if "selected_answer_index" not in st.session_state:
        st.session_state.selected_answer_index = -1


def generate_new_question():
    """Generate a new question based on performance."""
    adapter = QuestionAdapter(st.session_state.course, st.session_state.tracker)
    topic, subtopic, concept, difficulty = adapter.select_next_concept()
    
    # Get content context
    content_context = ""
    for t in st.session_state.course.topics:
        if t.name == topic:
            for st_obj in t.subtopics:
                if st_obj.name == subtopic:
                    content_context = st_obj.content or ""
                    break
    
    question = st.session_state.question_generator.generate_question(
        topic=topic,
        subtopic=subtopic,
        concept=concept,
        difficulty=difficulty,
        content_context=content_context
    )
    
    st.session_state.current_question = question
    st.session_state.question_answered = False
    st.session_state.selected_answer_index = -1
    clear_chat_history("quiz_chat")


def render_quiz_page():
    """Render the quiz page."""
    initialize_quiz_state()
    
    st.title("📝 Adaptive Quiz")
    
    # Show compact stats
    render_compact_stats(st.session_state.performance)
    
    st.markdown("---")
    
    # Generate initial question if needed
    if st.session_state.current_question is None:
        with st.spinner("Generating your first question..."):
            generate_new_question()
    
    question = st.session_state.current_question
    
    if question is None:
        st.error("Failed to generate question. Please try again.")
        if st.button("Retry"):
            st.rerun()
        return
    
    # Display question
    if not st.session_state.question_answered:
        selected = render_question_card(question, key_prefix="quiz")
        
        if st.button("Submit Answer", type="primary"):
            st.session_state.selected_answer_index = selected
            st.session_state.question_answered = True
            
            # Record answer
            correct_index = question.get_correct_answer_index()
            is_correct = selected == correct_index
            
            # Update performance
            for concept_name in question.concepts:
                st.session_state.tracker.record_answer(
                    topic=question.topic,
                    subtopic=question.subtopic,
                    concept=concept_name,
                    is_correct=is_correct
                )
            
            st.rerun()
    
    else:
        # Show result
        render_question_result(
            question,
            st.session_state.selected_answer_index,
            show_explanation=True
        )
        
        st.markdown("---")
        
        # Chat widget for follow-up questions
        selected_answer_text = question.answers[st.session_state.selected_answer_index].text
        is_correct = st.session_state.selected_answer_index == question.get_correct_answer_index()
        
        render_chat_widget(
            question=question,
            selected_answer=selected_answer_text,
            is_correct=is_correct,
            client=st.session_state.mistral_client,
            key_prefix="quiz_chat"
        )
        
        st.markdown("---")
        
        # Next question button
        if st.button("Next Question", type="primary"):
            with st.spinner("Generating next question..."):
                generate_new_question()
            st.rerun()


# Run the page
if __name__ == "__main__":
    render_quiz_page()

