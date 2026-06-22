"""Candidate generation via pgvector approximate nearest neighbor search.

Retrieves the top-N most semantically similar movies from the catalog using
HNSW cosine distance, then applies hard filters (negation, content type)
before passing candidates to the hybrid reranker.

Pipeline position:
  query embedding ──> ANN search (pgvector HNSW) ──> hard filters ──> candidates
"""

import logging

from pgvector.django import CosineDistance

from movies.models import Movie

logger = logging.getLogger(__name__)

DEFAULT_CANDIDATE_COUNT = 100


def generate_candidates(
    query_embedding: list[float],
    intent: dict | None = None,
    limit: int = DEFAULT_CANDIDATE_COUNT,
) -> list[dict]:
    """Retrieve candidate movies via ANN search with hard filters.

    1. pgvector HNSW cosine search for top candidates
    2. Hard filter: exclude movies matching negated genres
    3. Optional: filter by content_type if specified in intent
    """
    queryset = Movie.objects.filter(embedding__isnull=False)

    if intent:
        negations = intent.get("negations", [])
        if negations:
            for neg_genre in negations:
                queryset = queryset.exclude(genres__contains=[neg_genre])

        content_type = intent.get("content_type")
        if content_type:
            queryset = queryset.filter(content_type=content_type)

    candidates = (
        queryset
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:limit]
    )

    return [
        {
            "id": movie.id,
            "serial_name": movie.serial_name,
            "genres": movie.genres,
            "content_type": movie.content_type,
            "country": movie.country,
            "actors": movie.actors,
            "director": movie.director,
            "age_rating": movie.age_rating,
            "release_date": str(movie.release_date) if movie.release_date else None,
            "description": movie.description,
            "url": movie.url,
            "embedding": list(movie.embedding) if movie.embedding is not None else None,
            "distance": float(movie.distance),
        }
        for movie in candidates
    ]
