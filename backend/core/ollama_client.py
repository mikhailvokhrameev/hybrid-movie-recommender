"""Ollama LLM client for intent parsing and recommendation explanations.

Communicates with a standalone Ollama container via its HTTP API.
Two roles: (1) parse natural language queries into structured intent (JSON mode),
(2) generate Russian-language explanations for recommended movies (RAG pattern).
Falls back to empty intent if Ollama is unavailable (semantic search still works).

Provides both sync and async variants for use in sync management commands
and async Django views respectively.
"""

import json
import logging
import os
from typing import Generator

import httpx
import numpy as np
from django.conf import settings

from core.embedding_service import cosine_similarity, encode_texts

logger = logging.getLogger(__name__)

_genre_embeddings = None
GENRE_MATCH_THRESHOLD = float(os.environ.get("GENRE_MATCH_THRESHOLD", "0.5"))

CATALOG_GENRES = [
    "Аниме", "Артхаус", "Биографии", "Блоги", "Боевики", "Вестерны",
    "Военное", "Детективы", "Документальное", "Драмы", "Интервью",
    "Историческое", "Комедии", "Концерты", "Короткий метр", "Криминальное",
    "Курсы", "Мелодрамы", "Музыкальное", "Мультфильмы", "Презентации",
    "Приключения", "Природа", "Путешествия", "Семейное", "Советское",
    "Триллеры", "Ужасы", "Фантастика", "Фильмы для детей", "Фитнес", "Фэнтези",
]

INTENT_PROMPT = """You are a movie intent parser. Given a user query, return a JSON object.

ALLOWED GENRES (use ONLY these exact strings, copy-paste):
{genres}

JSON fields:
- "genres": list of matching genres from the ALLOWED list above
- "mood": one of: happy, sad, excited, relaxed, romantic, thoughtful, scared, energetic, or ""
- "themes": list of themes mentioned
- "negations": list of genres the user does NOT want (from ALLOWED list)
- "reference_films": list of film titles mentioned

Example:
User: "хочу что-то смешное, но не ужасы"
{{"genres": ["Комедии"], "mood": "happy", "themes": [], "negations": ["Ужасы"], "reference_films": []}}

Example:
User: "триллер как Молчание ягнят"
{{"genres": ["Триллеры"], "mood": "excited", "themes": [], "negations": [], "reference_films": ["Молчание ягнят"]}}

Now parse this query:
User: "{query}"
"""

EXPLANATION_PROMPT = """You are a movie recommendation assistant speaking Russian. The user asked: "{query}"

Based on their preferences, here are recommended movies. For each movie, write 1-2 sentences in Russian explaining why it matches what the user is looking for. Be specific about the connection between the user's request and each movie's qualities.

Movies:
{movies_context}

Write a brief, natural response in Russian recommending these movies with personalized explanations."""


def _build_movies_context(movies: list[dict]) -> str:
    return "\n".join(
        f"- {m.get('serial_name', m.get('title', ''))} ({', '.join(m.get('genres', []))}): {m.get('description', '')[:200]}"
        for m in movies
    )


def _extract_intent(parsed: dict) -> dict:
    return {
        "genres": _normalize_genres(parsed.get("genres", [])),
        "mood": parsed.get("mood", ""),
        "themes": parsed.get("themes", []),
        "negations": _normalize_genres(parsed.get("negations", [])),
        "reference_films": parsed.get("reference_films", []),
    }


def _intent_payload(query: str) -> dict:
    return {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": INTENT_PROMPT.format(
                query=query, genres=", ".join(CATALOG_GENRES)
            )},
        ],
        "format": "json",
        "stream": False,
    }


def _explanation_payload(query: str, movies: list[dict], stream: bool = False) -> dict:
    return {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": EXPLANATION_PROMPT.format(
                    query=query, movies_context=_build_movies_context(movies)
                ),
            },
        ],
        "stream": stream,
    }


# --- Low-level Ollama call (shared by ollama_client and evaluation) ---


