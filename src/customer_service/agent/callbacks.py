"""PostToolUse callback enforcement layer.

CCA Principle #1: Programmatic enforcement beats prompt-based guidance.
Business rules are enforced here in code — deterministically — not in system prompts.

Escalation thresholds (from CCA rules):
  - amount > $500 (requires_review flag set by check_policy_callback)
  - account closure flag
  - VIP tier
  - legal complaint keywords in user message

Compliance:
  - PII redaction: credit card numbers redacted to ****-****-****-NNNN pattern
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from customer_service.services.container import ServiceContainer

# ---------------------------------------------------------------------------
# Legal keyword detection (CCA: deterministic rules, not LLM confidence)
# ---------------------------------------------------------------------------

LEGAL_KEYWORDS: list[str] = ["lawsuit", "attorney", "lawyer", "legal action", "sue", "court"]

# ---------------------------------------------------------------------------
# PCI compliance: credit card regex
# Matches 16-digit card numbers with dashes or spaces as separators.
# Groups: (first-12-digits)(separator)(last-4-digits)
# ---------------------------------------------------------------------------

CARD_PATTERN: re.Pattern[str] = re.compile(r"\b(\d{4}[-\s]\d{4}[-\s]\d{4}[-\s])(\d{4})\b")


# ---------------------------------------------------------------------------
# CallbackResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class CallbackResult:
    """Result returned by a PostToolUse callback function.

    Attributes:
        action: What the dispatcher should do with the tool result.
            "allow"          -> return original tool result unchanged
            "replace_result" -> return replacement instead of original
            "block"          -> veto the operation; return replacement as error
        replacement: JSON string to return in place of original result (required when
            action is "block" or "replace_result").
        reason: Human-readable explanation (used for logging/debugging).
    """

    action: Literal["allow", "replace_result", "block"]
    replacement: str | None = None
    reason: str | None = None


# ---------------------------------------------------------------------------
# Per-tool callback functions
# Each has signature: (tool_name, input_dict, result_dict, context, services) -> CallbackResult
# ---------------------------------------------------------------------------

CallbackFn = Callable[
    [str, dict, dict, dict, ServiceContainer],
    CallbackResult,
]


def lookup_customer_callback(
    tool_name: str,
    input_dict: dict,
    result_dict: dict,
    context: dict,
    services: ServiceContainer,
) -> CallbackResult:
    """Set context flags from customer profile after lookup_customer executes.

    Sets context["vip"] and context["account_closure"] from the customer tier/flags.
    Also scans context["user_message"] for legal keywords to set context["legal_complaint"].

    CCA Rule: Programmatic detection of escalation conditions, not LLM confidence.
    Returns action="allow" — this callback only enriches context, never blocks.
    """
    # Set VIP flag from customer tier
    tier = result_dict.get("tier", "")
    if tier == "vip":
        context["vip"] = True

    # Set account_closure flag from customer flags list
    flags = result_dict.get("flags", [])
    if "account_closure" in flags:
        context["account_closure"] = True

    # Scan user message for legal keywords (CCA: deterministic, not LLM confidence)
    user_message = context.get("user_message", "").lower()
    if any(keyword in user_message for keyword in LEGAL_KEYWORDS):
        context["legal_complaint"] = True

    return CallbackResult(action="allow")


def check_policy_callback(
    tool_name: str,
    input_dict: dict,
    result_dict: dict,
    context: dict,
    services: ServiceContainer,
) -> CallbackResult:
    """Set context requires_review flag from policy check result.

    CCA Rule: requires_review is amount > $500 regardless of tier.
    Returns action="allow" — this callback only enriches context, never blocks.
    """
    if result_dict.get("requires_review"):
        context["requires_review"] = True

    return CallbackResult(action="allow")


def escalation_callback(
    tool_name: str,
    input_dict: dict,
    result_dict: dict,
    context: dict,
    services: ServiceContainer,
) -> CallbackResult:
    """Enforce escalation rules for process_refund.

    CCA Rule: Deterministic business rules in code (PostToolUse callbacks), NEVER
    self-reported LLM confidence scores for routing.

    Escalation triggers (any one is sufficient):
    - vip: Customer is VIP tier
    - account_closure: Customer account is flagged for closure
    - legal_complaint: User message contained legal keywords
    - requires_review: Refund amount > $500 threshold

    Returns action="block" with structured error JSON if any trigger is active.
    Returns action="allow" if no escalation conditions are met.
    """
    escalation_flags = {
        "vip": "VIP account requires human review",
        "account_closure": "Account closure in progress requires human review",
        "legal_complaint": "Legal complaint detected — escalate immediately",
        "requires_review": "Refund amount exceeds $500 review threshold",
    }

    for flag, reason in escalation_flags.items():
        if context.get(flag):
            blocked_result = {
                "status": "blocked",
                "reason": reason,
                "flag_triggered": flag,
                "action_required": "escalate_to_human",
            }
            return CallbackResult(
                action="block",
                replacement=json.dumps(blocked_result),
                reason=reason,
            )

    return CallbackResult(action="allow")


def compliance_callback(
    tool_name: str,
    input_dict: dict,
    result_dict: dict,
    context: dict,
    services: ServiceContainer,
) -> CallbackResult:
    """Enforce PII redaction for log_interaction results.

    CCA Rule: Programmatic redaction enforces PCI compliance — system prompt instructions
    alone are unreliable.

    Credit card numbers matching NNN[N]-NNN[N]-NNN[N]-NNN[N] pattern are replaced with
    ****-****-****-NNNN (preserving last 4 digits for reference).

    Handles two result shapes:
    - Flat: {"details": "..."}  (used in unit tests)
    - Nested: {"status": "logged", "entry": {"details": "..."}}  (log_interaction output)

    Returns action="replace_result" with redacted JSON if any card numbers found.
    Returns action="allow" if no PII detected.
    """
    total_count = 0
    redacted_result = dict(result_dict)

    # Handle flat "details" field (unit-test shape)
    if "details" in result_dict:
        redacted_details, count = CARD_PATTERN.subn(r"****-****-****-\2", result_dict["details"])
        if count > 0:
            redacted_result["details"] = redacted_details
            total_count += count

    # Handle nested "entry.details" field (log_interaction handler output shape)
    entry = result_dict.get("entry")
    if isinstance(entry, dict) and "details" in entry:
        redacted_entry_details, count = CARD_PATTERN.subn(r"****-****-****-\2", entry["details"])
        if count > 0:
            redacted_entry = dict(entry)
            redacted_entry["details"] = redacted_entry_details
            redacted_result["entry"] = redacted_entry
            # Expose top-level "details" for test assertions and audit inspection
            redacted_result["details"] = redacted_entry_details
            total_count += count

    if total_count == 0:
        return CallbackResult(action="allow")

    return CallbackResult(
        action="replace_result",
        replacement=json.dumps(redacted_result),
        reason=f"Redacted {total_count} credit card number(s) from log details",
    )


# ---------------------------------------------------------------------------
# build_callbacks() factory
# ---------------------------------------------------------------------------


def build_callbacks() -> dict[str, CallbackFn]:
    """Build and return the per-tool callback registry.

    CCA Rule: Per-tool dispatch — each callback is registered for exactly one tool.
    Callbacks not registered for a tool are never called for that tool.

    Returns:
        Dict mapping tool_name -> callback function.
    """
    return {
        "lookup_customer": lookup_customer_callback,
        "check_policy": check_policy_callback,
        "process_refund": escalation_callback,
        "log_interaction": compliance_callback,
    }
