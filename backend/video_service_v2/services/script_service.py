"""Script generation service."""
import json
import random
import re
from pathlib import Path
from backend.shared.services.llm.mistral_client import MistralClient
from backend.shared.services.llm.prompts import VIDEO_SCRIPT_PROMPT
from backend.course_service.models.course import Concept

BACKEND_ROOT = Path(__file__).parent.parent.parent


class ScriptService:
    """Generate video scripts."""
    
    def __init__(self, mistral_client: MistralClient | None = None):
        """Initialize script service."""
        self.client = mistral_client or MistralClient()
    
    def _load_parsed_data(self) -> dict:
        """Load parsed_data.json."""
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        if not parsed_data_file.exists():
            raise FileNotFoundError(f"parsed_data.json not found at {parsed_data_file}")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _extract_topics_subtopics_concepts(self) -> dict:
        """Extract topics, subtopics, and concepts from parsed_data.json.
        
        Returns:
            Dictionary with structure: {
                topic_name: {
                    subtopic_name: [concept_names]
                }
            }
        """
        parsed_data = self._load_parsed_data()
        structure = {}
        
        for file_path, file_data in parsed_data.items():
            quiz_questions = file_data.get("quiz", [])
            summary = file_data.get("summary", "")
            
            for question in quiz_questions:
                topic = question.get("topic", "")
                subtopic = question.get("subtopic", "")
                concepts = question.get("concepts", [])
                
                if not topic or not subtopic or not concepts:
                    continue
                
                if topic not in structure:
                    structure[topic] = {}
                
                if subtopic not in structure[topic]:
                    structure[topic][subtopic] = []
                
                for concept_name in concepts:
                    if concept_name not in structure[topic][subtopic]:
                        structure[topic][subtopic].append(concept_name)
        
        return structure
    
    def _get_concept_description(self, concept_name: str, topic: str) -> str:
        """Get concept description from parsed_data.json."""
        parsed_data = self._load_parsed_data()
        
        # Try to find concept in quiz questions or summaries
        for file_path, file_data in parsed_data.items():
            quiz_questions = file_data.get("quiz", [])
            summary = file_data.get("summary", "")
            
            # Check if this file has questions for this topic/concept
            for question in quiz_questions:
                if question.get("topic") == topic and concept_name in question.get("concepts", []):
                    # Use summary if available, otherwise use a default description
                    if summary:
                        return f"{summary[:500]}..." if len(summary) > 500 else summary
                    return f"Concept from {topic} topic"
        
        return f"Concept: {concept_name} from {topic}"
    
    def select_random(self) -> tuple[str, str, Concept]:
        """Select a random topic, subtopic, and concept from parsed_data.json.
        
        Returns:
            Tuple of (topic, subtopic, concept)
        """
        structure = self._extract_topics_subtopics_concepts()
        
        if not structure:
            raise ValueError("No topics found in parsed_data.json")
        
        # Select random topic
        topic = random.choice(list(structure.keys()))
        
        # Select random subtopic from topic
        subtopics = list(structure[topic].keys())
        if not subtopics:
            raise ValueError(f"No subtopics found for topic: {topic}")
        subtopic = random.choice(subtopics)
        
        # Select random concept from subtopic
        concepts = structure[topic][subtopic]
        if not concepts:
            raise ValueError(f"No concepts found for topic: {topic}, subtopic: {subtopic}")
        concept_name = random.choice(concepts)
        
        # Get concept description
        concept_description = self._get_concept_description(concept_name, topic)
        
        concept = Concept(
            name=concept_name,
            description=concept_description
        )
        
        return topic, subtopic, concept
    
    def generate(self, topic: str | None = None, subtopic: str | None = None, concept: Concept | None = None) -> str:
        """Generate script for a concept.
        
        Args:
            topic: Topic name (if None, randomly selected)
            subtopic: Subtopic name (if None, randomly selected)
            concept: Concept object (if None, randomly selected)
            
        Returns:
            Generated script text
        """
        # If any parameter is None, select randomly
        if topic is None or subtopic is None or concept is None:
            topic, subtopic, concept = self.select_random()
        
        script = self.client.generate_with_template(
            VIDEO_SCRIPT_PROMPT,
            topic=topic,
            subtopic=subtopic,
            concept_name=concept.name,
            concept_description=concept.description
        )
        return self._clean_script(script)
    
    def _clean_script(self, script: str) -> str:
        """Clean script by removing markdown, formatting, and extra text.
        
        Args:
            script: Raw script text from LLM
            
        Returns:
            Cleaned script text
        """
        # Remove markdown formatting
        script = re.sub(r'\*\*([^*]+)\*\*', r'\1', script)  # Bold
        script = re.sub(r'\*([^*]+)\*', r'\1', script)  # Italic
        script = re.sub(r'#+\s*', '', script)  # Headers
        script = re.sub(r'```.*?```', '', script, flags=re.DOTALL)  # Code blocks
        
        # Remove common introductory phrases and labels
        intro_patterns = [
            r'^.*?(?:script|here.*?script|script:).*?\n',
            r'^Sure!?\s*',
            r'^Here.*?:?\s*',
            r'^\s*---\s*$',
        ]
        for pattern in intro_patterns:
            script = re.sub(pattern, '', script, flags=re.IGNORECASE | re.MULTILINE)
        
        # Try to extract content between quotes if present (but prefer full content)
        # Look for triple-quoted strings first (more likely to contain full script)
        triple_quote_match = re.search(r'"""([^"]+)"""', script, re.DOTALL)
        if triple_quote_match:
            script = triple_quote_match.group(1)
        else:
            # Try single quotes
            single_quote_match = re.search(r"'([^']+)'", script, re.DOTALL)
            if single_quote_match and len(single_quote_match.group(1)) > 100:
                script = single_quote_match.group(1)
            else:
                # Try double quotes
                double_quote_match = re.search(r'"([^"]+)"', script, re.DOTALL)
                if double_quote_match and len(double_quote_match.group(1)) > 100:
                    script = double_quote_match.group(1)
        
        # Remove leading/trailing whitespace and normalize
        script = script.strip()
        script = re.sub(r'\n\s*\n\s*\n+', '\n\n', script)  # Multiple newlines to double
        script = re.sub(r'^\s*---\s*$', '', script, flags=re.MULTILINE)  # Remove separator lines
        
        return script.strip()

