"""Chat widget for AI follow-up questions."""
import streamlit as st
from typing import List, Dict
from src.services.llm.mistral_client import MistralClient
from src.services.llm.prompts import EXPLANATION_CHAT_PROMPT
from src.models.question import MultipleChoiceQuestion


def render_chat_widget(
    question: MultipleChoiceQuestion,
    selected_answer: str,
    is_correct: bool,
    client: MistralClient,
    key_prefix: str = "chat"
) -> None:
    """Render interactive chat widget for follow-up questions.
    
    Args:
        question: The question that was answered
        selected_answer: The answer the user selected
        is_correct: Whether the answer was correct
        client: Mistral client for generating responses
        key_prefix: Prefix for Streamlit widget keys
    """
    st.markdown("#### Ask a Follow-up Question")
    
    # Initialize chat history in session state
    chat_key = f"{key_prefix}_history"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    
    # Display chat history
    for msg in st.session_state[chat_key]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**AI Tutor:** {msg['content']}")
    
    # Chat input
    user_question = st.text_input(
        "Your question:",
        key=f"{key_prefix}_input",
        placeholder="Ask anything about this concept..."
    )
    
    if st.button("Send", key=f"{key_prefix}_send"):
        if user_question:
            # Add user message to history
            st.session_state[chat_key].append({
                "role": "user",
                "content": user_question
            })
            
            # Generate AI response
            try:
                correct_answer = question.get_correct_answer()
                
                response = client.generate_with_template(
                    EXPLANATION_CHAT_PROMPT,
                    question_text=question.question_text,
                    correct_answer=correct_answer.text if correct_answer else "N/A",
                    student_answer=selected_answer,
                    was_correct=str(is_correct),
                    topic=question.topic,
                    subtopic=question.subtopic,
                    concepts=", ".join(question.concepts),
                    explanation=question.explanation,
                    student_question=user_question
                )
                
                # Add AI response to history
                st.session_state[chat_key].append({
                    "role": "assistant",
                    "content": response
                })
                
                # Rerun to show new messages
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")


def clear_chat_history(key_prefix: str = "chat") -> None:
    """Clear chat history.
    
    Args:
        key_prefix: Prefix for chat widget keys
    """
    chat_key = f"{key_prefix}_history"
    if chat_key in st.session_state:
        st.session_state[chat_key] = []

