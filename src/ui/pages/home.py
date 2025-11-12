"""Home page with dashboard and progress."""
import streamlit as st
from src.ui.components.progress_display import render_progress_header, render_detailed_progress


def render_home_page():
    """Render the home/dashboard page."""
    # Initialize session state if needed
    if not st.session_state.get("initialized", False):
        from src.models.user_state import UserPerformance
        from src.services.tracking.performance_tracker import PerformanceTracker
        
        st.session_state.performance = UserPerformance()
        st.session_state.tracker = PerformanceTracker(st.session_state.performance)
        st.session_state.initialized = True
    
    st.title("🎓 Adaptive Learning Platform")
    
    # Show progress header
    render_progress_header(st.session_state.performance)
    
    st.markdown("---")
    
    # Welcome message
    if st.session_state.performance.total_questions_answered == 0:
        st.markdown("""
        ### Welcome to the Adaptive Learning Platform!
        
        This platform uses AI to create personalized questions based on your performance.
        
        **Features:**
        - 🎯 Adaptive questions that match your skill level
        - 📊 Real-time performance tracking
        - 💬 AI tutor for follow-up questions
        - 🎥 Personalized video content
        
        **Get Started:**
        1. Go to the **Quiz** page to start answering questions
        2. Track your progress here on the home page
        3. Watch personalized videos on the **Video Feed** page
        
        Good luck! 🚀
        """)
    else:
        # Show detailed progress
        render_detailed_progress(st.session_state.performance)
    
    st.markdown("---")
    
    # Quick action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Start Quiz", use_container_width=True):
            st.switch_page("pages/quiz.py")
    
    with col2:
        if st.button("🎥 Video Feed", use_container_width=True):
            st.switch_page("pages/video_feed.py")
    
    with col3:
        if st.button("🔄 Reset Progress", use_container_width=True):
            if st.session_state.get("confirm_reset"):
                from src.models.user_state import UserPerformance
                from src.services.tracking.performance_tracker import PerformanceTracker
                
                st.session_state.performance = UserPerformance()
                st.session_state.tracker = PerformanceTracker(st.session_state.performance)
                st.session_state.confirm_reset = False
                st.success("Progress reset!")
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("Click again to confirm reset")

