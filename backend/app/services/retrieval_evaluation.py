"""Repeatable local retrieval benchmark and ranking metrics."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hybrid_search import HybridSearchService

DEFAULT_BENCHMARK_PATH = Path(__file__).resolve().parents[1] / "evaluation" / "retrieval_cases.json"


def normalize_document_key(value: str) -> str:
    """Normalize stable keys so arXiv version suffixes do not fragment evaluation."""
    value = value.strip().lower()
    if value.startswith("arxiv:"):
        return re.sub(r"v\d+$", "", value)
    return value


def paper_document_key(paper) -> str:
    if paper.arxiv_id:
        return normalize_document_key(f"arxiv:{paper.arxiv_id}")
    if paper.doi:
        return normalize_document_key(f"doi:{paper.doi}")
    return f"id:{paper.id}"


def load_benchmark(path: Path = DEFAULT_BENCHMARK_PATH) -> dict:
    with path.open(encoding="utf-8") as benchmark_file:
        benchmark = json.load(benchmark_file)
    for case in benchmark["cases"]:
        case["relevant_ids"] = [normalize_document_key(value) for value in case["relevant_ids"]]
    return benchmark


def calculate_ranking_metrics(
    cases: Iterable[dict],
    rankings: dict[str, list[str]],
    top_k: int,
) -> dict:
    details = []
    for case in cases:
        relevant = {normalize_document_key(value) for value in case["relevant_ids"]}
        ranked = [normalize_document_key(value) for value in rankings.get(case["id"], [])[:top_k]]
        hits = [value for value in ranked if value in relevant]
        recall = len(set(hits)) / len(relevant) if relevant else 0.0
        reciprocal_rank = next((1 / rank for rank, value in enumerate(ranked, 1) if value in relevant), 0.0)
        dcg = sum(1 / math.log2(rank + 1) for rank, value in enumerate(ranked, 1) if value in relevant)
        ideal_hits = min(len(relevant), top_k)
        idcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
        ndcg = dcg / idcg if idcg else 0.0
        details.append({
            "id": case["id"],
            "query": case["query"],
            "relevant_ids": sorted(relevant),
            "ranked_ids": ranked,
            "recall_at_k": round(recall, 4),
            "reciprocal_rank": round(reciprocal_rank, 4),
            "ndcg_at_k": round(ndcg, 4),
        })

    count = len(details)
    return {
        "case_count": count,
        "recall_at_k": round(sum(item["recall_at_k"] for item in details) / count, 4) if count else 0.0,
        "mrr": round(sum(item["reciprocal_rank"] for item in details) / count, 4) if count else 0.0,
        "ndcg_at_k": round(sum(item["ndcg_at_k"] for item in details) / count, 4) if count else 0.0,
        "details": details,
    }


async def evaluate_retrieval(
    session: AsyncSession,
    *,
    mode: str = "bm25",
    top_k: int = 5,
    benchmark_path: Path = DEFAULT_BENCHMARK_PATH,
) -> dict:
    benchmark = load_benchmark(benchmark_path)
    search = HybridSearchService(session)
    rankings = {}
    for case in benchmark["cases"]:
        scored = await search.search(case["query"], top_k=top_k, mode=mode)
        papers_with_scores = await search.fetch_papers(scored)
        rankings[case["id"]] = [paper_document_key(paper) for paper, _score in papers_with_scores]

    metrics = calculate_ranking_metrics(benchmark["cases"], rankings, top_k)
    return {
        "benchmark_version": benchmark["version"],
        "description": benchmark.get("description", ""),
        "mode": mode,
        "top_k": top_k,
        **metrics,
    }
