"""
RAG Retriever Executor
======================
Invokes Phase 5 Qdrant RAG retriever through its public interface,
capturing retrieved policy chunks with full source provenance.
"""

from typing import Any, Dict, List, Optional
from app.agents.config import RAG_TOP_K
from app.rag import RAGRetriever


class RAGExecutor:
    """Executes RAG retrieval using Phase 5 RAGRetriever."""

    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        top_k: int = RAG_TOP_K,
    ):
        self._retriever = retriever
        self.top_k = top_k

    def _get_retriever(self) -> RAGRetriever:
        """Lazy-loads the RAGRetriever instance."""
        if self._retriever is None:
            self._retriever = RAGRetriever()
            if not self._retriever.is_index_ready():
                self._retriever.build_index()
        return self._retriever

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Executes knowledge-base retrieval for policy documents.

        Returns:
            list of structured provenance dictionaries containing chunk content, score, and source.
        """
        effective_top_k = top_k or self.top_k

        try:
            retriever = self._get_retriever()
            raw_response = retriever.retrieve(query=query, top_k=effective_top_k)

            if not raw_response.get("retrieved", False):
                return []

            rag_items: List[Dict[str, Any]] = []
            for item in raw_response.get("results", []):
                meta = item.get("metadata", {})
                rag_items.append({
                    "source_type": "rag",
                    "source": meta.get("source", "unknown"),
                    "document_id": meta.get("document_id", ""),
                    "section": meta.get("section", ""),
                    "title": meta.get("title", ""),
                    "chunk_id": item.get("chunk_id", ""),
                    "score": item.get("score", 0.0),
                    "content": item.get("content", ""),
                })

            return rag_items

        except Exception as e:
            # RAG errors do not crash workflow, returned as error item
            return [{
                "source_type": "rag",
                "source": "retrieval_error",
                "error": {
                    "type": "rag_exception",
                    "message": str(e),
                },
            }]
