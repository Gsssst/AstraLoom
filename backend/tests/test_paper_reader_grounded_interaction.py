import pytest

from app.services.paper_chunk_service import PaperChunkService
from app.services import memory_service, report_service


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
    assert evidence[0].source_type == "table"
    assert evidence[0].page_start == 7
    assert "91.3" in evidence[0].text


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

    assert any(ref["evidence_type"] == "table" and ref["page"] == 7 for ref in evidence)
    assert "类型: 表格" in context[0]["content"]
    assert "图片占位只表示" in context[0]["content"]
