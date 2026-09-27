"""
Test Markdown Document Chunker
==============================
Tests for:
  - Markdown heading boundary detection
  - Paragraph splitting and sliding window chunking
  - Chunk size and overlap enforcement
  - Unique chunk ID generation
  - Source and section metadata preservation
  - Validation of chunking configuration
"""

import pytest
from app.rag.chunker import MarkdownChunker
from app.rag.schemas import Document


def test_chunker_respects_configuration():
    """Verify chunker respects custom chunk_size and chunk_overlap."""
    chunker = MarkdownChunker(chunk_size=500, chunk_overlap=80)
    assert chunker.chunk_size == 500
    assert chunker.chunk_overlap == 80


def test_chunker_invalid_configuration():
    """Invalid chunk sizes or overlaps raise ValueError."""
    with pytest.raises(ValueError):
        MarkdownChunker(chunk_size=-100)

    with pytest.raises(ValueError):
        MarkdownChunker(chunk_overlap=-10)

    with pytest.raises(ValueError):
        MarkdownChunker(chunk_size=500, chunk_overlap=500)


def test_chunk_preserves_section_and_source():
    """Chunking preserves markdown heading sections and source filename."""
    content = """# NovaBank Home Loan Policy

## 1. Overview
NovaBank offers competitive home loans for purchasing, constructing, or renovating properties.

## 2. Eligibility Criteria
Borrowers must be Indian residents aged between 21 and 60 years. Minimum income is INR 30,000.
"""
    doc = Document(
        content=content,
        source="01_home_loan_policy.md",
        document_id="HOME_LOAN_POLICY",
        metadata={"category": "LOAN"},
    )

    chunker = MarkdownChunker(chunk_size=800, chunk_overlap=120)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    sections = [c.section for c in chunks if c.section]
    assert any("Overview" in s for s in sections)
    assert any("Eligibility Criteria" in s for s in sections)

    for c in chunks:
        assert c.source == "01_home_loan_policy.md"
        assert c.document_id == "HOME_LOAN_POLICY"
        assert c.chunk_id.startswith("01_home_loan_policy_chunk_")


def test_chunk_ids_are_globally_unique():
    """All generated chunk IDs must be unique across all documents."""
    doc1 = Document(
        content="## Section A\n\nContent for doc 1 paragraph.",
        source="doc1.md",
        document_id="DOC1",
    )
    doc2 = Document(
        content="## Section B\n\nContent for doc 2 paragraph.",
        source="doc2.md",
        document_id="DOC2",
    )

    chunker = MarkdownChunker()
    chunks = chunker.chunk_documents([doc1, doc2])

    chunk_ids = [c.chunk_id for c in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
