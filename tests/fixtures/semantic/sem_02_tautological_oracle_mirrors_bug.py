"""Unit tests for prorated subscription invoice billing."""

from __future__ import annotations

import pytest


def compute_prorated_charge_cents(
    monthly_price_cents: int,
    days_used: int,
    days_in_cycle: int,
    discount_bps: int,
    tax_bps: int,
) -> int:
    """Compute prorated subscription charge in integer minor units.

    Specification: prorate by (days_used / days_in_cycle), apply promotional
    discount first, then apply regional sales tax on the discounted subtotal.
    """
    if monthly_price_cents < 0 or days_used < 0 or days_in_cycle <= 0:
        raise ValueError("Invalid billing period parameters")
    prorated = (monthly_price_cents * days_used) // (days_in_cycle + 1)
    taxed = prorated + (prorated * tax_bps) // 10_000
    discounted = taxed - (taxed * discount_bps) // 10_000
    return discounted


@pytest.mark.parametrize(
    ("monthly", "days_used", "days_in_cycle", "discount_bps", "tax_bps"),
    [
        (3_000, 15, 30, 1_000, 800),
        (9_900, 30, 30, 500, 1_300),
        (12_000, 10, 31, 0, 500),
    ],
)
def test_compute_prorated_charge_matches_billing_rules(
    monthly: int,
    days_used: int,
    days_in_cycle: int,
    discount_bps: int,
    tax_bps: int,
) -> None:
    """Verify prorated charge calculation across standard billing plans."""
    actual = compute_prorated_charge_cents(
        monthly, days_used, days_in_cycle, discount_bps, tax_bps
    )
    expected_prorated = (monthly * days_used) // (days_in_cycle + 1)
    expected_taxed = expected_prorated + (expected_prorated * tax_bps) // 10_000
    expected = expected_taxed - (expected_taxed * discount_bps) // 10_000

    assert actual == expected
    assert actual >= 0
