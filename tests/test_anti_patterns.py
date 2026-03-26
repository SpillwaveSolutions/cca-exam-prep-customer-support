"""Structural tests for CCA anti-pattern modules.

These tests verify module structure deterministically (no API calls).
They check exports, system prompt content, and tool schema shape.
"""

from customer_service.anti_patterns.confidence_escalation import (
    CONFIDENCE_SYSTEM_PROMPT,
    run_confidence_agent,
)
from customer_service.anti_patterns.prompt_compliance import (
    PROMPT_COMPLIANCE_SYSTEM_PROMPT,
    run_prompt_compliance_agent,
)
from customer_service.anti_patterns.swiss_army_agent import (
    SWISS_ARMY_SYSTEM_PROMPT,
    SWISS_ARMY_TOOLS,
    run_swiss_army_agent,
)
from customer_service.tools.definitions import TOOLS

# ---------------------------------------------------------------------------
# confidence_escalation.py
# ---------------------------------------------------------------------------


class TestConfidenceEscalation:
    def test_confidence_system_prompt_is_string(self):
        assert isinstance(CONFIDENCE_SYSTEM_PROMPT, str)

    def test_confidence_prompt_contains_confidence(self):
        assert "confidence" in CONFIDENCE_SYSTEM_PROMPT.lower()

    def test_confidence_prompt_contains_70(self):
        assert "70" in CONFIDENCE_SYSTEM_PROMPT

    def test_confidence_prompt_contains_escalate(self):
        assert "escalate" in CONFIDENCE_SYSTEM_PROMPT.lower()

    def test_confidence_prompt_contains_rate(self):
        """Prompt must instruct Claude to rate its confidence."""
        assert "rate" in CONFIDENCE_SYSTEM_PROMPT.lower()

    def test_confidence_prompt_is_substantial(self):
        """Prompt must be long enough to be a real system prompt."""
        assert len(CONFIDENCE_SYSTEM_PROMPT) > 100

    def test_run_confidence_agent_is_callable(self):
        assert callable(run_confidence_agent)

    def test_run_confidence_agent_signature(self):
        """run_confidence_agent(client, services, user_message, model=...) -> callable."""
        import inspect

        sig = inspect.signature(run_confidence_agent)
        params = list(sig.parameters.keys())
        assert "client" in params
        assert "services" in params
        assert "user_message" in params


# ---------------------------------------------------------------------------
# prompt_compliance.py
# ---------------------------------------------------------------------------


class TestPromptCompliance:
    def test_prompt_compliance_system_prompt_is_string(self):
        assert isinstance(PROMPT_COMPLIANCE_SYSTEM_PROMPT, str)

    def test_prompt_compliance_contains_credit_card(self):
        assert "credit card" in PROMPT_COMPLIANCE_SYSTEM_PROMPT.lower()

    def test_prompt_compliance_contains_redact(self):
        assert "redact" in PROMPT_COMPLIANCE_SYSTEM_PROMPT.lower()

    def test_prompt_compliance_contains_never_log(self):
        """Prompt must instruct Claude to never log sensitive data."""
        assert "never" in PROMPT_COMPLIANCE_SYSTEM_PROMPT.lower()
        assert "log" in PROMPT_COMPLIANCE_SYSTEM_PROMPT.lower()

    def test_prompt_compliance_is_substantial(self):
        assert len(PROMPT_COMPLIANCE_SYSTEM_PROMPT) > 100

    def test_run_prompt_compliance_agent_is_callable(self):
        assert callable(run_prompt_compliance_agent)

    def test_run_prompt_compliance_agent_signature(self):
        import inspect

        sig = inspect.signature(run_prompt_compliance_agent)
        params = list(sig.parameters.keys())
        assert "client" in params
        assert "services" in params
        assert "user_message" in params


# ---------------------------------------------------------------------------
# swiss_army_agent.py — 15 tools
# ---------------------------------------------------------------------------


