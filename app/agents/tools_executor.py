"""
Banking Tools Executor
======================
Executes approved Phase 4 Banking Tools with strict customer context protection,
tool call limits, argument validation, and error isolation.
"""

from typing import Any, Dict, List, Optional
from app.agents.config import MAX_TOOL_CALLS
from app.tools import BANKING_TOOLS_DICT, get_tool_by_name
from app.tools.schemas import ToolResult

CUSTOMER_SPECIFIC_TOOLS = {
    "get_customer_details",
    "get_customer_profile",
    "get_accounts",
    "get_balance",
    "get_transactions",
    "get_transaction_summary",
    "check_loan_eligibility",
}


class ToolsExecutor:
    """Executes banking tools under trusted security constraints."""

    def __init__(self, max_tool_calls: int = MAX_TOOL_CALLS):
        self.max_tool_calls = max_tool_calls

    def execute_tools(
        self,
        tool_calls: List[Dict[str, Any]],
        trusted_customer_id: Optional[str] = None,
        current_tool_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Executes a list of tool calls under security constraints.

        Returns:
            dict containing:
                - tool_results: list of structured execution results
                - new_tool_count: updated total execution count
                - errors: any errors encountered
        """
        results: List[Dict[str, Any]] = []
        tool_count = current_tool_count

        for call in tool_calls:
            # Check maximum tool call limit
            if tool_count >= self.max_tool_calls:
                results.append({
                    "source_type": "tool",
                    "source": call.get("name", "unknown"),
                    "success": False,
                    "error": {
                        "type": "limit_exceeded",
                        "message": f"Maximum tool call limit of {self.max_tool_calls} reached.",
                    },
                })
                break

            name = call.get("name", "")
            raw_args = dict(call.get("args", {}))

            # Validate tool existence
            tool_func = get_tool_by_name(name)
            if not tool_func:
                results.append({
                    "source_type": "tool",
                    "source": name,
                    "success": False,
                    "error": {
                        "type": "unknown_tool",
                        "message": f"Tool '{name}' is not an approved NovaBank banking tool.",
                    },
                })
                tool_count += 1
                continue

            # Security: For customer-specific tools, enforce trusted customer_id
            if name in CUSTOMER_SPECIFIC_TOOLS:
                if not trusted_customer_id:
                    results.append({
                        "source_type": "tool",
                        "source": name,
                        "success": False,
                        "error": {
                            "type": "missing_customer_context",
                            "message": f"Customer context required to execute {name}.",
                        },
                    })
                    tool_count += 1
                    continue

                # Strict prevention of ID injection: override any user-provided customer_id
                raw_args["customer_id"] = trusted_customer_id

            # Execute tool safely
            try:
                tool_output = tool_func(**raw_args)
                tool_count += 1

                is_success = (
                    tool_output.get("success", False)
                    if isinstance(tool_output, dict)
                    else getattr(tool_output, "success", False)
                )
                data = (
                    tool_output.get("data")
                    if isinstance(tool_output, dict)
                    else getattr(tool_output, "data", None)
                )
                error_obj = (
                    tool_output.get("error")
                    if isinstance(tool_output, dict)
                    else getattr(tool_output, "error", None)
                )

                if is_success:
                    results.append({
                        "source_type": "tool",
                        "source": name,
                        "success": True,
                        "data": data,
                    })
                else:
                    err_dict = (
                        error_obj.model_dump()
                        if hasattr(error_obj, "model_dump")
                        else (error_obj if isinstance(error_obj, dict) else {"type": "execution_failed", "message": "Tool execution returned failure."})
                    )
                    results.append({
                        "source_type": "tool",
                        "source": name,
                        "success": False,
                        "error": err_dict,
                    })
            except Exception as e:
                tool_count += 1
                results.append({
                    "source_type": "tool",
                    "source": name,
                    "success": False,
                    "error": {
                        "type": "tool_exception",
                        "message": str(e),
                    },
                })

        return {
            "tool_results": results,
            "new_tool_count": tool_count,
        }
