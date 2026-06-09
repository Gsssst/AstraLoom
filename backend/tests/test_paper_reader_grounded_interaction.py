from app.services.paper_chunk_service import PaperChunkService


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
