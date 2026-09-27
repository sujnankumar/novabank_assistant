"""
Query Router & Intent Classifier
================================
Classifies customer queries into strictly validated routes:
  - TOOL
  - RAG
  - BOTH
  - CLARIFICATION
  - UNSUPPORTED
"""

from typing import Any, Dict, List, Optional, Set
from app.agents.llm import BaseLLMClient, get_llm_client

ALLOWED_ROUTES: Set[str] = {"TOOL", "RAG", "BOTH", "CLARIFICATION", "UNSUPPORTED"}


class QueryRouter:
    """Classifies queries and determines tool execution plans using the configured LLM client."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or get_llm_client()

    def route_query(
        self,
        query: str,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classifies incoming query into one of the 5 allowed routes and prepares candidate tool calls.

        Returns:
            dict containing:
                - route: validated string in ALLOWED_ROUTES
                - reason: explanatory string
                - tool_calls: list of candidate tool definitions
        """
        # Validate query string
        if not query or not isinstance(query, str) or not query.strip():
            return {
                "route": "UNSUPPORTED",
                "reason": "Query string is empty or invalid.",
                "tool_calls": [],
            }

        # Invoke LLM client classification
        result = self.llm_client.classify_route(query.strip(), customer_id)

        raw_route = str(result.get("route", "")).strip().upper()

        # Constrain route strictly to ALLOWED_ROUTES
        route = raw_route if raw_route in ALLOWED_ROUTES else "UNSUPPORTED"
        tools = result.get("tools", []) if route in ("TOOL", "BOTH") else []

        # Format candidate tool calls
        formatted_tool_calls: List[Dict[str, Any]] = []
        for t in tools:
            name = t.get("name")
            args = t.get("args", {})
            if name:
                # Enforce customer_id if present
                if customer_id and "customer_id" in args:
                    args["customer_id"] = customer_id
                formatted_tool_calls.append({"name": name, "args": args})

        return {
            "route": route,
            "reason": result.get("reason", "Route determined successfully."),
            "tool_calls": formatted_tool_calls,
        }
