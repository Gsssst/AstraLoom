"""写作助手闭环能力回归测试。"""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.latex_processor import latex_processor
from app.services.writing_service import WritingAssistantService
from app.services.writing_project_service import WritingProjectService


def _paper(**overrides):
    data = {
        "id": uuid4(),
        "title": "Video Grounding with Multimodal Large Language Models",
        "authors": ["Ada Researcher", "Bob Scientist"],
        "year": 2026,
        "arxiv_id": "2606.00001v1",
        "doi": None,
        "abstract": "This paper studies video grounding benchmarks and compares baseline methods for temporal localization.",
        "tags": ["video grounding", "benchmark"],
        "categories": [],
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.asyncio
async def test_recommend_citations_returns_role_and_match(monkeypatch):
    service = WritingAssistantService(SimpleNamespace())
    paper = _paper()

    async def fake_retrieve(_text, max_papers):
        return [(paper, 0.82)]

    monkeypatch.setattr(service, "retrieve_topic_papers", fake_retrieve)

    results = await service.recommend_citations(
        "compare video grounding baseline methods for multimodal models",
        top_k=3,
    )

    assert results[0]["role"] == "baseline_method"
    assert results[0]["role_label"] == "基线方法"
    assert results[0]["match_status"] in {"strong", "partial"}
    assert results[0]["paper_id"] == str(paper.id)
    assert results[0]["decision_label"].startswith("基线方法")
    assert results[0]["decision_confidence"] in {"high", "medium"}
    assert "基线" in results[0]["decision_action"] or "人工确认" in results[0]["decision_action"]


def test_citation_decision_marks_weak_support_as_risky():
    service = WritingAssistantService(SimpleNamespace())
    decision = service.build_citation_decision(
        {"role": "supporting_evidence", "role_label": "支持证据"},
        {"match_status": "weak", "match_label": "弱匹配"},
    )

    assert decision["decision_confidence"] == "low"
    assert "不建议直接引用" in decision["decision_warning"]
    assert decision["decision_action"] == "谨慎使用：先补证据或替换引用"


@pytest.mark.asyncio
async def test_related_work_table_contains_structured_rows(monkeypatch):
    service = WritingAssistantService(SimpleNamespace())
    paper = _paper()

    async def fake_retrieve(_topic, max_papers):
        return [(paper, 0.91)]

    monkeypatch.setattr(service, "retrieve_topic_papers", fake_retrieve)

    table = await service.generate_related_work_table("video grounding", max_papers=5)

    assert table["total_papers"] == 1
    assert table["rows"][0]["title"] == paper.title
    assert "证据角色" in table["markdown"]
    assert paper.title in table["markdown"]


def test_review_draft_sections_are_prefilled_from_rows():
    service = WritingProjectService(SimpleNamespace())
    paper_id = str(uuid4())
    sections = service._build_review_draft_sections(
        "video grounding",
        rows=[{
            "index": 1,
            "paper_id": paper_id,
            "title": "Grounded Video Understanding",
            "year": 2026,
            "contribution": "A grounded benchmark for video understanding.",
            "role_label": "支持证据",
            "comparison_point": "适合在评测指标上对比。",
        }],
        table={"markdown": "| table |"},
    )

    assert "video grounding" in sections["Abstract"]
    assert "Grounded Video Understanding" in sections["Related Work"]
    assert paper_id in sections["References"]


def test_submission_template_inspector_reads_zip_template():
    import io
    import zipfile

    archive_bytes = io.BytesIO()
    with zipfile.ZipFile(archive_bytes, "w") as archive:
        archive.writestr(
            "main.tex",
            "\\documentclass{article}\n\\usepackage{cvpr}\n\\begin{document}\n\\section{Introduction}\n\\end{document}",
        )
        archive.writestr("cvpr.sty", "% CVPR style file")

    inspection = latex_processor.inspect_submission_template("cvpr2026.zip", archive_bytes.getvalue())

    assert inspection["status"] == "ready"
    assert inspection["document_class"] == "article"
    assert inspection["style_files"] == ["cvpr.sty"]
    assert inspection["main_tex"] == "main.tex"
    assert "CVPR" in inspection["venue_hints"]


@pytest.mark.asyncio
async def test_bind_submission_profile_updates_project_metadata(monkeypatch):
    service = WritingProjectService(SimpleNamespace())
    project_id = str(uuid4())

    async def fake_get_project(_project_id, _user_id):
        return {
            "id": project_id,
            "title": "Video Grounding",
            "metadata_json": {"source": "manual"},
            "sections": [],
        }

    async def fake_update_project(_project_id, _user_id, **kwargs):
        return {
            "id": project_id,
            "metadata_json": kwargs["metadata_json"],
            "sections": [],
        }

    monkeypatch.setattr(service, "get_project", fake_get_project)
    monkeypatch.setattr(service, "update_project", fake_update_project)

    updated = await service.bind_submission_profile(
        project_id,
        "user-1",
        venue="CVPR",
        year="2026",
        template_inspection={
            "source_filename": "cvpr2026.zip",
            "status": "ready",
            "status_label": "已识别模板",
            "document_class": "article",
            "class_files": [],
            "style_files": ["cvpr.sty"],
            "venue_hints": ["CVPR"],
            "warnings": [],
        },
    )

    profile = updated["metadata_json"]["submission_profile"]

    assert profile["venue"] == "CVPR"
    assert profile["year"] == "2026"
    assert profile["template_source"] == "cvpr2026.zip"
    assert profile["style_files"] == ["cvpr.sty"]


@pytest.mark.asyncio
async def test_export_reference_list_uses_real_project_papers(monkeypatch):
    paper = _paper()

    class _Rows:
        def scalar_one_or_none(self):
            return paper

    class _Session:
        async def execute(self, _statement):
            return _Rows()

    service = WritingProjectService(_Session())

    async def fake_get_project(_project_id, _user_id):
        return {
            "metadata_json": {"recommended_paper_ids": [str(paper.id)]},
            "sections": [],
        }

    monkeypatch.setattr(service, "get_project", fake_get_project)

    references = await service.export_reference_list("project-1", "user-1")

    assert "[1]" in references
    assert paper.title in references
    assert "arXiv:2606.00001v1" in references


@pytest.mark.asyncio
async def test_export_readiness_flags_empty_sections_and_weak_evidence(monkeypatch):
    service = WritingProjectService(SimpleNamespace())

    async def fake_get_project(_project_id, _user_id):
        return {
            "id": "project-1",
            "title": "Video Grounding Survey",
            "metadata_json": {},
            "sections": [
                {"id": "s1", "title": "Introduction", "content": ""},
                {"id": "s2", "title": "Related Work", "content": "Video grounding needs evidence [1]."},
            ],
        }

    async def fake_get_evidence_cards(_project_id, _user_id):
        return {
            "cards": [],
            "coverage": {"total": 0, "local": 0, "external": 0, "bibtex_ready": 0},
        }

    async def fake_collect(_project):
        return []

    monkeypatch.setattr(service, "get_project", fake_get_project)
    monkeypatch.setattr(service, "get_evidence_cards", fake_get_evidence_cards)
    monkeypatch.setattr(service, "_collect_reference_papers", fake_collect)

    readiness = await service.build_export_readiness("project-1", "user-1")

    assert readiness["status"] == "incomplete"
    assert readiness["section_summary"]["empty"] == 1
    assert readiness["citation_summary"]["unmatched"] == 1
    assert readiness["warnings"]


@pytest.mark.asyncio
async def test_publication_package_contains_all_export_formats(monkeypatch):
    service = WritingProjectService(SimpleNamespace())

    async def fake_get_project(_project_id, _user_id):
        return {"id": "project-1", "title": "Video Grounding Survey", "sections": [], "metadata_json": {}}

    async def fake_markdown(_project_id, _user_id):
        return "# Video Grounding Survey"

    async def fake_latex(_project_id, _user_id):
        return "\\section{Introduction}"

    async def fake_bibtex(_project_id, _user_id):
        return "@article{video2026}"

    async def fake_references(_project_id, _user_id):
        return "[1] Video Grounding."

    async def fake_readiness(_project_id, _user_id):
        return {"status": "ready", "warnings": []}

    monkeypatch.setattr(service, "get_project", fake_get_project)
    monkeypatch.setattr(service, "export_to_markdown", fake_markdown)
    monkeypatch.setattr(service, "export_to_latex", fake_latex)
    monkeypatch.setattr(service, "export_to_bibtex", fake_bibtex)
    monkeypatch.setattr(service, "export_reference_list", fake_references)
    monkeypatch.setattr(service, "build_export_readiness", fake_readiness)

    package = await service.build_publication_package("project-1", "user-1")

    assert package["formats"]["markdown"]["content"].startswith("# Video")
    assert package["formats"]["latex"]["filename"].endswith(".tex")
    assert package["formats"]["bibtex"]["content"].startswith("@article")
    assert package["formats"]["references"]["content"].startswith("[1]")
    assert package["formats"]["docx"]["download_url"].endswith("format=docx")


@pytest.mark.asyncio
async def test_project_bibtex_export_uses_metadata(monkeypatch):
    paper = _paper()

    class _Rows:
        def scalar_one_or_none(self):
            return paper

    class _Session:
        async def execute(self, _statement):
            return _Rows()

    service = WritingProjectService(_Session())

    async def fake_get_project(_project_id, _user_id):
        return {
            "metadata_json": {"recommended_paper_ids": [str(paper.id)]},
            "sections": [],
        }

    monkeypatch.setattr(service, "get_project", fake_get_project)

    bibtex = await service.export_to_bibtex("project-1", "user-1")

    assert "@article" in bibtex
    assert paper.title in bibtex


@pytest.mark.asyncio
async def test_citation_match_endpoint_reports_local_support():
    from app.api.writing_v2 import CitationMatchRequest, check_citation_match

    paper = _paper()

    class _Rows:
        def scalar_one_or_none(self):
            return paper

    class _Session:
        async def execute(self, _statement):
            return _Rows()

    result = await check_citation_match(
        CitationMatchRequest(
            sentence="Video grounding benchmarks compare temporal localization baseline methods.",
            paper_id=str(paper.id),
        ),
        db=_Session(),
    )

    assert result["exists"] is True
    assert result["status"] in {"matched", "weak_match"}
    assert result["paper"]["title"] == paper.title


@pytest.mark.asyncio
async def test_create_review_draft_from_research_idea_preserves_evidence_metadata(monkeypatch):
    service = WritingProjectService(SimpleNamespace())
    local_paper_id = str(uuid4())
    project = SimpleNamespace(id=uuid4(), name="Video Grounding", description="Ground video events.")
    idea = SimpleNamespace(
        id=uuid4(),
        title="Temporal Evidence Grounding",
        description="Use grounded evidence for temporal localization.",
        hypothesis="Evidence-aware retrieval improves localization.",
        approach="Retrieve evidence and compare baselines.",
        novelty="Evidence-preserving writing loop.",
        evidence_json={"items": [{
            "paper_id": "ext:2606.00001",
            "imported_paper_id": local_paper_id,
            "title": "Grounding Video Reasoning",
            "year": 2026,
            "category": "seed",
            "score": 0.92,
            "relevance": "Core evidence for video grounding.",
            "arxiv_id": "2606.00001v1",
        }]},
        review_json={"scores": {"novelty": 8}, "rationale": "Good evidence", "uncertainty": "Needs stronger baselines"},
        experiment_plan={"dataset": "ActivityNet", "baselines": ["Baseline A"], "metrics": ["mIoU"], "steps": ["Run baseline"]},
    )
    captured = {}

    async def fake_create_project(**kwargs):
        captured["metadata"] = kwargs["metadata_json"]
        return {
            "id": "writing-project-1",
            "sections": [
                {"id": f"section-{index}", "title": title}
                for index, title in enumerate([
                    "Abstract", "Introduction", "Related Work",
                    "Related Work Comparison Table", "Research Gaps", "References",
                ])
            ],
        }

    async def fake_update_section(section_id, user_id, **kwargs):
        captured.setdefault("sections", {})[section_id] = kwargs["content"]
        return {}

    async def fake_get_project(project_id, user_id):
        return {"id": project_id, "metadata_json": captured["metadata"], "sections": []}

    monkeypatch.setattr(service, "create_project", fake_create_project)
    monkeypatch.setattr(service, "update_section", fake_update_section)
    monkeypatch.setattr(service, "get_project", fake_get_project)

    result = await service.create_review_draft_from_research_idea("user-1", project, idea)

    assert result["evidence_status"] == "sufficient"
    assert result["local_paper_count"] == 1
    assert captured["metadata"]["source"] == "research_idea"
    assert captured["metadata"]["source_idea_id"] == str(idea.id)
    assert captured["metadata"]["recommended_paper_ids"] == [local_paper_id]
    assert any("Grounding Video Reasoning" in content for content in captured["sections"].values())


@pytest.mark.asyncio
async def test_create_review_draft_from_research_idea_marks_weak_evidence(monkeypatch):
    service = WritingProjectService(SimpleNamespace())
    project = SimpleNamespace(id=uuid4(), name="Sparse Attention", description="")
    idea = SimpleNamespace(
        id=uuid4(),
        title="Adaptive Sparse Attention",
        description=None,
        hypothesis=None,
        approach=None,
        novelty=None,
        evidence_json={},
        review_json={},
        experiment_plan={},
    )
    captured = {}

    async def fake_create_project(**kwargs):
        captured["metadata"] = kwargs["metadata_json"]
        return {"id": "writing-project-2", "sections": [{"id": "section-rw", "title": "Related Work"}]}

    async def fake_update_section(section_id, user_id, **kwargs):
        captured["related_work"] = kwargs["content"]
        return {}

    async def fake_get_project(project_id, user_id):
        return {"id": project_id, "metadata_json": captured["metadata"], "sections": []}

    monkeypatch.setattr(service, "create_project", fake_create_project)
    monkeypatch.setattr(service, "update_section", fake_update_section)
    monkeypatch.setattr(service, "get_project", fake_get_project)

    result = await service.create_review_draft_from_research_idea("user-1", project, idea)

    assert result["evidence_status"] == "insufficient"
    assert result["evidence_count"] == 0
    assert captured["metadata"]["recommended_paper_ids"] == []
    assert "暂无可用证据论文" in captured["related_work"]


@pytest.mark.asyncio
async def test_writing_project_evidence_cards_normalize_local_and_external(monkeypatch):
    local_paper_id = str(uuid4())
    paper = _paper(id=local_paper_id, title="Local Evidence for Video Grounding")

    class _Rows:
        def scalar_one_or_none(self):
            return paper

    class _Session:
        async def execute(self, _statement):
            return _Rows()

    service = WritingProjectService(_Session())

    async def fake_get_project(_project_id, _user_id):
        return {
            "id": "project-1",
            "metadata_json": {
                "source": "research_idea",
                "evidence_items": [
                    {
                        "paper_id": "ext:2606.00001",
                        "imported_paper_id": local_paper_id,
                        "title": "Local Evidence for Video Grounding",
                        "year": 2026,
                        "category": "seed",
                        "relevance": "Core evidence for video grounding.",
                        "arxiv_id": "2606.00001v1",
                    },
                    {
                        "paper_id": "external:paper",
                        "title": "External Evidence",
                        "category": "background",
                        "abstract_excerpt": "External paper not imported yet.",
                    },
                ],
            },
        }

    monkeypatch.setattr(service, "get_project", fake_get_project)

    result = await service.get_evidence_cards("project-1", "user-1")

    assert result["coverage"]["total"] == 2
    assert result["coverage"]["local"] == 1
    assert result["cards"][0]["citation_marker"] == "[1]"
    assert result["cards"][0]["role_label"] == "核心证据"
    assert result["cards"][1]["local_status"] == "external"


@pytest.mark.asyncio
async def test_writing_project_section_citation_check_scores_local_support(monkeypatch):
    paper_id = str(uuid4())
    paper = _paper(
        id=paper_id,
        title="Video Grounding Benchmarks",
        abstract="Video grounding benchmarks compare temporal localization baseline methods.",
    )

    class _Rows:
        def scalar_one_or_none(self):
            return paper

    class _Session:
        async def execute(self, _statement):
            return _Rows()

    service = WritingProjectService(_Session())

    async def fake_get_cards(_project_id, _user_id):
        return {
            "cards": [{
                "index": 1,
                "citation_marker": "[1]",
                "title": paper.title,
                "paper_id": paper_id,
                "arxiv_id": paper.arxiv_id,
                "local_status": "local",
                "local_status_label": "已入库",
                "role_label": "支持证据",
            }]
        }

    monkeypatch.setattr(service, "get_evidence_cards", fake_get_cards)

    result = await service.check_section_citations(
        "project-1",
        "user-1",
        "Video grounding benchmarks compare temporal localization baseline methods [1].",
        section_id="section-1",
    )

    assert result["summary"]["total"] == 1
    assert result["checks"][0]["status"] in {"strong", "partial"}
    assert result["checks"][0]["card"]["title"] == paper.title
    assert result["checks"][0]["decision_label"]
    assert result["checks"][0]["decision_action"]


@pytest.mark.asyncio
async def test_writing_project_section_citation_check_marks_external_unchecked(monkeypatch):
    service = WritingProjectService(SimpleNamespace())

    async def fake_get_cards(_project_id, _user_id):
        return {
            "cards": [{
                "index": 1,
                "citation_marker": "[1]",
                "title": "External Evidence",
                "paper_id": None,
                "local_status": "external",
                "local_status_label": "未入库",
                "role_label": "背景资料",
            }]
        }

    monkeypatch.setattr(service, "get_evidence_cards", fake_get_cards)

    result = await service.check_section_citations(
        "project-1",
        "user-1",
        "The field still lacks robust grounding evidence [1].",
    )

    assert result["checks"][0]["status"] == "unchecked"
    assert result["summary"]["unchecked"] == 1
    assert "尚未导入本地论文库" in result["checks"][0]["explanation"]
    assert result["checks"][0]["decision_action"] == "先入库并补全文/补向量"
    assert "临时占位引用" in result["checks"][0]["decision_warning"]


@pytest.mark.asyncio
async def test_writing_section_quality_check_scores_ready_draft(monkeypatch):
    service = WritingProjectService(SimpleNamespace())

    async def fake_get_project(_project_id, _user_id):
        return {"id": "project-1", "title": "Video Grounding", "sections": []}

    monkeypatch.setattr(service, "get_project", fake_get_project)

    result = await service.analyze_section_quality(
        "project-1",
        "user-1",
        "Related Work",
        (
            "Video grounding methods increasingly rely on multimodal models to align temporal evidence with language claims [1]. "
            "Compared with baseline localization pipelines, recent benchmark results show that stronger evidence retrieval improves robustness. "
            "However, existing methods still leave a gap in long-video grounding and evaluation coverage.\n\n"
            "This section therefore compares prior work, evidence assumptions, and open limitations."
        ),
        section_id="section-1",
    )

    assert result["status"] == "ready"
    assert result["overall_score"] >= 78
    assert result["metrics"]["citation_count"] == 1
    assert all(item["status"] == "pass" for item in result["dimensions"])


@pytest.mark.asyncio
async def test_writing_section_quality_check_suggests_rewrite_actions(monkeypatch):
    service = WritingProjectService(SimpleNamespace())

    async def fake_get_project(_project_id, _user_id):
        return {"id": "project-1", "title": "Video Grounding", "sections": []}

    monkeypatch.setattr(service, "get_project", fake_get_project)

    result = await service.analyze_section_quality(
        "project-1",
        "user-1",
        "Introduction",
        "Video grounding is useful.",
    )

    assert result["status"] == "incomplete"
    assert result["overall_score"] < 45
    assert {item["key"] for item in result["rewrite_actions"]} >= {"claim", "evidence"}


@pytest.mark.asyncio
async def test_evidence_related_work_table_reports_coverage_warnings(monkeypatch):
    service = WritingProjectService(SimpleNamespace())

    async def fake_get_cards(_project_id, _user_id):
        return {
            "cards": [
                {
                    "citation_marker": "[1]",
                    "title": "Local Video Grounding",
                    "year": 2026,
                    "role_label": "核心证据",
                    "local_status": "local",
                    "local_status_label": "已入库",
                    "paper_id": str(uuid4()),
                    "arxiv_id": "2606.00001v1",
                    "doi": None,
                },
                {
                    "citation_marker": "[2]",
                    "title": "External Grounding Survey",
                    "year": 2025,
                    "role_label": "背景资料",
                    "local_status": "external",
                    "local_status_label": "未入库",
                    "paper_id": None,
                    "arxiv_id": "2501.00001v1",
                    "doi": None,
                },
            ],
            "coverage": {"total": 2, "local": 1, "external": 1, "bibtex_ready": 1},
        }

    monkeypatch.setattr(service, "get_evidence_cards", fake_get_cards)

    result = await service.build_evidence_related_work_table("project-1", "user-1")

    assert result["coverage"]["total"] == 2
    assert result["status"] == "weak_evidence"
    assert "Local Video Grounding" in result["markdown"]
    assert "External Grounding Survey" in result["markdown"]
    assert "证据提示" in result["markdown"]


@pytest.mark.asyncio
async def test_workbench_summary_prioritizes_next_actions(monkeypatch):
    service = WritingProjectService(SimpleNamespace())

    async def fake_get_project(_project_id, _user_id):
        return {
            "id": "project-1",
            "title": "Video Grounding Survey",
            "template_type": "survey",
            "progress": {"percentage": 20, "completed": 1, "total": 3, "total_words": 180},
            "metadata_json": {},
            "sections": [
                {"id": "s1", "title": "Introduction", "content": ""},
                {"id": "s2", "title": "Related Work", "content": "Video grounding needs evidence [1]."},
            ],
        }

    async def fake_readiness(_project_id, _user_id):
        return {
            "status": "incomplete",
            "status_label": "内容未完成",
            "warnings": ["有 1 个章节为空：Introduction", "尚未绑定官方投稿模板；内置结构模板不能保证当前年度会议格式。"],
            "section_summary": {
                "total": 2,
                "empty": 1,
                "short": 1,
                "total_words": 180,
                "empty_sections": ["Introduction"],
                "short_sections": ["Related Work"],
            },
            "evidence_coverage": {"total": 0, "local": 0, "external": 0, "bibtex_ready": 0},
            "citation_summary": {"mentions": 1, "unmatched": 1},
            "submission_profile": {
                "template_status": "missing",
                "status_label": "未绑定官方模板",
                "warnings": ["尚未上传或绑定官方投稿模板。"],
            },
        }

    async def fake_evidence(_project_id, _user_id):
        return {
            "evidence_status": "insufficient",
            "coverage": {"total": 0, "local": 0, "external": 0, "bibtex_ready": 0},
            "cards": [],
        }

    monkeypatch.setattr(service, "get_project", fake_get_project)
    monkeypatch.setattr(service, "build_export_readiness", fake_readiness)
    monkeypatch.setattr(service, "get_evidence_cards", fake_evidence)

    summary = await service.build_workbench_summary("project-1", "user-1")

    assert summary["stage"]["key"] == "drafting"
    assert summary["risk_level"] == "high"
    assert summary["progress"]["empty_sections"] == 1
    assert summary["evidence"]["status"] == "insufficient"
    assert summary["citations"]["unmatched"] == 1
    assert summary["submission"]["template_status"] == "missing"
    assert summary["next_actions"][0]["key"] == "fill-empty-section"
    assert any(action["key"] == "bind-submission-template" for action in summary["next_actions"])


@pytest.mark.asyncio
async def test_context_project_creation_stores_binding_metadata(monkeypatch):
    service = WritingProjectService(SimpleNamespace())
    captured = {}

    async def fake_resolve(**_kwargs):
        return {
            "writing_type": "paper",
            "target_venue": "CVPR",
            "target_year": "2026",
            "research_project_id": "research-1",
            "research_project_name": "Video Grounding",
            "description": "Ground videos in time and space.",
            "collection_ids": ["collection-1"],
            "collection_names": ["Video Grounding 核心论文"],
            "collection_sources": [{"id": "collection-1", "name": "Video Grounding 核心论文", "paper_count": 2}],
            "paper_ids": ["paper-1", "paper-2"],
        }

    async def fake_create_project(**kwargs):
        captured.update(kwargs)
        return {"id": "project-1", "title": kwargs["title"], "sections": []}

    async def fake_seed(_project_id, _user_id, _context):
        captured["seeded"] = True

    async def fake_get_project(_project_id, _user_id):
        return {"id": "project-1", "title": "Video Grounding Paper", "metadata_json": captured["metadata_json"], "sections": []}

    monkeypatch.setattr(service, "_resolve_writing_context", fake_resolve)
    monkeypatch.setattr(service, "create_project", fake_create_project)
    monkeypatch.setattr(service, "_seed_context_sections", fake_seed)
    monkeypatch.setattr(service, "get_project", fake_get_project)

    project = await service.create_project_from_context(
        user_id=str(uuid4()),
        title="Video Grounding Paper",
        template_type="cvpr",
        writing_type="paper",
        research_project_id="research-1",
        collection_ids=["collection-1"],
        target_venue="CVPR",
        target_year="2026",
    )

    metadata = captured["metadata_json"]
    assert metadata["source"] == "context_bound_writing_project"
    assert metadata["writing_context"]["research_project_name"] == "Video Grounding"
    assert metadata["recommended_paper_ids"] == ["paper-1", "paper-2"]
    assert metadata["submission_profile"]["venue"] == "CVPR"
    assert metadata["evidence_status"] == "sufficient"
    assert captured["seeded"] is True
    assert project["metadata_json"] == metadata
