import pytest
import sys
import types

from app.services.paper_chunk_service import PaperChunkService
from app.services import document_visual_evidence, memory_service, report_service


def _paragraph(marker: str) -> str:
    return f"{marker} " + " ".join([f"{marker} evidence"] * 90)


def test_introduction_question_retrieves_only_introduction_section():
    full_text = "\n\n".join([
        "Abstract",
        _paragraph("abstract-marker"),
        "1 Introduction",
        _paragraph("intro-marker"),
        "2 Methods",
        _paragraph("method-marker"),
        "3 Experiments",
        _paragraph("experiment-marker"),
    ])

    chunks, scope = PaperChunkService.retrieve_chunks(
        full_text,
        "请解释一下这篇论文的 introduction",
        top_k=3,
    )

    assert scope == "section"
    assert chunks
    assert any("intro-marker" in chunk for chunk, _score in chunks)
    assert all("method-marker" not in chunk for chunk, _score in chunks)


def test_chinese_section_alias_routes_to_matching_section():
    full_text = "\n\n".join([
        "1 引言",
        _paragraph("intro-marker"),
        "2 方法",
        _paragraph("method-marker"),
        "3 结论",
        _paragraph("conclusion-marker"),
    ])

    chunks, scope = PaperChunkService.retrieve_chunks(
        full_text,
        "论文的方法是什么？",
        top_k=2,
    )

    assert scope == "section"
    assert chunks
    assert any("method-marker" in chunk for chunk, _score in chunks)
    assert all("intro-marker" not in chunk for chunk, _score in chunks)


def test_missing_requested_section_falls_back_to_document_retrieval():
    full_text = _paragraph("document-marker")

    chunks, scope = PaperChunkService.retrieve_chunks(
        full_text,
        "请解释 introduction",
        top_k=2,
    )

    assert scope == "document"
    assert chunks
    assert "document-marker" in chunks[0][0]


def test_page_aware_evidence_preserves_section_and_page_number():
    page_texts = [
        "1 Introduction\n" + _paragraph("intro-marker"),
        "2 Methods\n" + _paragraph("method-marker"),
        "3 Experiments\n" + _paragraph("experiment-marker"),
    ]

    evidence, scope = PaperChunkService.retrieve_evidence(
        "\n\n".join(page_texts),
        "请解释 method",
        top_k=2,
        page_texts=page_texts,
    )

    assert scope == "section"
    assert evidence
    assert evidence[0].section == "method"
    assert evidence[0].page_start == 2
    assert "method-marker" in evidence[0].text


def test_evidence_retrieval_suppresses_redundant_chunks():
    repeated = " ".join(["contrastive alignment improves retrieval"] * 70)
    full_text = "\n\n".join([
        repeated,
        repeated + " with a small wording change",
        " ".join(["temporal localization benchmark reports failure cases"] * 70),
    ])

    evidence, scope = PaperChunkService.retrieve_evidence(
        full_text,
        "contrastive alignment retrieval failure cases",
        top_k=2,
    )

    assert scope == "document"
    assert len(evidence) == 2
    assert not all("contrastive alignment" in item.text for item in evidence)


def test_pdf_table_rows_convert_to_markdown():
    markdown = report_service.table_to_markdown([
        ["Model", "Accuracy", "F1"],
        ["Baseline", "72.1", "70.8"],
        ["Ours", "81.4", "80.2"],
    ])

    assert "| Model | Accuracy | F1 |" in markdown
    assert "| Ours | 81.4 | 80.2 |" in markdown


def test_pdf_table_rows_are_not_truncated_before_evidence_packaging():
    table = [[f"Metric {i}" for i in range(1, 15)]]
    table.extend([[f"row-{row}-col-{col}" for col in range(1, 15)] for row in range(1, 46)])

    markdown = report_service.table_to_markdown(table)

    assert "Metric 14" in markdown
    assert "row-45-col-14" in markdown
    assert "Table truncated" not in markdown


def test_structured_table_quality_flags_low_fidelity_tables():
    low = report_service.StructuredPdfBlock(
        block_type="table",
        page=7,
        text=(
            "[PDF table, page 7, table 2]\n"
            "| Column 1 | Column 2 | Column 3 |\n"
            "| --- | --- | --- |\n"
            "|  |  |  |"
        ),
    )
    high = report_service.StructuredPdfBlock(
        block_type="table",
        page=8,
        text=(
            "[PDF table, page 8, table 1]\n"
            "| Model | C-Acc | EtF1 |\n"
            "| --- | --- | --- |\n"
            "| Ours | 80.9 | 53.5 |\n"
            "| Gemini | 74.1 | 61.1 |"
        ),
    )

    low_quality = report_service.structured_table_quality_from_blocks([low])
    mixed_quality = report_service.structured_table_quality_from_blocks([low, high])

    assert low_quality["quality"] == "low"
    assert low_quality["low_quality_table_count"] == 1
    assert any("表头" in warning or "不完整" in warning for warning in low_quality["warnings"])
    assert mixed_quality["quality"] == "low"
    assert mixed_quality["low_quality_table_count"] == 1


