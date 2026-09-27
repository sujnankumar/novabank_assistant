"""
Multi-Intent Query Decomposer
=============================
Decomposes compound or multi-topic customer queries into structured, independent sub-queries.
Supports both deterministic rule-based analysis (for offline/tests) and live LLM decomposition.
Preserves customer isolation and strict anti-injection guardrails.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.agents.llm import BaseLLMClient, get_llm_client

logger = logging.getLogger("novabank.decomposer")

# Canonical banking products and normalized names
BANKING_PRODUCTS: List[Tuple[str, str]] = [
    ("credit card", "credit card"),
    ("home loan", "home loan"),
    ("housing loan", "home loan"),
    ("education loan", "education loan"),
    ("student loan", "education loan"),
    ("personal loan", "personal loan"),
    ("vehicle loan", "vehicle loan"),
    ("car loan", "vehicle loan"),
    ("auto loan", "vehicle loan"),
    ("fixed deposit", "fixed deposit"),
    ("fd", "fixed deposit"),
    ("savings account", "savings account"),
    ("recurring deposit", "recurring deposit"),
    ("rd", "recurring deposit"),
    ("fraud prevention", "fraud prevention"),
    ("account closure", "account closure"),
]

# Tool signal patterns and tool names
TOOL_PATTERNS: List[Tuple[str, List[str]]] = [
    ("get_balance", ["balance", "account balance", "how much money", "funds available", "current balance"]),
    ("get_transactions", ["recent transactions", "transaction history", "statement", "latest transactions", "past transactions", "transaction", "transactions", "purchases", "payments"]),
    ("get_transaction_summary", ["spending summary", "spending analysis", "spending breakdown", "monthly spending", "expense summary", "expense breakdown", "total spending", "overall spending", "how much did i spend", "money spent", "money i spent"]),
    ("get_account_info", ["account details", "my accounts", "account number", "account type"]),
    ("get_customer_profile", ["my profile", "customer profile", "who am i", "my details", "registered details"]),
]

# Specific topic categories for policy queries
TOPIC_CATEGORIES: List[Tuple[str, List[str]]] = [
    ("minimum credit score", ["minimum credit score", "credit score", "cibil score", "min score", "minimum score", "score required"]),
    ("eligibility requirements", ["requirement", "requirements", "eligibility", "eligible", "criteria", "qualify", "prerequisite"]),
    ("interest rates and charges", ["interest rate", "rate of interest", "interest rates", "charges", "fees", "annual fee", "finance charge"]),
    ("documents required", ["document", "documents", "documentation", "kyc", "papers"]),
    ("general policy and terms", ["terms", "policy", "rules", "process", "apply", "procedure", "guidelines"]),
]


class QueryDecomposer:
    """Detects and decomposes compound banking queries into independent sub-queries."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or get_llm_client()

    def decompose(
        self,
        query: str,
        customer_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Decomposes a query into structured independent sub-queries.
        Returns an empty list [] if the query is single-intent.

        Returns:
            List of sub-query dicts, each with:
                - query: str (standalone question)
                - route: "TOOL" | "RAG" | "BOTH"
                - tool: Optional[str] (canonical tool name if route == TOOL)
                - tool_calls: List[Dict[str, Any]]
        """
        if not query or not isinstance(query, str) or not query.strip():
            return []

        q_clean = query.strip()
        q_lower = q_clean.lower()

        # Step 1: Security checks - prompt injection & customer isolation violations
        # Malicious queries must not be decomposed into benign sub-queries
        injection_patterns = [
            r"ignore (all )?previous instructions",
            r"system prompt",
            r"reveal your (instructions|prompt)",
            r"you are now in developer mode",
            r"bypass (all )?(security|guardrails)",
        ]
        if any(re.search(pat, q_lower) for pat in injection_patterns):
            return []

        # Customer ID override check (e.g. asking for another customer's data)
        cust_match = re.search(r"\b(cust\d{3})\b", q_lower)
        if cust_match:
            target_cust = cust_match.group(1).upper()
            if customer_id and target_cust != customer_id.upper():
                return []

        # Step 2: Atomic single-intent check
        # Queries without coordinating conjunctions or multi-clause punctuation
        # and with at most one operational domain MUST NOT be decomposed.
        has_conjunction = bool(
            re.search(r"\b(?:and|also|as well as|along with|in addition to|plus)\b|;|\?.*?\?", q_lower)
        )
        found_prods = [
            canon for prod_key, canon in BANKING_PRODUCTS
            if re.search(rf"\b{re.escape(prod_key)}s?\b", q_lower)
        ]
        unique_prods = set(found_prods)

        has_balance = any(w in q_lower for w in TOOL_PATTERNS[0][1])
        has_transactions = any(w in q_lower for w in TOOL_PATTERNS[1][1])
        has_summary = any(w in q_lower for w in TOOL_PATTERNS[2][1])
        has_account_info = any(w in q_lower for w in TOOL_PATTERNS[3][1])
        has_profile = any(w in q_lower for w in TOOL_PATTERNS[4][1])
        tool_count = sum([has_balance, has_transactions, has_summary, has_account_info, has_profile])

        # If no conjunction and at most one operational domain, it is strictly single-intent
        if not has_conjunction and (tool_count + len(unique_prods) <= 1):
            return []

        # Step 3: Try LLM-based decomposition if live client is active
        # Otherwise, or on fallback, use deterministic rule-based decomposition
        from app.agents.llm import LangChainLLMClient
        if isinstance(self.llm_client, LangChainLLMClient) and getattr(self.llm_client, "_llm", None) is not None:
            try:
                sub_queries = self._llm_decompose(q_clean, customer_id)
                if sub_queries:
                    return sub_queries
            except Exception as e:
                logger.warning(f"[DECOMPOSER] LLM decomposition failed: {e}. Falling back to rule-based.")

        return self._rule_based_decompose(q_clean, customer_id)

    def _rule_based_decompose(
        self,
        query: str,
        customer_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Deterministic decomposition for offline environments, test suites, and fallbacks.
        Identifies independent intents by analyzing product domains, tool signals, and conjunctions.
        """
        q_lower = query.lower()

        # 1. Identify all distinct products mentioned
        found_products: List[Tuple[str, str]] = []
        for prod_key, canon_name in BANKING_PRODUCTS:
            pattern = rf"\b{re.escape(prod_key)}s?\b"
            if re.search(pattern, q_lower):
                if canon_name not in [p[1] for p in found_products]:
                    found_products.append((prod_key, canon_name))

        # 2. Identify tool intents
        has_balance = any(w in q_lower for w in TOOL_PATTERNS[0][1])
        has_transactions = any(w in q_lower for w in TOOL_PATTERNS[1][1])
        has_summary = any(w in q_lower for w in TOOL_PATTERNS[2][1])
        has_account_info = any(w in q_lower for w in TOOL_PATTERNS[3][1])
        has_profile = any(w in q_lower for w in TOOL_PATTERNS[4][1])

        tool_count = sum([has_balance, has_transactions, has_summary, has_account_info, has_profile])
        product_count = len(found_products)

        # Total distinct operational domains
        total_intents = tool_count + product_count

        # If 0 or 1 domain, this is a single-intent query: do not decompose
        if total_intents <= 1:
            return []

        # If query is comparing products within a single topic (e.g. "difference between savings and current account")
        if "difference" in q_lower or "compare" in q_lower or "versus" in q_lower or " vs " in q_lower:
            return []

        sub_queries: List[Dict[str, Any]] = []

        # 3. Add Tool Sub-Queries
        if has_balance:
            sub_queries.append({
                "query": "What is my account balance?",
                "route": "TOOL",
                "tool": "get_balance",
                "tool_calls": [{"name": "get_balance", "args": {"customer_id": customer_id} if customer_id else {}}],
            })
        if has_transactions:
            from app.agents.transaction_query_parser import parse_transaction_query
            # Split clauses by punctuation or coordinating conjunctions to isolate transaction query
            clauses = re.split(r"[,;]|\s+(?:and|also|as well as)\s+", query, flags=re.IGNORECASE)
            matching_clause = next(
                (c.strip() for c in clauses if any(w in c.lower() for w in ["transaction", "statement", "purchases", "payments"])),
                "",
            )
            target_txn_text = matching_clause if matching_clause else query

            parsed = parse_transaction_query(target_txn_text, customer_id=customer_id)
            txn_args: Dict[str, Any] = {
                "customer_id": customer_id,
                "limit": parsed["limit"],
                "sort": "desc",
            }
            if parsed.get("category"):
                txn_args["category"] = parsed["category"]
            if parsed.get("start_date"):
                txn_args["start_date"] = parsed["start_date"]
            if parsed.get("end_date"):
                txn_args["end_date"] = parsed["end_date"]
            if parsed.get("account_id"):
                txn_args["account_id"] = parsed["account_id"]

            sub_q_text = matching_clause if matching_clause else "What are my recent transactions?"
            if not sub_q_text.endswith("?"):
                sub_q_text = sub_q_text[0].upper() + sub_q_text[1:]

            sub_queries.append({
                "query": sub_q_text,
                "route": "TOOL",
                "tool": "get_transactions",
                "parameters": txn_args,
                "tool_calls": [{"name": "get_transactions", "args": txn_args}],
            })
        if has_summary and (not has_transactions or "summary" in q_lower or "expense" in q_lower):
            from app.agents.transaction_query_parser import extract_category, resolve_date_range
            cat = extract_category(query)
            s_d, e_d, _ = resolve_date_range(query)
            sum_args: Dict[str, Any] = {"customer_id": customer_id}
            if cat:
                sum_args["category"] = cat
            if s_d:
                sum_args["start_date"] = s_d
            if e_d:
                sum_args["end_date"] = e_d
            sub_queries.append({
                "query": "What is my transaction spending summary?",
                "route": "TOOL",
                "tool": "get_transaction_summary",
                "tool_calls": [{"name": "get_transaction_summary", "args": sum_args}],
            })
        if has_account_info and not has_balance:
            sub_queries.append({
                "query": "What are my registered account details?",
                "route": "TOOL",
                "tool": "get_account_info",
                "tool_calls": [{"name": "get_account_info", "args": {"customer_id": customer_id} if customer_id else {}}],
            })
        if has_profile:
            sub_queries.append({
                "query": "What are my registered customer details?",
                "route": "TOOL",
                "tool": "get_customer_profile",
                "tool_calls": [{"name": "get_customer_profile", "args": {"customer_id": customer_id} if customer_id else {}}],
            })

        # 4. Add Product RAG Sub-Queries
        # Split clauses by punctuation or coordinating conjunctions to inspect per-product context
        clauses = re.split(r"[,;]|\s+(?:and|also|as well as)\s+", query, flags=re.IGNORECASE)

        for prod_key, canon_name in found_products:
            # Locate clause that explicitly mentions this product
            matching_clause = next((c for c in clauses if prod_key in c.lower()), "")
            target_text = matching_clause if matching_clause else query

            # Detect topic for this specific product
            detected_topic = "general policy and terms"
            for topic_name, keywords in TOPIC_CATEGORIES:
                if any(kw in target_text.lower() for kw in keywords):
                    detected_topic = topic_name
                    break

            # If not found in local clause, fall back to global query topic
            if detected_topic == "general policy and terms":
                for topic_name, keywords in TOPIC_CATEGORIES:
                    if any(kw in query.lower() for kw in keywords):
                        detected_topic = topic_name
                        break

            # Construct clear, self-contained sub-query
            if detected_topic == "minimum credit score":
                sub_q = f"What is the minimum credit score required for a NovaBank {canon_name}?"
            elif detected_topic == "eligibility requirements":
                sub_q = f"What are the requirements to get a NovaBank {canon_name}?"
            elif detected_topic == "interest rates and charges":
                sub_q = f"What are the interest rates and charges for a NovaBank {canon_name}?"
            elif detected_topic == "documents required":
                sub_q = f"What documents are required for a NovaBank {canon_name}?"
            else:
                sub_q = f"What are the terms and policy guidelines for a NovaBank {canon_name}?"

            sub_queries.append({
                "query": sub_q,
                "route": "RAG",
                "tool": None,
                "tool_calls": [],
            })

        # Final check: if only 1 sub-query resulted, it is not compound
        if len(sub_queries) <= 1:
            return []

        return sub_queries

    def _llm_decompose(
        self,
        query: str,
        customer_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Uses live LLM client to decompose complex queries when available with strict grounding verification."""
        from langchain_core.messages import SystemMessage, HumanMessage
        import json

        q_lower = query.lower()
        prompt = (
            "You are a banking query analyzer. Decompose compound multi-topic queries into independent, "
            "self-contained sub-queries.\n"
            "STRICT RULES:\n"
            "- If the query asks for only a single topic or transaction query, return JSON: {\"is_compound\": false, \"sub_queries\": []}\n"
            "- NEVER invent or hallucinate banking products or loan types that are NOT explicitly mentioned in the query.\n"
            "- If the query asks for multiple independent topics, return JSON:\n"
            "{\n"
            "  \"is_compound\": true,\n"
            "  \"sub_queries\": [\n"
            "    {\"query\": \"...standalone question...\", \"route\": \"TOOL|RAG\", \"tool\": \"get_balance|get_transactions|null\"}\n"
            "  ]\n"
            "}\n"
            f"Query: {query}"
        )

        res = self.llm_client._llm.invoke([HumanMessage(content=prompt)])
        content = res.content if hasattr(res, "content") else str(res)

        if "{" in content and "}" in content:
            json_str = content[content.find("{"):content.rfind("}") + 1]
            data = json.loads(json_str)
            if not data.get("is_compound", False):
                return []
            raw_sub = data.get("sub_queries", [])
            sub_queries = []
            for item in raw_sub:
                q_text = item.get("query", "").strip()
                route = item.get("route", "RAG").upper()
                tool_name = item.get("tool")
                if not q_text:
                    continue

                # Strict grounding check:
                # If sub-query mentions a banking product, that product must appear in the user's query
                unsupported_product = False
                for prod_key, canon_name in BANKING_PRODUCTS:
                    if (prod_key in q_text.lower() or canon_name in q_text.lower()) and (prod_key not in q_lower and canon_name not in q_lower):
                        unsupported_product = True
                        break
                if unsupported_product:
                    continue

                # If sub-query route is RAG, verify original query actually asked a policy/general question
                if route == "RAG":
                    has_policy_signal = any(
                        p in q_lower for p in ["policy", "rules", "eligibility", "requirement", "interest", "terms", "document", "fee", "cibil", "score", "how do i"]
                    ) or any(prod_key in q_lower for prod_key, _ in BANKING_PRODUCTS)
                    if not has_policy_signal:
                        continue

                tc = []
                params: Dict[str, Any] = {}
                if route == "TOOL" and tool_name:
                    args = {"customer_id": customer_id} if customer_id else {}
                    if tool_name == "get_transactions":
                        from app.agents.transaction_query_parser import parse_transaction_query
                        parsed = parse_transaction_query(q_text, customer_id=customer_id)
                        args["limit"] = parsed["limit"]
                        args["sort"] = "desc"
                        if parsed.get("category"):
                            args["category"] = parsed["category"]
                        if parsed.get("start_date"):
                            args["start_date"] = parsed["start_date"]
                        if parsed.get("end_date"):
                            args["end_date"] = parsed["end_date"]
                        if parsed.get("account_id"):
                            args["account_id"] = parsed["account_id"]
                    elif tool_name == "get_transaction_summary":
                        from app.agents.transaction_query_parser import extract_category, resolve_date_range
                        cat = extract_category(q_text) or extract_category(query)
                        s_d, e_d, _ = resolve_date_range(q_text)
                        if cat:
                            args["category"] = cat
                        if s_d:
                            args["start_date"] = s_d
                        if e_d:
                            args["end_date"] = e_d
                    params = args
                    tc = [{"name": tool_name, "args": args}]
                sub_queries.append({
                    "query": q_text,
                    "route": route,
                    "tool": tool_name,
                    "parameters": params,
                    "tool_calls": tc,
                })
            if len(sub_queries) > 1:
                return sub_queries

        return []
