"""Course material JSON loader with validation."""
import json
from pathlib import Path
from typing import Optional
from src.models.course import CourseStructure


class CourseLoader:
    """Load and validate course material from JSON."""
    
    @staticmethod
    def load_from_file(file_path: str) -> CourseStructure:
        """Load course material from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Validated CourseStructure
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid or doesn't match schema
        """
        if isinstance(file_path, Path):
            path = file_path
        else:
            path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Course material file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        try:
            course = CourseStructure(**data)
            return course
        except Exception as e:
            raise ValueError(f"Invalid course material format: {e}")
    
    @staticmethod
    def load_from_dict(data: dict) -> CourseStructure:
        """Load course material from dictionary.
        
        Args:
            data: Course data dictionary
            
        Returns:
            Validated CourseStructure
        """
        return CourseStructure(**data)
    
    @staticmethod
    def create_sample_course() -> CourseStructure:
        """Create a sample course for testing/demo.
        
        Returns:
            Sample CourseStructure
        """
        sample_data = {
            "title": "Introduction to Python Programming",
            "description": "Learn the fundamentals of Python programming",
            "topics": [
                {
                    "name": "Python Basics",
                    "description": "Core Python syntax and concepts",
                    "subtopics": [
                        {
                            "name": "Variables and Data Types",
                            "description": "Understanding variables and basic data types",
                            "concepts": [
                                {
                                    "name": "Variables",
                                    "description": "Variables are containers for storing data values",
                                    "keywords": ["assignment", "naming", "dynamic typing"]
                                },
                                {
                                    "name": "Strings",
                                    "description": "Text data type in Python",
                                    "keywords": ["text", "quotes", "immutable", "methods"]
                                },
                                {
                                    "name": "Numbers",
                                    "description": "Integer and float data types",
                                    "keywords": ["int", "float", "arithmetic", "operations"]
                                }
                            ],
                            "content": "Python variables are created by assignment. Data types include strings, integers, floats, and more."
                        },
                        {
                            "name": "Control Flow",
                            "description": "If statements, loops, and control structures",
                            "concepts": [
                                {
                                    "name": "If Statements",
                                    "description": "Conditional execution of code blocks",
                                    "keywords": ["if", "elif", "else", "conditions", "boolean"]
                                },
                                {
                                    "name": "For Loops",
                                    "description": "Iteration over sequences",
                                    "keywords": ["for", "iteration", "range", "iterable"]
                                },
                                {
                                    "name": "While Loops",
                                    "description": "Conditional repetition",
                                    "keywords": ["while", "condition", "break", "continue"]
                                }
                            ],
                            "content": "Control flow statements allow you to control the execution path of your program."
                        }
                    ]
                },
                {
                    "name": "Data Structures",
                    "description": "Python's built-in data structures",
                    "subtopics": [
                        {
                            "name": "Lists",
                            "description": "Ordered, mutable collections",
                            "concepts": [
                                {
                                    "name": "List Basics",
                                    "description": "Creating and accessing lists",
                                    "keywords": ["list", "indexing", "slicing", "mutable"]
                                },
                                {
                                    "name": "List Methods",
                                    "description": "Common list operations",
                                    "keywords": ["append", "extend", "insert", "remove", "pop"]
                                }
                            ],
                            "content": "Lists are versatile, ordered collections that can hold items of different types."
                        },
                        {
                            "name": "Dictionaries",
                            "description": "Key-value pair collections",
                            "concepts": [
                                {
                                    "name": "Dictionary Basics",
                                    "description": "Creating and using dictionaries",
                                    "keywords": ["dict", "key", "value", "mapping"]
                                },
                                {
                                    "name": "Dictionary Methods",
                                    "description": "Common dictionary operations",
                                    "keywords": ["keys", "values", "items", "get", "update"]
                                }
                            ],
                            "content": "Dictionaries store data in key-value pairs for fast lookup."
                        }
                    ]
                }
            ]
        }
        return CourseStructure(**sample_data)

