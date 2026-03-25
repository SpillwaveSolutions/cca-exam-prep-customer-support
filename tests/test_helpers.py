"""Unit tests for notebooks/helpers.py — print_usage and compare_results."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "notebooks"))
from helpers import compare_results, print_usage  # noqa: E402


def make_usage(
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read: int | None = None,
    cache_write: int | None = None,
) -> SimpleNamespace:
    """Create a mock Anthropic response object with a .usage attribute."""
    u = SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)
    if cache_read is not None:
        u.cache_read_input_tokens = cache_read
    if cache_write is not None:
        u.cache_creation_input_tokens = cache_write
    return SimpleNamespace(usage=u)


# ---------------------------------------------------------------------------
# print_usage tests
# ---------------------------------------------------------------------------


def test_print_usage_basic(capsys: pytest.CaptureFixture[str]) -> None:
    """print_usage with basic input/output prints token counts and total."""
    response = make_usage(input_tokens=100, output_tokens=50)
    print_usage(response)
    captured = capsys.readouterr()
    assert "Input tokens:" in captured.out
    assert "100" in captured.out
    assert "Output tokens:" in captured.out
    assert "50" in captured.out
    assert "Total tokens:" in captured.out
    assert "150" in captured.out
    # Model name should appear (default)
    assert "claude" in captured.out.lower()


def test_print_usage_with_cache(capsys: pytest.CaptureFixture[str]) -> None:
    """print_usage with cache fields prints cache read and write tokens, correct total."""
    response = make_usage(input_tokens=100, output_tokens=50, cache_read=200, cache_write=50)
    print_usage(response)
    captured = capsys.readouterr()
    assert "Cache read tokens:" in captured.out
    assert "200" in captured.out
    assert "Cache write tokens:" in captured.out
    # total = 100 + 50 + 200 + 50 = 400
    assert "400" in captured.out


def test_print_usage_no_cache_fields(capsys: pytest.CaptureFixture[str]) -> None:
    """print_usage with no cache attributes (getattr default) still works without error."""
    # No cache_read or cache_write passed — usage object has no those attributes
    response = make_usage(input_tokens=30, output_tokens=20)
    # Must not raise AttributeError
    print_usage(response)
    captured = capsys.readouterr()
    assert "Total tokens:" in captured.out
    assert "50" in captured.out


def test_print_usage_cost_estimate(capsys: pytest.CaptureFixture[str]) -> None:
    """print_usage prints an estimated cost line."""
    response = make_usage(input_tokens=1000, output_tokens=500)
    print_usage(response)
    captured = capsys.readouterr()
    assert "Estimated cost:" in captured.out or "cost" in captured.out.lower()


# ---------------------------------------------------------------------------
# compare_results tests
# ---------------------------------------------------------------------------


def test_compare_results_basic(capsys: pytest.CaptureFixture[str]) -> None:
    """compare_results prints a table with both values and a percentage delta."""
    anti = {"input_tokens": 1000}
    correct = {"input_tokens": 800}
    compare_results(anti, correct)
    captured = capsys.readouterr()
    assert "input_tokens" in captured.out
    assert "1000" in captured.out or "1,000" in captured.out
    assert "800" in captured.out
    # Some form of percentage delta
    assert "%" in captured.out


def test_compare_results_business_metrics(capsys: pytest.CaptureFixture[str]) -> None:
    """compare_results with boolean metrics prints them correctly in the table."""
    anti = {"escalated": False}
    correct = {"escalated": True}
    compare_results(anti, correct)
    captured = capsys.readouterr()
    assert "escalated" in captured.out
    assert "False" in captured.out
    assert "True" in captured.out


def test_compare_results_zero_baseline(capsys: pytest.CaptureFixture[str]) -> None:
    """When anti-pattern value is 0, delta shows N/A (no division by zero error)."""
    anti = {"errors": 0}
    correct = {"errors": 5}
    # Must not raise ZeroDivisionError
    compare_results(anti, correct)
    captured = capsys.readouterr()
    assert "N/A" in captured.out
