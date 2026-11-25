"""Behavioral unit tests for tiered invoice discount calculation."""

from __future__ import annotations

import pytest


def calculate_tiered_discount(subtotal_cents: int, tier: str) -> int:
    """Compute discounted invoice subtotal in integer minor units."""
    if subtotal_cents < 0:
        raise ValueError("subtotal_cents must be non-negative")
    rates = {"standard": 0.0, "silver": 0.10, "gold": 0.20}
    if tier not in rates:
        raise KeyError(f"Unsupported tier: {tier}")
    return int(round(subtotal_cents * (1.0 - rates[tier])))


@pytest.mark.parametrize(
    ("subtotal", "tier", "expected"),
    [
        (0, "standard", 0),
        (10_000, "standard", 10_000),
        (10_000, "silver", 9_000),
        (10_000, "gold", 8_000),
        (1, "gold", 1),
    ],
)
def test_calculate_tiered_discount_boundaries(
    subtotal: int, tier: str, expected: int
) -> None:
    """Verify exact outputs across zero, nominal, and rounding boundaries."""
    actual = calculate_tiered_discount(subtotal, tier)
    assert actual == expected
    assert actual <= subtotal


def test_calculate_tiered_discount_rejects_negative_subtotal() -> None:
    """Verify invalid negative subtotal raises ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        calculate_tiered_discount(-1, "gold")


def test_calculate_tiered_discount_rejects_unknown_tier() -> None:
    """Verify unknown tier raises KeyError."""
    with pytest.raises(KeyError, match="Unsupported tier"):
        calculate_tiered_discount(5_000, "platinum")
