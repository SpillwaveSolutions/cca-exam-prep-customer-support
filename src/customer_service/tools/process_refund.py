"""Handler for the process_refund tool."""

import json

from customer_service.services.container import ServiceContainer


def handle_process_refund(input_dict: dict, services: ServiceContainer) -> str:
    """Process a refund for a customer order. Returns JSON string.

    Looks up customer to get tier, checks policy, then calls FinancialSystem.
    FinancialSystem trusts the policy_approved flag — no re-evaluation.

    CCA Rule: All tool handlers return JSON strings (matching Claude API tool_result format).
    Services are accessed via ServiceContainer — never imported directly.
    """
    customer_id = input_dict.get("customer_id", "")
    customer = services.customer_db.get_customer(customer_id)
    if customer is None:
        return json.dumps({"error": f"Customer not found: {customer_id}"})

    order_id = input_dict.get("order_id", "")
    amount = input_dict.get("amount", 0.0)

    policy_result = services.policy_engine.check_policy(customer.tier, amount)
    result = services.financial_system.process_refund(
        customer_id=customer_id,
        order_id=order_id,
        amount=amount,
        policy_approved=policy_result.approved,
    )
    return json.dumps(result)