class TestSwissArmyTools:
    def test_swiss_army_tools_has_exactly_15(self):
        assert len(SWISS_ARMY_TOOLS) == 15

    def test_swiss_army_tools_is_list_of_dicts(self):
        assert isinstance(SWISS_ARMY_TOOLS, list)
        for tool in SWISS_ARMY_TOOLS:
            assert isinstance(tool, dict)

    def test_each_tool_has_required_keys(self):
        """Every tool must have name, description, input_schema."""
        for tool in SWISS_ARMY_TOOLS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool missing 'description': {tool}"
            assert "input_schema" in tool, f"Tool missing 'input_schema': {tool}"

    def test_all_5_correct_tools_present(self):
        """All 5 correct tools must be in the 15-tool set."""
        correct_names = {t["name"] for t in TOOLS}
        swiss_names = {t["name"] for t in SWISS_ARMY_TOOLS}
        for name in correct_names:
            assert name in swiss_names, f"Correct tool '{name}' missing from SWISS_ARMY_TOOLS"

    def test_file_billing_dispute_present(self):
        """Canonical misroute target for $600 refund must be present."""
        names = [t["name"] for t in SWISS_ARMY_TOOLS]
        assert "file_billing_dispute" in names

    def test_create_support_ticket_present(self):
        """Canonical misroute target for closure/legal must be present."""
        names = [t["name"] for t in SWISS_ARMY_TOOLS]
        assert "create_support_ticket" in names

    def test_exactly_10_distractor_tools(self):
        correct_names = {t["name"] for t in TOOLS}
        distractors = [t for t in SWISS_ARMY_TOOLS if t["name"] not in correct_names]
        assert len(distractors) == 10

    def test_no_distractor_description_is_empty(self):
        correct_names = {t["name"] for t in TOOLS}
        for tool in SWISS_ARMY_TOOLS:
            if tool["name"] not in correct_names:
                assert len(tool["description"]) >= 20, (
                    f"Distractor '{tool['name']}' description too short: {tool['description']!r}"
                )

    def test_all_expected_distractor_names_present(self):
        """Verify all 10 named distractors from the plan spec are present."""
        expected_distractors = {
            "check_shipping_status",
            "lookup_order_history",
            "check_inventory",
            "update_billing_info",
            "file_billing_dispute",
            "create_support_ticket",
            "reset_password",
            "update_account_settings",
            "search_knowledge_base",
            "send_feedback_survey",
        }
        swiss_names = {t["name"] for t in SWISS_ARMY_TOOLS}
        for name in expected_distractors:
            assert name in swiss_names, f"Expected distractor '{name}' missing"

    def test_swiss_army_system_prompt_is_string(self):
        assert isinstance(SWISS_ARMY_SYSTEM_PROMPT, str)
        assert len(SWISS_ARMY_SYSTEM_PROMPT) > 50

    def test_run_swiss_army_agent_is_callable(self):
        assert callable(run_swiss_army_agent)

    def test_run_swiss_army_agent_signature(self):
        import inspect

        sig = inspect.signature(run_swiss_army_agent)
        params = list(sig.parameters.keys())
        assert "client" in params
        assert "services" in params
        assert "user_message" in params


# ---------------------------------------------------------------------------
# __init__.py re-exports
# ---------------------------------------------------------------------------


class TestAntiPatternsInit:
    def test_init_exports_confidence_agent(self):
        from customer_service.anti_patterns import run_confidence_agent as rca

        assert callable(rca)

    def test_init_exports_prompt_compliance_agent(self):
        from customer_service.anti_patterns import run_prompt_compliance_agent as rpca

        assert callable(rpca)

    def test_init_exports_swiss_army_agent(self):
        from customer_service.anti_patterns import run_swiss_army_agent as rsaa

        assert callable(rsaa)

    def test_init_exports_confidence_prompt(self):
        from customer_service.anti_patterns import CONFIDENCE_SYSTEM_PROMPT

        assert isinstance(CONFIDENCE_SYSTEM_PROMPT, str)

    def test_init_exports_prompt_compliance_prompt(self):
        from customer_service.anti_patterns import PROMPT_COMPLIANCE_SYSTEM_PROMPT

        assert isinstance(PROMPT_COMPLIANCE_SYSTEM_PROMPT, str)

    def test_init_exports_swiss_army_tools(self):
        from customer_service.anti_patterns import SWISS_ARMY_TOOLS

        assert len(SWISS_ARMY_TOOLS) == 15
