"""Static mappings between moods, genres, and time-of-day preferences.

Genre names are in Russian, matching the Okko catalog's genre taxonomy (32 genres).
These maps are used ONLY in the keyword fallback path (ollama_client._fallback_intent)
when Ollama is unavailable. The primary scoring path uses LLM-extracted genres directly.

TIME_PREFERENCES is documented here for production reference but not used in scoring.
A production system would validate these mappings via A/B testing with real user data.
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
