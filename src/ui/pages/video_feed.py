"""Video feed page with personalized recommendations."""
import streamlit as st
from src.models.user_state import UserPerformance
from src.services.tracking.performance_tracker import PerformanceTracker
from src.services.video.script_generator import ScriptGenerator
from src.services.video.tts_service import TTSService
from src.services.video.video_assembler import VideoAssembler
from src.services.video.content_recommender import ContentRecommender
from src.services.llm.mistral_client import MistralClient
from src.utils.course_loader import CourseLoader
from src.ui.components.progress_display import render_compact_stats


def initialize_video_state():
    """Initialize video-related session state."""
    if not st.session_state.get("initialized", False):
        st.session_state.performance = UserPerformance()
        st.session_state.tracker = PerformanceTracker(st.session_state.performance)
        st.session_state.initialized = True
    
    if "course" not in st.session_state:
        try:
            st.session_state.course = CourseLoader.load_from_file("data/course_material.json")
        except:
            st.session_state.course = CourseLoader.create_sample_course()
    
    if "mistral_client" not in st.session_state:
        st.session_state.mistral_client = MistralClient()
    
    if "video_services" not in st.session_state:
        script_gen = ScriptGenerator(st.session_state.mistral_client)
        tts_service = TTSService()
        video_assembler = VideoAssembler()
        
        st.session_state.video_services = {
            "script_generator": script_gen,
            "tts_service": tts_service,
            "video_assembler": video_assembler,
            "recommender": ContentRecommender(
                st.session_state.course,
                script_gen,
                tts_service,
                video_assembler
            )
        }
    
    if "generated_videos" not in st.session_state:
        st.session_state.generated_videos = []


def render_video_feed_page():
    """Render the video feed page."""
    initialize_video_state()
    
    st.title("🎥 Personalized Video Feed")
    
    # Show compact stats
    render_compact_stats(st.session_state.performance)
    
    st.markdown("---")
    
    # Check if user has answered any questions
    if st.session_state.performance.total_questions_answered == 0:
        st.info("""
        ### Start Learning First!
        
        Video recommendations are based on your performance in quizzes.
        
        👉 Go to the **Quiz** page to answer some questions first.
        """)
        
        if st.button("Go to Quiz", type="primary"):
            st.switch_page("pages/quiz.py")
        
        return
    
    # Get recommendations
    recommender = st.session_state.video_services["recommender"]
    recommendations = recommender.recommend_videos(
        st.session_state.performance,
        max_videos=5
    )
    
    if not recommendations:
        st.info("No video recommendations available at the moment. Keep learning!")
        return
    
    st.subheader("Recommended Videos for You")
    st.write("These videos are personalized based on your learning needs.")
    
    # Display recommendations
    for idx, (topic, subtopic, concept_name, relevance) in enumerate(recommendations):
        with st.expander(f"📹 {concept_name} - {subtopic}", expanded=(idx == 0)):
            st.write(f"**Topic:** {topic}")
            st.write(f"**Subtopic:** {subtopic}")
            st.write(f"**Relevance:** {'⭐' * int(relevance * 5)}")
            
            # Generate button
            if st.button(f"Generate Video", key=f"gen_{idx}"):
                with st.spinner("Generating video content..."):
                    try:
                        video_content = recommender.generate_video_content(
                            topic, subtopic, concept_name, relevance
                        )
                        
                        # Show script
                        st.success("✅ Video content generated!")
                        st.markdown("#### Video Script")
                        st.text_area(
                            "Script",
                            value=video_content.script,
                            height=200,
                            key=f"script_{idx}",
                            label_visibility="collapsed"
                        )
                        
                        st.info(f"Estimated duration: {video_content.metadata.duration_seconds:.0f} seconds")
                        
                        # Note about actual video generation
                        tts_available = st.session_state.video_services["tts_service"].is_available()
                        ffmpeg_available = st.session_state.video_services["video_assembler"].is_available()
                        
                        if not tts_available or not ffmpeg_available:
                            st.warning("""
                            **Note:** Full video generation requires:
                            - ElevenLabs API key for text-to-speech
                            - FFmpeg installed for video assembly
                            
                            Currently showing script preview only.
                            """)
                        else:
                            st.success("🎬 Video generation is fully configured!")
                        
                    except Exception as e:
                        st.error(f"Error generating video: {str(e)}")
    
    st.markdown("---")
    
    # Show weak areas
    weak_concepts = st.session_state.performance.get_all_weak_concepts()
    if weak_concepts:
        st.subheader("Focus Areas")
        st.write("These concepts need more practice:")
        
        for topic, subtopic, concept in weak_concepts[:5]:
            st.markdown(f"- **{concept}** ({topic} → {subtopic})")


# Run the page
if __name__ == "__main__":
    render_video_feed_page()

