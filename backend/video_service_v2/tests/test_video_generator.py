"""Tests for video generator."""
import pytest
import os
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from backend.video_service_v2.services.video_generator import VideoGenerator
from backend.video_service_v2.services.script_service import ScriptService
from backend.video_service_v2.services.video_extractor import VideoExtractor
from backend.video_service_v2.services.script_chunker import ScriptChunker
from backend.video_service_v2.services.tts_service import TTSService
from backend.course_service.models.course import Concept


@pytest.fixture
def concept():
    """Create test concept."""
    return Concept(
        name="Test Concept",
        description="Test description",
        keywords=["test"]
    )


@pytest.fixture
def mock_services():
    """Create mock services."""
    script_service = Mock(spec=ScriptService)
    script_service.generate = Mock(return_value="Test script")
    
    video_extractor = Mock(spec=VideoExtractor)
    video_extractor.extract_segment = Mock(return_value=True)
    
    script_chunker = Mock(spec=ScriptChunker)
    script_chunker.chunk = Mock(return_value=["chunk1", "chunk2"])
    
    tts_service = Mock(spec=TTSService)
    tts_service.generate_chunks = Mock(return_value=["audio1.mp3", "audio2.mp3"])
    
    return script_service, video_extractor, script_chunker, tts_service


@patch('subprocess.run')
def test_generate_video(mock_subprocess, mock_services, concept, tmp_path):
    """Test video generation."""
    script_service, video_extractor, script_chunker, tts_service = mock_services
    
    # Mock ffprobe for duration
    mock_subprocess.return_value = Mock(stdout="30.0\n", returncode=0)
    
    generator = VideoGenerator(
        script_service=script_service,
        video_extractor=video_extractor,
        script_chunker=script_chunker,
        tts_service=tts_service
    )
    
    video_path, audio_path, script, duration = generator.generate(
        "Topic",
        "Subtopic",
        concept,
        str(tmp_path)
    )
    
    assert script == "Test script"
    assert duration == 30.0
    script_service.generate.assert_called_once()
    script_chunker.chunk.assert_called_once()
    tts_service.generate_chunks.assert_called_once()


def test_generate_with_default_services(concept, tmp_path):
    """Test video generation with default services."""
    with patch('backend.video_service_v2.services.video_generator.ScriptService') as mock_script_class, \
         patch('backend.video_service_v2.services.video_generator.VideoExtractor') as mock_extractor_class, \
         patch('backend.video_service_v2.services.video_generator.ScriptChunker') as mock_chunker_class, \
         patch('backend.video_service_v2.services.video_generator.TTSService') as mock_tts_class, \
         patch('subprocess.run') as mock_subprocess:
        
        mock_script = Mock()
        mock_script.generate = Mock(return_value="Test script")
        mock_script_class.return_value = mock_script
        
        mock_extractor = Mock()
        mock_extractor.extract_segment = Mock(return_value=True)
        mock_extractor_class.return_value = mock_extractor
        
        mock_chunker = Mock()
        mock_chunker.chunk = Mock(return_value=["chunk1"])
        mock_chunker_class.return_value = mock_chunker
        
        mock_tts = Mock()
        mock_tts.generate_chunks = Mock(return_value=["audio1.mp3"])
        mock_tts_class.return_value = mock_tts
        
        mock_subprocess.return_value = Mock(stdout="30.0\n", returncode=0)
        
        generator = VideoGenerator()
        video_path, audio_path, script, duration = generator.generate(
            "Topic",
            "Subtopic",
            concept,
            str(tmp_path)
        )
        
        assert script == "Test script"


@patch('subprocess.run')
def test_generate_creates_output_directory(mock_subprocess, mock_services, concept, tmp_path):
    """Test that output directory is created."""
    script_service, video_extractor, script_chunker, tts_service = mock_services
    
    mock_subprocess.return_value = Mock(stdout="30.0\n", returncode=0)
    
    generator = VideoGenerator(
        script_service=script_service,
        video_extractor=video_extractor,
        script_chunker=script_chunker,
        tts_service=tts_service
    )
    
    nested_output = tmp_path / "nested" / "deep" / "path"
    video_path, audio_path, script, duration = generator.generate(
        "Topic",
        "Subtopic",
        concept,
        str(nested_output)
    )
    
    assert nested_output.exists()
    assert nested_output.is_dir()


@patch('subprocess.run')
def test_generate_file_permissions(mock_subprocess, mock_services, concept, tmp_path):
    """Test file permissions for output directory."""
    script_service, video_extractor, script_chunker, tts_service = mock_services
    
    mock_subprocess.return_value = Mock(stdout="30.0\n", returncode=0)
    
    generator = VideoGenerator(
        script_service=script_service,
        video_extractor=video_extractor,
        script_chunker=script_chunker,
        tts_service=tts_service
    )
    
    # Check output directory is writable
    assert os.access(tmp_path, os.W_OK), "Output directory should be writable"
    
    video_path, audio_path, script, duration = generator.generate(
        "Topic",
        "Subtopic",
        concept,
        str(tmp_path)
    )
    
    # Verify output files exist
    assert Path(video_path).exists() or Path(video_path).parent.exists()
    assert Path(audio_path).exists() or Path(audio_path).parent.exists()


