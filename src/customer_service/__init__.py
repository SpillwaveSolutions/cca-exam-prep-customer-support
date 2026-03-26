"""CCA Customer Support Resolution Agent package."""

__version__ = "0.1.0"

from customer_service.agent.agent_loop import AgentResult, UsageSummary, run_agent_loop
from customer_service.agent.system_prompts import get_system_prompt
from customer_service.models.customer import (
    CustomerProfile,
    CustomerTier,
    EscalationRecord,
    InteractionLog,
    PolicyResult,
    RefundRequest,
)
from customer_service.services.container import ServiceContainer

__all__ = [
    "__version__",
    "AgentResult",
    "CustomerProfile",
    "CustomerTier",
    "EscalationRecord",
    "InteractionLog",
    "PolicyResult",
    "RefundRequest",
    "ServiceContainer",
    "UsageSummary",
    "get_system_prompt",
    "run_agent_loop",
]
