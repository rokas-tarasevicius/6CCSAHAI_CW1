"""Video extraction service."""
import subprocess
import random
from pathlib import Path
from backend.shared.utils.config import Config


class VideoExtractor:
    """Extract video segments."""
    
    def __init__(self, source_path: str | None = None):
        """Initialize video extractor.
        
        Args:
            source_path: Path to source video (defaults to minecraft_source_pre_scaled.mp4)
        """
        if source_path:
            self.source_path = Path(source_path)
        else:
            backend_root = Path(__file__).parent.parent.parent.parent
            self.source_path = backend_root / "backend" / "video_service_v2" / "assets" / "minecraft_source_pre_scaled.mp4"
        
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source video not found: {self.source_path}")
        
        # Cache source video duration
        self._source_duration = None
    
    def _get_source_duration(self) -> float:
        """Get source video duration in seconds."""
        if self._source_duration is None:
            try:
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        str(self.source_path)
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self._source_duration = float(result.stdout.strip())
            except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
                self._source_duration = 30.0  # Fallback
        return self._source_duration
    
    def get_random_start_time(self, segment_duration: float) -> float:
        """Get a random start time for a segment.
        
        Args:
            segment_duration: Duration of the segment in seconds
            
        Returns:
            Random start time in seconds
        """
        source_duration = self._get_source_duration()
        max_start_time = max(0, source_duration - segment_duration)
        if max_start_time <= 0:
            return 0.0
        return random.uniform(0, max_start_time)
    
    def extract_segment(self, output_path: str, duration: float = 30.0, start_time: float = 0.0) -> bool:
        """Extract a video segment.
        
        Args:
            output_path: Path to save extracted video
            duration: Duration in seconds (default: 30)
            start_time: Start time in seconds (default: 0)
            
        Returns:
            True if successful
        """
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", str(self.source_path),
                    "-ss", str(start_time),
                    "-t", str(duration),
                    "-c:v", "libx264",  # Re-encode to ensure exact duration
                    "-preset", "fast",
                    "-crf", "23",
                    "-y",
                    str(output_path)
                ],
                check=True,
                capture_output=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Create dummy file if ffmpeg not available
            Path(output_path).touch()
            return False

