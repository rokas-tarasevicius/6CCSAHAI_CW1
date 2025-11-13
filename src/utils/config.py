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
    ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    
    # Video Generation
    VIDEO_WIDTH = 1280
    VIDEO_HEIGHT = 720
    VIDEO_FPS = 24
    VIDEO_CODEC = "libx264"
    
    # LLM Settings
    TEMPERATURE = 0.7
    MAX_TOKENS = 1000  # Reduced for faster generation
    QUESTION_MAX_TOKENS = 800  # Specific limit for questions
    
    # Question Generation
    QUESTIONS_PER_SESSION = 10
    MIN_ANSWERS = 2
    MAX_ANSWERS = 5
    QUESTION_CACHE_SIZE = 50  # Cache up to 50 questions

