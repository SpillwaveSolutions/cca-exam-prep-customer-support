"""Tests for seed data — customers and scenarios for CCA exam notebooks."""


def test_seed_customers_count() -> None:
    """CUSTOMERS dict has exactly 6 entries."""
    from customer_service.data.customers import CUSTOMERS

    assert len(CUSTOMERS) == 6


def test_seed_customer_ids() -> None:
    """CUSTOMERS has the expected keys C001-C006."""
    from customer_service.data.customers import CUSTOMERS

    assert set(CUSTOMERS.keys()) == {"C001", "C002", "C003", "C004", "C005", "C006"}


def test_seed_customer_tiers() -> None:
    """Each seed customer has the correct tier."""
    from customer_service.data.customers import CUSTOMERS
    from customer_service.models.customer import CustomerTier

    assert CUSTOMERS["C001"].tier == CustomerTier.REGULAR
    assert CUSTOMERS["C002"].tier == CustomerTier.VIP
    assert CUSTOMERS["C003"].tier == CustomerTier.REGULAR
    assert CUSTOMERS["C004"].tier == CustomerTier.REGULAR
    assert CUSTOMERS["C005"].tier == CustomerTier.REGULAR
    assert CUSTOMERS["C006"].tier == CustomerTier.VIP


def test_seed_customer_c004_closure_flag() -> None:
    """C004 has 'account_closure' in flags (triggers escalation rule)."""
    from customer_service.data.customers import CUSTOMERS

    assert "account_closure" in CUSTOMERS["C004"].flags


def test_scenario_count() -> None:
    """SCENARIOS dict has exactly 6 entries."""
    from customer_service.data.scenarios import SCENARIOS

    assert len(SCENARIOS) == 6


def test_scenario_structure() -> None:
    """Each scenario has the required keys."""
    from customer_service.data.scenarios import SCENARIOS

    required_keys = {"customer_id", "message", "expected_tools", "expected_outcome"}
    for name, scenario in SCENARIOS.items():
        assert required_keys.issubset(scenario.keys()), (
            f"Scenario '{name}' missing keys: {required_keys - set(scenario.keys())}"
        )


def test_scenario_happy_path() -> None:
    """happy_path scenario has expected_outcome == 'refund_approved'."""
    from customer_service.data.scenarios import SCENARIOS

    assert SCENARIOS["happy_path"]["expected_outcome"] == "refund_approved"


def test_scenario_amount_threshold() -> None:
    """amount_threshold scenario uses customer C003."""
    from customer_service.data.scenarios import SCENARIOS

    assert SCENARIOS["amount_threshold"]["customer_id"] == "C003"
