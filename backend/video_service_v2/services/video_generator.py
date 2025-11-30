"""Video generation orchestrator."""
import subprocess
import logging
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import List, Optional
from backend.video_service_v2.services.script_service import ScriptService
from backend.video_service_v2.services.video_extractor import VideoExtractor
from backend.video_service_v2.services.script_chunker import ScriptChunker
from backend.video_service_v2.services.tts_service import TTSService
from backend.course_service.models.course import Concept

logger = logging.getLogger(__name__)


class VideoGenerator:
    """Orchestrate video generation."""
    
    def __init__(
        self,
        script_service: ScriptService | None = None,
        video_extractor: VideoExtractor | None = None,
        script_chunker: ScriptChunker | None = None,
        tts_service: TTSService | None = None
    ):
        """Initialize video generator."""
        self.script_service = script_service or ScriptService()
        self.video_extractor = video_extractor or VideoExtractor()
        self.script_chunker = script_chunker or ScriptChunker()
        self.tts_service = tts_service or TTSService()
    
    def _get_cache_key(self, topic: str, subtopic: str, concept: Concept, unique: bool = False) -> str:
        """Generate cache key for video based on topic, subtopic, and concept.
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept object
            unique: If True, add timestamp to make key unique (for random videos)
            
        Returns:
            Cache key (hash string)
        """
        key_data = f"{topic}:{subtopic}:{concept.name}"
        if unique:
            # Add timestamp to ensure unique cache key for random videos
            key_data += f":{time.time()}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_video(self, cache_key: str, cache_dir: Path) -> Optional[tuple[str, str, float, str, str, str]]:
        """Check if cached video exists and return its metadata.
        
        Args:
            cache_key: Cache key for the video
            cache_dir: Cache directory path
            
        Returns:
            Tuple of (video_path, script, duration, topic, subtopic, concept) if cached, None otherwise
        """
        cache_file = cache_dir / f"{cache_key}.mp4"
        metadata_file = cache_dir / f"{cache_key}.json"
        
        if cache_file.exists() and cache_file.stat().st_size > 0 and metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"Found cached video: {cache_file}")
                return (
                    str(cache_file),
                    metadata.get('script', ''),
                    metadata.get('duration', 0.0),
                    metadata.get('topic', ''),
                    metadata.get('subtopic', ''),
                    metadata.get('concept', '')
                )
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        
        return None
    
    def list_cached_videos(self, cache_dir: Path) -> List[dict]:
        """List all cached videos with their metadata.
        
        Args:
            cache_dir: Cache directory path
            
        Returns:
            List of video metadata dictionaries
        """
        cached_videos = []
        
        if not cache_dir.exists():
            return cached_videos
        
        try:
            # Find all JSON metadata files
            for metadata_file in cache_dir.glob("*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    cache_key = metadata.get('cache_key', metadata_file.stem)
                    video_file = cache_dir / f"{cache_key}.mp4"
                    
                    if video_file.exists() and video_file.stat().st_size > 0:
                        cached_videos.append({
                            'video_path': f"{cache_key}.mp4",  # Just filename, file serving handles cache dir
                            'script': metadata.get('script', ''),
                            'duration_seconds': metadata.get('duration', 0.0),
                            'topic': metadata.get('topic', ''),
                            'subtopic': metadata.get('subtopic', ''),
                            'concept': metadata.get('concept', ''),
                            'cache_key': cache_key
                        })
                except Exception as e:
                    logger.warning(f"Failed to load cache metadata from {metadata_file}: {e}")
            
            logger.info(f"Found {len(cached_videos)} cached videos")
        except Exception as e:
            logger.error(f"Failed to list cached videos: {e}")
        
        return cached_videos
    
    def _save_to_cache(self, cache_key: str, cache_dir: Path, video_path: str, script: str, duration: float, topic: str, subtopic: str, concept_name: str) -> None:
        """Save video and metadata to cache.
        
        Args:
            cache_key: Cache key for the video
            cache_dir: Cache directory path
            video_path: Path to the video file
            script: Script text
            duration: Video duration in seconds
            topic: Topic name
            subtopic: Subtopic name
            concept_name: Concept name
        """
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy video to cache
            cache_file = cache_dir / f"{cache_key}.mp4"
            shutil.copy2(video_path, cache_file)
            
            # Save metadata
            metadata_file = cache_dir / f"{cache_key}.json"
            with open(metadata_file, 'w') as f:
                json.dump({
                    'script': script,
                    'duration': duration,
                    'video_path': str(cache_file),
                    'topic': topic,
                    'subtopic': subtopic,
                    'concept': concept_name,
                    'cache_key': cache_key
                }, f)
            
            logger.info(f"Cached video: {cache_file}")
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")
    
    def generate(
        self,
        topic: str,
        subtopic: str,
        concept: Concept,
        output_dir: str,
        force_regenerate: bool = False
    ) -> tuple[str, str, str, float]:
        """Generate video for a concept (with caching).
        
        Args:
            topic: Topic name
            subtopic: Subtopic name
            concept: Concept object
            output_dir: Directory to save output files
            force_regenerate: If True, bypass cache and always generate new video
            
        Returns:
            Tuple of (video_path, audio_path, script, duration_seconds)
        """
        # Get cache key and directory
        # For force_regenerate (random videos), use unique key to ensure different segments
        cache_key = self._get_cache_key(topic, subtopic, concept, unique=force_regenerate)
        # Cache directory is a sibling of output directory (both inside video_service_v2 package)
        cache_dir = Path(output_dir).parent / "cache"
        
        # Check cache first (unless forcing regeneration)
        if not force_regenerate:
            cached = self._get_cached_video(cache_key, cache_dir)
            
            if cached:
                cached_video_path, script, duration, _, _, _ = cached
                # Copy cached video to output location
                output_video_path = Path(output_dir) / "final_video.mp4"
                shutil.copy2(cached_video_path, output_video_path)
                logger.info(f"Using cached video: {cached_video_path}")
                # Return cached video (audio_path is empty since we don't cache it separately)
                return (str(output_video_path), "", script, duration)
        
        # Generate script (force regeneration or cache miss)
        script = self.script_service.generate(topic, subtopic, concept)
        
        # Chunk script for subtitles only
        chunks = self.script_chunker.chunk(script)
        logger.info(f"Script chunked into {len(chunks)} subtitle segments")
        
        # Generate TTS for the full script (temporary file, will be deleted)
        temp_audio_path = Path(output_dir) / "temp_audio.mp3"
        temp_audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if TTS service is available
        if not self.tts_service.available:
            logger.warning("TTS service is not available - video will have no audio")
        
        # Generate single audio file for entire script
        audio_generated = self.tts_service.generate(script, str(temp_audio_path))
        if not audio_generated:
            logger.error("Failed to generate TTS audio")
        
        # Get actual audio duration
        audio_duration = self._get_audio_duration(str(temp_audio_path))
        # Use actual audio duration for video (up to 30s max)
        video_duration = min(audio_duration, 30.0)
        
        # Generate subtitle file - use actual audio duration for accurate timing
        subtitle_path = Path(output_dir) / "temp_subtitles.srt"
        self._generate_subtitles(chunks, str(temp_audio_path), str(subtitle_path), video_duration)
        
        # Generate final video directly (no intermediate files)
        # Use actual audio duration to ensure video matches audio exactly
        final_video_path = Path(output_dir) / f"temp_{cache_key}.mp4"
        self._generate_final_video(str(temp_audio_path), str(subtitle_path), str(final_video_path), audio_duration)
        
        # Always save to cache (random videos use unique keys so they don't overwrite each other)
        self._save_to_cache(cache_key, cache_dir, str(final_video_path), script, audio_duration, topic, subtopic, concept.name)
        
        # Move video to output location
        output_video_path = Path(output_dir) / "final_video.mp4"
        shutil.move(str(final_video_path), str(output_video_path))
        
        # Clean up temporary files
        try:
            temp_audio_path.unlink(missing_ok=True)
            subtitle_path.unlink(missing_ok=True)
            # Clean up old temp_audio directory if it exists (from previous chunk-based approach)
            temp_audio_dir = Path(output_dir) / "temp_audio"
            if temp_audio_dir.exists():
                shutil.rmtree(temp_audio_dir, ignore_errors=True)
                logger.info("Cleaned up old temp_audio directory")
        except Exception as e:
            logger.warning(f"Failed to clean up temp files: {e}")
        
        return (
            str(output_video_path),
            "",  # No separate audio file needed
            script,
            audio_duration
        )
    
    def _generate_subtitles(self, chunks: List[str], audio_path: str, subtitle_path: str, total_duration: float) -> None:
        """Generate SRT subtitle file from script chunks.
        
        Args:
            chunks: List of script chunks for subtitles
            audio_path: Path to the full audio file (for actual duration calculation)
            subtitle_path: Path to save SRT file
            total_duration: Total video duration in seconds
        """
        try:
            # Get actual audio duration for accurate timing
            actual_audio_duration = self._get_audio_duration(audio_path) if Path(audio_path).exists() else total_duration
            # Use the shorter of audio duration or target duration
            effective_duration = min(actual_audio_duration, total_duration)
            
            # Calculate total words in all chunks for proportional timing
            total_words = sum(len(chunk.split()) for chunk in chunks)
            
            chunk_timings = []
            current_time = 0.0
            
            # Process all chunks with proportional timing based on word count
            for chunk in chunks:
                if not chunk.strip():
                    continue
                    
                words = chunk.split()
                word_count = len(words)
                
                # Calculate duration proportionally based on word count
                if total_words > 0:
                    chunk_duration = (word_count / total_words) * effective_duration
                else:
                    # Fallback: estimate based on speaking rate
                    chunk_duration = word_count / self.script_chunker.words_per_second if self.script_chunker.words_per_second > 0 else self.script_chunker.chunk_duration
                
                start_time = current_time
                end_time = min(current_time + chunk_duration, effective_duration)
                
                # Always add chunk if it has content and valid timing
                if end_time > start_time:
                    chunk_timings.append((start_time, end_time, chunk))
                    current_time = end_time
                
                # Stop if we've reached or exceeded total duration
                if current_time >= effective_duration:
                    break
            
            # Ensure the last subtitle extends to the end if we have remaining time
            if chunk_timings:
                last_start, last_end, last_text = chunk_timings[-1]
                # Extend last subtitle to match effective duration exactly
                if last_end < effective_duration:
                    chunk_timings[-1] = (last_start, effective_duration, last_text)
                # Also ensure we don't exceed effective duration
                elif last_end > effective_duration:
                    chunk_timings[-1] = (last_start, effective_duration, last_text)
            
            logger.info(f"Generated {len(chunk_timings)} subtitle entries covering {effective_duration:.2f}s total (audio: {actual_audio_duration:.2f}s, target: {total_duration:.2f}s)")
            
            # Write SRT file
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                for i, (start, end, text) in enumerate(chunk_timings, 1):
                    # Format times as SRT format: HH:MM:SS,mmm
                    start_str = self._format_srt_time(start)
                    end_str = self._format_srt_time(end)
                    
                    # Clean text for subtitles (remove extra whitespace)
                    clean_text = " ".join(text.split())
                    
                    # Split long lines (max ~50 chars per line, max 3 lines for readability)
                    # IMPORTANT: Never truncate - show all text, even if it exceeds limits
                    words = clean_text.split()
                    lines = []
                    current_line = []
                    current_length = 0
                    max_chars_per_line = 50
                    max_lines = 3
                    word_index = 0
                    
                    while word_index < len(words):
                        word = words[word_index]
                        # Calculate length if we add this word
                        word_len = len(word) + (1 if current_line else 0)  # +1 for space if not first word
                        
                        # If adding this word would exceed line length and we have content, start new line
                        if current_length + word_len > max_chars_per_line and current_line:
                            lines.append(" ".join(current_line))
                            current_line = [word]
                            current_length = len(word)
                            
                            # If we've hit max lines, add all remaining words to last line
                            if len(lines) >= max_lines:
                                remaining_words = words[word_index + 1:]
                                if remaining_words:
                                    lines[-1] = lines[-1] + " " + " ".join(remaining_words)
                                break
                        else:
                            current_line.append(word)
                            current_length += word_len
                        
                        word_index += 1
                    
                    # Add remaining words if we didn't break
                    if current_line:
                        lines.append(" ".join(current_line))
                    
                    # Ensure we have at least one line (show all text even if it's long)
                    subtitle_text = "\n".join(lines) if lines else clean_text
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{subtitle_text}\n\n")
            
            logger.info(f"Generated subtitle file with {len(chunk_timings)} entries: {subtitle_path}")
        except Exception as e:
            logger.error(f"Failed to generate subtitles: {e}")
            Path(subtitle_path).touch()
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds as SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _generate_final_video(self, audio_path: str, subtitle_path: str, output_path: str, duration: float) -> None:
        """Generate final video directly from source video, audio, and subtitles.
        
        Args:
            audio_path: Path to audio file
            subtitle_path: Path to SRT subtitle file
            output_path: Path to save final video
            duration: Target duration in seconds
        """
        try:
            source_video = self.video_extractor.source_path
            
            # Get random start time from source video
            start_time = self.video_extractor.get_random_start_time(duration)
            logger.info(f"Using random start time: {start_time:.2f}s for {duration:.2f}s segment")
            
            # Build ffmpeg command to generate final video in one step
            cmd = [
                "ffmpeg",
                "-ss", str(start_time),  # Start at random position
                "-i", str(source_video),
                "-i", audio_path,
                "-t", str(duration),  # Limit to target duration
            ]
            
            # Add subtitle filter if subtitle file exists and is valid
            subtitle_filter = self._build_subtitle_filter(subtitle_path)
            if subtitle_filter:
                cmd.extend(["-vf", subtitle_filter])
            else:
                cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "23"])
            
            cmd.extend([
                "-c:a", "aac",
                "-y",
                str(output_path)
            ])
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully generated final video: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate final video: {e.stderr}")
            Path(output_path).touch()
        except FileNotFoundError:
            logger.error("ffmpeg not found - cannot generate video")
            Path(output_path).touch()
    
    def _build_subtitle_filter(self, subtitle_path: str) -> str | None:
        """Build subtitle filter string for ffmpeg.
        
        Args:
            subtitle_path: Path to SRT subtitle file
            
        Returns:
            Subtitle filter string if file exists and is valid, None otherwise
        """
        if not subtitle_path or not Path(subtitle_path).exists():
            return None
        
        if Path(subtitle_path).stat().st_size == 0:
            return None
        
        abs_subtitle_path = Path(subtitle_path).absolute()
        escaped_path = str(abs_subtitle_path).replace("\\", "/").replace(":", "\\:")
        return f"subtitles={escaped_path}:force_style='FontName=DejaVu Sans Bold,FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=30'"
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return 30.0  # Default fallback

