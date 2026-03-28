"""Tests for HANDOFF-02: coordinator-subagent pattern with context isolation.

Behavior-first tests:
- Subagent messages list does NOT contain coordinator system prompt or history
- Each subagent receives only its task-specific context string
- Coordinator assembles results into CoordinatorResult
- CoordinatorResult.subagent_results has correct count
- run_agent_loop called once per subtask
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from customer_service.agent.coordinator import CoordinatorResult, run_coordinator
from customer_service.data.customers import CUSTOMERS
from customer_service.services.audit_log import AuditLog
from customer_service.services.container import ServiceContainer
from customer_service.services.customer_db import CustomerDatabase
from customer_service.services.escalation_queue import EscalationQueue
from customer_service.services.financial_system import FinancialSystem
from customer_service.services.policy_engine import PolicyEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_usage():
    return SimpleNamespace(
        input_tokens=100,
        output_tokens=50,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )


def _make_text_response(text="Done"):
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=text)],
        usage=_make_usage(),
    )


def _make_services():
    return ServiceContainer(
        customer_db=CustomerDatabase(CUSTOMERS),
        policy_engine=PolicyEngine(),
        financial_system=FinancialSystem(),
        escalation_queue=EscalationQueue(),
        audit_log=AuditLog(),
    )


def _make_coordinator_decomposition_response(topics=None):
    """Return a mock coordinator API response that decomposes into subtasks."""
    if topics is None:
        topics = ["refund", "shipping"]
    subtasks = [{"topic": t, "relevant_details": f"Details for {t}"} for t in topics]
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[
            SimpleNamespace(
                type="text",
                text=json.dumps(subtasks),
            )
        ],
        usage=_make_usage(),
    )


# ---------------------------------------------------------------------------
# TestSubagentContextIsolation
# ---------------------------------------------------------------------------


class TestSubagentContextIsolation:
    """Subagent receives only explicit context string, not coordinator history."""

    def test_subagent_user_message_contains_customer_and_task(self):
        """Each subagent user_message is an explicit context string with Customer and Task."""
        services = _make_services()

        coordinator_response = _make_coordinator_decomposition_response(["refund"])
        synthesis_response = _make_text_response("Resolved your refund and shipping issues.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary

        captured_user_messages = []

        def fake_run_agent_loop(client, services, user_message, system_prompt, **kwargs):
            captured_user_messages.append(user_message)
            return AgentResult(
                stop_reason="end_turn",
                final_text="Refund processed",
                usage=UsageSummary(input_tokens=50, output_tokens=20),
            )

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            side_effect=fake_run_agent_loop,
        ):
            run_coordinator(
                client=mock_client,
                services=services,
                user_message="I need help with my refund",
                customer_id="C001",
                customer_tier="standard",
            )

        assert len(captured_user_messages) == 1
        msg = captured_user_messages[0]
        assert "Customer" in msg, f"Expected 'Customer' in subagent message, got: {msg!r}"
        assert "Task" in msg, f"Expected 'Task' in subagent message, got: {msg!r}"
        assert "C001" in msg, "Expected customer_id in subagent message"

    def test_subagent_message_does_not_contain_coordinator_system_prompt(self):
        """Subagent user_message must NOT contain the coordinator system prompt text."""
        services = _make_services()

        coordinator_response = _make_coordinator_decomposition_response(["refund"])
        synthesis_response = _make_text_response("Resolved.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary
        from customer_service.agent.coordinator import COORDINATOR_SYSTEM_PROMPT

        captured_user_messages = []

        def fake_run_agent_loop(client, services, user_message, system_prompt, **kwargs):
            captured_user_messages.append(user_message)
            return AgentResult(
                stop_reason="end_turn",
                final_text="Done",
                usage=UsageSummary(),
            )

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            side_effect=fake_run_agent_loop,
        ):
            run_coordinator(
                client=mock_client,
                services=services,
                user_message="I need help",
                customer_id="C001",
            )

        assert len(captured_user_messages) == 1
        msg = captured_user_messages[0]
        # Coordinator system prompt text must NOT appear in subagent's user_message
        coordinator_snippet = COORDINATOR_SYSTEM_PROMPT[:50]
        assert coordinator_snippet not in msg, (
            "Subagent user_message must not contain coordinator system prompt text"
        )

    def test_subagent_message_is_string_not_messages_list(self):
        """Subagent user_message is a string (explicit context), not a messages list."""
        services = _make_services()

        coordinator_response = _make_coordinator_decomposition_response(["account"])
        synthesis_response = _make_text_response("Account updated.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary

        captured_user_messages = []

        def fake_run_agent_loop(client, services, user_message, system_prompt, **kwargs):
            captured_user_messages.append(user_message)
            return AgentResult(
                stop_reason="end_turn",
                final_text="Done",
                usage=UsageSummary(),
            )

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            side_effect=fake_run_agent_loop,
        ):
            run_coordinator(
                client=mock_client,
                services=services,
                user_message="update my account",
                customer_id="C001",
            )

        assert len(captured_user_messages) == 1
        assert isinstance(captured_user_messages[0], str), (
            "Subagent user_message must be a string, not a messages list"
        )


# ---------------------------------------------------------------------------
# TestCoordinatorAssembly
# ---------------------------------------------------------------------------


class TestCoordinatorAssembly:
    """Coordinator assembles results from all subagents into CoordinatorResult."""

    def test_coordinator_result_has_correct_subagent_count(self):
        """CoordinatorResult.subagent_results has length equal to decomposed subtasks."""
        services = _make_services()

        # Coordinator decomposes into 2 subtasks: refund + shipping
        coordinator_response = _make_coordinator_decomposition_response(["refund", "shipping"])
        synthesis_response = _make_text_response("Both issues resolved.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary

        def fake_run_agent_loop(client, services, user_message, system_prompt, **kwargs):
            return AgentResult(
                stop_reason="end_turn",
                final_text=f"Handled: {user_message[:30]}",
                usage=UsageSummary(input_tokens=50, output_tokens=20),
            )

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            side_effect=fake_run_agent_loop,
        ):
            result = run_coordinator(
                client=mock_client,
                services=services,
                user_message="refund my order and fix shipping",
                customer_id="C001",
            )

        assert isinstance(result, CoordinatorResult)
        assert len(result.subagent_results) == 2

    def test_coordinator_result_has_synthesis(self):
        """CoordinatorResult.synthesis is a non-empty string."""
        services = _make_services()

        coordinator_response = _make_coordinator_decomposition_response(["refund"])
        synthesis_response = _make_text_response("Your refund has been processed successfully.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary

        def fake_run_agent_loop(client, services, user_message, system_prompt, **kwargs):
            return AgentResult(
                stop_reason="end_turn",
                final_text="Refund handled",
                usage=UsageSummary(),
            )

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            side_effect=fake_run_agent_loop,
        ):
            result = run_coordinator(
                client=mock_client,
                services=services,
                user_message="refund",
                customer_id="C001",
            )

        assert isinstance(result.synthesis, str)
        assert len(result.synthesis) > 0

    def test_coordinator_result_three_subtasks(self):
        """CoordinatorResult assembles 3 subagent results for 3 decomposed subtasks."""
        services = _make_services()

        coordinator_response = _make_coordinator_decomposition_response(
            ["refund", "shipping", "account"]
        )
        synthesis_response = _make_text_response("All three issues resolved.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary

        def fake_run_agent_loop(client, services, user_message, system_prompt, **kwargs):
            return AgentResult(
                stop_reason="end_turn",
                final_text="Done",
                usage=UsageSummary(),
            )

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            side_effect=fake_run_agent_loop,
        ):
            result = run_coordinator(
                client=mock_client,
                services=services,
                user_message="refund, shipping, and account",
                customer_id="C001",
            )

        assert len(result.subagent_results) == 3


# ---------------------------------------------------------------------------
# TestCoordinatorDelegation
# ---------------------------------------------------------------------------


class TestCoordinatorDelegation:
    """run_agent_loop is called exactly N times for N subtasks."""

    def test_delegation_call_count_matches_subtask_count(self):
        """Verify run_agent_loop is called exactly once per subtask."""
        services = _make_services()

        # 2 subtasks decomposed
        coordinator_response = _make_coordinator_decomposition_response(["refund", "shipping"])
        synthesis_response = _make_text_response("Done.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            return_value=AgentResult(
                stop_reason="end_turn",
                final_text="Done",
                usage=UsageSummary(),
            ),
        ) as mock_run:
            run_coordinator(
                client=mock_client,
                services=services,
                user_message="refund and shipping",
                customer_id="C001",
            )

        assert mock_run.call_count == 2, (
            f"Expected run_agent_loop called 2 times, got {mock_run.call_count}"
        )

    def test_delegation_single_subtask_calls_once(self):
        """Single subtask calls run_agent_loop exactly once."""
        services = _make_services()

        coordinator_response = _make_coordinator_decomposition_response(["refund"])
        synthesis_response = _make_text_response("Done.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            return_value=AgentResult(
                stop_reason="end_turn",
                final_text="Done",
                usage=UsageSummary(),
            ),
        ) as mock_run:
            run_coordinator(
                client=mock_client,
                services=services,
                user_message="just a refund",
                customer_id="C001",
            )

        assert mock_run.call_count == 1


# ---------------------------------------------------------------------------
# TestSubagentFreshMessages
# ---------------------------------------------------------------------------


class TestSubagentFreshMessages:
    """Each subagent call receives a fresh user_message string."""

    def test_each_subagent_call_has_unique_context(self):
        """Each subagent user_message contains the task-specific topic."""
        services = _make_services()

        coordinator_response = _make_coordinator_decomposition_response(["refund", "shipping"])
        synthesis_response = _make_text_response("Done.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary

        captured_calls = []

        def fake_run_agent_loop(client, services, user_message, system_prompt, **kwargs):
            captured_calls.append({"user_message": user_message, "system_prompt": system_prompt})
            return AgentResult(
                stop_reason="end_turn",
                final_text="Done",
                usage=UsageSummary(),
            )

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            side_effect=fake_run_agent_loop,
        ):
            run_coordinator(
                client=mock_client,
                services=services,
                user_message="refund and shipping issue",
                customer_id="C001",
                customer_tier="standard",
            )

        assert len(captured_calls) == 2
        # Each call must have a unique user_message (not the same string)
        msg0 = captured_calls[0]["user_message"]
        msg1 = captured_calls[1]["user_message"]
        assert msg0 != msg1, "Each subagent must receive a different context string"

    def test_subagent_receives_topic_specific_system_prompt(self):
        """Each subagent receives a system prompt specialized for its topic."""
        services = _make_services()

        coordinator_response = _make_coordinator_decomposition_response(["refund", "shipping"])
        synthesis_response = _make_text_response("Done.")

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [coordinator_response, synthesis_response]

        from customer_service.agent.agent_loop import AgentResult, UsageSummary
        from customer_service.agent.coordinator import SUBAGENT_PROMPTS

        captured_system_prompts = []

        def fake_run_agent_loop(client, services, user_message, system_prompt, **kwargs):
            captured_system_prompts.append(system_prompt)
            return AgentResult(
                stop_reason="end_turn",
                final_text="Done",
                usage=UsageSummary(),
            )

        with patch(
            "customer_service.agent.coordinator.run_agent_loop",
            side_effect=fake_run_agent_loop,
        ):
            run_coordinator(
                client=mock_client,
                services=services,
                user_message="refund and shipping",
                customer_id="C001",
            )

        assert len(captured_system_prompts) == 2
        assert captured_system_prompts[0] == SUBAGENT_PROMPTS["refund"]
        assert captured_system_prompts[1] == SUBAGENT_PROMPTS["shipping"]
