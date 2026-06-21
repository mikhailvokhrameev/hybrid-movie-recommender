"""Ollama LLM client for intent parsing and recommendation explanations.

Communicates with a standalone Ollama container via its HTTP API.
Two roles: (1) parse natural language queries into structured intent (JSON mode),
(2) generate Russian-language explanations for recommended movies (RAG pattern).
Falls back to keyword extraction if Ollama is unavailable.
"""

import json
import logging
from typing import Generator

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

INTENT_PROMPT = """You are a movie intent parser. Extract structured information from the user's query about what kind of movie they want to watch.

Return a JSON object with these fields:
- genres: list of genre keywords (in Russian)
- mood: detected mood (happy, sad, excited, relaxed, romantic, thoughtful, scared, energetic, or empty string)
- themes: list of themes or topics mentioned
- negations: list of things the user does NOT want
- reference_films: list of film titles mentioned as reference

User query: {query}

Respond ONLY with valid JSON, no other text."""

EXPLANATION_PROMPT = """You are a movie recommendation assistant speaking Russian. The user asked: "{query}"

Based on their preferences, here are recommended movies. For each movie, write 1-2 sentences in Russian explaining why it matches what the user is looking for. Be specific about the connection between the user's request and each movie's qualities.

Movies:
{movies_context}

Write a brief, natural response in Russian recommending these movies with personalized explanations."""


def parse_intent(query: str, history: list[dict] | None = None) -> dict:
    """Extract structured intent from a natural language movie query via Ollama JSON mode.

    Returns dict with keys: genres, mood, themes, negations, reference_films.
    Falls back to keyword extraction if Ollama is unavailable or returns invalid JSON.
    """
    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "user", "content": INTENT_PROMPT.format(query=query)},
                ],
                "format": "json",
                "stream": False,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        parsed = json.loads(content)
        return {
            "genres": parsed.get("genres", []),
            "mood": parsed.get("mood", ""),
            "themes": parsed.get("themes", []),
            "negations": parsed.get("negations", []),
            "reference_films": parsed.get("reference_films", []),
        }
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Intent parsing failed, using fallback: {e}")
        return _fallback_intent(query)


def generate_explanation(query: str, movies: list[dict]) -> str:
    """Generate a Russian-language explanation of why each movie matches the query (RAG)."""
    movies_context = "\n".join(
        f"- {m['title']} ({', '.join(m.get('genres', []))}): {m.get('description', '')[:200]}"
        for m in movies
    )
    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": EXPLANATION_PROMPT.format(
                            query=query, movies_context=movies_context
                        ),
                    },
                ],
                "stream": False,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except (httpx.HTTPError, KeyError) as e:
        logger.warning(f"Explanation generation failed: {e}")
        return ""


def stream_explanation(query: str, movies: list[dict]) -> Generator[str, None, None]:
    """Streaming variant of generate_explanation. Yields tokens as they arrive from Ollama."""
    movies_context = "\n".join(
        f"- {m['title']} ({', '.join(m.get('genres', []))}): {m.get('description', '')[:200]}"
        for m in movies
    )
    try:
        with httpx.stream(
            "POST",
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": EXPLANATION_PROMPT.format(
                            query=query, movies_context=movies_context
                        ),
                    },
                ],
                "stream": True,
            },
            timeout=120.0,
        ) as response:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        logger.warning(f"Explanation streaming failed: {e}")


def is_available() -> bool:
    try:
        response = httpx.get(f"{settings.OLLAMA_BASE_URL}/", timeout=5.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def _fallback_intent(query: str) -> dict:
    query_lower = query.lower()
    genres = []
    mood = ""
    negations = []

    genre_keywords = {
        "комеди": "Комедии", "смешн": "Комедии", "весел": "Комедии",
        "драм": "Драмы", "серьёзн": "Драмы",
        "ужас": "Ужасы", "страшн": "Ужасы", "хоррор": "Ужасы",
        "боевик": "Боевики", "экшн": "Боевики", "экшен": "Боевики",
        "фантастик": "Фантастика", "космос": "Фантастика",
        "мелодрам": "Мелодрамы", "романтик": "Мелодрамы", "любов": "Мелодрамы",
        "триллер": "Триллеры", "напряжённ": "Триллеры",
        "детектив": "Детективы", "расследован": "Детективы",
        "мультфильм": "Мультфильмы", "мультик": "Мультфильмы",
        "документальн": "Документальное",
        "аниме": "Аниме",
    }

    for keyword, genre in genre_keywords.items():
        if keyword in query_lower:
            genres.append(genre)

    if "не хочу" in query_lower or "без " in query_lower or "кроме " in query_lower:
        for keyword, genre in genre_keywords.items():
            if keyword in query_lower:
                negations.append(genre)

    return {
        "genres": genres,
        "mood": mood,
        "themes": [],
        "negations": negations,
        "reference_films": [],
    }
