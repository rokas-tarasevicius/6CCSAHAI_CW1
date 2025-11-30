"""Tests for video extractor."""
import pytest
import os
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from backend.video_service_v2.services.video_extractor import VideoExtractor


@pytest.fixture
def mock_source_path(tmp_path):
    """Create mock source video path."""
    source = tmp_path / "source.mp4"
    source.touch()
    return str(source)


def test_init_with_custom_path(mock_source_path):
    """Test initialization with custom path."""
    extractor = VideoExtractor(mock_source_path)
    assert extractor.source_path == Path(mock_source_path)


def test_init_with_default_path():
    """Test initialization with default path."""
    backend_root = Path(__file__).parent.parent.parent.parent
    expected_path = backend_root / "video_service" / "assets" / "minecraft_source_pre_scaled.mp4"
    
    with patch.object(Path, 'exists', return_value=True):
        extractor = VideoExtractor()
        assert extractor.source_path == expected_path


def test_init_file_not_found():
    """Test initialization when file doesn't exist."""
    with patch.object(Path, 'exists', return_value=False):
        with pytest.raises(FileNotFoundError):
            VideoExtractor("nonexistent.mp4")


@patch('subprocess.run')
def test_extract_segment_success(mock_subprocess, mock_source_path, tmp_path):
    """Test successful video extraction."""
    mock_subprocess.return_value = Mock(returncode=0)
    output_path = tmp_path / "output.mp4"
    
    extractor = VideoExtractor(mock_source_path)
    result = extractor.extract_segment(str(output_path), duration=30.0)
    
    assert result is True
    mock_subprocess.assert_called_once()


@patch('subprocess.run')
def test_extract_segment_ffmpeg_unavailable(mock_subprocess, mock_source_path, tmp_path):
    """Test extraction when ffmpeg is unavailable."""
    mock_subprocess.side_effect = FileNotFoundError()
    output_path = tmp_path / "output.mp4"
    
    extractor = VideoExtractor(mock_source_path)
    result = extractor.extract_segment(str(output_path), duration=30.0)
    
    assert result is False
    assert output_path.exists()


@patch('subprocess.run')
def test_extract_segment_creates_output_directory(mock_subprocess, mock_source_path, tmp_path):
    """Test that output directory is created if it doesn't exist."""
    mock_subprocess.return_value = Mock(returncode=0)
    output_dir = tmp_path / "nested" / "deep" / "path"
    output_path = output_dir / "output.mp4"
    
    extractor = VideoExtractor(mock_source_path)
    result = extractor.extract_segment(str(output_path), duration=30.0)
    
    assert result is True
    assert output_dir.exists()
    assert output_dir.is_dir()


@patch('subprocess.run')
def test_extract_segment_with_custom_start_time(mock_subprocess, mock_source_path, tmp_path):
    """Test extraction with custom start time."""
    mock_subprocess.return_value = Mock(returncode=0)
    output_path = tmp_path / "output.mp4"
    
    extractor = VideoExtractor(mock_source_path)
    result = extractor.extract_segment(str(output_path), duration=15.0, start_time=10.0)
    
    assert result is True
    # Verify ffmpeg was called with correct start time
    call_args = mock_subprocess.call_args[0][0]
    assert "-ss" in call_args
    assert "10.0" in call_args
    assert "-t" in call_args
    assert "15.0" in call_args


@patch('subprocess.run')
def test_extract_segment_ffmpeg_error_handling(mock_subprocess, mock_source_path, tmp_path):
    """Test handling of ffmpeg errors."""
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "ffmpeg")
    output_path = tmp_path / "output.mp4"
    
    extractor = VideoExtractor(mock_source_path)
    result = extractor.extract_segment(str(output_path), duration=30.0)
    
    assert result is False
    # Should still create output file as fallback
    assert output_path.exists()


def test_extract_segment_file_permissions_read_source(mock_source_path, tmp_path):
    """Test that source file is readable."""
    extractor = VideoExtractor(mock_source_path)
    
    # Check source file permissions
    source_path = Path(mock_source_path)
    assert source_path.exists()
    assert os.access(source_path, os.R_OK), "Source file should be readable"


@patch('subprocess.run')
def test_extract_segment_file_permissions_write_output(mock_subprocess, mock_source_path, tmp_path):
    """Test that output directory is writable."""
    mock_subprocess.return_value = Mock(returncode=0)
    output_path = tmp_path / "output.mp4"
    
    extractor = VideoExtractor(mock_source_path)
    
    # Check output directory permissions
    output_dir = output_path.parent
    assert os.access(output_dir, os.W_OK), "Output directory should be writable"
    
    result = extractor.extract_segment(str(output_path), duration=30.0)
    
    assert result is True


@patch('subprocess.run')
def test_extract_segment_nested_directory_creation(mock_subprocess, mock_source_path, tmp_path):
    """Test creation of nested output directories."""
    mock_subprocess.return_value = Mock(returncode=0)
    nested_path = tmp_path / "level1" / "level2" / "level3" / "output.mp4"
    
    extractor = VideoExtractor(mock_source_path)
    result = extractor.extract_segment(str(nested_path), duration=30.0)
    
    assert result is True
    assert nested_path.parent.exists()
    assert nested_path.parent.is_dir()


def test_extract_segment_zero_duration(mock_source_path, tmp_path):
    """Test extraction with zero duration."""
    output_path = tmp_path / "output.mp4"
    extractor = VideoExtractor(mock_source_path)
    
    with patch('subprocess.run') as mock_subprocess:
        mock_subprocess.return_value = Mock(returncode=0)
        result = extractor.extract_segment(str(output_path), duration=0.0)
        
        assert result is True
        call_args = mock_subprocess.call_args[0][0]
        assert "-t" in call_args
        assert "0.0" in call_args


def test_extract_segment_negative_duration(mock_source_path, tmp_path):
    """Test extraction with negative duration."""
    output_path = tmp_path / "output.mp4"
    extractor = VideoExtractor(mock_source_path)
    
    with patch('subprocess.run') as mock_subprocess:
        mock_subprocess.return_value = Mock(returncode=0)
        result = extractor.extract_segment(str(output_path), duration=-5.0)
        
        # Should still attempt extraction (ffmpeg will handle validation)
        assert result is True

