"""
Knowledge Base Document Loader
==============================
Discovers and loads Markdown documents from the NovaBank knowledge-base directory.
Associates metadata from metadata.json and ignores non-markdown files.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from app.rag.config import KNOWLEDGE_BASE_DIR
from app.rag.schemas import Document

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Loads knowledge base markdown documents and associates metadata."""

    def __init__(self, kb_dir: Optional[str] = None):
        self.kb_dir = Path(kb_dir or KNOWLEDGE_BASE_DIR)

    def load_documents(self) -> List[Document]:
        """
        Discover and load all valid Markdown documents from knowledge_base.
        Raises FileNotFoundError if directory does not exist.
        """
        if not self.kb_dir.exists() or not self.kb_dir.is_dir():
            raise FileNotFoundError(
                f"Knowledge base directory does not exist: {self.kb_dir}"
            )

        # Load metadata.json if present
        metadata_map = {}
        metadata_path = self.kb_dir / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta_list = json.load(f)
                    if isinstance(meta_list, list):
                        for entry in meta_list:
                            fname = entry.get("filename")
                            if fname:
                                metadata_map[fname] = entry
            except Exception as e:
                logger.warning(f"Could not parse metadata.json in {self.kb_dir}: {e}")

        documents: List[Document] = []
        md_files = sorted(self.kb_dir.glob("*.md"))

        for file_path in md_files:
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue

            # Skip empty or whitespace-only documents (Section 24)
            if not content.strip():
                logger.warning(f"Skipping empty knowledge-base document: {file_path.name}")
                continue

            source = file_path.name
            doc_meta = metadata_map.get(source, {})
            doc_id = doc_meta.get("document_id") or file_path.stem

            documents.append(
                Document(
                    content=content,
                    source=source,
                    document_id=doc_id,
                    metadata=doc_meta,
                )
            )

        return documents
