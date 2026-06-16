from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.services import chat_agent_tools
from app.services.chat_agent_tools import (
    ChatAgentRuntimeState,
    ChatToolDefinition,
    ChatToolObservation,
    ChatToolRegistry,
    default_chat_tool_registry,
)
from app.services.chat_tool_planner import (
    _default_planner_llm,
    build_planner_messages,
    parse_planner_decision,
    planner_tool_context_block,
    planner_tool_trace_payload,
    run_llm_tool_planner,
)


class EchoArgs(BaseModel):
    text: str


def test_parse_planner_decision_accepts_fenced_json():
    decision = parse_planner_decision(
        """```json
        {"actions":[{"tool":"search_library","arguments":{"query":"video","limit":2},"thought_summary":"search local"}],"final":false}
        ```"""
    )

    assert decision.actions[0].tool == "search_library"
    assert decision.actions[0].arguments["limit"] == 2


def test_parse_planner_decision_rejects_malformed_output():
    with pytest.raises(ValueError):
        parse_planner_decision("I should search the library first.")


def test_build_planner_messages_includes_tool_schemas_and_observations():
    registry = default_chat_tool_registry()
    messages = build_planner_messages(
        user_query="search local papers",
        registry=registry,
        conversation_context=[{"role": "user", "content": "hello"}],
        observations=[ChatToolObservation(tool="search_library", summary="found one", result_count=1)],
    )
    combined = "\n".join(item["content"] for item in messages)

    assert "search_library" in combined
    assert "found one" in combined
    assert "Return exactly one JSON object" in combined


def test_build_planner_messages_includes_library_action_tools():
    registry = default_chat_tool_registry()
    messages = build_planner_messages(
        user_query="read a local paper and add it to my project",
        registry=registry,
    )
    combined = "\n".join(item["content"] for item in messages)

    assert "read_pdf" in combined
    assert "add_to_folder" in combined
    assert "create_research_project" in combined


