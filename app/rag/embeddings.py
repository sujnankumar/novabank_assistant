"""
Sentence Transformer Embedding Generator
========================================
Generates local, deterministic vector embeddings using sentence-transformers.
Embeddings are normalized for cosine similarity with Qdrant.
"""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.rag.config import EMBEDDING_MODEL


class EmbeddingGenerator:
    """Generates normalized vector representations using a local sentence-transformer model."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or EMBEDDING_MODEL
        self._model: Optional[SentenceTransformer] = None
        self._dimension: Optional[int] = None

    def _get_model(self) -> SentenceTransformer:
        """Lazy loader for SentenceTransformer model."""
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name, local_files_only=True)
            except Exception:
                self._model = SentenceTransformer(self.model_name)

            # Determine vector dimension cleanly
            if hasattr(self._model, "get_embedding_dimension"):
                self._dimension = self._model.get_embedding_dimension()
            else:
                self._dimension = self._model.get_sentence_embedding_dimension()
        return self._model

    @property
    def dimension(self) -> int:
        """Embedding vector dimension (e.g. 384 for all-MiniLM-L6-v2)."""
        if self._dimension is None:
            self._get_model()
        return self._dimension  # type: ignore

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate normalized embeddings for a list of texts.
        Returns a float32 2D numpy array of shape (len(texts), dimension).
        """
        if not texts:
            dim = self.dimension
            return np.empty((0, dim), dtype=np.float32)

        model = self._get_model()
        # normalize_embeddings=True ensures cosine similarity via inner product
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        embeddings_np = np.asarray(embeddings, dtype=np.float32)
        if len(embeddings_np) != len(texts):
            raise ValueError(
                f"Embedding count ({len(embeddings_np)}) does not match text count ({len(texts)})"
            )

        return embeddings_np

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate normalized embedding for a single query.
        Returns a float32 2D numpy array of shape (1, dimension).
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or whitespace-only")

        return self.embed_texts([query.strip()])
