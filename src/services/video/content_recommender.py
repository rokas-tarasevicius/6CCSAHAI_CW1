"""Video content recommendation based on performance."""
from typing import List, Optional
from datetime import datetime
import hashlib
from pathlib import Path
from src.models.user_state import UserPerformance
from src.models.course import CourseStructure, Concept
from src.models.video import VideoContent, VideoMetadata
from src.services.video.script_generator import ScriptGenerator
from src.services.video.tts_service import TTSService
from src.services.video.video_assembler import VideoAssembler
from src.utils.config import Config


class ContentRecommender:
    """Recommend and generate video content based on user performance."""
    
    def __init__(
        self,
        course: CourseStructure,
        script_generator: ScriptGenerator,
        tts_service: TTSService,
        video_assembler: VideoAssembler
    ):
        """Initialize content recommender.
        
        Args:
            course: Course structure
            script_generator: Script generation service
            tts_service: TTS service
            video_assembler: Video assembly service
        """
        self.course = course
        self.script_generator = script_generator
        self.tts_service = tts_service
        self.video_assembler = video_assembler
    
    def recommend_videos(
        self,
        performance: UserPerformance,
        max_videos: int = 5
    ) -> List[tuple[str, str, str, float]]:
        """Recommend concepts for video generation based on performance.
        
        Args:
            performance: User performance data
            max_videos: Maximum number of videos to recommend
            
        Returns:
            List of (topic, subtopic, concept_name, relevance_score) tuples
        """
        recommendations = []
        
        # Get weak concepts
        weak_concepts = performance.get_all_weak_concepts()
        
        if weak_concepts:
            # Prioritize weak areas
            for topic, subtopic, concept in weak_concepts[:max_videos]:
                concept_score = None
                if topic in performance.topic_scores:
                    topic_obj = performance.topic_scores[topic]
                    if subtopic in topic_obj.subtopic_scores:
                        subtopic_obj = topic_obj.subtopic_scores[subtopic]
                        if concept in subtopic_obj.concept_scores:
                            concept_score = subtopic_obj.concept_scores[concept]
                
                # Calculate relevance based on how weak the concept is
                if concept_score:
                    relevance = (100 - concept_score.accuracy) / 100.0
                else:
                    relevance = 0.5
                
                recommendations.append((topic, subtopic, concept, relevance))
        
        # If we need more recommendations, add untried concepts
        if len(recommendations) < max_videos:
            all_concepts = self.course.get_all_concepts()
            
            for topic, subtopic, concept in all_concepts:
                if len(recommendations) >= max_videos:
                    break
                
                # Check if already recommended
                if any(r[0] == topic and r[1] == subtopic and r[2] == concept.name 
                       for r in recommendations):
                    continue
                
                # Check if attempted
                attempted = False
                if topic in performance.topic_scores:
                    topic_obj = performance.topic_scores[topic]
                    if subtopic in topic_obj.subtopic_scores:
                        subtopic_obj = topic_obj.subtopic_scores[subtopic]
                        if concept.name in subtopic_obj.concept_scores:
                            attempted = True
                
                if not attempted:
                    recommendations.append((topic, subtopic, concept.name, 0.3))
        
        # Sort by relevance (highest first)
        recommendations.sort(key=lambda x: x[3], reverse=True)
        
        return recommendations[:max_videos]
    
    def generate_video_content(
        self,
        topic: str,
        subtopic: str,
        concept_name: str,
        relevance_score: float = 1.0
    ) -> VideoContent:
        """Generate video content for a concept, including audio and video files.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept_name: Concept name
            relevance_score: Relevance score for the video
            
        Returns:
            VideoContent object with metadata and file paths
        """
        # Find the concept
        concept = self._find_concept(topic, subtopic, concept_name)
        
        # Get parsed content from course structure for context
        content_context = ""
        for t in self.course.topics:
            if t.name == topic:
                for st in t.subtopics:
                    if st.name == subtopic:
                        content_context = st.content or ""
                        break
                break
        
        # Generate script with parsed content context
        script = self.script_generator.generate_script(topic, subtopic, concept, content_context)
        
        # Note: TTS service will sanitize the script before sending to ElevenLabs
        # This ensures alignment data matches the sanitized text used in subtitles
        
        # Estimate duration (use sanitized script if needed, but TTS handles sanitization)
        duration = self.script_generator.estimate_duration(script, words_per_minute=Config.REEL_WORDS_PER_MINUTE)
        
        # Generate unique ID for files
        file_id = self._generate_file_id(topic, subtopic, concept_name)
        
        # Create output directories
        # Create output directories (relative to project root)
        # Get project root by going up from src/services/video/
        project_root = Path(__file__).parent.parent.parent.parent
        audio_dir = project_root / "videos" / "audio"
        video_dir = project_root / "videos" / "video"
        audio_dir.mkdir(parents=True, exist_ok=True)
        video_dir.mkdir(parents=True, exist_ok=True)

        audio_path = str(audio_dir / f"{file_id}.mp3")
        video_path = str(video_dir / f"{file_id}.mp4")
        
        # Generate audio using TTS with timestamps for better subtitle sync
        # TTS service sanitizes the script internally, so word_timestamps will use sanitized text
        tts_result = self.tts_service.text_to_speech(script, audio_path, return_timestamps=True)
        
        if isinstance(tts_result, tuple):
            audio_success, word_timestamps = tts_result
        else:
            audio_success = tts_result
            word_timestamps = None
        
        # Verify audio file was created
        audio_file = Path(audio_path)
        if not audio_file.exists() or audio_file.stat().st_size == 0:
            raise ValueError(f"Audio generation failed: file not created or empty")
        
        minecraft_source = Path(Config.MINECRAFT_REEL_SOURCE)
        video_success = False
        created_dummy = False

        if Config.REEL_MODE and minecraft_source.exists():
            try:
                video_success = self.video_assembler.create_minecraft_reel_video(
                    audio_path,
                    str(minecraft_source),
                    video_path,
                    script,
                    duration=duration,
                    word_timestamps=word_timestamps
                )
            except Exception:
                video_success = False

        if not video_success:
            video_success = self.video_assembler._create_dummy_video(video_path)
            created_dummy = True

        # Verify video file was created
        video_file = Path(video_path)
        if not video_file.exists():
            raise ValueError(f"Video generation failed: file not created")
        # Only check file size if it's not a dummy video
        if not created_dummy and video_file.stat().st_size == 0:
            raise ValueError(f"Video generation failed: file is empty")
        
        # Create metadata
        metadata = VideoMetadata(
            topic=topic,
            subtopic=subtopic,
            concept=concept_name,
            duration_seconds=duration,
            created_at=datetime.now(),
            script=script,
            audio_path=audio_path if audio_success else None,
            video_path=video_path if video_success else None
        )
        
        return VideoContent(
            metadata=metadata,
            script=script,
            relevance_score=relevance_score
        )
    
    def _generate_file_id(self, topic: str, subtopic: str, concept_name: str) -> str:
        """Generate a unique file ID for video/audio files.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept_name: Concept name
            
        Returns:
            Unique file ID string
        """
        key_string = f"{topic}_{subtopic}_{concept_name}".lower().replace(" ", "_")
        # Create hash for uniqueness
        file_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
        # Clean filename
        clean_name = "".join(c for c in key_string if c.isalnum() or c in ('_', '-'))[:50]
        return f"{clean_name}_{file_hash}"
    
    def _find_concept(self, topic: str, subtopic: str, concept_name: str) -> Concept:
        """Find a concept by name.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept_name: Concept name
            
        Returns:
            Concept object
            
        Raises:
            ValueError: If concept not found
        """
        for t in self.course.topics:
            if t.name == topic:
                for st in t.subtopics:
                    if st.name == subtopic:
                        for c in st.concepts:
                            if c.name == concept_name:
                                return c
        
        raise ValueError(f"Concept not found: {topic}/{subtopic}/{concept_name}")

