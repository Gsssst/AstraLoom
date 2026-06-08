"""Regression tests for the evidence-grounded Research Idea Workbench."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.research_idea_workbench import ResearchIdeaWorkbenchService
from app.services.research_service import ResearchPipelineService
from app.api.research import DiscussRequest, IdeaDiscussEvolveRequest
from app.services.digest_service import ExperimentService
from app.api.research import ExternalEvidenceImportRequest, import_external_evidence
from app.db.models.research import ResearchCodeProjectVersion, ResearchIdeaRun, ResearchProject


class _Session:
    def __init__(self):
        self.commits = 0
        self.added = []
        self.next_scalar = None
        self.scalar_results = []

    async def commit(self):
        self.commits += 1

    async def refresh(self, _item):
        return None

    def add(self, item):
        self.added.append(item)

    async def execute(self, _query):
        if self.scalar_results:
            value = self.scalar_results.pop(0)
        else:
            value = self.next_scalar
        return SimpleNamespace(scalar_one_or_none=lambda: value)


@pytest.mark.asyncio
async def test_stage_transition_is_persisted_and_emitted():
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    run = SimpleNamespace(status="pending", stage="briefing", progress=0, message="")
    events = []

    await service._transition(run, "retrieving", status="running", callback=events.append)

    assert run.stage == "retrieving"
    assert run.progress == 18
    assert run.status == "running"
    assert session.commits == 1
    assert events == [{
        "type": "stage",
        "stage": "retrieving",
        "status": "running",
        "progress": 18,
        "message": "正在从论文库收集背景与灵感证据",
    }]


@pytest.mark.asyncio
async def test_gap_preview_stops_after_gap_map(monkeypatch):
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    project = SimpleNamespace(id=uuid4(), name="Grounded QA", description="", keywords=[], metadata_json={}, paper_ids=[])
    run = SimpleNamespace(
        status="pending",
        stage="briefing",
        progress=0,
        message="",
        config_json={"external_search": False},
        evidence_map=None,
        gap_map=None,
        error=None,
    )
    evidence = {"scope": "local_library", "seed": [], "background": [], "inspiration": []}
    gap_map = {"summary": "Gaps", "gaps": [{"title": "Gap A", "limitation": "L", "opportunity": "O", "research_question": "Q", "evidence_ids": [], "uncertainty": "U"}]}

    async def fake_collect(*_args, **_kwargs):
        return evidence

    async def fake_gap(*_args, **_kwargs):
        return gap_map

    monkeypatch.setattr(service, "collect_evidence", fake_collect)
    monkeypatch.setattr(service, "extract_gap_map", fake_gap)

    result = await service.execute_gap_preview(project, run)

    assert result.stage == "gap_review"
    assert result.status == "pending"
    assert result.gap_map == gap_map
    assert result.evidence_map == evidence


@pytest.mark.asyncio
async def test_continue_from_gap_review_applies_selection_and_constraints(monkeypatch):
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    project = SimpleNamespace(id=uuid4(), name="Grounded QA", description="", keywords=[], metadata_json={}, paper_ids=[])
    run = SimpleNamespace(
        status="pending",
        stage="gap_review",
        progress=48,
        message="",
        config_json={"external_search": False},
        evidence_map={"scope": "local_library", "seed": [], "background": [], "inspiration": []},
        gap_map={"summary": "Gaps", "gaps": [
            {"title": "Gap A", "limitation": "L1", "opportunity": "O1", "research_question": "Q1", "evidence_ids": [], "uncertainty": "U1"},
            {"title": "Gap B", "limitation": "L2", "opportunity": "O2", "research_question": "Q2", "evidence_ids": [], "uncertainty": "U2"},
        ]},
        error=None,
    )
    captured = {}

    async def fake_execute(_project, _run, _brief, _evidence, constrained_gap_map, _num_ideas, **_kwargs):
        captured["gap_map"] = constrained_gap_map
        captured["config"] = _run.config_json
        return []

    monkeypatch.setattr(service, "_execute_from_gap_map", fake_execute)

    ideas = await service.continue_from_gap_review(
        project,
        run,
        gap_selection={"selected_gap_titles": ["Gap B"], "blocked_gap_titles": ["Gap A"], "focus_note": "prefer low compute"},
        generation_constraints={"research_mode": "experiment", "risk_appetite": "conservative", "resource_budget": "low_compute"},
        num_ideas=2,
    )

    assert ideas == []
    assert run.status == "complete"
    assert captured["gap_map"]["gaps"][0]["title"] == "Gap B"
    assert captured["gap_map"]["blocked_gaps"][0]["title"] == "Gap A"
    assert captured["config"]["generation_constraints"]["resource_budget"] == "low_compute"
    assert captured["config"]["gap_selection"]["focus_note"] == "prefer low compute"


@pytest.mark.asyncio
async def test_gap_feedback_persists_edits_and_summary():
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    run = SimpleNamespace(
        gap_map={"summary": "Gaps", "gaps": [{
            "title": "Gap A",
            "limitation": "L",
            "opportunity": "O",
            "research_question": "Q",
            "evidence_ids": ["p1"],
            "uncertainty": "U",
        }]},
        evidence_map={"seed": [{"paper_id": "p1", "title": "Evidence"}], "background": [], "inspiration": []},
        config_json={},
    )

    result = await service.save_gap_feedback(run, 0, {
        "title": "Edited Gap",
        "limitation": "Narrower limitation",
        "evidence_ids": ["p1", "missing"],
        "rating": "weak",
        "labels": ["too_broad", "not_allowed"],
        "note": "Needs narrowing.",
    })

    gap = result.gap_map["gaps"][0]
    assert gap["title"] == "Edited Gap"
    assert gap["limitation"] == "Narrower limitation"
    assert gap["evidence_ids"] == ["p1"]
    assert gap["user_feedback"]["rating"] == "weak"
    assert gap["user_feedback"]["labels"] == ["too_broad"]
    assert result.config_json["gap_feedback"][0]["title"] == "Edited Gap"
    assert session.commits == 1


@pytest.mark.asyncio
async def test_refine_gap_falls_back_and_preserves_feedback(monkeypatch):
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    project = SimpleNamespace(id=uuid4(), name="Grounded QA", description="", keywords=[], metadata_json={}, paper_ids=[])
    run = SimpleNamespace(
        stage="complete",
        status="complete",
        progress=100,
        message="done",
        gap_map={"summary": "Gaps", "gaps": [{
            "title": "Broad Gap",
            "limitation": "Too broad.",
            "opportunity": "Test something.",
            "research_question": "What works?",
            "evidence_ids": ["p1"],
            "uncertainty": "High.",
            "user_feedback": {"rating": "weak", "labels": ["too_broad"], "note": "Make it testable."},
        }]},
        evidence_map={"seed": [{"paper_id": "p1", "title": "Evidence", "relevance": "Supports boundary analysis."}], "background": [], "inspiration": []},
        config_json={},
    )

    async def empty_json(_prompt):
        return {}

    monkeypatch.setattr(service, "_chat_json", empty_json)
    result = await service.refine_gap(project, run, 0, focus_note="prefer low compute")

    refined = result.gap_map["gaps"][0]
    assert refined["refinement"]["source"] == "fallback"
    assert refined["refinement"]["focus_note"] == "prefer low compute"
    assert refined["user_feedback"]["labels"] == ["too_broad"]
    assert result.stage == "gap_review"
    assert result.status == "pending"


def test_generation_context_summarizes_feedback_and_fallback_avoids_rejected_gap():
    service = ResearchIdeaWorkbenchService(_Session())
    gap_map = {"gaps": [
        {
            "title": "Rejected Gap",
            "limitation": "Do not use.",
            "evidence_ids": ["p1"],
            "user_feedback": {"rating": "reject", "labels": ["misaligned"], "note": "Out of scope."},
        },
        {
            "title": "Strong Gap",
            "limitation": "Boundary is unclear.",
            "evidence_ids": ["p1"],
            "user_feedback": {"rating": "strong", "labels": ["valuable"], "note": "Use this."},
        },
    ]}
    run = SimpleNamespace(config_json={})
    evidence = {"seed": [{"paper_id": "p1", "title": "Evidence"}], "background": [], "inspiration": []}

    context = service.generation_context_from_run(run, gap_map)
    candidates = ResearchIdeaWorkbenchService._fallback_candidates(
        {"name": "Grounded QA"},
        evidence,
        gap_map,
        count=1,
        generation_context=context,
    )

    assert context["gap_feedback"][0]["rating"] == "reject"
    assert context["gap_feedback"][1]["title"] == "Strong Gap"
    assert "Strong Gap" in candidates[0]["hypothesis"]
    assert "rating=strong" in candidates[0]["approach"]


def test_duplicate_candidates_are_merged_by_hypothesis_overlap():
    candidates = [
        {"title": "Adaptive pruning", "hypothesis": "adaptive pruning improves efficient inference"},
        {"title": "Adaptive pruning method", "hypothesis": "adaptive pruning improves efficient inference"},
        {"title": "Reliable retrieval", "hypothesis": "hybrid retrieval improves grounding quality"},
    ]

    unique, duplicates = ResearchIdeaWorkbenchService.deduplicate_candidates(candidates)

    assert [candidate["title"] for candidate in unique] == ["Adaptive pruning", "Reliable retrieval"]
    assert duplicates == [{
        "kept": "Adaptive pruning",
        "merged": "Adaptive pruning method",
        "reason": "hypothesis_overlap",
    }]


@pytest.mark.asyncio
async def test_candidate_tree_expansion_records_lineage():
    service = ResearchIdeaWorkbenchService(_Session())
    candidates = [{
        "title": "Reliable grounding",
        "hypothesis": "Evidence calibration improves grounding.",
        "approach": "Add calibration module.",
        "evidence_ids": ["p1", "p2"],
        "risks": [],
        "falsification_test": "Reject if benchmark score does not improve.",
        "minimum_experiment": {"dataset": "Bench", "baselines": ["Base"], "metrics": ["Score"], "steps": ["Run"]},
    }]

    expanded, summary = await service.expand_candidate_tree(candidates, rounds=2, beam_width=2)

    assert summary["root_count"] == 1
    assert summary["expanded_count"] >= 2
    assert expanded[0]["tree"]["operator"] == "root"
    assert any(item["tree"]["parent_title"] == "Reliable grounding" for item in expanded[1:])
    assert any(item["tree"]["operator"] == "strong_baseline" for item in expanded)


@pytest.mark.asyncio
async def test_candidate_tree_expansion_uses_llm_evolved_candidates(monkeypatch):
    service = ResearchIdeaWorkbenchService(_Session())
    parent = {
        "title": "Reliable grounding",
        "path": "grounded",
        "gap": "Weak grounding.",
        "hypothesis": "Calibration improves grounding.",
        "approach": "Add calibration.",
        "evidence_ids": ["p1"],
        "risks": ["Weak baseline"],
        "falsification_test": "Reject if score does not improve.",
        "minimum_experiment": {"dataset": "Bench", "baselines": ["Base"], "metrics": ["Score"], "steps": ["Run"]},
    }

    async def fake_chat_json(_prompt):
        return {"evolved": [{
            "parent_title": "Reliable grounding",
            "operator": "mechanism_shift",
            "critique": "Mechanism is underspecified.",
            "improvement": "Use uncertainty-aware calibration.",
            "selection_angle": "Covers mechanism shift.",
            "title": "Uncertainty-aware grounding",
            "path": "grounded",
            "gap": "Weak grounding.",
            "hypothesis": "Uncertainty-aware calibration improves grounding.",
            "approach": "Add calibrated uncertainty gate.",
            "evidence_ids": ["p1"],
            "risks": ["Over-calibration"],
            "falsification_test": "Reject if citation precision is unchanged.",
            "minimum_experiment": {"dataset": "Bench", "baselines": ["Base"], "metrics": ["Citation precision"], "steps": ["Run", "Ablate", "Audit"]},
        }]}

    monkeypatch.setattr(service, "_chat_json", fake_chat_json)
    expanded, summary = await service.expand_candidate_tree(
        [parent],
        {"name": "Grounded QA"},
        {"seed": [{"paper_id": "p1", "title": "Evidence", "abstract_excerpt": "grounding"}], "background": [], "inspiration": []},
        {"gaps": []},
        rounds=2,
        beam_width=2,
    )

    evolved = next(item for item in expanded if item["title"] == "Uncertainty-aware grounding")
    assert evolved["tree"]["source"] == "llm"
    assert evolved["critique"] == "Mechanism is underspecified."
    assert summary["llm_evolved_count"] == 1


def test_novelty_check_flags_similar_candidate():
    service = ResearchIdeaWorkbenchService(_Session())
    evidence = {
        "seed": [{"paper_id": "p1", "title": "Adaptive Token Pruning", "abstract_excerpt": "adaptive token pruning improves efficient inference"}],
        "background": [],
        "inspiration": [],
    }
    candidates = [{
        "title": "Adaptive Token Pruning",
        "hypothesis": "adaptive token pruning improves efficient inference",
        "approach": "prune tokens adaptively",
    }]

    checked = service.novelty_check_candidates(candidates, evidence)

    assert checked[0]["novelty_check"]["status"] in {"too_similar", "incremental"}
    assert checked[0]["novelty_check"]["nearest_evidence"]["paper_id"] == "p1"
    assert checked[0]["novelty_check"]["similar_work"][0]["paper_id"] == "p1"
    assert checked[0]["novelty_check"]["collision_risk"] in {"high", "medium"}


def test_novelty_collision_risk_tracks_high_medium_and_low_similarity():
    service = ResearchIdeaWorkbenchService(_Session())
    evidence = {
        "seed": [{
            "paper_id": "p1",
            "title": "Adaptive Token Pruning",
            "abstract_excerpt": "adaptive token pruning improves efficient inference under latency budgets",
            "source": "local_library",
            "category": "seed",
            "year": 2025,
        }],
        "background": [{
            "paper_id": "p2",
            "title": "Efficient Inference Calibration",
            "abstract_excerpt": "calibration for efficient inference improves robustness",
            "source": "semantic_scholar",
            "category": "background",
            "year": 2024,
        }],
        "inspiration": [],
    }
    candidates = [
        {
            "title": "Adaptive Token Pruning",
            "hypothesis": "adaptive token pruning improves efficient inference under latency budgets",
            "approach": "prune tokens adaptively",
        },
        {
            "title": "Inference Calibration Under Budget",
            "hypothesis": "calibration improves efficient inference robustness",
            "approach": "add calibration under fixed budgets",
        },
        {
            "title": "Citation Graph Curriculum",
            "hypothesis": "citation graph curriculum improves literature review planning",
            "approach": "rank papers by graph novelty",
        },
    ]

    checked = service.novelty_check_candidates(candidates, evidence)
    risks = [item["novelty_check"]["collision_risk"] for item in checked]

    assert risks[0] == "high"
    assert risks[1] in {"medium", "low"}
    assert risks[2] == "low"
    assert checked[0]["novelty_check"]["similar_work"][0]["relation"] == "nearest_collision_candidate"
    assert checked[0]["novelty_check"]["source_coverage"]["local_count"] == 2


@pytest.mark.asyncio
async def test_similar_work_collection_records_external_source_fallback(monkeypatch):
    service = ResearchIdeaWorkbenchService(_Session())

    async def fake_external(_query):
        return (
            [{
                "paper_id": "ext:arxiv:2606.00001",
                "title": "External Similar Work",
                "abstract_excerpt": "similar idea from external search",
                "source": "arxiv",
                "category": "inspiration",
                "year": 2026,
            }],
            {"semantic_scholar": "rate limited"},
        )

    monkeypatch.setattr(service, "_collect_external_evidence", fake_external)
    context = await service.collect_similar_work(
        {"name": "Efficient Inference", "keywords": ["pruning"]},
        {"seed": [{"paper_id": "p1", "title": "Local Evidence", "abstract_excerpt": "local evidence", "source": "local_library"}], "background": [], "inspiration": []},
        [{"title": "Adaptive Pruning", "hypothesis": "adaptive pruning improves efficient inference"}],
        external_search=True,
    )

    assert context["source_coverage"]["external_count"] == 1
    assert context["source_coverage"]["source_errors"] == {"semantic_scholar": "rate limited"}
    assert {item["paper_id"] for item in context["items"]} == {"p1", "ext:arxiv:2606.00001"}


def test_adversarial_review_objects_to_weak_baseline_and_metrics():
    service = ResearchIdeaWorkbenchService(_Session())
    candidate = {
        "title": "Weak proposal",
        "hypothesis": "Maybe improves something",
        "evidence_ids": ["p1"],
        "falsification_test": "",
        "minimum_experiment": {"dataset": "Bench", "baselines": [], "metrics": [], "steps": ["Run"]},
        "novelty_check": {"status": "likely_novel"},
    }

    reviewed = service.adversarial_review_candidates([candidate])

    adversarial = reviewed[0]["adversarial_review"]
    assert adversarial["penalty"] > 0
    assert adversarial["verdict"] in {"revise", "reject"}
    assert any("baseline" in item.lower() for item in adversarial["objections"])


def test_diverse_selection_prefers_distinct_facets_over_near_duplicate():
    service = ResearchIdeaWorkbenchService(_Session())
    candidates = [
        {
            "title": "Calibration for QA",
            "path": "grounded",
            "hypothesis": "calibration improves qa grounding",
            "score": 9.0,
            "evidence_ids": ["p1"],
            "minimum_experiment": {"dataset": "QA-Bench", "metrics": ["citation precision"], "baselines": ["Base"], "steps": ["Run"]},
            "risks": ["weak baseline"],
            "tree": {"operator": "root"},
        },
        {
            "title": "QA Calibration Variant",
            "path": "grounded",
            "hypothesis": "calibration improves qa grounding",
            "score": 8.9,
            "evidence_ids": ["p1"],
            "minimum_experiment": {"dataset": "QA-Bench", "metrics": ["citation precision"], "baselines": ["Base"], "steps": ["Run"]},
            "risks": ["weak baseline"],
            "tree": {"operator": "strong_baseline"},
        },
        {
            "title": "Cost-aware retrieval",
            "path": "inspiration",
            "hypothesis": "cost-aware retrieval improves latency under fixed quality",
            "score": 8.4,
            "evidence_ids": ["p2"],
            "minimum_experiment": {"dataset": "Latency-Bench", "metrics": ["latency"], "baselines": ["Base"], "steps": ["Run"]},
            "risks": ["cost tradeoff"],
            "tree": {"operator": "cost_aware"},
        },
    ]

    selected, summary = service.select_diverse_proposals(candidates, num_ideas=2)

    assert [item["title"] for item in selected] == ["Calibration for QA", "Cost-aware retrieval"]
    assert selected[0]["selection_rationale"]
    assert selected[1]["selection_score"] <= selected[1]["score"] + 0.5
    assert "diversity_facets" in selected[1]
    assert any(item["reason"] == "diversity_near_duplicate" for item in summary["suppressed"])


def test_validate_idea_blocks_high_collision_and_missing_experiment():
    service = ResearchIdeaWorkbenchService(_Session())
    idea = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        feasibility_score=5,
        referenced_papers={"paper_ids": ["p1"]},
        evidence_json={"items": [{"paper_id": "p1", "title": "Adaptive Token Pruning", "score": 0.9, "category": "seed"}]},
        review_json={
            "novelty_check": {
                "status": "too_similar",
                "score": 0.1,
                "max_similarity": 0.9,
                "rationale": "Too close to prior work.",
                "nearest_evidence": {"paper_id": "p1", "title": "Adaptive Token Pruning", "source": "local_library"},
            },
            "adversarial_review": {"objections": ["baseline 设置可能偏弱。"]},
        },
        experiment_plan={"dataset": "", "baselines": [], "metrics": [], "steps": ["Run once"]},
    )

    validation = service.validate_idea(idea)

    assert validation["collision_risk"]["level"] == "high"
    assert validation["writing_readiness"]["status"] == "blocked"
    assert validation["coverage"]["has_enough_evidence"] is False
    assert any(risk["type"] == "evidence_gap" for risk in validation["feasibility_risks"])
    assert validation["experiment_checklist"]["baselines"]["present"] is False
    assert validation["related_work"][0]["relation"] == "nearest_collision_candidate"


def test_validate_idea_prefers_ranked_similar_work_as_related_work():
    service = ResearchIdeaWorkbenchService(_Session())
    idea = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        feasibility_score=8,
        referenced_papers={"paper_ids": ["p1", "p2"]},
        evidence_json={"items": [{"paper_id": "p1", "title": "Supporting Evidence", "score": 0.9, "category": "seed"}]},
        review_json={
            "novelty_check": {
                "status": "incremental",
                "score": 0.55,
                "max_similarity": 0.45,
                "rationale": "Needs differentiation.",
                "nearest_evidence": {"paper_id": "p1", "title": "Supporting Evidence", "source": "local_library"},
                "similar_work": [{
                    "paper_id": "ext:arxiv:2606.00001",
                    "title": "External Collision Candidate",
                    "source": "arxiv",
                    "score": 0.62,
                    "relation": "similar_prior_work",
                    "reason": "候选文本与论文摘要存在明显重叠",
                }],
            },
            "adversarial_review": {"objections": []},
        },
        experiment_plan={"dataset": "Bench", "baselines": ["Strong baseline"], "metrics": ["Score"], "steps": ["Reproduce", "Run", "Ablate"]},
    )

    validation = service.validate_idea(idea)

    assert validation["related_work"][0]["paper_id"] == "ext:arxiv:2606.00001"
    assert validation["related_work"][0]["relation"] == "similar_prior_work"


def test_validate_idea_marks_complete_plan_as_writing_ready():
    service = ResearchIdeaWorkbenchService(_Session())
    idea = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        feasibility_score=8,
        referenced_papers={"paper_ids": ["p1", "p2"]},
        evidence_json={"items": [
            {"paper_id": "p1", "title": "Grounding Evidence", "score": 0.9, "category": "seed"},
            {"paper_id": "p2", "title": "Video Evidence", "score": 0.8, "category": "background"},
        ]},
        review_json={
            "novelty_check": {"status": "likely_novel", "score": 0.86, "max_similarity": 0.14, "rationale": "Low overlap."},
            "adversarial_review": {"objections": []},
        },
        experiment_plan={
            "dataset": "Charades-STA",
            "baselines": ["Latest strong baseline"],
            "metrics": ["mIoU", "Recall@1"],
            "steps": ["Reproduce baseline", "Run proposed method", "Ablation", "Error analysis"],
        },
    )

    validation = service.validate_idea(idea)

    assert validation["writing_readiness"]["status"] == "ready"
    assert validation["coverage"]["experiment_completeness"] == 1
    assert validation["experiment_checklist"]["ablations"]["present"] is True
    assert "创建写作草稿" in validation["next_actions"]


def _copilot_idea():
    return SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        generation_run_id=uuid4(),
        parent_idea_id=None,
        title="Evidence-grounded proposal",
        description="Use calibrated retrieval to reduce unsupported answers.",
        hypothesis="Calibration improves answer grounding.",
        approach="Add evidence calibration and evaluate against retrieval baselines.",
        novelty="Combines calibration with answer abstention.",
        feasibility_score=8,
        novelty_score=7,
        status="draft",
        referenced_papers={"paper_ids": ["p1", "p2"]},
        evidence_json={"scope": "local_library", "items": [
            {"paper_id": "p1", "title": "Grounded Retrieval", "score": 0.9, "category": "seed", "abstract_excerpt": "retrieval grounding"},
            {"paper_id": "p2", "title": "Answer Calibration", "score": 0.8, "category": "background", "abstract_excerpt": "calibration"},
        ]},
        review_json={
            "scores": {"novelty": 7, "evidence_grounding": 8, "feasibility": 8, "testability": 9, "impact": 7, "clarity": 8},
            "rationale": "Testable and evidence-backed.",
            "novelty_check": {"status": "likely_novel", "score": 0.8, "max_similarity": 0.2},
            "adversarial_review": {"objections": ["Needs a strong retrieval baseline."]},
        },
        experiment_plan={
            "dataset": "QA-Bench",
            "baselines": ["RAG baseline"],
            "metrics": ["citation precision"],
            "steps": ["Reproduce baseline", "Run calibration", "Ablation"],
        },
        evolution_json={},
        discussion_log=[],
    )


@pytest.mark.asyncio
async def test_idea_copilot_discussion_returns_structured_metadata(monkeypatch):
    session = _Session()
    service = ResearchPipelineService(session)
    idea = _copilot_idea()
    project = SimpleNamespace(id=idea.project_id, name="Grounded QA", description="Improve RAG reliability", keywords=["rag"])

    async def fake_chat(messages, **_kwargs):
        assert "审稿人" in messages[0]["content"]
        assert "Grounded Retrieval" in messages[0]["content"]
        assert "collision_risk" in messages[0]["content"]
        return """
        {
          "reply": "## 主要问题\\n需要补强强基线。",
          "risks": ["强基线不足"],
          "next_actions": ["补充 RAG baseline"],
          "suggested_questions": ["如何做消融？"],
          "evolution_focus": "围绕强基线和消融演化下一版"
        }
        """

    import app.services.research_service as research_module

    monkeypatch.setattr(research_module.llm_service, "chat", fake_chat)
    result = await service.discuss_idea(idea, "请严格审稿", project=project, mode="skeptic")

    assert result["mode"] == "skeptic"
    assert result["reply"].startswith("## 主要问题")
    assert result["risks"] == ["强基线不足"]
    assert result["next_actions"] == ["补充 RAG baseline"]
    assert result["suggested_questions"] == ["如何做消融？"]
    assert result["evolution_focus"] == "围绕强基线和消融演化下一版"
    assert result["context_summary"]["evidence_count"] == 2
    assert idea.discussion_log[-1]["metadata"]["evolution_focus"] == "围绕强基线和消融演化下一版"
    assert session.commits == 1


@pytest.mark.asyncio
async def test_idea_copilot_discussion_falls_back_for_plain_text(monkeypatch):
    service = ResearchPipelineService(_Session())
    idea = _copilot_idea()
    idea.evidence_json = {"scope": "local_library", "items": []}
    idea.experiment_plan = {}

    async def fake_chat(messages, **_kwargs):
        assert messages[-1]["content"] == "下一步？"
        return "请先补齐证据和最小实验。"

    import app.services.research_service as research_module

    monkeypatch.setattr(research_module.llm_service, "chat", fake_chat)
    result = await service.discuss_idea(idea, "下一步？", mode="mentor")

    assert result["reply"] == "请先补齐证据和最小实验。"
    assert result["context_summary"]["missing"]
    assert result["suggested_questions"]
    assert "演化" in result["evolution_focus"]


def test_discuss_request_rejects_invalid_copilot_mode():
    with pytest.raises(Exception):
        DiscussRequest(message="test", mode="invalid")


def test_discussion_evolve_request_accepts_optional_focus():
    req = IdeaDiscussEvolveRequest()

    assert req.focus == ""


def test_iteration_timeline_derives_lifecycle_events_from_existing_data():
    service = ResearchPipelineService(_Session())
    idea = _copilot_idea()
    idea.created_at = "2026-06-07T01:00:00+00:00"
    idea.discussion_log = []
    for index in range(10):
        idea.discussion_log.append({"role": "user", "content": f"question {index}"})
        idea.discussion_log.append({
            "role": "assistant",
            "content": f"assistant milestone {index}",
            "mode": "skeptic",
            "metadata": {
                "risks": [f"risk {index}"],
                "next_actions": [f"action {index}"],
                "suggested_questions": [f"follow up {index}"],
                "evolution_focus": f"focus {index}",
            },
        })
    child = SimpleNamespace(
        id=uuid4(),
        parent_idea_id=idea.id,
        title="Child proposal",
        status="draft",
        created_at="2026-06-07T03:00:00+00:00",
        evolution_json={"round": 2, "rationale": "Child rationale", "focus": "Child focus"},
    )
    experiments = [{
        "experiment_id": "exp-1",
        "idea_id": str(idea.id),
        "name": "Baseline",
        "dataset": "Bench",
        "results": {"score": 0.82},
        "notes": "Useful feedback",
        "timestamp": "2026-06-07T02:00:00+00:00",
    }]

    timeline = service.build_iteration_timeline(
        idea,
        SimpleNamespace(id=idea.project_id, name="Grounded QA", description="", keywords=[]),
        project_ideas=[idea, child],
        experiments=experiments,
    )

    event_types = [event["type"] for event in timeline["events"]]
    assert "created" in event_types
    assert "validation" in event_types
    assert "execution" in event_types
    assert "experiment" in event_types
    assert "child_version" in event_types
    assert timeline["summary"]["discussion_milestones"] == 8
    assert timeline["summary"]["experiment_count"] == 1
    assert timeline["summary"]["child_version_count"] == 1
    assert any(event["details"].get("evolution_focus") == "focus 9" for event in timeline["events"])


def test_iteration_timeline_sparse_proposal_still_has_core_events():
    service = ResearchPipelineService(_Session())
    idea = _copilot_idea()
    idea.evidence_json = {"scope": "local_library", "items": []}
    idea.review_json = {}
    idea.experiment_plan = {}
    idea.discussion_log = []

    timeline = service.build_iteration_timeline(idea, project_ideas=[], experiments=[])

    event_types = [event["type"] for event in timeline["events"]]
    assert event_types[0] == "created"
    assert {"validation", "execution"}.issubset(set(event_types))
    assert timeline["summary"]["discussion_milestones"] == 0
    assert timeline["summary"]["experiment_count"] == 0
    assert timeline["summary"]["event_count"] >= 3


def test_proposal_progress_board_groups_empty_project():
    service = ResearchPipelineService(_Session())
    project = SimpleNamespace(id=uuid4(), name="Empty", description="", keywords=[])

    board = service.build_proposal_progress_board(project, [], experiments=[])

    assert board["summary"]["total"] == 0
    assert board["summary"]["actionable"] == 0
    assert board["summary"]["recommended"] is None
    assert all(group["count"] == 0 for group in board["groups"])


def test_proposal_progress_board_classifies_ready_for_writing():
    service = ResearchPipelineService(_Session())
    project = SimpleNamespace(id=uuid4(), name="Grounded QA", description="", keywords=[])
    idea = _copilot_idea()
    idea.project_id = project.id

    board = service.build_proposal_progress_board(project, [idea], experiments=[])
    item = next(item for group in board["groups"] for item in group["items"])

    assert item["status"] == "ready_for_writing"
    assert item["recommended_action"]["type"] == "writing"
    assert item["priority"] >= 70
    assert item["signals"]["evidence_count"] == 2


def test_proposal_progress_board_classifies_needs_evidence_and_feedback_evolution():
    service = ResearchPipelineService(_Session())
    project = SimpleNamespace(id=uuid4(), name="Grounded QA", description="", keywords=[])
    sparse = _copilot_idea()
    sparse.id = uuid4()
    sparse.project_id = project.id
    sparse.title = "Sparse proposal"
    sparse.evidence_json = {"scope": "local_library", "items": []}
    sparse.referenced_papers = {"paper_ids": []}
    feedback = _copilot_idea()
    feedback.id = uuid4()
    feedback.project_id = project.id
    feedback.title = "Feedback proposal"
    experiments = [{
        "experiment_id": "exp-1",
        "idea_id": str(feedback.id),
        "name": "First run",
        "dataset": "Bench",
        "results": {"score": 0.74},
        "notes": "Needs iteration",
    }]

    board = service.build_proposal_progress_board(project, [sparse, feedback], experiments=experiments)
    items = {item["title"]: item for group in board["groups"] for item in group["items"]}

    assert items["Sparse proposal"]["status"] == "needs_evidence"
    assert items["Sparse proposal"]["recommended_action"]["type"] == "evidence"
    assert "证据覆盖不足" in items["Sparse proposal"]["blockers"]
    assert items["Feedback proposal"]["status"] == "needs_evolution"
    assert items["Feedback proposal"]["recommended_action"]["type"] == "evolve"
    assert board["summary"]["recommended"] == items["Feedback proposal"]["idea_id"]
    assert board["summary"]["counts"]["needs_evidence"] == 1
    assert board["summary"]["counts"]["needs_evolution"] == 1


def test_code_project_normalization_filters_unsafe_paths_and_adds_required_files():
    idea = _copilot_idea()
    raw = {
        "name": "Unsafe Project!",
        "framework": "pytorch",
        "summary": "Test package",
        "files": [
            {"path": "../secret.py", "content": "bad"},
            {"path": "/tmp/bad.py", "content": "bad"},
            {"path": "src/train.py", "language": "python", "purpose": "train", "content": "print('train')"},
            {"path": "src/train.py", "language": "python", "purpose": "duplicate", "content": "print('duplicate')"},
        ],
        "entrypoints": [{"name": "train", "path": "src/train.py", "command": "python src/train.py"}],
    }

    project = ResearchPipelineService.normalize_code_project(raw, idea, "pytorch")
    paths = [item["path"] for item in project["files"]]

    assert "../secret.py" not in paths
    assert "/tmp/bad.py" not in paths
    assert paths.count("src/train.py") == 1
    assert "README.md" in paths
    assert "configs/default.yaml" in paths
    assert project["entrypoints"][0]["path"] == "src/train.py"


def test_code_project_fallback_contains_reproducible_project_files():
    idea = _copilot_idea()

    project = ResearchPipelineService.normalize_code_project({}, idea, "pytorch")
    paths = {item["path"] for item in project["files"]}

    assert project["name"]
    assert project["framework"] == "pytorch"
    assert {"README.md", "requirements.txt", "src/train.py", "src/evaluate.py", "analysis/plot_results.py"}.issubset(paths)
    assert any("python src/train.py" in command for command in project["run_commands"])
    assert "No code is executed automatically by this application." in project["safety_notes"]


@pytest.mark.asyncio
async def test_generate_code_persists_project_package_and_legacy_code(monkeypatch):
    session = _Session()
    service = ResearchPipelineService(session)
    idea = _copilot_idea()

    async def fake_chat(messages, **_kwargs):
        assert "实验项目包" in messages[0]["content"]
        return """{
          "name": "grounded-qa",
          "framework": "pytorch",
          "summary": "Package summary",
          "setup": ["pip install -r requirements.txt"],
          "run_commands": ["python src/train.py"],
          "entrypoints": [{"name": "train", "path": "src/train.py", "command": "python src/train.py"}],
          "safety_notes": ["review before run"],
          "files": [
            {"path": "README.md", "language": "markdown", "purpose": "guide", "content": "# Guide"},
            {"path": "src/train.py", "language": "python", "purpose": "train", "content": "print('ok')"}
          ]
        }"""

    import app.services.research_service as research_module

    monkeypatch.setattr(research_module.llm_service, "chat", fake_chat)
    project = await service.generate_code(idea, framework="pytorch")

    assert project["name"] == "grounded-qa"
    assert idea.generated_code_project["name"] == "grounded-qa"
    assert idea.generated_code == "print('ok')"
    assert idea.status == "implemented"
    assert isinstance(session.added[0], ResearchCodeProjectVersion)
    assert session.added[0].version == 1
    assert session.added[0].project_manifest["name"] == "grounded-qa"
    assert session.commits == 1


@pytest.mark.asyncio
async def test_code_project_version_snapshot_increments_per_idea():
    session = _Session()
    session.next_scalar = 2
    service = ResearchPipelineService(session)
    idea = _copilot_idea()
    project = {
        "name": "project-v3",
        "framework": "pytorch",
        "summary": "third version",
        "files": [{"path": "README.md", "language": "markdown", "purpose": "guide", "content": "# v3"}],
    }

    version = await service.create_code_project_version(idea, project, "# v3")

    assert version.version == 3
    assert version.file_count == 1
    assert version.project_name == "project-v3"
    assert session.added == [version]


def test_code_project_manifest_diff_marks_added_removed_modified_and_unchanged():
    left = {
        "files": [
            {"path": "README.md", "language": "markdown", "content": "# Old"},
            {"path": "src/train.py", "language": "python", "content": "print('old')\n"},
            {"path": "src/remove.py", "language": "python", "content": "gone\n"},
            {"path": "requirements.txt", "language": "text", "content": "torch\n"},
        ]
    }
    right = {
        "files": [
            {"path": "README.md", "language": "markdown", "content": "# New"},
            {"path": "src/train.py", "language": "python", "content": "print('old')\n"},
            {"path": "src/add.py", "language": "python", "content": "added\n"},
            {"path": "requirements.txt", "language": "text", "content": "torch\n"},
        ]
    }

    diff = ResearchPipelineService.diff_code_project_manifests(left, right, from_version=1, to_version=2)
    statuses = {item["path"]: item["status"] for item in diff["files"]}

    assert diff["summary"] == {"added": 1, "removed": 1, "modified": 1, "unchanged": 2}
    assert statuses["src/add.py"] == "added"
    assert statuses["src/remove.py"] == "removed"
    assert statuses["README.md"] == "modified"
    assert statuses["src/train.py"] == "unchanged"
    readme = next(item for item in diff["files"] if item["path"] == "README.md")
    assert "--- a/README.md" in readme["diff"]
    assert "+++ b/README.md" in readme["diff"]


def test_experiment_execution_pack_explains_missing_setup():
    service = ResearchIdeaWorkbenchService(_Session())
    idea = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        feasibility_score=7,
        referenced_papers={"paper_ids": []},
        evidence_json={"items": []},
        review_json={},
        experiment_plan={"dataset": "", "baselines": [], "metrics": [], "steps": []},
    )

    pack = service.build_experiment_execution_pack(idea, experiments=[])

    assert pack["readiness"]["status"] == "needs_setup"
    assert any(task["key"] == "dataset" and task["status"] == "missing" for task in pack["minimum_tasks"])
    assert "补齐：选择数据集" in pack["next_actions"]
    assert pack["feedback"]["count"] == 0


def test_experiment_execution_pack_recommends_feedback_iteration():
    service = ResearchIdeaWorkbenchService(_Session())
    idea_id = uuid4()
    idea = SimpleNamespace(
        id=idea_id,
        project_id=uuid4(),
        feasibility_score=8,
        referenced_papers={"paper_ids": ["p1", "p2"]},
        evidence_json={"items": [
            {"paper_id": "p1", "title": "Evidence A", "score": 0.9, "category": "seed"},
            {"paper_id": "p2", "title": "Evidence B", "score": 0.8, "category": "background"},
        ]},
        review_json={"adversarial_review": {"objections": ["需要跨数据集验证。"]}},
        experiment_plan={
            "dataset": "Charades-STA",
            "baselines": ["Strong baseline"],
            "metrics": ["mIoU"],
            "steps": ["Reproduce baseline", "Run proposal", "Ablation"],
        },
    )
    feedback = {
        "experiment_id": "exp-1",
        "idea_id": str(idea_id),
        "name": "first run",
        "dataset": "Charades-STA",
        "results": {"mIoU": 0.42},
        "notes": "Fails on long videos.",
    }

    pack = service.build_experiment_execution_pack(idea, experiments=[feedback])

    assert pack["readiness"]["status"] == "needs_iteration"
    assert pack["feedback"]["count"] == 1
    assert pack["feedback"]["has_results"] is True
    assert pack["feedback"]["latest"]["experiment_id"] == "exp-1"
    assert "根据实验反馈演化 Proposal" in pack["next_actions"]


def test_collection_sources_are_summarized_from_evidence():
    evidence = [
        {"paper_id": "p1", "collection_ids": ["c1"], "collection_names": ["Video Grounding"]},
        {"paper_id": "p2", "collection_ids": ["c1"], "collection_names": ["Video Grounding"]},
        {"paper_id": "p3"},
    ]
    evidence_map = {"collection_sources": [{"id": "c1", "name": "Video Grounding", "paper_count": 5}]}

    sources = ResearchIdeaWorkbenchService._collection_sources_for_evidence(evidence, evidence_map)

    assert sources == [{"id": "c1", "name": "Video Grounding", "evidence_count": 2}]


@pytest.mark.asyncio
async def test_candidate_review_sorts_by_explainable_weighted_score(monkeypatch):
    service = ResearchIdeaWorkbenchService(_Session())
    candidates = [
        {"title": "Strong idea", "hypothesis": "one"},
        {"title": "Weak idea", "hypothesis": "two"},
    ]

    async def fake_chat_json(_prompt):
        return {"reviews": [
            {
                "title": "Weak idea",
                "scores": {key: 3 for key in ("novelty", "evidence_grounding", "feasibility", "testability", "impact", "clarity")},
                "rationale": "Needs revision",
            },
            {
                "title": "Strong idea",
                "scores": {key: 9 for key in ("novelty", "evidence_grounding", "feasibility", "testability", "impact", "clarity")},
                "rationale": "Advance",
            },
        ]}

    monkeypatch.setattr(service, "_chat_json", fake_chat_json)
    reviewed = await service.review_candidates({}, {}, candidates)

    assert [candidate["title"] for candidate in reviewed] == ["Strong idea", "Weak idea"]
    assert reviewed[0]["score"] == 9
    assert reviewed[0]["review"]["rationale"] == "Advance"


@pytest.mark.asyncio
async def test_top_proposal_persists_evidence_review_and_minimum_experiment():
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    paper_id = str(uuid4())
    run = SimpleNamespace(id=uuid4(), project_id=uuid4())
    experiment = {"dataset": "Benchmark", "baselines": ["Base"], "metrics": ["Score"], "steps": ["Run"]}
    reviewed = [{
        "title": "Grounded proposal",
        "gap": "Current methods fail under distribution shift.",
        "hypothesis": "A calibrated module improves robustness.",
        "approach": "Add calibration and compare against the base model.",
        "evidence_ids": [paper_id],
        "minimum_experiment": experiment,
        "score": 8.6,
        "base_score": 9.0,
        "novelty_check": {"status": "likely_novel", "score": 0.9},
        "adversarial_review": {"verdict": "advance", "penalty": 0, "objections": []},
        "tree": {"round": 1, "operator": "strong_baseline", "parent_title": "Root"},
        "selection_rationale": "综合评分高且贡献新的数据集维度",
        "selection_score": 8.8,
        "diversity_facets": ["path:grounded", "dataset:benchmark"],
        "suppressed_duplicates": [{"title": "Duplicate", "reason": "diversity_near_duplicate"}],
        "gap_selection": {"selected_gap_titles": ["Gap A"], "focus_note": "prefer low compute"},
        "review": {
            "scores": {"novelty": 8, "evidence_grounding": 9, "feasibility": 9, "testability": 9, "impact": 8, "clarity": 8},
            "rationale": "The hypothesis is falsifiable.",
            "uncertainty": "Needs a second dataset.",
            "recommendation": "advance",
        },
    }]
    evidence = {
        "scope": "local_library",
        "seed": [{"paper_id": paper_id, "title": "Evidence", "category": "seed"}],
        "background": [],
        "inspiration": [],
    }

    ideas = await service.persist_top_proposals(run, reviewed, evidence, num_ideas=1)

    assert len(ideas) == 1
    assert ideas[0].title == "Grounded proposal"
    assert ideas[0].evidence_json["items"][0]["paper_id"] == paper_id
    assert ideas[0].review_json["aggregate_score"] == 8.6
    assert ideas[0].review_json["base_score"] == 9.0
    assert ideas[0].review_json["novelty_check"]["status"] == "likely_novel"
    assert ideas[0].review_json["adversarial_review"]["verdict"] == "advance"
    assert ideas[0].review_json["search_tree"]["operator"] == "strong_baseline"
    assert ideas[0].review_json["selection_score"] == 8.8
    assert ideas[0].review_json["diversity_facets"] == ["path:grounded", "dataset:benchmark"]
    assert ideas[0].review_json["suppressed_duplicates"][0]["title"] == "Duplicate"
    assert ideas[0].review_json["gap_selection"]["selected_gap_titles"] == ["Gap A"]
    assert ideas[0].experiment_plan == experiment


@pytest.mark.asyncio
async def test_external_evidence_degrades_when_one_source_fails(monkeypatch):
    from app.services.paper_search import arxiv_service, semantic_scholar_service

    async def failed_search(*_args, **_kwargs):
        raise RuntimeError("rate limited")

    async def arxiv_search(*_args, **_kwargs):
        return [SimpleNamespace(
            title="Recent External Evidence",
            abstract="A recent paper about robust evaluation.",
            year=2026,
            doi=None,
            arxiv_id="2606.00001",
            source_url="https://arxiv.org/abs/2606.00001",
        )]

    monkeypatch.setattr(semantic_scholar_service, "search", failed_search)
    monkeypatch.setattr(arxiv_service, "search", arxiv_search)
    evidence, errors = await ResearchIdeaWorkbenchService(_Session())._collect_external_evidence("robust evaluation")

    assert errors == {"semantic_scholar": "rate limited"}
    assert evidence[0]["paper_id"] == "ext:arxiv:2606.00001"
    assert evidence[0]["source"] == "arxiv"


@pytest.mark.asyncio
async def test_evolution_persists_child_and_preserves_parent(monkeypatch):
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    parent_id = uuid4()
    parent = SimpleNamespace(
        id=parent_id,
        project_id=uuid4(),
        generation_run_id=uuid4(),
        title="Parent proposal",
        description="Initial gap",
        hypothesis="Initial hypothesis",
        approach="Initial approach",
        review_json={"uncertainty": "Needs cross-dataset validation"},
        experiment_plan={"dataset": "Base", "baselines": [], "metrics": [], "steps": []},
        evidence_json={"scope": "local_library", "items": []},
        referenced_papers={"paper_ids": []},
    )
    project = SimpleNamespace(name="Reliable models", description="", keywords=[], metadata_json={})

    async def fake_chat_json(_prompt):
        return {
            "title": "Cross-dataset child proposal",
            "gap": "Generalization remains uncertain.",
            "hypothesis": "Cross-dataset calibration improves generalization.",
            "approach": "Evaluate calibration on two held-out datasets.",
            "evolution_rationale": "Adds explicit cross-dataset validation.",
        }

    async def fake_review(_brief, _evidence, candidates):
        return [{**candidates[0], "score": 8.1, "review": {
            "scores": {"novelty": 8, "evidence_grounding": 7, "feasibility": 9, "testability": 9, "impact": 8, "clarity": 8},
            "rationale": "More testable.",
            "uncertainty": "Dataset selection.",
            "recommendation": "advance",
        }}]

    monkeypatch.setattr(service, "_chat_json", fake_chat_json)
    monkeypatch.setattr(service, "review_candidates", fake_review)
    child = await service.evolve_idea(parent, project, focus="Improve generalization")

    assert child.parent_idea_id == parent_id
    assert child.title == "Cross-dataset child proposal"
    assert child.evolution_json["focus"] == "Improve generalization"
    assert child.evolution_json["round"] == 2
    assert child.evolution_json["rationale"] == "Adds explicit cross-dataset validation."
    assert parent.title == "Parent proposal"


@pytest.mark.asyncio
async def test_evolution_increments_existing_round_and_preserves_experiment_feedback(monkeypatch):
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    parent = SimpleNamespace(
        id=uuid4(), project_id=uuid4(), generation_run_id=uuid4(), title="Round two",
        description="Gap", hypothesis="Hypothesis", approach="Approach",
        review_json={}, experiment_plan={}, evidence_json={"scope": "local_library", "items": []},
        referenced_papers={"paper_ids": []}, evolution_json={"round": 2},
    )
    project = SimpleNamespace(name="Reliable models", description="", keywords=[], metadata_json={})
    feedback = {"experiment_id": "exp-1", "results": {"accuracy": 0.82}, "notes": "Fails on shift"}

    async def fake_chat_json(prompt):
        assert '"experiment_id": "exp-1"' in prompt
        return {"title": "Round three", "hypothesis": "Improved", "evolution_rationale": "Uses failure case."}

    async def fake_review(_brief, _evidence, candidates):
        return [{**candidates[0], "score": 8.0, "review": {
            "scores": {"novelty": 8, "evidence_grounding": 8, "feasibility": 8, "testability": 8, "impact": 8, "clarity": 8},
            "rationale": "Feedback-grounded.", "uncertainty": "", "recommendation": "advance",
        }}]

    monkeypatch.setattr(service, "_chat_json", fake_chat_json)
    monkeypatch.setattr(service, "review_candidates", fake_review)
    child = await service.evolve_idea(parent, project, experiment_feedback=feedback)

    assert child.evolution_json["round"] == 3
    assert child.evolution_json["experiment_feedback"]["experiment_id"] == "exp-1"


@pytest.mark.asyncio
async def test_proposal_review_package_fallback_persists_structured_guidance(monkeypatch):
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    idea = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        title="Sparse evidence proposal",
        description="Use retrieval traces to improve grounded answers.",
        hypothesis="Trace-aware retrieval reduces hallucination.",
        approach="Train a verifier on retrieval traces.",
        novelty="Links traces to answer reliability.",
        feasibility_score=7,
        novelty_score=8,
        review_json={"adversarial_review": {"objections": ["Novelty over existing RAG verifiers is unclear."]}},
        experiment_plan={"dataset": "", "baselines": [], "metrics": [], "steps": []},
        evidence_json={"items": [{"paper_id": "p1", "title": "Trace RAG", "score": 0.7}]},
        referenced_papers={"paper_ids": ["p1"]},
        evolution_json={},
    )
    project = SimpleNamespace(name="Grounded QA", description="", keywords=[])

    async def empty_chat_json(_prompt):
        return {}

    monkeypatch.setattr(service, "_chat_json", empty_chat_json)

    package = await service.build_proposal_review_package(idea, project)

    assert package["writing_readiness"] in {"needs_revision", "blocked"}
    assert "Novelty over existing RAG verifiers is unclear." in package["reviewer_objections"]
    assert package["revision_plan"]
    assert package["next_revision_focus"]
    assert idea.review_json["proposal_review"] == package
    assert session.commits == 1


@pytest.mark.asyncio
async def test_review_guided_revision_creates_child_with_review_provenance(monkeypatch):
    session = _Session()
    service = ResearchIdeaWorkbenchService(session)
    parent = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        title="Parent proposal",
        status="draft",
        review_json={"proposal_review": {
            "next_revision_focus": "Clarify novelty and add cross-dataset evaluation.",
            "revision_plan": ["Differentiate from RAG verifiers", "Add cross-dataset benchmark"],
            "reviewer_objections": ["Novelty is unclear"],
            "required_experiments": ["Cross-dataset evaluation"],
        }},
    )
    project = SimpleNamespace(name="Grounded QA", description="", keywords=[])
    child = SimpleNamespace(id=uuid4(), evolution_json={"rationale": "Sharper novelty."})
    captured = {}

    async def fake_evolve(idea, _project, *, focus="", **_kwargs):
        captured["idea"] = idea
        captured["focus"] = focus
        return child

    monkeypatch.setattr(service, "evolve_idea", fake_evolve)

    result = await service.revise_idea_from_review(parent, project, focus="Prioritize novelty.")

    assert result is child
    assert captured["idea"] is parent
    assert "Prioritize novelty." in captured["focus"]
    assert "Differentiate from RAG verifiers" in captured["focus"]
    assert child.evolution_json["source"] == "proposal_review"
    assert child.evolution_json["review_focus"] == "Clarify novelty and add cross-dataset evaluation."
    assert child.evolution_json["review_objections"] == ["Novelty is unclear"]
    assert child.evolution_json["required_experiments"] == ["Cross-dataset evaluation"]
    assert session.commits == 1


def test_version_comparison_reports_parent_child_changes():
    service = ResearchIdeaWorkbenchService(_Session())
    parent = SimpleNamespace(
        id=uuid4(),
        title="Parent proposal",
        status="draft",
        hypothesis="Old hypothesis",
        approach="Old approach",
        description="Old description",
        experiment_plan={"dataset": "A", "baselines": ["BERT"], "metrics": ["F1"], "steps": ["run"]},
        evidence_json={"items": [{"paper_id": "p1"}]},
        review_json={"aggregate_score": 7},
        feasibility_score=7,
        novelty_score=7,
        evolution_json={},
    )
    child = SimpleNamespace(
        id=uuid4(),
        title="Child proposal",
        status="draft",
        hypothesis="New hypothesis",
        approach="New approach",
        description="Old description",
        experiment_plan={"dataset": "A+B", "baselines": ["BERT", "RAG"], "metrics": ["F1"], "steps": ["run", "ablate"]},
        evidence_json={"items": [{"paper_id": "p1"}, {"paper_id": "p2"}]},
        review_json={"aggregate_score": 8, "proposal_review": {"writing_readiness": "needs_revision"}},
        feasibility_score=8,
        novelty_score=8,
        evolution_json={"rationale": "Adds stronger benchmark.", "source": "proposal_review", "review_focus": "Benchmark"},
    )

    comparison = service.compare_idea_versions(child, parent)

    assert comparison["has_parent"] is True
    assert comparison["parent_idea_id"] == str(parent.id)
    assert comparison["revision_rationale"] == "Adds stronger benchmark."
    assert comparison["review_source"]["source"] == "proposal_review"
    changed_fields = {item["field"] for item in comparison["changes"]}
    assert {"title", "hypothesis", "approach", "experiment_plan", "evidence_count"}.issubset(changed_fields)


def test_iteration_timeline_includes_proposal_review_event():
    service = ResearchPipelineService(_Session())
    idea = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        title="Reviewed proposal",
        status="draft",
        description="Description",
        hypothesis="Hypothesis",
        approach="Approach",
        feasibility_score=7,
        novelty_score=8,
        evidence_json={"items": [{"paper_id": "p1"}, {"paper_id": "p2"}]},
        referenced_papers={"paper_ids": ["p1", "p2"]},
        experiment_plan={"dataset": "D", "baselines": ["B"], "metrics": ["F1"], "steps": ["s1", "s2", "s3"]},
        review_json={"proposal_review": {
            "summary": "Needs one revision.",
            "contributions": ["Trace-aware evaluation"],
            "weakest_assumptions": ["Trace labels transfer"],
            "reviewer_objections": ["Novelty unclear"],
            "required_experiments": ["Cross-domain test"],
            "revision_plan": ["Add baseline"],
            "writing_readiness": "needs_revision",
            "next_revision_focus": "Add baseline",
        }},
        evolution_json={},
        parent_idea_id=None,
        discussion_log=[],
        created_at=None,
    )

    timeline = service.build_iteration_timeline(idea, SimpleNamespace(id=idea.project_id, name="Grounded QA", description="", keywords=[]))

    review_events = [event for event in timeline["events"] if event["type"] == "proposal_review"]
    assert len(review_events) == 1
    assert review_events[0]["title"] == "结构化审稿包"
    assert review_events[0]["details"]["reviewer_objections"] == ["Novelty unclear"]


def test_proposal_board_groups_review_blockers_and_child_versions():
    service = ResearchPipelineService(_Session())
    project = SimpleNamespace(id=uuid4(), name="Grounded QA", description="", keywords=[])
    parent_id = uuid4()
    parent = SimpleNamespace(
        id=parent_id,
        project_id=project.id,
        title="Parent proposal",
        status="draft",
        description="Description",
        hypothesis="Hypothesis",
        approach="Approach",
        feasibility_score=8,
        novelty_score=8,
        evidence_json={"items": [{"paper_id": "p1"}, {"paper_id": "p2"}]},
        referenced_papers={"paper_ids": ["p1", "p2"]},
        experiment_plan={"dataset": "D", "baselines": ["B"], "metrics": ["F1"], "steps": ["s1", "s2", "s3"]},
        review_json={"aggregate_score": 8},
        evolution_json={},
        parent_idea_id=None,
        discussion_log=[],
        created_at=None,
    )
    blocked = SimpleNamespace(
        id=uuid4(),
        project_id=project.id,
        title="Blocked proposal",
        status="draft",
        description="Description",
        hypothesis="Hypothesis",
        approach="Approach",
        feasibility_score=8,
        novelty_score=8,
        evidence_json={"items": [{"paper_id": "p1"}, {"paper_id": "p2"}]},
        referenced_papers={"paper_ids": ["p1", "p2"]},
        experiment_plan={"dataset": "D", "baselines": ["B"], "metrics": ["F1"], "steps": ["s1", "s2", "s3"]},
        review_json={"aggregate_score": 8, "proposal_review": {
            "summary": "Needs revision.",
            "reviewer_objections": ["Novelty unclear"],
            "required_experiments": ["Cross-domain test"],
            "writing_readiness": "needs_revision",
        }},
        evolution_json={},
        parent_idea_id=None,
        discussion_log=[],
        created_at=None,
    )
    child = SimpleNamespace(
        id=uuid4(),
        project_id=project.id,
        title="Child proposal",
        status="draft",
        description="Description",
        hypothesis="Hypothesis",
        approach="Approach",
        feasibility_score=8,
        novelty_score=8,
        evidence_json={"items": [{"paper_id": "p1"}, {"paper_id": "p2"}]},
        referenced_papers={"paper_ids": ["p1", "p2"]},
        experiment_plan={"dataset": "D", "baselines": ["B"], "metrics": ["F1"], "steps": ["s1", "s2", "s3"]},
        review_json={"aggregate_score": 8},
        evolution_json={"source": "proposal_review", "round": 2},
        parent_idea_id=parent_id,
        discussion_log=[],
        created_at=None,
    )

    board = service.build_proposal_progress_board(project, [parent, blocked, child])

    blocked_items = [item for group in board["groups"] if group["status"] == "review_revision" for item in group["items"]]
    parent_items = [item for group in board["groups"] for item in group["items"] if item["idea_id"] == str(parent.id)]
    assert blocked_items[0]["idea_id"] == str(blocked.id)
    assert blocked_items[0]["recommended_action"]["type"] == "review_revision"
    assert blocked_items[0]["signals"]["review_objection_count"] == 1
    assert parent_items[0]["signals"]["has_child_versions"] is True
    assert parent_items[0]["recommended_action"]["type"] == "version_compare"


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _ExperimentSession:
    def __init__(self, project):
        self.project = project
        self.commits = 0

    async def execute(self, _query):
        return _ScalarResult(self.project)

    async def commit(self):
        self.commits += 1


class _SequenceSession:
    def __init__(self, values):
        self.values = list(values)
        self.commits = 0

    async def execute(self, _query):
        return _ScalarResult(self.values.pop(0))

    async def commit(self):
        self.commits += 1


@pytest.mark.asyncio
async def test_experiment_log_stores_stable_id_and_linked_proposal():
    project = SimpleNamespace(metadata_json={})
    service = ExperimentService(_ExperimentSession(project))

    result = await service.log_experiment(
        str(uuid4()), "baseline", {}, "Benchmark", {"accuracy": 0.8}, "first run", "idea-1",
    )

    experiment = result["experiment"]
    assert experiment["experiment_id"]
    assert experiment["idea_id"] == "idea-1"
    assert experiment["results"] == {"accuracy": 0.8}


@pytest.mark.asyncio
async def test_external_evidence_import_associates_local_paper_and_updates_map(monkeypatch):
    project = SimpleNamespace(id=uuid4(), user_id=uuid4(), paper_ids=[])
    run = SimpleNamespace(evidence_map={
        "seed": [], "background": [], "inspiration": [{
            "paper_id": "ext:arxiv:2606.00001", "title": "External paper", "year": 2026,
            "arxiv_id": "2606.00001", "abstract_excerpt": "Evidence", "source": "arxiv",
        }],
    })
    local_paper = SimpleNamespace(id=uuid4())
    session = _SequenceSession([project, run])

    async def fake_ingest(_service, paper, auto_download=True):
        assert paper.arxiv_id == "2606.00001"
        assert auto_download is False
        return local_paper, True

    monkeypatch.setattr("app.api.research.PaperIngestionService.ingest_paper", fake_ingest)
    response = await import_external_evidence(
        str(project.id),
        ExternalEvidenceImportRequest(paper_id="ext:arxiv:2606.00001", auto_download=False),
        session,
        SimpleNamespace(id=project.user_id),
    )

    assert response["is_new"] is True
    assert response["local_paper_id"] in project.paper_ids
    assert run.evidence_map["inspiration"][0]["imported_paper_id"] == response["local_paper_id"]


def test_structured_response_parser_accepts_json_code_fence():
    payload = ResearchIdeaWorkbenchService._parse_json('```json\n{"gaps": [{"title": "Gap"}]}\n```')

    assert payload["gaps"][0]["title"] == "Gap"


def test_fallback_candidates_remain_diverse_after_deduplication():
    candidates = ResearchIdeaWorkbenchService._fallback_candidates(
        {"name": "Efficient multimodal models"},
        {"seed": [], "background": [], "inspiration": []},
        {"gaps": [{"title": "Efficiency boundary", "limitation": "Current methods are costly."}]},
        count=5,
    )

    unique, _duplicates = ResearchIdeaWorkbenchService.deduplicate_candidates(candidates)

    assert len(unique) >= 3


def test_research_project_delete_cascades_workbench_rows():
    project_ideas = ResearchProject.ideas.property
    project_runs = ResearchProject.idea_runs.property
    run_ideas = ResearchIdeaRun.ideas.property

    assert "delete" in project_ideas.cascade
    assert "delete-orphan" in project_ideas.cascade
    assert project_ideas.passive_deletes is True
    assert "delete" in project_runs.cascade
    assert "delete-orphan" in project_runs.cascade
    assert project_runs.passive_deletes is True
    assert run_ideas.passive_deletes is True