def test_structured_table_quality_keeps_compact_valid_tables_high_quality():
    compact = report_service.StructuredPdfBlock(
        block_type="table",
        page=6,
        text=(
            "[PDF table, page 6, table 1]\n"
            "| Reward Functions | C-Acc | EtF1 | tIoU | TF1 |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| RtIoU + RC-Acc + RCaption | +11.57 | +8.84 | +4.30 | +3.89 |"
        ),
    )

    quality = report_service.structured_table_quality_from_blocks([compact])

    assert quality["quality"] == "high"
    assert quality["low_quality_table_count"] == 0


def test_caption_blocks_are_page_aware():
    blocks = report_service.extract_caption_blocks(
        "Figure 2. Overall architecture of the multimodal encoder.\n"
        "It contains an image tower and a text tower.\n\n"
        "Table 3. Ablation results on retrieval benchmarks.",
        page_number=5,
    )

    assert len(blocks) == 2
    assert {block.metadata["caption_type"] for block in blocks} == {"figure_caption", "table_caption"}
    assert all(block.page == 5 for block in blocks)


def test_structured_table_evidence_is_retrieved_with_page_number():
    full_text = _paragraph("method-marker")
    structured_blocks = [{
        "type": "table",
        "page": 7,
        "source": "pdfplumber",
        "text": "[PDF table, page 7, table 1]\n| Model | Accuracy |\n| --- | --- |\n| Ours | 91.3 |",
        "metadata": {"table_index": 1},
    }]

    evidence, scope = PaperChunkService.retrieve_evidence(
        full_text,
        "表格里的 Accuracy 是多少？",
        top_k=1,
        structured_blocks=structured_blocks,
    )

    assert scope == "structured+document"
    assert evidence[0].source_type == "table_pack"
    assert evidence[0].page_start == 7
    assert "91.3" in evidence[0].text


def test_historical_visual_blocks_are_not_used_as_evidence():
    full_text = _paragraph("method-marker")
    structured_blocks = [{
        "type": "visual_summary",
        "page": 4,
        "source": "caption+page_render",
        "text": (
            "[PDF visual asset, page 4, kind figure, asset fig4]\n"
            "Caption: Figure 4. Method architecture diagram.\n"
            "Visual summary: The diagram shows the visual encoder, temporal grounding head, and language decoder."
        ),
        "metadata": {
            "asset_id": "fig4",
            "kind": "figure",
            "caption": "Figure 4. Method architecture diagram.",
            "has_visual_summary": True,
        },
    }]

    evidence, scope = PaperChunkService.retrieve_evidence(
        full_text,
        "请解释图4中的方法架构图",
        top_k=3,
        structured_blocks=structured_blocks,
    )

    assert scope == "document"
    assert evidence
    assert all(item.source_type != "visual_pack" for item in evidence)
    assert all("temporal grounding head" not in item.text for item in evidence)


def test_ready_document_visual_evidence_is_retrieved_for_figure_questions():
    full_text = _paragraph("method-marker")
    visual_blocks = [{
        "type": "visual_evidence",
        "page": 4,
        "source": "docling",
        "text": (
            "[PDF visual evidence, page 4, kind architecture, asset ve1]\n"
            "Caption: Figure 4. Method architecture diagram.\n"
            "Visual summary: The diagram shows the visual encoder, temporal grounding head, and language decoder."
        ),
        "metadata": {
            "asset_id": "ve1",
            "kind": "architecture",
            "caption": "Figure 4. Method architecture diagram.",
            "confidence": 0.82,
            "visual_evidence": True,
        },
    }]

    evidence, scope = PaperChunkService.retrieve_evidence(
        full_text,
        "请解释图4中的方法架构图",
        top_k=3,
        structured_blocks=visual_blocks,
    )

    assert scope == "visual+structured"
    assert evidence[0].source_type == "visual_evidence"
    assert evidence[0].page_start == 4
    assert "temporal grounding head" in evidence[0].text


