"""Video content recommendation based on performance."""
from typing import List
from datetime import datetime
from src.models.user_state import UserPerformance
from src.models.course import CourseStructure, Concept
from src.models.video import VideoContent, VideoMetadata
from src.services.video.script_generator import ScriptGenerator
from src.services.video.tts_service import TTSService
from src.services.video.video_assembler import VideoAssembler


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
        """Generate video content for a concept.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept_name: Concept name
            relevance_score: Relevance score for the video
            
        Returns:
            VideoContent object with metadata
        """
        # Find the concept
        concept = self._find_concept(topic, subtopic, concept_name)
        
        # Generate script
        script = self.script_generator.generate_script(topic, subtopic, concept)
        
        # Estimate duration
        duration = self.script_generator.estimate_duration(script)
        
        # Create metadata
        metadata = VideoMetadata(
            topic=topic,
            subtopic=subtopic,
            concept=concept_name,
            duration_seconds=duration,
            created_at=datetime.now(),
            script=script
        )
        
        return VideoContent(
            metadata=metadata,
            script=script,
            relevance_score=relevance_score
        )
    
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

