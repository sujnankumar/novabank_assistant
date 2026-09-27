"""
Markdown Document Chunker
=========================
Splits Markdown documents into semantic chunks respecting heading boundaries,
paragraphs, and sentence structure with configurable size and overlap.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple
from app.rag.config import CHUNK_OVERLAP, CHUNK_SIZE
from app.rag.schemas import Document, DocumentChunk


class MarkdownChunker:
    """Semantic Markdown text splitter preserving section headers and metadata."""

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ):
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap cannot be negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_into_sections(self, text: str) -> List[Tuple[Optional[str], str]]:
        """Split markdown text into (section_heading, section_text) tuples."""
        lines = text.splitlines(keepends=True)
        sections: List[Tuple[Optional[str], str]] = []
        current_heading: Optional[str] = None
        current_lines: List[str] = []

        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in lines:
            match = heading_pattern.match(line.strip())
            if match:
                if current_lines:
                    sections.append((current_heading, "".join(current_lines)))
                    current_lines = []
                current_heading = match.group(2).strip()
            current_lines.append(line)

        if current_lines:
            sections.append((current_heading, "".join(current_lines)))

        return sections

    def _split_section_text(self, text: str) -> List[str]:
        """Split section text into chunks respecting chunk_size and chunk_overlap."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return []

        chunks: List[str] = []
        current_chunk_parts: List[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)

            # If para itself exceeds chunk_size, split by sentences
            if para_len > self.chunk_size:
                # Flush current accumulator
                if current_chunk_parts:
                    chunk_text = "\n\n".join(current_chunk_parts)
                    chunks.append(chunk_text)
                    current_chunk_parts = []
                    current_len = 0

                sentences = re.split(r"(?<=[.!?])\s+", para)
                sub_parts: List[str] = []
                sub_len = 0
                for s in sentences:
                    s_clean = s.strip()
                    if not s_clean:
                        continue
                    if sub_len + len(s_clean) + 1 > self.chunk_size and sub_parts:
                        chunks.append(" ".join(sub_parts))
                        # Keep overlap from previous sentences
                        overlap_parts: List[str] = []
                        overlap_len = 0
                        for prev_s in reversed(sub_parts):
                            if overlap_len + len(prev_s) <= self.chunk_overlap:
                                overlap_parts.insert(0, prev_s)
                                overlap_len += len(prev_s)
                            else:
                                break
                        sub_parts = overlap_parts
                        sub_len = sum(len(p) for p in sub_parts)

                    sub_parts.append(s_clean)
                    sub_len += len(s_clean) + 1

                if sub_parts:
                    chunks.append(" ".join(sub_parts))
                continue

            # Standard paragraph accumulation
            if current_len + para_len + 2 > self.chunk_size and current_chunk_parts:
                chunks.append("\n\n".join(current_chunk_parts))

                # Build overlap from the end of the previous chunk
                overlap_text = current_chunk_parts[-1]
                if len(overlap_text) <= self.chunk_overlap:
                    current_chunk_parts = [overlap_text, para]
                    current_len = len(overlap_text) + para_len + 2
                else:
                    current_chunk_parts = [para]
                    current_len = para_len
            else:
                current_chunk_parts.append(para)
                current_len += para_len + 2

        if current_chunk_parts:
            chunks.append("\n\n".join(current_chunk_parts))

        return chunks

    def chunk_document(self, document: Document) -> List[DocumentChunk]:
        """Split a single Document into a list of DocumentChunks."""
        doc_stem = Path(document.source).stem
        sections = self._split_into_sections(document.content)
        all_chunks: List[DocumentChunk] = []
        chunk_idx = 1

        for heading, section_text in sections:
            section_chunks = self._split_section_text(section_text)
            for c_text in section_chunks:
                c_text_clean = c_text.strip()
                if not c_text_clean:
                    continue

                chunk_id = f"{doc_stem}_chunk_{chunk_idx:03d}"
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        content=c_text_clean,
                        source=document.source,
                        document_id=document.document_id,
                        section=heading,
                        chunk_index=chunk_idx,
                        metadata={
                            **document.metadata,
                            "section": heading,
                            "source": document.source,
                            "document_id": document.document_id,
                            "chunk_id": chunk_id,
                        },
                    )
                )
                chunk_idx += 1

        return all_chunks

    def chunk_documents(self, documents: List[Document]) -> List[DocumentChunk]:
        """Chunk a list of documents sequentially."""
        chunks: List[DocumentChunk] = []
        for doc in documents:
            chunks.extend(self.chunk_document(doc))
        return chunks
