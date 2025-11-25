"""Video assembly using FFmpeg."""
import random
import re
import subprocess
import textwrap
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from backend.shared.utils.config import Config


class VideoAssembler:
    """Assemble videos from audio and images using FFmpeg."""
    
    def __init__(self):
        """Initialize video assembler."""
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available.
        
        Returns:
            True if FFmpeg is available
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True,
                text=True
            )
            return True
        except FileNotFoundError:
            return False
        except subprocess.CalledProcessError:
            return False
            

    def create_minecraft_reel_video(
        self,
        audio_path: str,
        source_video_path: str,
        output_path: str,
        script: str,
        duration: Optional[float] = None,
        word_timestamps: Optional[Dict[str, List[Tuple[float, float, str]]]] = None
    ) -> bool:
        """Create a Minecraft reel video using a source clip with subtitles and word highlighting."""
        if not self.ffmpeg_available:
            return self._create_dummy_video(output_path)

        source = Path(source_video_path)
        if not source.exists():
            raise FileNotFoundError(f"Minecraft source video not found: {source_video_path}")

        # Check for pre-scaled version first (optimization)
        pre_scaled = self._find_pre_scaled_video(source)
        if pre_scaled:
            print(f"✅ Using pre-scaled video: {pre_scaled} (faster - no scaling/padding needed)")
            actual_source = pre_scaled
            needs_scale_pad = False
        else:
            # Check if source needs scaling/padding
            needs_scale_pad = self._needs_scaling_padding(source)
            if not needs_scale_pad:
                print(f"✅ Source video already matches target resolution (faster - no scaling/padding needed)")
            actual_source = source

        audio_duration = self._get_media_duration(audio_path)
        estimated_duration = duration or audio_duration
        target_duration = min(
            max(estimated_duration, Config.REEL_DURATION_TARGET_MIN),
            Config.REEL_DURATION_TARGET_MAX
        )
        target_duration = max(target_duration, min(audio_duration, Config.REEL_DURATION_TARGET_MAX))

        video_duration = self._get_media_duration(str(actual_source))
        if video_duration <= 0:
            raise RuntimeError(f"Invalid duration for source video: {video_duration}")

        if target_duration > video_duration:
            target_duration = video_duration

        temp_dir = Path(output_path).parent / "temp" / "minecraft_reel"
        temp_dir.mkdir(parents=True, exist_ok=True)
        subtitles_path = temp_dir / "reel_subtitles.ass"
        
        # Get the actual duration of the audio
        final_audio_duration = self._get_media_duration(audio_path)
        if final_audio_duration <= 0:
            final_audio_duration = target_duration  # Fallback if duration probe fails
        
        # Use audio duration for subtitles (ensures perfect sync)
        final_duration = min(final_audio_duration, video_duration, Config.REEL_DURATION_TARGET_MAX)
        
        # Generate subtitles with word-by-word highlighting using FINAL audio duration
        self._write_subtitles_with_word_highlighting(
            script, 
            final_duration, 
            subtitles_path,
            word_timestamps=word_timestamps
        )
        
        # Calculate video start time based on final duration
        start_max = max(video_duration - final_duration, 0.0)
        start_time = random.uniform(0.0, start_max) if start_max > 0 else 0.0

        # Build video filter - only include scale/pad if needed
        if needs_scale_pad:
            # Need to scale and pad
            video_filter = (
                f"scale={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
                f"ass={subtitles_path}"
            )
        else:
            # Already correct resolution - just add subtitles
            video_filter = f"ass={subtitles_path}"

        try:
            cmd = [
                'ffmpeg',
                '-y',
                '-ss', f"{start_time:.3f}",
                '-i', str(actual_source),  # Use pre-scaled or original source
                '-i', audio_path,  # Use original audio directly
                '-t', f"{final_duration:.3f}",
                '-vf', video_filter,
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-c:v', Config.VIDEO_CODEC,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                '-shortest',
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)

            output_file = Path(output_path)
            if not output_file.exists():
                raise FileNotFoundError(f"Video file was not created: {output_path}")

            if output_file.stat().st_size == 0:
                raise ValueError(f"Video file is empty (0 bytes): {output_path}")

            return True
        except subprocess.CalledProcessError as e:
            stderr_text = (
                e.stderr.decode('utf-8', errors='ignore')
                if isinstance(e.stderr, bytes)
                else (e.stderr or 'No stderr')
            )
            raise RuntimeError(f"FFmpeg Minecraft reel command failed: {stderr_text}")
        finally:
            # Cleanup temp files
            try:
                subtitles_path.unlink()
            except Exception:
                pass

    
    def _create_dummy_video(self, output_path: str) -> bool:
        """Create a dummy video file for testing.
        
        Args:
            output_path: Path to save dummy video
            
        Returns:
            True if successful
        """
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder file
        Path(output_path).touch()
        
        return True

    def _get_video_dimensions(self, file_path: str) -> tuple[int, int] | None:
        """Get video width and height using ffprobe.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Tuple of (width, height) or None if probe fails
        """
        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width,height',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    file_path
                ],
                capture_output=True,
                text=True,
                check=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                width = int(lines[0].strip())
                height = int(lines[1].strip())
                return (width, height)
        except (subprocess.CalledProcessError, ValueError, IndexError):
            pass
        return None
    
    def _get_media_duration(self, file_path: str) -> float:
        """Probe the duration of a media file using ffprobe."""
        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    file_path
                ],
                capture_output=True,
                text=True,
                check=True
            )
            duration_str = result.stdout.strip()
            return float(duration_str) if duration_str else 0.0
        except subprocess.CalledProcessError as e:
            stderr_text = (
                e.stderr.decode('utf-8', errors='ignore')
                if isinstance(e.stderr, bytes)
                else (e.stderr or 'No stderr')
            )
            raise RuntimeError(f"Failed to probe duration for {file_path}: {stderr_text}") from e
        except ValueError:
            return 0.0
    
    def _find_pre_scaled_video(self, source_path: Path) -> Path | None:
        """Find pre-scaled version of source video if it exists.
        
        Checks for a pre-scaled version (e.g., minecraft_source_pre_scaled.mp4)
        and verifies it has the correct dimensions.
        
        Args:
            source_path: Path to source video
            
        Returns:
            Path to pre-scaled video if found and valid, None otherwise
        """
        source_dir = source_path.parent
        source_stem = source_path.stem
        pre_scaled_path = source_dir / f"{source_stem}_pre_scaled.mp4"
        
        if not pre_scaled_path.exists():
            return None
        
        # Verify dimensions match target
        dimensions = self._get_video_dimensions(str(pre_scaled_path))
        if dimensions:
            width, height = dimensions
            if width == Config.VIDEO_WIDTH and height == Config.VIDEO_HEIGHT:
                return pre_scaled_path
        
        # Pre-scaled version exists but has wrong dimensions
        return None
    
    def _needs_scaling_padding(self, source_path: Path) -> bool:
        """Check if source video needs scaling or padding.
        
        Args:
            source_path: Path to source video
            
        Returns:
            True if video needs processing, False if already matches target
        """
        dimensions = self._get_video_dimensions(str(source_path))
        
        if dimensions is None:
            # Can't determine dimensions - assume processing needed
            return True
        
        width, height = dimensions
        
        # Check if dimensions match target exactly
        return not (width == Config.VIDEO_WIDTH and height == Config.VIDEO_HEIGHT)

    def get_media_duration(self, file_path: str) -> float:
        """Public wrapper to probe the duration of a media file."""
        return self._get_media_duration(file_path)

    def _format_ass_time(self, time_seconds: float) -> str:
        """Format seconds into ASS-style timestamps (H:MM:SS.cc)."""
        total_seconds = max(0.0, time_seconds)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        centiseconds = int((total_seconds - int(total_seconds)) * 100)
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    def _escape_ass_text(self, text: str) -> str:
        """Escape text for ASS subtitles."""
        return (
            text.replace('\\', r'\\')
            .replace('{', r'\{')
            .replace('}', r'\}')
        )
        

    def _sanitize_script(self, script: str) -> str:
        """Sanitize script by removing formatting characters that cause TTS/subtitle issues.
        
        Removes:
        - Asterisks (*) - often read as "asterisk" by TTS
        - Slashes (/ \\) - formatting characters
        - Other markdown/formatting characters
        
        Args:
            script: Raw script text
            
        Returns:
            Sanitized script text
        """
        if not script:
            return ""
        
        # Remove common formatting characters that cause issues
        # Remove asterisks (often read as "asterisk" by TTS)
        sanitized = script.replace('*', '')
        
        # Remove slashes and backslashes
        sanitized = sanitized.replace('/', ' ').replace('\\', ' ')
        
        # Remove other markdown formatting characters
        sanitized = sanitized.replace('_', ' ').replace('~', ' ')
        
        sanitized = sanitized.replace('=', ' ')
        # Normalize whitespace
        sanitized = " ".join(sanitized.split())
        
        return sanitized.strip()

    def _normalize_script(self, script: str) -> str:
        """Normalize whitespace in the script."""
        return " ".join(script.split())

    def _build_subtitle_events(self, script: str, duration: float) -> List[tuple[float, float, str]]:
        """Split the script into timed events for subtitles."""
        normalized = self._normalize_script(script)
        if not normalized:
            normalized = "AI generated explanation"

        sentences = [
            sentence.strip()
            for sentence in re.split(r'(?<=[.!?])\s+', normalized)
            if sentence.strip()
        ]
        if not sentences:
            sentences = [normalized]

        words_per_second = Config.REEL_WORDS_PER_MINUTE / 60.0
        base_durations = []
        for sentence in sentences:
            word_count = len(sentence.split())
            base_duration = word_count / words_per_second if word_count else 0.5
            base_durations.append(base_duration)

        total_base_duration = sum(base_durations) or 1.0
        scale = (duration / total_base_duration) if duration > 0 else 1.0

        events: List[tuple[float, float, str]] = []
        start = 0.0
        max_lines = Config.REEL_SUBTITLE_MAX_LINES

        for sentence, base_duration in zip(sentences, base_durations):
            chunk_duration = base_duration * scale
            if chunk_duration <= 0:
                chunk_duration = 0.5

            end = min(start + chunk_duration, duration)
            lines = textwrap.wrap(sentence, width=Config.REEL_SUBTITLE_WRAP_CHARS)
            if not lines:
                lines = [sentence]
            if max_lines and len(lines) > max_lines:
                lines = lines[:max_lines]

            event_text = r"\N".join(self._escape_ass_text(line) for line in lines)
            events.append((start, end, event_text))

            start = end
            if start >= duration:
                break

        if not events:
            events = [(0.0, duration, self._escape_ass_text(normalized))]
        else:
            last_start, _, last_text = events[-1]
            events[-1] = (last_start, duration, last_text)

        return events

    def _write_subtitles(self, script: str, duration: float, subtitle_path: Path) -> None:
        """Write ASS subtitles covering the full duration with timed events."""
        events = self._build_subtitle_events(script, duration)
        subtitle_content = (
            "[Script Info]\n"
            "Title: Minecraft AI Reel\n"
            "ScriptType: v4.00+\n"
            "WrapStyle: 2\n"
            f"PlayResX: {Config.VIDEO_WIDTH}\n"
            f"PlayResY: {Config.VIDEO_HEIGHT}\n"
            "ScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,{Config.REEL_SUBTITLE_FONT},{Config.REEL_SUBTITLE_FONT_SIZE},&H00FFFFFF,"
            f"&H000000FF,&H00000000,&H20000000,1,0,0,1,100,110,0,0,3,3,2,5,10,10,"
            f"{Config.REEL_SUBTITLE_MARGIN_V},1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        for start, end, text in events:
            start_time = self._format_ass_time(start)
            end_time = self._format_ass_time(end)
            subtitle_content += (
                f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
            )

        subtitle_path.write_text(subtitle_content, encoding='utf-8')

    def _write_subtitles_with_word_highlighting(
        self, 
        script: str, 
        duration: float, 
        subtitle_path: Path,
        word_timestamps: Optional[Dict[str, List[Tuple[float, float, str]]]] = None
    ) -> None:
        """Write ASS subtitles with word-by-word highlighting using actual timestamps if available.

        Uses ASS karaoke (\\k) tags when timestamps are present. Otherwise falls back to
        simple sentence-level subtitles with heuristic timing.
        """
        # Fallback text if script is empty
        if not script:
            script = "AI generated explanation"

        # If we don't have timestamps, sanitize for fallback only
        sanitized = self._sanitize_script(script)

        # Center vertically - 50% of screen height
        center_y = Config.VIDEO_HEIGHT // 2

        # Build ASS header + style
        # NOTE: karaoke uses SecondaryColour for the highlight colour
        subtitle_content = (
            "[Script Info]\n"
            "Title: Minecraft AI Reel\n"
            "ScriptType: v4.00+\n"
            "WrapStyle: 2\n"
            f"PlayResX: {Config.VIDEO_WIDTH}\n"
            f"PlayResY: {Config.VIDEO_HEIGHT}\n"
            "ScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
            "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            # Primary: normal text (white)
            # Secondary: karaoke highlight (gold)
            # Outline: black border for readability
            f"Style: Default,{Config.REEL_SUBTITLE_FONT},{Config.REEL_SUBTITLE_FONT_SIZE},"
            f"&H00FFFFFF,&H0038D7FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,5,"
            f"{center_y},{center_y},{center_y},1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        # ---------- CASE 1: We have real word timestamps -> use karaoke WITH WRAPPING ----------
        if word_timestamps:
            import textwrap

            max_chars = getattr(Config, "REEL_SUBTITLE_WRAP_CHARS", 40) or 40

            for ts_sentence, ts_words in word_timestamps.items():
                if not ts_words:
                    continue

                # Sentence timing from first/last word
                first_start = ts_words[0][0]
                last_end = ts_words[-1][1]
                sent_start = first_start
                sent_end = min(last_end + 0.25, duration)  # tiny breathing room

                if sent_start >= duration:
                    break

                # `ts_sentence` should already be sanitized in TTSService
                sentence_text = " ".join(ts_sentence.split())
                if not sentence_text:
                    continue

                display_words = sentence_text.split()

                # Build list of (k_cs, display_word) for each word
                karaoke_tokens: List[Tuple[int, str]] = []
                for i, (w_start, w_end, w_text) in enumerate(ts_words):
                    # duration in seconds for this word
                    w_dur = max(w_end - w_start, 0.05)
                    k_cs = max(int(round(w_dur * 100)), 1)

                    # Prefer display word from sentence if available
                    if i < len(display_words):
                        display_word = display_words[i]
                    else:
                        display_word = w_text

                    escaped_word = self._escape_ass_text(display_word)
                    karaoke_tokens.append((k_cs, escaped_word))

                # --- WRAP TOKENS INTO MULTIPLE LINES ---
                # We wrap by *character length* of visible words, not counting \k tags.
                lines: List[List[Tuple[int, str]]] = []
                current_line: List[Tuple[int, str]] = []
                current_len = 0

                for k_cs, word in karaoke_tokens:
                    word_len = len(word)
                    # +1 for space if not first in line
                    extra = word_len + (1 if current_line else 0)

                    if current_line and (current_len + extra) > max_chars:
                        # Start new line
                        lines.append(current_line)
                        current_line = [(k_cs, word)]
                        current_len = word_len
                    else:
                        current_line.append((k_cs, word))
                        current_len += extra

                if current_line:
                    lines.append(current_line)

                # Build karaoke text with \k tags and \N line breaks
                line_strings: List[str] = []
                for line in lines:
                    parts = []
                    for k_cs, word in line:
                        parts.append(rf"{{\k{k_cs}}}{word}")
                    line_strings.append(" ".join(parts))

                # Join lines with ASS line breaks so they stack in the middle
                karaoke_text = r"\N".join(line_strings)

                # Single pos tag, centered – ASS will lay out multiple lines around this
                pos_tag = rf"{{\pos({Config.VIDEO_WIDTH // 2},{center_y})\an5\q2}}"
                full_text = f"{pos_tag}{karaoke_text}"

                start_str = self._format_ass_time(sent_start)
                end_str = self._format_ass_time(sent_end)

                subtitle_content += (
                    f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{full_text}\n"
                )

        # ---------- CASE 2: No timestamps -> simple heuristic subtitles ----------
        else:
            import re, textwrap

            if not sanitized:
                sanitized = "AI generated explanation"

            # Split into sentences
            sentences = [
                s.strip()
                for s in re.split(r'(?<=[.!?])\s+', sanitized)
                if s.strip()
            ]
            if not sentences:
                sentences = [sanitized]

            # Total words for timing
            total_words = sum(len(s.split()) for s in sentences) or 1

            # Use 90% of duration for speech, leave a tiny pause at end
            effective_duration = duration * 0.90
            word_duration = effective_duration / total_words

            current_time = 0.0
            line_height = Config.REEL_SUBTITLE_FONT_SIZE * 1.3

            for sentence in sentences:
                words = sentence.split()
                if not words:
                    continue

                sent_word_count = len(words)
                sent_start = current_time
                sent_end = min(
                    current_time + sent_word_count * word_duration,
                    duration,
                )

                if sent_start >= duration:
                    break

                # Wrap text (no per-word highlighting here)
                max_chars = Config.REEL_SUBTITLE_WRAP_CHARS
                max_lines = Config.REEL_SUBTITLE_MAX_LINES
                lines = textwrap.wrap(sentence, width=max_chars) or [sentence]
                if len(lines) > max_lines:
                    lines = lines[:max_lines]

                total_h = len(lines) * line_height
                start_y = center_y - (total_h // 2) + (line_height // 2)

                all_line_texts = []
                for idx, line in enumerate(lines):
                    line_y = start_y + idx * line_height
                    escaped_line = self._escape_ass_text(line)
                    pos_tag = rf"{{\pos({Config.VIDEO_WIDTH // 2},{line_y})\an5\q2}}"
                    all_line_texts.append(f"{pos_tag}{escaped_line}")

                joined = r"\N".join(all_line_texts)
                start_str = self._format_ass_time(sent_start)
                end_str = self._format_ass_time(sent_end)

                subtitle_content += (
                    f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{joined}\n"
                )

                current_time = sent_end

        # Finally write the ASS file
        subtitle_path.write_text(subtitle_content, encoding="utf-8")


    def is_available(self) -> bool:
        """Check if video assembly is available.
        
        Returns:
            True if FFmpeg is available
        """
        return self.ffmpeg_available