def test_structured_extraction_builds_document_visual_evidence_items():
    extraction = report_service.StructuredPdfExtraction(
        source_path="/tmp/paper.pdf",
        page_count=4,
        parser="docling",
        blocks=[
            report_service.StructuredPdfBlock(
                block_type="caption",
                page=2,
                source="docling",
                text="[PDF caption, page 2] Figure 2. Architecture overview.",
                metadata={"caption_type": "figure_caption", "bbox": [10, 20, 100, 160]},
            ),
            report_service.StructuredPdfBlock(
                block_type="table",
                page=3,
                source="docling",
                text="| Model | Acc |\n| --- | --- |\n| Ours | 91 |",
                metadata={"table_index": 1, "quality": "high", "caption": "Table 1. Results"},
            ),
        ],
    )

    items = document_visual_evidence.visual_evidence_items_from_structured_extraction(extraction, "paper-1")
    payload = document_visual_evidence.visual_evidence_payload_from_items(
        source_path="/tmp/paper.pdf",
        parser="docling",
        page_count=4,
        items=items,
    )

    assert payload["version"] == document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION
    assert payload["status"] == "ready"
    assert len(payload["items"]) == 2
    assert {item["kind"] for item in payload["items"]} >= {"architecture", "table"}
    assert payload["items"][0]["bbox"] == [10.0, 20.0, 100.0, 160.0]


def test_visual_evidence_private_asset_token_resolves_only_inside_asset_root(monkeypatch, tmp_path):
    asset_root = tmp_path / "visual"
    asset_file = asset_root / "paper-1" / "crop.png"
    asset_file.parent.mkdir(parents=True)
    asset_file.write_bytes(b"png")
    outside_file = tmp_path / "outside.png"
    outside_file.write_bytes(b"png")
    monkeypatch.setattr(document_visual_evidence.settings, "PDF_VISUAL_EVIDENCE_ASSET_DIR", str(asset_root))
    token = document_visual_evidence.visual_asset_public_token(str(asset_file))
    outside_token = document_visual_evidence.visual_asset_public_token(str(outside_file))
    paper = types.SimpleNamespace(
        pdf_path="/tmp/paper.pdf",
        metadata_json={
            document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY: {
                "version": document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION,
                "source_path": "/tmp/paper.pdf",
                "status": "ready",
                "items": [
                    {"id": "v1", "kind": "figure", "page": 1, "status": "ready", "asset_path": str(asset_file)},
                    {"id": "v2", "kind": "figure", "page": 1, "status": "ready", "asset_path": str(outside_file)},
                ],
            }
        },
    )

    assert document_visual_evidence.resolve_visual_asset_path_from_paper(paper, token) == asset_file.resolve()
    assert document_visual_evidence.resolve_visual_asset_path_from_paper(paper, outside_token) is None


def test_visual_asset_route_requires_paper_scope_uuid():
    item = document_visual_evidence.VisualEvidenceItem(
        id="v1",
        kind="figure",
        asset_path="/private/crop.png",
        metadata={"document_scope": "550e8400-e29b-41d4-a716-446655440000"},
    )
    route = document_visual_evidence.visual_asset_route_for_item(item, item.asset_path)

    assert route.startswith("/api/papers/visual-evidence-assets/550e8400-e29b-41d4-a716-446655440000/")
    upload_item = document_visual_evidence.VisualEvidenceItem(
        id="v2",
        kind="figure",
        asset_path="/private/upload.png",
        metadata={"document_scope": "upload-abc"},
    )
    assert document_visual_evidence.visual_asset_route_for_item(upload_item, upload_item.asset_path) is None


def test_vision_json_normalization_handles_malformed_and_confidence():
    parsed = document_visual_evidence.parse_vision_json('```json\n{"kind":"table","markdown":"| A | B |","confidence":1.7}\n```')
    normalized = document_visual_evidence.normalize_vision_adapter_result(parsed, provider="openai-compatible", model="vision")

    assert normalized["status"] == "ready"
    assert normalized["kind"] == "table"
    assert normalized["markdown"] == "| A | B |"
    assert normalized["confidence"] == 1.0
    assert normalized["provider"] == "openai-compatible"
    assert document_visual_evidence.parse_vision_json("not json")["status"] == "invalid"


def test_section_first_table_question_keeps_structured_table_evidence():
    full_text = "\n\n".join([
        "1 Introduction",
        _paragraph("intro-marker"),
        "5 Experiments",
        _paragraph("experiment-marker"),
    ])
    structured_blocks = [
        {
            "type": "table",
            "page": 6,
            "source": "docling",
            "text": (
                "[PDF table, page 6, table 1]\n"
                "| Reward Functions | C-Acc | EtF1 |\n"
                "| --- | --- | --- |\n"
                "| RtIoU + RC-Acc + RCaption | +11.57 | +8.84 |"
            ),
            "metadata": {"table_index": 1},
        }
    ]

    evidence, scope = PaperChunkService.retrieve_evidence(
        full_text,
        "请基于实验表格说明 Caption reward 的贡献和 OMTG Bench 结果",
        top_k=4,
        structured_blocks=structured_blocks,
    )

    assert scope == "section+structured"
    assert any(item.source_type == "table_pack" and item.page_start == 6 for item in evidence)
    assert any("experiment-marker" in item.text for item in evidence)


