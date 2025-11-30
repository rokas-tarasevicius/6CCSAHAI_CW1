"""Configuration management for the application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration."""
    
    # Mistral API
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY environment variable is required. Please set it in .env file.")
    MISTRAL_MODEL = "mistral-small-latest"
    
    # ElevenLabs API
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    # Custom voice ID (optional) - if set, will try this first, fallback to default
    ELEVENLABS_CUSTOM_VOICE_ID = os.getenv("ELEVENLABS_CUSTOM_VOICE_ID", "")
    ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice (fallback)
    # TTS Model: eleven_turbo_v2 (cheapest/fastest), eleven_multilingual_v2, or eleven_monolingual_v1
    ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2")
    
    # Video Generation
    VIDEO_WIDTH = 1280
    VIDEO_HEIGHT = 720
    VIDEO_FPS = 24
    VIDEO_CODEC = "libx264"
    
    # Short-form Reel Settings
    REEL_MODE = True  # Enable reel-optimized generation
    REEL_DURATION_TARGET_MIN = 15  # Minimum duration in seconds
    REEL_DURATION_TARGET_MAX = 60  # Maximum duration in seconds
    REEL_WORDS_PER_MINUTE = 150  # Speaking rate for duration estimation
    MINECRAFT_REEL_SOURCE = os.getenv(
        "MINECRAFT_REEL_SOURCE",
        str(Path(__file__).parent.parent.parent / "video_service" / "assets" / "minecraft_source.mp4")
    )
    REEL_SUBTITLE_FONT = os.getenv("REEL_SUBTITLE_FONT", "DejaVuSans-Bold")
    REEL_SUBTITLE_FONT_SIZE = int(os.getenv("REEL_SUBTITLE_FONT_SIZE", "56"))
    REEL_SUBTITLE_WRAP_CHARS = int(os.getenv("REEL_SUBTITLE_WRAP_CHARS", "40"))
    REEL_SUBTITLE_MARGIN_V = int(os.getenv("REEL_SUBTITLE_MARGIN_V", "60"))
    REEL_SUBTITLE_MAX_LINES = int(os.getenv("REEL_SUBTITLE_MAX_LINES", "5"))
    
    # LLM Settings
    TEMPERATURE = 0.7
    MAX_TOKENS = 1000  # Reduced for faster generation
    QUESTION_MAX_TOKENS = 800  # Specific limit for questions
    
    # Question Generation
    QUESTIONS_PER_SESSION = 10
    MIN_ANSWERS = 2
    MAX_ANSWERS = 5
    QUESTION_CACHE_SIZE = 50  # Cache up to 50 questions

