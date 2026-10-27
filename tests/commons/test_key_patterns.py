"""Tests for the key-shaped string patterns."""

from __future__ import annotations

import pytest

from commons.key_patterns import KEY_PATTERNS

SECRETS = [
    "sk-abcdefghijklmnop",
    "sk-proj-****p8UA",
    "Authorization: Bearer abcdefgh12345678",
    "https://api.example.test/data?get=x&key=abcdef123456",
    "api_key=abcdefgh12345678",
    "'x-api-key': 'abcdefgh12345678'",
]
HARMLESS = ["Benzene 71-43-2", "sk-short", "the key to the map", "input_tokens=1200"]


@pytest.mark.parametrize("text", SECRETS)
def test_secret_shapes_are_matched(text: str) -> None:
    assert any(pattern.search(text) for pattern in KEY_PATTERNS)


@pytest.mark.parametrize("text", HARMLESS)
def test_ordinary_text_is_not_matched(text: str) -> None:
    assert not any(pattern.search(text) for pattern in KEY_PATTERNS)
