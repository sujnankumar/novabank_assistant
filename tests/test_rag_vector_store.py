"""
Test Qdrant Vector Store
========================
Comprehensive unit tests for QdrantVectorStore covering:
  1. Qdrant collection creation
  2. Collection configuration
  3. Vector dimension = 384
  4. Cosine distance metric
  5. Vector insertion and upsert
  6. Metadata and payload persistence
  7. Search functionality
  8. Top-k behavior
  9. Similarity score ordering (descending)
  10. Collection reload and persistence
  11. Missing/uninitialized collection handling
  12. Idempotent rebuild without duplicate vectors
  13. Empty collection handling
  14. Invalid vector dimension handling
"""

import pytest
import numpy as np
from qdrant_client import models

from app.rag.schemas import DocumentChunk
from app.rag.vector_store import QdrantVectorStore


def test_qdrant_collection_creation_and_config(tmp_path):
    """1-4: Verify collection creation, dimension 384, and cosine distance config."""
    store = QdrantVectorStore(
        storage_path=str(tmp_path / "qdrant_test_1"),
        collection_name="test_config_coll",
        vector_size=384,
    )

    chunks = [
        DocumentChunk(
            chunk_id="test_chunk_001",
            content="NovaBank offers competitive savings interest rates.",
            source="06_savings_account_policy.md",
            document_id="SAVINGS_POLICY",
            section="Interest Rates",
            chunk_index=0,
        )
    ]
    # Create normalized 384-dimensional vector
    v = np.zeros((1, 384), dtype=np.float32)
    v[0, 0] = 1.0

    store.create_index(v, chunks)

    # 1. Collection exists
    assert store.has_collection() is True

    # 2-4. Collection config verification
    info = store.client.get_collection("test_config_coll")
    vectors_config = info.config.params.vectors

    assert vectors_config.size == 384
    assert vectors_config.distance == models.Distance.COSINE
    assert store.total_vectors == 1
    store.close()


def test_vector_insertion_payload_and_search(tmp_path):
    """5-7: Verify vector upsert, payload preservation, and cosine search."""
    store = QdrantVectorStore(
        storage_path=str(tmp_path / "qdrant_test_2"),
        collection_name="test_search_coll",
    )

    chunks = [
        DocumentChunk(
            chunk_id="chunk_loan_001",
            content="Home loan interest rates starting at 8.25% p.a.",
            source="01_home_loan_policy.md",
            document_id="HOME_LOAN",
            section="Interest Rates",
            chunk_index=0,
            metadata={"category": "lending"},
        ),
        DocumentChunk(
            chunk_id="chunk_savings_001",
            content="Savings accounts require minimum balance of INR 1000.",
            source="06_savings_account_policy.md",
            document_id="SAVINGS",
            section="Balance Requirements",
            chunk_index=0,
            metadata={"category": "deposits"},
        ),
    ]

    # Two orthogonal unit vectors (384 dimensions)
    v1 = np.zeros(384, dtype=np.float32)
    v1[0] = 1.0
    v2 = np.zeros(384, dtype=np.float32)
    v2[1] = 1.0
    embeddings = np.vstack([v1, v2])

    store.create_index(embeddings, chunks)
    assert store.total_vectors == 2

    # Query with vector identical to v1
    query_vector = np.zeros(384, dtype=np.float32)
    query_vector[0] = 1.0

    results = store.search(query_vector, top_k=2)
    assert len(results) == 2

    top_score, top_chunk = results[0]
    assert pytest.approx(top_score, abs=1e-3) == 1.0
    assert top_chunk.chunk_id == "chunk_loan_001"
    assert top_chunk.source == "01_home_loan_policy.md"
    assert top_chunk.document_id == "HOME_LOAN"
    assert top_chunk.section == "Interest Rates"
    assert top_chunk.metadata.get("category") == "lending"

    # Second result should have score ~ 0.0 (orthogonal)
    second_score, second_chunk = results[1]
    assert pytest.approx(second_score, abs=1e-3) == 0.0
    assert second_chunk.chunk_id == "chunk_savings_001"
    store.close()


def test_top_k_behavior_and_similarity_ordering(tmp_path):
    """8-9: Verify top_k limits results and orders them strictly descending by score."""
    store = QdrantVectorStore(
        storage_path=str(tmp_path / "qdrant_test_3"),
        collection_name="test_topk_coll",
    )

    chunks = [
        DocumentChunk(
            chunk_id=f"chunk_order_{i}",
            content=f"Content for chunk {i}",
            source="test.md",
            document_id="TEST",
            section="Section",
            chunk_index=i,
        )
        for i in range(4)
    ]

    # Target query vector is along axis 0
    # Vectors with decreasing cosine similarity to query:
    # v0: cos = 1.0
    # v1: cos = 0.8
    # v2: cos = 0.5
    # v3: cos = 0.0
    v0 = np.zeros(384, dtype=np.float32); v0[0] = 1.0
    v1 = np.zeros(384, dtype=np.float32); v1[0] = 0.8; v1[1] = 0.6
    v2 = np.zeros(384, dtype=np.float32); v2[0] = 0.5; v2[1] = float(np.sqrt(0.75))
    v3 = np.zeros(384, dtype=np.float32); v3[1] = 1.0
    embeddings = np.vstack([v0, v1, v2, v3])

    store.create_index(embeddings, chunks)

    query = np.zeros(384, dtype=np.float32)
    query[0] = 1.0

    # Request top_k = 2
    results = store.search(query, top_k=2)
    assert len(results) == 2

    # Check strictly descending ordering
    assert results[0][0] >= results[1][0]
    assert results[0][1].chunk_id == "chunk_order_0"
    assert results[1][1].chunk_id == "chunk_order_1"

    # Request top_k = 4
    all_results = store.search(query, top_k=4)
    assert len(all_results) == 4
    scores = [r[0] for r in all_results]
    assert scores == sorted(scores, reverse=True)
    store.close()


