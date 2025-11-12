"""Question card component for displaying questions."""
import streamlit as st
from src.models.question import MultipleChoiceQuestion


def render_question_card(question: MultipleChoiceQuestion, key_prefix: str = "q") -> int:
    """Render a question card with answer options.
    
    Args:
        question: Question to display
        key_prefix: Prefix for Streamlit widget keys
        
    Returns:
        Selected answer index (or -1 if not answered)
    """
    st.markdown(f"### {question.question_text}")
    
    # Show metadata
    with st.expander("Question Info"):
        st.write(f"**Topic:** {question.topic}")
        st.write(f"**Subtopic:** {question.subtopic}")
        st.write(f"**Difficulty:** {question.difficulty.value.title()}")
        if question.concepts:
            st.write(f"**Concepts:** {', '.join(question.concepts)}")
    
    # Display answer options as radio buttons
    answer_texts = [ans.text for ans in question.answers]
    
    selected = st.radio(
        "Select your answer:",
        options=range(len(answer_texts)),
        format_func=lambda i: answer_texts[i],
        key=f"{key_prefix}_answer"
    )
    
    return selected


def render_question_result(
    question: MultipleChoiceQuestion,
    selected_index: int,
    show_explanation: bool = True
) -> None:
    """Render the result of an answered question.
    
    Args:
        question: The question
        selected_index: Index of selected answer
        show_explanation: Whether to show explanation
    """
    correct_index = question.get_correct_answer_index()
    is_correct = selected_index == correct_index
    
    # Show result
    if is_correct:
        st.success("✅ Correct!")
    else:
        st.error("❌ Incorrect")
        st.info(f"The correct answer was: {question.answers[correct_index].text}")
    
    # Show explanation
    if show_explanation and question.explanation:
        st.markdown("#### Explanation")
        st.write(question.explanation)

