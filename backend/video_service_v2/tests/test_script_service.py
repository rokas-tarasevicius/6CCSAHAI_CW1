"""Tests for script service."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from backend.video_service_v2.services.script_service import ScriptService
from backend.course_service.models.course import Concept


@pytest.fixture
def mock_mistral_client():
    """Create mock Mistral client."""
    client = Mock()
    client.generate_with_template = Mock(return_value="Generated script text")
    return client


@pytest.fixture
def concept():
    """Create test concept."""
    return Concept(
        name="Test Concept",
        description="Test description",
        keywords=["test", "concept"]
    )


def test_generate_script(mock_mistral_client, concept):
    """Test script generation."""
    service = ScriptService(mock_mistral_client)
    script = service.generate("Topic", "Subtopic", concept)
    
    assert script == "Generated script text"
    mock_mistral_client.generate_with_template.assert_called_once()


def test_generate_script_default_client(concept):
    """Test script generation with default client."""
    with patch('backend.video_service_v2.services.script_service.MistralClient') as mock_client_class:
        mock_client = Mock()
        mock_client.generate_with_template = Mock(return_value="Generated script")
        mock_client_class.return_value = mock_client
        
        service = ScriptService()
        script = service.generate("Topic", "Subtopic", concept)
        
        assert script == "Generated script"


def test_select_random(mock_mistral_client):
    """Test random selection from parsed_data.json."""
    service = ScriptService(mock_mistral_client)
    
    # Check if parsed_data.json exists (using same path calculation as service)
    # Test file: backend/video_service_v2/tests/test_script_service.py
    # Service file: backend/video_service_v2/services/script_service.py
    # Service BACKEND_ROOT = backend/
    # So from test, we need: project_root / backend / course_service / data / parsed_data.json
    project_root = Path(__file__).parent.parent.parent.parent
    parsed_data_file = project_root / "backend" / "course_service" / "data" / "parsed_data.json"
    
    if not parsed_data_file.exists():
        pytest.skip("parsed_data.json not found, skipping test")
    
    # Test select_random
    topic, subtopic, concept = service.select_random()
    
    assert isinstance(topic, str)
    assert isinstance(subtopic, str)
    assert isinstance(concept, Concept)
    assert concept.name
    assert concept.description


def test_generate_with_random_selection(mock_mistral_client):
    """Test generate with random selection."""
    service = ScriptService(mock_mistral_client)
    
    # Check if parsed_data.json exists (using same path calculation as service)
    # Test file: backend/video_service_v2/tests/test_script_service.py
    # Service file: backend/video_service_v2/services/script_service.py
    # Service BACKEND_ROOT = backend/
    # So from test, we need: project_root / backend / course_service / data / parsed_data.json
    project_root = Path(__file__).parent.parent.parent.parent
    parsed_data_file = project_root / "backend" / "course_service" / "data" / "parsed_data.json"
    
    if not parsed_data_file.exists():
        pytest.skip("parsed_data.json not found, skipping test")
    
    # Test generate with None parameters (should trigger random selection)
    script = service.generate()
    
    assert script == "Generated script text"
    mock_mistral_client.generate_with_template.assert_called_once()

