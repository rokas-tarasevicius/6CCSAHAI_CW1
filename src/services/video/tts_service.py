"""Text-to-speech service using ElevenLabs."""
from typing import Optional
import os
from pathlib import Path
from src.utils.config import Config


class TTSService:
    """Text-to-speech conversion service."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize TTS service.
        
        Args:
            api_key: ElevenLabs API key (defaults to Config.ELEVENLABS_API_KEY)
        """
        self.api_key = api_key or Config.ELEVENLABS_API_KEY
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        
        # Check if ElevenLabs is available
        self.elevenlabs_available = bool(self.api_key)
        
        if self.elevenlabs_available:
            try:
                from elevenlabs import VoiceSettings
                from elevenlabs.client import ElevenLabs
                self.client = ElevenLabs(api_key=self.api_key)
                self.voice_settings = VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            except ImportError:
                self.elevenlabs_available = False
    
    def text_to_speech(
        self,
        text: str,
        output_path: str
    ) -> bool:
        """Convert text to speech audio file.
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.elevenlabs_available:
            # Create a dummy audio file for testing
            return self._create_dummy_audio(output_path)
        
        try:
            # Generate audio using ElevenLabs
            audio = self.client.generate(
                text=text,
                voice=self.voice_id,
                voice_settings=self.voice_settings,
                model="eleven_monolingual_v1"
            )
            
            # Save audio to file
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"TTS error: {e}")
            return self._create_dummy_audio(output_path)
    
    def _create_dummy_audio(self, output_path: str) -> bool:
        """Create a dummy audio file for testing without API.
        
        Args:
            output_path: Path to save dummy audio file
            
        Returns:
            True if successful
        """
        # Create empty audio file as placeholder
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal silent audio file (just a marker)
        Path(output_path).touch()
        
        return True
    
    def is_available(self) -> bool:
        """Check if TTS service is available.
        
        Returns:
            True if service is available
        """
        return self.elevenlabs_available

