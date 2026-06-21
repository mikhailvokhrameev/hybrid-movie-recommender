"""Session-based preference learning via exponential moving average (EMA).

Maintains a 768-dim preference vector per conversation session.
Each query embedding is blended into the running vector with alpha=0.7
(recent queries dominate). The vector is L2-normalized after each update
to keep cosine similarity scores consistent regardless of turn count.
"""

import numpy as np


ALPHA = 0.7


def update_preference_vector(
    current_vector: list[float] | None,
    query_embedding: list[float],
    alpha: float = ALPHA,
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
    prefs = {
        "liked_genres": list(current_preferences.get("liked_genres", [])),
        "disliked_genres": list(current_preferences.get("disliked_genres", [])),
        "themes": list(current_preferences.get("themes", [])),
        "reference_films": list(current_preferences.get("reference_films", [])),
    }

    for genre in intent.get("genres", []):
        if genre not in prefs["liked_genres"]:
            prefs["liked_genres"].append(genre)

    for genre in intent.get("negations", []):
        if genre not in prefs["disliked_genres"]:
            prefs["disliked_genres"].append(genre)

    for theme in intent.get("themes", []):
        if theme not in prefs["themes"]:
            prefs["themes"].append(theme)

    for film in intent.get("reference_films", []):
        if film not in prefs["reference_films"]:
            prefs["reference_films"].append(film)

    return prefs
