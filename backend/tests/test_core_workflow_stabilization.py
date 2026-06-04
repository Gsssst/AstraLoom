"""Regression tests for the core workflow stabilization change."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.main import app
from app.services import llm as llm_module
from app.services import research_service as research_module


@pytest.mark.asyncio
async def test_non_streaming_llm_returns_content_and_tracks_usage(monkeypatch):
    usage = SimpleNamespace(prompt_tokens=3, completion_tokens=5, total_tokens=8)
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="generated answer"))],
        usage=usage,
    )
    tracked = []

    async def fake_completion(**_kwargs):
        return response

    async def fake_log_usage(**kwargs):
        tracked.append(kwargs)

    service = llm_module.LLMService()
    monkeypatch.setattr(llm_module.litellm, "acompletion", fake_completion)
    monkeypatch.setattr(service, "_log_usage", fake_log_usage)

    result = await service.chat([{"role": "user", "content": "hello"}])

    assert result == "generated answer"
    assert tracked == [
        {"prompt_tokens": 3, "completion_tokens": 5, "total_tokens": 8}
    ]


@pytest.mark.asyncio
async def test_research_idea_generation_accepts_paper_source_tuples(monkeypatch):
    paper = SimpleNamespace(
        title="Reliable Research Workflows",
        authors=["Ada Researcher"],
        year=2026,
        abstract="A paper about reliable research automation.",
        full_text="Detailed evidence.",
        tags=["automation"],
        arxiv_id="2601.00001",
    )
    session = SimpleNamespace(
        added=[],
        add=lambda item: session.added.append(item),
        commit=_async_noop,
        rollback=_async_noop,
    )
    project = SimpleNamespace(
        id=uuid4(),
        name="Research automation",
        description="Generate grounded ideas",
        keywords=["research", "automation"],
        paper_ids=[],
    )
    idea_json = (
        '[{"title":"Grounded idea","description":"Use evidence.",'
        '"innovation":"Traceable prompts","approach":"Evaluate it.",'
        '"feasibility":8,"novelty":7}]'
    )

    async def fake_select_papers(*_args, **_kwargs):
        return [(paper, 0.91, "manual")]

    async def fake_chat(*_args, **_kwargs):
        return idea_json

    async def fake_ensure_full_text(_paper):
        return _paper.full_text

    monkeypatch.setattr(
        "app.services.paper_selection.PaperSelectionService.select_papers",
        fake_select_papers,
    )
    monkeypatch.setattr(research_module.llm_service, "chat", fake_chat)
    monkeypatch.setattr("app.services.report_service.ensure_full_text", fake_ensure_full_text)

    ideas = await research_module.ResearchPipelineService(session).generate_ideas(project)

    assert len(ideas) == 1
    assert ideas[0].title == "Grounded idea"
    assert ideas[0].referenced_papers["1"]["arxiv_id"] == "2601.00001"


def test_export_markdown_route_precedes_dynamic_paper_detail_route():
    paths = [route.path for route in app.routes]

    assert paths.index("/api/papers/export-markdown") < paths.index("/api/papers/{paper_id}")


def test_profile_update_route_is_registered_once():
    profile_put_routes = [
        route
        for route in app.routes
        if route.path == "/api/settings/profile" and "PUT" in (route.methods or set())
    ]

    assert len(profile_put_routes) == 1

async def _async_noop():
    return None
