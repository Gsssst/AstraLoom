from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.services import chat_agent_tools
from app.services.chat_agent_tools import (
    ChatAgentRuntimeState,
    ChatAgentToolRuntime,
    ChatToolCall,
    ChatToolDefinition,
    ChatToolObservation,
    ChatToolRegistry,
    ImportPaperArgs,
    chat_tool_confirmation_token,
    default_chat_tool_registry,
    deterministic_chat_tool_plan,
)


class EchoArgs(BaseModel):
    text: str


def test_registry_schema_export_includes_side_effect_policy():
    registry = default_chat_tool_registry()
    schemas = {schema["name"]: schema for schema in registry.schemas()}

    assert {"search_papers", "search_library", "import_paper"} <= set(schemas)
    assert schemas["import_paper"]["side_effect"] is True
    assert schemas["search_papers"]["side_effect"] is False


@pytest.mark.asyncio
async def test_unknown_tool_is_rejected_with_allowed_tools():
    registry = default_chat_tool_registry()
    state = ChatAgentRuntimeState(user_query="test")

    observation = await registry.execute(ChatToolCall(tool="missing_tool"), state)

    assert observation.status == "rejected"
    assert "search_papers" in observation.details["allowed_tools"]


@pytest.mark.asyncio
async def test_invalid_arguments_do_not_execute():
    called = False

    async def _executor(args, state):
        nonlocal called
        called = True
        return ChatToolObservation(tool="echo", status="completed")

    registry = ChatToolRegistry()
    registry.register(ChatToolDefinition(name="echo", label="Echo", args_model=EchoArgs, executor=_executor))

    observation = await registry.execute(ChatToolCall(tool="echo", arguments={}), ChatAgentRuntimeState(user_query="x"))

    assert observation.status == "rejected"
    assert called is False


@pytest.mark.asyncio
async def test_runtime_stops_at_max_steps_and_records_trace():
    async def _executor(args, state):
        return ChatToolObservation(tool="echo", status="completed", summary=args.text, result_count=1)

    registry = ChatToolRegistry()
    registry.register(ChatToolDefinition(name="echo", label="Echo", args_model=EchoArgs, executor=_executor))
    runtime = ChatAgentToolRuntime(registry, max_steps=1)
    state = await runtime.run(
        ChatAgentRuntimeState(user_query="x"),
        [
            ChatToolCall(tool="echo", arguments={"text": "one"}),
            ChatToolCall(tool="echo", arguments={"text": "two"}),
        ],
    )

    assert state.stop_reason == "max_steps"
    assert len(state.observations) == 1
    assert [event.status for event in state.trace_events] == ["running", "completed"]


@pytest.mark.asyncio
async def test_side_effect_tool_waits_for_exact_confirmation():
    registry = default_chat_tool_registry()
    args = {
        "source": "arxiv",
        "remote_id": "2601.00001",
        "auto_download": False,
        "title": "arXiv:2601.00001",
    }
    normalized_args = ImportPaperArgs.model_validate(args).model_dump()

    observation = await registry.execute(
        ChatToolCall(tool="import_paper", arguments=args),
        ChatAgentRuntimeState(user_query="import"),
        allow_side_effects=False,
    )

    assert observation.status == "waiting_confirmation"
    assert observation.details["confirmation_token"] == chat_tool_confirmation_token("import_paper", normalized_args)


@pytest.mark.asyncio
async def test_search_papers_returns_references_and_context(monkeypatch):
    async def _fake_search(query, *, source, max_results, **kwargs):
        return [
            chat_agent_tools.PaperResult(
                title="Video Grounding Paper",
                authors=["A"],
                abstract="A useful paper.",
                year=2026,
                arxiv_id="2601.00001",
                source="arxiv",
                source_url="https://arxiv.org/abs/2601.00001",
                pdf_url="https://arxiv.org/pdf/2601.00001",
                metadata={"remote_id": "2601.00001"},
            )
        ]

    monkeypatch.setattr(chat_agent_tools, "search_scholarly_papers", _fake_search)

    state = await ChatAgentToolRuntime(default_chat_tool_registry()).run(
        ChatAgentRuntimeState(user_query="find papers"),
        [ChatToolCall(tool="search_papers", arguments={"query": "video grounding", "limit": 1})],
    )

    assert state.observations[0].status == "completed"
    assert state.references[0]["remote_ingest_token"]
    assert "Video Grounding Paper" in state.context_blocks[0]