def test_collection_reload_and_persistence(tmp_path):
    """10: Verify Qdrant collection persists to disk and can be reloaded."""
    storage_dir = str(tmp_path / "qdrant_test_4")
    store = QdrantVectorStore(
        storage_path=storage_dir,
        collection_name="test_persist_coll",
    )

    chunks = [
        DocumentChunk(
            chunk_id="chunk_persist_001",
            content="Persistent banking chunk content.",
            source="policy.md",
            document_id="POLICY",
            section="Persistence",
            chunk_index=0,
        )
    ]
    vec = np.zeros((1, 384), dtype=np.float32)
    vec[0, 0] = 1.0

    store.create_index(vec, chunks)
    store.save()
    assert store.total_vectors == 1

    # Reload using a fresh instance pointing to the same storage path
    reloaded_store = QdrantVectorStore(
        storage_path=storage_dir,
        collection_name="test_persist_coll",
    )
    assert reloaded_store.load() is True
    assert reloaded_store.total_vectors == 1

    query = np.zeros(384, dtype=np.float32)
    query[0] = 1.0
    results = reloaded_store.search(query, top_k=1)
    assert len(results) == 1
    assert results[0][1].chunk_id == "chunk_persist_001"
    store.close()


def test_missing_and_uninitialized_collection_behavior(tmp_path):
    """11: Verify missing/uninitialized collection handling."""
    store = QdrantVectorStore(
        storage_path=str(tmp_path / "qdrant_test_5"),
        collection_name="nonexistent_collection",
    )

    assert store.has_collection() is False
    assert store.total_vectors == 0
    assert store.load() is False

    query = np.zeros(384, dtype=np.float32)
    with pytest.raises(RuntimeError) as exc_info:
        store.search(query, top_k=1)
    assert "has not been initialized" in str(exc_info.value)

    with pytest.raises(RuntimeError):
        store.save()
    store.close()


def test_rebuild_without_duplicate_vectors(tmp_path):
    """12: Verify rebuilding the collection is idempotent and creates no duplicate vectors."""
    store = QdrantVectorStore(
        storage_path=str(tmp_path / "qdrant_test_6"),
        collection_name="test_rebuild_coll",
    )

    chunks = [
        DocumentChunk(
            chunk_id="chunk_a",
            content="Content A",
            source="a.md",
            document_id="A",
            section="A",
            chunk_index=0,
        ),
        DocumentChunk(
            chunk_id="chunk_b",
            content="Content B",
            source="b.md",
            document_id="B",
            section="B",
            chunk_index=0,
        ),
    ]
    vecs = np.zeros((2, 384), dtype=np.float32)
    vecs[0, 0] = 1.0
    vecs[1, 1] = 1.0

    # Build once
    store.create_index(vecs, chunks)
    assert store.total_vectors == 2

    # Rebuild again with identical data
    store.create_index(vecs, chunks)
    assert store.total_vectors == 2, "Rebuild must not create duplicate vectors"
    store.close()


def test_empty_collection_behavior(tmp_path):
    """13: Verify empty collection creation and search handling."""
    store = QdrantVectorStore(
        storage_path=str(tmp_path / "qdrant_test_7"),
        collection_name="test_empty_coll",
        vector_size=384,
    )

    empty_embeddings = np.empty((0, 384), dtype=np.float32)
    store.create_index(empty_embeddings, [])

    assert store.has_collection() is True
    assert store.total_vectors == 0

    query = np.zeros(384, dtype=np.float32)
    results = store.search(query, top_k=5)
    assert results == []
    store.close()


def test_invalid_vector_dimension_handling(tmp_path):
    """14: Verify dimension mismatch between query and index raises ValueError."""
    store = QdrantVectorStore(
        storage_path=str(tmp_path / "qdrant_test_8"),
        collection_name="test_dim_coll",
        vector_size=384,
    )

    chunks = [
        DocumentChunk(
            chunk_id="chunk_dim_001",
            content="Dimension test chunk",
            source="test.md",
            document_id="TEST",
            section="Dim",
            chunk_index=0,
        )
    ]
    vecs = np.zeros((1, 384), dtype=np.float32)
    store.create_index(vecs, chunks)

    # Query with 128-dimensional vector instead of 384
    wrong_query = np.zeros(128, dtype=np.float32)
    with pytest.raises(ValueError) as exc_info:
        store.search(wrong_query, top_k=1)
    assert "dimension" in str(exc_info.value).lower()
    store.close()


def test_deterministic_point_id_mapping():
    """Verify chunk_id_to_point_id is deterministic and collision-free for distinct chunk IDs."""
    chunk_id_1 = "01_home_loan_policy_chunk_001"
    chunk_id_2 = "01_home_loan_policy_chunk_002"

    id_1a = QdrantVectorStore.chunk_id_to_point_id(chunk_id_1)
    id_1b = QdrantVectorStore.chunk_id_to_point_id(chunk_id_1)
    id_2 = QdrantVectorStore.chunk_id_to_point_id(chunk_id_2)

    assert id_1a == id_1b, "Point ID generation must be deterministic"
    assert id_1a != id_2, "Distinct chunk IDs must yield distinct point IDs"
