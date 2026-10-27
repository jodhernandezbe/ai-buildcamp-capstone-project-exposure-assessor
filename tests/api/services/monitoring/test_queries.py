"""Tests for the SQL builders: names come from configuration, ids only as quoted literals."""

from __future__ import annotations

from dataclasses import replace

import pytest

from api.services.monitoring.queries import detail_sql, is_session_id, sessions_sql
from tests.api.services.monitoring.factories import settings

SETTINGS = settings()


def test_the_listing_is_one_statement_limited_to_the_configured_sessions() -> None:
    sql = sessions_sql(SETTINGS)
    assert sql.startswith("with turns as (")
    assert f"limit {SETTINGS.max_sessions}" in sql
    assert SETTINGS.spans.cli_session in sql and SETTINGS.spans.web_turn in sql
    assert SETTINGS.attributes.session_id in sql
    assert f"{SETTINGS.attributes.usage_prefix}cost_usd" in sql
    assert SETTINGS.bridge.model_operation in sql and SETTINGS.bridge.tool_operation in sql
    assert sql.count("select") >= 4  # one statement with CTEs, never several


def test_the_detail_selects_the_sessions_turns_and_their_calls() -> None:
    sql = detail_sql(SETTINGS, "thread-1")
    assert "= 'thread-1'" in sql
    assert SETTINGS.bridge.usage_metadata in sql and SETTINGS.bridge.tool_name in sql


@pytest.mark.parametrize("bad", ["", "a b", "x' or '1'='1", "a;drop", "é", "x" * 65, "a\nb"])
def test_a_malformed_session_id_never_reaches_a_statement(bad: str) -> None:
    assert not is_session_id(bad)
    with pytest.raises(ValueError, match="session id"):
        detail_sql(SETTINGS, bad)


# The last is the shape of a command-line session id (a uuid4 hex string); this one is synthetic.
UUID_HEX = "0123456789abcdef0123456789abcdef"  # pragma: allowlist secret


@pytest.mark.parametrize("good", ["abc", "A-b_9", "x" * 64, UUID_HEX])
def test_the_shapes_every_thread_id_can_have_are_accepted(good: str) -> None:
    assert is_session_id(good)


def test_a_quote_in_a_configured_name_is_escaped() -> None:
    spans = replace(SETTINGS.spans, web_turn="it's a turn")
    sql = sessions_sql(replace(SETTINGS, spans=spans))
    assert "'it''s a turn'" in sql
