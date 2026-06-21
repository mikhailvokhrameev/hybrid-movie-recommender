"""Offline evaluation metrics for recommendation quality.

Metrics:
  - precision_at_k: fraction of recommended items in the relevant set
  - ndcg_at_k: normalized discounted cumulative gain (position-aware)
  - coverage: fraction of catalog items that appear in any recommendation
  - diversity: 1 - mean pairwise cosine similarity among recommended items

Usage:
  from core.evaluation import precision_at_k, ndcg_at_k, diversity
  p5 = precision_at_k(recommended_titles, relevant_titles, k=5)
"""

import math

import numpy as np

from core.embedding_service import cosine_similarity


def precision_at_k(recommended: list[str], relevant: list[str], k: int = 5) -> float:
    """Fraction of top-k recommendations that are in the relevant set."""
    if k <= 0:
        return 0.0
    top_k = recommended[:k]
    relevant_set = set(relevant)
    hits = sum(1 for item in top_k if item in relevant_set)
    return hits / k


def recall_at_k(recommended: list[str], relevant: list[str], k: int = 5) -> float:
    """Fraction of relevant items that appear in top-k recommendations."""
    if not relevant:
        return 0.0
    top_k = set(recommended[:k])
    relevant_set = set(relevant)
    hits = len(top_k & relevant_set)
    return hits / len(relevant_set)


def ndcg_at_k(recommended: list[str], relevant: list[str], k: int = 5) -> float:
    """Normalized Discounted Cumulative Gain at position k."""
    relevant_set = set(relevant)
    dcg = 0.0
    for i, item in enumerate(recommended[:k]):
        if item in relevant_set:
            dcg += 1.0 / math.log2(i + 2)

    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))

    if idcg == 0:
        return 0.0
    return dcg / idcg


def coverage(all_recommendations: list[list[str]], catalog_size: int) -> float:
    """Fraction of catalog items that appear in at least one recommendation list."""
    if catalog_size == 0:
        return 0.0
    unique_items = set()
    for rec_list in all_recommendations:
        unique_items.update(rec_list)
    return len(unique_items) / catalog_size


def diversity(embeddings: list[list[float]]) -> float:
    """1 - mean pairwise cosine similarity among recommended items.

    High diversity (close to 1.0) means recommendations are spread across
    different regions of the embedding space.
    """
    n = len(embeddings)
    if n < 2:
        return 1.0

    total_sim = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_sim += cosine_similarity(embeddings[i], embeddings[j])
            pairs += 1

    mean_sim = total_sim / pairs
    return 1.0 - mean_sim


def evaluate_query(
    recommended_titles: list[str],
    relevant_titles: list[str],
    recommended_embeddings: list[list[float]] | None = None,
    k: int = 5,
) -> dict:
    """Run all metrics for a single query."""
    metrics = {
        "precision_at_k": precision_at_k(recommended_titles, relevant_titles, k),
        "recall_at_k": recall_at_k(recommended_titles, relevant_titles, k),
        "ndcg_at_k": ndcg_at_k(recommended_titles, relevant_titles, k),
    }
    if recommended_embeddings:
        metrics["diversity"] = diversity(recommended_embeddings)
    return metrics


def aggregate_metrics(per_query_metrics: list[dict]) -> dict:
    """Average metrics across all queries in a test set."""
    if not per_query_metrics:
        return {}

    keys = per_query_metrics[0].keys()
    return {
        key: np.mean([m[key] for m in per_query_metrics if key in m])
        for key in keys
    }
