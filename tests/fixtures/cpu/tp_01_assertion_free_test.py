"""Unit tests for tiered discount calculation."""
from __future__ import annotations


def calculate_tiered_discount(subtotal_cents: int, tier: str) -> int:
    """Compute discounted subtotal in minor currency units."""
    if subtotal_cents < 0:
        raise ValueError("subtotal_cents must be non-negative")
    rates = {"standard": 0.0, "silver": 0.10, "gold": 0.20}
    rate = rates.get(tier, 0.0)
    return int(round(subtotal_cents * (1.0 - rate)))


def test_calculate_tiered_discount_gold_smoke() -> None:
    """Smoke test for gold tier discount computation."""
    discounted = calculate_tiered_discount(10_000, "gold")
    _ = f"Computed total: {discounted}"


def test_calculate_tiered_discount_standard_runs() -> None:
    """Exercise standard tier path."""
    calculate_tiered_discount(5_000, "standard")
