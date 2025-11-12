"""Course material data models."""
from typing import List, Optional
from pydantic import BaseModel, Field


class Concept(BaseModel):
    """A key concept within a subtopic."""
    name: str
    description: str
    keywords: List[str] = Field(default_factory=list)


class Subtopic(BaseModel):
    """A subtopic within a topic."""
    name: str
    description: str
    concepts: List[Concept] = Field(default_factory=list)
    content: Optional[str] = None


class Topic(BaseModel):
    """A main topic in the course."""
    name: str
    description: str
    subtopics: List[Subtopic] = Field(default_factory=list)


class CourseStructure(BaseModel):
    """Complete course material structure."""
    title: str
    description: str
    topics: List[Topic]
    
    def get_all_concepts(self) -> List[tuple[str, str, Concept]]:
        """Get all concepts with their topic and subtopic names."""
        concepts = []
        for topic in self.topics:
            for subtopic in topic.subtopics:
                for concept in subtopic.concepts:
                    concepts.append((topic.name, subtopic.name, concept))
        return concepts

