import json
from types import SimpleNamespace

import pytest

from app.api import chat_sessions
from app.services import llm as llm_module


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
