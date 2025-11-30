"""Text-to-speech service using ElevenLabs."""
import logging
from pathlib import Path
from typing import List
from backend.shared.utils.config import Config

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-speech service."""
    
    def __init__(self, api_key: str | None = None):
        """Initialize TTS service.
        
        Args:
            api_key: ElevenLabs API key (defaults to Config.ELEVENLABS_API_KEY)
        """
        self.api_key = api_key or Config.ELEVENLABS_API_KEY
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        self.model_id = Config.ELEVENLABS_MODEL_ID
        
        logger.info(f"TTS Service initialized with model: {self.model_id}")
        
        if self.api_key:
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
                self.available = True
            except ImportError:
                self.available = False
        else:
            self.available = False
    
    def generate(self, text: str, output_path: str) -> bool:
        """Generate speech from text.
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            
        Returns:
            True if successful
        """
        if not self.available:
            logger.warning(f"TTS service not available - creating empty file: {output_path}")
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).touch()
            return False
        
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Generating TTS with model '{self.model_id}' for text length: {len(text)} chars")
            
            audio = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                voice_settings=self.voice_settings,
                model_id=self.model_id
            )
            
            with open(output_path, 'wb') as f:
                if hasattr(audio, '__iter__') and not isinstance(audio, (bytes, str)):
                    for chunk in audio:
                        if isinstance(chunk, bytes):
                            f.write(chunk)
                        else:
                            chunk_bytes = getattr(chunk, 'data', None)
                            if chunk_bytes is None:
                                chunk_bytes = bytes(chunk) if hasattr(chunk, '__bytes__') else str(chunk).encode()
                            f.write(chunk_bytes)
                else:
                    if isinstance(audio, bytes):
                        f.write(audio)
                    else:
                        audio_bytes = getattr(audio, 'data', None)
                        if audio_bytes is None:
                            audio_bytes = bytes(audio) if hasattr(audio, '__bytes__') else str(audio).encode()
                        f.write(audio_bytes)
            
            file_size = Path(output_path).stat().st_size
            if file_size == 0:
                logger.error(f"TTS generated empty file: {output_path}")
                return False
            
            logger.info(f"Successfully generated TTS audio: {output_path} ({file_size} bytes)")
            return True
        except Exception as e:
            error_str = str(e)
            # Check for quota exceeded errors
            if "quota_exceeded" in error_str.lower() or "quota" in error_str.lower():
                logger.error(f"TTS quota exceeded. Model: {self.model_id}, Error: {error_str}")
                logger.error("Consider: 1) Waiting for quota reset, 2) Upgrading ElevenLabs plan, 3) Using shorter scripts")
            else:
                logger.error(f"TTS generation failed (model: {self.model_id}): {error_str}")
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).touch()
            return False
    
    def generate_chunks(self, chunks: List[str], output_dir: str) -> List[str]:
        """Generate audio for multiple chunks.
        
        Args:
            chunks: List of text chunks
            output_dir: Directory to save audio files
            
        Returns:
            List of audio file paths
        """
        output_paths = []
        for i, chunk in enumerate(chunks):
            output_path = Path(output_dir) / f"chunk_{i}.mp3"
            self.generate(chunk, str(output_path))
            output_paths.append(str(output_path))
        return output_paths

