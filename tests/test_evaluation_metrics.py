"""
Phase 10 Tests — Evaluation Metrics
====================================
Tests for accuracy, precision/recall/F1, Hit@K, MRR, confusion matrix,
latency statistics, and aggregate metric computations.
"""

import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import pytest
from app.evaluation.metrics import (
    accuracy,
    precision_recall_f1,
    confusion_matrix,
    hit_at_k,
    reciprocal_rank,
    compute_hit_at_k_metrics,
    compute_latency_stats,
    compute_routing_metrics,
    compute_tool_metrics,
    compute_safety_metrics,
)
from app.evaluation.models import EvaluationResult, LatencyStats


class TestAccuracy:
    def test_perfect(self):
        assert accuracy(10, 10) == 1.0

    def test_zero(self):
        assert accuracy(0, 10) == 0.0

    def test_empty(self):
        assert accuracy(0, 0) == 0.0

    def test_partial(self):
        assert accuracy(7, 10) == 0.7


class TestPrecisionRecallF1:
    def test_perfect(self):
        p, r, f1 = precision_recall_f1(10, 0, 0)
        assert p == 1.0
        assert r == 1.0
        assert f1 == 1.0

    def test_no_predictions(self):
        p, r, f1 = precision_recall_f1(0, 0, 10)
        assert p == 0.0
        assert r == 0.0
        assert f1 == 0.0

    def test_mixed(self):
        p, r, f1 = precision_recall_f1(5, 2, 3)
        assert 0 < p < 1
        assert 0 < r < 1
        assert 0 < f1 < 1


class TestConfusionMatrix:
    def test_basic(self):
        expected = ["A", "B", "A", "B"]
        predicted = ["A", "A", "A", "B"]
        cm = confusion_matrix(expected, predicted)
        assert cm["A"]["A"] == 2
        assert cm["B"]["A"] == 1
        assert cm["B"]["B"] == 1

    def test_all_correct(self):
        expected = ["X", "Y", "X"]
        predicted = ["X", "Y", "X"]
        cm = confusion_matrix(expected, predicted)
        assert cm["X"]["X"] == 2
        assert cm["Y"]["Y"] == 1


class TestHitAtK:
    def test_hit_at_1_found(self):
        assert hit_at_k(["doc1", "doc2", "doc3"], ["doc1"], 1) is True

    def test_hit_at_1_not_found(self):
        assert hit_at_k(["doc2", "doc3", "doc4"], ["doc1"], 1) is False

    def test_hit_at_3_found(self):
        assert hit_at_k(["doc2", "doc3", "doc1"], ["doc1"], 3) is True

    def test_hit_at_5_found(self):
        assert hit_at_k(["a", "b", "c", "d", "doc1"], ["doc1"], 5) is True

    def test_hit_at_5_not_found(self):
        assert hit_at_k(["a", "b", "c", "d", "e"], ["doc1"], 5) is False

    def test_no_expected(self):
        """No expected sources means no RAG evaluation needed - always true."""
        assert hit_at_k(["a", "b"], [], 1) is True

    def test_multiple_expected(self):
        assert hit_at_k(["doc2", "doc3"], ["doc1", "doc2"], 3) is True

    def test_empty_retrieved(self):
        assert hit_at_k([], ["doc1"], 1) is False


class TestReciprocalRank:
    def test_rank_1(self):
        assert reciprocal_rank(["doc1", "doc2"], ["doc1"]) == 1.0

    def test_rank_2(self):
        assert reciprocal_rank(["doc2", "doc1"], ["doc1"]) == 0.5

    def test_rank_3(self):
        assert reciprocal_rank(["a", "b", "doc1"], ["doc1"]) == pytest.approx(1 / 3)

    def test_not_found(self):
        assert reciprocal_rank(["a", "b", "c"], ["doc1"]) == 0.0

    def test_no_expected(self):
        assert reciprocal_rank(["a", "b"], []) == 1.0


class TestLatencyStats:
    def test_basic(self):
        stats = compute_latency_stats([100.0, 200.0, 300.0, 400.0, 500.0])
        assert stats.min_ms == 100.0
        assert stats.max_ms == 500.0
        assert stats.mean_ms == 300.0
        assert stats.count == 5

    def test_p95(self):
        latencies = list(range(1, 101))  # 1..100
        stats = compute_latency_stats([float(x) for x in latencies])
        assert stats.p95_ms >= 95.0

    def test_single(self):
        stats = compute_latency_stats([42.0])
        assert stats.min_ms == 42.0
        assert stats.max_ms == 42.0
        assert stats.p50_ms == 42.0

    def test_empty(self):
        stats = compute_latency_stats([])
        assert stats.count == 0
        assert stats.min_ms == 0.0


class TestComputeRoutingMetrics:
    def _make_result(self, expected, predicted):
        return EvaluationResult(
            case_id="test",
            query="test",
            intent="TEST",
            expected_route=expected,
            predicted_route=predicted,
            route_correct=(expected == predicted),
            expected_tools=[],
            predicted_tools=[],
            tool_selection_correct=True,
            tool_execution_success=True,
            expected_sources=[],
            retrieved_sources=[],
        )

    def test_routing_metrics(self):
        results = [
            self._make_result("TOOL", "TOOL"),
            self._make_result("RAG", "RAG"),
            self._make_result("TOOL", "RAG"),
        ]
        metrics = compute_routing_metrics(results)
        assert metrics["accuracy"] == pytest.approx(2 / 3, abs=0.01)
        assert metrics["total_evaluated"] == 3

    def test_perfect_routing(self):
        results = [self._make_result("TOOL", "TOOL") for _ in range(5)]
        metrics = compute_routing_metrics(results)
        assert metrics["accuracy"] == 1.0
