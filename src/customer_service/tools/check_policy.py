"""Handler for the check_policy tool."""

import json

from customer_service.services.container import ServiceContainer


def handle_check_policy(input_dict: dict, services: ServiceContainer) -> str:
    """Check refund policy eligibility for a customer. Returns JSON string.

    CCA Rule: All tool handlers return JSON strings (matching Claude API tool_result format).
    Services are accessed via ServiceContainer — never imported directly.
    """
    customer_id = input_dict.get("customer_id", "")
    customer = services.customer_db.get_customer(customer_id)
    if customer is None:
        return json.dumps({"error": f"Customer not found: {customer_id}"})

    requested_amount = input_dict.get("requested_amount", 0.0)
    result = services.policy_engine.check_policy(customer.tier, requested_amount)
    return json.dumps(result.model_dump())
