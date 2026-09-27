"""
Run Evaluation Script
=====================
Executes baseline or optimized evaluation on the NovaBank system.

Usage:
    python scripts/run_evaluation.py --mode baseline
    python scripts/run_evaluation.py --mode optimized
    python scripts/run_evaluation.py --mode holdout
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("LLM_PROVIDER", "mock")

from app.evaluation.dataset import (
    load_config,
    load_evaluation_cases,
    load_route_mapping,
    deterministic_split,
    check_leakage,
    validate_cases,
)
from app.evaluation.runner import EvaluationRunner


def main():
    parser = argparse.ArgumentParser(description="Run NovaBank Phase 10 Evaluation")
    parser.add_argument("--mode", choices=["baseline", "optimized", "holdout", "full"],
                        default="baseline", help="Evaluation mode")
    parser.add_argument("--max-cases", type=int, default=None,
                        help="Limit number of cases (for quick testing)")
    args = parser.parse_args()

    config = load_config()
    cases = load_evaluation_cases()
    route_mapping = load_route_mapping()

    # Validate
    errors = validate_cases(cases, route_mapping)
    if errors:
        for e in errors:
            print(e)
        sys.exit(1)

    # Split
    seed = config.get("seed", 42)
    dev_ratio = config.get("dev_ratio", 0.80)
    dev_cases, holdout_cases = deterministic_split(cases, seed=seed, dev_ratio=dev_ratio)

    # Check leakage (case ID overlap is fatal; query text duplicates are informational)
    leakage_errors = check_leakage(dev_cases, holdout_cases)
    id_errors = [e for e in leakage_errors if "ID overlap" in e]
    if id_errors:
        for e in id_errors:
            print(e)
        sys.exit(1)
    for e in leakage_errors:
        print(f"WARNING: {e}")

    print(f"Dataset: {len(cases)} total, {len(dev_cases)} dev, {len(holdout_cases)} holdout")

    runner = EvaluationRunner(config=config)

    if args.mode == "baseline":
        eval_cases = dev_cases[:args.max_cases] if args.max_cases else dev_cases
        print(f"\nRunning BASELINE evaluation on {len(eval_cases)} development cases...")
        report = runner.run_evaluation(eval_cases, label="Baseline / Development")

        json_path = runner.save_report_json(report, "baseline_evaluation.json")
        md_path = runner.save_report_markdown(report, "baseline_evaluation.md")
        print(f"\nBaseline JSON: {json_path}")
        print(f"Baseline MD: {md_path}")
        _print_summary(report)

    elif args.mode == "optimized":
        eval_cases = dev_cases[:args.max_cases] if args.max_cases else dev_cases
        print(f"\nRunning OPTIMIZED evaluation on {len(eval_cases)} development cases...")
        report = runner.run_evaluation(eval_cases, label="Optimized / Development")

        json_path = runner.save_report_json(report, "optimized_evaluation.json")
        md_path = runner.save_report_markdown(report, "optimized_evaluation.md")
        print(f"\nOptimized JSON: {json_path}")
        print(f"Optimized MD: {md_path}")
        _print_summary(report)

    elif args.mode == "holdout":
        eval_cases = holdout_cases[:args.max_cases] if args.max_cases else holdout_cases
        print(f"\nRunning HOLDOUT evaluation on {len(eval_cases)} holdout cases...")
        report = runner.run_evaluation(eval_cases, label="Optimized / Holdout")

        json_path = runner.save_report_json(report, "final_holdout_evaluation.json")
        md_path = runner.save_report_markdown(report, "final_holdout_evaluation.md")
        print(f"\nHoldout JSON: {json_path}")
        print(f"Holdout MD: {md_path}")
        _print_summary(report)

    elif args.mode == "full":
        # Run all three
        print("\n=== BASELINE ===")
        report_b = runner.run_evaluation(dev_cases, label="Baseline / Development")
        runner.save_report_json(report_b, "baseline_evaluation.json")
        runner.save_report_markdown(report_b, "baseline_evaluation.md")
        _print_summary(report_b)

        print("\n=== OPTIMIZED (same config for now) ===")
        report_o = runner.run_evaluation(dev_cases, label="Optimized / Development")
        runner.save_report_json(report_o, "optimized_evaluation.json")
        runner.save_report_markdown(report_o, "optimized_evaluation.md")
        _print_summary(report_o)

        print("\n=== HOLDOUT ===")
        report_h = runner.run_evaluation(holdout_cases, label="Optimized / Holdout")
        runner.save_report_json(report_h, "final_holdout_evaluation.json")
        runner.save_report_markdown(report_h, "final_holdout_evaluation.md")
        _print_summary(report_h)


def _print_summary(report):
    """Print a brief summary to console."""
    r = report.routing
    t = report.tools
    rag = report.rag
    s = report.safety
    lat = report.latency_ms
    print(f"\n  Routing Accuracy:       {r.get('accuracy', 0):.4f}")
    print(f"  Tool Selection Acc:     {t.get('selection_accuracy', 0):.4f}")
    print(f"  Tool Execution Success: {t.get('execution_success_rate', 0):.4f}")
    print(f"  RAG Hit@1:              {rag.get('hit_at_1', 0):.4f}")
    print(f"  RAG Hit@3:              {rag.get('hit_at_3', 0):.4f}")
    print(f"  RAG Hit@5:              {rag.get('hit_at_5', 0):.4f}")
    print(f"  RAG MRR:                {rag.get('mrr', 0):.4f}")
    print(f"  Response Grounding:     {report.response.get('grounding_rate', 0):.4f}")
    print(f"  Safety Success:         {s.get('safety_success_rate', 0):.4f}")
    print(f"  Latency p50:            {lat.get('p50_ms', 0):.2f} ms")
    print(f"  Latency p95:            {lat.get('p95_ms', 0):.2f} ms")
    print(f"  Failures:               {len(report.failures)}")


if __name__ == "__main__":
    main()
