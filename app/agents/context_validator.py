"""
Context Validator & Provenance Aggregator
=========================================
Validates tool and RAG execution outputs, preserves explicit source provenance,
and checks that retrieved information is grounded and sufficient to answer.
"""

from typing import Any, Dict, List, Tuple


class ContextValidator:
    """Validates retrieved execution context and assembles source-attributed payloads."""

    def validate_and_aggregate(
        self,
        route: str,
        tool_results: List[Dict[str, Any]],
        rag_results: List[Dict[str, Any]],
        customer_id: str | None = None,
    ) -> Tuple[List[Dict[str, Any]], str, List[Dict[str, Any]]]:
        """
        Aggregates tool and RAG results into a unified context list and extracts clean sources.

        Returns:
            Tuple of:
                - context: List of validated context items with source_type
                - status: "success" | "needs_customer_context" | "unsupported" | "error"
                - sources: Clean source summaries for output schema
        """
        context: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = []

        if route == "CLARIFICATION":
            return [], "needs_customer_context", []

        if route == "UNSUPPORTED":
            return [], "unsupported", []

        # 1. Process Tool Results
        seen_tools = set()
        for item in tool_results:
            context.append(item)
            tool_name = item.get("source", "")
            if item.get("success", False) and tool_name not in seen_tools:
                seen_tools.add(tool_name)
                sources.append({
                    "type": "tool",
                    "name": tool_name,
                })

        # 2. Process RAG Results
        seen_rag = set()
        for item in rag_results:
            context.append(item)
            if "error" not in item:
                src = item.get("source", "")
                sec = item.get("section", "")
                key = (src, sec)
                if key not in seen_rag:
                    seen_rag.add(key)
                    source_entry: Dict[str, Any] = {
                        "type": "rag",
                        "source": src,
                    }
                    if sec:
                        source_entry["section"] = sec
                    if item.get("document_id"):
                        source_entry["document_id"] = item.get("document_id")
                    if item.get("title"):
                        source_entry["title"] = item.get("title")
                    if item.get("chunk_id"):
                        source_entry["chunk_id"] = item.get("chunk_id")
                    if item.get("content"):
                        source_entry["snippet"] = item.get("content", "").strip()[:200]
                    sources.append(source_entry)

        # 3. Determine Overall Status
        # Check if errors occurred
        has_tool_error = any(not item.get("success", True) for item in tool_results)
        has_rag_error = any("error" in item for item in rag_results)

        if (route == "TOOL" and has_tool_error and not sources) or (
            route == "RAG" and has_rag_error and not sources
        ):
            status = "error"
        else:
            status = "success"

        return context, status, sources
