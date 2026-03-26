"""Handler for the process_refund tool.

CCA Pattern: Two-step vetoable dispatch.
  1. propose_refund: compute the proposed result WITHOUT writing to FinancialSystem
  2. (callback runs on proposed result — may block)
  3. commit_refund: write to FinancialSystem only if callback allows

This ensures the veto guarantee: a blocked refund leaves FinancialSystem untouched.
"""

import json

from customer_service.services.container import ServiceContainer


def propose_refund(input_dict: dict, services: ServiceContainer) -> dict:
    """Compute proposed refund result WITHOUT committing to FinancialSystem.

    Performs customer lookup and policy check, returning a proposed result dict.
    Does NOT call services.financial_system.process_refund(). This is the first
    step of the two-step vetoable dispatch pattern.

    CCA Rule: Callbacks run on the proposed result before any financial write occurs.

    Args:
        input_dict: Tool input with customer_id, order_id, amount, reason.
        services: Injected ServiceContainer.

    Returns:
        Proposed result dict (not yet committed) or error dict if lookup fails.
    """
    customer_id = input_dict.get("customer_id", "")
    customer = services.customer_db.get_customer(customer_id)
    if customer is None:
        return {"error": f"Customer not found: {customer_id}"}

    order_id = input_dict.get("order_id", "")
    amount = input_dict.get("amount", 0.0)

    policy_result = services.policy_engine.check_policy(customer.tier, amount)
    # Return proposed result — no FinancialSystem write yet
    return {
        "status": "proposed",
        "customer_id": customer_id,
        "order_id": order_id,
        "amount": amount,
        "policy_approved": policy_result.approved,
        "requires_review": policy_result.requires_review,
    }


def commit_refund(
    customer_id: str,
    order_id: str,
    amount: float,
    policy_approved: bool,
    services: ServiceContainer,
) -> str:
    """Commit a previously proposed refund to FinancialSystem. Returns JSON string.

    Called only after callbacks have approved the refund (action="allow").

    CCA Rule: All tool handlers return JSON strings (matching Claude API tool_result format).

    Args:
        customer_id: Customer requesting the refund.
        order_id: Order being refunded.
        amount: Refund amount in USD.
        policy_approved: Whether PolicyEngine approved the amount.
        services: Injected ServiceContainer.

    Returns:
        JSON string with FinancialSystem result.
    """
    result = services.financial_system.process_refund(
        customer_id=customer_id,
        order_id=order_id,
        amount=amount,
        policy_approved=policy_approved,
    )
    return json.dumps(result)


def handle_process_refund(input_dict: dict, services: ServiceContainer) -> str:
    """Process a refund for a customer order. Returns JSON string.

    Simple path: propose then commit (no callbacks). Used for backward compatibility
    when dispatch() is called without callbacks.

    Looks up customer to get tier, checks policy, then calls FinancialSystem.
    FinancialSystem trusts the policy_approved flag — no re-evaluation.

    CCA Rule: All tool handlers return JSON strings (matching Claude API tool_result format).
    Services are accessed via ServiceContainer — never imported directly.
    """
    proposed = propose_refund(input_dict, services)
    if "error" in proposed:
        return json.dumps(proposed)

    return commit_refund(
        customer_id=proposed["customer_id"],
        order_id=proposed["order_id"],
        amount=proposed["amount"],
        policy_approved=proposed["policy_approved"],
        services=services,
    )
