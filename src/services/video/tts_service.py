"""Text-to-speech service using ElevenLabs."""
from typing import Optional, Dict, List, Tuple, Union
import os
import base64
from pathlib import Path
from src.utils.config import Config


class TTSService:
    """Text-to-speech conversion service."""
    
    def __init__(self, api_key: Optional[str] = None, custom_voice_id: Optional[str] = None):
        """Initialize TTS service.
        
        Args:
            api_key: ElevenLabs API key (defaults to Config.ELEVENLABS_API_KEY)
            custom_voice_id: Optional custom voice ID to try first (defaults to Config.ELEVENLABS_CUSTOM_VOICE_ID)
        """
        self.api_key = api_key or Config.ELEVENLABS_API_KEY
        # Try custom voice first if provided, otherwise use default
        self.custom_voice_id = custom_voice_id or Config.ELEVENLABS_CUSTOM_VOICE_ID
        self.default_voice_id = Config.ELEVENLABS_VOICE_ID
        self.voice_id = self.custom_voice_id if self.custom_voice_id else self.default_voice_id
        
        # Track which voice is currently being used
        self._validated_voice_id = None  # Will be set on first successful use
        
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
        
        # Normalize whitespace
        sanitized = " ".join(sanitized.split())
        
        return sanitized.strip()
    
    def text_to_speech(
        self,
        text: str,
        output_path: str,
        return_timestamps: bool = False
    ) -> Union[bool, Tuple[bool, Optional[Dict[str, List[Tuple[float, float, str]]]]]]:
        """Convert text to speech audio file.
        
        IMPORTANT: Sanitizes text before sending to ElevenLabs to remove formatting characters.
        This ensures alignment data matches the sanitized text used in subtitles.
        
        Args:
            text: Text to convert (will be sanitized before TTS)
            output_path: Path to save audio file
            return_timestamps: If True, also return word timestamps
            
        Returns:
            If return_timestamps=False: True if successful, False otherwise
            If return_timestamps=True: Tuple of (success: bool, word_timestamps: Dict[str, List[Tuple[float, float, str]]] | None)
                word_timestamps maps sentence text to list of (start_time, end_time, word) tuples
                All text in word_timestamps is sanitized (matches what was sent to ElevenLabs)
        """
        if not self.elevenlabs_available:
            result = self._create_dummy_audio(output_path)
            return (result, None) if return_timestamps else result
        
        # IMPORTANT: Sanitize text BEFORE sending to ElevenLabs
        # This ensures alignment data matches sanitized text used in subtitles
        sanitized_text = self._sanitize_script(text)
        if not sanitized_text:
            sanitized_text = "AI generated explanation"
        
        try:
            word_timestamps = None
            
            # If timestamps requested, use convert_with_timestamps
            if return_timestamps:
                try:
                    # Try custom voice first if configured, then fallback to default
                    voice_ids_to_try = []
                    if self.custom_voice_id:
                        voice_ids_to_try.append(self.custom_voice_id)
                    voice_ids_to_try.append(self.default_voice_id)
                    
                    response = None
                    voice_used = None
                    last_error = None
                    
                    for voice_id_to_try in voice_ids_to_try:
                        try:
                            if hasattr(self.client, 'text_to_speech') and hasattr(self.client.text_to_speech, 'convert_with_timestamps'):
                                # Use SANITIZED text for TTS - this is what ElevenLabs will align
                                response = self.client.text_to_speech.convert_with_timestamps(
                                    voice_id=voice_id_to_try,
                                    text=sanitized_text,  # Use sanitized text
                                    voice_settings=self.voice_settings,
                                    model_id="eleven_multilingual_v2"  # Timestamps work better with multilingual model
                                )
                                voice_used = voice_id_to_try
                                # Cache successful voice for future use
                                self._validated_voice_id = voice_id_to_try
                                
                                # Log which voice was used (only on first try or fallback)
                                if voice_id_to_try == self.custom_voice_id:
                                    print(f"✅ Using custom voice: {voice_id_to_try}")
                                elif voice_id_to_try == self.default_voice_id and self.custom_voice_id:
                                    print(f"⚠️  Custom voice unavailable, using default voice: {voice_id_to_try}")
                                
                                break  # Success - exit loop
                        except Exception as e:
                            error_msg = str(e).lower()
                            # Check if it's a voice-related error (voice doesn't exist or no access)
                            if any(keyword in error_msg for keyword in ['voice', 'not found', 'invalid', '404', '403', 'unauthorized', 'permission']):
                                last_error = e
                                # Try next voice
                                continue
                            else:
                                # Other errors (network, API issues) - re-raise
                                raise
                    
                    if response is None:
                        # All voices failed - this will be caught and we'll fall back to regular conversion
                        print(f"DEBUG: convert_with_timestamps failed for all voices, will fall back to regular conversion")
                        raise Exception(f"All voice attempts failed. Last error: {last_error}")
                    
                    # Use the response and voice_used for processing
                    print(f"DEBUG: convert_with_timestamps succeeded, processing response...")
                    # Extract audio and alignment data
                    # Response is AudioWithTimestampsResponse (Pydantic model)
                    # Has attributes: audio_base_64 (with underscore!) and alignment
                    if hasattr(response, 'audio_base_64'):
                        # Pydantic model - use attribute access (correct field name with underscore)
                        audio_base64 = response.audio_base_64
                        alignment_obj = response.alignment if hasattr(response, 'alignment') else None
                    elif hasattr(response, 'audio_base64'):
                        # Fallback for different naming
                        audio_base64 = response.audio_base64
                        alignment_obj = response.alignment if hasattr(response, 'alignment') else None
                    elif isinstance(response, dict):
                        # Dict response - check both naming conventions
                        audio_base64 = response.get('audio_base_64') or response.get('audio_base64') or response.get('audio')
                        alignment_obj = response.get('alignment') or response.get('normalized_alignment')
                    else:
                        # Try to get attributes via getattr (try both naming conventions)
                        audio_base64 = getattr(response, 'audio_base_64', 
                                              getattr(response, 'audio_base64', 
                                                     getattr(response, 'audio', None)))
                        alignment_obj = getattr(response, 'alignment', None)
                    
                    if audio_base64:
                        # Decode base64 audio
                        audio_bytes = base64.b64decode(audio_base64)
                        
                        # Save audio to file
                        output_dir = Path(output_path).parent
                        output_dir.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(audio_bytes)
                        
                        # Process alignment data to get word timestamps
                        # alignment_obj might be a Pydantic model - convert to dict if needed
                        if alignment_obj is not None:
                            # Debug: log what type of alignment_obj we have
                            print(f"DEBUG: alignment_obj type: {type(alignment_obj)}")
                            print(f"DEBUG: alignment_obj has model_dump: {hasattr(alignment_obj, 'model_dump')}")
                            print(f"DEBUG: alignment_obj has dict: {hasattr(alignment_obj, 'dict')}")
                            # Handle Pydantic models (v1 and v2)
                            if hasattr(alignment_obj, 'model_dump'):
                                # Pydantic v2 - use model_dump()
                                alignment = alignment_obj.model_dump()
                            elif hasattr(alignment_obj, 'dict'):
                                # Pydantic v1 - use dict()
                                alignment = alignment_obj.dict()
                            elif hasattr(alignment_obj, '__dict__'):
                                # Regular object - convert to dict
                                alignment = alignment_obj.__dict__
                            elif isinstance(alignment_obj, dict):
                                # Already a dict
                                alignment = alignment_obj
                            else:
                                # Try to access as dict-like
                                try:
                                    alignment = dict(alignment_obj)
                                except (TypeError, ValueError):
                                    alignment = {}
                            
                            # Use SANITIZED text - alignment is based on sanitized text
                            print(f"DEBUG: Processing alignment data, keys: {list(alignment.keys()) if isinstance(alignment, dict) else 'N/A'}")
                            word_timestamps = self._process_alignment_to_word_timestamps(alignment, sanitized_text)
                            
                            # Debug: check if word_timestamps is empty
                            if not word_timestamps or len(word_timestamps) == 0:
                                print("Warning: _process_alignment_to_word_timestamps returned empty result")
                                print(f"   Alignment data keys: {list(alignment.keys()) if isinstance(alignment, dict) else 'N/A'}")
                                print(f"   Alignment data sample: {str(alignment)[:200] if isinstance(alignment, dict) else str(alignment)[:200]}")
                        else:
                            print("Warning: No alignment data in response")
                            word_timestamps = None
                        
                        # Verify file was created
                        audio_file = Path(output_path)
                        if not audio_file.exists() or audio_file.stat().st_size == 0:
                            raise ValueError(f"Audio file was not created or is empty: {output_path}")
                        
                        # Return result - even if word_timestamps is None/empty, we succeeded in generating audio
                        return (True, word_timestamps) if return_timestamps else True
                except Exception as e:
                    error_str = str(e)
                    error_lower = error_str.lower()
                    
                    # Check if it's a quota/credit issue
                    if 'quota' in error_lower or 'credits' in error_lower:
                        print(f"⚠️  ElevenLabs quota exceeded - falling back to regular conversion")
                        print(f"   (Timestamp generation requires more credits than available)")
                    else:
                        print(f"Warning: convert_with_timestamps failed ({type(e).__name__}), falling back to regular conversion")
                        print(f"   Error: {str(e)[:200]}")
                    import traceback
                    traceback.print_exc()
            
            # Fallback to regular conversion (without timestamps)
            # Use SANITIZED text for fallback TTS as well
            # Try custom voice first if configured, then fallback to default
            voice_ids_to_try = []
            if self.custom_voice_id:
                voice_ids_to_try.append(self.custom_voice_id)
            voice_ids_to_try.append(self.default_voice_id)
            
            audio = None
            last_error = None
            voice_used = None
            
            for voice_id_to_try in voice_ids_to_try:
                try:
                    # Method 1: Newer API (v2.x) - text_to_speech.convert
                    if hasattr(self.client, 'text_to_speech') and hasattr(self.client.text_to_speech, 'convert'):
                        audio = self.client.text_to_speech.convert(
                            voice_id=voice_id_to_try,
                            text=sanitized_text,
                            voice_settings=self.voice_settings,
                            model_id="eleven_monolingual_v1"
                        )
                        voice_used = voice_id_to_try
                        # Cache successful voice for future use
                        self._validated_voice_id = voice_id_to_try
                        
                        # Log which voice was used (only on first try or fallback)
                        if voice_id_to_try == self.custom_voice_id:
                            print(f"✅ Using custom voice: {voice_id_to_try}")
                        elif voice_id_to_try == self.default_voice_id and self.custom_voice_id:
                            print(f"⚠️  Custom voice unavailable, using default voice: {voice_id_to_try}")
                        
                        break  # Success - exit loop
                except Exception as e:
                    error_msg = str(e).lower()
                    # Check if it's a voice-related error (voice doesn't exist or no access)
                    if any(keyword in error_msg for keyword in ['voice', 'not found', 'invalid', '404', '403', 'unauthorized', 'permission']):
                        last_error = e
                        # Try next voice
                        continue
                    else:
                        # Other errors - try alternative API methods
                        last_error = e
                        try:
                            # Method 2: Alternative new API - convert_as_stream
                            if hasattr(self.client, 'text_to_speech') and hasattr(self.client.text_to_speech, 'convert_as_stream'):
                                audio = self.client.text_to_speech.convert_as_stream(
                                    voice_id=voice_id_to_try,
                                    text=sanitized_text,
                                    voice_settings=self.voice_settings,
                                    model_id="eleven_monolingual_v1"
                                )
                                voice_used = voice_id_to_try
                                self._validated_voice_id = voice_id_to_try
                                
                                if voice_id_to_try == self.custom_voice_id:
                                    print(f"✅ Using custom voice: {voice_id_to_try}")
                                elif voice_id_to_try == self.default_voice_id and self.custom_voice_id:
                                    print(f"⚠️  Custom voice unavailable, using default voice: {voice_id_to_try}")
                                
                                break  # Success - exit loop
                        except Exception as e2:
                            error_msg2 = str(e2).lower()
                            if any(keyword in error_msg2 for keyword in ['voice', 'not found', 'invalid', '404', '403']):
                                last_error = e2
                                continue  # Try next voice
                            # Try Method 3
                            try:
                                # Method 3: Old API (v1.x) - direct generate
                                if hasattr(self.client, 'generate'):
                                    audio = self.client.generate(
                                        text=sanitized_text,
                                        voice=voice_id_to_try,
                                        voice_settings=self.voice_settings,
                                        model="eleven_monolingual_v1"
                                    )
                                    voice_used = voice_id_to_try
                                    self._validated_voice_id = voice_id_to_try
                                    
                                    if voice_id_to_try == self.custom_voice_id:
                                        print(f"✅ Using custom voice: {voice_id_to_try}")
                                    elif voice_id_to_try == self.default_voice_id and self.custom_voice_id:
                                        print(f"⚠️  Custom voice unavailable, using default voice: {voice_id_to_try}")
                                    
                                    break  # Success - exit loop
                            except Exception as e3:
                                error_msg3 = str(e3).lower()
                                if any(keyword in error_msg3 for keyword in ['voice', 'not found', 'invalid', '404', '403']):
                                    last_error = e3
                                    continue  # Try next voice
                                # Re-raise if it's not a voice-related error
                                raise
            
            if audio is None:
                if last_error:
                    raise AttributeError(f"All voices failed. Last error: {type(last_error).__name__}: {str(last_error)}")
                else:
                    raise ValueError("No audio was generated by any API method")
            
            if audio is None:
                raise ValueError("No audio was generated by any API method")
            
            # Save audio to file
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            bytes_written = 0
            with open(output_path, 'wb') as f:
                # Handle both generator/stream and direct bytes
                if hasattr(audio, '__iter__') and not isinstance(audio, (bytes, str)):
                    # It's a generator/stream
                    for chunk in audio:
                        if isinstance(chunk, bytes):
                            f.write(chunk)
                            bytes_written += len(chunk)
                        else:
                            # Some SDKs return objects with .data or need conversion
                            try:
                                chunk_bytes = getattr(chunk, 'data', None)
                                if chunk_bytes is None:
                                    # Try to convert to bytes
                                    chunk_bytes = bytes(chunk) if hasattr(chunk, '__bytes__') else str(chunk).encode()
                                f.write(chunk_bytes)
                                bytes_written += len(chunk_bytes)
                            except Exception:
                                continue
                else:
                    # Direct bytes or single object
                    if isinstance(audio, bytes):
                        f.write(audio)
                        bytes_written = len(audio)
                    else:
                        # Try to get bytes from object
                        try:
                            audio_bytes = getattr(audio, 'data', None)
                            if audio_bytes is None:
                                # Try to convert to bytes
                                audio_bytes = bytes(audio) if hasattr(audio, '__bytes__') else str(audio).encode()
                            f.write(audio_bytes)
                            bytes_written = len(audio_bytes)
                        except Exception as bytes_error:
                            raise ValueError(f"Could not extract bytes from audio object: {bytes_error}")
            
            # Verify file was created
            audio_file = Path(output_path)
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file was not created: {output_path}")
            
            file_size = audio_file.stat().st_size
            if file_size == 0:
                raise ValueError(f"Audio file is empty (0 bytes): {output_path}")
            
            return (True, None) if return_timestamps else True
            
        except Exception as e:
            # Log error but don't print full traceback in normal operation
            if isinstance(e, (AttributeError, ValueError, FileNotFoundError)):
                raise
            # For other errors, create dummy file as fallback
            result = self._create_dummy_audio(output_path)
            return (result, None) if return_timestamps else result
    
    def _process_alignment_to_word_timestamps(
        self, 
        alignment: Dict, 
        text: str
    ) -> Dict[str, List[Tuple[float, float, str]]]:
        """Process alignment data from ElevenLabs API to extract word-level timestamps.
        
        Args:
            alignment: Alignment data from ElevenLabs API with character timestamps
            text: Original text that was converted
            
        Returns:
            Dictionary mapping sentence text to list of (start_time, end_time, word) tuples
        """
        import re
        
        # Extract character-level timestamps
        characters = alignment.get('characters', [])
        char_start_times = alignment.get('character_start_times_seconds', [])
        char_end_times = alignment.get('character_end_times_seconds', [])
        
        if not characters or not char_start_times or not char_end_times:
            return {}
        
        # Reconstruct text from characters
        # Note: text should already be sanitized before TTS, so characters should match
        reconstructed_text = ''.join(characters)
        
        # Split text into sentences
        sentences = [
            sentence.strip()
            for sentence in re.split(r'(?<=[.!?])\s+', text)
            if sentence.strip()
        ]
        if not sentences:
            sentences = [text.strip()]
        
        # Process each sentence to extract word timestamps
        word_timestamps = {}
        char_idx = 0  # Current position in characters array
        
        for sentence in sentences:
            words = sentence.split()
            sentence_word_timestamps = []
            
            for word in words:
                # Find word in characters array starting from current position
                word_chars = list(word.lower())
                word_start_char_idx = None
                word_end_char_idx = None
                
                # Search for word starting from current position
                search_start = char_idx
                for i in range(search_start, len(characters)):
                    # Try to match word characters (case-insensitive)
                    if i + len(word_chars) > len(characters):
                        break
                    
                    matched = True
                    char_idx_in_word = 0
                    word_start = None
                    word_end = None
                    
                    for j in range(i, min(i + len(word_chars) * 2, len(characters))):
                        char = characters[j]
                        
                        # Skip formatting characters (shouldn't be present if sanitized properly)
                        if char in '*/\_~':
                            continue
                        
                        # If we've matched all word chars, we found the word
                        if char_idx_in_word >= len(word_chars):
                            break
                        
                        # Check if character matches word char (case-insensitive)
                        if char.lower() == word_chars[char_idx_in_word]:
                            if word_start is None:
                                word_start = j
                            word_end = j
                            char_idx_in_word += 1
                        elif char.isspace():
                            # Allow spaces - might be within word boundaries if formatting chars were removed
                            if word_start is not None:
                                continue  # Keep searching
                            else:
                                continue  # Skip leading spaces
                        else:
                            # Non-matching character - not our word
                            matched = False
                            break
                    
                    # If we matched all characters, we found the word
                    if matched and word_start is not None and word_end is not None and char_idx_in_word >= len(word_chars):
                        word_start_char_idx = word_start
                        word_end_char_idx = word_end
                        char_idx = word_end + 1
                        
                        # Skip spaces after word
                        while char_idx < len(characters) and (characters[char_idx].isspace() or characters[char_idx] in '*/\_~'):
                            char_idx += 1
                        break
                
                # Get timestamps if found
                if word_start_char_idx is not None and word_end_char_idx is not None:
                    if word_start_char_idx < len(char_start_times) and word_end_char_idx < len(char_end_times):
                        word_start_time = char_start_times[word_start_char_idx]
                        word_end_time = char_end_times[word_end_char_idx]
                        sentence_word_timestamps.append((word_start_time, word_end_time, word))
            
            if sentence_word_timestamps:
                word_timestamps[sentence] = sentence_word_timestamps
        
        return word_timestamps
    
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

