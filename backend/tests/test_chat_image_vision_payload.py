"""Regression tests for chat image attachment LLM payloads."""

from app.api import chat_sessions


def test_chat_upload_limit_uses_50mb_configuration_for_files_and_data_urls():
    assert chat_sessions.MAX_CHAT_UPLOAD_BYTES == 50 * 1024 * 1024
    assert chat_sessions.MAX_CHAT_IMAGE_DATA_URL_LENGTH >= 69_905_196


def _request() -> chat_sessions.SendMessageRequest:
    return chat_sessions.SendMessageRequest(
        content="请读图",
        attachments=[
            chat_sessions.ChatImageAttachment(
                filename="vision.png",
                mime_type="image/png",
                data_url="data:image/png;base64,aGVsbG8=",
            )
        ],
    )


def test_openai_compatible_chat_request_replaces_current_user_with_image_parts(monkeypatch):
    monkeypatch.setattr(
        chat_sessions.llm_service,
        "get_active_option",
        lambda: {"provider": chat_sessions.OPENAI_COMPATIBLE_PROVIDER},
    )
    context = [
        {"role": "system", "content": "context"},
        {"role": "user", "content": "请读图"},
    ]

    result = chat_sessions._build_llm_context_for_request(context, _request())

    assert len(result) == 2
    assert result[-1]["role"] == "user"
    assert result[-1]["content"] == [
        {"type": "text", "text": "请读图"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,aGVsbG8="}},
    ]


def test_deepseek_chat_request_uses_text_only_image_fallback(monkeypatch):
    monkeypatch.setattr(
        chat_sessions.llm_service,
        "get_active_option",
        lambda: {"provider": "deepseek"},
    )

    result = chat_sessions._build_llm_context_for_request(
        [{"role": "user", "content": "请读图"}],
        _request(),
    )

    assert result[-1]["role"] == "system"
    assert "不支持视觉图片输入" in result[-1]["content"]
    assert "data:image" not in result[-1]["content"]


def test_uploaded_pdf_visual_context_reuses_message_references_without_reparse():
    from types import SimpleNamespace

    message = SimpleNamespace(
        references=[
            {
                "id": "PDF-V1",
                "type": "uploaded_pdf_visual_evidence",
                "source": "uploaded_pdf",
                "filename": "paper.pdf",
                "page": 3,
                "evidence_type": "visual_table",
                "snippet": "| Model | Acc |\n| Ours | 91 |",
                "metadata": {
                    "asset_id": "ve-table",
                    "kind": "table",
                    "caption": "Table 1. Main results.",
                    "confidence": 0.82,
                    "summary": "Main experimental results table.",
                },
            }
        ]
    )

    context, refs = chat_sessions._uploaded_pdf_visual_context_from_messages([message])

    assert len(refs) == 1
    assert "paper.pdf" not in context
    assert "Table 1. Main results." in context
    assert "| Ours | 91 |" in context


def test_uploaded_pdf_visual_context_formats_ready_table_evidence():
    visual_blocks = [
        {
            "type": "visual_table",
            "page": 4,
            "text": "[PDF visual table evidence, page 4]\n| Model | Acc |\n| Ours | 91 |",
            "metadata": {
                "asset_id": "upload-table-1",
                "kind": "table",
                "caption": "Table 1. Main results.",
                "confidence": 0.88,
                "visual_evidence": True,
            },
        }
    ]

    context = chat_sessions._format_uploaded_pdf_visual_context("paper.pdf", visual_blocks)
    refs = chat_sessions._uploaded_pdf_visual_references("paper.pdf", visual_blocks)

    assert "[PDF 视觉/表格证据: paper.pdf]" in context
    assert "Table 1. Main results." in context
    assert "| Ours | 91 |" in context
    assert refs[0]["type"] == "uploaded_pdf_visual_evidence"
    assert refs[0]["page"] == 4
    assert refs[0]["metadata"]["asset_id"] == "upload-table-1"


def test_uploaded_pdf_text_only_fallback_warns_against_unseen_visual_claims():
    context = chat_sessions._format_uploaded_pdf_visual_context("scan.pdf", [])

    assert "没有 ready 的图像/表格视觉证据" in context
    assert "只能基于已提取文本回答" in context
    assert "不能描述未解析的视觉细节" in context


def test_uploaded_pdf_visual_asset_routes_remain_private_to_paper_scope():
    from app.services import document_visual_evidence

    item = document_visual_evidence.VisualEvidenceItem(
        id="upload-table",
        kind="table",
        asset_path="/private/visual-evidence/upload-scope/table.png",
        metadata={"document_scope": "upload-scope"},
    )

    assert document_visual_evidence.visual_asset_route_for_item(item, item.asset_path) is None
