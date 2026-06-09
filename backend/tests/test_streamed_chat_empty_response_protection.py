import json
from types import SimpleNamespace

import pytest

from app.api import chat_sessions
from app.api import settings as settings_api
from app.services import llm as llm_module
from app.services.usage_tracker import UsageTracker, set_usage_user


def _chunk(*, content=None, reasoning_content=None):
    delta = SimpleNamespace(content=content, reasoning_content=reasoning_content)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def _stream(chunks):
    async def generate():
        for chunk in chunks:
            yield chunk

    return generate()


@pytest.mark.asyncio
async def test_reasoning_only_stream_retries_with_larger_token_budget(monkeypatch):
    calls = []

    async def _fake_completion(**kwargs):
        calls.append(kwargs["max_tokens"])
        if len(calls) == 1:
            return _stream([_chunk(reasoning_content="thinking")])
        return _stream([_chunk(content="visible answer")])

    monkeypatch.setattr(llm_module.litellm, "acompletion", _fake_completion)

    service = llm_module.LLMService()
    tokens = [token async for token in service.chat_stream([{"role": "user", "content": "question"}])]

    assert calls == [llm_module.DEFAULT_MAX_TOKENS, llm_module.LARGE_MAX_TOKENS]
    assert tokens == ["visible answer"]


@pytest.mark.asyncio
async def test_empty_stream_raises_after_single_retry(monkeypatch):
    calls = []

    async def _fake_completion(**kwargs):
        calls.append(kwargs["max_tokens"])
        return _stream([])

    monkeypatch.setattr(llm_module.litellm, "acompletion", _fake_completion)

    service = llm_module.LLMService()
    with pytest.raises(RuntimeError, match="模型未返回可展示内容"):
        _ = [token async for token in service.chat_stream([{"role": "user", "content": "question"}])]

    assert calls == [
        llm_module.DEFAULT_MAX_TOKENS,
        llm_module.LARGE_MAX_TOKENS,
        llm_module.MAX_MAX_TOKENS,
    ]


def test_stream_event_json_preserves_multiline_content():
    event = chat_sessions._stream_event("content", "first line\nsecond line")
    payload = json.loads(event.removeprefix("data: ").removesuffix("\n\n"))

    assert payload == {"type": "content", "content": "first line\nsecond line"}


def test_stream_failure_content_replaces_blank_reply_with_visible_fallback():
    full_content, appended = chat_sessions._stream_failure_content("")

    assert full_content == chat_sessions.EMPTY_STREAM_FALLBACK
    assert appended == chat_sessions.EMPTY_STREAM_FALLBACK


def test_llm_service_builds_openai_compatible_kwargs(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-compatible")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    monkeypatch.setattr(llm_module.settings, "LLM_RUNTIME_CONFIG_PATH", str(tmp_path / "llm.json"))

    service = llm_module.LLMService()
    selected = service.select_model("openai-compatible", "gpt-5.5")

    assert selected["provider"] == "openai-compatible"
    assert selected["configured"] is True
    assert service._get_kwargs() == {
        "model": "openai/gpt-5.5",
        "api_key": "sk-compatible",
        "api_base": "https://llm.example.com/v1",
    }


def test_llm_service_uses_provider_specific_paper_chat_limits(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_module.settings, "DEEPSEEK_API_KEY", "sk-deepseek")
    monkeypatch.setattr(llm_module.settings, "DEEPSEEK_API_BASE", "https://api.deepseek.com")
    monkeypatch.setattr(llm_module.settings, "DEEPSEEK_MODEL", "deepseek-v4-pro")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-compatible")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    monkeypatch.setattr(llm_module.settings, "LLM_RUNTIME_CONFIG_PATH", str(tmp_path / "llm.json"))

    service = llm_module.LLMService()

    assert service.paper_chat_max_tokens() == llm_module.DEEPSEEK_MAX_OUTPUT_TOKENS

    service.select_model("openai-compatible", "gpt-5.5")

    assert service.paper_chat_max_tokens() == llm_module.OPENAI_COMPATIBLE_MAX_OUTPUT_TOKENS
    assert service._clamp_output_tokens(999_999) == llm_module.OPENAI_COMPATIBLE_MAX_OUTPUT_TOKENS


def test_llm_service_rejects_unconfigured_provider_without_changing_selection(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_module.settings, "DEEPSEEK_API_KEY", "sk-deepseek")
    monkeypatch.setattr(llm_module.settings, "DEEPSEEK_API_BASE", "https://api.deepseek.com")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "")
    monkeypatch.setattr(llm_module.settings, "LLM_RUNTIME_CONFIG_PATH", str(tmp_path / "llm.json"))

    service = llm_module.LLMService()

    with pytest.raises(ValueError, match="API Base"):
        service.select_model("openai-compatible", "gpt-5.5")

    assert service.get_active_option()["provider"] == "deepseek"


@pytest.mark.asyncio
async def test_llm_usage_records_active_model(monkeypatch, tmp_path):
    captured = []

    async def fake_log_usage(**kwargs):
        captured.append(kwargs)

    monkeypatch.setattr(UsageTracker, "log_usage", fake_log_usage)
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-compatible")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    monkeypatch.setattr(llm_module.settings, "LLM_RUNTIME_CONFIG_PATH", str(tmp_path / "llm.json"))
    set_usage_user(None)

    service = llm_module.LLMService()
    service.select_model("openai-compatible", "gpt-5.5")
    await service._log_usage(prompt_tokens=1, completion_tokens=2, total_tokens=3)

    assert captured[0]["model"] == "gpt-5.5"


@pytest.mark.asyncio
async def test_settings_api_config_lists_models_without_keys(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-compatible")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    monkeypatch.setattr(llm_module.settings, "LLM_RUNTIME_CONFIG_PATH", str(tmp_path / "llm.json"))
    monkeypatch.setattr(settings_api.llm_service, "runtime_config_path", str(tmp_path / "llm.json"))

    response = await settings_api.get_api_config(SimpleNamespace(id="user"))
    payload = response.model_dump()

    assert any(item["provider"] == "openai-compatible" for item in payload["options"])
    assert "sk-compatible" not in json.dumps(payload)
    assert payload["provider"] == "deepseek"


@pytest.mark.asyncio
async def test_settings_api_update_switches_openai_compatible_model(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-compatible")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    monkeypatch.setattr(settings_api.llm_service, "runtime_config_path", str(tmp_path / "llm.json"))

    response = await settings_api.update_api_config(
        settings_api.UpdateApiConfigRequest(provider="openai-compatible", model="gpt-5.5"),
        SimpleNamespace(username="admin"),
    )

    assert response.provider == "openai-compatible"
    assert response.model == "gpt-5.5"
    assert response.configured is True
