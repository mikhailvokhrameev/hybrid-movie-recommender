"""Multi-signal hybrid scoring with MMR diversification.

Scoring pipeline:
  candidates ──> hybrid_score() per movie ──> mmr_diversify() ──> top-N

Three scoring signals, weighted sum:
  - semantic (0.4): cosine similarity between query and movie embeddings
  - metadata (0.3): genre overlap between LLM-extracted intent and movie genres
  - session  (0.3): cosine similarity between session preference vector and movie

Cosine similarity is mapped from [-1, 1] to [0, 1] via (sim + 1) / 2.
Weights are configurable via SCORE_WEIGHT_* environment variables.

MMR (Maximal Marginal Relevance, Carbonell & Goldstein 1998) ensures the
top-N results are diverse: each subsequent pick maximizes
  lambda * score - (1 - lambda) * max_similarity_to_selected
"""

from django.conf import settings

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


def mmr_diversify(
    scored_candidates: list[dict],
    top_n: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """Select top-N diverse results via Maximal Marginal Relevance.

    Each candidate dict must have 'total' (relevance score) and
    'embedding' (for pairwise similarity computation).
    """
    if len(scored_candidates) <= top_n:
        return scored_candidates

    candidates = list(scored_candidates)
    selected = []

    best = max(candidates, key=lambda c: c["total"])
    selected.append(best)
    candidates.remove(best)

    while len(selected) < top_n and candidates:
        best_mmr_score = -float("inf")
        best_candidate = None

        for candidate in candidates:
            relevance = candidate["total"]

            max_sim = 0.0
            cand_emb = candidate.get("embedding")
            if cand_emb:
                for sel in selected:
                    sel_emb = sel.get("embedding")
                    if sel_emb:
                        sim = cosine_similarity(cand_emb, sel_emb)
                        max_sim = max(max_sim, sim)

            mmr = lambda_param * relevance - (1 - lambda_param) * max_sim

            if mmr > best_mmr_score:
                best_mmr_score = mmr
                best_candidate = candidate

        if best_candidate:
            selected.append(best_candidate)
            candidates.remove(best_candidate)
        else:
            break

    return selected


def _semantic_score(movie: dict, query_embedding: list[float]) -> float:
    movie_embedding = movie.get("embedding")
    if movie_embedding is None:
        return 0.0
    sim = cosine_similarity(query_embedding, movie_embedding)
    return max(0.0, (sim + 1.0) / 2.0)


def _metadata_score(movie: dict, intent: dict) -> float:
    """Genre overlap between LLM-extracted intent genres and movie genres."""
    intent_genres = set(intent.get("genres", []))
    movie_genres = set(movie.get("genres", []))

    if not intent_genres:
        return 0.5

    overlap = len(intent_genres & movie_genres)
    return overlap / len(intent_genres)


def _session_score(movie: dict, session_vector: list[float]) -> float:
    movie_embedding = movie.get("embedding")
    if movie_embedding is None:
        return 0.0
    sim = cosine_similarity(session_vector, movie_embedding)
    return max(0.0, (sim + 1.0) / 2.0)