@pytest.mark.asyncio
async def test_default_planner_llm_uses_structured_output_for_openai_compatible(monkeypatch):
    captured = {}

    class FakeLLMService:
        active_provider = "openai-compatible"

        async def chat_completion_direct(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(content='{"actions":[],"final":true,"final_context_summary":"done"}')

    monkeypatch.setattr("app.services.chat_tool_planner.llm_service", FakeLLMService())

    raw = await _default_planner_llm([{"role": "user", "content": "plan"}])

    assert raw == '{"actions":[],"final":true,"final_context_summary":"done"}'
    assert captured["response_format"]["type"] == "json_schema"
    assert captured["response_format"]["json_schema"]["name"] == "chat_tool_planner_decision"
    assert "actions" in captured["response_format"]["json_schema"]["schema"]["properties"]


@pytest.mark.asyncio
async def test_planner_executes_valid_tool_action():
    async def _executor(args, state):
        return ChatToolObservation(
            tool="echo",
            status="completed",
            summary=args.text,
            result_count=1,
            context_blocks=[f"Echo: {args.text}"],
        )

    registry = ChatToolRegistry()
    registry.register(ChatToolDefinition(name="echo", label="Echo", args_model=EchoArgs, executor=_executor))

    async def _planner_llm(messages):
        return '{"actions":[{"tool":"echo","arguments":{"text":"one"},"thought_summary":"echo once"}],"final":false}'

    result = await run_llm_tool_planner(
        user_query="echo",
        state=ChatAgentRuntimeState(user_query="echo"),
        registry=registry,
        planner_llm=_planner_llm,
        max_rounds=1,
    )

    assert result.state.observations[0].status == "completed"
    assert "Echo: one" in planner_tool_context_block(result)
    assert planner_tool_trace_payload(result, registry)["workflow"] == "llm_tool_planner"


@pytest.mark.asyncio
async def test_planner_malformed_output_falls_back_to_deterministic_plan(monkeypatch):
    async def _fake_search(query, *, source, max_results, **kwargs):
        return [
            chat_agent_tools.PaperResult(
                title="Fallback Paper",
                authors=["A"],
                abstract="fallback",
                year=2026,
                arxiv_id="2601.00001",
                source="arxiv",
                metadata={"remote_id": "2601.00001"},
            )
        ]

    async def _planner_llm(messages):
        return "not json"

    monkeypatch.setattr(chat_agent_tools, "search_scholarly_papers", _fake_search)
    result = await run_llm_tool_planner(
        user_query="检索 arxiv 上 video grounding 论文",
        state=ChatAgentRuntimeState(user_query="检索 arxiv 上 video grounding 论文"),
        registry=default_chat_tool_registry(),
        planner_llm=_planner_llm,
        max_rounds=1,
    )

    assert result.fallback_used is True
    assert result.stop_reason == "fallback_used"
    assert any(ref["title"] == "Fallback Paper" for ref in result.state.references)


@pytest.mark.asyncio
async def test_planner_force_mode_falls_back_when_model_returns_no_actions(monkeypatch):
    async def _fake_search(query, *, source, max_results, **kwargs):
        return [
            chat_agent_tools.PaperResult(
                title="Forced Fallback Paper",
                authors=["A"],
                abstract="force fallback",
                year=2026,
                arxiv_id="2601.00002",
                source="arxiv",
                metadata={"remote_id": "2601.00002"},
            )
        ]

    async def _planner_llm(messages):
        return '{"actions":[],"final":true,"final_context_summary":"answer directly"}'

    monkeypatch.setattr(chat_agent_tools, "search_scholarly_papers", _fake_search)
    result = await run_llm_tool_planner(
        user_query="检索 arxiv 上 video grounding 论文",
        state=ChatAgentRuntimeState(user_query="检索 arxiv 上 video grounding 论文"),
        registry=default_chat_tool_registry(),
        planner_llm=_planner_llm,
        max_rounds=1,
        force_fallback=True,
    )
    trace = planner_tool_trace_payload(result, default_chat_tool_registry())

    assert result.fallback_used is True
    assert result.force_fallback_used is True
    assert result.tool_mode == "force"
    assert result.stop_reason == "fallback_used"
    assert trace["tool_mode"] == "force"
    assert trace["force_fallback_used"] is True
    assert any(ref["title"] == "Forced Fallback Paper" for ref in result.state.references)


@pytest.mark.asyncio
async def test_planner_auto_mode_does_not_fallback_when_model_returns_final_no_actions(monkeypatch):
    called = False

    async def _fake_search(query, *, source, max_results, **kwargs):
        nonlocal called
        called = True
        return []

    async def _planner_llm(messages):
        return '{"actions":[],"final":true,"final_context_summary":"answer directly"}'

    monkeypatch.setattr(chat_agent_tools, "search_scholarly_papers", _fake_search)
    result = await run_llm_tool_planner(
        user_query="检索 arxiv 上 video grounding 论文",
        state=ChatAgentRuntimeState(user_query="检索 arxiv 上 video grounding 论文"),
        registry=default_chat_tool_registry(),
        planner_llm=_planner_llm,
        max_rounds=1,
    )

    assert called is False
    assert result.fallback_used is False
    assert result.force_fallback_used is False
    assert result.tool_mode == "auto"
    assert result.stop_reason == "completed"


@pytest.mark.asyncio
async def test_planner_unknown_tool_is_rejected_without_fallback():
    async def _planner_llm(messages):
        return '{"actions":[{"tool":"missing","arguments":{},"thought_summary":"bad"}],"final":false}'

    result = await run_llm_tool_planner(
        user_query="do something",
        state=ChatAgentRuntimeState(user_query="do something"),
        registry=default_chat_tool_registry(),
        planner_llm=_planner_llm,
        max_rounds=1,
    )

    assert result.state.observations[0].status == "rejected"
    assert result.fallback_used is False


@pytest.mark.asyncio
async def test_planner_invalid_arguments_are_rejected():
    async def _planner_llm(messages):
        return '{"actions":[{"tool":"search_library","arguments":{},"thought_summary":"missing query"}],"final":false}'

    result = await run_llm_tool_planner(
        user_query="请在论文库检索",
        state=ChatAgentRuntimeState(user_query="请在论文库检索"),
        registry=default_chat_tool_registry(),
        planner_llm=_planner_llm,
        max_rounds=1,
    )

    assert result.state.observations[0].status == "rejected"
    assert result.stop_reason in {"rejected", "fallback_used"}


@pytest.mark.asyncio
async def test_planner_stops_at_round_budget():
    async def _executor(args, state):
        return ChatToolObservation(tool="echo", status="completed", summary=args.text)

    registry = ChatToolRegistry()
    registry.register(ChatToolDefinition(name="echo", label="Echo", args_model=EchoArgs, executor=_executor))

    async def _planner_llm(messages):
        return '{"actions":[{"tool":"echo","arguments":{"text":"again"},"thought_summary":"repeat"}],"final":false}'

    result = await run_llm_tool_planner(
        user_query="repeat",
        state=ChatAgentRuntimeState(user_query="repeat"),
        registry=registry,
        planner_llm=_planner_llm,
        max_rounds=1,
        max_tool_steps=3,
        enable_fallback=False,
    )

    assert result.stop_reason == "max_rounds"


@pytest.mark.asyncio
async def test_planner_import_waits_for_confirmation():
    async def _planner_llm(messages):
        return (
            '{"actions":[{"tool":"import_paper","arguments":{"source":"arxiv","remote_id":"2601.00001",'
            '"auto_download":false,"title":"arXiv:2601.00001"},"thought_summary":"import requested"}],"final":false}'
        )

    result = await run_llm_tool_planner(
        user_query="请导入 arXiv:2601.00001",
        state=ChatAgentRuntimeState(user_query="请导入 arXiv:2601.00001", user=SimpleNamespace(id="u1")),
        registry=default_chat_tool_registry(),
        planner_llm=_planner_llm,
        max_rounds=2,
    )

    assert result.stop_reason == "waiting_confirmation"
    assert result.state.observations[0].status == "waiting_confirmation"
    assert result.state.observations[0].details["confirmation_token"]
