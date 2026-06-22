"""Run offline evaluation of the recommendation scoring pipeline.

Usage:
  python manage.py evaluate_scoring                    # run with default weights
  python manage.py evaluate_scoring --sweep            # grid search over weight space
  python manage.py evaluate_scoring --weights 0.5,0.3,0.2  # custom weights
"""

import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from core.candidate_generation import generate_candidates
from core.embedding_service import encode_query
from core.evaluation import evaluate_query, aggregate_metrics
from core.scoring import hybrid_score, mmr_diversify

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Evaluate recommendation scoring quality on the test query set"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-set",
            type=str,
            default="data/test_queries.json",
            help="Path to test queries JSON file",
        )
        parser.add_argument(
            "--k",
            type=int,
            default=5,
            help="Number of recommendations to evaluate (default: 5)",
        )
        parser.add_argument(
            "--sweep",
            action="store_true",
            help="Run grid search over weight space",
        )
        parser.add_argument(
            "--weights",
            type=str,
            default=None,
            help="Custom weights as comma-separated values: semantic,metadata,session",
        )

    def handle(self, *args, **options):
        with open(options["test_set"]) as f:
            test_set = json.load(f)

        k = options["k"]
        self.stdout.write(f"Loaded {len(test_set)} test queries")

        if options["sweep"]:
            self._run_sweep(test_set, k)
        else:
            weights = self._parse_weights(options["weights"])
            self._run_eval(test_set, k, weights)

    def _parse_weights(self, weights_str):
        if weights_str:
            parts = [float(x) for x in weights_str.split(",")]
            return {"semantic": parts[0], "metadata": parts[1], "session": parts[2]}
        return settings.SCORE_WEIGHTS

    def _build_intent(self, test_case):
        """Build intent dict from test case, including content_type filter."""
        intent = {"genres": list(test_case.get("relevant_genres", []))}
        if "negated_genres" in test_case:
            intent["negations"] = test_case["negated_genres"]
        if "relevant_content_type" in test_case:
            intent["content_type"] = test_case["relevant_content_type"]
        return intent

    def _score_query(self, test_case, k, weights):
        """Run the full pipeline for one query and return metrics."""
        query = test_case["query"]
        relevant_titles = test_case.get("relevant_titles", [])

        query_embedding = encode_query(query)
        intent = self._build_intent(test_case)
        candidates = generate_candidates(query_embedding, intent)

        scored = []
        for movie in candidates:
            scores = hybrid_score(movie, query_embedding, intent, weights=weights)
            scored.append({**movie, **scores})

        scored.sort(key=lambda x: x["total"], reverse=True)
        diversified = mmr_diversify(scored, top_n=k)

        recommended_titles = [m["serial_name"] for m in diversified]
        recommended_embeddings = [
            m["embedding"] for m in diversified if m.get("embedding") is not None
        ]

        return evaluate_query(
            recommended_titles,
            relevant_titles,
            recommended_embeddings,
            k=k,
        )

    def _run_eval(self, test_set, k, weights):
        self.stdout.write(
            f"Weights: semantic={weights['semantic']}, "
            f"metadata={weights['metadata']}, session={weights['session']}"
        )

        per_query = []
        for test_case in test_set:
            metrics = self._score_query(test_case, k, weights)
            per_query.append(metrics)

            self.stdout.write(
                f"  {test_case['query'][:50]:50s} P@{k}={metrics['precision_at_k']:.2f} "
                f"NDCG={metrics['ndcg_at_k']:.2f} "
                f"Div={metrics.get('diversity', 0):.2f}"
            )

        aggregated = aggregate_metrics(per_query)
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("AGGREGATE METRICS:")
        for key, value in aggregated.items():
            self.stdout.write(f"  {key}: {value:.4f}")

    def _run_sweep(self, test_set, k):
        self.stdout.write("Running weight grid search...")
        results = []

        for sem in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
            for met in [0.1, 0.2, 0.3, 0.4]:
                ses = round(1.0 - sem - met, 2)
                if ses < 0:
                    continue
                weights = {"semantic": sem, "metadata": met, "session": ses}

                per_query = []
                for test_case in test_set:
                    metrics = self._score_query(test_case, k, weights)
                    per_query.append(metrics)

                aggregated = aggregate_metrics(per_query)
                results.append((weights, aggregated))

        results.sort(key=lambda x: x[1].get("ndcg_at_k", 0), reverse=True)

        self.stdout.write("\nTop 5 weight configurations by NDCG@k:")
        self.stdout.write(f"{'Semantic':>8} {'Meta':>6} {'Session':>8} {'P@k':>6} {'NDCG':>6}")
        self.stdout.write("-" * 40)
        for weights, metrics in results[:5]:
            self.stdout.write(
                f"{weights['semantic']:>8.2f} {weights['metadata']:>6.2f} "
                f"{weights['session']:>8.2f} "
                f"{metrics.get('precision_at_k', 0):>6.3f} "
                f"{metrics.get('ndcg_at_k', 0):>6.3f}"
            )
