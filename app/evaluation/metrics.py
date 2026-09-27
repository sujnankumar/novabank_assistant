"""
Evaluation Metrics
==================
Pure metric computation functions for routing, tools, RAG, safety, and latency.
All functions are deterministic and require no external dependencies.
"""

import math
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from app.evaluation.models import EvaluationResult, LatencyStats


def accuracy(correct: int, total: int) -> float:
    """Compute accuracy as correct/total."""
    if total == 0:
        return 0.0
    return round(correct / total, 4)


def precision_recall_f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    """Compute precision, recall, and F1 score."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def confusion_matrix(
    expected: List[str],
    predicted: List[str],
    labels: Optional[List[str]] = None,
) -> Dict[str, Dict[str, int]]:
    """Build a confusion matrix from expected and predicted labels."""
    if labels is None:
        labels = sorted(set(expected) | set(predicted))

    matrix = {exp: {pred: 0 for pred in labels} for exp in labels}
    for e, p in zip(expected, predicted):
        if e in matrix and p in matrix[e]:
            matrix[e][p] += 1

    return matrix


def hit_at_k(retrieved_sources: List[str], expected_sources: List[str], k: int) -> bool:
    """Check if at least one expected source appears in top-k retrieved sources."""
    if not expected_sources:
        return True  # No ground truth means no RAG evaluation needed
    top_k = retrieved_sources[:k]
    return any(src in top_k for src in expected_sources)


def reciprocal_rank(retrieved_sources: List[str], expected_sources: List[str]) -> float:
    """Calculate reciprocal rank of first relevant document."""
    if not expected_sources:
        return 1.0  # No ground truth
    for i, src in enumerate(retrieved_sources):
        if src in expected_sources:
            return 1.0 / (i + 1)
    return 0.0


def compute_hit_at_k_metrics(results: List[EvaluationResult]) -> Dict[str, float]:
    """Compute Hit@1, Hit@3, Hit@5, and MRR from evaluation results."""
    rag_results = [r for r in results if r.expected_sources]
    if not rag_results:
        return {"hit_at_1": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr": 0.0, "rag_evaluable_count": 0}

    total = len(rag_results)
    h1 = sum(1 for r in rag_results if r.rag_hit_at_1) / total
    h3 = sum(1 for r in rag_results if r.rag_hit_at_3) / total
    h5 = sum(1 for r in rag_results if r.rag_hit_at_5) / total
    mrr = sum(r.rag_reciprocal_rank for r in rag_results) / total

    return {
        "hit_at_1": round(h1, 4),
        "hit_at_3": round(h3, 4),
        "hit_at_5": round(h5, 4),
        "mrr": round(mrr, 4),
        "rag_evaluable_count": total,
    }


def compute_tool_metrics(results: List[EvaluationResult]) -> Dict[str, Any]:
    """Compute tool selection and execution metrics."""
    tool_evaluable = [r for r in results if r.expected_tools]
    if not tool_evaluable:
        return {
            "selection_accuracy": 0.0,
            "execution_success_rate": 0.0,
            "tool_evaluable_count": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }

    total = len(tool_evaluable)
    correct_selection = sum(1 for r in tool_evaluable if r.tool_selection_correct)
    successful_execution = sum(1 for r in tool_evaluable if r.tool_execution_success)

    # Compute set-based precision/recall/F1 across all tool-evaluable cases
    total_tp, total_fp, total_fn = 0, 0, 0
    for r in tool_evaluable:
        expected_set = set(r.expected_tools)
        predicted_set = set(r.predicted_tools)
        total_tp += len(expected_set & predicted_set)
        total_fp += len(predicted_set - expected_set)
        total_fn += len(expected_set - predicted_set)

    p, rec, f1 = precision_recall_f1(total_tp, total_fp, total_fn)

    return {
        "selection_accuracy": accuracy(correct_selection, total),
        "execution_success_rate": accuracy(successful_execution, total),
        "tool_evaluable_count": total,
        "precision": p,
        "recall": rec,
        "f1": f1,
    }


def compute_routing_metrics(results: List[EvaluationResult]) -> Dict[str, Any]:
    """Compute routing accuracy and confusion matrix."""
    total = len(results)
    correct = sum(1 for r in results if r.route_correct)

    expected = [r.expected_route for r in results]
    predicted = [r.predicted_route for r in results]
    cm = confusion_matrix(expected, predicted)

    # Per-route accuracy
    per_route = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in results:
        per_route[r.expected_route]["total"] += 1
        if r.route_correct:
            per_route[r.expected_route]["correct"] += 1

    per_route_accuracy = {
        route: accuracy(stats["correct"], stats["total"])
        for route, stats in sorted(per_route.items())
    }

    return {
        "accuracy": accuracy(correct, total),
        "total_evaluated": total,
        "correct": correct,
        "confusion_matrix": cm,
        "per_route_accuracy": per_route_accuracy,
    }


def compute_safety_metrics(results: List[EvaluationResult]) -> Dict[str, Any]:
    """Compute safety/refusal metrics."""
    safety_cases = [r for r in results if r.expected_route == "UNSUPPORTED" or not r.safety_passed]
    total = len(safety_cases) if safety_cases else 1
    passed = sum(1 for r in safety_cases if r.safety_passed)

    isolation_cases = [r for r in results if r.expected_tools]
    isolation_total = len(isolation_cases) if isolation_cases else 1
    isolation_passed = sum(1 for r in isolation_cases if r.customer_isolation_passed)

    return {
        "safety_success_rate": accuracy(passed, total) if safety_cases else 1.0,
        "safety_cases_total": len(safety_cases),
        "safety_cases_passed": passed,
        "customer_isolation_rate": accuracy(isolation_passed, isolation_total),
        "isolation_cases_total": len(isolation_cases),
        "isolation_cases_passed": isolation_passed,
    }


def compute_response_metrics(results: List[EvaluationResult]) -> Dict[str, Any]:
    """Compute response grounding metrics."""
    evaluable = [r for r in results if r.response_text and r.expected_route != "UNSUPPORTED"]
    if not evaluable:
        return {"grounding_rate": 0.0, "evaluable_count": 0}

    grounded = sum(1 for r in evaluable if r.response_grounded)
    return {
        "grounding_rate": accuracy(grounded, len(evaluable)),
        "evaluable_count": len(evaluable),
        "grounded_count": grounded,
    }


def compute_latency_stats(latencies: List[float]) -> LatencyStats:
    """Compute latency statistics from a list of latency values in ms."""
    if not latencies:
        return LatencyStats()

    sorted_lat = sorted(latencies)
    n = len(sorted_lat)

    min_val = sorted_lat[0]
    max_val = sorted_lat[-1]
    mean_val = sum(sorted_lat) / n
    median_val = sorted_lat[n // 2] if n % 2 == 1 else (sorted_lat[n // 2 - 1] + sorted_lat[n // 2]) / 2
    p50_val = median_val  # p50 == median
    p95_idx = min(int(math.ceil(0.95 * n)) - 1, n - 1)
    p95_val = sorted_lat[p95_idx]

    return LatencyStats(
        min_ms=round(min_val, 2),
        mean_ms=round(mean_val, 2),
        median_ms=round(median_val, 2),
        p50_ms=round(p50_val, 2),
        p95_ms=round(p95_val, 2),
        max_ms=round(max_val, 2),
        count=n,
    )
