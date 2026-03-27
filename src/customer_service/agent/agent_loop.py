"""Agentic tool-use loop for CCA Customer Support agent.

CCA Rules enforced here:
- Terminate on stop_reason, NEVER content-type checking (CCA agentic loop rule)
- stop_reason == 'end_turn' -> agent is done
- stop_reason == 'tool_use' -> dispatch tools, continue loop
- Accumulate usage tokens across all iterations
- Safety limit: max_iterations guard returns 'max_iterations' stop_reason
"""

from dataclasses import dataclass, field

from customer_service.services.container import ServiceContainer
from customer_service.tools.definitions import TOOLS
from customer_service.tools.handlers import dispatch


@dataclass
class UsageSummary:
    """Accumulated token usage across all loop iterations."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


@dataclass
class AgentResult:
    """Result returned by run_agent_loop."""

    stop_reason: str
    messages: list = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    final_text: str = ""
    usage: UsageSummary = field(default_factory=UsageSummary)


def run_agent_loop(
    client: object,
    services: ServiceContainer,
    user_message: str,
    system_prompt: str | list[dict],
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 4096,
    max_iterations: int = 10,
    tools: list[dict] | None = None,
    callbacks: dict | None = None,
) -> AgentResult:
    """Run the agentic tool-use loop until end_turn or max_iterations.

    CCA Rule: Terminate on stop_reason ONLY — never check content block types.
    This is deterministic: stop_reason drives all flow control.

    Args:
        client: Anthropic API client (or mock in tests)
        services: Injected ServiceContainer with all 5 services
        user_message: Initial customer message
        system_prompt: System context (context only, rules enforced in callbacks).
            Accepts either a plain string OR a list of TextBlockParam dicts for
            prompt caching (OPTIM-01). Pass get_system_prompt_with_caching() to
            enable caching of the POLICY_DOCUMENT block. The Anthropic SDK's
            client.messages.create(system=...) natively accepts both forms.
        model: Claude model identifier
        max_tokens: Max output tokens per API call
        max_iterations: Safety limit to prevent infinite loops
        tools: Tool schemas to pass to the API. Defaults to TOOLS (5 correct tools).
            Anti-pattern modules may pass SWISS_ARMY_TOOLS (15 tools) here.
        callbacks: Per-tool PostToolUse callback registry from build_callbacks().
            CCA Principle #1: programmatic enforcement beats prompt-based guidance.

    Returns:
        AgentResult with stop_reason, all messages, tool_calls, final_text, and usage
    """
    active_tools = tools if tools is not None else TOOLS
    # Build context dict for callback enrichment (user_message + escalation flags)
    context: dict = {"user_message": user_message}
    messages: list[dict] = [{"role": "user", "content": user_message}]
    tool_calls: list[dict] = []
    usage = UsageSummary()

    for _iteration in range(max_iterations):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            tools=active_tools,
            messages=messages,
        )

        # Accumulate usage across all iterations
        usage.input_tokens += response.usage.input_tokens
        usage.output_tokens += response.usage.output_tokens
        usage.cache_read_input_tokens += getattr(response.usage, "cache_read_input_tokens", 0) or 0
        usage.cache_creation_input_tokens += (
            getattr(response.usage, "cache_creation_input_tokens", 0) or 0
        )

        # Append assistant turn to message history
        messages.append({"role": "assistant", "content": response.content})

        # CCA RULE: Check stop_reason, NEVER content block types
        if response.stop_reason != "tool_use":
            # Extract final text from text blocks
            final_text = ""
            for block in response.content:
                if hasattr(block, "type") and block.type == "text":
                    final_text = block.text
                    break
            return AgentResult(
                stop_reason=response.stop_reason,
                messages=messages,
                tool_calls=tool_calls,
                final_text=final_text,
                usage=usage,
            )

        # Dispatch all tool_use blocks and collect results
        tool_results = []
        for block in response.content:
            if not (hasattr(block, "type") and block.type == "tool_use"):
                continue

            tool_calls.append({"name": block.name, "input": block.input, "id": block.id})
            result_content = dispatch(
                block.name, block.input, services, context=context, callbacks=callbacks
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                }
            )

        # CCA PITFALL: Send ONLY tool_result blocks — no text alongside them
        messages.append({"role": "user", "content": tool_results})

    # Safety limit exceeded
    return AgentResult(
        stop_reason="max_iterations",
        messages=messages,
        tool_calls=tool_calls,
        final_text="",
        usage=usage,
    )
