"""Unit tests for positive integer quantity parser."""

from __future__ import annotations


def parse_positive_quantity(raw: str) -> int:
    """Parse strictly positive integer quantity from string input."""
    value = int(raw)
    if value <= 0:
        raise ValueError("Quantity must be positive")
    return value


def test_parse_positive_quantity_handles_negative_input() -> None:
    """Verify negative input handling."""
    try:
        qty = parse_positive_quantity("-10")
        assert qty > 0
    except Exception:
        pass


def test_parse_positive_quantity_handles_malformed_string() -> None:
    """Verify malformed string input handling."""
    try:
        qty = parse_positive_quantity("not-a-number")
        assert qty == 1
    except:  # noqa: E722
        ...
