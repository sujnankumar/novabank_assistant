"""
Benchmark Module
================
Measures end-to-end and component-level latency with warmup runs.
"""

import time
import platform
import datetime
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.evaluation.dataset import load_config, load_evaluation_cases, deterministic_split
from app.evaluation.metrics import compute_latency_stats
from app.evaluation.models import EvaluationCase, LatencyStats

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


class Benchmark:
    """End-to-end latency benchmarking with warmup support."""

    def __init__(
        self,
        orchestrator=None,
        warmup_runs: int = 1,
        benchmark_runs: int = 3,
    ):
        self._orchestrator = orchestrator
        self.warmup_runs = warmup_runs
        self.benchmark_runs = benchmark_runs

    def _get_orchestrator(self):
        if self._orchestrator is None:
            from app.agents.orchestrator import BankingOrchestrator
            self._orchestrator = BankingOrchestrator()
        return self._orchestrator

    def run_benchmark(
        self,
        cases: List[EvaluationCase],
        max_cases: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run latency benchmark on evaluation cases."""
        orchestrator = self._get_orchestrator()
        eval_cases = cases[:max_cases] if max_cases else cases

        # Warmup
        warmup_latencies = []
        if self.warmup_runs > 0 and eval_cases:
            for i in range(min(self.warmup_runs, len(eval_cases))):
                case = eval_cases[i % len(eval_cases)]
                start = time.perf_counter()
                try:
                    orchestrator.run(
                        query=case.query,
                        customer_id=case.customer_id if case.customer_id else None,
                    )
                except Exception:
                    pass
                elapsed = (time.perf_counter() - start) * 1000
                warmup_latencies.append(elapsed)

        # Benchmark runs
        all_latencies = []
        for run_idx in range(self.benchmark_runs):
            run_latencies = []
            for case in eval_cases:
                start = time.perf_counter()
                try:
                    orchestrator.run(
                        query=case.query,
                        customer_id=case.customer_id if case.customer_id else None,
                    )
                except Exception:
                    pass
                elapsed = (time.perf_counter() - start) * 1000
                run_latencies.append(elapsed)
            all_latencies.extend(run_latencies)

        warm_stats = compute_latency_stats(all_latencies)
        cold_stats = compute_latency_stats(warmup_latencies) if warmup_latencies else None

        result = {
            "benchmark_conditions": {
                "num_queries": len(eval_cases),
                "warmup_runs": self.warmup_runs,
                "benchmark_runs": self.benchmark_runs,
                "total_measurements": len(all_latencies),
                "llm_mode": "mock",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "qdrant_mode": "local_persistent",
                "retrieval_top_k": 4,
                "platform": platform.platform(),
                "timestamp": datetime.datetime.now().isoformat(),
            },
            "warm_run": asdict(warm_stats),
        }

        if cold_stats:
            result["cold_start"] = asdict(cold_stats)

        return result

    def save_benchmark(self, result: Dict[str, Any], filename: str = "benchmark_results.json") -> Path:
        """Save benchmark results to JSON."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / filename
        path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        return path
