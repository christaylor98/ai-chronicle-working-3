"""
Semantic similarity utilities for node comparison and deduplication.
"""

import numpy as np
from typing import List, Tuple, Optional

# Lazy import to allow system to work without fastembed
_fastembed_available = False
_TextEmbedding = None

try:
    from fastembed import TextEmbedding as _TextEmbedding
    _fastembed_available = True
except (ImportError, AttributeError):
    pass


class SimilarityEngine:
    """
    Semantic similarity computation for atomic node deduplication.

    Uses fastembed if available, falls back to basic text similarity.

    UPGRADE NOTES (v1.3):
    - Upgraded from BAAI/bge-small-en-v1.5 (384d) to BAAI/bge-base-en-v1.5 (768d)
      per EMBEDDING_MODEL_UPGRADE_SPEC.v1.0
    - bge-base provides higher-fidelity semantic discrimination between topically
      distinct but surface-similar statements (~110MB vs ~67MB, still ONNX-based)
    - Embedding dimension increases from 384 to 768 (automatic, transparent)
    - Cache invalidation: in-memory _cache is cleared on engine restart
    - All cosine similarity logic and fallback BOW behaviour unchanged
    - Drop-in replacement: no API surface changes required

    UPGRADE NOTES (v1.2):
    - Replaced sentence-transformers with fastembed (BAAI/bge-small-en-v1.5).
      fastembed uses ONNX runtime instead of PyTorch — ~67MB vs ~1GB, no CUDA
      required, and produces unit-norm embeddings identical in behaviour to
      the previous all-MiniLM-L6-v2 setup.
    - fastembed.embed() returns a generator; batch encoding collects via list().
    - normalize_embeddings is implicit in fastembed — no flag needed.
    - All cosine similarity logic and fallback BOW behaviour is unchanged.
    """

    # Stopwords to exclude from fallback BOW vectors
    _STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above", "below",
        "and", "but", "or", "nor", "so", "yet", "both", "either", "neither",
        "not", "no", "that", "this", "these", "those", "it", "its", "their",
        "they", "he", "she", "we", "i", "you", "who", "which", "what",
        "than", "then", "when", "where", "how", "all", "each", "every",
        "some", "any", "most", "more", "other", "such", "only", "also",
        "there", "here", "up", "out", "about", "over", "just", "very",
    }

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        """
        Initialize similarity engine.

        Args:
            model_name: fastembed model name for sentence embeddings (if available).
                        BAAI/bge-base-en-v1.5 (768d, ~110MB) provides superior semantic
                        discrimination compared to bge-small (384d, ~67MB) while remaining
                        efficient via ONNX runtime. Produces unit-norm embeddings ideal
                        for cosine similarity.
        """
        self.model = None
        self._cache: dict = {}
        self._use_semantic = _fastembed_available

        if self._use_semantic and _TextEmbedding is not None:
            try:
                self.model = _TextEmbedding(model_name)
                # Warm up to catch load errors early
                list(self.model.embed(["warmup"]))
            except Exception as e:
                print(f"Warning: Could not load fastembed model: {e}")
                print("Falling back to basic text similarity.")
                self._use_semantic = False
        elif not self._use_semantic:
            print("Warning: fastembed not available. Using basic text similarity.")
            print("Install with: pip install fastembed")

        # Fallback vocabulary built lazily per batch
        self._vocab: dict = {}

    # ------------------------------------------------------------------
    # Encoding
    # ------------------------------------------------------------------

    def encode(self, text: str) -> np.ndarray:
        """Get embedding for text with caching."""
        if text in self._cache:
            return self._cache[text]

        if self._use_semantic and self.model is not None:
            # fastembed.embed() returns a generator — take the first (and only) result
            embedding = next(iter(self.model.embed([text])))
            embedding = np.array(embedding, dtype=np.float32)
        else:
            embedding = self._basic_encode(text)

        self._cache[text] = embedding
        return embedding

    def _basic_encode(self, text: str) -> np.ndarray:
        """
        Stopword-filtered term-frequency vector as fallback.

        Unlike the previous hash-collision approach, this builds a shared
        vocabulary across all encoded texts so cosine distances are
        semantically meaningful rather than structurally inflated.
        """
        tokens = [w for w in text.lower().split() if w not in self._STOPWORDS and len(w) > 1]

        # Register new tokens in shared vocabulary
        for token in tokens:
            if token not in self._vocab:
                self._vocab[token] = len(self._vocab)

        if not self._vocab:
            return np.zeros(1)

        vector = np.zeros(len(self._vocab))
        for token in tokens:
            if token in self._vocab:
                vector[self._vocab[token]] += 1

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def _invalidate_cache(self):
        """
        Invalidate encoding cache when vocabulary grows.
        Called automatically during batch encode to keep vectors consistent.
        """
        self._cache.clear()

    # ------------------------------------------------------------------
    # Similarity computation
    # ------------------------------------------------------------------

    def _cosine(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Raw cosine similarity clamped to [0, 1].

        For semantic mode (unit-norm vectors): dot product IS cosine similarity.
        For fallback mode (unit-norm term vectors): same formula applies.

        Note: The previous (similarity + 1) / 2 rescaling was intended to map
        [-1, 1] → [0, 1] but incorrectly compressed the meaningful range for
        unit-norm vectors, causing all pairs to cluster around 0.5–0.75
        regardless of actual semantic distance. Raw clamp is correct here.
        """
        n1 = np.linalg.norm(emb1)
        n2 = np.linalg.norm(emb2)
        if n1 == 0 or n2 == 0:
            return 0.0
        similarity = float(np.dot(emb1, emb2) / (n1 * n2))
        return max(0.0, min(1.0, similarity))

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.

        Returns:
            Similarity score in range [0.0, 1.0]
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        return self._cosine(emb1, emb2)

    # ------------------------------------------------------------------
    # Batch operations
    # ------------------------------------------------------------------

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

        # For fallback mode, encode all at once to build shared vocabulary first
        if not self._use_semantic:
            all_texts = [query] + statements
            self._invalidate_cache()
            for text in all_texts:
                self.encode(text)
            # Re-encode with stable vocabulary
            self._invalidate_cache()

        query_emb = self.encode(query)
        candidates = []

        for idx, stmt in enumerate(statements):
            stmt_emb = self.encode(stmt)
            similarity = self._cosine(query_emb, stmt_emb)
            if similarity >= threshold:
                candidates.append((idx, similarity))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def compute_pairwise_similarities(
        self, statements: List[str], threshold: float = 0.85
    ) -> List[Tuple[int, int, float]]:
        """
        Compute all pairwise similarities above threshold.

        DEPRECATED: Use compute_topk_similarities for ingestion.
        This method applies semantic cutoffs which violate MEASUREMENT_SPEC v1.0.

        Returns:
            List of (idx1, idx2, similarity) tuples
        """
        if len(statements) < 2:
            return []

        embeddings = self._batch_encode(statements)
        pairs = []

        for i in range(len(statements)):
            for j in range(i + 1, len(statements)):
                similarity = self._cosine(embeddings[i], embeddings[j])
                if similarity >= threshold:
                    pairs.append((i, j, similarity))

        return pairs

    def compute_topk_similarities(
        self, statements: List[str], k: int = 10
    ) -> List[Tuple[int, int, float]]:
        """
        Compute top-K most similar neighbors for each statement.

        Per INGESTION_SIMILARITY_MEASUREMENT_SPEC.v1.0:
        - No global threshold filtering during ingestion
        - Store bounded measurements (top-K per node)
        - Preserve reversibility by not discarding similarity data
        - Maintain symmetry: if A→B exists, ensure B→A exists

        This prevents n^2 explosion while preserving measurement semantics.
        Projection layer applies thresholds, not ingestion layer.

        Args:
            statements: List of statements to compare
            k: Maximum number of neighbors to retain per statement

        Returns:
            List of (idx1, idx2, similarity) tuples for symmetric top-K pairs
        """
        if len(statements) < 2:
            return []

        embeddings = self._batch_encode(statements)
        n = len(statements)

        # Compute upper-triangle similarity matrix
        similarity_matrix: dict = {}
        for i in range(n):
            for j in range(i + 1, n):
                similarity_matrix[(i, j)] = self._cosine(embeddings[i], embeddings[j])

        # For each node, select top-K neighbors
        selected_pairs: set = set()

        for idx in range(n):
            neighbors = []
            for i in range(n):
                if i == idx:
                    continue
                key = (min(idx, i), max(idx, i))
                sim = similarity_matrix.get(key, 0.0)
                neighbors.append((i, sim))

            neighbors.sort(key=lambda x: x[1], reverse=True)
            top_k = neighbors[:k]

            for neighbor_idx, sim in top_k:
                pair = (min(idx, neighbor_idx), max(idx, neighbor_idx))
                selected_pairs.add((pair[0], pair[1], sim))

        return sorted(list(selected_pairs))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _batch_encode(self, statements: List[str]) -> List[np.ndarray]:
        """
        Encode a batch of statements efficiently.

        For semantic mode: uses fastembed batch inference (faster than one-by-one).
        For fallback mode: builds shared vocabulary first, then encodes.
        """
        if self._use_semantic and self.model is not None:
            # Batch encode — much faster than individual calls for large sets
            uncached = [s for s in statements if s not in self._cache]
            if uncached:
                batch_embeddings = list(self.model.embed(uncached))
                for text, emb in zip(uncached, batch_embeddings):
                    self._cache[text] = np.array(emb, dtype=np.float32)
            return [self._cache[s] for s in statements]
        else:
            # Fallback: build shared vocabulary across all statements first
            self._invalidate_cache()
            for stmt in statements:
                self.encode(stmt)
            # Now re-encode with stable full vocabulary
            self._invalidate_cache()
            return [self.encode(stmt) for stmt in statements]