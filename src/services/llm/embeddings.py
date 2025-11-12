"""Semantic similarity using embeddings and cosine similarity."""
import numpy as np
from typing import List, Tuple, Optional
from mistralai import Mistral
from src.utils.config import Config


class EmbeddingsService:
    """Service for computing embeddings and semantic similarity."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize embeddings service.
        
        Args:
            api_key: Mistral API key (defaults to Config.MISTRAL_API_KEY)
        """
        self.client = Mistral(api_key=api_key or Config.MISTRAL_API_KEY)
        self.model = "mistral-embed"
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        response = self.client.embeddings.create(
            model=self.model,
            inputs=[text]
        )
        return np.array(response.data[0].embedding)
    
    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        response = self.client.embeddings.create(
            model=self.model,
            inputs=texts
        )
        return [np.array(item.embedding) for item in response.data]
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_most_similar(
        self, 
        query: str, 
        candidates: List[str]
    ) -> List[Tuple[str, float]]:
        """Find most similar candidates to query using cosine similarity.
        
        Args:
            query: Query text
            candidates: List of candidate texts
            
        Returns:
            List of (candidate, similarity_score) tuples, sorted by similarity (highest first)
        """
        if not candidates:
            return []
        
        query_embedding = self.get_embedding(query)
        candidate_embeddings = self.get_embeddings_batch(candidates)
        
        similarities = []
        for candidate, candidate_embedding in zip(candidates, candidate_embeddings):
            similarity = self.cosine_similarity(query_embedding, candidate_embedding)
            similarities.append((candidate, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities

