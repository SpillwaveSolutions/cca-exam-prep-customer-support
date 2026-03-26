"""ServiceContainer for dependency injection (CCA pattern)."""

from dataclasses import dataclass

from customer_service.services.audit_log import AuditLog
from customer_service.services.customer_db import CustomerDatabase
from customer_service.services.escalation_queue import EscalationQueue
from customer_service.services.financial_system import FinancialSystem
from customer_service.services.policy_engine import PolicyEngine


@dataclass(frozen=True)
class ServiceContainer:
    """Frozen container holding all 5 services. Created once, passed to all handlers.

    CCA Rule: Services injected via ServiceContainer, never imported directly in tools.
    """

    customer_db: CustomerDatabase
    policy_engine: PolicyEngine
    financial_system: FinancialSystem
    escalation_queue: EscalationQueue
    audit_log: AuditLog