@pytest.mark.asyncio
async def test_search_library_uses_rag_service(monkeypatch):
    paper = SimpleNamespace(
        id="paper-1",
        title="Local Paper",
        arxiv_id="2601.00002",
        year=2025,
        authors=["B"],
        abstract="local abstract",
        source_url="https://example.com/local",
        metadata_json={"pdf_url": "https://example.com/local.pdf"},
    )

    class FakeRAG:
        def __init__(self, db):
            self.db = db

        async def search_keyword_and_semantic(self, query, top_k):
            return [(paper, 0.92)]

    monkeypatch.setattr(chat_agent_tools, "RAGService", FakeRAG)

    runtime_state = ChatAgentRuntimeState(user_query="search library")
    runtime_state.db = object()
    state = await ChatAgentToolRuntime(default_chat_tool_registry()).run(
        runtime_state,
        [ChatToolCall(tool="search_library", arguments={"query": "local", "limit": 1})],
    )

    assert state.observations[0].status == "completed"
    assert state.references[0]["source"] == "local_library"
    assert state.references[0]["paper_id"] == "paper-1"


@pytest.mark.asyncio
async def test_confirmed_import_executes_ingest_and_save(monkeypatch):
    paper = SimpleNamespace(
        id="paper-1",
        title="Imported Paper",
        arxiv_id="2601.00003",
        year=2026,
        source_url="https://arxiv.org/abs/2601.00003",
        metadata_json={"pdf_url": "https://arxiv.org/pdf/2601.00003"},
    )
    calls = {"ingest": 0, "save": 0}

    class FakeIngestion:
        def __init__(self, db):
            self.db = db

        async def ingest_remote(self, source, remote_id, auto_download=False, imported_by_user=None):
            calls["ingest"] += 1
            return paper, True

    class FakeEnhance:
        def __init__(self, db):
            self.db = db

        async def save_paper(self, user_id, paper_id):
            calls["save"] += 1
            return SimpleNamespace(user_id=user_id, paper_id=paper_id)

    monkeypatch.setattr(chat_agent_tools, "PaperIngestionService", FakeIngestion)
    monkeypatch.setattr(chat_agent_tools, "PaperEnhanceService", FakeEnhance)

    args = ImportPaperArgs(source="arxiv", remote_id="2601.00003", auto_download=False).model_dump()
    token = chat_tool_confirmation_token("import_paper", args)
    runtime_state = ChatAgentRuntimeState(user_query="confirm import", user=SimpleNamespace(id="user-1"))
    runtime_state.db = object()
    state = await ChatAgentToolRuntime(default_chat_tool_registry()).run(
        runtime_state,
        [ChatToolCall(tool="import_paper", arguments=args, confirmation_token=token)],
        allow_side_effects=True,
    )

    assert state.observations[0].status == "completed"
    assert calls == {"ingest": 1, "save": 1}
    assert state.references[0]["paper_id"] == "paper-1"


def test_deterministic_import_plan_for_explicit_arxiv_id_waits_confirmation():
    calls = deterministic_chat_tool_plan("请导入 arXiv:2601.00003 到论文库")

    assert calls[0].tool == "import_paper"
    assert calls[0].arguments["source"] == "arxiv"
    assert calls[0].arguments["remote_id"] == "2601.00003"


def test_deterministic_library_plan_prefers_local_library_signal():
    calls = deterministic_chat_tool_plan("请在我的论文库里检索 video grounding")

    assert calls[0].tool == "search_library"
