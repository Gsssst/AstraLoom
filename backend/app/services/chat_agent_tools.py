"""Shared chat agent tool runtime.

This module keeps the agent loop small and explicit: registered tools expose
typed schemas, every call is validated before execution, and mutation tools are
blocked until the user confirms the exact pending action.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import logging
import re
from uuid import UUID
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.paper import Folder, Paper, PaperFolderItem, UserPaper
from app.db.models.research import ResearchProject
from app.services.paper_enhance import PaperEnhanceService
from app.services.paper_ingestion import PaperIngestionService
from app.services.paper_search import (
    PaperResult,
    create_remote_ingest_token,
    read_remote_ingest_token,
    search_scholarly_papers,
)
from app.services.paper_chunk_service import PaperChunkService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

ChatToolStatus = Literal[
    "planned",
    "running",
    "completed",
    "failed",
    "skipped",
    "rejected",
    "waiting_confirmation",
    "available",
]

TOOL_CONTEXT_MAX_CHARS = 9000
TOOL_RESULT_ABSTRACT_CHARS = 700
CHAT_TOOL_MAX_RESULTS = 20


class ChatToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    thought_summary: str = ""
    call_id: str | None = None
    confirmation_token: str | None = None


class ChatToolObservation(BaseModel):
    tool: str
    status: ChatToolStatus = "completed"
    summary: str = ""
    result_count: int = 0
    references: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    context_blocks: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class ChatToolTraceEvent(BaseModel):
    id: str
    tool: str
    label: str
    status: ChatToolStatus
    summary: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class ChatAgentRuntimeState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_query: str
    db: AsyncSession | None = None
    user: Any = None
    session_id: str | None = None
    observations: list[ChatToolObservation] = Field(default_factory=list)
    trace_events: list[ChatToolTraceEvent] = Field(default_factory=list)
    references: list[dict[str, Any]] = Field(default_factory=list)
    context_blocks: list[str] = Field(default_factory=list)
    stop_reason: str = ""


class SearchPapersArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=8, ge=1, le=CHAT_TOOL_MAX_RESULTS)
    source: Literal["arxiv", "arxiv_enriched", "scholarly", "semantic_scholar", "openalex", "google_scholar"] = "arxiv_enriched"
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)
    sort_by: Literal["relevance", "date"] = "relevance"


class SearchLibraryArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class ImportPaperArgs(BaseModel):
    source: Literal["arxiv", "semantic_scholar", "openalex", "google_scholar"]
    remote_id: str = Field(..., min_length=1, max_length=300)
    remote_ingest_token: str | None = None
    auto_download: bool = False
    title: str | None = Field(default=None, max_length=1000)


class ReadPdfArgs(BaseModel):
    paper_id: str = Field(..., min_length=1, max_length=80)
    query: str | None = Field(default=None, max_length=500)
    top_k: int = Field(default=3, ge=1, le=5)
    max_chars: int = Field(default=3500, ge=500, le=6000)


class AddToFolderArgs(BaseModel):
    folder_id: str = Field(..., min_length=1, max_length=80)
    paper_ids: list[str] = Field(..., min_length=1, max_length=50)


class CreateResearchProjectArgs(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    description: str | None = Field(default=None, max_length=3000)
    keywords: list[str] = Field(default_factory=list, max_length=20)
    paper_ids: list[str] = Field(default_factory=list, max_length=50)


class EmptyToolArgs(BaseModel):
    pass


ToolExecutor = Callable[[BaseModel, ChatAgentRuntimeState], Awaitable[ChatToolObservation] | ChatToolObservation]


@dataclass(frozen=True)
class ChatToolDefinition:
    name: str
    label: str
    args_model: type[BaseModel]
    executor: ToolExecutor
    side_effect: bool = False
    description: str = ""

    def schema_summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "side_effect": self.side_effect,
            "parameters": self.args_model.model_json_schema(),
        }


class ChatToolRegistry:
    def __init__(self):
        self._tools: dict[str, ChatToolDefinition] = {}

    def register(self, definition: ChatToolDefinition) -> None:
        self._tools[definition.name] = definition

    def get(self, name: str) -> ChatToolDefinition | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema_summary() for tool in self._tools.values()]

    async def execute(
        self,
        call: ChatToolCall,
        state: ChatAgentRuntimeState,
        *,
        allow_side_effects: bool = False,
    ) -> ChatToolObservation:
        definition = self.get(call.tool)
        if not definition:
            return ChatToolObservation(
                tool=call.tool,
                status="rejected",
                summary=f"Unknown chat tool: {call.tool}",
                details={"allowed_tools": list(self._tools)},
            )
        try:
            args = definition.args_model.model_validate(call.arguments or {})
        except ValidationError as exc:
            return ChatToolObservation(
                tool=call.tool,
                status="rejected",
                summary="Tool arguments failed validation.",
                details={"errors": exc.errors()},
            )
        if definition.side_effect and not allow_side_effects:
            token = chat_tool_confirmation_token(call.tool, args.model_dump())
            return ChatToolObservation(
                tool=call.tool,
                status="waiting_confirmation",
                summary=f"{definition.label} 需要用户确认后执行。",
                details={
                    "side_effect": True,
                    "confirmation_token": token,
                    "arguments": args.model_dump(),
                    "action_label": definition.label,
                },
            )
        if definition.side_effect:
            expected = chat_tool_confirmation_token(call.tool, args.model_dump())
            if call.confirmation_token != expected:
                return ChatToolObservation(
                    tool=call.tool,
                    status="rejected",
                    summary="Confirmation token does not match this tool call.",
                    details={"side_effect": True},
                )
        try:
            result = definition.executor(args, state)
            if inspect.isawaitable(result):
                result = await result
            return result
        except Exception as exc:
            logger.exception("Chat tool failed: %s", call.tool)
            return ChatToolObservation(
                tool=call.tool,
                status="failed",
                summary=f"{definition.label} failed: {exc}",
                details={"error": str(exc)},
            )


class ChatAgentToolRuntime:
    def __init__(self, registry: ChatToolRegistry, *, max_steps: int = 6):
        self.registry = registry
        self.max_steps = max(1, max_steps)

    async def run(
        self,
        state: ChatAgentRuntimeState,
        actions: list[ChatToolCall],
        *,
        allow_side_effects: bool = False,
    ) -> ChatAgentRuntimeState:
        for index, call in enumerate(actions[: self.max_steps], start=1):
            definition = self.registry.get(call.tool)
            label = definition.label if definition else call.tool
            event_base = call.call_id or f"chat-agent-{index}-{call.tool}"
            state.trace_events.append(ChatToolTraceEvent(
                id=f"{event_base}-running",
                tool=call.tool,
                label=label,
                status="running",
                summary=call.thought_summary or f"Running {call.tool}",
                details={"arguments": call.arguments},
            ))
            observation = await self.registry.execute(call, state, allow_side_effects=allow_side_effects)
            state.observations.append(observation)
            state.references.extend(observation.references)
            state.context_blocks.extend(observation.context_blocks)
            state.trace_events.append(ChatToolTraceEvent(
                id=f"{event_base}-{observation.status}",
                tool=call.tool,
                label=label,
                status=observation.status,
                summary=observation.summary,
                details={
                    **observation.details,
                    "result_count": observation.result_count,
                    "reference_count": len(observation.references),
                },
            ))
        if len(actions) > self.max_steps:
            state.stop_reason = "max_steps"
        elif not state.stop_reason:
            waiting = any(item.status == "waiting_confirmation" for item in state.observations)
            failed = any(item.status == "failed" for item in state.observations)
            rejected = any(item.status == "rejected" for item in state.observations)
            state.stop_reason = "waiting_confirmation" if waiting else "failed" if failed else "rejected" if rejected else "completed"
        return state


def chat_tool_confirmation_token(tool: str, arguments: dict[str, Any]) -> str:
    stable = json.dumps({"tool": tool, "arguments": arguments}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode()).hexdigest()[:32]


def parse_chat_tool_action_json(value: str) -> list[ChatToolCall]:
    cleaned = (value or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()
    parsed = json.loads(cleaned)
    raw_actions = parsed.get("actions") if isinstance(parsed, dict) else parsed
    if not isinstance(raw_actions, list):
        raise ValueError("Chat tool action JSON must contain an actions array")
    return [ChatToolCall.model_validate(item) for item in raw_actions if isinstance(item, dict)]


def deterministic_chat_tool_plan(query: str) -> list[ChatToolCall]:
    text = (query or "").strip()
    lowered = text.lower()
    if not text:
        return []
    wants_import = bool(re.search(r"(入库|导入|import|save paper|加入论文库)", lowered))
    paper_signal = bool(re.search(r"(论文|paper|papers|arxiv|semantic scholar|openalex|scholar)", lowered))
    library_signal = bool(re.search(r"(知识库|论文库|library|已入库|本地)", lowered))
    actions: list[ChatToolCall] = []
    uuid_values = re.findall(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", lowered)
    wants_read_pdf = bool(re.search(r"(读|阅读|解析|总结|read|summari[sz]e|pdf|全文)", lowered))
    wants_folder = bool(re.search(r"(加入|添加|add|move|保存).*(分类|文件夹|folder|collection)", lowered))
    wants_project = bool(re.search(r"(创建|新建|建立|create).*(研究方向|项目|project|research direction)", lowered))
    arxiv_match = re.search(r"(?:arxiv[:\s]*)?(\d{4}\.\d{4,5}(?:v\d+)?)", lowered)
    doi_match = re.search(r"(10\.\d{4,9}/[^\s,，。；;]+)", text)
    if wants_read_pdf and uuid_values:
        actions.append(ChatToolCall(
            tool="read_pdf",
            arguments={"paper_id": uuid_values[0], "query": text, "top_k": 3},
            thought_summary="用户要求阅读本地论文证据。",
        ))
        return actions
    if wants_folder and len(uuid_values) >= 2:
        folder_match = re.search(
            r"(?:分类|文件夹|folder|collection)\s*(?:是|为|:|：)?\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            lowered,
        )
        folder_id = folder_match.group(1) if folder_match else uuid_values[0]
        paper_ids = [value for value in uuid_values if value != folder_id]
        if not paper_ids:
            return actions
        actions.append(ChatToolCall(
            tool="add_to_folder",
            arguments={"folder_id": folder_id, "paper_ids": paper_ids},
            thought_summary="用户要求把本地论文加入分类，需要确认后执行。",
        ))
        return actions
    if wants_project:
        title_match = re.search(r"(?:研究方向|项目|project|方向)[：:\s]*([^，。；;\n]{2,80})", text, flags=re.IGNORECASE)
        name = title_match.group(1).strip() if title_match else text[:80]
        actions.append(ChatToolCall(
            tool="create_research_project",
            arguments={"name": name, "description": text, "paper_ids": uuid_values[:20]},
            thought_summary="用户要求创建研究方向，需要确认后执行。",
        ))
        return actions
    if wants_import and arxiv_match:
        arxiv_id = arxiv_match.group(1)
        actions.append(ChatToolCall(
            tool="import_paper",
            arguments={
                "source": "arxiv",
                "remote_id": arxiv_id,
                "auto_download": False,
                "title": f"arXiv:{arxiv_id}",
            },
            thought_summary="用户明确给出了 arXiv ID，准备导入前等待确认。",
        ))
        return actions
    if wants_import and doi_match:
        doi = doi_match.group(1).rstrip(".")
        actions.append(ChatToolCall(
            tool="import_paper",
            arguments={
                "source": "semantic_scholar",
                "remote_id": doi,
                "auto_download": False,
                "title": doi,
            },
            thought_summary="用户明确给出了 DOI，准备导入前等待确认。",
        ))
        return actions
    if wants_import and paper_signal:
        actions.append(ChatToolCall(
            tool="search_papers",
            arguments={"query": text, "limit": 5, "source": "arxiv_enriched"},
            thought_summary="先搜索可确认的远程论文候选，再等待用户确认入库。",
        ))
    elif library_signal:
        actions.append(ChatToolCall(
            tool="search_library",
            arguments={"query": text, "limit": 5},
            thought_summary="检索本地论文库。",
        ))
    elif paper_signal:
        actions.append(ChatToolCall(
            tool="search_papers",
            arguments={"query": text, "limit": 8, "source": "arxiv_enriched"},
            thought_summary="检索学术论文候选。",
        ))
    return actions


def paper_result_reference(paper: PaperResult, rank: int, *, source: str = "chat_tool") -> dict[str, Any]:
    metadata = getattr(paper, "metadata", {}) or {}
    return {
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "arxiv_id": paper.arxiv_id,
        "doi": paper.doi,
        "url": paper.source_url,
        "pdf_url": paper.pdf_url,
        "source": source,
        "provider": paper.source,
        "rank": rank,
        "remote_id": metadata.get("remote_id") or paper.arxiv_id or paper.doi or paper.source_url,
        "remote_ingest_token": create_remote_ingest_token(paper),
    }


def paper_result_context(paper: PaperResult, rank: int) -> str:
    authors = ", ".join((paper.authors or [])[:5]) or "unknown"
    return "\n".join([
        f"[TOOL-PAPER-{rank}] {paper.title}",
        f"Source: {paper.source} | Year: {paper.year or 'unknown'} | Citations: {paper.citation_count or 0}",
        f"Authors: {authors}",
        f"arXiv: {paper.arxiv_id or 'N/A'} | DOI: {paper.doi or 'N/A'}",
        f"Abstract: {(paper.abstract or '')[:TOOL_RESULT_ABSTRACT_CHARS]}",
    ])


def local_paper_reference(paper: Paper, score: float, rank: int) -> dict[str, Any]:
    metadata = paper.metadata_json or {}
    return {
        "title": paper.title,
        "arxiv_id": paper.arxiv_id,
        "year": paper.year,
        "similarity": round(float(score or 0), 4),
        "source": "local_library",
        "rank": rank,
        "paper_id": str(paper.id),
        "url": paper.source_url,
        "pdf_url": metadata.get("pdf_url"),
    }


def local_paper_context(paper: Paper, score: float, rank: int) -> str:
    authors = paper.authors if isinstance(paper.authors, list) else []
    return "\n".join([
        f"[TOOL-LIBRARY-{rank}] {paper.title}",
        f"Year: {paper.year or 'unknown'} | Similarity: {float(score or 0):.3f}",
        f"Authors: {', '.join(authors[:5]) or 'unknown'}",
        f"arXiv: {paper.arxiv_id or 'N/A'}",
        f"Abstract: {(paper.abstract or '')[:TOOL_RESULT_ABSTRACT_CHARS]}",
    ])


async def _tool_search_papers(args: SearchPapersArgs, state: ChatAgentRuntimeState) -> ChatToolObservation:
    papers = await search_scholarly_papers(
        args.query,
        source=args.source,
        max_results=args.limit,
        year_from=args.year_from,
        year_to=args.year_to,
        sort_by=args.sort_by,
    )
    references = [paper_result_reference(paper, index + 1) for index, paper in enumerate(papers)]
    context_blocks = [paper_result_context(paper, index + 1) for index, paper in enumerate(papers)]
    return ChatToolObservation(
        tool="search_papers",
        status="completed",
        summary=f"已检索到 {len(papers)} 篇学术论文候选。",
        result_count=len(papers),
        references=references,
        artifacts=[{"type": "paper_candidate", **ref} for ref in references],
        context_blocks=context_blocks,
        details={
            "query": args.query,
            "source": args.source,
            "limit": args.limit,
            "year_from": args.year_from,
            "year_to": args.year_to,
        },
    )


async def _tool_search_library(args: SearchLibraryArgs, state: ChatAgentRuntimeState) -> ChatToolObservation:
    if not state.db:
        return ChatToolObservation(
            tool="search_library",
            status="failed",
            summary="search_library requires a database session.",
        )
    rag = RAGService(state.db)
    results = await rag.search_keyword_and_semantic(args.query, top_k=args.limit)
    references = [local_paper_reference(paper, score, index + 1) for index, (paper, score) in enumerate(results)]
    context_blocks = [local_paper_context(paper, score, index + 1) for index, (paper, score) in enumerate(results)]
    return ChatToolObservation(
        tool="search_library",
        status="completed",
        summary=f"已从本地论文库检索到 {len(results)} 篇相关论文。",
        result_count=len(results),
        references=references,
        context_blocks=context_blocks,
        details={"query": args.query, "limit": args.limit},
    )


def _parse_uuid_arg(value: str, field_name: str) -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}") from exc


async def _load_user_accessible_paper(db: AsyncSession, user_id: Any, paper_id: str) -> Paper | None:
    pid = _parse_uuid_arg(paper_id, "paper_id")
    result = await db.execute(
        select(Paper)
        .outerjoin(UserPaper, (UserPaper.paper_id == Paper.id) & (UserPaper.user_id == user_id))
        .where(
            Paper.id == pid,
            (UserPaper.user_id == user_id) | (Paper.imported_by_user_id == user_id),
        )
    )
    return result.scalar_one_or_none()


def _local_paper_tool_reference(paper: Paper, *, source: str = "local_library") -> dict[str, Any]:
    metadata = paper.metadata_json or {}
    return {
        "title": paper.title,
        "arxiv_id": paper.arxiv_id,
        "year": paper.year,
        "source": source,
        "paper_id": str(paper.id),
        "url": paper.source_url,
        "pdf_url": metadata.get("pdf_url"),
    }


async def _tool_read_pdf(args: ReadPdfArgs, state: ChatAgentRuntimeState) -> ChatToolObservation:
    if not state.db or not state.user:
        return ChatToolObservation(
            tool="read_pdf",
            status="failed",
            summary="read_pdf requires a database session and authenticated user.",
        )
    try:
        paper = await _load_user_accessible_paper(state.db, state.user.id, args.paper_id)
    except ValueError as exc:
        return ChatToolObservation(tool="read_pdf", status="rejected", summary=str(exc), details=args.model_dump())
    if not paper:
        return ChatToolObservation(
            tool="read_pdf",
            status="rejected",
            summary="未找到可访问的本地论文，请先检索论文库或导入论文。",
            details={"paper_id": args.paper_id},
        )

    has_full_text = bool(paper.full_text and len(paper.full_text) > 500)
    query = args.query or state.user_query or paper.title
    evidence_blocks: list[str] = []
    evidence_scores: list[float] = []
    coverage = "full_text" if has_full_text else "abstract_only"
    if has_full_text:
        chunks, _scope = PaperChunkService.retrieve_chunks(paper.full_text or "", query, top_k=args.top_k)
        for index, (chunk, score) in enumerate(chunks[: args.top_k], start=1):
            cleaned = re.sub(r"\s+", " ", chunk).strip()
            if cleaned:
                evidence_scores.append(float(score or 0))
                evidence_blocks.append(f"[PDF-EVIDENCE-{index}] score={float(score or 0):.3f}\n{cleaned[:args.max_chars]}")
    if not evidence_blocks:
        abstract = (paper.abstract or "").strip()
        meta = " | ".join(filter(None, [f"Year: {paper.year}" if paper.year else "", f"arXiv: {paper.arxiv_id}" if paper.arxiv_id else ""]))
        fallback_text = "\n".join(filter(None, [meta, f"Abstract: {abstract}" if abstract else "No abstract available."]))
        evidence_blocks = [f"[PDF-ABSTRACT]\n{fallback_text[:args.max_chars]}"]
        coverage = "abstract_only"

    context = "\n\n".join([
        f"[TOOL-READ-PDF] {paper.title}",
        f"Evidence coverage: {coverage}",
        *evidence_blocks,
    ])[: args.max_chars * max(1, len(evidence_blocks))]
    return ChatToolObservation(
        tool="read_pdf",
        status="completed",
        summary=f"已读取《{paper.title}》的{'全文片段' if coverage == 'full_text' else '摘要级'}证据。",
        result_count=len(evidence_blocks),
        references=[_local_paper_tool_reference(paper, source="local_pdf")],
        context_blocks=[context],
        details={
            "paper_id": str(paper.id),
            "query": query,
            "evidence_coverage": coverage,
            "scores": evidence_scores,
            "has_full_text": has_full_text,
        },
    )


async def _tool_add_to_folder(args: AddToFolderArgs, state: ChatAgentRuntimeState) -> ChatToolObservation:
    if not state.db or not state.user:
        return ChatToolObservation(
            tool="add_to_folder",
            status="failed",
            summary="add_to_folder requires a database session and authenticated user.",
        )
    try:
        folder_id = _parse_uuid_arg(args.folder_id, "folder_id")
        paper_ids = [_parse_uuid_arg(value, "paper_id") for value in args.paper_ids]
    except ValueError as exc:
        return ChatToolObservation(tool="add_to_folder", status="rejected", summary=str(exc), details=args.model_dump())

    folder = (await state.db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == state.user.id)
    )).scalar_one_or_none()
    if not folder:
        return ChatToolObservation(
            tool="add_to_folder",
            status="rejected",
            summary="分类未找到或不属于当前用户。",
            details={"folder_id": args.folder_id},
        )

    papers_result = await state.db.execute(select(Paper).where(Paper.id.in_(paper_ids)))
    papers = list(papers_result.scalars().all())
    paper_by_id = {paper.id: paper for paper in papers}
    missing = [str(pid) for pid in paper_ids if pid not in paper_by_id]
    if missing:
        return ChatToolObservation(
            tool="add_to_folder",
            status="rejected",
            summary=f"论文不存在: {', '.join(missing[:3])}",
            details={"missing_paper_ids": missing},
        )

    existing_result = await state.db.execute(
        select(PaperFolderItem.paper_id).where(
            PaperFolderItem.folder_id == folder.id,
            PaperFolderItem.user_id == state.user.id,
            PaperFolderItem.paper_id.in_(paper_ids),
        )
    )
    existing_items = set(existing_result.scalars().all())
    added = 0
    for pid in paper_ids:
        user_paper = (await state.db.execute(
            select(UserPaper).where(UserPaper.user_id == state.user.id, UserPaper.paper_id == pid)
        )).scalar_one_or_none()
        if not user_paper:
            state.db.add(UserPaper(user_id=state.user.id, paper_id=pid, saved=True))
        else:
            user_paper.saved = True
        if pid not in existing_items:
            state.db.add(PaperFolderItem(folder_id=folder.id, paper_id=pid, user_id=state.user.id))
            existing_items.add(pid)
            added += 1
    await state.db.commit()
    references = [_local_paper_tool_reference(paper_by_id[pid]) for pid in paper_ids if pid in paper_by_id]
    return ChatToolObservation(
        tool="add_to_folder",
        status="completed",
        summary=f"已将 {added} 篇论文加入分类「{folder.name}」，跳过 {len(paper_ids) - added} 篇已存在论文。",
        result_count=added,
        references=references,
        artifacts=[{"type": "folder_link", "folder_id": str(folder.id), "paper_ids": [str(pid) for pid in paper_ids]}],
        context_blocks=[f"[TOOL-FOLDER] 分类「{folder.name}」新增 {added} 篇论文，跳过 {len(paper_ids) - added} 篇。"],
        details={"folder_id": str(folder.id), "folder_name": folder.name, "added": added, "skipped": len(paper_ids) - added},
    )


async def _tool_create_research_project(args: CreateResearchProjectArgs, state: ChatAgentRuntimeState) -> ChatToolObservation:
    if not state.db or not state.user:
        return ChatToolObservation(
            tool="create_research_project",
            status="failed",
            summary="create_research_project requires a database session and authenticated user.",
        )
    try:
        paper_ids = [_parse_uuid_arg(value, "paper_id") for value in args.paper_ids]
    except ValueError as exc:
        return ChatToolObservation(tool="create_research_project", status="rejected", summary=str(exc), details=args.model_dump())
    if paper_ids:
        existing_result = await state.db.execute(select(Paper.id).where(Paper.id.in_(paper_ids)))
        existing = set(existing_result.scalars().all())
        missing = [str(pid) for pid in paper_ids if pid not in existing]
        if missing:
            return ChatToolObservation(
                tool="create_research_project",
                status="rejected",
                summary=f"论文不存在: {', '.join(missing[:3])}",
                details={"missing_paper_ids": missing},
            )

    project = ResearchProject(
        name=args.name.strip(),
        description=args.description,
        keywords=[item.strip() for item in args.keywords if item.strip()],
        paper_ids=[str(pid) for pid in paper_ids],
        user_id=state.user.id,
        metadata_json={"created_from": "chat_agent_tool", "session_id": state.session_id},
    )
    state.db.add(project)
    await state.db.commit()
    await state.db.refresh(project)
    reference = {
        "source": "research_project",
        "project_id": str(project.id),
        "title": project.name,
        "paper_ids": project.paper_ids or [],
    }
    return ChatToolObservation(
        tool="create_research_project",
        status="completed",
        summary=f"已创建研究方向「{project.name}」。",
        result_count=1,
        references=[reference],
        artifacts=[{"type": "research_project", **reference}],
        context_blocks=[f"[TOOL-RESEARCH-PROJECT] {project.name} 已创建，关联论文 {len(project.paper_ids or [])} 篇。"],
        details={"project_id": str(project.id), "name": project.name, "paper_count": len(project.paper_ids or [])},
    )


async def _tool_import_paper(args: ImportPaperArgs, state: ChatAgentRuntimeState) -> ChatToolObservation:
    if not state.db or not state.user:
        return ChatToolObservation(
            tool="import_paper",
            status="failed",
            summary="import_paper requires a database session and authenticated user.",
        )
    service = PaperIngestionService(state.db)
    preview = read_remote_ingest_token(args.remote_ingest_token) if args.remote_ingest_token else None
    if preview and preview.source == args.source and (preview.metadata or {}).get("remote_id") == args.remote_id:
        paper, is_new = await service.ingest_paper(preview, auto_download=args.auto_download, imported_by_user=state.user)
    else:
        paper, is_new = await service.ingest_remote(
            args.source,
            args.remote_id,
            auto_download=args.auto_download,
            imported_by_user=state.user,
        )
    if not paper:
        return ChatToolObservation(
            tool="import_paper",
            status="failed",
            summary="未能从远程学术源解析这篇论文。",
            details=args.model_dump(),
        )
    await PaperEnhanceService(state.db).save_paper(str(state.user.id), str(paper.id))
    metadata = paper.metadata_json or {}
    reference = {
        "title": paper.title,
        "arxiv_id": paper.arxiv_id,
        "year": paper.year,
        "source": "local_library",
        "paper_id": str(paper.id),
        "url": paper.source_url,
        "pdf_url": metadata.get("pdf_url"),
    }
    return ChatToolObservation(
        tool="import_paper",
        status="completed",
        summary=f"{'已入库' if is_new else '已存在，已加入你的论文库'}：{paper.title}",
        result_count=1,
        references=[reference],
        artifacts=[{"type": "imported_paper", "paper_id": str(paper.id), "is_new": is_new, "title": paper.title}],
        context_blocks=[f"[TOOL-IMPORTED] {paper.title} ({paper.year or 'unknown'}) 已加入当前用户论文库。"],
        details={"paper_id": str(paper.id), "is_new": is_new},
    )


def default_chat_tool_registry() -> ChatToolRegistry:
    registry = ChatToolRegistry()
    registry.register(ChatToolDefinition(
        name="search_papers",
        label="检索论文",
        description="Search scholarly providers for paper candidates without importing them.",
        args_model=SearchPapersArgs,
        executor=_tool_search_papers,
    ))
    registry.register(ChatToolDefinition(
        name="search_library",
        label="检索论文库",
        description="Search the user's local paper library.",
        args_model=SearchLibraryArgs,
        executor=_tool_search_library,
    ))
    registry.register(ChatToolDefinition(
        name="import_paper",
        label="导入论文",
        description="Import a remote paper into the user's library after explicit confirmation.",
        args_model=ImportPaperArgs,
        executor=_tool_import_paper,
        side_effect=True,
    ))
    registry.register(ChatToolDefinition(
        name="read_pdf",
        label="读取论文",
        description="Read bounded evidence from a local paper's stored full text or abstract.",
        args_model=ReadPdfArgs,
        executor=_tool_read_pdf,
    ))
    registry.register(ChatToolDefinition(
        name="add_to_folder",
        label="加入分类",
        description="Add local papers to an existing folder after explicit confirmation.",
        args_model=AddToFolderArgs,
        executor=_tool_add_to_folder,
        side_effect=True,
    ))
    registry.register(ChatToolDefinition(
        name="create_research_project",
        label="创建研究方向",
        description="Create a research project and optionally link local papers after explicit confirmation.",
        args_model=CreateResearchProjectArgs,
        executor=_tool_create_research_project,
        side_effect=True,
    ))
    return registry


def chat_tool_trace_payload(state: ChatAgentRuntimeState, registry: ChatToolRegistry | None = None) -> dict[str, Any]:
    return {
        "enabled": bool(state.trace_events),
        "workflow": "chat_agent_tools",
        "stop_reason": state.stop_reason,
        "tools": (registry or default_chat_tool_registry()).schemas(),
        "steps": [event.model_dump() for event in state.trace_events],
    }


def chat_tool_context_block(state: ChatAgentRuntimeState) -> str:
    blocks: list[str] = []
    for observation in state.observations:
        if observation.context_blocks:
            blocks.append(f"Tool `{observation.tool}` observation: {observation.summary}\n" + "\n\n".join(observation.context_blocks))
    text = "\n\n".join(blocks)
    return text[:TOOL_CONTEXT_MAX_CHARS]
