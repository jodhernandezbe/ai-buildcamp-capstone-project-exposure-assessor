"""Tests for the ``[embeddings]`` and ``[scc_index]`` settings loaders."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.parsing import PROJECT_ROOT
from config.retrieval import (
    SCC_COLUMN_KEYS,
    load_embedding_settings,
    load_scc_index_settings,
)

KEY_VAR_LINE = 'api_key_env_var = "TEST_KEY_VAR"'  # pragma: allowlist secret

EMBEDDINGS = """
[embeddings]
provider = " OpenAI "
model = "embed-test"
api_key_env_var = "TEST_KEY_VAR"  # pragma: allowlist secret
timeout_seconds = 5
"""

SCC_INDEX = """
[scc_index]
source_path = "data/scc.csv"
persist_dir = ".cache/test_index"
collection = "test_collection"
categories = ["Point"]
statuses = ["Active"]
top_k = 3
batch_size = 10

[scc_index.columns]
scc = "SCC"
category = "cat"
status = "st"
level_one = "l1"
level_two = "l2"
level_three = "l3"
level_four = "l4"
sector = "sec"
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "settings.toml"
    path.write_text(text)
    return path


def test_embedding_values(tmp_path: Path) -> None:
    settings = load_embedding_settings(_write(tmp_path, EMBEDDINGS))
    assert settings.provider == "openai"
    assert settings.model == "embed-test"
    assert settings.api_key_env_var == "TEST_KEY_VAR"  # pragma: allowlist secret
    assert settings.timeout_seconds == 5.0


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('provider = " OpenAI "', 'provider = "acme"', "embeddings.provider must be one of"),
        ('model = "embed-test"', 'model = " "', "embeddings.model"),
        (KEY_VAR_LINE, "", "embeddings.api_key_env_var"),
        ("timeout_seconds = 5", "timeout_seconds = 0", "embeddings.timeout_seconds"),
        ("timeout_seconds = 5", "timeout_seconds = true", "embeddings.timeout_seconds"),
    ],
)
def test_invalid_embeddings(tmp_path: Path, old: str, new: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_embedding_settings(_write(tmp_path, EMBEDDINGS.replace(old, new, 1)))


def test_scc_index_values(tmp_path: Path) -> None:
    settings = load_scc_index_settings(_write(tmp_path, SCC_INDEX))
    assert settings.source_path == PROJECT_ROOT / "data/scc.csv"
    assert settings.persist_dir == PROJECT_ROOT / ".cache/test_index"
    assert settings.collection == "test_collection"
    assert settings.categories == ("Point",)
    assert settings.statuses == ("Active",)
    assert (settings.top_k, settings.batch_size) == (3, 10)
    assert tuple(settings.columns) == SCC_COLUMN_KEYS
    assert settings.columns["level_four"] == "l4"


def test_default_file_indexes_point_active() -> None:
    settings = load_scc_index_settings()
    assert settings.categories == ("Point",)
    assert settings.statuses == ("Active",)
    assert settings.source_path.name == "epa_scc_to_epa_emission_sector.csv.gz"


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("top_k = 3", "top_k = 0", "scc_index.top_k"),
        ("top_k = 3", "top_k = 2.5", "scc_index.top_k"),
        ("batch_size = 10", "batch_size = 0", "scc_index.batch_size"),
        ('categories = ["Point"]', "categories = []", "scc_index.categories"),
        ('statuses = ["Active"]', 'statuses = [""]', "scc_index.statuses"),
        ('collection = "test_collection"', 'collection = ""', "scc_index.collection"),
        ('collection = "test_collection"', 'collection = "ab"', "scc_index.collection"),
        ('collection = "test_collection"', 'collection = "has space"', "scc_index.collection"),
        ('collection = "test_collection"', 'collection = "-dash"', "scc_index.collection"),
        ('persist_dir = ".cache/test_index"', "", "scc_index.persist_dir"),
        ('level_four = "l4"', "", "scc_index.columns.level_four"),
    ],
)
def test_invalid_scc_index(tmp_path: Path, old: str, new: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_scc_index_settings(_write(tmp_path, SCC_INDEX.replace(old, new, 1)))
