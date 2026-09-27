"""
Evaluation Runner
=================
Executes the evaluation pipeline: loads cases, runs the system, evaluates results,
and produces machine-readable and human-readable reports.
"""

import json
import time
import platform
import datetime
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.evaluation.dataset import (
    load_config,
    load_evaluation_cases,
    load_route_mapping,
    deterministic_split,
    check_leakage,
    validate_cases,
)
from app.evaluation.evaluators import (
    RAGEvaluator,
    ResponseEvaluator,
    RoutingEvaluator,
    SafetyEvaluator,
    ToolEvaluator,
)
from app.evaluation.metrics import (
    compute_hit_at_k_metrics,
    compute_latency_stats,
    compute_response_metrics,
    compute_routing_metrics,
    compute_safety_metrics,
    compute_tool_metrics,
)
from app.evaluation.models import EvaluationCase, EvaluationReport, EvaluationResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


class EvaluationRunner:
    """Executes evaluation against the existing NovaBank system."""

    def __init__(
        self,
        orchestrator=None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.config = config or load_config()
        self._orchestrator = orchestrator

    def _get_orchestrator(self):
        """Lazy-load the orchestrator to avoid import-time side effects."""
        if self._orchestrator is None:
            from app.agents.orchestrator import BankingOrchestrator
            self._orchestrator = BankingOrchestrator()
        return self._orchestrator

    def run_single_case(self, case: EvaluationCase) -> EvaluationResult:
        """Execute a single evaluation case through the existing system."""
        orchestrator = self._get_orchestrator()

        # Time the execution
        start_time = time.perf_counter()
        try:
            system_output = orchestrator.run(
                query=case.query,
                customer_id=case.customer_id if case.customer_id else None,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return EvaluationResult(
                case_id=case.case_id,
                query=case.query,
                intent=case.intent,
                expected_route=case.expected_route,
                predicted_route="ERROR",
                route_correct=False,
                expected_tools=case.expected_tools,
                predicted_tools=[],
                tool_selection_correct=False,
                tool_execution_success=False,
                expected_sources=case.expected_sources,
                retrieved_sources=[],
                latency_ms=round(elapsed, 2),
                error=str(e),
            )

        elapsed = (time.perf_counter() - start_time) * 1000

        # Run evaluators
        routing_result = RoutingEvaluator.evaluate(case, system_output)
        tool_result = ToolEvaluator.evaluate(case, system_output)
        rag_result = RAGEvaluator.evaluate(case, system_output)
        response_result = ResponseEvaluator.evaluate(case, system_output)
        safety_result = SafetyEvaluator.evaluate(case, system_output)

        return EvaluationResult(
            case_id=case.case_id,
            query=case.query,
            intent=case.intent,
            expected_route=case.expected_route,
            predicted_route=routing_result["predicted_route"],
            route_correct=routing_result["route_correct"],
            expected_tools=case.expected_tools,
            predicted_tools=tool_result["predicted_tools"],
            tool_selection_correct=tool_result["tool_selection_correct"],
            tool_execution_success=tool_result["tool_execution_success"],
            expected_sources=case.expected_sources,
            retrieved_sources=rag_result["retrieved_sources"],
            rag_hit_at_1=rag_result["rag_hit_at_1"],
            rag_hit_at_3=rag_result["rag_hit_at_3"],
            rag_hit_at_5=rag_result["rag_hit_at_5"],
            rag_reciprocal_rank=rag_result["rag_reciprocal_rank"],
            response_grounded=response_result["response_grounded"],
            safety_passed=safety_result["safety_passed"],
            customer_isolation_passed=safety_result["customer_isolation_passed"],
            latency_ms=round(elapsed, 2),
            response_text=response_result.get("response_text", ""),
        )

    def run_evaluation(
        self,
        cases: List[EvaluationCase],
        label: str = "evaluation",
    ) -> EvaluationReport:
        """Run evaluation on a set of cases and compile report."""
        results: List[EvaluationResult] = []
        for case in cases:
            result = self.run_single_case(case)
            results.append(result)

        # Compile metrics
        routing_metrics = compute_routing_metrics(results)
        tool_metrics = compute_tool_metrics(results)
        rag_metrics = compute_hit_at_k_metrics(results)
        response_metrics = compute_response_metrics(results)
        safety_metrics = compute_safety_metrics(results)
        latencies = [r.latency_ms for r in results if r.latency_ms > 0]
        latency_stats = compute_latency_stats(latencies)

        # Compile failures
        failures = []
        for r in results:
            failure_reasons = []
            if not r.route_correct:
                failure_reasons.append(f"Route: expected={r.expected_route}, got={r.predicted_route}")
            if r.expected_tools and not r.tool_selection_correct:
                failure_reasons.append(f"Tools: expected={r.expected_tools}, got={r.predicted_tools}")
            if r.expected_sources and not r.rag_hit_at_1:
                failure_reasons.append(f"RAG: expected={r.expected_sources}, got={r.retrieved_sources}")
            if not r.safety_passed:
                failure_reasons.append("Safety check failed")
            if r.error:
                failure_reasons.append(f"Error: {r.error}")
            if failure_reasons:
                failures.append({
                    "case_id": r.case_id,
                    "query": r.query[:100],
                    "intent": r.intent,
                    "reasons": failure_reasons,
                })

        report = EvaluationReport(
            metadata={
                "phase": 10,
                "label": label,
                "seed": self.config.get("seed", 42),
                "dataset_version": self.config.get("dataset_version", "v1"),
                "mode": "offline",
                "total_cases": len(cases),
                "timestamp": datetime.datetime.now().isoformat(),
                "llm_provider": "mock",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "qdrant_collection": "novabank_knowledge",
                "retrieval_top_k": 4,
                "platform": platform.platform(),
            },
            routing=routing_metrics,
            tools=tool_metrics,
            rag=rag_metrics,
            response=response_metrics,
            safety=safety_metrics,
            latency_ms=asdict(latency_stats),
            failures=failures,
            results=[asdict(r) for r in results],
        )

        return report

    def save_report_json(self, report: EvaluationReport, filename: str):
        """Save evaluation report as JSON."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / filename
        data = asdict(report)
        # Remove full result details from JSON to keep it manageable
        summary_data = {k: v for k, v in data.items() if k != "results"}
        summary_data["total_results"] = len(data.get("results", []))
        path.write_text(json.dumps(summary_data, indent=2, default=str), encoding="utf-8")
        return path

    def save_report_markdown(self, report: EvaluationReport, filename: str) -> Path:
        """Generate human-readable Markdown evaluation report."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / filename

        md = report.metadata
        r = report.routing
        t = report.tools
        rag = report.rag
        resp = report.response
        safety = report.safety
        lat = report.latency_ms

        lines = [
            f"# NovaBank Phase 10 Evaluation Report - {md.get('label', 'Evaluation')}",
            "",
            f"**Generated:** {md.get('timestamp', 'N/A')}",
            f"**Dataset Version:** {md.get('dataset_version', 'v1')}",
            f"**Seed:** {md.get('seed', 42)}",
            f"**Mode:** {md.get('mode', 'offline')}",
            f"**Total Cases:** {md.get('total_cases', 0)}",
            f"**LLM Provider:** {md.get('llm_provider', 'mock')}",
            f"**Embedding Model:** {md.get('embedding_model', 'N/A')}",
            "",
            "---",
            "",
            "## Routing",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Accuracy | {r.get('accuracy', 0):.4f} |",
            f"| Total Evaluated | {r.get('total_evaluated', 0)} |",
            f"| Correct | {r.get('correct', 0)} |",
            "",
        ]

        # Per-route accuracy
        per_route = r.get("per_route_accuracy", {})
        if per_route:
            lines.append("### Per-Route Accuracy")
            lines.append("")
            lines.append("| Route | Accuracy |")
            lines.append("|-------|----------|")
            for route, acc in sorted(per_route.items()):
                lines.append(f"| {route} | {acc:.4f} |")
            lines.append("")

        # Confusion matrix
        cm = r.get("confusion_matrix", {})
        if cm:
            labels = sorted(cm.keys())
            lines.append("### Confusion Matrix")
            lines.append("")
            header = "| Expected \\ Predicted | " + " | ".join(labels) + " |"
            separator = "|" + "|".join(["---"] * (len(labels) + 1)) + "|"
            lines.append(header)
            lines.append(separator)
            for exp in labels:
                row = f"| **{exp}** | " + " | ".join(str(cm[exp].get(p, 0)) for p in labels) + " |"
                lines.append(row)
            lines.append("")

        # Tools
        lines.extend([
            "## Tools",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Selection Accuracy | {t.get('selection_accuracy', 0):.4f} |",
            f"| Execution Success Rate | {t.get('execution_success_rate', 0):.4f} |",
            f"| Precision | {t.get('precision', 0):.4f} |",
            f"| Recall | {t.get('recall', 0):.4f} |",
            f"| F1 | {t.get('f1', 0):.4f} |",
            f"| Tool-Evaluable Cases | {t.get('tool_evaluable_count', 0)} |",
            "",
        ])

        # RAG
        lines.extend([
            "## RAG Retrieval",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Hit@1 | {rag.get('hit_at_1', 0):.4f} |",
            f"| Hit@3 | {rag.get('hit_at_3', 0):.4f} |",
            f"| Hit@5 | {rag.get('hit_at_5', 0):.4f} |",
            f"| MRR | {rag.get('mrr', 0):.4f} |",
            f"| RAG-Evaluable Cases | {rag.get('rag_evaluable_count', 0)} |",
            "",
        ])

        # Response
        lines.extend([
            "## Response Quality",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Grounding Rate | {resp.get('grounding_rate', 0):.4f} |",
            f"| Evaluable Cases | {resp.get('evaluable_count', 0)} |",
            "",
        ])

        # Safety
        lines.extend([
            "## Safety",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Safety Success Rate | {safety.get('safety_success_rate', 0):.4f} |",
            f"| Customer Isolation Rate | {safety.get('customer_isolation_rate', 0):.4f} |",
            "",
        ])

        # Latency
        lines.extend([
            "## Latency",
            "",
            "| Metric | Value (ms) |",
            "|--------|-----------|",
            f"| Min | {lat.get('min_ms', 0):.2f} |",
            f"| Mean | {lat.get('mean_ms', 0):.2f} |",
            f"| Median | {lat.get('median_ms', 0):.2f} |",
            f"| p50 | {lat.get('p50_ms', 0):.2f} |",
            f"| p95 | {lat.get('p95_ms', 0):.2f} |",
            f"| Max | {lat.get('max_ms', 0):.2f} |",
            f"| Count | {lat.get('count', 0)} |",
            "",
        ])

        # Failures
        if report.failures:
            lines.extend([
                "## Failures",
                "",
                f"Total failures: {len(report.failures)}",
                "",
            ])
            for f in report.failures[:20]:
                lines.append(f"### {f['case_id']} ({f['intent']})")
                lines.append(f"**Query:** {f['query']}")
                for reason in f["reasons"]:
                    lines.append(f"- {reason}")
                lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path
