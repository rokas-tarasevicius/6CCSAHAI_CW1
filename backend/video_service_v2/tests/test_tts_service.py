"""Tests for TTS service."""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from backend.video_service_v2.services.tts_service import TTSService


@pytest.fixture
def mock_elevenlabs():
    """Mock ElevenLabs client."""
    with patch('elevenlabs.client.ElevenLabs') as mock:
        client = MagicMock()
        text_to_speech = MagicMock()
        convert = MagicMock(return_value=b"audio_data")
        text_to_speech.convert = convert
        client.text_to_speech = text_to_speech
        mock.return_value = client
        yield client


def test_init_with_api_key(mock_elevenlabs):
    """Test initialization with API key."""
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config, \
         patch('elevenlabs.VoiceSettings'):
        mock_config.ELEVENLABS_API_KEY = "test_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService()
        assert service.available is True


def test_init_without_api_key():
    """Test initialization without API key."""
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = ""
        
        service = TTSService()
        assert service.available is False


@patch('elevenlabs.client.ElevenLabs')
@patch('elevenlabs.VoiceSettings')
def test_generate_success(mock_voice_settings, mock_elevenlabs_class, tmp_path):
    """Test successful TTS generation."""
    mock_client = MagicMock()
    mock_text_to_speech = MagicMock()
    mock_convert = MagicMock(return_value=b"audio_data")
    mock_text_to_speech.convert = mock_convert
    mock_client.text_to_speech = mock_text_to_speech
    mock_elevenlabs_class.return_value = mock_client
    
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = "test_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService()
        output_path = tmp_path / "output.mp3"
        result = service.generate("test text", str(output_path))
        
        assert result is True
        assert output_path.exists()


def test_generate_unavailable(tmp_path):
    """Test TTS generation when service unavailable."""
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = ""
        
        service = TTSService()
        output_path = tmp_path / "output.mp3"
        result = service.generate("test text", str(output_path))
        
        assert result is False
        assert output_path.exists()


def test_generate_chunks(tmp_path):
    """Test generating TTS for multiple chunks."""
    with patch('elevenlabs.client.ElevenLabs') as mock_elevenlabs_class, \
         patch('elevenlabs.VoiceSettings'):
        mock_client = MagicMock()
        mock_text_to_speech = MagicMock()
        mock_convert = MagicMock(return_value=b"audio_data")
        mock_text_to_speech.convert = mock_convert
        mock_client.text_to_speech = mock_text_to_speech
        mock_elevenlabs_class.return_value = mock_client
        
        with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
            mock_config.ELEVENLABS_API_KEY = "test_key"
            mock_config.ELEVENLABS_VOICE_ID = "test_voice"
            
            service = TTSService()
            chunks = ["chunk1", "chunk2", "chunk3"]
            output_paths = service.generate_chunks(chunks, str(tmp_path))
            
            assert len(output_paths) == len(chunks)
            assert all(Path(p).exists() for p in output_paths)


@patch('elevenlabs.client.ElevenLabs')
@patch('elevenlabs.VoiceSettings')
def test_generate_creates_output_directory(mock_voice_settings, mock_elevenlabs_class, tmp_path):
    """Test that output directory is created if it doesn't exist."""
    mock_client = MagicMock()
    mock_text_to_speech = MagicMock()
    mock_convert = MagicMock(return_value=b"audio_data")
    mock_text_to_speech.convert = mock_convert
    mock_client.text_to_speech = mock_text_to_speech
    mock_elevenlabs_class.return_value = mock_client
    
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = "test_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService()
        nested_path = tmp_path / "nested" / "deep" / "path" / "output.mp3"
        result = service.generate("test text", str(nested_path))
        
        assert result is True
        assert nested_path.parent.exists()
        assert nested_path.parent.is_dir()


@patch('elevenlabs.client.ElevenLabs')
@patch('elevenlabs.VoiceSettings')
def test_generate_file_permissions_write_output(mock_voice_settings, mock_elevenlabs_class, tmp_path):
    """Test that output directory is writable."""
    mock_client = MagicMock()
    mock_text_to_speech = MagicMock()
    mock_convert = MagicMock(return_value=b"audio_data")
    mock_text_to_speech.convert = mock_convert
    mock_client.text_to_speech = mock_text_to_speech
    mock_elevenlabs_class.return_value = mock_client
    
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = "test_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService()
        output_path = tmp_path / "output.mp3"
        
        # Check output directory permissions
        output_dir = output_path.parent
        assert os.access(output_dir, os.W_OK), "Output directory should be writable"
        
        result = service.generate("test text", str(output_path))
        
        assert result is True
        assert output_path.exists()


