"""Regression tests for the evidence-grounded Research Idea Workbench."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.research_idea_workbench import ResearchIdeaWorkbenchService
from app.services.digest_service import ExperimentService
from app.api.research import ExternalEvidenceImportRequest, import_external_evidence


class _Session:
    def __init__(self):
        self.commits = 0
        self.added = []

    async def commit(self):
        self.commits += 1

    async def refresh(self, _item):
        return None

    def add(self, item):
        self.added.append(item)


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


def test_candidate_tree_expansion_records_lineage():
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

    expanded, summary = service.expand_candidate_tree(candidates, rounds=2, beam_width=2)

    assert summary["root_count"] == 1
    assert summary["expanded_count"] == 3
    assert expanded[0]["tree"]["operator"] == "root"
    assert any(item["tree"]["parent_title"] == "Reliable grounding" for item in expanded[1:])
    assert any(item["tree"]["operator"] == "strong_baseline" for item in expanded)


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
