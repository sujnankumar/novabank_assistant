"""
Run Benchmark Script
====================
Executes latency benchmarking on the NovaBank system.

Usage:
    python scripts/run_benchmark.py
    python scripts/run_benchmark.py --max-cases 10 --runs 3
"""

import argparse
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("LLM_PROVIDER", "mock")

from app.evaluation.benchmark import Benchmark
from app.evaluation.dataset import load_config, load_evaluation_cases, deterministic_split


def main():
    parser = argparse.ArgumentParser(description="Run NovaBank Phase 10 Benchmark")
    parser.add_argument("--max-cases", type=int, default=20, help="Number of cases to benchmark")
    parser.add_argument("--warmup", type=int, default=1, help="Number of warmup runs")
    parser.add_argument("--runs", type=int, default=3, help="Number of benchmark runs")
    args = parser.parse_args()

    config = load_config()
    cases = load_evaluation_cases()
    dev_cases, _ = deterministic_split(cases, seed=config.get("seed", 42))

    bench = Benchmark(warmup_runs=args.warmup, benchmark_runs=args.runs)
    print(f"Running benchmark: {args.max_cases} cases x {args.runs} runs (warmup: {args.warmup})")

    result = bench.run_benchmark(dev_cases, max_cases=args.max_cases)
    path = bench.save_benchmark(result)

    warm = result["warm_run"]
    print(f"\nWarm Run Latency:")
    print(f"  Min:    {warm['min_ms']:.2f} ms")
    print(f"  Mean:   {warm['mean_ms']:.2f} ms")
    print(f"  Median: {warm['median_ms']:.2f} ms")
    print(f"  p50:    {warm['p50_ms']:.2f} ms")
    print(f"  p95:    {warm['p95_ms']:.2f} ms")
    print(f"  Max:    {warm['max_ms']:.2f} ms")

    if "cold_start" in result:
        cold = result["cold_start"]
        print(f"\nCold Start:")
        print(f"  Mean: {cold['mean_ms']:.2f} ms")

    print(f"\nResults saved to: {path}")


if __name__ == "__main__":
    main()
