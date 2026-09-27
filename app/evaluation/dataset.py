"""
Evaluation Dataset Loader
=========================
Loads evaluation cases, performs deterministic dev/holdout split,
validates ground truth completeness.
"""

import json
import hashlib
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.evaluation.models import EvaluationCase

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EVALUATION_DIR = PROJECT_ROOT / "evaluation"


def load_config() -> Dict[str, Any]:
    """Load evaluation configuration."""
    config_path = EVALUATION_DIR / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Evaluation config not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def load_route_mapping() -> Dict[str, Dict[str, Any]]:
    """Load and validate route mapping."""
    path = EVALUATION_DIR / "route_mapping.json"
    if not path.exists():
        raise FileNotFoundError(f"Route mapping not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["mapping"]


def load_retrieval_ground_truth() -> Dict[str, List[str]]:
    """Load RAG retrieval ground truth."""
    path = EVALUATION_DIR / "retrieval_ground_truth.json"
    if not path.exists():
        raise FileNotFoundError(f"Retrieval ground truth not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["ground_truth"]


def load_evaluation_cases() -> List[EvaluationCase]:
    """Load evaluation cases from evaluation_cases.json."""
    path = EVALUATION_DIR / "evaluation_cases.json"
    if not path.exists():
        raise FileNotFoundError(f"Evaluation cases not found: {path}. Run scripts/build_evaluation_cases.py first.")
    data = json.loads(path.read_text(encoding="utf-8"))

    cases = []
    seen_ids = set()
    for rec in data["cases"]:
        cid = rec["case_id"]
        if cid in seen_ids:
            raise ValueError(f"Duplicate case_id: {cid}")
        seen_ids.add(cid)

        case = EvaluationCase(
            case_id=cid,
            query_id=rec["query_id"],
            query=rec["query"],
            customer_id=rec.get("customer_id", ""),
            intent=rec["intent"],
            expected_route=rec["expected_route"],
            expected_tools=rec.get("expected_tools", []),
            expected_sources=rec.get("expected_sources", []),
            category=rec.get("category", ""),
            expected_agent=rec.get("expected_agent", ""),
            expected_data_source=rec.get("expected_data_source", ""),
        )
        cases.append(case)

    return cases


def validate_cases(cases: List[EvaluationCase], route_mapping: Dict[str, Any]) -> List[str]:
    """
    Validate evaluation cases for completeness.
    Returns list of validation errors (empty if valid).
    """
    errors = []
    intents_in_cases = set(c.intent for c in cases)
    mapped_intents = set(route_mapping.keys())

    # Check for unmapped intents
    unmapped = intents_in_cases - mapped_intents
    for intent in sorted(unmapped):
        errors.append(f"ERROR: Missing route mapping for intent '{intent}'")

    # Check for required fields
    for c in cases:
        if not c.query.strip():
            errors.append(f"ERROR: Empty query in case {c.case_id}")
        if not c.intent:
            errors.append(f"ERROR: Missing intent in case {c.case_id}")
        if not c.expected_route:
            errors.append(f"ERROR: Missing expected_route in case {c.case_id}")

    # Check IDs are unique
    ids = [c.case_id for c in cases]
    if len(ids) != len(set(ids)):
        errors.append("ERROR: Duplicate case IDs detected")

    return errors


def deterministic_split(
    cases: List[EvaluationCase],
    seed: int = 42,
    dev_ratio: float = 0.80,
) -> Tuple[List[EvaluationCase], List[EvaluationCase]]:
    """
    Deterministic stratified split of evaluation cases into dev and holdout sets.
    Uses fixed seed for reproducibility. Stratifies by intent to preserve distribution.

    Returns:
        Tuple of (development_cases, holdout_cases)
    """
    # Group by intent for stratification
    intent_groups: Dict[str, List[EvaluationCase]] = {}
    for case in cases:
        intent_groups.setdefault(case.intent, []).append(case)

    dev_cases = []
    holdout_cases = []

    rng = random.Random(seed)

    for intent in sorted(intent_groups.keys()):
        group = sorted(intent_groups[intent], key=lambda c: c.case_id)
        # Shuffle deterministically
        rng.shuffle(group)

        n_dev = max(1, round(len(group) * dev_ratio))
        # Ensure at least 1 in holdout if group has >= 2
        if len(group) >= 2 and n_dev == len(group):
            n_dev = len(group) - 1

        dev_cases.extend(group[:n_dev])
        holdout_cases.extend(group[n_dev:])

    return dev_cases, holdout_cases


def check_leakage(
    dev_cases: List[EvaluationCase],
    holdout_cases: List[EvaluationCase],
) -> List[str]:
    """Check for case leakage between dev and holdout sets.
    Uses (query, customer_id) pairs since the same query from different customers is valid."""
    errors = []

    dev_ids = set(c.case_id for c in dev_cases)
    holdout_ids = set(c.case_id for c in holdout_cases)
    id_overlap = dev_ids & holdout_ids
    if id_overlap:
        errors.append(f"ERROR: Development/holdout ID overlap: {sorted(id_overlap)}")

    # Check for identical (query, customer_id) pairs — same customer asking same query
    dev_pairs = set((c.query, c.customer_id) for c in dev_cases)
    holdout_pairs = set((c.query, c.customer_id) for c in holdout_cases)
    pair_overlap = dev_pairs & holdout_pairs
    if pair_overlap:
        for q, cid in sorted(pair_overlap):
            errors.append(f"ERROR: Development/holdout duplicate (customer+query): '{q[:60]}...' by {cid}")

    return errors
