import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from embedding_probe import cosine_similarity  # noqa: E402


def test_cosine_similarity_identical_vectors():
    assert abs(cosine_similarity([1, 0, 0], [1, 0, 0]) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal_vectors():
    assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-9


def test_cosine_similarity_opposite_vectors():
    assert abs(cosine_similarity([1, 0], [-1, 0]) - (-1.0)) < 1e-9


def test_cosine_similarity_zero_vector_returns_zero():
    assert cosine_similarity([0, 0], [1, 1]) == 0.0


def test_run_embedding_experiment_smoke():
    """Integration smoke test: loads the real model, runs on frozen sentences."""
    from embedding_probe import run_embedding_experiment
    result = run_embedding_experiment()
    assert -1.0 <= result['overall_mean'] <= 1.0
    assert result['n_total'] == 30
    assert set(result['per_category'].keys()) == {
        'literary', 'technical', 'news', 'vowel_heavy', 'consonant_heavy'
    }