def test_table_question_uses_adaptive_evidence_budget_and_packs_page_context():
    full_text = "\n\n".join([
        "1 Introduction",
        _paragraph("intro-marker"),
        "5 Experiments",
        "Table 3 shows the ablation of reward functions on OMTG Bench. " + "experiment context " * 50,
    ])
    page_texts = [
        "1 Introduction\n" + _paragraph("intro-marker"),
        "5 Experiments\nTable 3 shows the ablation of reward functions on OMTG Bench. " + "experiment context " * 50,
    ]
    long_table_rows = "\n".join(
        f"| RtIoU + RC-Acc + RCaption row {i} | +{i}.10 | +{i}.20 | +{i}.30 |"
        for i in range(1, 18)
    )
    structured_blocks = [
        {
            "type": "caption",
            "page": 2,
            "source": "pdfplumber",
            "text": "[PDF caption, page 2] Table 3. Ablation on reward functions on OMTG Bench.",
            "metadata": {"caption_type": "table_caption"},
        },
        {
            "type": "table",
            "page": 2,
            "source": "docling",
            "text": (
                "[PDF table]\n"
                "| Reward Functions | C-Acc | EtF1 | TF1 |\n"
                "| --- | --- | --- | --- |\n"
                f"{long_table_rows}"
            ),
            "metadata": {"table_index": 3},
        },
        {
            "type": "table",
            "page": 3,
            "source": "docling",
            "text": "[PDF table]\n| Model | C-Acc |\n| --- | --- |\n| Gemini-2.5-Pro | 74.1 |",
            "metadata": {"table_index": 4},
        },
    ]

    evidence, scope = PaperChunkService.retrieve_evidence(
        full_text,
        "请基于实验表格说明 Caption reward 的贡献、OMTG Bench 的结果和 baseline 对比",
        top_k=4,
        page_texts=page_texts,
        structured_blocks=structured_blocks,
    )

    assert scope == "section+structured"
    assert len(evidence) > 4
    first_pack = next(item for item in evidence if item.source_type == "table_pack" and item.page_start == 2)
    assert "### 表格" in first_pack.text
    assert "row 17" in first_pack.text
    assert "### 同页表格标题" in first_pack.text
    assert "### 同页正文说明" in first_pack.text
    assert first_pack.metadata["evidence_pack"] is True


def test_broad_experiment_question_uses_dossier_with_table_catalog_and_full_tables():
    full_text = "\n\n".join([
        "1 Introduction",
        _paragraph("intro-marker"),
        "4 Experiments",
        "We evaluate all baselines on OMTG Bench and report metrics, ablations, and efficiency. "
        + "experiment overview " * 80,
        "5 Conclusion",
        "The experiments show stronger accuracy with remaining limitations. " + "discussion " * 80,
    ])
    page_texts = [
        "1 Introduction\n" + _paragraph("intro-marker"),
        "4 Experiments\nWe evaluate all baselines on OMTG Bench and report metrics. " + "experiment overview " * 80,
        "4 Experiments\nAblation studies compare reward functions and efficiency. " + "ablation context " * 80,
        "5 Conclusion\nThe experiments show stronger accuracy with remaining limitations. " + "discussion " * 80,
    ]
    long_rows = "\n".join(
        f"| Ours-row-{row} | {80 + row}.1 | {70 + row}.2 | {row * 3}ms |"
        for row in range(1, 32)
    )
    structured_blocks = [
        {
            "type": "caption",
            "page": 2,
            "source": "pdfplumber",
            "text": "[PDF caption, page 2] Table 1. Main results on OMTG Bench.",
            "metadata": {"caption_type": "table_caption"},
        },
        {
            "type": "table",
            "page": 2,
            "source": "docling",
            "text": (
                "[PDF table]\n"
                "| Model | C-Acc | EtF1 | Latency |\n"
                "| --- | --- | --- | --- |\n"
                f"{long_rows}"
            ),
            "metadata": {"table_index": 1, "quality": "high"},
        },
        {
            "type": "caption",
            "page": 3,
            "source": "pdfplumber",
            "text": "[PDF caption, page 3] Table 2. Reward ablation results.",
            "metadata": {"caption_type": "table_caption"},
        },
        {
            "type": "table",
            "page": 3,
            "source": "docling",
            "text": (
                "[PDF table]\n"
                "| Reward Functions | C-Acc | EtF1 |\n"
                "| --- | --- | --- |\n"
                "| RtIoU | +4.10 | +2.20 |\n"
                "| RtIoU + RC-Acc + RCaption | +11.57 | +8.84 |"
            ),
            "metadata": {"table_index": 2, "quality": "high"},
        },
        {
            "type": "caption",
            "page": 4,
            "source": "pdfplumber",
            "text": "[PDF caption, page 4] Table 3. Efficiency comparison.",
            "metadata": {"caption_type": "table_caption"},
        },
        {
            "type": "table",
            "page": 4,
            "source": "docling",
            "text": (
                "[PDF table]\n"
                "| Method | Throughput |\n"
                "| --- | --- |\n"
                "| Dense | 120 tok/s |\n"
                "| Twilight | 211 tok/s |"
            ),
            "metadata": {"table_index": 3, "quality": "high"},
        },
    ]

    evidence, scope = PaperChunkService.retrieve_evidence(
        full_text,
        "请整体分析这篇论文的整个实验，所有表格、指标、baseline 和消融都要考虑",
        top_k=4,
        page_texts=page_texts,
        structured_blocks=structured_blocks,
    )

    assert scope == "experiment_dossier+structured"
    assert PaperChunkService.detect_evidence_strategy("请整体分析整个实验和所有表格") == "experiment"
    assert PaperChunkService.recommended_evidence_top_k("请整体分析整个实验和所有表格") == 24
    assert evidence[0].source_type == "experiment_dossier"
    catalog = next(item for item in evidence if item.source_type == "table_catalog")
    assert catalog.metadata["table_count"] == 3
    assert "Table 1. Main results" in catalog.text
    assert "Table 2. Reward ablation" in catalog.text
    assert "Table 3. Efficiency" in catalog.text
    assert any(item.source_type == "table_pack" and "Ours-row-31" in item.text for item in evidence)
    assert any(item.source_type == "text" and item.metadata.get("experiment_context") for item in evidence)


