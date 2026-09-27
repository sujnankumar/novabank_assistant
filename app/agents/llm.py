"""
LLM Provider Abstraction & Factory
==================================
Pluggable LLM interfaces supporting both local deterministic rule-based execution
(for testing and offline runs) and live LangChain/OpenAI providers.
"""

import abc
import os
import re
from typing import Any, Dict, List, Optional
from app.agents.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_PROVIDER
from app.agents.prompts import RESPONSE_GENERATION_SYSTEM_PROMPT, ROUTING_SYSTEM_PROMPT


class BaseLLMClient(abc.ABC):
    """Abstract interface for LLM operations in the banking assistant."""

    @abc.abstractmethod
    def classify_route(
        self,
        query: str,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze query and return route ('TOOL', 'RAG', 'BOTH', 'CLARIFICATION', 'UNSUPPORTED')
        along with any initial tool recommendations.
        """
        pass

    @abc.abstractmethod
    def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        route: str,
        status: str,
        customer_id: Optional[str] = None,
    ) -> str:
        """
        Generate grounded natural language response strictly from supplied context.
        """
        pass


class RuleBasedLLMClient(BaseLLMClient):
    """
    Deterministic LLM client for offline execution and automated test suites.
    Performs semantic keyword classification and grounded template rendering
    without requiring external API keys.
    """

    def classify_route(
        self,
        query: str,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        q_lower = query.lower().strip()

        # Prompt injection detection
        injection_patterns = [
            r"ignore (all )?previous instructions",
            r"system prompt",
            r"reveal your (instructions|prompt)",
            r"you are now in developer mode",
            r"bypass (all )?(security|guardrails)",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, q_lower):
                return {
                    "route": "UNSUPPORTED",
                    "reason": "Security violation: prompt injection attempt detected.",
                    "tools": [],
                }

        # Check for unauthorized customer ID override attempts
        # e.g., "give me CUST002's balance" when customer_id is CUST001 or None
        cust_match = re.search(r"\b(cust\d{3})\b", q_lower)
        if cust_match:
            target_cust = cust_match.group(1).upper()
            if customer_id and target_cust != customer_id.upper():
                return {
                    "route": "UNSUPPORTED",
                    "reason": f"Unauthorized access: cannot query data for {target_cust}.",
                    "tools": [],
                }

        # Out-of-domain checks
        unsupported_keywords = [
            "quantum", "spacecraft", "propulsion", "recipe", "weather in",
            "capital of", "movie", "song", "poem", "sports score"
        ]
        if any(w in q_lower for w in unsupported_keywords):
            return {
                "route": "UNSUPPORTED",
                "reason": "Query is outside NovaBank banking domain.",
                "tools": [],
            }

        # Customer-specific signals
        customer_specific_signals = [
            "my balance", "account balance", "my account", "my current balance",
            "my transactions", "recent transactions", "transaction history",
            "show my transaction", "what accounts do i have", "my profile",
            "my details", "am i eligible", "check my eligibility", "eligible for a",
            "loans available to me", "my customer id", "can i afford",
            "my name", "what is my name", "who am i", "who i am", "what's my name",
            "my info", "personal details", "about me", "my city", "my occupation",
            "my income", "my salary", "my credit score", "my age", "how old am i",
            "where do i live", "my job", "what is my job", "tell me about me",
            "tell me about myself", "who is logged in", "logged in user", "who am i logged in as"
        ]
        is_customer_specific = any(s in q_lower for s in customer_specific_signals)

        # General policy signals (RAG)
        policy_signals = [
            "policy", "rules", "eligibility requirements", "interest rate",
            "fixed deposit", "home loan policy", "savings account rules",
            "vehicle loan", "education loan", "personal loan policy",
            "how do i report", "report a fraudulent", "fraud", "closure rules",
            "how to close", "dormant account", "minimum balance", "documents required",
            "what documents", "charges", "fees", "what is a fixed deposit", "what is an fd"
        ]
        is_policy = any(p in q_lower for p in policy_signals)

        # If customer query asks for other customers without authorization
        if "cust" in q_lower and not customer_id:
            # Explicit customer ID in query but no authenticated context
            is_customer_specific = True

        # Check for BOTH (Mixed queries)
        # e.g., "What is my current balance and what is the minimum balance requirement?"
        # "Am I eligible for a home loan and what documents are required?"
        if is_customer_specific and is_policy:
            if not customer_id:
                return {
                    "route": "CLARIFICATION",
                    "reason": "Customer-specific context required for balance/eligibility part of the query.",
                    "tools": [],
                }
            return {
                "route": "BOTH",
                "reason": "Query requests both customer data and bank policy.",
                "tools": self._determine_tools(q_lower, customer_id),
            }

        # TOOL-only
        if is_customer_specific:
            if not customer_id:
                return {
                    "route": "CLARIFICATION",
                    "reason": "Customer identification is required for this request.",
                    "tools": [],
                }
            tools = self._determine_tools(q_lower, customer_id)
            return {
                "route": "TOOL",
                "reason": "Customer-specific banking tool requested.",
                "tools": tools,
            }

        # RAG-only
        if is_policy:
            return {
                "route": "RAG",
                "reason": "General NovaBank policy or procedure requested.",
                "tools": [],
            }

        # Fallback for general bank products or interest rates
        if "interest" in q_lower or "rate" in q_lower or "product" in q_lower or "loan" in q_lower:
            return {
                "route": "RAG",
                "reason": "General product or interest rate information requested.",
                "tools": [],
            }

        # Fallback to UNSUPPORTED for completely unrecognized queries
        return {
            "route": "UNSUPPORTED",
            "reason": "Unable to map query to known banking tools or knowledge base policies.",
            "tools": [],
        }

    def _determine_tools(self, q_lower: str, customer_id: Optional[str]) -> List[Dict[str, Any]]:
        """Identify candidate banking tools based on customer query."""
        tools: List[Dict[str, Any]] = []

        # Customer identity & demographic details
        if any(w in q_lower for w in [
            "name", "who am i", "who i am", "who's", "who is", "about me", "my info",
            "detail", "customer", "city", "occupation", "job", "income", "salary",
            "credit score", "credit", "age", "gender", "where do i live", "logged in",
            "personal details", "profile"
        ]):
            tools.append({"name": "get_customer_details", "args": {"customer_id": customer_id}})

        # Account balances
        if "balance" in q_lower:
            tools.append({"name": "get_balance", "args": {"customer_id": customer_id}})

        # Transactions
        if "transaction" in q_lower:
            if "summary" in q_lower:
                tools.append({"name": "get_transaction_summary", "args": {"customer_id": customer_id}})
            else:
                tools.append({"name": "get_transactions", "args": {"customer_id": customer_id, "limit": 5}})

        # Accounts list
        if "account" in q_lower and "balance" not in q_lower:
            tools.append({"name": "get_accounts", "args": {"customer_id": customer_id}})

        # Loan eligibility
        if "eligible" in q_lower or "eligibility" in q_lower or "can i afford" in q_lower:
            loan_id = "LOAN001"
            if "vehicle" in q_lower:
                loan_id = "LOAN004"
            elif "personal" in q_lower:
                loan_id = "LOAN002"
            elif "education" in q_lower:
                loan_id = "LOAN003"

            amount_match = re.search(r"(\d+[\d,]*\d*)", q_lower)
            amount = 5000000.0
            if amount_match:
                cleaned = amount_match.group(1).replace(",", "")
                try:
                    val = float(cleaned)
                    if val > 1000:
                        amount = val
                except ValueError:
                    pass

            tools.append({
                "name": "check_loan_eligibility",
                "args": {
                    "customer_id": customer_id,
                    "loan_id": loan_id,
                    "requested_amount": amount,
                },
            })

        # Default fallback if customer query was detected but no specific tool matched
        if not tools and customer_id:
            tools.append({"name": "get_customer_details", "args": {"customer_id": customer_id}})

        return tools

    def _clean_section_title(self, section: str) -> str:
        """Strip numeric prefixes, punctuation, and FAQ question prefixes from section titles."""
        if not section:
            return ""
        clean = section.strip()
        # Remove FAQ prefixes (e.g. 'Q: What is a fixed deposit (FD)?' -> 'What is a fixed deposit (FD)?')
        clean = re.sub(r"^(Q\s*[:\.]\s*|Question\s*[:\.]\s*|FAQ\s*[:\.]\s*)", "", clean, flags=re.IGNORECASE)
        # Remove leading numbering and punctuation (e.g. '14. Co-applicants' -> 'Co-applicants', '4.1 Age Requirements' -> 'Age Requirements')
        clean = re.sub(r"^\d+(\.\d+)*[\.\:\-\)]?\s*", "", clean).strip()

        # If title is a full question (e.g. "What are the eligibility criteria for a NovaBank home loan?"), don't repeat it as a heading
        if clean.endswith("?") or re.match(r"^(what|how|can|why|where|is|are|do|does)\b", clean, flags=re.IGNORECASE):
            # Extract core subject or leave blank to avoid repeating question
            if "eligib" in clean.lower():
                return "Eligibility Criteria"
            elif "rate" in clean.lower() or "interest" in clean.lower():
                return "Interest Rates & Charges"
            elif "document" in clean.lower():
                return "Documentation Requirements"
            elif "apply" in clean.lower():
                return "Application Process"
            return ""

        return clean

    def _synthesize_rag_items(self, query: str, rag_items: List[Dict[str, Any]]) -> str:
        """Synthesizes RAG context chunks into clean, natural, ChatGPT-quality markdown."""
        if not rag_items:
            return ""

        q_lower = query.lower()

        # Identify banking product or policy topic for friendly context
        topic = "NovaBank Policy"
        if "home loan" in q_lower:
            topic = "NovaBank Home Loans"
        elif "fixed deposit" in q_lower or "fd" in q_lower:
            topic = "NovaBank Fixed Deposits"
        elif "savings" in q_lower:
            topic = "NovaBank Savings Accounts"
        elif "vehicle" in q_lower or "car loan" in q_lower:
            topic = "NovaBank Vehicle Loans"
        elif "education" in q_lower:
            topic = "NovaBank Education Loans"
        elif "personal loan" in q_lower:
            topic = "NovaBank Personal Loans"
        elif "fraud" in q_lower:
            topic = "Fraud Prevention & Account Security"
        elif "close" in q_lower or "dormant" in q_lower:
            topic = "Account Maintenance & Closure"

        # Determine a natural introductory phrase based on query intent
        if "rate" in q_lower or "interest" in q_lower:
            intro = f"Here are the current interest rates and terms for **{topic}**:"
        elif "eligible" in q_lower or "eligibility" in q_lower or "requirement" in q_lower:
            intro = f"Here are the eligibility criteria and requirements for **{topic}**:"
        elif "document" in q_lower:
            intro = f"Here are the required documents and procedures for **{topic}**:"
        else:
            intro = f"Here is the relevant information regarding **{topic}**:"

        # Prioritize chunks from the primary matching document or query domain
        primary_doc = rag_items[0].get("source", "")
        domain_keyword = primary_doc.split("_")[1] if "_" in primary_doc else ""
        relevant_chunks = [
            it for it in rag_items
            if (domain_keyword and domain_keyword in it.get("source", "")) or it.get("source") == primary_doc
        ]
        items_to_use = relevant_chunks if relevant_chunks else rag_items

        sections_content: List[str] = []
        seen_snippets = set()

        for item in items_to_use:
            raw_content = item.get("content", "").strip()
            section_raw = item.get("section", "")
            clean_title = self._clean_section_title(section_raw)

            # Clean and filter non-informational content
            cleaned_lines = []
            for line in raw_content.splitlines():
                l_strip = line.strip()
                # Skip markdown metadata, disclaimers, horizontal rules, and document titles
                if (
                    not l_strip
                    or l_strip.startswith("# ")
                    or l_strip.startswith("## ")
                    or l_strip.startswith("---")
                    or l_strip.startswith(">")
                    or l_strip.startswith("**Document ID:")
                    or l_strip.startswith("**Version:")
                    or l_strip.startswith("**Effective Date:")
                    or l_strip.startswith("**Last Updated:")
                    or l_strip.startswith("**Category:")
                    or l_strip.startswith("**Scope:")
                ):
                    continue

                # Omit FAQ question lines repeating the prompt
                if re.match(r"^(###\s*)?(Q\s*[:\.]\s*|Question\s*[:\.]\s*)", l_strip, flags=re.IGNORECASE):
                    continue

                # Clean FAQ answer prefixes like **A:** or A:
                line_cleaned = re.sub(r"^\s*(\*\*)?A\s*[:\.]\s*(\*\*)?\s*", "", line)

                # Clean section numbers from embedded headers (e.g. '### 4.1 Age Requirements' -> '### Age Requirements')
                line_cleaned = re.sub(r"^(#+\s*)\d+(\.\d+)*[\.\:\-\)]?\s*", r"\1", line_cleaned)

                cleaned_lines.append(line_cleaned)

            chunk_text = "\n".join(cleaned_lines).strip()
            if not chunk_text:
                continue

            # Deduplicate nearly identical chunks
            snippet_key = chunk_text[:80].lower()
            if snippet_key in seen_snippets:
                continue
            seen_snippets.add(snippet_key)

            # Format chunk with subheading if it represents a distinct policy section
            if "|" in chunk_text:
                # Tables
                if clean_title:
                    sections_content.append(f"### {clean_title}\n\n{chunk_text}")
                else:
                    sections_content.append(chunk_text)
            elif clean_title and len(items_to_use) > 1 and clean_title.lower() not in chunk_text.lower()[:60]:
                sections_content.append(f"### {clean_title}\n{chunk_text}")
            else:
                sections_content.append(chunk_text)

        if not sections_content:
            return f"Information on **{topic}** is currently being updated in our system."

        body = "\n\n".join(sections_content)
        closing = "\n\nPlease let me know if you would like more details or assistance with your application!"
        return f"{intro}\n\n{body}{closing}"

    def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        route: str,
        status: str,
        customer_id: Optional[str] = None,
    ) -> str:
        """Render grounded response strictly from supplied context using natural conversational markdown."""
        if status == "needs_customer_context":
            return "Customer identification is required for this request. Please provide your Customer ID to proceed."

        if status == "unsupported":
            return "I cannot answer that using the available NovaBank information. Please ask a banking or policy-related question."

        if status == "error":
            return "An error occurred while processing your banking request. Please try again later."

        tool_items = [c for c in context if c.get("source_type") == "tool"]
        rag_items = [c for c in context if c.get("source_type") == "rag"]

        tool_sections: List[str] = []

        # 1. Synthesize Tool Results
        for item in tool_items:
            tool_name = item.get("source", "")
            data = item.get("data")
            error = item.get("error")

            if error:
                err_msg = error.get("message", "Error executing tool")
                tool_sections.append(f"Unable to retrieve details from {tool_name}: {err_msg}.")
                continue

            if not data:
                continue

            if tool_name == "get_balance":
                total = data.get("total_balance", 0.0)
                curr = data.get("currency", "INR")
                accounts = data.get("accounts", [])

                acc_lines = []
                for a in accounts:
                    acc_lines.append(
                        f"- **{a.get('account_type', 'Account')} (`{a.get('account_id', 'ACC')}`):** {curr} {a.get('balance', 0):,.2f} ({a.get('status', 'Active')})"
                    )
                acc_block = ("\n\n### Account Breakdown\n" + "\n".join(acc_lines)) if acc_lines else ""
                tool_sections.append(
                    f"Your total account balance is **{curr} {total:,.2f}**.{acc_block}"
                )

            elif tool_name == "get_accounts":
                accounts = data.get("accounts", [])
                if accounts:
                    acc_summaries = [
                        f"- **{a.get('account_type')}** (`{a.get('account_id')}`): {a.get('currency', 'INR')} {a.get('balance', 0):,.2f} (Status: {a.get('status', 'Active')})"
                        for a in accounts
                    ]
                    tool_sections.append(
                        f"You have {len(accounts)} active account(s) registered with NovaBank:\n" + "\n".join(acc_summaries)
                    )
                else:
                    tool_sections.append("No active accounts found.")

            elif tool_name in ["get_transactions", "get_transaction_summary"]:
                if tool_name == "get_transactions":
                    txs = data.get("transactions", [])
                    if txs:
                        rows = [
                            f"| {t.get('date', 'N/A')} | {t.get('description', 'Transaction')} | {t.get('transaction_type', 'N/A')} | INR {t.get('amount', 0):,.2f} | {t.get('status', 'Completed')} |"
                            for t in txs[:5]
                        ]
                        table = (
                            "| Date | Description | Type | Amount | Status |\n"
                            "|---|---|---|---|---|\n"
                            + "\n".join(rows)
                        )
                        tool_sections.append(f"Here are your latest transactions:\n\n{table}")
                    else:
                        tool_sections.append("No recent transactions found.")
                else:
                    total_spent = data.get("total_debits", 0.0)
                    total_credited = data.get("total_credits", 0.0)
                    net = total_credited - total_spent
                    tool_sections.append(
                        f"Here is a summary of your recent transaction activity:\n"
                        f"- **Total Debits:** INR {total_spent:,.2f}\n"
                        f"- **Total Credits:** INR {total_credited:,.2f}\n"
                        f"- **Net Cash Flow:** {'+' if net >= 0 else '-'}INR {abs(net):,.2f}."
                    )

            elif tool_name == "check_loan_eligibility":
                eligible = data.get("eligible", False)
                max_amt = data.get("max_eligible_amount", 0)
                reasons = data.get("reasons", [])
                if eligible:
                    tool_sections.append(
                        f"### Loan Eligibility Assessment\n"
                        f"Based on your credit profile and account history, **you are eligible** for this loan!\n\n"
                        f"- **Maximum Eligible Amount:** INR {max_amt:,.2f}\n"
                        f"- **Application Status:** Pre-approved for processing."
                    )
                else:
                    reason_text = "; ".join(reasons) if reasons else "criteria not met"
                    tool_sections.append(
                        f"### Loan Eligibility Assessment\n"
                        f"You are currently not eligible for this loan ({reason_text})."
                    )

            elif tool_name in ["get_customer_details", "get_customer_profile"]:
                name = data.get("name")
                cid = data.get("customer_id") or customer_id

                if any(w in query.lower() for w in ["name", "who am i", "who i am", "who's", "who is"]):
                    if name:
                        tool_sections.append(
                            f"Your registered name with NovaBank is **{name}** (Customer ID: `{cid}`)."
                        )
                    else:
                        tool_sections.append(f"Your registered Customer ID is `{cid}`.")
                else:
                    lines = []
                    if name:
                        lines.append(f"- **Customer Name:** {name}")
                    if cid:
                        lines.append(f"- **Customer ID:** `{cid}`")
                    if data.get("occupation"):
                        lines.append(f"- **Occupation:** {data.get('occupation')}")
                    if data.get("city"):
                        lines.append(f"- **City:** {data.get('city')}")
                    if data.get("age"):
                        lines.append(f"- **Age:** {data.get('age')}")
                    if data.get("monthly_income"):
                        lines.append(f"- **Monthly Income:** INR {data.get('monthly_income'):,.2f}")
                    if data.get("credit_score"):
                        lines.append(f"- **Credit Score:** {data.get('credit_score')}")
                    if data.get("customer_segment"):
                        lines.append(f"- **Customer Segment:** {data.get('customer_segment')}")
                    if data.get("preferred_language"):
                        lines.append(f"- **Preferred Language:** {data.get('preferred_language')}")

                    greeting = f"Here are your registered customer details, **{name}**:" if name else "Here are your customer details:"
                    tool_sections.append(f"### Customer Details\n{greeting}\n\n" + "\n".join(lines))

        # 2. Synthesize RAG Results
        rag_content = self._synthesize_rag_items(query, rag_items) if rag_items else ""

        # 3. Combine results based on route
        if tool_sections and rag_content:
            tool_combined = "\n\n".join(tool_sections)
            return (
                f"### Account Information\n{tool_combined}\n\n"
                f"### Policy & Guidelines\n{rag_content}"
            )
        elif tool_sections:
            return "\n\n".join(tool_sections)
        elif rag_content:
            return rag_content

        if not tool_sections and customer_id:
            try:
                from app.repositories.json_repository import repository
                cust = repository.get_customer_by_id(customer_id)
                if cust and any(w in query.lower() for w in ["name", "who am i", "who i am", "what's my name", "about me", "who is"]):
                    fname = cust.get("name", "").split()[0]
                    return f"Hello {fname}! Your registered name with NovaBank is **{cust.get('name')}** (Customer ID: `{customer_id}`)."
            except Exception:
                pass

        if route == "RAG":
            return "NovaBank policy details are currently unavailable for this query."
        elif route == "TOOL":
            return "Your requested account information is currently unavailable."
        return "Information is currently unavailable."


class LangChainLLMClient(BaseLLMClient):
    """
    Live LangChain client connecting to external providers (e.g. OpenAI, OpenRouter).
    Delegates to RuleBasedLLMClient if API key is not present or execution fails.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str = "",
        base_url: str = "",
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key or LLM_API_KEY
        self.base_url = base_url or LLM_BASE_URL
        self.fallback = RuleBasedLLMClient()
        self._llm = None
        self._init_llm()

    def _init_llm(self) -> None:
        """Initialize LangChain chat model if key is available."""
        if not self.api_key:
            return

        try:
            from langchain_openai import ChatOpenAI

            kwargs: Dict[str, Any] = {
                "model": self.model,
                "api_key": self.api_key,
                "temperature": 0.0,
                "timeout": 12.0,  # 12-second strict network timeout to prevent UI freezes
                "max_retries": 1,
            }
            if self.base_url:
                kwargs["base_url"] = self.base_url

            # OpenRouter headers for compliance and leaderboard ranking
            if self.provider == "openrouter" or "openrouter" in (self.base_url or "").lower():
                kwargs["default_headers"] = {
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "NovaBank AI Banking Assistant",
                }

            self._llm = ChatOpenAI(**kwargs)
        except Exception as e:
            import logging
            logging.getLogger("novabank.llm").warning(f"[LLM] Failed to initialize ChatOpenAI: {e}")
            self._llm = None

    def classify_route(
        self,
        query: str,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Classify query using LangChain model with deterministic fallback."""
        if self._llm is None:
            return self.fallback.classify_route(query, customer_id)

        import logging
        import time
        logger = logging.getLogger("novabank.llm")

        t0 = time.time()
        logger.info(f"[LLM ROUTING] Calling {self.provider} ({self.model}) to classify query...")
        try:
            prompt = (
                f"{ROUTING_SYSTEM_PROMPT}\n\n"
                f"Customer Context Available: {customer_id is not None}\n"
                f"Customer Query: {query}\n\n"
                f"Return JSON with 'route' (TOOL|RAG|BOTH|CLARIFICATION|UNSUPPORTED) and 'reason'."
            )
            res = self._llm.invoke(prompt)
            content = res.content if hasattr(res, "content") else str(res)
            logger.info(f"[LLM ROUTING] Received route response in {time.time() - t0:.2f}s")

            # Try direct JSON parsing first
            parsed_route = None
            try:
                import json
                cleaned = content.strip()
                if "{" in cleaned and "}" in cleaned:
                    json_str = cleaned[cleaned.find("{"):cleaned.rfind("}")+1]
                    data = json.loads(json_str)
                    r = str(data.get("route", "")).strip().upper()
                    if r in ["TOOL", "RAG", "BOTH", "CLARIFICATION", "UNSUPPORTED"]:
                        parsed_route = r
            except Exception:
                pass

            if not parsed_route:
                # Regex match checking compound/longer routes first
                for candidate in ["BOTH", "CLARIFICATION", "UNSUPPORTED", "TOOL", "RAG"]:
                    if re.search(rf'"route"\s*:\s*"{candidate}"', content, re.IGNORECASE) or re.search(rf"\b{candidate}\b", content.upper()):
                        parsed_route = candidate
                        break

            if parsed_route:
                fallback_tools = self.fallback._determine_tools(query.lower(), customer_id) if parsed_route in ("TOOL", "BOTH") else []
                return {"route": parsed_route, "reason": content.strip()[:200], "tools": fallback_tools}

            return self.fallback.classify_route(query, customer_id)
        except Exception as err:
            logger.warning(
                f"[LLM ROUTING] LLM call failed or timed out after {time.time() - t0:.2f}s ({err}). "
                f"Falling back to instant deterministic routing."
            )
            return self.fallback.classify_route(query, customer_id)

    def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        route: str,
        status: str,
        customer_id: Optional[str] = None,
    ) -> str:
        """Generate response using LangChain model with deterministic fallback."""
        if self._llm is None or status != "success" or not context:
            return self.fallback.generate_response(query, context, route, status, customer_id)

        import logging
        import time
        logger = logging.getLogger("novabank.llm")

        t0 = time.time()
        logger.info(f"[LLM GENERATION] Calling {self.provider} ({self.model}) to synthesize response...")
        try:
            # Inject authenticated customer context if available
            customer_info_str = ""
            if customer_id:
                try:
                    from app.repositories.json_repository import repository
                    cust = repository.get_customer_by_id(customer_id)
                    if cust:
                        customer_info_str = (
                            f"AUTHENTICATED CUSTOMER IDENTITY (Verified & Authoritative):\n"
                            f"- Full Name: {cust.get('name')}\n"
                            f"- Customer ID: {customer_id}\n"
                            f"- Age: {cust.get('age')}\n"
                            f"- Gender: {cust.get('gender')}\n"
                            f"- City: {cust.get('city')}\n"
                            f"- Occupation: {cust.get('occupation')}\n"
                            f"- Monthly Income: INR {cust.get('monthly_income', 0):,.2f}\n"
                            f"- Credit Score: {cust.get('credit_score')}\n\n"
                        )
                except Exception:
                    pass

            context_str = "\n\n".join([
                f"Source: {c.get('source_type', '').upper()} - {c.get('source', '')}\n"
                f"Data: {c.get('data') or c.get('content', '')}"
                for c in context
            ])
            prompt = (
                f"{RESPONSE_GENERATION_SYSTEM_PROMPT}\n\n"
                f"{customer_info_str}"
                f"Customer Query: {query}\n\n"
                f"Retrieved Context:\n{context_str}\n\n"
                f"Answer the query accurately based ONLY on the above context and authenticated customer identity:"
            )
            res = self._llm.invoke(prompt)
            text = res.content.strip() if hasattr(res, "content") else str(res).strip()
            logger.info(f"[LLM GENERATION] Generated response in {time.time() - t0:.2f}s (len={len(text)})")
            return text
        except Exception as err:
            logger.warning(
                f"[LLM GENERATION] LLM call failed or timed out after {time.time() - t0:.2f}s ({err}). "
                f"Falling back to instant deterministic response generation."
            )
            return self.fallback.generate_response(query, context, route, status, customer_id)


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> BaseLLMClient:
    """Factory function returning configured LLM client."""
    prov = (provider or LLM_PROVIDER or "mock").lower()
    mod = model or LLM_MODEL
    key = api_key or LLM_API_KEY
    url = base_url or LLM_BASE_URL

    if prov == "openrouter" and not url:
        url = "https://openrouter.ai/api/v1"

    if prov == "mock" or not key:
        return RuleBasedLLMClient()

    return LangChainLLMClient(provider=prov, model=mod, api_key=key, base_url=url)
