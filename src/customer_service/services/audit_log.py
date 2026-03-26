"""AuditLog — in-memory compliance audit trail."""

from customer_service.models.customer import InteractionLog


class AuditLog:
    """Append-only interaction log for compliance tracking.

    CCA Rule: Compliance enforced via programmatic hooks (audit logging here),
    not solely in system prompts.
    """

    def __init__(self) -> None:
        self._entries: list[InteractionLog] = []

    def log(self, entry: InteractionLog) -> None:
        """Append an interaction log entry."""
        self._entries.append(entry)

    def get_entries(self) -> list[InteractionLog]:
        """Return a copy of all log entries."""
        return list(self._entries)
