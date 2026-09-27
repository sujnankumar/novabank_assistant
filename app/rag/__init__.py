"""
NovaBank RAG Package
====================
Provides knowledge-base retrieval pipeline components backed by Qdrant.
"""

from .chunker import MarkdownChunker
from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL,
    KNOWLEDGE_BASE_DIR,
    QDRANT_COLLECTION_NAME,
    QDRANT_DISTANCE,
    QDRANT_STORAGE_PATH,
    QDRANT_VECTOR_SIZE,
    SIMILARITY_THRESHOLD,
)
from .embeddings import EmbeddingGenerator
from .loader import DocumentLoader
from .retriever import RAGRetriever
from .schemas import (
    Document,
    DocumentChunk,
    RetrievalItem,
    RetrievalResponse,
)
from .vector_store import QdrantVectorStore

__all__ = [
    "RAGRetriever",
    "DocumentLoader",
    "MarkdownChunker",
    "EmbeddingGenerator",
    "QdrantVectorStore",
    "Document",
    "DocumentChunk",
    "RetrievalItem",
    "RetrievalResponse",
    "EMBEDDING_MODEL",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "DEFAULT_TOP_K",
    "SIMILARITY_THRESHOLD",
    "KNOWLEDGE_BASE_DIR",
    "QDRANT_COLLECTION_NAME",
    "QDRANT_STORAGE_PATH",
    "QDRANT_VECTOR_SIZE",
    "QDRANT_DISTANCE",
]
