"""Tests for the 5 simulated in-memory services and ServiceContainer."""

import dataclasses

import pytest

from customer_service.models.customer import CustomerTier, EscalationRecord, InteractionLog
from customer_service.services.container import ServiceContainer


def test_customer_db_lookup(services: ServiceContainer) -> None:
    """CustomerDatabase returns correct profile for known customer ID."""
    profile = services.customer_db.get_customer("C001")
    assert profile is not None
    assert profile.name == "Alice Johnson"


def test_customer_db_not_found(services: ServiceContainer) -> None:
    """CustomerDatabase returns None for unknown customer ID."""
    assert services.customer_db.get_customer("INVALID") is None


def test_policy_limits_basic(services: ServiceContainer) -> None:
    """BASIC tier: $50 is within $100 limit — approved, no review."""
    result = services.policy_engine.check_policy(CustomerTier.BASIC, 50.0)
    assert result.approved is True
    assert result.limit == 100.0
    assert result.requires_review is False


def test_policy_limits_regular(services: ServiceContainer) -> None:
    """REGULAR tier: $50 is within $100 limit — approved, no review."""
    result = services.policy_engine.check_policy(CustomerTier.REGULAR, 50.0)
    assert result.approved is True
    assert result.limit == 100.0
    assert result.requires_review is False


def test_policy_limits_premium(services: ServiceContainer) -> None:
    """PREMIUM tier: $400 is within $500 limit — approved, no review."""
    result = services.policy_engine.check_policy(CustomerTier.PREMIUM, 400.0)
    assert result.approved is True
    assert result.limit == 500.0
    assert result.requires_review is False


def test_policy_limits_vip(services: ServiceContainer) -> None:
    """VIP tier: $4000 is within $5000 limit — approved, review triggered (>$500)."""
    result = services.policy_engine.check_policy(CustomerTier.VIP, 4000.0)
    assert result.approved is True
    assert result.limit == 5000.0
    assert result.requires_review is True  # $4000 > $500 review threshold


def test_policy_over_limit(services: ServiceContainer) -> None:
    """REGULAR tier: $200 exceeds $100 limit — rejected."""
    result = services.policy_engine.check_policy(CustomerTier.REGULAR, 200.0)
    assert result.approved is False


def test_policy_review_threshold_below(services: ServiceContainer) -> None:
    """Exactly $500 does NOT trigger requires_review (strictly greater than threshold)."""
    result = services.policy_engine.check_policy(CustomerTier.VIP, 500.0)
    assert result.requires_review is False


def test_policy_review_threshold_above(services: ServiceContainer) -> None:
    """$501 triggers requires_review (strictly greater than $500 threshold)."""
    result = services.policy_engine.check_policy(CustomerTier.VIP, 501.0)
    assert result.requires_review is True


def test_financial_system_approve(services: ServiceContainer) -> None:
    """process_refund with policy_approved=True returns status='approved'."""
    result = services.financial_system.process_refund("C001", "ORD-001", 50.0, policy_approved=True)
    assert result["status"] == "approved"
    assert result["customer_id"] == "C001"
    assert result["amount"] == 50.0


def test_financial_system_reject_over_limit(services: ServiceContainer) -> None:
    """process_refund with policy_approved=False returns status='rejected'."""
    result = services.financial_system.process_refund(
        "C001", "ORD-001", 200.0, policy_approved=False
    )
    assert result["status"] == "rejected"


def test_escalation_queue(services: ServiceContainer) -> None:
    """EscalationQueue stores records and returns them via get_escalations()."""
    record = EscalationRecord(
        customer_id="C001",
        customer_tier="regular",
        issue_type="refund",
        disputed_amount=600.0,
        escalation_reason="Amount exceeds $500",
        recommended_action="Manual review",
        conversation_summary="Customer requested large refund.",
        turns_elapsed=2,
    )
    services.escalation_queue.add_escalation(record)
    escalations = services.escalation_queue.get_escalations()
    assert len(escalations) == 1
    assert escalations[0].customer_id == "C001"


def test_audit_log(services: ServiceContainer) -> None:
    """AuditLog stores entries and returns them via get_entries()."""
    entry = InteractionLog(
        customer_id="C001",
        action="lookup",
        details='{"customer_id": "C001"}',
        timestamp="2026-03-26T05:00:00Z",
    )
    services.audit_log.log(entry)
    entries = services.audit_log.get_entries()
    assert len(entries) == 1
    assert entries[0].action == "lookup"


def test_service_container_frozen(services: ServiceContainer) -> None:
    """ServiceContainer raises FrozenInstanceError on attribute mutation."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        services.customer_db = None  # type: ignore[misc]
