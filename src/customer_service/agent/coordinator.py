"""Hub-and-spoke coordinator-subagent pattern for CCA Customer Support.

CCA Pattern 6 (Handoffs) — CORRECT coordinator approach.

Architecture:
  Coordinator decomposes multi-topic customer queries into subtasks, delegates each
  to a specialized subagent via run_agent_loop, then synthesizes results.

CCA Isolation Rule:
  Each subagent receives ONLY an explicit context string — never the coordinator's
  messages list or system prompt. This prevents context pollution and token waste.

  Correct:
    subagent_context = f"Customer ID: {customer_id}\\nTask: {topic}\\n..."
    run_agent_loop(..., user_message=subagent_context, ...)

  Wrong (anti-pattern — DO NOT do this):
    run_agent_loop(..., user_message=coordinator_messages, ...)
"""

import json
import re
from dataclasses import dataclass, field

from customer_service.agent.agent_loop import AgentResult, UsageSummary, run_agent_loop
from customer_service.agent.callbacks import build_callbacks
from customer_service.services.container import ServiceContainer

# ---------------------------------------------------------------------------
# Coordinator system prompt
# ---------------------------------------------------------------------------

COORDINATOR_SYSTEM_PROMPT = """You are a customer support coordinator.

Your job is to analyze a customer's message and decompose it into a JSON list of subtasks.
Each subtask handles one topic.

Available topics: "refund", "shipping", "account"

Return a JSON array where each element has:
  - "topic": one of "refund", "shipping", "account"
  - "relevant_details": the specific details from the customer message relevant to this topic

Example output:
[
  {"topic": "refund", "relevant_details": "Customer wants refund for order O001 ($750)"},
  {"topic": "shipping", "relevant_details": "Package not delivered after 10 days"}
]

Return ONLY the JSON array. No explanation, no preamble.
"""

# ---------------------------------------------------------------------------
# Per-topic subagent system prompts
# ---------------------------------------------------------------------------

REFUND_AGENT_PROMPT = """You are a refund specialist for a customer support team.

Your role is to help customers with refund requests. You can:
- Look up customer accounts
- Check refund policies
- Process eligible refunds
- Escalate high-value or complex refunds to human agents

Always verify customer eligibility before processing a refund.
Business rules are enforced by the system — do not override them.
"""

SHIPPING_AGENT_PROMPT = """You are a shipping specialist for a customer support team.

Your role is to help customers with shipping-related issues. You can:
- Look up customer accounts and order status
- Provide shipping estimates and tracking information
- Log shipping complaints and follow-up actions
- Escalate unresolved shipping disputes

Focus only on shipping-related aspects of the customer's request.
"""

ACCOUNT_AGENT_PROMPT = """You are an account management specialist for a customer support team.

Your role is to help customers with account-related issues. You can:
- Look up and update customer account information
- Handle account closure requests (escalate to human agent)
- Check account status and tier
- Log account-related interactions

Focus only on account-related aspects of the customer's request.
"""

SUBAGENT_PROMPTS: dict[str, str] = {
    "refund": REFUND_AGENT_PROMPT,
    "shipping": SHIPPING_AGENT_PROMPT,
    "account": ACCOUNT_AGENT_PROMPT,
}

# ---------------------------------------------------------------------------
# CoordinatorResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class CoordinatorResult:
    """Result returned by run_coordinator.

    Attributes:
        subagent_results: List of AgentResult from each specialized subagent.
        synthesis: Unified customer-facing response combining all subagent outputs.
    """

    subagent_results: list[AgentResult] = field(default_factory=list)
    synthesis: str = ""


# ---------------------------------------------------------------------------
# _parse_subtasks helper
# ---------------------------------------------------------------------------


def _parse_subtasks(response) -> list[dict]:
    """Extract JSON list of subtasks from coordinator's text response.

    Returns list of dicts with "topic" and "relevant_details" keys.
    Falls back to single "refund" subtask if parsing fails.

    Args:
        response: Claude API response object with .content list.

    Returns:
        List of subtask dicts, each with "topic" and "relevant_details".
    """
    text = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            text = block.text
            break

    # Extract JSON array — handle markdown code blocks
    json_match = re.search(r"\[.*\]", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)

    try:
        subtasks = json.loads(text)
        if isinstance(subtasks, list):
            # Filter to known topics only
            valid = [
                st
                for st in subtasks
                if isinstance(st, dict) and st.get("topic") in SUBAGENT_PROMPTS
            ]
            if valid:
                return valid
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: single refund subtask
    return [{"topic": "refund", "relevant_details": text or "Customer needs assistance"}]