def test_table_evidence_lane_demotes_low_fidelity_tables():
    candidates = [
        PaperChunkService._structured_evidence_candidates([{
            "type": "table",
            "page": 1,
            "source": "pdfplumber",
            "text": "[PDF table]\n| Caption Reward OMTG | Column 2 |\n| --- | --- |\n|  |  |",
        }])[0],
        PaperChunkService._structured_evidence_candidates([{
            "type": "table",
            "page": 6,
            "source": "docling",
            "text": (
                "[PDF table]\n"
                "| Reward Functions | C-Acc | EtF1 |\n"
                "| --- | --- | --- |\n"
                "| RtIoU + RC-Acc + RCaption | +11.57 | +8.84 |"
            ),
        }])[0],
    ]
    for item in candidates:
        item.score = 0.8

    results = PaperChunkService._table_evidence_lane(
        candidates,
        "Caption reward 对 OMTG Bench 的 EtF1 贡献是多少？",
        top_k=2,
    )

    assert results[0].page_start == 6
    assert "+8.84" in results[0].text


def test_omtg_table_question_prefers_real_tables_over_figure_captions():
    candidates = PaperChunkService._structured_evidence_candidates([
        {
            "type": "caption",
            "page": 3,
            "source": "pdfplumber",
            "text": "[PDF caption, page 3] Figure 2. Overview of OMTG Bench data generation with Caption Reward.",
            "metadata": {"caption_type": "figure_caption"},
        },
        {
            "type": "caption",
            "page": 6,
            "source": "pdfplumber",
            "text": "[PDF caption, page 6] Table 3. Ablation on reward functions on OMTG Bench.",
            "metadata": {"caption_type": "table_caption"},
        },
        {
            "type": "table",
            "page": 6,
            "source": "docling",
            "text": (
                "[PDF table]\n"
                "| Reward Functions | C-Acc | EtF1 | tIoU | TF1 |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| RtIoU + RC-Acc + RCaption | +11.57 | +8.84 | +4.30 | +3.89 |"
            ),
            "metadata": {"table_index": 3},
        },
        {
            "type": "table",
            "page": 7,
            "source": "docling",
            "text": (
                "[PDF table]\n"
                "| Model | C-Acc | EtF1 |\n"
                "| --- | --- | --- |\n"
                "| Gemini-2.5-Pro | 74.1 | 61.1 |\n"
                "| OMTG-4B | 55.63 | 65.40 |"
            ),
            "metadata": {"table_index": 1},
        },
    ])

    results = PaperChunkService._table_evidence_lane(
        candidates,
        "请基于实验表格说明 Caption reward 的贡献、OMTG Bench 的结果和 baseline 对比",
        top_k=3,
    )

    assert results[0].source_type == "table"
    assert results[0].page_start == 6
    assert "RCaption" in results[0].text
    assert all("Figure 2" not in item.text for item in results[:2])


async def _identity_ensure_structured_pdf_content(paper):
    return report_service.structured_pdf_metadata_from_paper(paper)


