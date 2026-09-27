"""
Test Knowledge Base Document Loader
===================================
Tests for:
  - Loading valid knowledge base directory
  - Markdown file discovery and count (12 documents)
  - UTF-8 reading and non-empty content
  - Metadata association from metadata.json
  - Empty-document handling
  - Missing-directory handling
"""

import pytest
from pathlib import Path
from app.rag.loader import DocumentLoader


def test_loader_discovers_all_twelve_documents():
    """Loader discovers all 12 documents from knowledge_base directory."""
    loader = DocumentLoader()
    docs = loader.load_documents()

    assert len(docs) == 12
    sources = [d.source for d in docs]

    expected_files = [
        "01_home_loan_policy.md",
        "02_personal_loan_policy.md",
        "03_education_loan_policy.md",
        "04_vehicle_loan_policy.md",
        "05_credit_card_policy.md",
        "06_savings_account_policy.md",
        "07_fixed_deposit_policy.md",
        "08_transaction_policy.md",
        "09_account_management_policy.md",
        "10_fraud_and_security_policy.md",
        "11_customer_service_policy.md",
        "12_general_banking_faq.md",
    ]

    for expected in expected_files:
        assert expected in sources, f"Missing document: {expected}"


def test_loader_associates_metadata():
    """Loaded documents have associated metadata from metadata.json."""
    loader = DocumentLoader()
    docs = loader.load_documents()

    for doc in docs:
        assert doc.source.endswith(".md")
        assert len(doc.content.strip()) > 0
        assert doc.document_id is not None
        assert isinstance(doc.metadata, dict)

    # Check specific metadata on home loan doc
    home_loan_doc = next(d for d in docs if d.source == "01_home_loan_policy.md")
    assert home_loan_doc.metadata.get("category") == "LOAN"
    assert "Home Loan" in home_loan_doc.metadata.get("title", "")


def test_loader_missing_directory_raises_error(tmp_path):
    """Attempting to load from a non-existent directory raises FileNotFoundError."""
    non_existent = tmp_path / "does_not_exist"
    loader = DocumentLoader(kb_dir=str(non_existent))

    with pytest.raises(FileNotFoundError) as exc_info:
        loader.load_documents()

    assert "does not exist" in str(exc_info.value).lower()


def test_loader_skips_empty_files(tmp_path):
    """Empty files in the directory are safely skipped."""
    kb_temp = tmp_path / "kb_test"
    kb_temp.mkdir()

    # Create one valid doc and one empty doc
    valid_file = kb_temp / "valid.md"
    valid_file.write_text("# Valid Document\n\nSome banking content.", encoding="utf-8")

    empty_file = kb_temp / "empty.md"
    empty_file.write_text("   \n\n  ", encoding="utf-8")

    # Create a non-md file to ensure it's ignored
    other_file = kb_temp / "notes.txt"
    other_file.write_text("Not markdown", encoding="utf-8")

    loader = DocumentLoader(kb_dir=str(kb_temp))
    docs = loader.load_documents()

    assert len(docs) == 1
    assert docs[0].source == "valid.md"
