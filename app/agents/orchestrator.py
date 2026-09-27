"""
NovaBank AI Orchestrator
========================
LangGraph-based coordinator connecting Query Routing, Phase 4 Banking Tools,
Phase 5 Qdrant RAG, Context Validation, and Grounded Response Generation.
"""

import uuid
from typing import Any, Dict, List, Optional
from langgraph.graph import END, START, StateGraph

from app.agents.config import MAX_STEPS, MAX_TOOL_CALLS
from app.agents.context_validator import ContextValidator
from app.agents.llm import BaseLLMClient, get_llm_client
from app.agents.rag_executor import RAGExecutor
from app.agents.response_generator import ResponseGenerator
from app.agents.router import QueryRouter
from app.agents.state import AgentState
from app.agents.tools_executor import ToolsExecutor


class BankingOrchestrator:
    """Coordinates customer query understanding, tool invocation, RAG retrieval, and grounded response synthesis."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        max_steps: int = MAX_STEPS,
        max_tool_calls: int = MAX_TOOL_CALLS,
        router: Optional[QueryRouter] = None,
        tools_executor: Optional[ToolsExecutor] = None,
        rag_executor: Optional[RAGExecutor] = None,
        context_validator: Optional[ContextValidator] = None,
        response_generator: Optional[ResponseGenerator] = None,
    ):
        self.llm_client = llm_client or get_llm_client()
        self.max_steps = max_steps
        self.max_tool_calls = max_tool_calls

        self.router = router or QueryRouter(llm_client=self.llm_client)
        self.tools_executor = tools_executor or ToolsExecutor(max_tool_calls=self.max_tool_calls)
        self.rag_executor = rag_executor or RAGExecutor()
        self.context_validator = context_validator or ContextValidator()
        self.response_generator = response_generator or ResponseGenerator(llm_client=self.llm_client)

        self._graph = self._build_graph()

    def _build_graph(self):
        """Constructs explicit, bounded LangGraph state graph."""
        builder = StateGraph(AgentState)

        # 1. Add explicit nodes
        builder.add_node("analyze_query", self._node_analyze_query)
        builder.add_node("route_query", self._node_route_query)
        builder.add_node("execute_tools", self._node_execute_tools)
        builder.add_node("retrieve_rag", self._node_retrieve_rag)
        builder.add_node("validate_context", self._node_validate_context)
        builder.add_node("generate_response", self._node_generate_response)

        # 2. Add transitions
        builder.add_edge(START, "analyze_query")
        builder.add_edge("analyze_query", "route_query")

        # Routing decision edge
        def _route_decision(state: AgentState) -> str:
            route = state.get("route", "UNSUPPORTED")
            if route == "TOOL":
                return "execute_tools"
            elif route == "RAG":
                return "retrieve_rag"
            elif route == "BOTH":
                return "execute_tools"
            else:
                return "validate_context"

        builder.add_conditional_edges(
            "route_query",
            _route_decision,
            {
                "execute_tools": "execute_tools",
                "retrieve_rag": "retrieve_rag",
                "validate_context": "validate_context",
            },
        )

        # Transition after execute_tools
        def _post_tools_decision(state: AgentState) -> str:
            if state.get("route") == "BOTH":
                return "retrieve_rag"
            return "validate_context"

        builder.add_conditional_edges(
            "execute_tools",
            _post_tools_decision,
            {
                "retrieve_rag": "retrieve_rag",
                "validate_context": "validate_context",
            },
        )

        builder.add_edge("retrieve_rag", "validate_context")
        builder.add_edge("validate_context", "generate_response")
        builder.add_edge("generate_response", END)

        return builder.compile()

    # ==================== Graph Node Implementations ====================

    def _node_analyze_query(self, state: AgentState) -> Dict[str, Any]:
        """Validates query format and initializes execution counters."""
        step = state.get("step_count", 0) + 1
        query = state.get("query", "").strip()
        query_snippet = f"'{query[:50]}...'" if len(query) > 50 else f"'{query}'"

        thought_step = {
            "node": "analyze_query",
            "title": "Analyzing inquiry",
            "description": f"Parsing natural language banking request: {query_snippet}",
            "type": "analysis",
        }

        if not query:
            return {
                "route": "UNSUPPORTED",
                "status": "unsupported",
                "response": "Query cannot be empty.",
                "step_count": step,
                "thought_steps": [thought_step],
            }

        return {"step_count": step, "thought_steps": [thought_step]}

    def _node_route_query(self, state: AgentState) -> Dict[str, Any]:
        """Classifies query intent into TOOL, RAG, BOTH, CLARIFICATION, or UNSUPPORTED."""
        step = state.get("step_count", 0) + 1

        # Check step limit
        if step > self.max_steps:
            return {
                "route": "UNSUPPORTED",
                "status": "error",
                "error": {"type": "step_limit_exceeded", "message": "Graph execution step limit reached."},
                "step_count": step,
            }

        route_info = self.router.route_query(
            query=state.get("query", ""),
            customer_id=state.get("customer_id"),
        )

        tool_calls = route_info.get("tool_calls", [])
        tool_names = [t.get("name") for t in tool_calls]

        if route_info["route"] == "TOOL":
            desc = f"Routing to transactional banking tools: {', '.join(tool_names) if tool_names else 'Account services'}"
        elif route_info["route"] == "RAG":
            desc = "Routing to NovaBank policy and product knowledge base search"
        elif route_info["route"] == "BOTH":
            desc = f"Hybrid query: executing tools ({', '.join(tool_names)}) and searching policy documents"
        elif route_info["route"] == "CLARIFICATION":
            desc = "Inquiry requires authenticated customer context or clarification"
        else:
            desc = "General conversational or unsupported banking query"

        thought_step = {
            "node": "route_query",
            "title": f"Routing query: {route_info['route']}",
            "description": desc,
            "type": "routing",
            "route": route_info["route"],
            "tools": tool_names,
        }

        return {
            "route": route_info["route"],
            "tool_calls": tool_calls,
            "selected_tools": tool_names,
            "step_count": step,
            "thought_steps": [thought_step],
        }

    def _node_execute_tools(self, state: AgentState) -> Dict[str, Any]:
        """Invokes Banking Tools with security constraints and tool call limits."""
        step = state.get("step_count", 0) + 1

        if step > self.max_steps:
            return {"step_count": step}

        tool_calls = state.get("tool_calls", [])
        trusted_cust_id = state.get("customer_id")
        current_count = state.get("tool_count", 0)

        exec_res = self.tools_executor.execute_tools(
            tool_calls=tool_calls,
            trusted_customer_id=trusted_cust_id,
            current_tool_count=current_count,
        )

        executed_names = [r.get("source") for r in exec_res["tool_results"]]
        thought_step = {
            "node": "execute_tools",
            "title": f"Executed banking tools ({len(executed_names)})",
            "description": f"Invoked APIs securely: {', '.join(executed_names)}" if executed_names else "Executed requested account operations",
            "type": "tool",
            "tools": executed_names,
        }

        return {
            "tool_results": exec_res["tool_results"],
            "tool_count": exec_res["new_tool_count"],
            "step_count": step,
            "thought_steps": [thought_step],
        }

    def _node_retrieve_rag(self, state: AgentState) -> Dict[str, Any]:
        """Executes Phase 5 Qdrant RAG retrieval."""
        step = state.get("step_count", 0) + 1

        if step > self.max_steps:
            return {"step_count": step}

        query = state.get("query", "")
        rag_results = self.rag_executor.retrieve(query=query)

        seen_sources = set()
        sources_found = []
        for r in rag_results:
            src = r.get("source")
            if src and "error" not in r and src not in seen_sources:
                seen_sources.add(src)
                sources_found.append(src)

        thought_step = {
            "node": "retrieve_rag",
            "title": f"Knowledge base search ({len(rag_results)} chunks found)",
            "description": f"Retrieved policy guidelines from: {', '.join(sources_found)}" if sources_found else "Queried NovaBank vector store",
            "type": "rag",
            "sources": sources_found,
        }

        return {
            "rag_results": rag_results,
            "step_count": step,
            "thought_steps": [thought_step],
        }

    def _node_validate_context(self, state: AgentState) -> Dict[str, Any]:
        """Validates outputs, aggregates provenance, and checks sufficiency."""
        step = state.get("step_count", 0) + 1

        route = state.get("route", "UNSUPPORTED")
        tool_results = state.get("tool_results", [])
        rag_results = state.get("rag_results", [])
        customer_id = state.get("customer_id")

        context, status, sources = self.context_validator.validate_and_aggregate(
            route=route,
            tool_results=tool_results,
            rag_results=rag_results,
            customer_id=customer_id,
        )

        thought_step = {
            "node": "validate_context",
            "title": f"Context validated ({len(context)} facts checked)",
            "description": f"Verified grounding & security constraints. Status: '{status}' with {len(sources)} source attribution(s).",
            "type": "validation",
            "status": status,
        }

        return {
            "context": context,
            "status": status,
            "sources": sources,
            "step_count": step,
            "thought_steps": [thought_step],
        }

    def _node_generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Produces the final grounded natural-language answer."""
        step = state.get("step_count", 0) + 1

        thought_step = {
            "node": "generate_response",
            "title": "Synthesizing grounded response",
            "description": "Composed final response strictly grounded on validated banking records and official policy documentation.",
            "type": "generation",
        }

        # Preserve any pre-set response (e.g. from empty query or step limit)
        if state.get("response"):
            return {"step_count": step, "thought_steps": [thought_step]}

        # Check step limit
        if step > self.max_steps:
            return {
                "status": "error",
                "response": "Execution limit exceeded. Please try asking a more specific question.",
                "step_count": step,
                "thought_steps": [thought_step],
            }

        response = self.response_generator.generate(
            query=state.get("query", ""),
            context=state.get("context", []),
            route=state.get("route", "UNSUPPORTED"),
            status=state.get("status", "success"),
            customer_id=state.get("customer_id"),
        )

        return {
            "response": response,
            "step_count": step,
            "thought_steps": [thought_step],
        }

    # ==================== Public Interface ====================

    def run(
        self,
        query: str,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end orchestration for a customer query.

        Parameters:
            query (str): The natural language query from the customer.
            customer_id (str, optional): Trusted customer ID context (e.g. "CUST001").

        Returns:
            dict containing:
                - status: "success" | "needs_customer_context" | "unsupported" | "error"
                - route: "TOOL" | "RAG" | "BOTH" | "CLARIFICATION" | "UNSUPPORTED"
                - response: Grounded natural language response string
                - sources: List of source provenance items
                - error: (optional) Structured error details if status is "error"
        """
        initial_state: AgentState = {
            "query": query,
            "customer_id": customer_id,
            "route": None,
            "selected_tools": [],
            "tool_calls": [],
            "tool_results": [],
            "rag_results": [],
            "context": [],
            "response": None,
            "status": "success",
            "sources": [],
            "error": None,
            "run_id": f"run_{uuid.uuid4().hex[:12]}",
            "step_count": 0,
            "tool_count": 0,
            "thought_steps": [],
        }

        # Execute through LangGraph
        final_state = self._graph.invoke(initial_state)

        output: Dict[str, Any] = {
            "status": final_state.get("status", "success"),
            "route": final_state.get("route", "UNSUPPORTED"),
            "response": final_state.get("response"),
            "sources": final_state.get("sources", []),
            "thought_process": final_state.get("thought_steps", []),
        }

        if final_state.get("error"):
            output["error"] = final_state["error"]

        return output
