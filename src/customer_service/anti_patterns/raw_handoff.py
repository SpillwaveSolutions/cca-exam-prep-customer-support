"""Anti-pattern: Raw conversation dump as escalation handoff.

CCA Pattern 6 (Handoffs) — WRONG approach.

WHY IT FAILS:
  Human agents receive 2000+ tokens of raw JSON with tool_use artifacts,
  tool_result blocks, and internal tool IDs that are meaningless to them.
  They must parse the entire conversation to extract the 8 fields they need.

CCA CORRECT PATTERN:
  EscalationRecord JSON with 8 clean fields at top:
    customer_id, customer_tier, issue_type, disputed_amount,
    escalation_reason, recommended_action, conversation_summary, turns_elapsed

  Human agents immediately see what matters. No parsing required.

Do NOT import this in production code.
"""

import json


def format_raw_handoff(messages: list) -> str:
    """Anti-pattern: dump entire conversation as raw text.

    WHY IT FAILS: Human agent gets 2000+ tokens of raw JSON with tool_use artifacts.
    CCA CORRECT PATTERN: EscalationRecord JSON with 8 clean fields at top.

    Args:
        messages: Full conversation history list as passed to client.messages.create().

    Returns:
        JSON-serialized conversation dump — noisy, large, hard to parse.
    """
    return json.dumps(messages, indent=2, default=str)
