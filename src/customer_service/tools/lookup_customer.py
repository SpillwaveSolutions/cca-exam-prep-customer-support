"""Handler for the lookup_customer tool."""

import json

from customer_service.services.container import ServiceContainer


def handle_lookup_customer(input_dict: dict, services: ServiceContainer) -> str:
    """Look up a customer by ID. Returns JSON string with customer data or error.

    CCA Rule: All tool handlers return JSON strings (matching Claude API tool_result format).
    Services are accessed via ServiceContainer — never imported directly.
    """
    customer_id = input_dict.get("customer_id", "")
    customer = services.customer_db.get_customer(customer_id)
    if customer is None:
        return json.dumps({"error": f"Customer not found: {customer_id}"})
    return json.dumps(customer.model_dump())
