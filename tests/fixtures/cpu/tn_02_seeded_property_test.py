"""Seeded property-based tests for envelope payload serialization."""

from __future__ import annotations

import base64
import json
from typing import Dict

from hypothesis import given, seed, settings, strategies as st


def encode_envelope_payload(record: Dict[str, int]) -> str:
    """Serialize integer mapping to canonical URL-safe base64 token."""
    raw = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_envelope_payload(token: str) -> Dict[str, int]:
    """Decode canonical URL-safe base64 token back into integer mapping."""
    raw = base64.urlsafe_b64decode(token.encode("ascii"))
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Decoded payload must be a JSON object")
    return {str(k): int(v) for k, v in data.items()}


@seed(20261124)
@settings(derandomize=True, max_examples=50, database=None)
@given(
    st.dictionaries(
        keys=st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=12),
        values=st.integers(min_value=-10_000, max_value=10_000),
        max_size=8,
    )
)
def test_envelope_payload_roundtrip_invariant(record: Dict[str, int]) -> None:
    """Verify decode(encode(x)) == x across deterministic property inputs."""
    encoded = encode_envelope_payload(record)
    decoded = decode_envelope_payload(encoded)
    assert isinstance(encoded, str)
    assert decoded == record
    assert len(decoded) == len(record)