@pytest.mark.asyncio
async def test_paper_context_includes_structured_table_and_caption_evidence(monkeypatch):
    from types import SimpleNamespace

    metadata = {
        report_service.PDF_STRUCTURED_METADATA_KEY: {
            "version": report_service.PDF_STRUCTURED_METADATA_VERSION,
            "source_path": "/tmp/paper.pdf",
            "parser": "test",
            "page_count": 8,
            "table_count": 1,
            "caption_count": 1,
            "visual_count": 0,
            "blocks": [
                {
                    "type": "table",
                    "page": 7,
                    "source": "pdfplumber",
                    "text": "[PDF table, page 7, table 1]\n| Model | Accuracy |\n| --- | --- |\n| Ours | 91.3 |",
                    "metadata": {"table_index": 1},
                },
                {
                    "type": "caption",
                    "page": 3,
                    "source": "pdfplumber",
                    "text": "[PDF caption, page 3] Figure 2. Multimodal encoder architecture.",
                    "metadata": {"caption_type": "figure_caption"},
                },
            ],
        }
    }
    paper = SimpleNamespace(
        id="paper-1",
        title="Structured paper",
        authors=["A"],
        year=2026,
        abstract="Abstract.",
        full_text="1 Introduction\n" + "plain evidence " * 120,
        arxiv_id="2606.00001",
        pdf_path="/tmp/paper.pdf",
        metadata_json=metadata,
    )

    monkeypatch.setattr(report_service, "extract_pdf_page_texts", lambda _path: [paper.full_text])
    monkeypatch.setattr(report_service, "ensure_structured_pdf_content", _identity_ensure_structured_pdf_content)

    context, evidence = await memory_service.build_paper_context_with_evidence(
        paper,
        "表格里的 Accuracy 和图 2 说明了什么？",
        history=[],
    )

    assert any(ref["evidence_type"] == "table_pack" and ref["page"] == 7 for ref in evidence)
    assert "类型: 表格证据包" in context[0]["content"]
    assert "证据类型可能包含正文、表格、视觉证据、视觉表格、图/表标题、OCR 文本或公式" in context[0]["content"]


@pytest.mark.asyncio
async def test_paper_context_labels_experiment_dossier_evidence(monkeypatch):
    from types import SimpleNamespace

    full_text = (
        "1 Introduction\n" + "intro text " * 80 + "\n\n"
        "4 Experiments\nWe evaluate all baselines and metrics on the benchmark. " + "experiment text " * 120 + "\n\n"
        "5 Conclusion\nThe evaluation confirms the main trend. " + "discussion text " * 80
    )
    metadata = {
        report_service.PDF_STRUCTURED_METADATA_KEY: {
            "version": report_service.PDF_STRUCTURED_METADATA_VERSION,
            "source_path": "/tmp/paper.pdf",
            "parser": "test",
            "page_count": 4,
            "table_count": 2,
            "caption_count": 2,
            "visual_count": 0,
            "blocks": [
                {
                    "type": "caption",
                    "page": 2,
                    "source": "pdfplumber",
                    "text": "[PDF caption, page 2] Table 1. Main benchmark results.",
                    "metadata": {"caption_type": "table_caption"},
                },
                {
                    "type": "table",
                    "page": 2,
                    "source": "docling",
                    "text": (
                        "[PDF table]\n"
                        "| Model | Accuracy | F1 |\n"
                        "| --- | --- | --- |\n"
                        "| Baseline | 72.1 | 70.8 |\n"
                        "| Ours | 81.4 | 80.2 |"
                    ),
                    "metadata": {"table_index": 1, "quality": "high"},
                },
                {
                    "type": "caption",
                    "page": 3,
                    "source": "pdfplumber",
                    "text": "[PDF caption, page 3] Table 2. Ablation results.",
                    "metadata": {"caption_type": "table_caption"},
                },
                {
                    "type": "table",
                    "page": 3,
                    "source": "docling",
                    "text": (
                        "[PDF table]\n"
                        "| Variant | Accuracy |\n"
                        "| --- | --- |\n"
                        "| w/o rerank | 76.4 |\n"
                        "| full | 81.4 |"
                    ),
                    "metadata": {"table_index": 2, "quality": "high"},
                },
            ],
        }
    }
    paper = SimpleNamespace(
        id="paper-2",
        title="Experiment paper",
        authors=["A"],
        year=2026,
        abstract="Abstract.",
        full_text=full_text,
        arxiv_id="2606.00002",
        pdf_path="/tmp/paper.pdf",
        metadata_json=metadata,
    )

    monkeypatch.setattr(
        report_service,
        "extract_pdf_page_texts",
        lambda _path: [
            "1 Introduction\n" + "intro text " * 80,
            "4 Experiments\nWe evaluate all baselines and metrics on the benchmark. " + "experiment text " * 80,
            "4 Experiments\nAblation results compare variants. " + "ablation text " * 80,
            "5 Conclusion\nThe evaluation confirms the main trend. " + "discussion text " * 80,
        ],
    )
    monkeypatch.setattr(report_service, "ensure_structured_pdf_content", _identity_ensure_structured_pdf_content)

    context, evidence = await memory_service.build_paper_context_with_evidence(
        paper,
        "请整体分析这篇论文的整个实验和所有表格",
        history=[],
    )

    assert any(ref["evidence_type"] == "experiment_dossier" for ref in evidence)
    assert any(ref["evidence_type"] == "table_catalog" and ref["metadata"]["table_count"] == 2 for ref in evidence)
    assert "类型: 实验证据档案" in context[0]["content"]
    assert "类型: 表格目录" in context[0]["content"]