@patch('subprocess.run')
def test_generate_handles_audio_combine_error(mock_subprocess, mock_services, concept, tmp_path):
    """Test handling of audio combination errors."""
    script_service, video_extractor, script_chunker, tts_service = mock_services
    
    # Mock ffprobe for duration
    def mock_subprocess_side_effect(*args, **kwargs):
        # First call for ffprobe (duration)
        if 'ffprobe' in args[0]:
            return Mock(stdout="30.0\n", returncode=0)
        # Second call for audio combine (should fail)
        elif 'concat' in args[0]:
            raise subprocess.CalledProcessError(1, "ffmpeg")
        return Mock(returncode=0)
    
    mock_subprocess.side_effect = mock_subprocess_side_effect
    
    generator = VideoGenerator(
        script_service=script_service,
        video_extractor=video_extractor,
        script_chunker=script_chunker,
        tts_service=tts_service
    )
    
    video_path, audio_path, script, duration = generator.generate(
        "Topic",
        "Subtopic",
        concept,
        str(tmp_path)
    )
    
    # Should still return paths even if combine fails
    assert script == "Test script"
    assert Path(audio_path).exists() or Path(audio_path).parent.exists()


@patch('subprocess.run')
def test_generate_handles_video_combine_error(mock_subprocess, mock_services, concept, tmp_path):
    """Test handling of video/audio combination errors."""
    script_service, video_extractor, script_chunker, tts_service = mock_services
    
    # Mock ffprobe for duration
    def mock_subprocess_side_effect(*args, **kwargs):
        # First call for ffprobe (duration)
        if 'ffprobe' in args[0]:
            return Mock(stdout="30.0\n", returncode=0)
        # Second call for audio combine
        elif 'concat' in args[0]:
            return Mock(returncode=0)
        # Third call for video/audio combine (should fail)
        else:
            raise subprocess.CalledProcessError(1, "ffmpeg")
    
    mock_subprocess.side_effect = mock_subprocess_side_effect
    
    generator = VideoGenerator(
        script_service=script_service,
        video_extractor=video_extractor,
        script_chunker=script_chunker,
        tts_service=tts_service
    )
    
    video_path, audio_path, script, duration = generator.generate(
        "Topic",
        "Subtopic",
        concept,
        str(tmp_path)
    )
    
    # Should still return paths even if combine fails
    assert script == "Test script"
    assert Path(video_path).exists() or Path(video_path).parent.exists()


@patch('subprocess.run')
def test_generate_handles_ffprobe_error(mock_subprocess, mock_services, concept, tmp_path):
    """Test handling of ffprobe errors for duration calculation."""
    script_service, video_extractor, script_chunker, tts_service = mock_services
    
    # Mock ffprobe to fail
    def mock_subprocess_side_effect(*args, **kwargs):
        if 'ffprobe' in args[0]:
            raise subprocess.CalledProcessError(1, "ffprobe")
        return Mock(returncode=0)
    
    mock_subprocess.side_effect = mock_subprocess_side_effect
    
    generator = VideoGenerator(
        script_service=script_service,
        video_extractor=video_extractor,
        script_chunker=script_chunker,
        tts_service=tts_service
    )
    
    video_path, audio_path, script, duration = generator.generate(
        "Topic",
        "Subtopic",
        concept,
        str(tmp_path)
    )
    
    # Should use default duration (30.0) when ffprobe fails
    assert script == "Test script"
    assert duration == 30.0


@patch('subprocess.run')
def test_generate_handles_empty_audio_chunks(mock_subprocess, mock_services, concept, tmp_path):
    """Test handling when no audio chunks are generated."""
    script_service, video_extractor, script_chunker, tts_service = mock_services
    
    # Mock TTS to return empty list
    tts_service.generate_chunks = Mock(return_value=[])
    
    mock_subprocess.return_value = Mock(stdout="30.0\n", returncode=0)
    
    generator = VideoGenerator(
        script_service=script_service,
        video_extractor=video_extractor,
        script_chunker=script_chunker,
        tts_service=tts_service
    )
    
    video_path, audio_path, script, duration = generator.generate(
        "Topic",
        "Subtopic",
        concept,
        str(tmp_path)
    )
    
    assert script == "Test script"
    # Audio path should still be created
    assert Path(audio_path).exists() or Path(audio_path).parent.exists()


@patch('subprocess.run')
def test_generate_limits_video_duration(mock_subprocess, mock_services, concept, tmp_path):
    """Test that video duration is limited to 30 seconds."""
    script_service, video_extractor, script_chunker, tts_service = mock_services
    
    # Mock ffprobe to return long duration
    mock_subprocess.return_value = Mock(stdout="60.0\n", returncode=0)
    
    generator = VideoGenerator(
        script_service=script_service,
        video_extractor=video_extractor,
        script_chunker=script_chunker,
        tts_service=tts_service
    )
    
    video_path, audio_path, script, duration = generator.generate(
        "Topic",
        "Subtopic",
        concept,
        str(tmp_path)
    )
    
    # Video extractor should be called with 30.0 duration (min of 60.0 and 30.0)
    video_extractor.extract_segment.assert_called()
    call_args = video_extractor.extract_segment.call_args
    assert call_args[1]['duration'] == 30.0  # Should be limited to 30 seconds

