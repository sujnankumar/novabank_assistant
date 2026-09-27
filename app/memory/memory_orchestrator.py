"""
Memory-Aware Orchestration Layer
================================
Wraps the Phase 6 BankingOrchestrator with conversation memory capabilities:
- Enforces customer/conversation isolation
- Loads chronological history
- Contextualizes conversational follow-ups without altering authoritative sources
- Executes Phase 6 orchestrator
- Persists user query and grounded assistant response
"""

import re
import time
from typing import Any, Dict, List, Optional

from app.agents.orchestrator import BankingOrchestrator
from app.memory.config import MAX_HISTORY_MESSAGES
from app.memory.exceptions import (
    ConversationNotFoundError,
    CustomerMismatchError,
    InvalidMessageError,
)
from app.memory.interface import ConversationMemory
from app.memory.models import Message
from app.memory.sqlite_memory import SQLiteConversationMemory


class MemoryOrchestrator:
    """Coordinates conversational session memory with Phase 6 Banking Orchestrator."""

    # Product/topic keywords for contextual query resolution
    TOPIC_PATTERNS = {
        "home loans": [r"\bhome loans?\b", r"\bhousing loans?\b"],
        "personal loans": [r"\bpersonal loans?\b"],
        "education loans": [r"\beducation loans?\b", r"\bstudent loans?\b"],
        "vehicle loans": [r"\bvehicle loans?\b", r"\bcar loans?\b", r"\bauto loans?\b"],
        "fixed deposits": [r"\bfixed deposits?\b", r"\bfds?\b"],
        "recurring deposits": [r"\brecurring deposits?\b", r"\brds?\b"],
        "savings accounts": [r"\bsavings accounts?\b"],
        "current accounts": [r"\bcurrent accounts?\b"],
        "credit cards": [r"\bcredit cards?\b"],
        "dormant accounts": [r"\bdormant\b"],
        "fraud reporting": [r"\bfraud\b", r"\bfraudulent\b"],
        "account closure": [r"\bclose account\b", r"\bclosure\b"],
    }

    def __init__(
        self,
        memory: Optional[ConversationMemory] = None,
        orchestrator: Optional[BankingOrchestrator] = None,
        max_history: int = MAX_HISTORY_MESSAGES,
    ):
        self.memory = memory or SQLiteConversationMemory()
        self.orchestrator = orchestrator or BankingOrchestrator()
        self.max_history = max_history

    def _extract_active_topic(self, history: List[Message]) -> Optional[str]:
        """
        Inspects recent conversation turns (latest first) to identify the active banking product or topic.
        """
        for msg in reversed(history):
            content_lower = msg.content.lower()
            for topic_name, patterns in self.TOPIC_PATTERNS.items():
                if any(re.search(pat, content_lower) for pat in patterns):
                    return topic_name
        return None

    def _build_contextual_query(self, query: str, history: List[Message]) -> str:
        """
        Builds contextual input for the Phase 6 orchestrator by resolving follow-up
        references (e.g. 'What is the interest rate?' -> 'What is the interest rate for home loans?')
        while ensuring customer data and policies continue to come from authoritative sources.
        """
        if not history:
            return query

        q_lower = query.lower().strip()

        # If query already explicitly mentions a product or self-contained topic, do not mutate
        has_explicit_product = any(
            re.search(pat, q_lower)
            for patterns in self.TOPIC_PATTERNS.values()
            for pat in patterns
        )
        if has_explicit_product:
            return query

        # Detect follow-up signals that rely on previous conversational context
        follow_up_signals = [
            "interest rate", "rate", "eligibility", "eligible",
            "documents", "requirements", "tenure", "charges", "fees",
            "apply", "rules", "policy", "it", "that", "this"
        ]
        is_follow_up = any(re.search(rf"\b{re.escape(sig)}\b", q_lower) for sig in follow_up_signals)

        if not is_follow_up:
            return query

        active_topic = self._extract_active_topic(history)
        if not active_topic:
            return query

        # Resolve specific common follow-up phrasing naturally
        if "interest rate" in q_lower or "rate" in q_lower:
            return f"What is the interest rate for {active_topic}?"
        if "eligibility" in q_lower or "eligible" in q_lower:
            if "am i eligible" in q_lower:
                return f"Am I eligible for a {active_topic}?"
            return f"What are the eligibility requirements for {active_topic}?"
        if "document" in q_lower:
            return f"What documents are required for {active_topic}?"
        if "fee" in q_lower or "charge" in q_lower:
            return f"What are the fees and charges for {active_topic}?"
        if "rule" in q_lower or "policy" in q_lower:
            return f"What is the policy for {active_topic}?"

        # General context attachment
        clean_q = query.rstrip(".?")
        return f"{clean_q} regarding {active_topic}?"

    def run_conversation(
        self,
        conversation_id: str,
        customer_id: str,
        query: str,
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end memory-aware conversational turn.

        Steps:
            1. Validate conversation_id and customer_id.
            2. Load conversation history.
            3. Build contextual input for the Phase 6 orchestrator.
            4. Execute the Phase 6 orchestrator.
            5. Persist user message and final assistant response.
            6. Return the Phase 6 response.

        Parameters:
            conversation_id (str): Target conversation session ID.
            customer_id (str): Trusted customer identity (e.g. 'CUST001').
            query (str): Natural language customer input.

        Returns:
            Dict[str, Any]: Orchestrator response dictionary containing status, route, response, and sources.

        Raises:
            ConversationNotFoundError: If conversation does not exist.
            CustomerMismatchError: If customer_id does not match conversation owner.
            InvalidMessageError: If query is empty.
        """
        clean_conv_id = (conversation_id or "").strip()
        clean_cust_id = (customer_id or "").strip()

        if not clean_conv_id:
            raise ConversationNotFoundError("A valid conversation_id is required.")
        if not clean_cust_id:
            raise CustomerMismatchError("A valid customer_id is required.")

        # Validate query text
        if not isinstance(query, str) or not query.strip():
            raise InvalidMessageError("Query cannot be empty or whitespace only.")

        clean_query = query.strip()

        # Step 1 & 2: Validate identity and load history
        # get_history enforces that conversation exists and customer matches
        history = self.memory.get_history(
            conversation_id=clean_conv_id,
            customer_id=clean_cust_id,
            limit=self.max_history,
        )

        # Step 3: Build contextual input for Phase 6
        contextual_query = self._build_contextual_query(clean_query, history)

        # Step 4: Execute Phase 6 orchestrator with trusted customer identity
        t0 = time.time()
        output = self.orchestrator.run(
            query=contextual_query,
            customer_id=clean_cust_id,
        )
        elapsed = time.time() - t0
        elapsed_ms = round(elapsed * 1000, 1)
        output["execution_time_ms"] = elapsed_ms

        # Step 5: Persist user message and assistant response
        # Save actual user query (unaltered)
        self.memory.add_message(
            conversation_id=clean_conv_id,
            customer_id=clean_cust_id,
            role="user",
            content=clean_query,
        )

        # Save final assistant response (conversational text only, no raw tool objects)
        assistant_response = output.get("response")
        if assistant_response and isinstance(assistant_response, str) and assistant_response.strip():
            self.memory.add_message(
                conversation_id=clean_conv_id,
                customer_id=clean_cust_id,
                role="assistant",
                content=assistant_response.strip(),
                sources=output.get("sources"),
                thought_process=output.get("thought_process"),
                execution_time_ms=elapsed_ms,
            )

        # Step 6: Return orchestrator output
        return output


def run_conversation(
    conversation_id: str,
    customer_id: str,
    query: str,
    memory: Optional[ConversationMemory] = None,
    orchestrator: Optional[BankingOrchestrator] = None,
) -> Dict[str, Any]:
    """
    Convenience function executing an end-to-end memory-aware conversational turn.
    """
    runner = MemoryOrchestrator(memory=memory, orchestrator=orchestrator)
    return runner.run_conversation(
        conversation_id=conversation_id,
        customer_id=customer_id,
        query=query,
    )