def test_external_parser_payload_normalizes_common_block_shapes():
    extraction = report_service.structured_extraction_from_external_payload(
        {
            "page_count": 9,
            "blocks": [
                {"category": "Table", "markdown": "| Model | Acc |\n| --- | --- |\n| Ours | 91 |", "page": "4"},
                {"type": "figure_caption", "text": "Figure 2. Architecture.", "page_number": 5},
                {"kind": "formula", "content": "L = L_text + L_image", "page": 6},
            ],
        },
        source_path="/tmp/paper.pdf",
        parser="command",
    )

    assert extraction.page_count == 9
    assert [block.block_type for block in extraction.blocks] == ["table", "caption", "formula"]
    assert [block.page for block in extraction.blocks] == [4, 5, 6]
    assert all(block.source == "command" for block in extraction.blocks)


def test_low_quality_detection_flags_merged_numeric_cells():
    block = report_service.StructuredPdfBlock(
        block_type="table",
        page=3,
        text=(
            "| Task | Scores |\n"
            "| --- | --- |\n"
            "| GSM8K | 72.4 81.5 90.2 |\n"
            "| COQA | 61.1 63.2 64.9 |"
        ),
    )

    quality = report_service.structured_table_quality_from_blocks([block])

    assert quality["quality"] == "low"
    assert quality["merged_numeric_cell_count"] == 2
    assert "merged_numeric_cells" in quality["flags"]


def test_table_metadata_drives_evidence_text():
    block = report_service.StructuredPdfBlock(
        block_type="table",
        page=3,
        source="docling",
        text="bad merged table text",
        metadata={
            "table_index": 3,
            "caption": "Table 3. RULER",
            "headers": ["Task", "Accuracy"],
            "cells": [["GSM8K strict", "72.4"], ["COQA f1", "83.1"]],
        },
    )

    text = report_service.evidence_text_from_structured_block(block)

    assert "bad merged" not in text
    assert "Caption: Table 3. RULER" in text
    assert "| GSM8K strict | 72.4 |" in text
    assert "| COQA f1 | 83.1 |" in text


def test_parser_subprocess_environment_uses_huggingface_mirror(monkeypatch):
    monkeypatch.setattr(report_service.settings, "HF_ENDPOINT", "https://hf-mirror.com")
    monkeypatch.setattr(report_service.settings, "HF_HOME", "/cache/hf")
    monkeypatch.setattr(report_service.settings, "TRANSFORMERS_CACHE", "/cache/transformers")
    monkeypatch.setattr(report_service.settings, "SENTENCE_TRANSFORMERS_HOME", "/cache/st")

    env = report_service.parser_subprocess_environment()

    assert env["HF_ENDPOINT"] == "https://hf-mirror.com"
    assert env["HF_HOME"] == "/cache/hf"
    assert env["TRANSFORMERS_CACHE"] == "/cache/transformers"
    assert env["SENTENCE_TRANSFORMERS_HOME"] == "/cache/st"


def test_command_parser_success_normalizes_json(monkeypatch):
    captured = {}

    class Completed:
        returncode = 0
        stdout = b'{"blocks":[{"type":"ocr","text":"OCR text from figure","page":2}]}'
        stderr = b""

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["env"] = kwargs["env"]
        captured["timeout"] = kwargs["timeout"]
        return Completed()

    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_COMMAND", "fake-parser --json {pdf_path}")
    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_TIMEOUT_SECONDS", 12)
    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_MAX_OUTPUT_BYTES", 4096)
    monkeypatch.setattr(report_service.settings, "HF_ENDPOINT", "https://hf-mirror.com")
    monkeypatch.setattr(report_service.subprocess, "run", fake_run)

    extraction = report_service.extract_pdf_structured_content_with_command("/tmp/paper.pdf")

    assert captured["args"] == ["fake-parser", "--json", "/tmp/paper.pdf"]
    assert captured["timeout"] == 12
    assert captured["env"]["HF_ENDPOINT"] == "https://hf-mirror.com"
    assert extraction.blocks[0].block_type == "ocr"
    assert extraction.blocks[0].page == 2


def test_command_backend_failure_falls_back_to_lightweight(monkeypatch):
    fallback = report_service.StructuredPdfExtraction(
        source_path="/tmp/paper.pdf",
        page_count=1,
        parser="test-lightweight",
        blocks=[report_service.StructuredPdfBlock(block_type="caption", text="fallback caption", page=1)],
    )

    def failing_command(_path):
        raise RuntimeError("parser missing")

    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_BACKEND", "command")
    monkeypatch.setattr(report_service, "extract_pdf_structured_content_with_command", failing_command)
    monkeypatch.setattr(report_service, "extract_pdf_structured_content_lightweight", lambda _path: fallback)

    extraction = report_service.extract_pdf_structured_content("/tmp/paper.pdf")

    assert extraction.parser == "test-lightweight"
    assert extraction.blocks[0].text == "fallback caption"


