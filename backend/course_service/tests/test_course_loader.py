"""Unit tests for course loader."""
import pytest
import json
from pathlib import Path
from backend.course_service.services.course_loader import CourseLoader
from backend.course_service.models.course import CourseStructure


class TestCourseLoader:
    """Test course loading functionality."""
    
    def test_create_sample_course(self):
        """Test creating a sample course."""
        course = CourseLoader.create_sample_course()
        
        assert isinstance(course, CourseStructure)
        assert course.title == "Introduction to Python Programming"
        assert len(course.topics) > 0
    
    def test_load_from_dict(self):
        """Test loading course from dictionary."""
        data = {
            "title": "Test Course",
            "description": "A test course",
            "topics": [
                {
                    "name": "Test Topic",
                    "description": "Test",
                    "subtopics": [
                        {
                            "name": "Test Subtopic",
                            "description": "Test",
                            "concepts": [
                                {
                                    "name": "Test Concept",
                                    "description": "Test",
                                    "keywords": ["test"]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        course = CourseLoader.load_from_dict(data)
        assert course.title == "Test Course"
        assert len(course.topics) == 1
    
    def test_load_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            CourseLoader.load_from_file("nonexistent.json")
    
    def test_load_from_file_invalid_json(self, tmp_path):
        """Test loading from invalid JSON file."""
        # Create invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json")
        
        with pytest.raises(Exception):
            CourseLoader.load_from_file(str(invalid_file))

