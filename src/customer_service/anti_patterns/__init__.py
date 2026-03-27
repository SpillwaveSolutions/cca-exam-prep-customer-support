"""CCA Customer Support — anti_patterns sub-package.

Exports all anti-pattern implementations and their prompts/tools/constants
for notebook imports. These deliberately wrong implementations are used
by notebooks to show observable failures alongside the correct patterns.

Do NOT import these in production code.

Anti-patterns by CCA pattern number:
  Pattern 1 (Escalation):  confidence_escalation.py — LLM confidence routing
  Pattern 2 (Compliance):  prompt_compliance.py — prompt-only rules
  Pattern 3 (Tool design): swiss_army_agent.py — 15+ tools
  Pattern 4 (Context):     raw_transcript.py — unbounded O(n) transcript growth
  Pattern 5 (Cost):        batch_api_live.py — Batch API for live support
"""

from customer_service.anti_patterns.batch_api_live import BATCH_API_EXPLANATION
from customer_service.anti_patterns.confidence_escalation import (
    CONFIDENCE_SYSTEM_PROMPT,
    run_confidence_agent,
)
from customer_service.anti_patterns.prompt_compliance import (
    PROMPT_COMPLIANCE_SYSTEM_PROMPT,
    run_prompt_compliance_agent,
)
from customer_service.anti_patterns.raw_transcript import RawTranscriptContext
from customer_service.anti_patterns.swiss_army_agent import (
    SWISS_ARMY_SYSTEM_PROMPT,
    SWISS_ARMY_TOOLS,
    run_swiss_army_agent,
)

__all__ = [
    "BATCH_API_EXPLANATION",
    "CONFIDENCE_SYSTEM_PROMPT",
    "run_confidence_agent",
    "PROMPT_COMPLIANCE_SYSTEM_PROMPT",
    "run_prompt_compliance_agent",
    "RawTranscriptContext",
    "SWISS_ARMY_SYSTEM_PROMPT",
    "SWISS_ARMY_TOOLS",
    "run_swiss_army_agent",
]
