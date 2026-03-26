"""Tests for PostToolUse callback enforcement layer.

CCA Principle #1: Programmatic enforcement beats prompt-based guidance.
These tests verify deterministic business-rule enforcement via callbacks.
"""

import json

import pytest

from customer_service.agent.callbacks import (
    CallbackResult,
    build_callbacks,
    check_policy_callback,
    compliance_callback,
    escalation_callback,
    lookup_customer_callback,
)
from customer_service.data.customers import CUSTOMERS
from customer_service.services.audit_log import AuditLog
from customer_service.services.container import ServiceContainer
from customer_service.services.customer_db import CustomerDatabase
from customer_service.services.escalation_queue import EscalationQueue
from customer_service.services.financial_system import FinancialSystem
from customer_service.services.policy_engine import PolicyEngine


@pytest.fixture
def fresh_services() -> ServiceContainer:
    """Fresh ServiceContainer with no prior state."""
    return ServiceContainer(
        customer_db=CustomerDatabase(CUSTOMERS),
        policy_engine=PolicyEngine(),
        financial_system=FinancialSystem(),
        escalation_queue=EscalationQueue(),
        audit_log=AuditLog(),
    )


# ---------------------------------------------------------------------------
# CallbackResult dataclass
# ---------------------------------------------------------------------------


class TestCallbackResult:
    def test_allow_action(self):
        result = CallbackResult(action="allow")
        assert result.action == "allow"
        assert result.replacement is None
        assert result.reason is None

    def test_block_action_with_replacement(self):
        replacement = json.dumps({"status": "blocked"})
        result = CallbackResult(action="block", replacement=replacement, reason="VIP account")
        assert result.action == "block"
        assert result.replacement == replacement
        assert result.reason == "VIP account"

    def test_replace_result_action(self):
        result = CallbackResult(action="replace_result", replacement='{"redacted": true}')
        assert result.action == "replace_result"


# ---------------------------------------------------------------------------
# escalation_callback: blocks when any escalation flag is set
# ---------------------------------------------------------------------------


