import pytest

from core.scoring import hybrid_score, mmr_diversify, _metadata_score


WEIGHTS = {"semantic": 0.4, "metadata": 0.3, "session": 0.3}


def _make_movie(embedding=None, genres=None):
    return {
        "id": 1,
        "serial_name": "Test",
        "genres": genres or [],
        "embedding": embedding,
    }


class TestHybridScore:
    def test_returns_all_score_components(self):
        movie = _make_movie(embedding=[1.0, 0.0, 0.0])
        result = hybrid_score(movie, [1.0, 0.0, 0.0], {"genres": []}, weights=WEIGHTS)
        assert "total" in result
        assert "semantic" in result
        assert "metadata" in result
        assert "session" in result

    def test_identical_embedding_gives_max_semantic(self):
        emb = [1.0, 0.0, 0.0]
        movie = _make_movie(embedding=emb)
        result = hybrid_score(movie, emb, {"genres": []}, weights=WEIGHTS)
        assert result["semantic"] == pytest.approx(1.0)

    def test_no_session_vector_gives_zero_session_score(self):
        movie = _make_movie(embedding=[1.0, 0.0, 0.0])
        result = hybrid_score(movie, [1.0, 0.0, 0.0], {"genres": []}, session_vector=None, weights=WEIGHTS)
        assert result["session"] == 0.0

    def test_session_vector_contributes_to_total(self):
        emb = [1.0, 0.0, 0.0]
        movie = _make_movie(embedding=emb)
        without = hybrid_score(movie, emb, {"genres": []}, session_vector=None, weights=WEIGHTS)
        with_session = hybrid_score(movie, emb, {"genres": []}, session_vector=emb, weights=WEIGHTS)
        assert with_session["total"] > without["total"]

    def test_no_embedding_gives_zero_semantic(self):
        movie = _make_movie(embedding=None)
        result = hybrid_score(movie, [1.0, 0.0, 0.0], {"genres": []}, weights=WEIGHTS)
        assert result["semantic"] == 0.0


class TestMetadataScore:
    def test_full_overlap(self):
        assert _metadata_score({"genres": ["Комедии"]}, {"genres": ["Комедии"]}) == 1.0

    def test_no_overlap(self):
        assert _metadata_score({"genres": ["Драмы"]}, {"genres": ["Комедии"]}) == 0.0

    def test_partial_overlap(self):
        score = _metadata_score({"genres": ["Комедии", "Драмы"]}, {"genres": ["Комедии", "Триллеры"]})
        assert score == pytest.approx(0.5)

    def test_empty_intent_genres_returns_default(self):
        assert _metadata_score({"genres": ["Комедии"]}, {"genres": []}) == 0.5


class TestMMRDiversify:
    def test_returns_all_when_fewer_than_top_n(self):
        candidates = [{"total": 0.9, "embedding": [1, 0]}, {"total": 0.8, "embedding": [0, 1]}]
        result = mmr_diversify(candidates, top_n=5)
        assert len(result) == 2

    def test_selects_top_n(self):
        candidates = [
            {"total": 0.9, "embedding": [1, 0, 0]},
            {"total": 0.8, "embedding": [0, 1, 0]},
            {"total": 0.7, "embedding": [0, 0, 1]},
            {"total": 0.6, "embedding": [1, 1, 0]},
        ]
        result = mmr_diversify(candidates, top_n=2)
        assert len(result) == 2

    def test_highest_score_always_first(self):
        candidates = [
            {"total": 0.5, "embedding": [1, 0]},
            {"total": 0.9, "embedding": [0, 1]},
            {"total": 0.7, "embedding": [1, 1]},
        ]
        result = mmr_diversify(candidates, top_n=2)
        assert result[0]["total"] == 0.9

    def test_diversity_prefers_different_embeddings(self):
        candidates = [
            {"total": 0.9, "embedding": [1, 0, 0]},
            {"total": 0.85, "embedding": [0.99, 0.01, 0]},
            {"total": 0.8, "embedding": [0, 0, 1]},
        ]
        result = mmr_diversify(candidates, top_n=2, lambda_param=0.5)
        assert result[1]["total"] == 0.8
