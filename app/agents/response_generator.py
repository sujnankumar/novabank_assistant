"""
Grounded Response Generator
===========================
Generates accurate, concise natural-language answers strictly grounded in retrieved
tool results and RAG context, following all NovaBank safety and anti-fabrication rules.
"""

from typing import Any, Dict, List, Optional
from app.agents.llm import BaseLLMClient, get_llm_client


class ResponseGenerator:
    """Generates grounded responses from validated execution context."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or get_llm_client()

    def generate(
        self,
        query: str,
        context: List[Dict[str, Any]],
        route: str,
        status: str,
        customer_id: Optional[str] = None,
        sub_queries: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Synthesizes the final natural-language response.

        Returns:
            Grounded response string.
        """
        return self.llm_client.generate_response(
            query=query,
            context=context,
            route=route,
            status=status,
            customer_id=customer_id,
            sub_queries=sub_queries,
        )
