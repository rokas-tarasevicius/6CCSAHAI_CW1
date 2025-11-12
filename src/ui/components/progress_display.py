"""Progress and score display components."""
import streamlit as st
from src.models.user_state import UserPerformance
from src.services.tracking.analytics import PerformanceAnalytics


def render_progress_header(performance: UserPerformance) -> None:
    """Render progress information in header.
    
    Args:
        performance: User performance data
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Trophy Score", f"🏆 {performance.trophy_score}")
    
    with col2:
        st.metric("Questions", performance.total_questions_answered)
    
    with col3:
        accuracy = performance.overall_accuracy
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    with col4:
        mastery = PerformanceAnalytics.get_mastery_level(performance)
        st.metric("Level", mastery)


def render_detailed_progress(performance: UserPerformance) -> None:
    """Render detailed progress breakdown.
    
    Args:
        performance: User performance data
    """
    st.subheader("Your Progress")
    
    # Overall stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Correct", performance.total_correct)
        st.metric("Total Incorrect", performance.total_incorrect)
    
    with col2:
        accuracy = performance.overall_accuracy
        st.metric("Overall Accuracy", f"{accuracy:.1f}%")
        st.metric("Trophy Score", f"🏆 {performance.trophy_score}")
    
    # Topic breakdown
    if performance.topic_scores:
        st.markdown("#### Performance by Topic")
        
        topic_breakdown = PerformanceAnalytics.get_topic_breakdown(performance)
        
        for topic_data in topic_breakdown:
            if topic_data["attempts"] > 0:
                with st.expander(f"{topic_data['topic']} - {topic_data['accuracy']:.1f}%"):
                    st.write(f"**Questions Answered:** {topic_data['attempts']}")
                    st.write(f"**Correct:** {topic_data['correct']}")
                    st.write(f"**Accuracy:** {topic_data['accuracy']:.1f}%")
                    
                    # Progress bar
                    st.progress(topic_data['accuracy'] / 100.0)
    
    # Insights
    insights = PerformanceAnalytics.generate_insights(performance)
    if insights:
        st.markdown("#### Insights")
        for insight in insights:
            st.info(insight)


def render_compact_stats(performance: UserPerformance) -> None:
    """Render compact stats display.
    
    Args:
        performance: User performance data
    """
    st.markdown(f"""
    **Stats:** {performance.total_questions_answered} questions | 
    {performance.total_correct} correct | 
    {performance.overall_accuracy:.1f}% accuracy | 
    🏆 {performance.trophy_score}
    """)