@patch('elevenlabs.client.ElevenLabs')
@patch('elevenlabs.VoiceSettings')
def test_generate_handles_api_error(mock_voice_settings, mock_elevenlabs_class, tmp_path):
    """Test handling of ElevenLabs API errors."""
    mock_client = MagicMock()
    mock_text_to_speech = MagicMock()
    mock_text_to_speech.convert = MagicMock(side_effect=Exception("API Error"))
    mock_client.text_to_speech = mock_text_to_speech
    mock_elevenlabs_class.return_value = mock_client
    
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = "test_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService()
        output_path = tmp_path / "output.mp3"
        result = service.generate("test text", str(output_path))
        
        # Should return False but still create file
        assert result is False
        assert output_path.exists()


@patch('elevenlabs.client.ElevenLabs')
@patch('elevenlabs.VoiceSettings')
def test_generate_handles_chunk_iterator(mock_voice_settings, mock_elevenlabs_class, tmp_path):
    """Test handling of chunked audio response."""
    mock_client = MagicMock()
    mock_text_to_speech = MagicMock()
    # Simulate chunked response
    mock_audio_chunks = [b"chunk1", b"chunk2", b"chunk3"]
    mock_text_to_speech.convert = MagicMock(return_value=iter(mock_audio_chunks))
    mock_client.text_to_speech = mock_text_to_speech
    mock_elevenlabs_class.return_value = mock_client
    
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = "test_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService()
        output_path = tmp_path / "output.mp3"
        result = service.generate("test text", str(output_path))
        
        assert result is True
        assert output_path.exists()
        # Verify file contains data
        assert output_path.stat().st_size > 0


@patch('elevenlabs.client.ElevenLabs')
@patch('elevenlabs.VoiceSettings')
def test_generate_handles_bytes_response(mock_voice_settings, mock_elevenlabs_class, tmp_path):
    """Test handling of bytes audio response."""
    mock_client = MagicMock()
    mock_text_to_speech = MagicMock()
    mock_text_to_speech.convert = MagicMock(return_value=b"audio_bytes_data")
    mock_client.text_to_speech = mock_text_to_speech
    mock_elevenlabs_class.return_value = mock_client
    
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = "test_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService()
        output_path = tmp_path / "output.mp3"
        result = service.generate("test text", str(output_path))
        
        assert result is True
        assert output_path.exists()
        # Verify file contains data
        assert output_path.stat().st_size > 0


def test_generate_chunks_empty_list(tmp_path):
    """Test generating chunks with empty list."""
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = ""
        
        service = TTSService()
        output_paths = service.generate_chunks([], str(tmp_path))
        
        assert output_paths == []


@patch('elevenlabs.client.ElevenLabs')
@patch('elevenlabs.VoiceSettings')
def test_generate_chunks_nested_directory(mock_voice_settings, mock_elevenlabs_class, tmp_path):
    """Test generating chunks in nested directory."""
    mock_client = MagicMock()
    mock_text_to_speech = MagicMock()
    mock_convert = MagicMock(return_value=b"audio_data")
    mock_text_to_speech.convert = mock_convert
    mock_client.text_to_speech = mock_text_to_speech
    mock_elevenlabs_class.return_value = mock_client
    
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = "test_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService()
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        chunks = ["chunk1", "chunk2"]
        output_paths = service.generate_chunks(chunks, str(nested_dir))
        
        assert len(output_paths) == len(chunks)
        assert nested_dir.exists()
        assert all(Path(p).exists() for p in output_paths)


def test_init_with_custom_api_key():
    """Test initialization with custom API key."""
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config, \
         patch('elevenlabs.client.ElevenLabs') as mock_elevenlabs, \
         patch('elevenlabs.VoiceSettings'):
        mock_config.ELEVENLABS_API_KEY = "default_key"
        mock_config.ELEVENLABS_VOICE_ID = "test_voice"
        
        service = TTSService(api_key="custom_key")
        mock_elevenlabs.assert_called_once_with(api_key="custom_key")
        assert service.available is True


def test_generate_empty_text(tmp_path):
    """Test generating TTS with empty text."""
    with patch('backend.video_service_v2.services.tts_service.Config') as mock_config:
        mock_config.ELEVENLABS_API_KEY = ""
        
        service = TTSService()
        output_path = tmp_path / "output.mp3"
        result = service.generate("", str(output_path))
        
        # Should still create file even with empty text
        assert result is False
        assert output_path.exists()

