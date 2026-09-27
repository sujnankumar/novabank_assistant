"""
Qdrant Vector Store Manager
===========================
Manages Qdrant vector indexing, similarity search, and local persistence.
"""

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from qdrant_client import QdrantClient, models

from app.rag.config import (
    QDRANT_COLLECTION_NAME,
    QDRANT_STORAGE_PATH,
    QDRANT_VECTOR_SIZE,
)
from app.rag.schemas import DocumentChunk

# Cache open QdrantClient instances by resolved storage path to avoid file-lock conflicts in local mode
_CLIENT_CACHE: Dict[str, QdrantClient] = {}


def _get_qdrant_client(storage_path: str) -> QdrantClient:
    """Retrieve or create a QdrantClient instance for the given storage path."""
    if storage_path == ":memory:":
        resolved = ":memory:"
    else:
        resolved = str(Path(storage_path).resolve())

    if resolved not in _CLIENT_CACHE:
        if resolved == ":memory:":
            _CLIENT_CACHE[resolved] = QdrantClient(":memory:")
        else:
            Path(resolved).mkdir(parents=True, exist_ok=True)
            _CLIENT_CACHE[resolved] = QdrantClient(path=resolved)

    return _CLIENT_CACHE[resolved]


import atexit

def _close_qdrant_client(storage_path: str) -> None:
    """Close and evict a cached QdrantClient instance."""
    if storage_path == ":memory:":
        resolved = ":memory:"
    else:
        resolved = str(Path(storage_path).resolve())

    if resolved in _CLIENT_CACHE:
        try:
            _CLIENT_CACHE[resolved].close()
        except Exception:
            pass
        del _CLIENT_CACHE[resolved]


def _close_all_qdrant_clients() -> None:
    """Close all cached QdrantClient instances cleanly before Python exits."""
    for path, client in list(_CLIENT_CACHE.items()):
        try:
            client.close()
        except Exception:
            pass
    _CLIENT_CACHE.clear()


atexit.register(_close_all_qdrant_clients)


class QdrantVectorStore:
    """Qdrant vector store for cosine similarity search with local payload persistence."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        collection_name: Optional[str] = None,
        vector_size: Optional[int] = None,
    ):
        self.storage_path = str(storage_path or QDRANT_STORAGE_PATH)
        self.collection_name = collection_name or QDRANT_COLLECTION_NAME
        self.vector_size = vector_size or QDRANT_VECTOR_SIZE

    @property
    def client(self) -> QdrantClient:
        """Get or initialize the underlying Qdrant client."""
        return _get_qdrant_client(self.storage_path)

    def close(self) -> None:
        """Close the underlying client connection and release storage locks."""
        _close_qdrant_client(self.storage_path)

    @property
    def total_vectors(self) -> int:
        """Return total number of vectors in the collection."""
        if not self.has_collection():
            return 0
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception:
            return 0

    def has_collection(self) -> bool:
        """Check if the collection exists in Qdrant."""
        try:
            return self.client.collection_exists(self.collection_name)
        except Exception:
            return False

    @staticmethod
    def chunk_id_to_point_id(chunk_id: str) -> str:
        """
        Deterministically convert a chunk ID to a UUID string for Qdrant.
        Preserves reproducible point identity across index rebuilds.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    def create_index(
        self,
        embeddings: np.ndarray,
        chunks: List[DocumentChunk],
        batch_size: int = 100,
    ) -> None:
        """
        Build or rebuild Qdrant collection from embeddings and chunk metadata.
        Rebuilding the collection drops existing data to avoid duplicate vectors.
        """
        if embeddings.shape[0] != len(chunks):
            raise ValueError(
                f"Embedding count ({embeddings.shape[0]}) does not match chunk count ({len(chunks)})"
            )

        dimension = embeddings.shape[1] if len(chunks) > 0 else self.vector_size
        self.vector_size = dimension

        # Cleanly recreate collection if it already exists
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE,
            ),
        )

        if len(chunks) == 0:
            return

        # Prepare points
        points: List[models.PointStruct] = []
        for i, chunk in enumerate(chunks):
            point_id = self.chunk_id_to_point_id(chunk.chunk_id)
            vector = embeddings[i].tolist()
            payload = {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "source": chunk.source,
                "document_id": chunk.document_id,
                "section": chunk.section,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata,
            }
            points.append(models.PointStruct(id=point_id, vector=vector, payload=payload))

        # Upsert in batches
        for start_idx in range(0, len(points), batch_size):
            batch = points[start_idx : start_idx + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
                wait=True,
            )

    def save(self, persist_dir: Optional[str] = None) -> None:
        """
        Persist collection to disk.
        In local persistent mode, Qdrant auto-persists to storage_path.
        Maintains API compatibility.
        """
        if not self.has_collection():
            raise RuntimeError(
                f"Cannot save an uninitialized Qdrant collection: {self.collection_name}"
            )

    def load(self, persist_dir: Optional[str] = None) -> bool:
        """
        Verify persisted collection exists and is available.
        Returns True if collection exists and contains vectors, False otherwise.
        """
        if not self.has_collection():
            return False
        return self.total_vectors > 0

    def search(
        self,
        query_embedding: Union[np.ndarray, List[float]],
        top_k: int = 5,
    ) -> List[Tuple[float, DocumentChunk]]:
        """
        Search for top_k most similar chunks using cosine similarity.
        Returns list of (score, DocumentChunk) tuples.
        """
        if not self.has_collection():
            raise RuntimeError(
                f"Qdrant collection '{self.collection_name}' has not been initialized or loaded. Build the index first."
            )

        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        # Convert numpy array to 1D float list
        if isinstance(query_embedding, np.ndarray):
            query_vector = query_embedding.flatten().tolist()
        else:
            query_vector = list(query_embedding)

        # Validate query dimension against collection config
        info = self.client.get_collection(self.collection_name)
        expected_size = info.config.params.vectors.size
        if len(query_vector) != expected_size:
            raise ValueError(
                f"Query vector dimension ({len(query_vector)}) does not match index dimension ({expected_size})"
            )

        if self.total_vectors == 0:
            return []

        search_response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )

        results: List[Tuple[float, DocumentChunk]] = []
        for scored_point in search_response.points:
            payload = scored_point.payload or {}
            chunk = DocumentChunk(
                chunk_id=payload.get("chunk_id", str(scored_point.id)),
                content=payload.get("content", ""),
                source=payload.get("source", ""),
                document_id=payload.get("document_id", ""),
                section=payload.get("section"),
                chunk_index=payload.get("chunk_index", 0),
                metadata=payload.get("metadata", {}),
            )
            score = float(scored_point.score)
            results.append((score, chunk))

        return results
