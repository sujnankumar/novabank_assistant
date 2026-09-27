"""
Evaluation Data Models
======================
Typed representations for evaluation cases, results, and reports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvaluationCase:
    """A single evaluation test case."""
    case_id: str
    query_id: str
    query: str
    customer_id: str
    intent: str
    expected_route: str
    expected_tools: List[str]
    expected_sources: List[str]
    category: str
    expected_agent: str = ""
    expected_data_source: str = ""


@dataclass
class EvaluationResult:
    """Result of evaluating a single case."""
    case_id: str
    query: str
    intent: str
    expected_route: str
    predicted_route: str
    route_correct: bool
    expected_tools: List[str]
    predicted_tools: List[str]
    tool_selection_correct: bool
    tool_execution_success: bool
    expected_sources: List[str]
    retrieved_sources: List[str]
    rag_hit_at_1: bool = False
    rag_hit_at_3: bool = False
    rag_hit_at_5: bool = False
    rag_reciprocal_rank: float = 0.0
    response_grounded: bool = False
    safety_passed: bool = True
    customer_isolation_passed: bool = True
    latency_ms: float = 0.0
    response_text: str = ""
    error: Optional[str] = None
    component_latencies: Dict[str, float] = field(default_factory=dict)


@dataclass
class LatencyStats:
    """Latency statistics."""
    min_ms: float = 0.0
    mean_ms: float = 0.0
    median_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    max_ms: float = 0.0
    count: int = 0


@dataclass
class EvaluationReport:
    """Complete evaluation report."""
    metadata: Dict[str, Any] = field(default_factory=dict)
    routing: Dict[str, Any] = field(default_factory=dict)
    tools: Dict[str, Any] = field(default_factory=dict)
    rag: Dict[str, Any] = field(default_factory=dict)
    response: Dict[str, Any] = field(default_factory=dict)
    safety: Dict[str, Any] = field(default_factory=dict)
    latency_ms: Dict[str, Any] = field(default_factory=dict)
    failures: List[Dict[str, Any]] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