class _FakeDoclingItem:
    def __init__(self, text, *, label=None, page_no=None):
        self.text = text
        self.label = label
        self.prov = [{"page_no": page_no}] if page_no else []


class _FakeDoclingTable:
    def __init__(self, markdown, *, page_no=None):
        self._markdown = markdown
        self.prov = [{"page_no": page_no}] if page_no else []

    def export_to_markdown(self):
        return self._markdown


class _FakeDoclingDocument:
    pages = {1: object(), 2: object(), 3: object()}

    def __init__(self):
        self.texts = [_FakeDoclingItem("Docling paragraph about multimodal fusion.", page_no=1)]
        self.tables = [_FakeDoclingTable("| Model | Score |\n| --- | --- |\n| Ours | 92 |", page_no=2)]
        self.pictures = [_FakeDoclingItem("Figure 3. Attention heatmap.", label="figure_caption", page_no=3)]

    def export_to_dict(self):
        return {
            "blocks": [
                {"type": "formula", "text": "L = L_v + L_t", "page": 2},
            ],
        }

    def export_to_markdown(self):
        return "# Docling Markdown\n\nFull document markdown."


def test_docling_document_normalizes_markdown_dict_and_collections():
    extraction = report_service.structured_extraction_from_docling_document(
        _FakeDoclingDocument(),
        source_path="/tmp/paper.pdf",
    )

    types_by_text = {block.text: block.block_type for block in extraction.blocks}

    assert extraction.parser == "docling"
    assert extraction.page_count == 3
    assert types_by_text["L = L_v + L_t"] == "formula"
    assert types_by_text["Docling paragraph about multimodal fusion."] == "text"
    assert types_by_text["| Model | Score |\n| --- | --- |\n| Ours | 92 |"] == "table"
    assert types_by_text["Figure 3. Attention heatmap."] == "caption"
    assert any(block.block_type == "docling_markdown" for block in extraction.blocks)


def test_docling_backend_success_uses_optional_python_api(monkeypatch):
    seen_paths = []

    class FakeConverter:
        def convert(self, path):
            seen_paths.append(path)
            return types.SimpleNamespace(document=_FakeDoclingDocument())

    fake_converter_module = types.ModuleType("docling.document_converter")
    fake_converter_module.DocumentConverter = FakeConverter
    fake_docling_module = types.ModuleType("docling")

    monkeypatch.setitem(sys.modules, "docling", fake_docling_module)
    monkeypatch.setitem(sys.modules, "docling.document_converter", fake_converter_module)

    extraction = report_service.extract_pdf_structured_content_with_docling("/tmp/paper.pdf")

    assert seen_paths == ["/tmp/paper.pdf"]
    assert extraction.parser == "docling"
    assert any(block.source == "docling" for block in extraction.blocks)


def test_docling_backend_failure_falls_back_to_lightweight(monkeypatch):
    fallback = report_service.StructuredPdfExtraction(
        source_path="/tmp/paper.pdf",
        page_count=1,
        parser="test-lightweight",
        blocks=[report_service.StructuredPdfBlock(block_type="caption", text="fallback caption", page=1)],
    )

    def failing_docling(_path):
        raise RuntimeError("docling missing")

    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_BACKEND", "docling")
    monkeypatch.setattr(report_service, "extract_pdf_structured_content_with_docling", failing_docling)
    monkeypatch.setattr(report_service, "extract_pdf_structured_content_lightweight", lambda _path: fallback)

    extraction = report_service.extract_pdf_structured_content("/tmp/paper.pdf")

    assert extraction.parser == "test-lightweight"
    assert extraction.blocks[0].text == "fallback caption"


def test_auto_backend_prefers_docling_when_available(monkeypatch):
    docling = report_service.StructuredPdfExtraction(
        source_path="/tmp/paper.pdf",
        page_count=1,
        parser="docling",
        blocks=[report_service.StructuredPdfBlock(
            block_type="table",
            text="| Model | Score |\n| --- | --- |\n| Ours | 92 |",
            page=1,
            source="docling",
        )],
    )

    def fail_lightweight(_path):
        raise AssertionError("auto should prefer docling before lightweight fallback")

    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_BACKEND", "auto")
    monkeypatch.setattr(report_service, "extract_pdf_structured_content_with_docling", lambda _path: docling)
    monkeypatch.setattr(report_service, "extract_pdf_structured_content_lightweight", fail_lightweight)

    extraction = report_service.extract_pdf_structured_content("/tmp/paper.pdf")

    assert extraction.parser == "docling"
    assert extraction.blocks[0].source == "docling"
