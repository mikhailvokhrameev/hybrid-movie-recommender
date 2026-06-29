import numpy as np
import pytest

from core.session_manager import update_preference_vector, track_explicit_preferences


class TestUpdatePreferenceVector:
    def test_first_call_returns_normalized_vector(self):
        embedding = [3.0, 4.0]
        result = update_preference_vector(None, embedding)
        norm = np.linalg.norm(result)
        assert norm == pytest.approx(1.0, abs=1e-6)

    def test_first_call_preserves_direction(self):
        embedding = [3.0, 4.0]
        result = update_preference_vector(None, embedding)
        assert result[0] == pytest.approx(0.6, abs=1e-6)
        assert result[1] == pytest.approx(0.8, abs=1e-6)

    def test_ema_blends_with_alpha(self):
        current = [1.0, 0.0]
        query = [0.0, 1.0]
        result = update_preference_vector(current, query, alpha=0.5)
        assert abs(result[0] - result[1]) < 0.01

    def test_result_is_normalized(self):
        current = [1.0, 0.0, 0.0]
        query = [0.0, 1.0, 0.0]
        result = update_preference_vector(current, query, alpha=0.7)
        norm = np.linalg.norm(result)
        assert norm == pytest.approx(1.0, abs=1e-6)

    def test_high_alpha_favors_new_query(self):
        current = [1.0, 0.0]
        query = [0.0, 1.0]
        result = update_preference_vector(current, query, alpha=0.9)
        assert result[1] > result[0]

    def test_zero_vector_handling(self):
        result = update_preference_vector(None, [0.0, 0.0, 0.0])
        assert all(v == 0.0 for v in result)


class TestTrackExplicitPreferences:
    def test_empty_preferences_and_intent(self):
        result = track_explicit_preferences({}, {})
        assert result == {
            "liked_genres": [],
            "disliked_genres": [],
            "themes": [],
            "reference_films": [],
        }

    def test_accumulates_genres(self):
        prefs = {"liked_genres": ["Комедии"]}
        intent = {"genres": ["Драмы"]}
        result = track_explicit_preferences(prefs, intent)
        assert result["liked_genres"] == ["Комедии", "Драмы"]

    def test_no_duplicates(self):
        prefs = {"liked_genres": ["Комедии"]}
        intent = {"genres": ["Комедии"]}
        result = track_explicit_preferences(prefs, intent)
        assert result["liked_genres"] == ["Комедии"]

    def test_negations_go_to_disliked(self):
        result = track_explicit_preferences({}, {"negations": ["Ужасы"]})
        assert result["disliked_genres"] == ["Ужасы"]

    def test_reference_films_accumulated(self):
        prefs = {"reference_films": ["Интерстеллар"]}
        intent = {"reference_films": ["Начало"]}
        result = track_explicit_preferences(prefs, intent)
        assert "Интерстеллар" in result["reference_films"]
        assert "Начало" in result["reference_films"]

    def test_themes_accumulated(self):
        result = track_explicit_preferences({}, {"themes": ["космос", "путешествия"]})
        assert result["themes"] == ["космос", "путешествия"]
