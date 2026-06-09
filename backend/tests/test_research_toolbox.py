"""Tests for research toolbox helpers and API contract."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.api import toolbox
from app.services.research_idea_workbench import ResearchIdeaWorkbenchService


def test_toolbox_normalizes_tags_without_duplicates():
    assert toolbox._normalize_tags(["RAG", " rag ", "", "Graph", "Graph"]) == ["RAG", "Graph"]


def test_toolbox_response_includes_linked_paper_evidence():
    paper_id = uuid4()
    tool_id = uuid4()
    now = datetime.now(timezone.utc)
    tool = SimpleNamespace(
        id=tool_id,
        name="GraphRAG",
        kind="algorithm",
        summary="Graph-augmented retrieval",
        use_cases="Multi-hop evidence organization",
        limitations="Graph construction cost",
        tags=["RAG", "graph"],
        maturity="experimental",
        created_by_user_id=uuid4(),
        created_at=now,
        updated_at=now,
        paper_links=[
            SimpleNamespace(
                relation="used",
                evidence_note="Used graph retrieval over paper chunks.",
                paper=SimpleNamespace(
                    id=paper_id,
                    title="Graph Retrieval for Research",
                    year=2026,
                    source="arxiv",
                ),
            )
        ],
    )

    response = toolbox._tool_to_response(tool)

    assert response.id == str(tool_id)
    assert response.tags == ["RAG", "graph"]
    assert response.papers[0].id == str(paper_id)
    assert response.papers[0].relation == "used"
    assert response.papers[0].evidence_note == "Used graph retrieval over paper chunks."


def test_tool_context_is_included_in_generation_constraints():
    tool_id = str(uuid4())
    context = {
        "gap_selection": {"selected_gap_titles": ["Graph reasoning gap"], "blocked_gap_titles": [], "focus_note": "low compute"},
        "generation_constraints": {"research_mode": "system", "risk_appetite": "balanced", "resource_budget": "reproducible"},
        "tool_context": {
            "mode": "required",
            "tool_ids": [tool_id],
            "tools": [
                {
                    "id": tool_id,
                    "name": "GraphRAG",
                    "kind": "algorithm",
                    "summary": "Graph-augmented retrieval",
                    "use_cases": "Multi-hop evidence organization",
                    "limitations": "Graph construction cost",
                    "tags": ["RAG", "graph"],
                    "maturity": "experimental",
                    "evidence": [{"paper_id": str(uuid4()), "title": "Graph Retrieval", "relation": "used"}],
                }
            ],
        },
    }

    text = ResearchIdeaWorkbenchService._format_generation_constraints(context)

    assert "GraphRAG" in text
    assert "tool_instruction" in text
    assert "必须至少使用一个选中的工具箱条目" in text
