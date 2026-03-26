"""Pre-built test scenarios for CCA exam notebooks."""

SCENARIOS: dict[str, dict] = {
    "happy_path": {
        "customer_id": "C001",
        "message": "I'd like a $50 refund for order #ORD-001. The item was defective.",
        "expected_tools": ["lookup_customer", "check_policy", "process_refund", "log_interaction"],
        "expected_outcome": "refund_approved",
    },
    "vip_escalation": {
        "customer_id": "C002",
        "message": "I need a $200 refund immediately. I'm a VIP customer.",
        "expected_tools": ["lookup_customer", "check_policy", "escalate_to_human"],
        "expected_outcome": "escalated_vip",
    },
    "amount_threshold": {
        "customer_id": "C003",
        "message": "I need a $600 refund for my damaged order.",
        "expected_tools": ["lookup_customer", "check_policy", "escalate_to_human"],
        "expected_outcome": "escalated_amount",
    },
    "account_closure": {
        "customer_id": "C004",
        "message": "I want a refund and to close my account.",
        "expected_tools": ["lookup_customer", "escalate_to_human"],
        "expected_outcome": "escalated_closure",
    },
    "legal_keyword": {
        "customer_id": "C005",
        "message": "This is unacceptable. I'm considering a lawsuit over this matter.",
        "expected_tools": ["lookup_customer", "escalate_to_human"],
        "expected_outcome": "escalated_legal",
    },
    "multi_trigger": {
        "customer_id": "C006",
        "message": "I'm a VIP and I want a $600 refund before I close my account.",
        "expected_tools": ["lookup_customer", "check_policy", "escalate_to_human"],
        "expected_outcome": "escalated_multi",
    },
}
