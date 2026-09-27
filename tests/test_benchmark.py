"""
Phase 10 Tests — Benchmark
===========================
Tests for latency collection, percentile calculation, warmup, and report generation.
"""

import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("LLM_PROVIDER", "mock")

import pytest
from unittest.mock import MagicMock, patch
from app.evaluation.benchmark import Benchmark
from app.evaluation.metrics import compute_latency_stats
from app.evaluation.models import EvaluationCase


def _make_case(case_id="EVAL-0001", query="What is my balance?", customer_id="CUST001"):
    return EvaluationCase(
        case_id=case_id,
        query_id="Q001",
        query=query,
        customer_id=customer_id,
        intent="CHECK_BALANCE",
        expected_route="TOOL",
        expected_tools=["get_balance"],
        expected_sources=[],
        category="customer_specific",
    )


class TestBenchmarkLatency:
    def test_latency_collection(self):
        """Benchmark collects latency measurements."""
        mock_orch = MagicMock()
        mock_orch.run.return_value = {
            "status": "success", "route": "TOOL", "response": "Balance: 50000",
            "sources": [], "thought_process": [],
        }
        bench = Benchmark(orchestrator=mock_orch, warmup_runs=0, benchmark_runs=1)
        cases = [_make_case()]
        result = bench.run_benchmark(cases)
        assert "warm_run" in result
        assert result["warm_run"]["count"] >= 1

    def test_warmup_runs(self):
        """Benchmark performs warmup before measurement."""
        mock_orch = MagicMock()
        mock_orch.run.return_value = {
            "status": "success", "route": "TOOL", "response": "Balance: 50000",
            "sources": [], "thought_process": [],
        }
        bench = Benchmark(orchestrator=mock_orch, warmup_runs=2, benchmark_runs=1)
        cases = [_make_case()]
        result = bench.run_benchmark(cases)
        assert "cold_start" in result
        assert result["cold_start"]["count"] >= 1
        # Warmup calls + benchmark calls
        assert mock_orch.run.call_count >= 2

    def test_percentile_calculation(self):
        """Percentile statistics are computed correctly."""
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        stats = compute_latency_stats(latencies)
        assert stats.min_ms == 10.0
        assert stats.max_ms == 100.0
        assert stats.mean_ms == 55.0
        assert stats.p95_ms >= 90.0
        assert stats.count == 10

    def test_benchmark_conditions_recorded(self):
        """Benchmark records conditions metadata."""
        mock_orch = MagicMock()
        mock_orch.run.return_value = {
            "status": "success", "route": "TOOL", "response": "OK",
            "sources": [], "thought_process": [],
        }
        bench = Benchmark(orchestrator=mock_orch, warmup_runs=0, benchmark_runs=1)
        cases = [_make_case()]
        result = bench.run_benchmark(cases)
        conditions = result["benchmark_conditions"]
        assert "num_queries" in conditions
        assert "llm_mode" in conditions
        assert "platform" in conditions
        assert "timestamp" in conditions

    def test_report_generation(self, tmp_path):
        """Benchmark saves results to JSON."""
        mock_orch = MagicMock()
        mock_orch.run.return_value = {
            "status": "success", "route": "TOOL", "response": "OK",
            "sources": [], "thought_process": [],
        }
        bench = Benchmark(orchestrator=mock_orch, warmup_runs=0, benchmark_runs=1)
        cases = [_make_case()]
        result = bench.run_benchmark(cases)

        import json
        path = tmp_path / "benchmark_test.json"
        path.write_text(json.dumps(result, indent=2, default=str))
        loaded = json.loads(path.read_text())
        assert "warm_run" in loaded
