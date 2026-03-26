"""Tests for tool schemas, handlers, and dispatch registry."""

import json

from customer_service.tools.definitions import TOOLS
from customer_service.tools.handlers import DISPATCH, dispatch


class TestToolSchemas:
    """CORE-04: Tool schema structure and CCA compliance."""

    def test_tool_count(self):
        assert len(TOOLS) == 5

    def test_tool_schema_structure(self):
        for tool in TOOLS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool missing 'description': {tool}"
            assert "input_schema" in tool, f"Tool missing 'input_schema': {tool}"

    def test_tool_names(self):
        names = {t["name"] for t in TOOLS}
        expected = {
            "lookup_customer",
            "check_policy",
            "process_refund",
            "escalate_to_human",
            "log_interaction",
        }
        assert names == expected

    def test_tool_descriptions_have_negative_bounds(self):
        for tool in TOOLS:
            assert "does NOT" in tool["description"] or "does not" in tool["description"], (
                f"Tool '{tool['name']}' description missing negative bounds: {tool['description']}"
            )

    def test_no_title_in_input_schema(self):
        for tool in TOOLS:
            assert "title" not in tool["input_schema"], (
                f"Tool '{tool['name']}' input_schema has top-level 'title' key"
            )

    def test_input_schema_is_object_type(self):
        for tool in TOOLS:
            schema = tool["input_schema"]
            assert schema.get("type") == "object"
            assert "properties" in schema


class TestDispatchRegistry:
    """CORE-05: Dispatch routing."""

    def test_dispatch_has_all_tools(self):
        expected = {
            "lookup_customer",
            "check_policy",
            "process_refund",
            "escalate_to_human",
            "log_interaction",
        }
        assert set(DISPATCH.keys()) == expected

    def test_dispatch_lookup_customer(self, services):
        result = dispatch("lookup_customer", {"customer_id": "C001"}, services)
        parsed = json.loads(result)
        assert parsed["name"] == "Alice Johnson"

    def test_dispatch_check_policy(self, services):
        result = dispatch(
            "check_policy", {"customer_id": "C001", "requested_amount": 50.0}, services
        )
        parsed = json.loads(result)
        assert parsed["approved"] is True

    def test_dispatch_process_refund(self, services):
        result = dispatch(
            "process_refund",
            {"customer_id": "C001", "order_id": "ORD-001", "amount": 50.0, "reason": "Defective"},
            services,
        )
        parsed = json.loads(result)
        assert "status" in parsed

    def test_dispatch_escalate_to_human(self, services):
        result = dispatch(
            "escalate_to_human",
            {
                "customer_id": "C001",
                "customer_tier": "regular",
                "issue_type": "refund",
                "disputed_amount": 600.0,
                "escalation_reason": "Amount exceeds $500 threshold",
                "recommended_action": "Review refund manually",
                "conversation_summary": "Customer requested $600 refund",
                "turns_elapsed": 3,
            },
            services,
        )
        parsed = json.loads(result)
        assert parsed["status"] == "escalated"

    def test_dispatch_log_interaction(self, services):
        result = dispatch(
            "log_interaction",
            {
                "customer_id": "C001",
                "action": "lookup",
                "details": "Looked up customer profile",
            },
            services,
        )
        parsed = json.loads(result)
        assert parsed["status"] == "logged"

    def test_dispatch_unknown_tool_structured_error(self, services):
        """CCA Rule: Error responses use structured error context."""
        result = dispatch("nonexistent_tool", {}, services)
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["error_type"] == "unknown_tool"
        assert parsed["source"] == "dispatch"
        assert parsed["retry_eligible"] is False
        assert parsed["fallback_available"] is False
        assert parsed["partial_data"] is None

    def test_dispatch_malformed_input_returns_structured_error(self, services):
        """CCA Rule: Malformed input returns structured error, never raises."""
        # escalate_to_human requires many fields — passing empty dict triggers KeyError
        result = dispatch("escalate_to_human", {}, services)
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["error_type"] == "invalid_input"
        assert parsed["source"] == "escalate_to_human"
        assert parsed["retry_eligible"] is True

    def test_dispatch_malformed_log_interaction(self, services):
        """log_interaction with missing fields returns structured error."""
        result = dispatch("log_interaction", {}, services)
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["error_type"] == "invalid_input"
        assert parsed["source"] == "log_interaction"

    def test_all_handlers_return_json_strings(self, services):
        """Every handler must return a valid JSON string (CCA rule)."""
        test_inputs = {
            "lookup_customer": {"customer_id": "C001"},
            "check_policy": {"customer_id": "C001", "requested_amount": 50.0},
            "process_refund": {
                "customer_id": "C001",
                "order_id": "ORD-001",
                "amount": 50.0,
                "reason": "Test",
            },
            "escalate_to_human": {
                "customer_id": "C001",
                "customer_tier": "regular",
                "issue_type": "refund",
                "disputed_amount": 50.0,
                "escalation_reason": "test",
                "recommended_action": "test",
                "conversation_summary": "test",
                "turns_elapsed": 1,
            },
            "log_interaction": {"customer_id": "C001", "action": "test", "details": "test"},
        }
        for tool_name, input_dict in test_inputs.items():
            result = dispatch(tool_name, input_dict, services)
            assert isinstance(result, str), f"{tool_name} returned {type(result)}"
            json.loads(result)  # Must not raise
