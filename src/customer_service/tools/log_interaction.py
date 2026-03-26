"""Handler for the log_interaction tool."""

import json
from datetime import UTC, datetime

from customer_service.models.customer import InteractionLog
from customer_service.services.container import ServiceContainer


def handle_log_interaction(input_dict: dict, services: ServiceContainer) -> str:
    """Log a customer interaction for compliance and audit. Returns JSON string.

    CCA Rule: Compliance is enforced programmatically (audit logging here),
    not solely in system prompts.
    All tool handlers return JSON strings (matching Claude API tool_result format).
    Services are accessed via ServiceContainer — never imported directly.
    """
    entry = InteractionLog(
        customer_id=input_dict["customer_id"],
        action=input_dict["action"],
        details=input_dict["details"],
        timestamp=datetime.now(UTC).isoformat(),
    )
    services.audit_log.log(entry)
    return json.dumps({"status": "logged", "entry": entry.model_dump()})
