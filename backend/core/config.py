"""Static mappings between moods, genres, and time-of-day preferences.

Genre names are in Russian, matching the Okko catalog's genre taxonomy (32 genres).
Used by scoring.py for metadata matching and by mood_detector.py for mood-to-genre resolution.
"""

MOOD_GENRE_MAP = {
    "happy": ["Комедии", "Приключения", "Семейное"],
    "sad": ["Драмы", "Мелодрамы"],
    "excited": ["Боевики", "Триллеры", "Приключения"],
    "relaxed": ["Комедии", "Семейное", "Документальное"],
    "romantic": ["Мелодрамы", "Комедии"],
    "thoughtful": ["Драмы", "Детективы", "Документальное"],
    "scared": ["Ужасы", "Триллеры"],
    "energetic": ["Боевики", "Приключения"],
}

TIME_PREFERENCES = {
    "morning": ["Комедии", "Семейное", "Документальное"],
    "afternoon": ["Боевики", "Приключения", "Документальное"],
    "evening": ["Драмы", "Триллеры", "Детективы"],
    "night": ["Ужасы", "Триллеры", "Фантастика"],
}
