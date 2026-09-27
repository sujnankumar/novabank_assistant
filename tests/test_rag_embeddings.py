"""
Test Sentence Transformer Embedding Generator
==============================================
Tests for:
  - Model loading and dimension detection (384)
  - Embedding batch generation and normalization
  - Determinism on repeated embeddings
  - Empty text list handling
  - Query validation (empty/whitespace raises ValueError)
"""

import pytest
import numpy as np
from app.rag.embeddings import EmbeddingGenerator


def test_embedding_dimension():
    """Default all-MiniLM-L6-v2 model has dimension 384."""
    generator = EmbeddingGenerator()
    assert generator.dimension == 384


def test_embedding_generation_shape_and_normalization():
    """Embeddings generated must match text count, be float32, and have L2 norm == 1.0."""
    generator = EmbeddingGenerator()
    texts = [
        "NovaBank offers attractive personal loans.",
        "Fixed deposits earn up to 7.25% annual interest.",
    ]
    embeddings = generator.embed_texts(texts)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (2, 384)
    assert embeddings.dtype == np.float32

    # Verify L2 normalization: norm of each vector must be approximately 1.0
    for vec in embeddings:
        norm = np.linalg.norm(vec)
        assert pytest.approx(norm, abs=1e-4) == 1.0


def test_embedding_determinism():
    """Same input text produces consistent embedding vector."""
    generator = EmbeddingGenerator()
    text = "What is the penalty for early withdrawal of a fixed deposit?"

    emb1 = generator.embed_query(text)
    emb2 = generator.embed_query(text)

    assert np.allclose(emb1, emb2, atol=1e-5)


def test_embed_empty_list():
    """Empty list returns empty 2D array with dimension 384."""
    generator = EmbeddingGenerator()
    embeddings = generator.embed_texts([])
    assert embeddings.shape == (0, 384)


def test_embed_query_invalid():
    """Empty or whitespace-only query raises ValueError."""
    generator = EmbeddingGenerator()
    with pytest.raises(ValueError):
        generator.embed_query("")

    with pytest.raises(ValueError):
        generator.embed_query("   ")
