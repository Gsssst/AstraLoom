import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import settings as settings_api


@pytest.mark.asyncio
async def test_api_config_connection_test_returns_safe_success(monkeypatch):
    async def fake_chat(**kwargs):
        assert kwargs["max_tokens"] == 32
        return "模型连接测试成功。"

    monkeypatch.setattr(
        settings_api.llm_service,
        "get_active_option",
        lambda: {
            "provider": "openai-compatible",
            "model": "gpt-5.5",
            "configured": True,
            "api_base": "https://secret.example.com/v1",
            "has_api_key": True,
        },
    )
    monkeypatch.setattr(settings_api.llm_service, "chat", fake_chat)

    response = await settings_api.test_api_config(SimpleNamespace(username="admin"))
    payload = response.model_dump()
    serialized = json.dumps(payload, ensure_ascii=False)

    assert payload["provider"] == "openai-compatible"
    assert payload["model"] == "gpt-5.5"
    assert payload["configured"] is True
    assert payload["ok"] is True
    assert payload["latency_ms"] >= 0
    assert payload["preview"] == "模型连接测试成功。"
    assert "api_key" not in serialized
    assert "api_base" not in serialized
    assert "secret.example.com" not in serialized


@pytest.mark.asyncio
async def test_api_config_connection_test_rejects_unconfigured_model(monkeypatch):
    monkeypatch.setattr(
        settings_api.llm_service,
        "get_active_option",
        lambda: {
            "provider": "openai-compatible",
            "model": "gpt-5.5",
            "configured": False,
        },
    )

    with pytest.raises(HTTPException) as exc:
        await settings_api.test_api_config(SimpleNamespace(username="admin"))

    assert exc.value.status_code == 400
    assert "尚未" in exc.value.detail
