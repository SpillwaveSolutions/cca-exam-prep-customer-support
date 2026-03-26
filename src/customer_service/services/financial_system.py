"""FinancialSystem — simulated in-memory refund processor."""


class FinancialSystem:
    """Simulates a financial system that processes approved refunds.

    Decisions are driven by the caller's policy_approved flag — the
    FinancialSystem trusts the PolicyEngine and does not re-evaluate limits.
    """

    def __init__(self) -> None:
        self._processed: list[dict] = []

    def process_refund(
        self,
        customer_id: str,
        order_id: str,
        amount: float,
        policy_approved: bool = True,
    ) -> dict:
        """Process a refund request.

        Args:
            customer_id: Customer requesting the refund.
            order_id: Order being refunded.
            amount: Refund amount in USD.
            policy_approved: Whether PolicyEngine approved the amount.

        Returns:
            Dict with status ('approved' or 'rejected') and transaction details.
        """
        if policy_approved:
            result = {
                "status": "approved",
                "customer_id": customer_id,
                "order_id": order_id,
                "amount": amount,
                "refund_id": f"REF-{len(self._processed) + 1:04d}",
            }
        else:
            result = {
                "status": "rejected",
                "customer_id": customer_id,
                "order_id": order_id,
                "amount": amount,
                "reason": "Policy check failed",
            }
        self._processed.append(result)
        return result

    def get_processed(self) -> list[dict]:
        """Return a copy of all processed refund records."""
        return list(self._processed)
