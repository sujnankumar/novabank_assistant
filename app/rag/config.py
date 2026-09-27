"""
RAG Pipeline Configuration
==========================
Centralized configuration values for embedding, chunking, Qdrant storage, and retrieval.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Embedding model (local sentence-transformers)
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Chunking settings
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))

# Retrieval settings
DEFAULT_TOP_K = int(os.getenv("RAG_DEFAULT_TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.35"))

# Directory paths
KNOWLEDGE_BASE_DIR = os.getenv("RAG_KNOWLEDGE_BASE_DIR", str(PROJECT_ROOT / "knowledge_base"))

# Qdrant vector store configuration
QDRANT_COLLECTION_NAME = os.getenv("RAG_QDRANT_COLLECTION_NAME", "novabank_knowledge")
QDRANT_STORAGE_PATH = os.getenv("RAG_QDRANT_STORAGE_PATH", str(PROJECT_ROOT / "qdrant_storage"))
QDRANT_VECTOR_SIZE = int(os.getenv("RAG_QDRANT_VECTOR_SIZE", "384"))
QDRANT_DISTANCE = os.getenv("RAG_QDRANT_DISTANCE", "cosine")
