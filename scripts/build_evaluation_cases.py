"""
Evaluation Case Builder
=======================
Builds versioned evaluation cases from Phase 1 synthetic dataset,
combining query_labels.json, processed_queries.json, route_mapping.json,
and retrieval_ground_truth.json into a single evaluation_cases.json.
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build_evaluation_cases() -> dict:
    """Build evaluation cases from existing Phase 1 data and Phase 10 ground truth."""

    # Load source data
    processed_path = PROJECT_ROOT / "data" / "processed_queries.json"
    labels_path = PROJECT_ROOT / "data" / "query_labels.json"
    route_map_path = PROJECT_ROOT / "evaluation" / "route_mapping.json"
    rag_gt_path = PROJECT_ROOT / "evaluation" / "retrieval_ground_truth.json"
    config_path = PROJECT_ROOT / "evaluation" / "config.json"

    for p in [processed_path, labels_path, route_map_path, rag_gt_path, config_path]:
        if not p.exists():
            raise FileNotFoundError(f"Required file not found: {p}")

    processed = json.loads(processed_path.read_text(encoding="utf-8"))
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    route_map_data = json.loads(route_map_path.read_text(encoding="utf-8"))
    rag_gt_data = json.loads(rag_gt_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))

    route_mapping = route_map_data["mapping"]
    rag_ground_truth = rag_gt_data["ground_truth"]

    # Index labels by query_id
    labels_by_id = {l["query_id"]: l for l in labels}

    # Validate all intents have route mappings
    all_intents = set(l["intent"] for l in labels)
    unmapped = all_intents - set(route_mapping.keys())
    if unmapped:
        raise ValueError(f"ERROR: Missing route mapping for intents: {sorted(unmapped)}")

    # Build evaluation cases
    cases = []
    for i, query_rec in enumerate(processed):
        qid = query_rec["query_id"]
        label_rec = labels_by_id.get(qid)
        if not label_rec:
            raise ValueError(f"ERROR: No label found for query_id {qid}")

        intent = label_rec["intent"]
        route_info = route_mapping[intent]

        case_id = f"EVAL-{i+1:04d}"

        # Determine expected tools
        expected_tools = list(route_info.get("tools", []))

        # Refine tools based on query text for specific intents
        query_lower = query_rec["query"].lower()
        if intent == "LOAN_ELIGIBILITY":
            if "vehicle" in query_lower or "car" in query_lower:
                expected_tools = ["check_loan_eligibility"]
            elif "education" in query_lower:
                expected_tools = ["check_loan_eligibility"]
            elif "personal" in query_lower:
                expected_tools = ["check_loan_eligibility"]
            else:
                expected_tools = ["check_loan_eligibility"]

        # Determine expected RAG documents
        expected_sources = []
        if intent in rag_ground_truth:
            all_docs = rag_ground_truth[intent]
            # Narrow down based on query text
            if intent in ("LOAN_DOCUMENTS", "LOAN_INFORMATION", "LOAN_INTEREST_RATE", "LOAN_ELIGIBILITY"):
                if "home" in query_lower or "housing" in query_lower:
                    expected_sources = ["01_home_loan_policy.md"]
                elif "personal" in query_lower:
                    expected_sources = ["02_personal_loan_policy.md"]
                elif "education" in query_lower or "student" in query_lower:
                    expected_sources = ["03_education_loan_policy.md"]
                elif "vehicle" in query_lower or "car" in query_lower or "auto" in query_lower:
                    expected_sources = ["04_vehicle_loan_policy.md"]
                else:
                    # Generic loan query - any loan doc is acceptable
                    expected_sources = list(all_docs)
            else:
                expected_sources = list(all_docs)

        case = {
            "case_id": case_id,
            "query_id": qid,
            "query": query_rec["query"],
            "customer_id": query_rec.get("customer_id", ""),
            "intent": intent,
            "expected_route": route_info["route"],
            "expected_tools": expected_tools,
            "expected_sources": expected_sources,
            "category": route_info["category"],
            "expected_agent": label_rec.get("expected_agent", ""),
            "expected_data_source": label_rec.get("expected_data_source", ""),
        }
        cases.append(case)

    result = {
        "version": config.get("dataset_version", "v1"),
        "total_cases": len(cases),
        "cases": cases,
    }

    return result


def main():
    """Build and save evaluation cases."""
    result = build_evaluation_cases()
    output_path = PROJECT_ROOT / "evaluation" / "evaluation_cases.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built {result['total_cases']} evaluation cases -> {output_path}")

    # Print intent distribution
    from collections import Counter
    intent_counts = Counter(c["intent"] for c in result["cases"])
    route_counts = Counter(c["expected_route"] for c in result["cases"])
    print(f"\nIntent distribution ({len(intent_counts)} intents):")
    for k, v in sorted(intent_counts.items()):
        print(f"  {k}: {v}")
    print(f"\nRoute distribution:")
    for k, v in sorted(route_counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
