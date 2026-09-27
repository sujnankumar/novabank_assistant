"""
Policy Documents API Router
===========================
Provides endpoints for browsing and viewing NovaBank policy documents and knowledge base guidelines.
Used for document preview modals and interactive citations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Path as FPath, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/policies", tags=["Policies"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
KB_DIR = BASE_DIR / "knowledge_base"


class PolicyMetadata(BaseModel):
    document_id: str
    filename: str
    title: str
    category: str
    effective_date: Optional[str] = None
    last_updated: Optional[str] = None
    source: Optional[str] = None


class PolicyDetail(BaseModel):
    document_id: str
    filename: str
    title: str
    category: str
    content: str
    sections: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _load_metadata() -> List[Dict[str, Any]]:
    """Loads knowledge base metadata.json if available."""
    meta_file = KB_DIR / "metadata.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _extract_sections(content: str) -> List[str]:
    """Extracts all markdown H1, H2, and H3 headers from content."""
    sections: List[str] = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
            clean_hdr = line.lstrip("#").strip()
            if clean_hdr:
                sections.append(clean_hdr)
    return sections


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List all policy documents",
    description="Retrieve listing and metadata for all official NovaBank policy documents.",
)
def list_policies() -> List[Dict[str, Any]]:
    """Returns a list of all official policy documents with metadata."""
    metadata_list = _load_metadata()
    if metadata_list:
        return metadata_list

    # Fallback to scanning KB_DIR
    results = []
    if KB_DIR.exists():
        for p in sorted(KB_DIR.glob("*.md")):
            results.append({
                "document_id": p.stem.upper(),
                "filename": p.name,
                "title": p.stem.replace("_", " ").title(),
                "category": "BANKING_POLICY",
            })
    return results


@router.get(
    "/{filename}",
    response_model=PolicyDetail,
    status_code=status.HTTP_200_OK,
    summary="Get policy document content",
    description="Retrieve the complete markdown text and metadata of a specific policy document.",
    responses={
        200: {"description": "Policy document found and returned"},
        404: {"description": "Policy document not found"},
    },
)
def get_policy(
    filename: str = FPath(..., description="Document filename (e.g. 06_savings_account_policy.md) or ID"),
) -> PolicyDetail:
    """Retrieve full content and headers for a policy document."""
    # Sanitize to prevent path traversal
    safe_name = Path(filename).name.strip()
    if not safe_name.endswith(".md"):
        safe_name = f"{safe_name}.md"

    # Search by filename
    target_path = KB_DIR / safe_name

    metadata_list = _load_metadata()
    matched_meta: Dict[str, Any] = {}

    # If direct filename didn't match, check by document_id in metadata
    if not target_path.exists():
        clean_search = filename.strip().upper()
        for meta in metadata_list:
            if meta.get("document_id", "").upper() == clean_search or meta.get("filename", "") == filename.strip():
                target_path = KB_DIR / meta.get("filename", "")
                matched_meta = meta
                break

    if not target_path.exists() or not target_path.is_file():
        # Check partial match on stem (e.g. savings_account_policy)
        clean_stem = filename.lower().replace(".md", "").lstrip("0123456789_")
        for p in KB_DIR.glob("*.md"):
            if clean_stem in p.stem.lower():
                target_path = p
                break

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy document '{filename}' not found."
        )

    # Find metadata
    if not matched_meta:
        for meta in metadata_list:
            if meta.get("filename") == target_path.name:
                matched_meta = meta
                break

    try:
        content = target_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read policy document: {exc}"
        )

    title = matched_meta.get("title")
    if not title:
        # Extract first H1 header
        for line in content.splitlines():
            if line.startswith("# "):
                title = line.lstrip("#").strip()
                break
        if not title:
            title = target_path.stem.replace("_", " ").title()

    sections = _extract_sections(content)

    return PolicyDetail(
        document_id=matched_meta.get("document_id", target_path.stem.upper()),
        filename=target_path.name,
        title=title,
        category=matched_meta.get("category", "General Policy"),
        content=content,
        sections=sections,
        metadata=matched_meta,
    )
