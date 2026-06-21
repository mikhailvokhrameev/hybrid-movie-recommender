"""Multi-signal hybrid scoring for movie recommendations.

Combines three signals into a weighted total score:
  - semantic (0.4): cosine similarity between query and movie embeddings
  - metadata (0.3): genre overlap, mood match, negation filtering
  - session  (0.3): cosine similarity between session preference vector and movie

Cosine similarity is mapped from [-1, 1] to [0, 1] for consistent scoring.
Weights are configurable via SCORE_WEIGHT_* environment variables.
"""

from django.conf import settings

from core.config import MOOD_GENRE_MAP
from core.embedding_service import cosine_similarity


def hybrid_score(
    movie: dict,
    query_embedding: list[float],
    intent: dict,
    session_vector: list[float] | None = None,
    weights: dict | None = None,
) -> dict:
    w = weights or settings.SCORE_WEIGHTS

    semantic = _semantic_score(movie, query_embedding)
    metadata = _metadata_score(movie, intent)
    session = _session_score(movie, session_vector) if session_vector else 0.0

    total = (
        semantic * w["semantic"]
        + metadata * w["metadata"]
        + session * w["session"]
    )

    return {
        "total": total,
        "semantic": semantic,
        "metadata": metadata,
        "session": session,
    }


def _semantic_score(movie: dict, query_embedding: list[float]) -> float:
    movie_embedding = movie.get("embedding")
    if not movie_embedding:
        return 0.0
    sim = cosine_similarity(query_embedding, movie_embedding)
    return max(0.0, (sim + 1.0) / 2.0)


def _metadata_score(movie: dict, intent: dict) -> float:
    scores = []

    intent_genres = set(intent.get("genres", []))
    movie_genres = set(movie.get("genres", []))
    if intent_genres:
        overlap = len(intent_genres & movie_genres)
        scores.append(overlap / len(intent_genres))

    mood = intent.get("mood", "")
    if mood and mood in MOOD_GENRE_MAP:
        mood_genres = set(MOOD_GENRE_MAP[mood])
        overlap = len(mood_genres & movie_genres)
        scores.append(overlap / len(mood_genres) if mood_genres else 0.0)

    negations = set(intent.get("negations", []))
    if negations and negations & movie_genres:
        return 0.0

    if not scores:
        return 0.5

    return sum(scores) / len(scores)


def _session_score(movie: dict, session_vector: list[float]) -> float:
    movie_embedding = movie.get("embedding")
    if not movie_embedding:
        return 0.0
    sim = cosine_similarity(session_vector, movie_embedding)
    return max(0.0, (sim + 1.0) / 2.0)
