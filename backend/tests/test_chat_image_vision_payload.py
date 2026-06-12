"""Regression tests for chat image attachment LLM payloads."""

from app.api import chat_sessions


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
