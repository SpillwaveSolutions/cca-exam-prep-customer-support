"""Tests for Pydantic data models — CCA Customer Support Resolution Agent."""

import pytest
from pydantic import ValidationError


def test_customer_tier_values() -> None:
    """CustomerTier enum has exactly 4 members with correct string values."""
    from customer_service.models.customer import CustomerTier

    assert len(CustomerTier) == 4
    assert CustomerTier.BASIC.value == "basic"
    assert CustomerTier.REGULAR.value == "regular"
    assert CustomerTier.PREMIUM.value == "premium"
    assert CustomerTier.VIP.value == "vip"


def test_customer_profile_valid() -> None:
    """CustomerProfile can be created with valid fields."""
    from customer_service.models.customer import CustomerProfile, CustomerTier

    profile = CustomerProfile(
        customer_id="C001",
        name="Alice",
        email="alice@example.com",
        tier=CustomerTier.REGULAR,
    )
    assert profile.customer_id == "C001"
    assert profile.name == "Alice"
    assert profile.email == "alice@example.com"
    assert profile.tier == CustomerTier.REGULAR


def test_customer_profile_defaults() -> None:
    """CustomerProfile defaults: account_open=True, flags=[]."""
    from customer_service.models.customer import CustomerProfile, CustomerTier

    profile = CustomerProfile(
        customer_id="C001",
        name="Alice",
        email="alice@example.com",
        tier=CustomerTier.REGULAR,
    )
    assert profile.account_open is True
    assert profile.flags == []


def test_refund_request_valid() -> None:
    """RefundRequest can be created with valid fields."""
    from customer_service.models.customer import RefundRequest

    req = RefundRequest(
        customer_id="C001",
        order_id="ORD-001",
        amount=50.0,
        reason="Defective",
    )
    assert req.amount == 50.0


def test_refund_request_negative_amount() -> None:
    """RefundRequest rejects negative amount (gt=0 constraint)."""
    from customer_service.models.customer import RefundRequest

    with pytest.raises(ValidationError):
        RefundRequest(
            customer_id="C001",
            order_id="ORD-001",
            amount=-10.0,
            reason="Defective",
        )


def test_escalation_record_valid() -> None:
    """EscalationRecord can be created with all required fields."""
    from customer_service.models.customer import EscalationRecord

    record = EscalationRecord(
        customer_id="C001",
        customer_tier="regular",
        issue_type="refund",
        disputed_amount=600.0,
        escalation_reason="Amount exceeds $500 threshold",
        recommended_action="Review and approve manually",
        conversation_summary="Customer requested $600 refund for damaged item.",
        turns_elapsed=3,
    )
    assert record.customer_id == "C001"
    assert record.turns_elapsed == 3


def test_policy_result_valid() -> None:
    """PolicyResult can be created with all fields."""
    from customer_service.models.customer import PolicyResult

    result = PolicyResult(approved=True, limit=100.0, requires_review=False)
    assert result.approved is True
    assert result.limit == 100.0
    assert result.requires_review is False


def test_interaction_log_valid() -> None:
    """InteractionLog can be created with all fields."""
    from customer_service.models.customer import InteractionLog

    log = InteractionLog(
        customer_id="C001",
        action="lookup",
        details='{"customer_id": "C001"}',
        timestamp="2026-03-26T05:00:00Z",
    )
    assert log.action == "lookup"


def test_model_json_schema_generation() -> None:
    """model_json_schema() returns valid dict with 'properties' key for each model."""
    from customer_service.models.customer import (
        CustomerProfile,
        EscalationRecord,
        PolicyResult,
        RefundRequest,
    )

    for model_cls in [CustomerProfile, RefundRequest, EscalationRecord, PolicyResult]:
        schema = model_cls.model_json_schema()
        assert isinstance(schema, dict), f"{model_cls.__name__} schema is not a dict"
        assert "properties" in schema, f"{model_cls.__name__} schema missing 'properties'"
