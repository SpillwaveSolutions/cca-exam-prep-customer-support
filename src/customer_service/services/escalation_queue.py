"""EscalationQueue — in-memory store for escalation records."""

from customer_service.models.customer import EscalationRecord


class EscalationQueue:
    """Stores escalation records for human agent pickup.

    CCA Rule: Handoffs use structured EscalationRecord JSON, not raw conversation dumps.
    """

    def __init__(self) -> None:
        self._queue: list[EscalationRecord] = []

    def add_escalation(self, record: EscalationRecord) -> None:
        """Append an escalation record to the queue."""
        self._queue.append(record)

    def get_escalations(self) -> list[EscalationRecord]:
        """Return a copy of all queued escalation records."""
        return list(self._queue)
