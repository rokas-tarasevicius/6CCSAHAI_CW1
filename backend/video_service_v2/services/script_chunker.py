"""Script chunking service."""
from typing import List


class ScriptChunker:
    """Chunk scripts into time-based segments."""
    
    def __init__(self, chunk_duration: float = 3.0, words_per_minute: int = 150):
        """Initialize script chunker.
        
        Args:
            chunk_duration: Duration of each chunk in seconds (default: 3.0 for subtitles)
            words_per_minute: Average speaking rate (default: 150)
        """
        self.chunk_duration = chunk_duration
        self.words_per_second = words_per_minute / 60.0
    
    def chunk(self, script: str) -> List[str]:
        """Chunk script into time-based segments.
        
        Args:
            script: Script text
            
        Returns:
            List of script chunks
        """
        words = script.split()
        words_per_chunk = int(self.chunk_duration * self.words_per_second)
        
        chunks = []
        for i in range(0, len(words), words_per_chunk):
            chunk = " ".join(words[i:i + words_per_chunk])
            chunks.append(chunk)
        
        return chunks

