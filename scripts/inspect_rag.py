"""
RAG Inspection Utility
======================
Development and evaluation utility for manually inspecting RAG retrieval results.
Prints source document, section heading, similarity score, and retrieved content.
Does NOT generate natural language answers.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag import RAGRetriever


def inspect_query(query: str, top_k: int = 5):
    retriever = RAGRetriever()

    if not retriever.is_index_ready():
        print("Vector index not found on disk. Building index now...")
        retriever.build_index()

    print("=" * 80)
    print(f"QUERY: {query}")
    print(f"TOP_K: {top_k} | THRESHOLD: {retriever.similarity_threshold}")
    print("=" * 80)

    response = retriever.retrieve(query, top_k=top_k)

    if not response["retrieved"]:
        print("\n[NO RESULTS RETRIEVED] No document chunks met the similarity threshold.")
        return

    print(f"\nRetrieved {len(response['results'])} relevant chunk(s):\n")
    for i, item in enumerate(response["results"], 1):
        meta = item["metadata"]
        print(f"--- Result #{i} (Score: {item['score']:.4f}) ---")
        print(f"  Source Document: {meta.get('source')}")
        print(f"  Document ID:     {meta.get('document_id')}")
        print(f"  Section:         {meta.get('section')}")
        print(f"  Chunk ID:        {item.get('chunk_id')}")
        print("  Content:")
        # Indent content
        for line in item["content"].splitlines()[:10]:
            print(f"    {line}")
        if len(item["content"].splitlines()) > 10:
            print("    [... remaining lines truncated ...]")
        print()


if __name__ == "__main__":
    test_query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What are the eligibility requirements for a home loan?"
    )
    inspect_query(test_query)
