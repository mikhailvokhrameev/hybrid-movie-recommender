"""Session-based preference learning via exponential moving average (EMA).

Maintains a 768-dim preference vector per conversation session.
Each query embedding is blended into the running vector with a configurable
alpha (default 0.7). The vector is L2-normalized after each update to keep
cosine similarity scores consistent regardless of turn count.

Alpha is configurable via SESSION_ALPHA env var. Tune it with:
  manage.py evaluate_scoring --sweep
"""

import os

import numpy as np


DEFAULT_ALPHA = float(os.environ.get("SESSION_ALPHA", "0.7"))


def update_preference_vector(
    current_vector: list[float] | None,
    query_embedding: list[float],
    alpha: float = DEFAULT_ALPHA,
) -> list[float]:
    query_vec = np.array(query_embedding)

    if current_vector is None:
        normalized = query_vec / (np.linalg.norm(query_vec) or 1.0)
        return normalized.tolist()

    current_vec = np.array(current_vector)
    updated = alpha * query_vec + (1 - alpha) * current_vec

    norm = np.linalg.norm(updated)
    if norm > 0:
        updated = updated / norm

    return updated.tolist()


def track_explicit_preferences(
    current_preferences: dict,
    intent: dict,
) -> dict:
    INTENT_TO_PREF = [
        ("genres", "liked_genres"),
        ("negations", "disliked_genres"),
        ("themes", "themes"),
        ("reference_films", "reference_films"),
    ]

    prefs = {pref_key: list(current_preferences.get(pref_key, [])) for _, pref_key in INTENT_TO_PREF}

    for intent_key, pref_key in INTENT_TO_PREF:
        for item in intent.get(intent_key, []):
            if item not in prefs[pref_key]:
                prefs[pref_key].append(item)

    return prefs
