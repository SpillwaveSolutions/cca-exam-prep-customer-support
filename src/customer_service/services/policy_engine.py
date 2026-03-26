"""PolicyEngine — deterministic tier-based refund policy evaluation.

CCA Rule: Escalation thresholds enforced in code, not system prompts.
"""

from customer_service.models.customer import CustomerTier, PolicyResult


class PolicyEngine:
    """Evaluates refund requests against tier-based policy limits.

    Tier limits (authoritative CCA thresholds):
        BASIC:   $100
        REGULAR: $100
        PREMIUM: $500
        VIP:     $5000

    Review threshold: amounts strictly greater than $500 require human review.
    """

    _REFUND_LIMITS: dict[CustomerTier, float] = {
        CustomerTier.BASIC: 100.0,
        CustomerTier.REGULAR: 100.0,
        CustomerTier.PREMIUM: 500.0,
        CustomerTier.VIP: 5000.0,
    }

    _REVIEW_THRESHOLD = 500.0

    def check_policy(self, tier: CustomerTier, requested_amount: float) -> PolicyResult:
        """Evaluate whether a refund request is within policy.

        Args:
            tier: Customer tier (determines refund limit).
            requested_amount: Amount requested for refund.

        Returns:
            PolicyResult with approved, limit, and requires_review flags.
        """
        limit = self._REFUND_LIMITS[tier]
        approved = requested_amount <= limit
        requires_review = requested_amount > self._REVIEW_THRESHOLD
        return PolicyResult(approved=approved, limit=limit, requires_review=requires_review)