def _chat_sync(messages: list[dict], json_mode: bool = False, timeout: float = 60.0) -> str:
    """Send a chat request to Ollama and return the response content string."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    response = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


# --- Sync API (for management commands) ---


def parse_intent(query: str) -> dict:
    """Extract structured intent from a natural language movie query via Ollama JSON mode."""
    try:
        content = _chat_sync(
            _intent_payload(query)["messages"],
            json_mode=True,
            timeout=60.0,
        )
        return _extract_intent(json.loads(content))
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Intent parsing failed, using fallback: {e}")
        return _fallback_intent(query)


def generate_explanation(query: str, movies: list[dict]) -> str:
    """Generate a Russian-language explanation of why each movie matches the query (RAG)."""
    try:
        return _chat_sync(
            _explanation_payload(query, movies)["messages"],
            timeout=120.0,
        )
    except (httpx.HTTPError, KeyError) as e:
        logger.warning(f"Explanation generation failed: {e}")
        return ""


def stream_explanation(query: str, movies: list[dict]) -> Generator[str, None, None]:
    """Streaming variant of generate_explanation. Yields tokens as they arrive."""
    try:
        with httpx.stream(
            "POST",
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json=_explanation_payload(query, movies, stream=True),
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


# --- Async API (for Django async views) ---


async def aparse_intent(query: str) -> dict:
    """Async variant of parse_intent for use in async Django views."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=_intent_payload(query),
                timeout=60.0,
            )
            response.raise_for_status()
            parsed = json.loads(response.json()["message"]["content"])
            return _extract_intent(parsed)
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Async intent parsing failed, using fallback: {e}")
        return _fallback_intent(query)


async def agenerate_explanation(query: str, movies: list[dict]) -> str:
    """Async variant of generate_explanation for use in async Django views."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=_explanation_payload(query, movies),
                timeout=120.0,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
    except (httpx.HTTPError, KeyError) as e:
        logger.warning(f"Async explanation generation failed: {e}")
        return ""


async def ais_available() -> bool:
    """Async variant of is_available."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/", timeout=5.0)
            return response.status_code == 200
    except httpx.HTTPError:
        return False


def _get_genre_embeddings() -> np.ndarray:
    """Encode all catalog genres once, cache for the process lifetime."""
    global _genre_embeddings
    if _genre_embeddings is None:
        _genre_embeddings = encode_texts(CATALOG_GENRES)
        logger.info(f"Cached embeddings for {len(CATALOG_GENRES)} catalog genres")
    return _genre_embeddings


def _normalize_genres(raw_genres: list) -> list[str]:
    """Map LLM genre output to exact catalog genre names via embedding similarity.

    'комедия' -> 'Комедии', 'хоррор' -> 'Ужасы', 'мультик' -> 'Мультфильмы'
    """
    if not raw_genres:
        return []

    genre_embs = _get_genre_embeddings()
    normalized = []

    for raw in raw_genres:
        if not isinstance(raw, str) or not raw.strip():
            continue

        if raw in CATALOG_GENRES:
            normalized.append(raw)
            continue

        raw_emb = encode_texts([raw])[0]
        best_score = -1.0
        best_genre = None
        for i, catalog_emb in enumerate(genre_embs):
            sim = cosine_similarity(raw_emb.tolist(), catalog_emb.tolist())
            if sim > best_score:
                best_score = sim
                best_genre = CATALOG_GENRES[i]

        if best_genre and best_score >= GENRE_MATCH_THRESHOLD:
            if best_genre not in normalized:
                normalized.append(best_genre)
            logger.debug(f"Genre normalized: '{raw}' -> '{best_genre}' (sim={best_score:.3f})")
        else:
            logger.debug(f"Genre dropped: '{raw}' (best='{best_genre}' sim={best_score:.3f})")

    return normalized


def _fallback_intent(_query: str) -> dict:
    """Return empty intent when Ollama is unavailable.

    Semantic search via embeddings still works without parsed intent --
    it just loses metadata filtering. This is preferable to broken
    keyword parsing that silently produces wrong results.
    """
    return {
        "genres": [],
        "mood": "",
        "themes": [],
        "negations": [],
        "reference_films": [],
    }
