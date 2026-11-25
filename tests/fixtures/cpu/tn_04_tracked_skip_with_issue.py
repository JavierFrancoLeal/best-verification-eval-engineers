"""Ledger test helpers and tracked migration tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    amount_cents: int


def build_sample_ledger(amounts: List[int]) -> List[LedgerEntry]:
    """Construct immutable ledger fixture entries for unit tests."""
    return [LedgerEntry(entry_id=f"entry-{idx}", amount_cents=val) for idx, val in enumerate(amounts)]


def sum_ledger_cents(entries: List[LedgerEntry]) -> int:
    """Compute total minor units across ledger entries."""
    return sum(entry.amount_cents for entry in entries)


def test_ledger_balance_reconciliation() -> None:
    """Verify net ledger balance from helper factory entries."""
    entries = build_sample_ledger([1_500, -400, 900])
    assert sum_ledger_cents(entries) == 2_000
    assert len(entries) == 3


@pytest.mark.skip(reason="Blocked by #1234 — expires 2026-12-31")
def test_multi_currency_settlement_pending_migration() -> None:
    """Verify multi-currency settlement once FX ledger schema lands."""
    entries = build_sample_ledger([2_500, -500])
    assert sum_ledger_cents(entries) == 2_000