# ---------------------------------------------------------------------------
# run_coordinator
# ---------------------------------------------------------------------------


def run_coordinator(
    client: object,
    services: ServiceContainer,
    user_message: str,
    customer_id: str = "",
    customer_tier: str = "",
    model: str = "claude-sonnet-4-6",
) -> CoordinatorResult:
    """Run the coordinator-subagent pattern for multi-topic customer queries.

    CCA Rule: Each subagent receives an explicit context string — never the coordinator's
    messages history. This is the hub-and-spoke isolation guarantee.

    Steps:
      1. Decompose: Call coordinator LLM to split customer message into subtasks.
      2. Delegate: For each subtask, build an explicit context string and call
         run_agent_loop with the topic-specific system prompt.
         CRITICAL: subagent gets ONLY the context string — no coordinator messages.
      3. Synthesize: Call LLM to combine all subagent outputs into a unified response.

    Args:
        client: Anthropic API client (or mock in tests).
        services: Injected ServiceContainer.
        user_message: Full customer message (may contain multiple topics).
        customer_id: Customer ID for context injection.
        customer_tier: Customer tier for context injection.
        model: Claude model identifier.

    Returns:
        CoordinatorResult with subagent_results list and synthesized response.
    """
    # Step 1 — Decompose: coordinator LLM splits message into subtasks
    decompose_response = client.messages.create(
        model=model,
        max_tokens=512,
        system=COORDINATOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    subtasks = _parse_subtasks(decompose_response)

    # Step 2 — Delegate: each subagent gets ONLY an explicit context string
    subagent_results: list[AgentResult] = []
    for subtask in subtasks:
        topic = subtask.get("topic", "refund")
        details = subtask.get("relevant_details", user_message)

        # CCA RULE: explicit context string — subagent NEVER sees coordinator messages
        subagent_context = (
            f"Customer ID: {customer_id}\n"
            f"Customer tier: {customer_tier}\n"
            f"Task: {topic}\n"
            f"Details: {details}\n"
        )

        system_prompt = SUBAGENT_PROMPTS.get(topic, REFUND_AGENT_PROMPT)
        agent_result = run_agent_loop(
            client=client,
            services=services,
            user_message=subagent_context,
            system_prompt=system_prompt,
            model=model,
            callbacks=build_callbacks(),
        )
        subagent_results.append(agent_result)

    # Step 3 — Synthesize: combine all subagent outputs into unified response
    subagent_summaries = "\n\n".join(
        f"[{subtasks[i].get('topic', 'unknown')}]: {r.final_text}"
        for i, r in enumerate(subagent_results)
    )
    synthesis_prompt = (
        f"Customer message: {user_message}\n\n"
        f"Specialist responses:\n{subagent_summaries}\n\n"
        "Write a unified, friendly response to the customer covering all their issues."
    )
    synthesis_response = client.messages.create(
        model=model,
        max_tokens=512,
        system="You are a customer support coordinator writing a final unified response.",
        messages=[{"role": "user", "content": synthesis_prompt}],
    )

    synthesis_text = ""
    for block in synthesis_response.content:
        if hasattr(block, "type") and block.type == "text":
            synthesis_text = block.text
            break

    return CoordinatorResult(
        subagent_results=subagent_results,
        synthesis=synthesis_text,
    )


# ---------------------------------------------------------------------------
# Unused import guard — UsageSummary imported for type completeness
# ---------------------------------------------------------------------------
__all__ = [
    "COORDINATOR_SYSTEM_PROMPT",
    "SUBAGENT_PROMPTS",
    "REFUND_AGENT_PROMPT",
    "SHIPPING_AGENT_PROMPT",
    "ACCOUNT_AGENT_PROMPT",
    "CoordinatorResult",
    "run_coordinator",
]

# Keep UsageSummary in scope — it's part of the AgentResult type used by callers
_UsageSummary = UsageSummary
