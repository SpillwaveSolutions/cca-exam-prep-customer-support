"""Tests for agentic loop (CORE-06)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from customer_service.agent.agent_loop import AgentResult, UsageSummary, run_agent_loop
from customer_service.agent.system_prompts import get_system_prompt


def _make_usage(inp=100, out=50, cr=0, cw=0):
    """Create a mock usage object matching Anthropic SDK shape."""
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


class TestAgentResult:
    def test_agent_result_fields(self):
        result = AgentResult(stop_reason="end_turn")
        assert result.stop_reason == "end_turn"
        assert result.messages == []
        assert result.tool_calls == []
        assert result.final_text == ""
        assert isinstance(result.usage, UsageSummary)

    def test_usage_summary_defaults(self):
        u = UsageSummary()
        assert u.input_tokens == 0
        assert u.output_tokens == 0
        assert u.cache_read_input_tokens == 0
        assert u.cache_creation_input_tokens == 0


class TestAgentLoop:
    def test_loop_end_turn(self, services):
        """Agent returns immediately when stop_reason is end_turn."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_response(
            stop_reason="end_turn",
            content=[_make_text_block("I've helped you!")],
        )
        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Hello",
            system_prompt="You are helpful.",
        )
        assert result.stop_reason == "end_turn"
        assert result.final_text == "I've helped you!"
        assert mock_client.messages.create.call_count == 1

    def test_loop_tool_use_then_end(self, services):
        """Agent dispatches tool, then ends on second call."""
        mock_client = MagicMock()
        # First call: tool_use
        tool_response = _make_response(
            stop_reason="tool_use",
            content=[_make_tool_use_block("lookup_customer", {"customer_id": "C001"})],
        )
        # Second call: end_turn
        end_response = _make_response(
            stop_reason="end_turn",
            content=[_make_text_block("Found Alice!")],
        )
        mock_client.messages.create.side_effect = [tool_response, end_response]

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Look up C001",
            system_prompt="You are helpful.",
        )
        assert result.stop_reason == "end_turn"
        assert result.final_text == "Found Alice!"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "lookup_customer"
        assert mock_client.messages.create.call_count == 2

    def test_loop_max_iterations(self, services):
        """Loop stops at max_iterations with correct stop_reason."""
        mock_client = MagicMock()
        # Always return tool_use to trigger infinite loop
        mock_client.messages.create.return_value = _make_response(
            stop_reason="tool_use",
            content=[_make_tool_use_block()],
        )
        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="Loop forever",
            system_prompt="test",
            max_iterations=3,
        )
        assert result.stop_reason == "max_iterations"
        assert mock_client.messages.create.call_count == 3

    def test_loop_usage_accumulation(self, services):
        """Usage tokens accumulated across iterations."""
        mock_client = MagicMock()
        tool_resp = _make_response(
            stop_reason="tool_use",
            content=[_make_tool_use_block()],
            usage=_make_usage(inp=100, out=50, cr=10, cw=5),
        )
        end_resp = _make_response(
            stop_reason="end_turn",
            content=[_make_text_block("Done")],
            usage=_make_usage(inp=80, out=30, cr=20, cw=0),
        )
        mock_client.messages.create.side_effect = [tool_resp, end_resp]

        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="test",
            system_prompt="test",
        )
        assert result.usage.input_tokens == 180  # 100 + 80
        assert result.usage.output_tokens == 80  # 50 + 30
        assert result.usage.cache_read_input_tokens == 30  # 10 + 20
        assert result.usage.cache_creation_input_tokens == 5  # 5 + 0

    def test_loop_handles_max_tokens_stop(self, services):
        """Non-tool stop reasons terminate gracefully."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_response(
            stop_reason="max_tokens",
            content=[_make_text_block("Truncat")],
        )
        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="test",
            system_prompt="test",
        )
        assert result.stop_reason == "max_tokens"
        assert result.final_text == "Truncat"

    def test_loop_no_content_type_checking(self, services):
        """Verify loop uses stop_reason, NOT content block types."""
        mock_client = MagicMock()
        # Return end_turn even though content has tool_use block
        # (hypothetical edge case — loop must trust stop_reason)
        mock_client.messages.create.return_value = _make_response(
            stop_reason="end_turn",
            content=[_make_tool_use_block(), _make_text_block("Done")],
        )
        result = run_agent_loop(
            client=mock_client,
            services=services,
            user_message="test",
            system_prompt="test",
        )
        # Must end, not dispatch tools, because stop_reason says end_turn
        assert result.stop_reason == "end_turn"
        assert mock_client.messages.create.call_count == 1


class TestSystemPrompt:
    def test_get_system_prompt_returns_string(self):
        prompt = get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_system_prompt_mentions_customer_support(self):
        prompt = get_system_prompt()
        assert "customer" in prompt.lower()
