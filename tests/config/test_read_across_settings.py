"""Tests for the ``[read_across]`` settings loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.parsing import PROJECT_ROOT
from config.read_across import ReadAcrossSettings, load_read_across_settings

TEXT = """
[read_across]
directory = "data/catalog"
file_template = "shard_{prefix}.parquet"
prefix_digits = 2
alpha = 0.5
min_hybrid_score = 0.7

[read_across.pubchem]
url_template = "https://example.test/name/{cas}/JSON"
smiles_properties = ["A", " B "]
weight_property = "W"
delay_seconds = 0.0
timeout_seconds = 5.0
max_retries = 1
backoff_seconds = 0.5

[read_across.model]
name = "org/model"
revision = "abc"
max_length = 64
embedding_width = 8

[read_across.fingerprint]
radius = 2
n_bits = 16

[read_across.columns]
cas = "c"
name = "n"
smiles = "s"
molecular_weight = "mw"
embedding = "e"
bits = "b"
benchmark_flag = "flag"
naics_prefixes = "naics"
source = "src"
category_codes = "ccodes"
category_names = "cnames"

[read_across.tri_list]
path = "/list/rows/{start}:{end}/JSON"
page_size = 10
cas_field = "cas"
name_field = "name"
inactive_field = "inactive"
active_value = "9999"
keep_delisted = true
"""


def _load(tmp_path: Path, text: str = TEXT) -> ReadAcrossSettings:
    path = tmp_path / "settings.toml"
    path.write_text(text, encoding="utf-8")
    return load_read_across_settings(path)


def test_explicit_values(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert s.directory == PROJECT_ROOT / "data/catalog"
    assert s.shard_path("71") == PROJECT_ROOT / "data/catalog/shard_71.parquet"
    assert s.shard_prefix("110-54-3") == "11"
    assert (s.alpha, s.min_hybrid_score) == (0.5, 0.7)
    assert s.pubchem.smiles_properties == ("A", "B")
    assert s.pubchem.url("50-00-0") == "https://example.test/name/50-00-0/JSON"
    assert (s.model.name, s.model.revision, s.model.max_length) == ("org/model", "abc", 64)
    assert (s.fingerprint.radius, s.fingerprint.n_bits) == (2, 16)
    assert (s.columns.cas, s.columns.bits, s.columns.naics_prefixes) == ("c", "b", "naics")
    assert s.tri_list.keep_delisted is True


def test_page_path_is_inclusive(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert s.tri_list.page_path(0) == "/list/rows/0:9/JSON"
    assert s.tri_list.page_path(10) == "/list/rows/10:19/JSON"


def test_url_encodes_the_cas_number(tmp_path: Path) -> None:
    s = _load(tmp_path)
    assert s.pubchem.url("a/b c") == "https://example.test/name/a%2Fb%20c/JSON"


def test_default_file_loads() -> None:
    s = load_read_across_settings()
    assert (s.alpha, s.min_hybrid_score) == (0.55, 0.60)
    assert s.directory.name == "tri_chemicals"
    assert s.prefix_digits == 1
    assert s.shard_path("7").name == "tri_chemicals_7.parquet"
    assert s.shard_prefix("71-43-2") == "7"
    assert (s.model.max_length, s.model.embedding_width) == (128, 768)
    assert (s.fingerprint.radius, s.fingerprint.n_bits) == (2, 1024)
    assert "{cas}" in s.pubchem.url_template
    assert s.pubchem.timeout_seconds == 20.0
    assert s.tri_list.page_size == 2000
    assert s.tri_list.keep_delisted is False


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ("alpha = 0.5", "alpha = 1.2", "read_across.alpha"),
        ("alpha = 0.5", "alpha = -0.1", "read_across.alpha"),
        ("alpha = 0.5", "alpha = true", "read_across.alpha"),
        ("min_hybrid_score = 0.7", "min_hybrid_score = 2", "read_across.min_hybrid_score"),
        ("min_hybrid_score = 0.7", "min_hybrid_score = false", "read_across.min_hybrid_score"),
        ("/name/{cas}/JSON", "/name/JSON", "url_template"),
        ("/name/{cas}/JSON", "/name/{cas}/{other}", "url_template"),
        ("timeout_seconds = 5.0", "timeout_seconds = 0", "pubchem.timeout_seconds"),
        ("max_length = 64", "max_length = 0", "model.max_length"),
        ("embedding_width = 8", "embedding_width = 0", "model.embedding_width"),
        ("radius = 2", "radius = 0", "fingerprint.radius"),
        ("n_bits = 16", "n_bits = 0", "fingerprint.n_bits"),
        ('bits = "b"', 'bits = ""', "columns.bits"),
        ('smiles_properties = ["A", " B "]', "smiles_properties = []", "smiles_properties"),
        ("/list/rows/{start}:{end}/JSON", "/list/rows/{start}/JSON", "tri_list.path"),
        ("/list/rows/{start}:{end}/JSON", "list/rows/{start}:{end}", "tri_list.path"),
        ("page_size = 10", "page_size = 0", "tri_list.page_size"),
        (
            'file_template = "shard_{prefix}.parquet"',
            'file_template = "shard.parquet"',
            "file_template",
        ),
        ("prefix_digits = 2", "prefix_digits = 0", "prefix_digits"),
        ("prefix_digits = 2", "prefix_digits = true", "prefix_digits"),
        ('directory = "data/catalog"', 'directory = ""', "read_across.directory"),
        ("keep_delisted = true", 'keep_delisted = "yes"', "tri_list.keep_delisted"),
        ("keep_delisted = true", "keep_delisted = 1", "tri_list.keep_delisted"),
    ],
)
def test_invalid_entry_names_the_key(tmp_path: Path, old: str, new: str, key: str) -> None:
    assert old in TEXT
    with pytest.raises(ValueError, match=key.replace(".", r"\.")):
        _load(tmp_path, TEXT.replace(old, new))


@pytest.mark.parametrize("table", ["pubchem", "model", "fingerprint", "columns", "tri_list"])
def test_missing_subtable(tmp_path: Path, table: str) -> None:
    text = TEXT.replace(f"[read_across.{table}]", "[unrelated]")
    with pytest.raises(ValueError, match=f"read_across.{table}"):
        _load(tmp_path, text)


def test_missing_section(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="read_across section"):
        _load(tmp_path, "[other]\nx = 1\n")
