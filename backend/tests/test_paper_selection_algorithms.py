"""Regression tests for paper recommendation ranking algorithms."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.paper_selection import PaperSelectionService


def _paper(**overrides):
    data = {
        "id": uuid4(),
        "title": "Contrastive Video Grounding with Temporal Evidence",
        "authors": ["Ada", "Bob"],
        "year": 2025,
        "abstract": "This paper studies contrastive video grounding with temporal evidence and strong benchmarks.",
        "arxiv_id": "2606.00001",
        "doi": None,
        "full_text": "full text " * 120,
        "embedding": [0.1, 0.2],
        "citation_count": 80,
        "tags": ["video grounding", "contrastive"],
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.asyncio
async def test_recommendation_signals_boost_saved_and_complete_papers(monkeypatch):
    service = PaperSelectionService(SimpleNamespace())
    saved = _paper(title="Saved Complete Paper")
    sparse = _paper(
        title="Sparse Paper",
        abstract="short",
        arxiv_id=None,
        full_text=None,
        embedding=None,
        citation_count=0,
        year=2016,
    )

    async def fake_signals(_papers):
        return {str(saved.id): 1.0}

    monkeypatch.setattr(service, "_load_user_paper_signals", fake_signals)

    ranked = await service._apply_recommendation_signals([
        (sparse, 0.72, "semantic:sparse"),
        (saved, 0.68, "semantic:saved"),
    ])

    assert ranked[0][0] is saved
    assert ranked[0][1] > ranked[1][1]


def test_recommendation_diversity_keeps_manual_and_suppresses_near_duplicates():
    service = PaperSelectionService(SimpleNamespace())
    manual = _paper(title="Manual Seed Paper", arxiv_id="2606.00010")
    duplicate_a = _paper(title="Video Grounding Temporal Localization Benchmark", arxiv_id="2606.00011")
    duplicate_b = _paper(title="Video Grounding Temporal Localization Benchmarks", arxiv_id="2606.00012")
    diverse = _paper(title="Failure Analysis for Multimodal Reasoning", tags=["failure analysis"], arxiv_id="2606.00013")

    selected = service._diversity_sample([
        (duplicate_a, 0.96, "semantic:a"),
        (duplicate_b, 0.95, "semantic:b"),
        (diverse, 0.88, "entity:failure"),
        (manual, 1.0, "manual"),
    ], max_papers=3)

    assert selected[0][0] is manual
    titles = [item[0].title for item in selected]
    assert "Failure Analysis for Multimodal Reasoning" in titles
    assert len(titles) == 3
