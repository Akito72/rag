from dataclasses import dataclass


@dataclass(slots=True)
class RetrievalMetrics:
    hit_rate_at_k: float
    mean_reciprocal_rank: float


def evaluate_retrieval(results: list[list[str]], expected: list[str]) -> RetrievalMetrics:
    hits = 0
    reciprocal_rank_total = 0.0
    for retrieved, target in zip(results, expected):
        if target in retrieved:
            hits += 1
            reciprocal_rank_total += 1.0 / (retrieved.index(target) + 1)

    total = len(expected) or 1
    return RetrievalMetrics(
        hit_rate_at_k=hits / total,
        mean_reciprocal_rank=reciprocal_rank_total / total,
    )
