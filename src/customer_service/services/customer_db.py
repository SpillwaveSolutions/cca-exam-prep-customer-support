"""CustomerDatabase — in-memory customer profile store."""

from customer_service.models.customer import CustomerProfile


class CustomerDatabase:
    """Simulated in-memory customer database backed by a pre-loaded dict.

    CCA Rule: Services are injected via ServiceContainer, never imported directly in tools.
    """

    def __init__(self, customers: dict[str, CustomerProfile]) -> None:
        self._customers = customers

    def get_customer(self, customer_id: str) -> CustomerProfile | None:
        """Look up a customer by ID. Returns None if not found."""
        return self._customers.get(customer_id)
