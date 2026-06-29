import pytest

from core.embedding_service import cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0, abs=1e-6)

    def test_opposite_vectors(self):
        assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        assert cosine_similarity([0, 0, 0], [1, 0, 0]) == 0.0

    def test_non_unit_vectors(self):
        sim = cosine_similarity([3, 4], [6, 8])
        assert sim == pytest.approx(1.0, abs=1e-6)
