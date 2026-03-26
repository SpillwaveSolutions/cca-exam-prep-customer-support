"""CCA Anti-Pattern 1: Confidence-Based Escalation.

WRONG PATTERN: System prompt tells Claude to self-rate confidence and route
based on a numeric threshold. This is the #1 CCA exam trap.

WHY IT FAILS:
- Claude reports high confidence even for cases that require escalation
- A $600 refund (amount > $500) gets processed instead of escalated
- Self-reported confidence is NEVER a reliable routing signal

CCA CORRECT PATTERN (in agent/callbacks.py):
- Deterministic business rules check amount, tier, and flags in code
- process_refund callback blocks when amount > $500, Claude naturally escalates

This module is imported ONLY by notebooks to demonstrate the failure.
Do NOT add callbacks or programmatic enforcement here — the anti-pattern
must fail in its expected way for the teaching comparison to work.
"""

from customer_service.agent.agent_loop import AgentResult, run_agent_loop
from customer_service.services.container import ServiceContainer

# ---------------------------------------------------------------------------
# The anti-pattern: confidence routing in the system prompt
# ---------------------------------------------------------------------------

CONFIDENCE_SYSTEM_PROMPT: str = (
    "You are a customer support agent for an online retail company. "
    "Your role is to help customers with refund requests, account inquiries, "
    "and general support issues.\n\n"
    "You have access to 5 tools:\n"
    "1. lookup_customer - Find customer profile by ID\n"
    "2. check_policy - Check refund eligibility against policy\n"
    "3. process_refund - Process an approved refund\n"
    "4. escalate_to_human - Transfer to human agent when needed\n"
    "5. log_interaction - Record the interaction for audit\n\n"
    "ESCALATION RULE:\n"
    "Before taking any action on a refund or escalation, rate your confidence "
    "from 0-100 that you can handle this case correctly without human assistance. "
    "If your confidence is below 70, use escalate_to_human to transfer the case. "
    "If your confidence is 70 or above, proceed to handle the case yourself, "
    "including processing refunds directly.\n\n"
    "Always look up the customer first before taking any action. "
    "Check policy before processing refunds. "
    "Log every interaction for compliance purposes.\n\n"
    "Be professional, empathetic, and efficient."
)


def run_confidence_agent(
    client: object,
    services: ServiceContainer,
    user_message: str,
    model: str = "claude-sonnet-4-6",
) -> AgentResult:
    """Run the confidence-based escalation anti-pattern agent.

    ANTI-PATTERN: No callbacks. Routing relies on self-reported confidence
    in the system prompt. Claude will typically report high confidence (>=70)
    and handle $600 refunds directly instead of escalating.

    Args:
        client: Anthropic API client
        services: Injected ServiceContainer
        user_message: Customer message
        model: Claude model identifier

    Returns:
        AgentResult — typically without escalation even for $600 refunds
    """
    return run_agent_loop(
        client=client,
        services=services,
        user_message=user_message,
        system_prompt=CONFIDENCE_SYSTEM_PROMPT,
        model=model,
    )
    # NOTE: No callbacks passed. This is the anti-pattern.
    # The correct pattern (in agent/callbacks.py) uses deterministic rules.
