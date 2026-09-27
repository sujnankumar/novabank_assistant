"""
Build RAG Vector Index Script
=============================
Loads the NovaBank knowledge base, chunks documents, generates sentence-transformer
embeddings, builds the Qdrant vector collection, and persists the collection to disk.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag import (
    DocumentLoader,
    MarkdownChunker,
    EmbeddingGenerator,
    QdrantVectorStore,
    RAGRetriever,
)


def build():
    print("=" * 70)
    print("NOVABANK RAG PIPELINE — QDRANT INDEX BUILDER")
    print("=" * 70)

    loader = DocumentLoader()
    chunker = MarkdownChunker()
    embeddings = EmbeddingGenerator()
    vector_store = QdrantVectorStore()

    print("\n1. Loading knowledge base...")
    documents = loader.load_documents()
    print(f"   Documents loaded: {len(documents)}")

    print("\n2. Chunking documents...")
    chunks = chunker.chunk_documents(documents)
    print(f"   Chunks created: {len(chunks)}")

    print("\n3. Generating embeddings...")
    print(f"   Embedding model:  {embeddings.model_name}")
    texts = [c.content for c in chunks]
    embeddings_matrix = embeddings.embed_texts(texts)
    print(f"   Embeddings generated: {len(embeddings_matrix)}")
    print(f"   Vector dimension:     {embeddings.dimension}")

    print("\n4. Building Qdrant collection (idempotent rebuild)...")
    print(f"   Collection name: {vector_store.collection_name}")
    print(f"   Storage path:    {vector_store.storage_path}")
    vector_store.create_index(embeddings_matrix, chunks)
    print(f"   Collection vectors: {vector_store.total_vectors}")

    print("\n5. Verifying vector count and persistence...")
    vector_store.save()
    assert vector_store.total_vectors == len(chunks), (
        f"Vector count mismatch: {vector_store.total_vectors} vs expected {len(chunks)}"
    )
    print(f"   Verification passed: {vector_store.total_vectors} vectors in Qdrant collection.")
    print(f"   Index successfully saved to {vector_store.storage_path}")

    vector_store.close()

    print("\n" + "=" * 70)
    print("QDRANT RAG INDEX BUILT AND PERSISTED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    build()