class TestEscalationCallback:
    def test_block_refund_amount_over_500(self, fresh_services):
        """C003 $600 refund -> escalation_callback returns action='block'."""
        context: dict = {
            "user_message": "I want a refund",
            "requires_review": True,  # amount > $500
        }
        result_dict = {"status": "proposed", "amount": 600.0}
        cb_result = escalation_callback(
            "process_refund",
            {"customer_id": "C003", "order_id": "ORD-003", "amount": 600.0},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "block"
        replacement = json.loads(cb_result.replacement)
        assert replacement["status"] == "blocked"
        assert replacement["action_required"] == "escalate_to_human"

    def test_block_refund_vip(self, fresh_services):
        """C002 VIP -> escalation_callback returns action='block'."""
        context: dict = {
            "user_message": "Refund my order",
            "vip": True,
        }
        result_dict = {"status": "proposed", "amount": 100.0}
        cb_result = escalation_callback(
            "process_refund",
            {"customer_id": "C002", "order_id": "ORD-002", "amount": 100.0},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "block"
        replacement = json.loads(cb_result.replacement)
        assert replacement["action_required"] == "escalate_to_human"

    def test_block_refund_account_closure(self, fresh_services):
        """C004 account_closure flag -> escalation_callback returns action='block'."""
        context: dict = {
            "user_message": "Process my refund",
            "account_closure": True,
        }
        result_dict = {"status": "proposed", "amount": 50.0}
        cb_result = escalation_callback(
            "process_refund",
            {"customer_id": "C004", "order_id": "ORD-004", "amount": 50.0},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "block"
        replacement = json.loads(cb_result.replacement)
        assert replacement["action_required"] == "escalate_to_human"

    def test_block_refund_legal_complaint(self, fresh_services):
        """Message with 'lawsuit' -> legal_complaint flag set, callback returns action='block'."""
        context: dict = {
            "user_message": "I will file a lawsuit if you don't refund me",
            "legal_complaint": True,
        }
        result_dict = {"status": "proposed", "amount": 50.0}
        cb_result = escalation_callback(
            "process_refund",
            {"customer_id": "C001", "order_id": "ORD-001", "amount": 50.0},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "block"
        replacement = json.loads(cb_result.replacement)
        assert replacement["action_required"] == "escalate_to_human"

    def test_allow_refund_no_flags(self, fresh_services):
        """C001 $50 refund, no flags -> escalation_callback returns action='allow'."""
        context: dict = {
            "user_message": "Please refund my order",
        }
        result_dict = {"status": "proposed", "amount": 50.0}
        cb_result = escalation_callback(
            "process_refund",
            {"customer_id": "C001", "order_id": "ORD-001", "amount": 50.0},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"

    def test_allow_refund_all_flags_false(self, fresh_services):
        """Explicit False flags should not trigger block."""
        context: dict = {
            "user_message": "Refund please",
            "vip": False,
            "account_closure": False,
            "legal_complaint": False,
            "requires_review": False,
        }
        result_dict = {"status": "proposed", "amount": 50.0}
        cb_result = escalation_callback(
            "process_refund",
            {"customer_id": "C001", "order_id": "ORD-001", "amount": 50.0},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"


# ---------------------------------------------------------------------------
# compliance_callback: PII redaction for log_interaction
# ---------------------------------------------------------------------------


class TestComplianceCallback:
    def test_redact_credit_card_number(self, fresh_services):
        """log details with '4111-1111-1111-1111' -> action='replace_result' with redaction."""
        context: dict = {"user_message": "help"}
        result_dict = {
            "status": "logged",
            "details": "Card used: 4111-1111-1111-1111 for refund",
        }
        cb_result = compliance_callback(
            "log_interaction",
            {"customer_id": "C001", "action": "refund", "details": "card details"},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "replace_result"
        replacement = json.loads(cb_result.replacement)
        assert "4111-1111-1111-1111" not in replacement["details"]
        assert "****-****-****-1111" in replacement["details"]

    def test_redact_credit_card_with_spaces(self, fresh_services):
        """Card numbers with spaces should also be redacted."""
        context: dict = {"user_message": "help"}
        result_dict = {
            "status": "logged",
            "details": "Card: 4111 1111 1111 1111 processed",
        }
        cb_result = compliance_callback(
            "log_interaction",
            {},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "replace_result"
        replacement = json.loads(cb_result.replacement)
        assert "4111 1111 1111 1111" not in replacement["details"]

    def test_no_redaction_needed_allows(self, fresh_services):
        """log details without card numbers -> compliance_callback returns action='allow'."""
        context: dict = {"user_message": "help"}
        result_dict = {
            "status": "logged",
            "details": "Customer called about a refund inquiry",
        }
        cb_result = compliance_callback(
            "log_interaction",
            {},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"

    def test_redact_preserves_last_four(self, fresh_services):
        """Redacted card should end with last 4 digits."""
        context: dict = {"user_message": "help"}
        result_dict = {
            "status": "logged",
            "details": "Card 5555-5555-5555-4444 used",
        }
        cb_result = compliance_callback(
            "log_interaction",
            {},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "replace_result"
        replacement = json.loads(cb_result.replacement)
        assert "****-****-****-4444" in replacement["details"]


# ---------------------------------------------------------------------------
# lookup_customer_callback: sets context flags from customer profile
# ---------------------------------------------------------------------------


class TestLookupCustomerCallback:
    def test_sets_vip_flag_for_vip_customer(self, fresh_services):
        """VIP customer lookup sets context['vip'] = True."""
        context: dict = {"user_message": "hello"}
        result_dict = {
            "customer_id": "C002",
            "name": "Bob Chen",
            "tier": "vip",
            "flags": [],
        }
        cb_result = lookup_customer_callback(
            "lookup_customer",
            {"customer_id": "C002"},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"
        assert context.get("vip") is True

    def test_sets_account_closure_flag(self, fresh_services):
        """Customer with account_closure flag sets context['account_closure'] = True."""
        context: dict = {"user_message": "hello"}
        result_dict = {
            "customer_id": "C004",
            "name": "David Kim",
            "tier": "regular",
            "flags": ["account_closure"],
        }
        cb_result = lookup_customer_callback(
            "lookup_customer",
            {"customer_id": "C004"},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"
        assert context.get("account_closure") is True

    def test_sets_legal_complaint_from_user_message(self, fresh_services):
        """Legal keywords in user_message set context['legal_complaint'] = True."""
        context: dict = {"user_message": "I will sue your company if you don't help me"}
        result_dict = {"customer_id": "C001", "tier": "regular", "flags": []}
        cb_result = lookup_customer_callback(
            "lookup_customer",
            {"customer_id": "C001"},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"
        assert context.get("legal_complaint") is True

    def test_no_flags_for_regular_customer(self, fresh_services):
        """Regular customer with no flags sets nothing alarming."""
        context: dict = {"user_message": "Can you help me with my order?"}
        result_dict = {"customer_id": "C001", "tier": "regular", "flags": []}
        cb_result = lookup_customer_callback(
            "lookup_customer",
            {"customer_id": "C001"},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"
        assert not context.get("vip")
        assert not context.get("account_closure")
        assert not context.get("legal_complaint")


# ---------------------------------------------------------------------------
# check_policy_callback: sets requires_review flag from policy result
# ---------------------------------------------------------------------------


class TestCheckPolicyCallback:
    def test_sets_requires_review_when_true(self, fresh_services):
        """Policy result with requires_review=True sets context flag."""
        context: dict = {"user_message": "refund"}
        result_dict = {"approved": True, "limit": 1000.0, "requires_review": True}
        cb_result = check_policy_callback(
            "check_policy",
            {"customer_id": "C001", "requested_amount": 600.0},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"
        assert context.get("requires_review") is True

    def test_no_requires_review_when_false(self, fresh_services):
        """Policy result with requires_review=False leaves flag unset."""
        context: dict = {"user_message": "refund"}
        result_dict = {"approved": True, "limit": 1000.0, "requires_review": False}
        cb_result = check_policy_callback(
            "check_policy",
            {"customer_id": "C001", "requested_amount": 50.0},
            result_dict,
            context,
            fresh_services,
        )
        assert cb_result.action == "allow"
        assert not context.get("requires_review")


# ---------------------------------------------------------------------------
# build_callbacks: factory function returns per-tool dict
# ---------------------------------------------------------------------------


class TestBuildCallbacks:
    def test_build_callbacks_returns_dict(self, fresh_services):
        callbacks = build_callbacks()
        assert isinstance(callbacks, dict)

    def test_build_callbacks_has_all_tools(self, fresh_services):
        callbacks = build_callbacks()
        assert "lookup_customer" in callbacks
        assert "check_policy" in callbacks
        assert "process_refund" in callbacks
        assert "log_interaction" in callbacks

    def test_callbacks_are_callable(self, fresh_services):
        callbacks = build_callbacks()
        for tool_name, cb in callbacks.items():
            assert callable(cb), f"Callback for {tool_name} is not callable"

    def test_process_refund_key_maps_to_escalation_callback(self, fresh_services):
        """Per-tool registry dispatches ONLY to the registered tool."""
        callbacks = build_callbacks()
        assert "process_refund" in callbacks
        # Verify it is actually the escalation logic by calling it with a blocked scenario
        context: dict = {"user_message": "refund", "requires_review": True}
        cb_func = callbacks["process_refund"]
        result = cb_func(
            "process_refund",
            {"customer_id": "C003", "order_id": "ORD-003", "amount": 600.0},
            {"status": "proposed"},
            context,
            fresh_services,
        )
        assert result.action == "block"

    def test_log_interaction_key_maps_to_compliance_callback(self, fresh_services):
        """log_interaction callback is the PII redaction logic."""
        callbacks = build_callbacks()
        context: dict = {"user_message": "help"}
        result_dict = {"status": "logged", "details": "Card 4111-1111-1111-1111"}
        cb_func = callbacks["log_interaction"]
        result = cb_func("log_interaction", {}, result_dict, context, fresh_services)
        assert result.action == "replace_result"


# ---------------------------------------------------------------------------
# Task 2: Dispatch integration and veto guarantee tests
# ---------------------------------------------------------------------------


class TestVetoGuarantee:
    """Veto guarantee: blocked refund must NOT touch FinancialSystem."""

    def test_veto_guarantee_financial_system_untouched(self, fresh_services):
        """Fresh ServiceContainer + C003 $600 -> FinancialSystem.get_processed() stays empty."""
        from customer_service.tools.handlers import dispatch

        callbacks = build_callbacks()
        # requires_review is pre-set because $600 > $500 (normally set by check_policy_callback)
        context: dict = {"user_message": "Please refund my order", "requires_review": True}

        result = dispatch(
            "process_refund",
            {"customer_id": "C003", "order_id": "ORD-003", "amount": 600.0, "reason": "Test"},
            fresh_services,
            context=context,
            callbacks=callbacks,
        )

        parsed = json.loads(result)
        assert parsed["status"] == "blocked"
        assert parsed["action_required"] == "escalate_to_human"
        # VETO GUARANTEE: FinancialSystem must be untouched
        assert fresh_services.financial_system.get_processed() == []

    def test_allow_commits_to_financial_system(self, fresh_services):
        """C001 $50 refund, no escalation flags -> FinancialSystem records the refund."""
        from customer_service.tools.handlers import dispatch

        callbacks = build_callbacks()
        context: dict = {"user_message": "Please refund my small order"}

        result = dispatch(
            "process_refund",
            {"customer_id": "C001", "order_id": "ORD-001", "amount": 50.0, "reason": "Test"},
            fresh_services,
            context=context,
            callbacks=callbacks,
        )

        parsed = json.loads(result)
        assert parsed["status"] == "approved"
        # ALLOW: FinancialSystem must have one record
        assert len(fresh_services.financial_system.get_processed()) == 1

    def test_dispatch_backward_compatible(self, fresh_services):
        """dispatch() without context/callbacks still returns valid JSON."""
        from customer_service.tools.handlers import dispatch

        result = dispatch("lookup_customer", {"customer_id": "C001"}, fresh_services)
        parsed = json.loads(result)
        assert parsed["name"] == "Alice Johnson"

    def test_compliance_redaction_in_dispatch(self, fresh_services):
        """dispatch log_interaction with callbacks redacts card number in result.

        log_interaction returns {"status": "logged", "entry": {"details": "..."}},
        so we check entry.details for the redacted value.
        """
        from customer_service.tools.handlers import dispatch

        callbacks = build_callbacks()
        context: dict = {"user_message": "help"}

        result = dispatch(
            "log_interaction",
            {
                "customer_id": "C001",
                "action": "payment",
                "details": "Processed card 4111-1111-1111-1111",
            },
            fresh_services,
            context=context,
            callbacks=callbacks,
        )

        parsed = json.loads(result)
        entry_details = parsed.get("entry", {}).get("details", "")
        assert "4111-1111-1111-1111" not in entry_details
        assert "****-****-****-1111" in entry_details

    def test_compliance_audit_log_never_has_raw_pii(self, fresh_services):
        """THE CRITICAL TEST: PII must never reach AuditLog, not just returned JSON.

        CCA Rule: Programmatic redaction happens BEFORE the write, not after.
        This test catches the bug where dispatch runs the handler first (writing
        raw PII to audit_log) and only then redacts the returned JSON.
        """
        from customer_service.tools.handlers import dispatch

        callbacks = build_callbacks()
        context: dict = {"user_message": "help"}

        dispatch(
            "log_interaction",
            {
                "customer_id": "C001",
                "action": "payment",
                "details": "Customer provided card 4111-1111-1111-1111 for refund",
            },
            fresh_services,
            context=context,
            callbacks=callbacks,
        )

        # Check the ACTUAL audit log, not the returned JSON
        entries = fresh_services.audit_log.get_entries()
        assert len(entries) == 1
        assert "4111-1111-1111-1111" not in entries[0].details, (
            "Raw PII leaked to audit log — redaction must happen BEFORE handler write"
        )
        assert "****-****-****-1111" in entries[0].details

    def test_veto_guarantee_vip_customer(self, fresh_services):
        """VIP customer refund -> blocked, FinancialSystem untouched."""
        from customer_service.tools.handlers import dispatch

        callbacks = build_callbacks()
        context: dict = {"user_message": "I need a refund", "vip": True}

        result = dispatch(
            "process_refund",
            {"customer_id": "C002", "order_id": "ORD-002", "amount": 100.0, "reason": "Test"},
            fresh_services,
            context=context,
            callbacks=callbacks,
        )

        parsed = json.loads(result)
        assert parsed["status"] == "blocked"
        assert fresh_services.financial_system.get_processed() == []
