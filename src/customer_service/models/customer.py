"""Pydantic data models for CCA Customer Support Resolution Agent."""

from enum import StrEnum

from pydantic import BaseModel, Field


class CustomerTier(StrEnum):
    """Customer tier levels for policy lookup."""

    BASIC = "basic"
    REGULAR = "regular"
    PREMIUM = "premium"
    VIP = "vip"


class CustomerProfile(BaseModel):
    """Customer profile returned by CustomerDatabase lookup."""

    customer_id: str = Field(description="Unique customer identifier")
    name: str = Field(description="Customer full name")
    email: str = Field(description="Customer email address")
    tier: CustomerTier = Field(description="Customer tier level")
    account_open: bool = Field(default=True, description="Whether account is active")
    flags: list[str] = Field(
        default_factory=list,
        description="Account flags (e.g., 'account_closure')",
    )


class RefundRequest(BaseModel):
    """Request to process a customer refund."""

    customer_id: str = Field(description="Customer requesting refund")
    order_id: str = Field(description="Order ID for the refund")
    amount: float = Field(gt=0, description="Refund amount in USD (must be positive)")
    reason: str = Field(description="Reason for refund request")


class PolicyResult(BaseModel):
    """Result from PolicyEngine policy check."""

    approved: bool = Field(description="Whether the refund is within policy limits")
    limit: float = Field(description="Maximum refund allowed for this tier")
    requires_review: bool = Field(description="Whether amount exceeds $500 review threshold")


class EscalationRecord(BaseModel):
    """Structured escalation handoff record (CCA handoff pattern)."""

    customer_id: str = Field(description="Customer being escalated")
    customer_tier: str = Field(description="Customer tier at time of escalation")
    issue_type: str = Field(description="Type of issue (refund, complaint, etc.)")
    disputed_amount: float = Field(description="Amount in dispute")
    escalation_reason: str = Field(description="Why this was escalated")
    recommended_action: str = Field(description="Suggested next step for human agent")
    conversation_summary: str = Field(description="Structured summary of conversation so far")
    turns_elapsed: int = Field(description="Number of conversation turns before escalation")


class InteractionLog(BaseModel):
    """Audit log entry for compliance tracking."""

    customer_id: str = Field(description="Customer involved")
    action: str = Field(description="Action taken (lookup, refund, escalation, etc.)")
    details: str = Field(description="JSON string with action details")
    timestamp: str = Field(description="ISO 8601 timestamp of action")
