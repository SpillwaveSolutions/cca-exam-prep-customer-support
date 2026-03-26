"""Tool dispatch registry (CCA pattern: dict-based routing).

CCA Rule: Dict-based dispatch is deterministic and auditable.
All handlers return JSON strings (matching Claude API tool_result format).

Dispatch supports optional PostToolUse callbacks per CCA Principle #1:
  - Callbacks enforce business rules after tool execution (or before commit for process_refund)
  - Per-tool dispatch: callbacks dict maps tool_name -> callback function
  - Backward compatible: context and callbacks default to None
"""

import json
from collections.abc import Callable

from customer_service.services.container import ServiceContainer
from customer_service.tools.check_policy import handle_check_policy
from customer_service.tools.escalate_to_human import handle_escalate_to_human
from customer_service.tools.log_interaction import handle_log_interaction
from customer_service.tools.lookup_customer import handle_lookup_customer
from customer_service.tools.process_refund import (
    commit_refund,
    handle_process_refund,
    propose_refund,
)

DISPATCH: dict[str, Callable[[dict, ServiceContainer], str]] = {
    "lookup_customer": handle_lookup_customer,
    "check_policy": handle_check_policy,
    "process_refund": handle_process_refund,
    "escalate_to_human": handle_escalate_to_human,
    "log_interaction": handle_log_interaction,
}


def dispatch(
    tool_name: str,
    input_dict: dict,
    services: ServiceContainer,
    context: dict | None = None,
    callbacks: dict[str, Callable] | None = None,
) -> str:
    """Route tool_use block to correct handler. Returns JSON string always.

    CCA Rules:
    - Unknown tool names return a structured JSON error, never raise exceptions.
    - Silent failures (swallowed exceptions) violate the CCA silent-failure-prevention rule.
    - Error responses use structured error context per CCA rules: status, error_type, source,
      retry_eligible, fallback_available, partial_data.
    - Per-tool callbacks enforce business rules (Principle #1: programmatic > prompt-based).

    Callback execution:
    - process_refund: two-step vetoable dispatch (propose -> callback -> commit or block)
    - Other tools: run handler, then callback. If action="replace_result", return replacement.

    Args:
        tool_name: Name of the tool to dispatch.
        input_dict: Tool input from Claude tool_use block.
        services: Injected ServiceContainer.
        context: Mutable context dict (user_message + escalation flags set by callbacks).
        callbacks: Per-tool callback registry from build_callbacks(). Optional.

    Returns:
        JSON string result to return as tool_result content.
    """
    handler = DISPATCH.get(tool_name)
    if handler is None:
        return json.dumps(
            {
                "status": "error",
                "error_type": "unknown_tool",
                "source": "dispatch",
                "message": f"Unknown tool: {tool_name}",
                "retry_eligible": False,
                "fallback_available": False,
                "partial_data": None,
            }
        )

    # Normalize context
    ctx = context if context is not None else {}

    try:
        # Special case: process_refund uses two-step vetoable dispatch
        if tool_name == "process_refund" and callbacks and "process_refund" in callbacks:
            return _dispatch_process_refund_with_callback(
                input_dict, services, ctx, callbacks["process_refund"]
            )

        # Pre-handler callback for log_interaction: redact input BEFORE handler writes
        # CCA Rule: PII must never reach the audit log — redact before write, not after
        if tool_name == "log_interaction" and callbacks and "log_interaction" in callbacks:
            cb = callbacks["log_interaction"]
            # Pass input_dict as result_dict so callback can find "details" field
            cb_result = cb(tool_name, input_dict, input_dict, ctx, services)
            if cb_result.action == "replace_result" and cb_result.replacement is not None:
                try:
                    redacted = json.loads(cb_result.replacement)
                    if "details" in redacted:
                        input_dict = {**input_dict, "details": redacted["details"]}
                except (json.JSONDecodeError, ValueError):
                    pass

        # Standard dispatch: run handler, optionally run post-handler callback
        result = handler(input_dict, services)

        if callbacks:
            cb = callbacks.get(tool_name)
            if cb is not None and tool_name != "log_interaction":  # already handled above
                try:
                    result_dict = json.loads(result)
                except (json.JSONDecodeError, ValueError):
                    result_dict = {}
                cb_result = cb(tool_name, input_dict, result_dict, ctx, services)
                if cb_result.action == "replace_result" and cb_result.replacement is not None:
                    return cb_result.replacement

        return result

    except (KeyError, TypeError, ValueError) as exc:
        return json.dumps(
            {
                "status": "error",
                "error_type": "invalid_input",
                "source": tool_name,
                "message": str(exc),
                "retry_eligible": True,
                "fallback_available": False,
                "partial_data": None,
            }
        )


def _dispatch_process_refund_with_callback(
    input_dict: dict,
    services: ServiceContainer,
    context: dict,
    callback: Callable,
) -> str:
    """Two-step vetoable dispatch for process_refund.

    CCA Veto Guarantee: FinancialSystem is NEVER written to for a blocked refund.

    Steps:
    1. propose_refund: compute proposed result (no FinancialSystem write)
    2. run callback on proposed result
    3. if action="block": return blocked replacement JSON (FinancialSystem untouched)
    4. if action="allow": call commit_refund (writes to FinancialSystem)
    """
    proposed = propose_refund(input_dict, services)

    if "error" in proposed:
        return json.dumps(proposed)

    cb_result = callback("process_refund", input_dict, proposed, context, services)

    if cb_result.action == "block" and cb_result.replacement is not None:
        # Veto: return blocked result without touching FinancialSystem
        return cb_result.replacement

    # Callback approved: commit to FinancialSystem
    return commit_refund(
        customer_id=proposed["customer_id"],
        order_id=proposed["order_id"],
        amount=proposed["amount"],
        policy_approved=proposed["policy_approved"],
        services=services,
    )
