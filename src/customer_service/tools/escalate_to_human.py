"""Handler for the escalate_to_human tool."""

import json

from customer_service.models.customer import EscalationRecord
from customer_service.services.container import ServiceContainer


def handle_escalate_to_human(input_dict: dict, services: ServiceContainer) -> str:
    """Escalate interaction to human agent with structured context. Returns JSON string.

    CCA Rule: Escalation handoff uses structured EscalationRecord JSON, not raw conversation.
    All tool handlers return JSON strings (matching Claude API tool_result format).
    Services are accessed via ServiceContainer — never imported directly.
    """
    record = EscalationRecord(
        customer_id=input_dict["customer_id"],
        customer_tier=input_dict["customer_tier"],
        issue_type=input_dict["issue_type"],
        disputed_amount=input_dict["disputed_amount"],
        escalation_reason=input_dict["escalation_reason"],
        recommended_action=input_dict["recommended_action"],
        conversation_summary=input_dict["conversation_summary"],
        turns_elapsed=input_dict["turns_elapsed"],
    )
    services.escalation_queue.add_escalation(record)
    return json.dumps({"status": "escalated", "record": record.model_dump()})
