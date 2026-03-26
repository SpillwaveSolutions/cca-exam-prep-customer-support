"""CCA Anti-Pattern 2: Prompt-Only Compliance Enforcement.

WRONG PATTERN: System prompt instructs Claude to never log credit card numbers
or PII. No programmatic enforcement exists — compliance relies entirely on
Claude following the prompt instruction.

WHY IT FAILS:
- System prompts are probabilistic guidance, not deterministic enforcement
- Claude sometimes logs raw card numbers anyway (e.g., "4111-1111-1111-1111")
- Passing a compliance audit requires 100% reliability — prompts cannot provide this

CCA CORRECT PATTERN (in agent/callbacks.py):
- log_interaction callback runs a regex over the details field BEFORE the handler
  writes to the audit log
- Pattern: r'\\d{4}[-\\s]\\d{4}[-\\s]\\d{4}[-\\s]\\d{4}' → '****-****-****-NNNN'
- This runs on every single call, deterministically

This module is imported ONLY by notebooks to demonstrate the failure.
Do NOT add callbacks or redaction here — the anti-pattern must fail in its
expected way for the teaching comparison to work.
"""

from customer_service.agent.agent_loop import AgentResult, run_agent_loop
from customer_service.services.container import ServiceContainer

# ---------------------------------------------------------------------------
# The anti-pattern: compliance rules embedded in the system prompt only
# ---------------------------------------------------------------------------

PROMPT_COMPLIANCE_SYSTEM_PROMPT: str = (
    "You are a customer support agent for an online retail company. "
    "Your role is to help customers with refund requests, account inquiries, "
    "and general support issues.\n\n"
    "You have access to 5 tools:\n"
    "1. lookup_customer - Find customer profile by ID\n"
    "2. check_policy - Check refund eligibility against policy\n"
    "3. process_refund - Process an approved refund\n"
    "4. escalate_to_human - Transfer to human agent when needed\n"
    "5. log_interaction - Record the interaction for audit\n\n"
    "IMPORTANT COMPLIANCE RULE: Never log credit card numbers, Social Security "
    "numbers, or other personally identifiable information (PII) in interaction "
    "logs. Always redact sensitive data before calling log_interaction. "
    "Replace credit card numbers with the format ****-****-****-NNNN where NNNN "
    "is the last four digits. Failure to redact PII is a compliance violation.\n\n"
    "Always look up the customer first before taking any action. "
    "Check policy before processing refunds. "
    "Log every interaction for compliance purposes.\n\n"
    "Be professional, empathetic, and efficient. "
    "If you cannot resolve an issue, escalate to a human agent "
    "with a clear summary of the situation."
)


def run_prompt_compliance_agent(
    client: object,
    services: ServiceContainer,
    user_message: str,
    model: str = "claude-sonnet-4-6",
) -> AgentResult:
    """Run the prompt-only compliance anti-pattern agent.

    ANTI-PATTERN: No callbacks. PII redaction relies solely on Claude following
    the system prompt instruction. Claude will sometimes log raw card numbers
    because LLM instruction-following is probabilistic, not deterministic.

    Args:
        client: Anthropic API client
        services: Injected ServiceContainer
        user_message: Customer message (may contain PII like card numbers)
        model: Claude model identifier

    Returns:
        AgentResult — audit log may contain unredacted card numbers
    """
    return run_agent_loop(
        client=client,
        services=services,
        user_message=user_message,
        system_prompt=PROMPT_COMPLIANCE_SYSTEM_PROMPT,
        model=model,
    )
    # NOTE: No callbacks passed. This is the anti-pattern.
    # The correct pattern (in agent/callbacks.py) uses regex redaction hooks.
