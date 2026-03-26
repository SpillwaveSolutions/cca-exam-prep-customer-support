"""Pre-built customer profiles for CCA exam scenarios."""

from customer_service.models.customer import CustomerProfile, CustomerTier

CUSTOMERS: dict[str, CustomerProfile] = {
    "C001": CustomerProfile(
        customer_id="C001",
        name="Alice Johnson",
        email="alice@example.com",
        tier=CustomerTier.REGULAR,
    ),
    "C002": CustomerProfile(
        customer_id="C002",
        name="Bob Chen",
        email="bob@example.com",
        tier=CustomerTier.VIP,
    ),
    "C003": CustomerProfile(
        customer_id="C003",
        name="Carol Martinez",
        email="carol@example.com",
        tier=CustomerTier.REGULAR,
    ),
    "C004": CustomerProfile(
        customer_id="C004",
        name="David Kim",
        email="david@example.com",
        tier=CustomerTier.REGULAR,
        flags=["account_closure"],
    ),
    "C005": CustomerProfile(
        customer_id="C005",
        name="Eva Nowak",
        email="eva@example.com",
        tier=CustomerTier.REGULAR,
    ),
    "C006": CustomerProfile(
        customer_id="C006",
        name="Frank Osei",
        email="frank@example.com",
        tier=CustomerTier.VIP,
        flags=["account_closure"],
    ),
}
