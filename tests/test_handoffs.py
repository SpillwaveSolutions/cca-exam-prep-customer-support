"""Tests for HANDOFF-01 (tool_choice forced escalation) and ANTI-05 (raw handoff).

Behavior-first tests:
- _has_escalation_required detects action_required: escalate_to_human in tool results
- Forced tool_choice produces EscalationRecord in escalation_queue (store verified)
- AgentResult.stop_reason == "escalated" after forced escalation
- Usage accumulates from both normal and forced calls
- format_raw_handoff output contains tool_use artifacts and is >5x structured length
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from customer_service.agent.agent_loop import _has_escalation_required, run_agent_loop
from customer_service.agent.callbacks import CallbackResult, build_callbacks
from customer_service.agent.system_prompts import get_system_prompt
from customer_service.anti_patterns.raw_handoff import format_raw_handoff
from customer_service.data.customers import CUSTOMERS
from customer_service.models.customer import EscalationRecord
from customer_service.services.audit_log import AuditLog
from customer_service.services.container import ServiceContainer
from customer_service.services.customer_db import CustomerDatabase
from customer_service.services.escalation_queue import EscalationQueue
from customer_service.services.financial_system import FinancialSystem
from customer_service.services.policy_engine import PolicyEngine

# ---------------------------------------------------------------------------
# Helpers shared across test classes
# ---------------------------------------------------------------------------


def _make_usage(inp=100, out=50, cr=0, cw=0):
    return SimpleNamespace(
        input_tokens=inp,
        output_tokens=out,
        cache_read_input_tokens=cr,
        cache_creation_input_tokens=cw,
    )


def _make_text_block(text="Done"):
    return SimpleNamespace(type="text", text=text)


def _make_tool_use_block(name="lookup_customer", input_dict=None, tool_id="toolu_01"):
    return SimpleNamespace(
        type="tool_use",
        name=name,
        input=input_dict or {"customer_id": "C001"},
        id=tool_id,
    )


def _make_response(stop_reason="end_turn", content=None, usage=None):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=content or [_make_text_block()],
        usage=usage or _make_usage(),
    )


def _make_services():
    return ServiceContainer(
        customer_db=CustomerDatabase(CUSTOMERS),
        policy_engine=PolicyEngine(),
        financial_system=FinancialSystem(),
        escalation_queue=EscalationQueue(),
        audit_log=AuditLog(),
    )


def _always_block_refund(tool_name, input_dict, result_dict, context, svc):
    """Test helper: callback that always blocks process_refund."""
    return CallbackResult(
        action="block",
        replacement=json.dumps(
            {
                "status": "blocked",
                "reason": "Refund amount exceeds $500 review threshold",
                "flag_triggered": "requires_review",
                "action_required": "escalate_to_human",
            }
        ),
    )


def _make_escalation_input(amount=750.0):
    return {
        "customer_id": "C001",
        "customer_tier": "standard",
        "issue_type": "refund",
        "disputed_amount": amount,
        "escalation_reason": "Refund amount exceeds $500 review threshold",
        "recommended_action": "Review refund request",
        "conversation_summary": f"Customer requested refund of ${amount}",
        "turns_elapsed": 1,
    }


# ---------------------------------------------------------------------------
# TestBlockedResultDetection
# ---------------------------------------------------------------------------


class TestBlockedResultDetection:
    """Tests for _has_escalation_required helper."""

    def test_detects_action_required_in_tool_result(self):
        """Returns True when any tool_result has action_required: escalate_to_human."""
        blocked_content = json.dumps(
            {
                "status": "blocked",
                "reason": "VIP account requires human review",
                "flag_triggered": "vip",
                "action_required": "escalate_to_human",
            }
        )
        tool_results = [
            {"type": "tool_result", "tool_use_id": "toolu_01", "content": blocked_content},
        ]
        assert _has_escalation_required(tool_results) is True

    def test_returns_false_for_normal_tool_results(self):
        """Returns False when no tool_result has action_required field."""
        normal_content = json.dumps({"status": "success", "customer_id": "C001"})
        tool_results = [
            {"type": "tool_result", "tool_use_id": "toolu_01", "content": normal_content},
        ]
        assert _has_escalation_required(tool_results) is False

    def test_returns_false_for_empty_list(self):
        """Returns False for empty tool results list."""
        assert _has_escalation_required([]) is False

    def test_detects_block_among_multiple_results(self):
        """Returns True when one of multiple results has action_required."""
        normal = json.dumps({"status": "success", "customer_id": "C001"})
        blocked = json.dumps(
            {
                "status": "blocked",
                "flag_triggered": "requires_review",
                "action_required": "escalate_to_human",
            }
        )
        tool_results = [
            {"type": "tool_result", "tool_use_id": "toolu_01", "content": normal},
            {"type": "tool_result", "tool_use_id": "toolu_02", "content": blocked},
        ]
        assert _has_escalation_required(tool_results) is True

    def test_returns_false_when_action_required_is_different_value(self):
        """Returns False when action_required is not 'escalate_to_human'."""
        content = json.dumps({"status": "blocked", "action_required": "retry"})
        tool_results = [
            {"type": "tool_result", "tool_use_id": "toolu_01", "content": content},
        ]
        assert _has_escalation_required(tool_results) is False


# ---------------------------------------------------------------------------
# TestToolChoiceEnforcement
# ---------------------------------------------------------------------------


class TestToolChoiceEnforcement:
    """Tests for forced tool_choice call when escalation_callback blocks process_refund."""

    def test_forced_escalation_stores_record_in_queue(self):
        """Forced tool_choice call produces EscalationRecord in escalation_queue."""
        services = _make_services()
        callbacks = build_callbacks()

        # check_policy uses 'requested_amount' key (not 'amount') for $750 > $500 trigger
        first_response = _make_response(
            stop_reason="tool_use",
            content=[
                _make_tool_use_block("lookup_customer", {"customer_id": "C001"}, "toolu_01"),
                _make_tool_use_block(
                    "check_policy",
                    {"customer_id": "C001", "requested_amount": 750.0, "order_id": "O001"},
                    "toolu_02",
                ),
                _make_tool_use_block(
                    "process_refund",
                    {"customer_id": "C001", "order_id": "O001", "amount": 750.0},
                    "toolu_03",
                ),
            ],
            usage=_make_usage(inp=200, out=100),
        )
        forced_response = _make_response(
            stop_reason="end_turn",
            content=[
                _make_tool_use_block(
                    "escalate_to_human", _make_escalation_input(750.0), "toolu_04"
                ),
            ],
            usage=_make_usage(inp=150, out=80),
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [first_response, forced_response]

        run_agent_loop(
            client=mock_client,
            services=services,
            user_message="I need a refund for order O001, it was $750",
            system_prompt=get_system_prompt(),
            callbacks=callbacks,
        )

        # TEST THE STORE — not just the return value
        escalations = services.escalation_queue.get_escalations()
        assert len(escalations) == 1, f"Expected 1 escalation in queue, got {len(escalations)}"
        assert escalations[0].customer_id == "C001"
        assert escalations[0].disputed_amount == 750.0

    def test_forced_escalation_stop_reason_is_escalated(self):
        """AgentResult.stop_reason == 'escalated' after forced tool_choice."""
        services = _make_services()

        first_response = _make_response(
            stop_reason="tool_use",
            content=[
                _make_tool_use_block(
                    "process_refund",
                    {"customer_id": "C001", "order_id": "O001", "amount": 750.0},
                    "toolu_01",
                ),
            ],
            usage=_make_usage(inp=200, out=100),
        )
        forced_response = _make_response(
            stop_reason="end_turn",
            content=[
                _make_tool_use_block(
                    "escalate_to_human", _make_escalation_input(750.0), "toolu_02"
                ),
            ],
            usage=_make_usage(inp=150, out=80),
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [first_response, forced_response]

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="I need a refund",
            system_prompt=get_system_prompt(),
            callbacks={"process_refund": _always_block_refund},
        )

        assert result.stop_reason == "escalated"

    def test_forced_escalation_uses_tool_choice(self):
        """Second API call uses tool_choice to force escalate_to_human."""
        services = _make_services()

        first_response = _make_response(
            stop_reason="tool_use",
            content=[
                _make_tool_use_block(
                    "process_refund",
                    {"customer_id": "C001", "order_id": "O001", "amount": 750.0},
                    "toolu_01",
                ),
            ],
        )
        forced_response = _make_response(
            stop_reason="end_turn",
            content=[
                _make_tool_use_block("escalate_to_human", _make_escalation_input(), "toolu_02"),
            ],
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [first_response, forced_response]

        run_agent_loop(
            client=mock_client,
            services=services,
            user_message="refund",
            system_prompt="test",
            callbacks={"process_refund": _always_block_refund},
        )

        # Verify second call used tool_choice
        assert mock_client.messages.create.call_count == 2
        second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
        assert "tool_choice" in second_call_kwargs
        assert second_call_kwargs["tool_choice"]["type"] == "tool"
        assert second_call_kwargs["tool_choice"]["name"] == "escalate_to_human"


# ---------------------------------------------------------------------------
# TestEscalatedStopReason
# ---------------------------------------------------------------------------


class TestEscalatedStopReason:
    """Verify stop_reason is exactly 'escalated' string (not 'end_turn')."""

    def test_stop_reason_is_escalated_not_end_turn(self):
        """stop_reason must be exactly 'escalated', never 'end_turn'."""
        services = _make_services()

        first_response = _make_response(
            stop_reason="tool_use",
            content=[
                _make_tool_use_block(
                    "process_refund",
                    {"customer_id": "C001", "order_id": "O001", "amount": 600.0},
                    "toolu_01",
                ),
            ],
        )
        forced_response = _make_response(
            stop_reason="end_turn",
            content=[
                _make_tool_use_block(
                    "escalate_to_human", _make_escalation_input(600.0), "toolu_02"
                ),
            ],
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [first_response, forced_response]

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="refund",
            system_prompt="test",
            callbacks={"process_refund": _always_block_refund},
        )

        assert result.stop_reason == "escalated"
        assert result.stop_reason != "end_turn"

    def test_normal_flow_still_returns_end_turn(self):
        """Normal flow (no blocked tools) still returns end_turn."""
        services = _make_services()
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_response(
            stop_reason="end_turn",
            content=[_make_text_block("All done!")],
        )

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="just say hello",
            system_prompt="test",
        )
        assert result.stop_reason == "end_turn"


# ---------------------------------------------------------------------------
# TestUsageAccumulation
# ---------------------------------------------------------------------------


class TestUsageAccumulation:
    """Usage tokens accumulate from both normal call and forced call."""

    def test_usage_accumulates_from_both_calls(self):
        """Total usage includes tokens from normal and forced API calls."""
        services = _make_services()

        first_response = _make_response(
            stop_reason="tool_use",
            content=[
                _make_tool_use_block(
                    "process_refund",
                    {"customer_id": "C001", "order_id": "O001", "amount": 600.0},
                    "toolu_01",
                ),
            ],
            usage=_make_usage(inp=200, out=100),
        )
        forced_response = _make_response(
            stop_reason="end_turn",
            content=[
                _make_tool_use_block(
                    "escalate_to_human", _make_escalation_input(600.0), "toolu_02"
                ),
            ],
            usage=_make_usage(inp=150, out=80),
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [first_response, forced_response]

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="refund",
            system_prompt="test",
            callbacks={"process_refund": _always_block_refund},
        )

        # Usage must accumulate from BOTH the normal call and the forced call
        assert result.usage.input_tokens == 350  # 200 + 150
        assert result.usage.output_tokens == 180  # 100 + 80


# ---------------------------------------------------------------------------
# TestRawHandoffAntiPattern
# ---------------------------------------------------------------------------


class TestRawHandoffAntiPattern:
    """format_raw_handoff produces observable noise (tool_use artifacts)."""

    def _make_fake_messages(self) -> list:
        """Create a realistic multi-turn conversation with tool_use and tool_result blocks.

        A realistic escalation conversation involves multiple turns: greet, lookup,
        check policy, attempt refund, get blocked. This raw dump is large to demonstrate
        the noise problem for human agents receiving the handoff.
        """
        return [
            {
                "role": "user",
                "content": (
                    "Hi, I need a refund for order O001 ($750). The item arrived damaged last week."
                ),
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "I'm sorry about the damaged item. "
                            "Let me look up your account and check refund policy."
                        ),
                    },
                    {
                        "type": "tool_use",
                        "id": "toolu_01",
                        "name": "lookup_customer",
                        "input": {"customer_id": "C001"},
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01",
                        "content": json.dumps(
                            {
                                "customer_id": "C001",
                                "name": "Alice Johnson",
                                "email": "alice@example.com",
                                "tier": "standard",
                                "account_status": "active",
                                "flags": [],
                                "order_history": ["O001", "O998", "O997"],
                                "registered_since": "2022-01-15",
                            }
                        ),
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Found your account. Checking refund policy for $750.",
                    },
                    {
                        "type": "tool_use",
                        "id": "toolu_02",
                        "name": "check_policy",
                        "input": {
                            "customer_id": "C001",
                            "requested_amount": 750.0,
                            "order_id": "O001",
                        },
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_02",
                        "content": json.dumps(
                            {
                                "eligible": True,
                                "requires_review": True,
                                "policy": (
                                    "Refund amounts above $500 require supervisor review "
                                    "before processing."
                                ),
                                "max_automatic_refund": 500.0,
                                "review_sla_hours": 24,
                            }
                        ),
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Policy requires review. Let me attempt to process it.",
                    },
                    {
                        "type": "tool_use",
                        "id": "toolu_03",
                        "name": "process_refund",
                        "input": {"customer_id": "C001", "order_id": "O001", "amount": 750.0},
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_03",
                        "content": json.dumps(
                            {
                                "status": "blocked",
                                "reason": (
                                    "Refund amount exceeds $500 review threshold. "
                                    "Supervisor approval required."
                                ),
                                "flag_triggered": "requires_review",
                                "action_required": "escalate_to_human",
                                "transaction_id": None,
                                "blocked_at": "2026-03-27T10:15:00Z",
                            }
                        ),
                    },
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "I was unable to process the refund automatically as it exceeds "
                            "our $500 threshold. Escalating to a human agent. "
                            "You will be contacted within 24 hours."
                        ),
                    },
                    {
                        "type": "tool_use",
                        "id": "toolu_04",
                        "name": "escalate_to_human",
                        "input": {
                            "customer_id": "C001",
                            "customer_tier": "standard",
                            "issue_type": "refund",
                            "disputed_amount": 750.0,
                            "escalation_reason": "Refund amount exceeds $500 review threshold",
                            "recommended_action": "Review and approve refund for damaged item",
                            "conversation_summary": (
                                "Alice Johnson requested refund of $750 for order O001 "
                                "citing damaged item. Policy confirmed requires_review. "
                                "Automated processing blocked."
                            ),
                            "turns_elapsed": 3,
                        },
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_04",
                        "content": json.dumps(
                            {"status": "escalated", "ticket_id": "ESC-2026-0042"}
                        ),
                    },
                ],
            },
        ]

    def test_raw_handoff_contains_tool_use_substring(self):
        """format_raw_handoff output must contain 'tool_use' (observable noise)."""
        messages = self._make_fake_messages()
        output = format_raw_handoff(messages)
        assert "tool_use" in output, "Raw handoff must contain 'tool_use' artifacts"

    def test_raw_handoff_is_longer_than_structured(self):
        """Raw handoff output is >5x longer than a structured EscalationRecord JSON."""
        messages = self._make_fake_messages()
        raw_output = format_raw_handoff(messages)

        record = EscalationRecord(
            customer_id="C001",
            customer_tier="standard",
            issue_type="refund",
            disputed_amount=750.0,
            escalation_reason="Refund amount exceeds $500 review threshold",
            recommended_action="Review and approve or deny refund request",
            conversation_summary=(
                "Customer Alice requested refund of $750 for order O001. "
                "Policy check flagged amount > $500 for review."
            ),
            turns_elapsed=3,
        )
        structured_json = json.dumps(record.model_dump())

        ratio = len(raw_output) / len(structured_json)
        assert ratio > 5, (
            f"Raw handoff ({len(raw_output)} chars) must be >5x structured "
            f"({len(structured_json)} chars). Got ratio {ratio:.1f}x"
        )


# ---------------------------------------------------------------------------
# TestHandoffTokenComparison
# ---------------------------------------------------------------------------


class TestHandoffTokenComparison:
    """Verify raw handoff char count vs structured handoff char count ratio."""

    def test_raw_vs_structured_char_count_ratio(self):
        """Explicitly verify raw:structured ratio exceeds 5."""
        many_messages = []
        for i in range(5):
            many_messages.extend(
                [
                    {"role": "user", "content": f"Turn {i} user message about refund"},
                    {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": f"Processing turn {i}..."},
                            {
                                "type": "tool_use",
                                "id": f"toolu_{i:02d}",
                                "name": "lookup_customer",
                                "input": {"customer_id": "C001", "turn": i},
                            },
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": f"toolu_{i:02d}",
                                "content": json.dumps(
                                    {
                                        "customer_id": "C001",
                                        "name": "Alice Smith",
                                        "tier": "standard",
                                        "account_status": "active",
                                        "turn": i,
                                    }
                                ),
                            },
                        ],
                    },
                ]
            )

        raw = format_raw_handoff(many_messages)
        structured = json.dumps(
            {
                "customer_id": "C001",
                "customer_tier": "standard",
                "issue_type": "refund",
                "disputed_amount": 150.0,
                "escalation_reason": "VIP tier",
                "recommended_action": "Approve",
                "conversation_summary": "Customer requested refund. 5 turns of lookup.",
                "turns_elapsed": 5,
            }
        )

        ratio = len(raw) / len(structured)
        assert ratio > 5, f"Expected ratio > 5, got {ratio:.1f}x"
