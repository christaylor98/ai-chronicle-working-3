"""
Semantic similarity utilities for node comparison and deduplication.
"""

import numpy as np
from typing import List, Tuple, Optional

# Lazy import to allow system to work without sentence-transformers
_sentence_transformer_available = False
_SentenceTransformer = None

try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
    _sentence_transformer_available = True
except (ImportError, AttributeError) as e:
    # sentence-transformers not available or has dependency issues
    pass


class SimilarityEngine:
    """
    Semantic similarity computation for atomic node deduplication.
    
    Uses sentence transformers if available, falls back to basic text similarity.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize similarity engine.
        
        Args:
            model_name: HuggingFace model for sentence embeddings (if available)
        """
        self.model = None
        self._cache = {}
        self._use_semantic = _sentence_transformer_available
        
        if self._use_semantic and _SentenceTransformer is not None:
            try:
                self.model = _SentenceTransformer(model_name)
            except Exception as e:
                print(f"Warning: Could not load sentence transformer model: {e}")
                print("Falling back to basic text similarity")
                self._use_semantic = False
        elif not self._use_semantic:
            print("Warning: sentence-transformers not available. Using basic text similarity.")
            print("Install with: pip install sentence-transformers>=2.2.0")
    
    def encode(self, text: str) -> np.ndarray:
        """Get embedding for text with caching."""
        if text in self._cache:
            return self._cache[text]
        
        if self._use_semantic and self.model is not None:
            embedding = self.model.encode(text, convert_to_numpy=True)
        else:
            # Basic fallback: TF-IDF-like vector from bag of words
            embedding = self._basic_encode(text)
        
        self._cache[text] = embedding
        return embedding
    
    def _basic_encode(self, text: str) -> np.ndarray:
        """Simple bag-of-words encoding as fallback."""
        # Tokenize and create basic vector
        words = text.lower().split()
        # Use hash-based indexing to create a fixed-size vector
        vocab_size = 1000
        vector = np.zeros(vocab_size)
        
        for word in words:
            idx = hash(word) % vocab_size
            vector[idx] += 1
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Returns:
            Similarity score in range [0.0, 1.0]
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        # Ensure range [0, 1]
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))
    
    def find_similar(
        self, query: str, statements: List[str], threshold: float = 0.85
    ) -> List[Tuple[int, float]]:
        """
        Find statements similar to query above threshold.
        
        Args:
            query: Target statement
            statements: Candidate statements to compare
            threshold: Minimum similarity score
        
        Returns:
            List of (index, similarity) tuples sorted by similarity descending
        """
        if not statements:
            return []
        
        query_emb = self.encode(query)
        candidates = []
        
        for idx, stmt in enumerate(statements):
            stmt_emb = self.encode(stmt)
            similarity = np.dot(query_emb, stmt_emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(stmt_emb)
            )
            similarity = float(max(0.0, min(1.0, (similarity + 1) / 2)))
            
            if similarity >= threshold:
                candidates.append((idx, similarity))
        
        # Sort by similarity descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
    
    def compute_pairwise_similarities(
        self, statements: List[str], threshold: float = 0.85
    ) -> List[Tuple[int, int, float]]:
        """
        Compute all pairwise similarities above threshold.
        
        Returns:
            List of (idx1, idx2, similarity) tuples
        """
        if len(statements) < 2:
            return []
        
        # Encode all statements
        embeddings = [self.encode(stmt) for stmt in statements]
        
        pairs = []
        for i in range(len(statements)):
            for j in range(i + 1, len(statements)):
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
                similarity = float(max(0.0, min(1.0, (similarity + 1) / 2)))
                
                if similarity >= threshold:
                    pairs.append((i, j, similarity))
        
        return pairs
