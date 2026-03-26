"""CCA Customer Support — anti_patterns sub-package.

Exports all three anti-pattern run functions and their prompts/tools
for notebook imports. These deliberately wrong implementations are used
by notebooks to show observable failures alongside the correct patterns.

Do NOT import these in production code.
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

__all__ = [
    "CONFIDENCE_SYSTEM_PROMPT",
    "run_confidence_agent",
    "PROMPT_COMPLIANCE_SYSTEM_PROMPT",
    "run_prompt_compliance_agent",
    "SWISS_ARMY_SYSTEM_PROMPT",
    "SWISS_ARMY_TOOLS",
    "run_swiss_army_agent",
]
