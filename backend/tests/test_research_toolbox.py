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


def test_tool_fit_plan_ranks_matching_tools_and_assigns_roles():
    tool_id = str(uuid4())
    brief = {"name": "Graph reasoning", "description": "Multi-hop graph retrieval", "keywords": ["graph", "retrieval"]}
    gap_map = {
        "gaps": [
            {
                "title": "Graph retrieval reliability gap",
                "limitation": "Graph retrieval lacks robust multi-hop evidence grounding.",
                "opportunity": "Use graph-augmented retrieval with stronger evaluation.",
                "research_question": "Can graph retrieval improve multi-hop QA reliability?",
            }
        ]
    }
    context = {
        "tool_context": {
            "mode": "required",
            "tools": [
                {
                    "id": tool_id,
                    "name": "GraphRAG",
                    "kind": "algorithm",
                    "summary": "Graph retrieval for multi-hop evidence grounding",
                    "use_cases": "Graph retrieval and question answering",
                    "limitations": "Graph construction cost",
                    "tags": ["graph", "retrieval"],
                    "maturity": "experimental",
                    "evidence": [{"title": "Graph Retrieval", "evidence_note": "Used for multi-hop reasoning."}],
                }
            ],
        }
    }

    plan = ResearchIdeaWorkbenchService.build_tool_fit_plan(brief, gap_map, context)

    assert plan["items"][0]["tool_id"] == tool_id
    assert plan["items"][0]["role"] == "core_component"
    assert plan["items"][0]["fit_score"] > 0
    assert plan["items"][0]["matched_gap_titles"] == ["Graph retrieval reliability gap"]


def test_fallback_candidates_use_top_tool_fit_item():
    tool_id = str(uuid4())
    brief = {"name": "Graph reasoning"}
    evidence_map = {"seed": [], "background": [], "inspiration": []}
    gap_map = {"gaps": [{"title": "Graph gap", "limitation": "Graph retrieval is brittle.", "evidence_ids": []}]}
    generation_context = {
        "tool_context": {
            "mode": "baseline",
            "tools": [{"id": tool_id, "name": "GraphRAG", "kind": "algorithm", "tags": ["graph"]}],
        },
        "tool_fit_plan": {
            "mode": "baseline",
            "items": [
                {
                    "tool_id": tool_id,
                    "tool_name": "GraphRAG",
                    "role": "baseline_or_comparator",
                    "fit_score": 0.8,
                    "recommended_use": "把 GraphRAG 作为强基线。",
                    "rationale": "与 graph gap 高度匹配。",
                }
            ],
        },
    }

    candidates = ResearchIdeaWorkbenchService._fallback_candidates(
        brief, evidence_map, gap_map, 1, generation_context=generation_context
    )

    assert candidates[0]["used_tool_ids"] == [tool_id]
    assert candidates[0]["used_tool_names"] == ["GraphRAG"]
    assert "GraphRAG" in candidates[0]["minimum_experiment"]["baselines"]
    assert candidates[0]["tool_fit_rationale"] == "与 graph gap 高度匹配。"
