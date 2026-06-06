import json

from app.api import chat_sessions


def test_active_model_stream_metadata_exposes_safe_status(monkeypatch):
    monkeypatch.setattr(
        chat_sessions.llm_service,
        "get_active_option",
        lambda: {
            "provider": chat_sessions.OPENAI_COMPATIBLE_PROVIDER,
            "label": "GPT-5.5（OpenAI 兼容）",
            "model": "gpt-5.5",
            "configured": True,
            "supports_thinking": False,
            "api_base": "https://secret.example.com/v1",
            "has_api_key": True,
            "api_key_env": "OPENAI_COMPATIBLE_API_KEY",
        },
    )

    metadata = chat_sessions._active_model_stream_metadata(
        rag_enabled=True,
        web_search_enabled=True,
        search_depth="deep",
        attachments=[
            chat_sessions.ChatImageAttachment(
                filename="vision.png",
                mime_type="image/png",
                data_url="data:image/png;base64,aGVsbG8=",
            )
        ],
    )
    serialized = json.dumps(metadata, ensure_ascii=False)

    assert metadata["provider"] == chat_sessions.OPENAI_COMPATIBLE_PROVIDER
    assert metadata["label"] == "GPT-5.5（OpenAI 兼容）"
    assert metadata["model"] == "gpt-5.5"
    assert metadata["configured"] is True
    assert metadata["capabilities"] == {
        "rag": True,
        "web_search": True,
        "thinking": False,
        "vision": True,
    }
    assert metadata["search_depth"] == "deep"
    assert metadata["image_attachments"] == 1
    assert "api_key" not in serialized
    assert "api_base" not in serialized
    assert "secret.example.com" not in serialized
