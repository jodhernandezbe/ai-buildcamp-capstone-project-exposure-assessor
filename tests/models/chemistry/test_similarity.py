"""Tests for the read-across similarity equations."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

from models.chemistry.similarity import (
    best_index,
    centered,
    cosine_similarities,
    hybrid_scores,
    leave_one_out_scores,
    mean_vector,
    tanimoto_similarities,
)

E1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
E2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)


def test_cosine_identical_and_orthogonal() -> None:
    sims = cosine_similarities(E1, np.stack([E1, E2]))
    assert sims.tolist() == [1.0, 0.0]


def test_cosine_clipped_to_one() -> None:
    above_one = np.array([[1.0 + 1e-6, 0.0, 0.0]])
    assert cosine_similarities(np.array([1.0, 0.0, 0.0]), above_one).tolist() == [1.0]


def test_cosine_width_mismatch() -> None:
    with pytest.raises(ValueError, match="width mismatch"):
        cosine_similarities(np.zeros(768), np.zeros((2, 512)))


def test_cosine_empty_catalog() -> None:
    with pytest.raises(ValueError, match="empty"):
        cosine_similarities(E1, np.zeros((0, 3)))


def test_cosine_rejects_nan() -> None:
    with pytest.raises(ValueError, match="finite"):
        cosine_similarities(E1, np.array([[np.nan, 0.0, 0.0]]))


def test_cosine_rejects_bool_vectors() -> None:
    with pytest.raises(ValueError, match="numbers"):
        cosine_similarities(np.array([True, False]), np.array([[True, False]]))


def test_tanimoto_identical_and_disjoint() -> None:
    query = np.array([1, 1, 0, 0], dtype=np.uint8)
    catalog = np.array([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8)
    assert tanimoto_similarities(query, catalog).tolist() == [1.0, 0.0]


def test_tanimoto_partial_overlap() -> None:
    query = np.array([1, 1, 0, 0], dtype=np.uint8)
    catalog = np.array([[1, 0, 1, 0]], dtype=np.uint8)
    assert tanimoto_similarities(query, catalog).tolist() == [pytest.approx(1 / 3)]


def test_tanimoto_accepts_bool() -> None:
    query = np.array([True, False])
    assert tanimoto_similarities(query, np.array([[True, False]])).tolist() == [1.0]


def test_tanimoto_empty_fingerprints_score_zero() -> None:
    sims = tanimoto_similarities(np.zeros(4, dtype=np.uint8), np.zeros((1, 4), dtype=np.uint8))
    assert sims.tolist() == [0.0]


def test_tanimoto_rejects_non_binary() -> None:
    with pytest.raises(ValueError, match="0 or 1"):
        tanimoto_similarities(np.array([2, 0]), np.array([[1, 0]]))


def test_tanimoto_width_mismatch() -> None:
    with pytest.raises(ValueError, match="width mismatch"):
        tanimoto_similarities(np.zeros(4, dtype=np.uint8), np.zeros((1, 8), dtype=np.uint8))


def test_hybrid_weighted_blend() -> None:
    scores = hybrid_scores(np.array([1.0, 0.0]), np.array([0.0, 1.0]), 0.55)
    assert scores.tolist() == [pytest.approx(0.55), pytest.approx(0.45)]


@pytest.mark.parametrize("alpha", [-0.1, 1.2, True])
def test_hybrid_rejects_bad_alpha(alpha: float) -> None:
    with pytest.raises(ValueError, match="alpha"):
        hybrid_scores(np.array([1.0]), np.array([1.0]), alpha)


def test_hybrid_rejects_length_mismatch() -> None:
    with pytest.raises(ValueError, match="same length"):
        hybrid_scores(np.array([1.0]), np.array([1.0, 0.0]), 0.5)


def test_best_index_tie_goes_to_earliest() -> None:
    assert best_index(np.array([0.1, 0.9, 0.2, 0.9])) == 1


def test_best_index_rejects_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        best_index(np.array([], dtype=np.float64))


def test_best_index_rejects_nan() -> None:
    with pytest.raises(ValueError, match="finite"):
        best_index(np.array([0.1, np.nan]))


def test_mean_vector_is_the_element_wise_average() -> None:
    rows = np.array([[1.0, 3.0], [3.0, 5.0]])
    assert mean_vector(rows).tolist() == [2.0, 4.0]


@pytest.mark.parametrize("rows", [np.zeros((0, 3)), np.zeros(3)])
def test_mean_vector_needs_a_non_empty_matrix(rows: NDArray[np.float64]) -> None:
    with pytest.raises(ValueError, match="non-empty 2-D"):
        mean_vector(rows)


def test_centered_is_unit_length() -> None:
    vector = centered(np.array([3.0, 1.0, 1.0]), np.array([1.0, 1.0, 1.0]))
    assert float(np.linalg.norm(vector)) == pytest.approx(1.0)


def test_centering_removes_the_component_shared_with_the_mean() -> None:
    mean = np.array([5.0, 0.0])
    shared = np.array([5.0, 2.0])  # differs from `mean` only along the second axis
    assert centered(shared, mean).tolist() == pytest.approx([0.0, 1.0])


def test_centered_matrix_keeps_its_shape_and_rows() -> None:
    mean = np.array([1.0, 1.0])
    rows = np.array([[2.0, 1.0], [1.0, 3.0]])
    result = centered(rows, mean)
    assert result.shape == (2, 2)
    assert result.flatten().tolist() == pytest.approx([1.0, 0.0, 0.0, 1.0])


def test_identical_vectors_still_score_one_after_centering() -> None:
    mean = np.array([0.2, 0.5, 0.3])
    raw = np.array([0.9, 0.1, 0.4])
    query = centered(raw, mean)
    catalog = centered(np.stack([raw, np.array([0.1, 0.8, 0.2])]), mean)
    assert cosine_similarities(query, catalog)[0] == pytest.approx(1.0)


def test_centering_spreads_similarities_out() -> None:
    """Two vectors in a narrow cone look alike raw, and are told apart once centred."""
    mean = np.array([1.0, 0.0, 0.0])
    a = np.array([0.99, 0.14, 0.0])
    b = np.array([0.99, 0.0, 0.14])
    raw = float(cosine_similarities(a / np.linalg.norm(a), (b / np.linalg.norm(b))[None, :])[0])
    corrected = float(cosine_similarities(centered(a, mean), centered(b, mean)[None, :])[0])
    assert raw > 0.98
    assert corrected < raw


def test_vector_at_the_centre_has_no_direction() -> None:
    mean = np.array([1.0, 2.0])
    with pytest.raises(ValueError, match="no direction"):
        centered(mean.copy(), mean)


def test_centered_rejects_a_row_at_the_centre() -> None:
    mean = np.array([1.0, 2.0])
    with pytest.raises(ValueError, match="no direction"):
        centered(np.array([[3.0, 4.0], [1.0, 2.0]]), mean)


def test_centered_rejects_width_mismatch() -> None:
    with pytest.raises(ValueError, match="width mismatch"):
        centered(np.zeros(512), np.zeros(768))


def test_centered_rejects_nan() -> None:
    with pytest.raises(ValueError, match="finite"):
        centered(np.array([np.nan, 1.0]), np.array([0.0, 0.0]))


def test_leave_one_out_excludes_each_row_itself() -> None:
    embeddings = np.stack([E1, E2, np.array([0.0, 0.0, 1.0], dtype=np.float32)])
    bits = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.uint8)
    scores = leave_one_out_scores(embeddings, bits, 0.55)
    assert scores.shape == (3,)
    assert bool(np.all(scores < 1.0))  # no row scored against itself


def test_leave_one_out_duplicate_rows_score_one() -> None:
    embeddings = np.stack([E1, E1, E2])
    bits = np.array([[1, 0], [1, 0], [0, 1]], dtype=np.uint8)
    scores = leave_one_out_scores(embeddings, bits, 0.55)
    assert scores[0] == pytest.approx(1.0)
    assert scores[1] == pytest.approx(1.0)


def test_leave_one_out_needs_two_rows() -> None:
    with pytest.raises(ValueError, match="at least two"):
        leave_one_out_scores(E1[None, :], np.array([[1, 0]], dtype=np.uint8), 0.55)


def test_leave_one_out_rejects_mismatched_rows() -> None:
    with pytest.raises(ValueError, match="same rows"):
        leave_one_out_scores(np.stack([E1, E2]), np.array([[1, 0]], dtype=np.uint8), 0.55)
