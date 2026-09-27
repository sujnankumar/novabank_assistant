"""
RAG Retriever
=============
Retrieval pipeline interface connecting document loading, chunking,
embedding generation, Qdrant vector search, threshold filtering, and result formatting.
"""

from typing import Any, Dict, List, Optional
from app.rag.chunker import MarkdownChunker
from app.rag.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL,
    KNOWLEDGE_BASE_DIR,
    QDRANT_COLLECTION_NAME,
    QDRANT_STORAGE_PATH,
    SIMILARITY_THRESHOLD,
)
from app.rag.embeddings import EmbeddingGenerator
from app.rag.loader import DocumentLoader
from app.rag.schemas import RetrievalItem, RetrievalResponse
from app.rag.vector_store import QdrantVectorStore


class RAGRetriever:
    """End-to-end RAG retriever for NovaBank general banking knowledge backed by Qdrant."""

    def __init__(
        self,
        kb_dir: Optional[str] = None,
        storage_path: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        default_top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        **kwargs,
    ):
        self.kb_dir = kb_dir or KNOWLEDGE_BASE_DIR
        self.storage_path = (
            storage_path or kwargs.get("storage_path") or QDRANT_STORAGE_PATH
        )
        self.collection_name = collection_name or QDRANT_COLLECTION_NAME
        self.default_top_k = default_top_k or DEFAULT_TOP_K
        self.similarity_threshold = (
            similarity_threshold if similarity_threshold is not None else SIMILARITY_THRESHOLD
        )

        self.loader = DocumentLoader(kb_dir=self.kb_dir)
        self.chunker = MarkdownChunker(
            chunk_size=chunk_size or CHUNK_SIZE,
            chunk_overlap=chunk_overlap or CHUNK_OVERLAP,
        )
        self.embeddings = EmbeddingGenerator(model_name=embedding_model or EMBEDDING_MODEL)
        self.vector_store = QdrantVectorStore(
            storage_path=self.storage_path,
            collection_name=self.collection_name,
            vector_size=self.embeddings.dimension,
        )

    def is_index_ready(self) -> bool:
        """Check if Qdrant collection is loaded or can be loaded from disk."""
        if self.vector_store.total_vectors > 0:
            return True
        return self.vector_store.load()

    def build_index(self) -> Dict[str, Any]:
        """
        Build and persist the complete Qdrant vector collection from knowledge base markdown files.
        """
        # 1. Load documents
        documents = self.loader.load_documents()
        if not documents:
            raise ValueError(f"No valid markdown documents found in {self.kb_dir}")

        # 2. Chunk documents
        chunks = self.chunker.chunk_documents(documents)
        if not chunks:
            raise ValueError("No chunks created from loaded documents")

        # 3. Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings_matrix = self.embeddings.embed_texts(texts)

        # 4. Build Qdrant collection
        self.vector_store.create_index(embeddings_matrix, chunks)

        # 5. Persist index
        self.vector_store.save()

        return {
            "documents_loaded": len(documents),
            "chunks_created": len(chunks),
            "embeddings_generated": len(embeddings_matrix),
            "vector_dimension": self.embeddings.dimension,
            "index_vectors": self.vector_store.total_vectors,
            "storage_path": str(self.storage_path),
            "collection_name": self.collection_name,
        }

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant knowledge-base chunks for a query.

        Parameters:
            query (str): User query string
            top_k (int, optional): Number of results to retrieve (default: 5)
            threshold (float, optional): Minimum cosine similarity score (default: 0.35)

        Returns:
            dict: Structured response with query, retrieved boolean, and ranked results.
        """
        # 1. Query validation
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("Query cannot be empty or whitespace-only")

        # 2. top_k validation
        effective_top_k = top_k if top_k is not None else self.default_top_k
        if effective_top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {effective_top_k}")

        effective_threshold = (
            threshold if threshold is not None else self.similarity_threshold
        )

        # 3. Ensure index is loaded
        if not self.is_index_ready():
            raise RuntimeError(
                "RAG vector index has not been built. Please run build_index() first."
            )

        # 4. Generate query embedding
        query_vector = self.embeddings.embed_query(query.strip())

        # 5. Search Qdrant vector store
        # Fetch slightly more to account for threshold filtering or duplicates
        search_results = self.vector_store.search(
            query_vector,
            top_k=effective_top_k * 2,
        )

        # 6. Apply threshold and deduplicate by chunk_id
        seen_chunks = set()
        retrieval_items: List[RetrievalItem] = []

        for score, chunk in search_results:
            if score < effective_threshold:
                continue

            if chunk.chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk.chunk_id)

            item = RetrievalItem(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                score=round(score, 4),
                metadata={
                    "source": chunk.source,
                    "document_id": chunk.document_id,
                    "section": chunk.section,
                },
            )
            retrieval_items.append(item)

            if len(retrieval_items) >= effective_top_k:
                break

        # Results must be sorted descending by similarity score
        retrieval_items.sort(key=lambda x: x.score, reverse=True)

        is_retrieved = len(retrieval_items) > 0

        response = RetrievalResponse(
            query=query.strip(),
            retrieved=is_retrieved,
            results=retrieval_items,
        )

        return response.model_dump()
