"""Tool dispatch registry (CCA pattern: dict-based routing).

CCA Rule: Dict-based dispatch is deterministic and auditable.
All handlers return JSON strings (matching Claude API tool_result format).
"""

import json
from collections.abc import Callable

from customer_service.services.container import ServiceContainer
from customer_service.tools.check_policy import handle_check_policy
from customer_service.tools.escalate_to_human import handle_escalate_to_human
from customer_service.tools.log_interaction import handle_log_interaction
from customer_service.tools.lookup_customer import handle_lookup_customer
from customer_service.tools.process_refund import handle_process_refund

DISPATCH: dict[str, Callable[[dict, ServiceContainer], str]] = {
    "lookup_customer": handle_lookup_customer,
    "check_policy": handle_check_policy,
    "process_refund": handle_process_refund,
    "escalate_to_human": handle_escalate_to_human,
    "log_interaction": handle_log_interaction,
}


def dispatch(tool_name: str, input_dict: dict, services: ServiceContainer) -> str:
    """Route tool_use block to correct handler. Returns JSON string always.

    CCA Rule: Unknown tool names return a structured JSON error, never raise exceptions.
    Silent failures (swallowed exceptions) violate the CCA silent-failure-prevention rule.
    """
    handler = DISPATCH.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    return handler(input_dict, services)
