"""Configuration management for the application."""
import os


class Config:
    """Application configuration."""
    
    # Mistral API
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "DDNWDdI7EojlRqY75qKZVnbtmF21QVCQ")
    MISTRAL_MODEL = "mistral-small-latest"
    
    # ElevenLabs API
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    
    # Video Generation
    VIDEO_WIDTH = 1280
    VIDEO_HEIGHT = 720
    VIDEO_FPS = 24
    VIDEO_CODEC = "libx264"
    
    # LLM Settings
    TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    
    # Question Generation
    QUESTIONS_PER_SESSION = 10
    MIN_ANSWERS = 2
    MAX_ANSWERS = 5

