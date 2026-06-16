import json

import pytest

from app.services import llm as llm_module


class FakeStreamResponse:
    status_code = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def aiter_lines(self):
        events = [
            {"type": "response.reasoning_summary_text.delta", "delta": "先分析问题。"},
            {"type": "response.output_text.delta", "delta": "最终回答"},
            {"type": "response.completed"},
        ]
        for event in events:
            yield f"data: {json.dumps(event, ensure_ascii=False)}"
            yield ""


class FakeAsyncClient:
    captured = {}

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def stream(self, method, url, headers=None, json=None):
        self.__class__.captured = {
            "method": method,
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": self.kwargs.get("timeout"),
        }
        return FakeStreamResponse()


class FakeChatCompletionClient:
    captured = {}

    async def post(self, url, headers=None, json=None):
        self.__class__.captured = {
            "url": url,
            "headers": headers,
            "json": json,
        }
        return SimpleResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "{\"ok\":true}",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url_citation": {
                                        "title": "Source",
                                        "url": "https://example.com/source",
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
            }
        )


class SimpleResponse:
    status_code = 200
    text = ""

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_responses_input_converts_multimodal_chat_parts():
    result = llm_module._responses_input([
        {"role": "user", "content": [
            {"type": "text", "text": "看图"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,aGVsbG8="}},
        ]},
    ])

    assert result == [{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "看图"},
            {"type": "input_image", "image_url": "data:image/png;base64,aGVsbG8="},
        ],
    }]


@pytest.mark.asyncio
async def test_openai_responses_stream_maps_reasoning_summary_and_output(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_module.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-compatible")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    monkeypatch.setattr(llm_module.settings, "LLM_RUNTIME_CONFIG_PATH", str(tmp_path / "llm.json"))

    service = llm_module.LLMService()
    service.select_model("openai-compatible", "gpt-5.5")
    events = [
        event async for event in service.chat_stream_responses_with_reasoning_summary(
            messages=[{"role": "user", "content": "问题"}],
            max_tokens=128,
        )
    ]

    assert events == [
        {"type": "reasoning", "content": "先分析问题。"},
        {"type": "content", "content": "最终回答"},
    ]
    assert FakeAsyncClient.captured["method"] == "POST"
    assert FakeAsyncClient.captured["url"] == "https://llm.example.com/v1/responses"
    assert FakeAsyncClient.captured["headers"]["Authorization"] == "Bearer sk-compatible"
    assert FakeAsyncClient.captured["json"]["model"] == "gpt-5.5"
    assert FakeAsyncClient.captured["json"]["reasoning"] == {"effort": "medium", "summary": "auto"}
    assert FakeAsyncClient.captured["json"]["max_output_tokens"] == 128
    assert FakeAsyncClient.captured["json"]["stream"] is True


@pytest.mark.asyncio
async def test_openai_compatible_thinking_routes_to_responses(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-compatible")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    monkeypatch.setattr(llm_module.settings, "LLM_RUNTIME_CONFIG_PATH", str(tmp_path / "llm.json"))

    async def fake_responses_stream(**kwargs):
        yield {"type": "reasoning", "content": "摘要"}
        yield {"type": "content", "content": "回答"}

    service = llm_module.LLMService()
    service.select_model("openai-compatible", "gpt-5.5")
    monkeypatch.setattr(service, "chat_stream_responses_with_reasoning_summary", fake_responses_stream)

    events = [event async for event in service.chat_stream_with_thinking([{"role": "user", "content": "问题"}])]

    assert events == [
        {"type": "reasoning", "content": "摘要"},
        {"type": "content", "content": "回答"},
    ]


@pytest.mark.asyncio
async def test_direct_chat_completion_accepts_daya_extension_body(monkeypatch, tmp_path):
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-compatible")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(llm_module.settings, "OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    monkeypatch.setattr(llm_module.settings, "LLM_RUNTIME_CONFIG_PATH", str(tmp_path / "llm.json"))

    service = llm_module.LLMService()
    service.select_model("openai-compatible", "gpt-5.5")
    result = await service.chat_completion_direct(
        messages=[{"role": "user", "content": "return json"}],
        response_format={"type": "json_object"},
        web_search_options={"search_context_size": "medium"},
        client=FakeChatCompletionClient(),
    )

    assert FakeChatCompletionClient.captured["url"] == "https://llm.example.com/v1/chat/completions"
    assert FakeChatCompletionClient.captured["headers"]["Authorization"] == "Bearer sk-compatible"
    assert FakeChatCompletionClient.captured["json"]["model"] == "gpt-5.5"
    assert FakeChatCompletionClient.captured["json"]["response_format"] == {"type": "json_object"}
    assert FakeChatCompletionClient.captured["json"]["web_search_options"] == {"search_context_size": "medium"}
    assert result.content == "{\"ok\":true}"
    assert result.annotations[0]["url_citation"]["url"] == "https://example.com/source"
