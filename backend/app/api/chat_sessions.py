"""多对话会话管理 API。"""

import asyncio
import json
import logging
import re
from typing import Any, List, Literal, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.user import User
from app.core.security import get_current_user
from app.core.config import settings
from app.services.llm import OPENAI_COMPATIBLE_PROVIDER, llm_service
from app.services.cvf_openaccess import normalize_cvf_venue, search_cvf_openaccess
from app.services.paper_search import PaperResult, create_remote_ingest_token, deduplicate_papers, search_scholarly_papers
from app.services.rag_service import RAGService
from app.services.research_scout_agent import (
    EmptyToolArgs,
    ResearchScoutAgent,
    ResearchScoutAgentState,
    ResearchScoutConstraints,
    ResearchScoutToolCall,
    ResearchScoutToolDefinition,
    ResearchScoutToolObservation,
    ResearchScoutToolRegistry,
)
from app.services.chat_agent_tools import (
    ChatAgentRuntimeState,
    ChatAgentToolRuntime,
    ChatToolCall,
    AddToFolderArgs,
    CreateResearchProjectArgs,
    ImportPaperArgs,
    chat_tool_confirmation_token,
    chat_tool_trace_payload,
    default_chat_tool_registry,
)
from app.services.chat_tool_planner import (
    planner_tool_context_block,
    planner_tool_trace_payload,
    run_llm_tool_planner,
)
from app.services.web_search import format_web_context, search_web_results
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat-sessions", tags=["对话会话"])
MAX_CHAT_UPLOAD_BYTES = max(1, int(settings.MAX_UPLOAD_SIZE_MB or 50)) * 1024 * 1024
MAX_CHAT_IMAGE_DATA_URL_LENGTH = ((MAX_CHAT_UPLOAD_BYTES + 2) // 3) * 4 + 128


async def _extract_pdf_text(file_bytes: bytes, filename: str) -> str:
    """从 PDF 中提取文本，依次尝试多种方式。"""
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(file_bytes)
    tmp.close()
    tmp_path = tmp.name
    extracted_text = ""
    page_count = 0

    try:
        # 方式1: pdfplumber
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(tmp_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: text_parts.append(t)
            if any(t.strip() for t in text_parts):
                extracted_text = "\n\n".join(text_parts)
                logger.info(f"pdfplumber 提取: {filename} → {len(extracted_text)} 字符")
        except Exception as e:
            logger.warning(f"pdfplumber 失败: {e}")

        # 方式2: fitz
        if not extracted_text:
            try:
                import fitz
                text_parts = []
                doc = fitz.open(tmp_path)
                page_count = len(doc)
                for page in doc: text_parts.append(page.get_text())
                doc.close()
                if any(t.strip() for t in text_parts):
                    extracted_text = "\n\n".join(text_parts)
                    logger.info(f"fitz 提取: {filename} → {len(extracted_text)} 字符")
            except Exception as e:
                logger.warning(f"fitz 失败: {e}")

        # 方式3: pikepdf 修复后 fitz
        if not extracted_text:
            try:
                import pikepdf
                repaired = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                pdf = pikepdf.open(tmp_path)
                pdf.save(repaired.name)
                pdf.close()
                import fitz
                text_parts = []
                doc = fitz.open(repaired.name)
                page_count = len(doc)
                for page in doc: text_parts.append(page.get_text())
                doc.close()
                os.unlink(repaired.name)
                if any(t.strip() for t in text_parts):
                    extracted_text = "\n\n".join(text_parts)
                    logger.info(f"pikepdf 修复后提取: {filename} → {len(extracted_text)} 字符")
            except Exception as e:
                logger.warning(f"pikepdf 失败: {e}")

    finally:
        try: os.unlink(tmp_path)
        except: pass

    if extracted_text and len(extracted_text.strip()) > 100:
        return extracted_text[:50000]
    else:
        logger.error(f"PDF 提取完全失败: {filename}")
        return ""


async def _extract_pdf_text_and_visual_evidence(file_bytes: bytes, filename: str) -> tuple[str, dict | None, list[dict]]:
    """Extract PDF text plus bounded document visual/table evidence."""

    extracted_text = await _extract_pdf_text(file_bytes, filename)
    try:
        from app.services.document_visual_evidence import extract_visual_evidence_from_pdf_bytes

        visual_payload, visual_blocks = await extract_visual_evidence_from_pdf_bytes(file_bytes, filename)
    except Exception as exc:
        logger.warning("PDF visual evidence extraction failed for upload %s: %s", filename, exc)
        visual_payload, visual_blocks = None, []
    return extracted_text, visual_payload, visual_blocks


def _format_uploaded_pdf_visual_context(filename: str, visual_blocks: list[dict]) -> str:
    if not visual_blocks:
        return (
            f"\n\n[PDF 视觉证据状态: {filename}]\n"
            "当前上传 PDF 没有 ready 的图像/表格视觉证据；如果用户询问图片、架构图、曲线或表格截图，"
            "请明确说明只能基于已提取文本回答，不能描述未解析的视觉细节。"
        )
    from app.services.document_visual_evidence import format_visual_evidence_context

    return (
        f"\n\n[PDF 视觉/表格证据: {filename}]\n"
        "以下证据来自同一 PDF 的结构化视觉证据，回答图、表、实验结果时必须引用这些内容：\n"
        f"{format_visual_evidence_context(visual_blocks)}"
    )


def _uploaded_pdf_visual_references(filename: str, visual_blocks: list[dict]) -> list[dict]:
    references: list[dict] = []
    for index, block in enumerate(visual_blocks, 1):
        metadata = block.get("metadata") if isinstance(block.get("metadata"), dict) else {}
        references.append({
            "id": f"PDF-V{index}",
            "type": "uploaded_pdf_visual_evidence",
            "source": "uploaded_pdf",
            "filename": filename,
            "page": block.get("page"),
            "evidence_type": block.get("type"),
            "snippet": str(block.get("text") or "")[:320],
            "metadata": metadata,
        })
    return references


def _uploaded_pdf_visual_context_from_messages(messages: list[ChatMessage], *, limit: int = 8) -> tuple[str, list[dict]]:
    """Reuse ready uploaded-PDF visual/table references without reparsing attachments."""

    references: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for message in messages:
        for ref in message.references or []:
            if not isinstance(ref, dict):
                continue
            if ref.get("type") != "uploaded_pdf_visual_evidence":
                continue
            metadata = ref.get("metadata") if isinstance(ref.get("metadata"), dict) else {}
            key = (
                str(ref.get("filename") or ""),
                str(ref.get("page") or ""),
                str(metadata.get("asset_id") or ref.get("id") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            references.append(ref)
            if len(references) >= limit:
                break
        if len(references) >= limit:
            break

    if not references:
        return "", []

    lines = [
        "以下是本会话已经上传 PDF 的 ready 视觉/表格证据；后续回答涉及图、表、实验结果或方法架构时应优先引用这些证据，不能重新假设未解析的图片内容。"
    ]
    for index, ref in enumerate(references, 1):
        metadata = ref.get("metadata") if isinstance(ref.get("metadata"), dict) else {}
        kind = metadata.get("kind") or ref.get("evidence_type") or "visual"
        page = ref.get("page") or "unknown"
        caption = metadata.get("caption")
        summary = metadata.get("summary")
        confidence = metadata.get("confidence")
        lines.append(f"\n### [UPDF-V{index}] {kind} page {page} confidence {confidence if confidence is not None else 'unknown'}")
        if caption:
            lines.append(f"Caption: {caption}")
        if summary:
            lines.append(f"Summary: {summary}")
        snippet = str(ref.get("snippet") or "").strip()
        if snippet:
            lines.append(snippet[:900])
    return "\n".join(lines).strip(), references


class SessionCreate(BaseModel):
    title: str = Field(default="新对话", max_length=300)
    rag_enabled: bool = True


class SessionResponse(BaseModel):
    id: str
    title: str
    rag_enabled: bool
    message_count: int = 0
    last_message: Optional[str] = None
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    references: Optional[list] = None
    tool_trace: Optional[dict] = None
    created_at: str


class ChatImageAttachment(BaseModel):
    filename: str = Field(default="image")
    mime_type: str = Field(default="image/png")
    data_url: str = Field(..., max_length=MAX_CHAT_IMAGE_DATA_URL_LENGTH)

    @field_validator("data_url")
    @classmethod
    def validate_data_url(cls, value: str) -> str:
        if not value.startswith("data:image/") or ";base64," not in value[:80]:
            raise ValueError("图片附件必须是 data:image/*;base64 格式")
        return value


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)
    rag_enabled: Optional[bool] = None
    extra_context: Optional[str] = Field(default=None, description="额外上下文（如文件内容），不显示在对话中")
    attachments: list[ChatImageAttachment] = Field(default_factory=list, max_length=4)
    web_search: Optional[bool] = Field(default=False, description="是否启用联网搜索")
    search_depth: Literal["quick", "standard", "deep"] = Field(default="standard", description="检索深度")
    show_thinking: bool = Field(default=False, description="是否展示思考过程")
    assistant_mode: Literal["general", "research_scout"] = Field(default="general", description="对话助手模式")
    tool_mode: Literal["auto", "off", "force"] = Field(default="auto", description="通用 Agent 工具模式")


class ConfirmToolRequest(BaseModel):
    message_id: str
    tool: Literal["import_paper", "add_to_folder", "create_research_project"]
    arguments: dict[str, Any]
    confirmation_token: str


RETRIEVAL_DEPTH_LIMITS = {
    "quick": {"rag_papers": 2, "web_results": 2, "web_queries": 1},
    "standard": {"rag_papers": 3, "web_results": 5, "web_queries": 3},
    "deep": {"rag_papers": 5, "web_results": 8, "web_queries": 5},
}
RESEARCH_SCOUT_LIMITS = {"quick": 5, "standard": 8, "deep": 12}
RESEARCH_SCOUT_MAX_FINAL_RESULTS = 50
RESEARCH_SCOUT_MAX_PER_QUERY_RESULTS = 60
RESEARCH_SCOUT_POOL_MULTIPLIER = 4
RESEARCH_SCOUT_INTENT_YEAR_RE = re.compile(r"(?<!\d)(20\d{2}|19\d{2})(?!\d)")
RESEARCH_SCOUT_RECENT_HINTS = {"recent", "latest", "new", "newest", "sota", "2024", "2025", "2026", "近", "最新", "近期", "近年"}
RESEARCH_SCOUT_REPRO_HINTS = {"reproducible", "replication", "code", "github", "可复现", "复现", "代码"}
RESEARCH_SCOUT_CITATION_HINTS = {"high citation", "highly cited", "经典", "高引用", "seminal", "survey"}
RESEARCH_SCOUT_NOVEL_HINTS = {"interesting", "novel", "新颖", "有趣", "idea", "inspiration"}
RESEARCH_SCOUT_HARD_CONSTRAINT_HINTS = {"必须", "只要", "限定", "仅限", "只能", "only", "must", "require", "required", "hard"}
RESEARCH_SCOUT_EVALUATION_FOCUS = {
    "novelty": {"novel", "novelty", "innovation", "innovative", "新颖", "创新", "有趣"},
    "relevance": {"relevant", "relevance", "related", "关系", "相关", "有用"},
    "reproducibility": {"reproducible", "replication", "code", "github", "复现", "可复现", "代码"},
    "impact": {"impact", "citation", "cited", "influential", "影响力", "高引用", "经典"},
    "experiment_quality": {"experiment", "ablation", "benchmark", "dataset", "实验", "消融", "基准", "数据集"},
    "risk": {"risk", "limitation", "weakness", "风险", "局限", "缺点"},
}
RESEARCH_SCOUT_VENUE_ALIASES = {
    "cvpr": "CVPR",
    "iccv": "ICCV",
    "eccv": "ECCV",
    "neurips": "NeurIPS",
    "nips": "NeurIPS",
    "iclr": "ICLR",
    "icml": "ICML",
    "acl": "ACL",
    "emnlp": "EMNLP",
    "naacl": "NAACL",
    "sigir": "SIGIR",
    "kdd": "KDD",
    "aaai": "AAAI",
    "ijcai": "IJCAI",
    "mm": "ACM MM",
    "acm mm": "ACM MM",
    "tpami": "TPAMI",
    "ijcv": "IJCV",
    "tacl": "TACL",
}
RESEARCH_SCOUT_INSTITUTION_ALIASES = {
    "mit": "MIT",
    "stanford": "Stanford",
    "cmu": "CMU",
    "carnegie mellon": "Carnegie Mellon",
    "berkeley": "UC Berkeley",
    "uc berkeley": "UC Berkeley",
    "harvard": "Harvard",
    "oxford": "Oxford",
    "cambridge": "Cambridge",
    "tsinghua": "Tsinghua",
    "清华": "清华大学",
    "pku": "Peking University",
    "peking university": "Peking University",
    "北大": "北京大学",
    "zhejiang university": "Zhejiang University",
    "浙大": "浙江大学",
    "google": "Google",
    "google research": "Google Research",
    "deepmind": "DeepMind",
    "meta": "Meta",
    "fair": "FAIR",
    "microsoft": "Microsoft",
    "msra": "MSRA",
    "openai": "OpenAI",
    "nvidia": "NVIDIA",
}

EMPTY_STREAM_FALLBACK = "⚠️ 模型本轮未返回可展示内容，请重新发送问题或稍后重试。"
INTERRUPTED_STREAM_FALLBACK = "\n\n> ⚠️ 回答生成中途出现异常，以上内容可能不完整，请重试。"
PAPER_DISCOVERY_TRIGGER_RE = re.compile(
    r"(?:找|搜索|检索|推荐|列出|整理|筛选|查找|find|search|recommend|list|scout|shortlist)",
    re.IGNORECASE,
)
PAPER_DISCOVERY_PAPER_RE = re.compile(r"(?:论文|paper|papers|arxiv|cvpr|iccv|eccv|neurips|iclr|icml)", re.IGNORECASE)
PAPER_DISCOVERY_COUNT_RE = re.compile(r"(?:\b\d+\s*(?:篇|个|条)?\b|[一二两三四五六七八九十]+\s*篇)", re.IGNORECASE)
RESEARCH_SCOUT_COUNT_RE = re.compile(
    r"(?:(?<!\d)(\d{1,3})(?!\d)\s*(?:篇|个|条|papers?|articles?|works?)?|([一二两三四五六七八九十百两]+)\s*(?:篇|个|条|篇论文|papers?)?)",
    re.IGNORECASE,
)
RESEARCH_SCOUT_CHINESE_NUMERALS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def _parse_chinese_count(value: str) -> int | None:
    text = (value or "").strip()
    if not text:
        return None
    if text == "十":
        return 10
    if "百" in text:
        before, _, after = text.partition("百")
        hundreds = _parse_chinese_count(before) if before else 1
        tail = _parse_chinese_count(after) if after else 0
        if hundreds is not None and tail is not None:
            return hundreds * 100 + tail
    if "十" in text:
        before, _, after = text.partition("十")
        tens = _parse_chinese_count(before) if before else 1
        ones = _parse_chinese_count(after) if after else 0
        if tens is not None and ones is not None:
            return tens * 10 + ones
    return RESEARCH_SCOUT_CHINESE_NUMERALS.get(text)


def _research_scout_requested_count(query: str) -> int | None:
    candidates: list[int] = []
    for match in RESEARCH_SCOUT_COUNT_RE.finditer(query or ""):
        if match.group(1):
            try:
                candidates.append(int(match.group(1)))
            except ValueError:
                continue
        elif match.group(2):
            parsed = _parse_chinese_count(match.group(2))
            if parsed:
                candidates.append(parsed)
    meaningful = [count for count in candidates if 0 < count <= 500]
    return max(meaningful) if meaningful else None


def _research_scout_final_limit(query: str, search_depth: str) -> dict[str, Any]:
    requested = _research_scout_requested_count(query)
    default_limit = RESEARCH_SCOUT_LIMITS.get(search_depth, RESEARCH_SCOUT_LIMITS["standard"])
    raw_limit = requested or default_limit
    final_limit = max(1, min(raw_limit, RESEARCH_SCOUT_MAX_FINAL_RESULTS))
    return {
        "requested_count": requested,
        "default_count": default_limit,
        "final_limit": final_limit,
        "max_final_limit": RESEARCH_SCOUT_MAX_FINAL_RESULTS,
        "capped": bool(requested and requested > RESEARCH_SCOUT_MAX_FINAL_RESULTS),
    }


def _is_paper_discovery_request(content: str) -> bool:
    """Detect explicit paper-finding prompts that should use Research Scout."""

    text = (content or "").strip()
    if not text:
        return False
    lowered = text.lower()
    if not PAPER_DISCOVERY_TRIGGER_RE.search(text):
        return False
    if PAPER_DISCOVERY_PAPER_RE.search(text):
        return True
    if PAPER_DISCOVERY_COUNT_RE.search(text) and any(term in lowered for term in ("arxiv", "conference", "会议", "顶会", "研究", "paper")):
        return True
    return False


def _effective_assistant_mode(req: SendMessageRequest) -> Literal["general", "research_scout"]:
    if req.assistant_mode == "research_scout" or _is_paper_discovery_request(req.content):
        return "research_scout"
    return "general"


def _web_search_enabled_for_mode(req: SendMessageRequest, effective_mode: str) -> bool:
    return bool(req.web_search) and effective_mode != "research_scout"


CHAT_TOOL_TRACE_REFERENCE_TYPE = "chat_tool_trace"


def _chat_tool_planner_enabled(req: SendMessageRequest, effective_mode: str) -> bool:
    return effective_mode != "research_scout" and req.tool_mode != "off" and bool((req.content or "").strip())


def _tool_trace_reference(tool_trace: dict[str, Any] | None) -> dict[str, Any] | None:
    if not tool_trace:
        return None
    return {
        "source": CHAT_TOOL_TRACE_REFERENCE_TYPE,
        "type": CHAT_TOOL_TRACE_REFERENCE_TYPE,
        "tool_trace": tool_trace,
    }


def _references_with_tool_trace(
    references: list[dict[str, Any]],
    tool_trace: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    visible = [
        ref
        for ref in references
        if not (
            isinstance(ref, dict)
            and ref.get("source") == CHAT_TOOL_TRACE_REFERENCE_TYPE
            and ref.get("type") == CHAT_TOOL_TRACE_REFERENCE_TYPE
        )
    ]
    trace_ref = _tool_trace_reference(tool_trace)
    return [*visible, trace_ref] if trace_ref else visible


def _tool_trace_from_references(references: list | None) -> dict[str, Any] | None:
    for ref in references or []:
        if not isinstance(ref, dict):
            continue
        if ref.get("source") == CHAT_TOOL_TRACE_REFERENCE_TYPE and ref.get("type") == CHAT_TOOL_TRACE_REFERENCE_TYPE:
            payload = ref.get("tool_trace")
            return payload if isinstance(payload, dict) else None
    return None


def _visible_chat_references(references: list | None) -> list:
    return [
        ref
        for ref in references or []
        if not (
            isinstance(ref, dict)
            and ref.get("source") == CHAT_TOOL_TRACE_REFERENCE_TYPE
            and ref.get("type") == CHAT_TOOL_TRACE_REFERENCE_TYPE
        )
    ]


async def _build_chat_agent_tool_context(
    query: str,
    *,
    db: AsyncSession,
    user: User,
    session_id: str,
    conversation_context: list[dict[str, Any]] | None = None,
    tool_mode: Literal["auto", "force"] = "auto",
) -> tuple[str, list[dict[str, Any]], dict[str, Any] | None]:
    registry = default_chat_tool_registry()
    state = ChatAgentRuntimeState(
        user_query=query,
        db=db,
        user=user,
        session_id=session_id,
    )
    result = await run_llm_tool_planner(
        user_query=query,
        state=state,
        registry=registry,
        conversation_context=conversation_context,
        force_fallback=tool_mode == "force",
    )
    if not result.state.trace_events:
        return "", [], None
    tool_trace = planner_tool_trace_payload(result, registry)
    tool_trace["tool_mode"] = tool_mode
    return planner_tool_context_block(result), result.state.references, tool_trace


def _stream_event(event_type: str, content: Any = None) -> str:
    payload = {"type": event_type}
    if content is not None:
        payload["content"] = content
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_failure_content(full_content: str) -> tuple[str, str]:
    appended = INTERRUPTED_STREAM_FALLBACK if full_content else EMPTY_STREAM_FALLBACK
    return f"{full_content}{appended}", appended


def _image_text_fallback(attachments: list[ChatImageAttachment]) -> str:
    if not attachments:
        return ""
    names = ", ".join(item.filename for item in attachments)
    return (
        f"[图片附件: {names}]\n"
        "当前选择的模型不支持视觉图片输入，不能看到图片本体。"
        "请用户切换到 GPT-5.5（OpenAI 兼容）模型后再进行图片分析。"
    )


def _build_llm_context_for_request(
    context: list[dict[str, Any]],
    req: Any,
) -> list[dict[str, Any]]:
    """Attach current-turn images only when the active provider supports vision."""
    attachments = getattr(req, "attachments", None) or []
    if not attachments:
        return context

    active_provider = llm_service.get_active_option().get("provider")
    if active_provider != OPENAI_COMPATIBLE_PROVIDER:
        fallback = _image_text_fallback(attachments)
        return [*context, {"role": "system", "content": fallback}] if fallback else context

    request_text = str(getattr(req, "content", None) or getattr(req, "question", "") or "").strip()
    text = request_text or "请分析上传的图片。"
    content_parts: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for attachment in attachments:
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": attachment.data_url},
        })
    multimodal_message = {"role": "user", "content": content_parts}
    if context and context[-1].get("role") == "user" and context[-1].get("content") == request_text:
        return [*context[:-1], multimodal_message]
    return [*context, multimodal_message]


def _active_model_stream_metadata(
    *,
    rag_enabled: bool,
    web_search_enabled: bool,
    search_depth: str,
    attachments: list[ChatImageAttachment] | None = None,
) -> dict[str, Any]:
    """Return frontend-safe model metadata for the current streamed turn."""
    active_option = llm_service.get_active_option()
    provider = str(active_option.get("provider") or "")
    model = str(active_option.get("model") or "")
    label = str(active_option.get("label") or model or provider or "当前模型")
    supports_vision = provider == OPENAI_COMPATIBLE_PROVIDER
    image_count = sum(1 for item in attachments or [] if item.mime_type.startswith("image/"))

    return {
        "provider": provider,
        "label": label,
        "model": model,
        "configured": bool(active_option.get("configured")),
        "capabilities": {
            "rag": bool(rag_enabled),
            "web_search": bool(web_search_enabled),
            "thinking": bool(active_option.get("supports_thinking")),
            "vision": supports_vision,
        },
        "search_depth": search_depth,
        "image_attachments": image_count,
    }


def _retrieval_limits(search_depth: str) -> dict[str, int]:
    return RETRIEVAL_DEPTH_LIMITS.get(search_depth, RETRIEVAL_DEPTH_LIMITS["standard"])


def _compact_author_list(authors: list[str], limit: int = 3) -> list[str]:
    cleaned = [author for author in authors if author]
    if len(cleaned) <= limit:
        return cleaned
    return [*cleaned[:limit], f"+{len(cleaned) - limit} authors"]


def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = re.sub(r"\s+", " ", str(item or "").strip(" \t\n\r,，;；。.:："))
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def _research_scout_alias_matches(text: str, aliases: dict[str, str]) -> list[str]:
    lowered = (text or "").lower()
    return _dedupe_preserve([
        label
        for alias, label in aliases.items()
        if re.search(rf"(?<![a-z0-9]){re.escape(alias.lower())}(?![a-z0-9])", lowered)
    ])


def _research_scout_split_constraint_text(value: str) -> list[str]:
    cleaned = re.sub(
        r"(论文|paper|papers|文章|工作|成果|发表|单位|机构|学校|公司|实验室|lab|university|institute|company)$",
        "",
        (value or "").strip(),
        flags=re.IGNORECASE,
    )
    parts = re.split(r"\s*(?:,|，|、|/|;|；|\band\b|\bor\b|和|或)\s*", cleaned)
    return [part.strip() for part in parts if 1 < len(part.strip()) <= 80]


def _research_scout_marker_values(query: str, markers: list[str]) -> list[str]:
    values: list[str] = []
    for marker in markers:
        pattern = rf"{marker}\s*(?:是|为|:|：|=|from|in|at)?\s*([^，。；;\n]+)"
        for match in re.finditer(pattern, query or "", flags=re.IGNORECASE):
            values.extend(_research_scout_split_constraint_text(match.group(1)))
    return values


def _research_scout_venue_from_metadata(metadata: dict[str, Any]) -> str | None:
    venue = metadata.get("venue")
    if isinstance(venue, dict):
        return venue.get("name") or venue.get("displayName") or venue.get("alternate_names", [None])[0]
    if isinstance(venue, str):
        return venue
    return None


def _research_scout_year_range(intent: dict[str, Any]) -> tuple[int | None, int | None]:
    years = sorted({int(year) for year in intent.get("years") or [] if str(year).isdigit()})
    if not years:
        return None, None
    return years[0], years[-1]


def _research_scout_cvf_venues(intent: dict[str, Any]) -> list[str]:
    return _dedupe_preserve([
        normalized
        for venue in intent.get("venues") or []
        if (normalized := normalize_cvf_venue(str(venue)))
    ])


def _research_scout_constraint_mode(intent: dict[str, Any]) -> str:
    if intent.get("constraint_mode") == "hard":
        return "hard"
    if intent.get("venues") or intent.get("years") or intent.get("institutions") or intent.get("authors"):
        return "hard"
    return "soft"


def _research_scout_institutions_from_metadata(metadata: dict[str, Any]) -> list[str]:
    institutions = metadata.get("institutions") or []
    if not isinstance(institutions, list):
        return []
    return _dedupe_preserve([str(item) for item in institutions if item])


def _research_scout_metadata_provenance(metadata: dict[str, Any]) -> dict[str, Any]:
    provenance = metadata.get("metadata_provenance")
    return dict(provenance) if isinstance(provenance, dict) else {}


def _research_scout_text_blob(paper: PaperResult) -> str:
    metadata = getattr(paper, "metadata", {}) or {}
    parts = [
        paper.title or "",
        paper.abstract or "",
        " ".join(paper.authors or []),
        _research_scout_venue_from_metadata(metadata) or "",
        " ".join(_research_scout_institutions_from_metadata(metadata)),
        " ".join(str(item) for item in metadata.get("concepts", []) or []),
    ]
    return " ".join(parts).lower()


def _research_scout_rationale(paper: PaperResult, query: str, rank: int) -> dict[str, str]:
    abstract = (paper.abstract or "").lower()
    title = (paper.title or "").lower()
    query_terms = [term for term in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", query.lower()) if term]
    matched_terms = [term for term in query_terms if term in title or term in abstract][:5]
    source_label = {
        "arxiv": "arXiv",
        "semantic_scholar": "Semantic Scholar",
        "openalex": "OpenAlex",
        "google_scholar": "Google Scholar",
    }.get(paper.source, paper.source or "scholarly source")
    signals: list[str] = []
    if matched_terms:
        signals.append(f"匹配关键词：{', '.join(matched_terms)}")
    if paper.year:
        signals.append(f"{paper.year} 年论文")
    if paper.citation_count:
        signals.append(f"引用数约 {paper.citation_count}")
    if paper.pdf_url:
        signals.append("有开放 PDF")
    if not signals:
        signals.append(f"来自 {source_label} 的候选结果")

    return {
        "why_interesting": f"候选 #{rank} 在题名/摘要中呈现与当前问题相关的线索，{signals[0]}。",
        "why_useful": "适合先作为快速阅读对象，用来判断该方向的方法、任务或实验设置是否值得纳入后续研究。",
        "caveat": "推荐理由基于标题、摘要和元数据，关键结论仍需要阅读全文和实验表格确认。",
        "library_relation": "可先作为外部候选补充到论文库，再根据阅读结果归入分类或研究方向素材池。",
    }


def _research_scout_intent(query: str, search_depth: str) -> dict[str, Any]:
    lowered = (query or "").lower()
    tokens = [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", lowered)
        if token not in {"find", "some", "paper", "papers", "about", "with", "from", "into", "that"}
    ]
    years = sorted({int(item) for item in RESEARCH_SCOUT_INTENT_YEAR_RE.findall(query or "")})
    methods = [
        term for term in tokens
        if term in {"transformer", "diffusion", "rag", "llm", "vlm", "contrastive", "alignment", "retrieval", "grounding"}
    ]
    datasets = [
        term.upper() for term in tokens
        if term in {"charades", "activitynet", "tacos", "didemo", "ego4d", "anet"}
    ]
    tasks = []
    if "grounding" in lowered:
        tasks.append("grounding")
    if "retrieval" in lowered or "moment" in lowered:
        tasks.append("moment retrieval")
    if "video" in lowered:
        tasks.append("video understanding")
    preferences = []
    if any(hint in lowered for hint in RESEARCH_SCOUT_NOVEL_HINTS):
        preferences.append("novel_or_interesting")
    if any(hint in lowered for hint in RESEARCH_SCOUT_REPRO_HINTS):
        preferences.append("reproducible")
    if any(hint in lowered for hint in RESEARCH_SCOUT_CITATION_HINTS):
        preferences.append("high_citation")
    if any(hint in lowered for hint in RESEARCH_SCOUT_RECENT_HINTS):
        preferences.append("recent")
    venues = [
        *_research_scout_alias_matches(query, RESEARCH_SCOUT_VENUE_ALIASES),
        *_research_scout_marker_values(query, ["venue", "conference", "journal", "会议", "期刊", "顶会", "发表在", "来自会议"]),
    ]
    institutions = [
        *_research_scout_alias_matches(query, RESEARCH_SCOUT_INSTITUTION_ALIASES),
        *_research_scout_marker_values(query, ["institution", "affiliation", "organization", "org", "单位", "机构", "学校", "公司", "实验室", "来自"]),
    ]
    authors = _research_scout_marker_values(query, ["author", "authors", "作者", "团队"])
    evaluation_focus = [
        key
        for key, hints in RESEARCH_SCOUT_EVALUATION_FOCUS.items()
        if any(hint in lowered for hint in hints)
    ]
    explicit_hard = any(hint in lowered for hint in RESEARCH_SCOUT_HARD_CONSTRAINT_HINTS)
    constraint_mode = "hard" if explicit_hard or years or venues or institutions or authors else "soft"
    return {
        "topic": " ".join(tokens[:8]) or query,
        "years": years,
        "methods": sorted(set(methods)),
        "datasets": sorted(set(datasets)),
        "tasks": sorted(set(tasks)),
        "preferences": preferences or ["relevance"],
        "venues": _dedupe_preserve(venues),
        "institutions": _dedupe_preserve(institutions),
        "authors": _dedupe_preserve(authors),
        "constraint_mode": constraint_mode,
        "evaluation_focus": evaluation_focus or ["novelty", "relevance", "reproducibility", "impact", "experiment_quality", "risk"],
        "search_depth": search_depth,
    }


RESEARCH_SCOUT_QUERY_LIMITS = {"quick": 2, "standard": 4, "deep": 6}
RESEARCH_SCOUT_QUERY_NOISE_RE = re.compile(
    r"(请帮我|帮我|请|找|搜索|检索|推荐|列出|整理|论文|几篇|一些|关于|有关|的|paper|papers|find|search|recommend|list)",
    re.IGNORECASE,
)


def _clean_research_scout_query(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(value or "").strip())
    cleaned = cleaned.strip(" ,;:，。；：")
    if not cleaned:
        return ""
    cleaned = re.sub(r"\b\d+\s*(?:篇|papers?)?\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = RESEARCH_SCOUT_QUERY_NOISE_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:，。；：")
    return cleaned


def _fallback_research_scout_queries(query: str, intent: dict[str, Any], limit: int = 4) -> list[str]:
    raw = _clean_research_scout_query(query)
    lowered = (query or "").lower()
    variants: list[str] = []
    if any(term in query for term in ["多模态大模型", "多模态大语言模型"]) or "mllm" in lowered:
        variants.extend([
            "multimodal large language model",
            "MLLM",
            "vision language model",
        ])
    if any(term in query for term in ["视觉语言模型", "视觉-语言模型"]) or "vlm" in lowered:
        variants.extend(["vision language model", "visual language model", "VLM"])
    if any(term in query for term in ["大语言模型", "大模型"]) or "llm" in lowered:
        variants.extend(["large language model", "LLM"])
    if "memory" in lowered or "记忆" in query:
        memory_variants = ["memory", "long term memory", "memory augmented"]
        if variants:
            variants = [f"{base} {suffix}" for base in variants[:4] for suffix in memory_variants[:2]]
            variants.append("memory augmented multimodal large language model")
        else:
            variants.extend(memory_variants)
    if (
        "video grounding" in lowered
        or "视频定位" in query
        or "视频 grounding" in lowered
        or "temporal grounding" in lowered
        or "moment retrieval" in lowered
    ):
        variants.extend([
            "video grounding",
            "temporal video grounding",
            "video moment retrieval",
            "natural language video localization",
            "temporal sentence grounding",
            "moment localization",
            "text-to-video moment retrieval",
            "video temporal localization",
            "video-language grounding",
        ])
    methods = intent.get("methods") or []
    tasks = intent.get("tasks") or []
    topic_terms = [str(item) for item in [raw, *methods, *tasks] if item]
    if topic_terms:
        variants.append(" ".join(topic_terms[:6]))
    variants.append(raw or query)
    return _dedupe_preserve(variants)[:limit]


def _coerce_research_scout_planned_queries(parsed: Any, fallback: list[str], limit: int) -> list[str]:
    if not isinstance(parsed, dict):
        return fallback[:limit]
    queries = parsed.get("queries")
    if not isinstance(queries, list):
        return fallback[:limit]
    cleaned = []
    for item in queries:
        if isinstance(item, dict):
            value = item.get("query") or item.get("text")
        else:
            value = item
        value = _clean_research_scout_query(str(value or ""))
        if value and len(value) <= 120:
            cleaned.append(value)
    return _dedupe_preserve([*cleaned, *fallback])[:limit]


async def _plan_research_scout_queries(query: str, intent: dict[str, Any], search_depth: str, final_limit: int | None = None) -> list[str]:
    base_limit = RESEARCH_SCOUT_QUERY_LIMITS.get(search_depth, RESEARCH_SCOUT_QUERY_LIMITS["standard"])
    limit = min(8, max(base_limit, 6 if (final_limit or 0) >= 20 else base_limit))
    fallback = _fallback_research_scout_queries(query, intent, limit=limit)
    prompt = (
        "你是学术论文检索 query planner。请根据用户问题生成适合 arXiv、Semantic Scholar、OpenAlex 的英文检索关键词。"
        "要求：只输出 JSON；queries 是 2-8 个英文短 query；优先使用学术常用术语、缩写、同义任务名；不要包含中文礼貌请求、数量词或无关解释。"
        "如果用户问题是中文，先理解研究方向再翻译/扩展。"
        "\n输出格式：{\"queries\":[\"query 1\",\"query 2\"],\"aliases\":[\"...\"],\"rationale\":\"...\"}"
        "\n\n用户问题："
        f"{query}"
        "\n\n已解析意图："
        + json.dumps(intent, ensure_ascii=False)
        + "\n\n本地兜底候选："
        + json.dumps(fallback, ensure_ascii=False)
    )
    try:
        raw = await llm_service.chat(
            messages=[
                {"role": "system", "content": "你只返回可解析 JSON。不要 Markdown。不要编造论文，只规划检索 query。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=800,
        )
        return _coerce_research_scout_planned_queries(_extract_json_object(raw), fallback, limit)
    except Exception as exc:
        logger.warning("Research Scout query planning failed, using fallback queries: %s", exc)
        return fallback[:limit]


def _research_scout_score_dimension(
    *,
    score: int,
    reason: str,
    evidence: list[str],
    confidence: str = "medium",
) -> dict[str, Any]:
    bounded_score = max(1, min(5, int(score)))
    return {
        "score": bounded_score,
        "reason": reason,
        "evidence": evidence[:3] or ["当前检索元数据不足，需阅读全文确认。"],
        "confidence": confidence if confidence in {"high", "medium", "low"} else "medium",
    }


def _coerce_research_scout_dimension(value: Any, fallback: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return fallback
    try:
        score = int(value.get("score", fallback.get("score", 3)))
    except (TypeError, ValueError):
        score = int(fallback.get("score", 3))
    evidence = value.get("evidence")
    if not isinstance(evidence, list):
        evidence = fallback.get("evidence") or []
    confidence = value.get("confidence") if value.get("confidence") in {"high", "medium", "low"} else fallback.get("confidence", "medium")
    reason = str(value.get("reason") or fallback.get("reason") or "基于可见检索元数据的保守评估。")[:260]
    return _research_scout_score_dimension(
        score=score,
        reason=reason,
        evidence=[str(item)[:220] for item in evidence if item],
        confidence=str(confidence),
    )


def _coerce_research_scout_evaluation(value: Any, fallback: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return fallback
    coerced = dict(fallback)
    for key in ["novelty", "relevance", "reproducibility", "impact", "experiment_quality", "risk"]:
        coerced[key] = _coerce_research_scout_dimension(value.get(key), fallback.get(key, {}))
    reading_priority = value.get("reading_priority")
    if reading_priority in {"high", "medium", "low"}:
        coerced["reading_priority"] = reading_priority
    focus = value.get("focus")
    if isinstance(focus, list):
        coerced["focus"] = [str(item) for item in focus if item][:6]
    coerced["source"] = "llm"
    return coerced


def _extract_json_object(text: str) -> Any:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise


def _research_scout_query_matches(paper: PaperResult, query: str) -> list[str]:
    blob = _research_scout_text_blob(paper)
    terms = [
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", (query or "").lower())
        if term not in {"find", "some", "paper", "papers", "about", "with", "from", "into", "that", "using"}
    ]
    return [term for term in _dedupe_preserve(terms) if term in blob][:6]


def _research_scout_constraint_matches(paper: PaperResult, intent: dict[str, Any]) -> dict[str, Any]:
    metadata = getattr(paper, "metadata", {}) or {}
    blob = _research_scout_text_blob(paper)
    venue = _research_scout_venue_from_metadata(metadata)
    institutions = _research_scout_institutions_from_metadata(metadata)
    author_blob = " ".join(paper.authors or []).lower()

    def match_values(values: list[str], *, target: str | None = None, fallback_blob: str = blob) -> list[str]:
        matches = []
        for value in values or []:
            normalized = value.lower()
            if (target and normalized in target.lower()) or normalized in fallback_blob:
                matches.append(value)
        return _dedupe_preserve(matches)

    venue_matches = match_values(intent.get("venues") or [], target=venue)
    institution_matches = match_values(intent.get("institutions") or [], target=" ".join(institutions))
    author_matches = match_values(intent.get("authors") or [], fallback_blob=author_blob)
    requested = {
        "venues": intent.get("venues") or [],
        "institutions": intent.get("institutions") or [],
        "authors": intent.get("authors") or [],
    }
    return {
        "constraint_mode": intent.get("constraint_mode") or "soft",
        "venue": {
            "requested": requested["venues"],
            "matched": venue_matches,
            "available": venue,
            "status": "matched" if venue_matches else ("not_requested" if not requested["venues"] else "unknown"),
        },
        "institution": {
            "requested": requested["institutions"],
            "matched": institution_matches,
            "available": institutions,
            "status": "matched" if institution_matches else ("not_requested" if not requested["institutions"] else "unknown"),
        },
        "author": {
            "requested": requested["authors"],
            "matched": author_matches,
            "available": _compact_author_list(paper.authors or [], limit=5),
            "status": "matched" if author_matches else ("not_requested" if not requested["authors"] else "unknown"),
        },
    }


def _research_scout_candidate_evaluation(
    paper: PaperResult,
    query: str,
    intent: dict[str, Any],
    constraint_matches: dict[str, Any],
) -> dict[str, Any]:
    metadata = getattr(paper, "metadata", {}) or {}
    query_matches = _research_scout_query_matches(paper, query)
    concepts = [str(item) for item in (metadata.get("concepts") or []) if item]
    year = paper.year or 0
    citation_count = int(paper.citation_count or 0)
    current_year = 2026
    is_recent = bool(year and year >= current_year - 2)
    has_pdf = bool(paper.pdf_url)
    has_open_metadata = bool(metadata.get("open_access") or paper.pdf_url)
    has_dataset = any(dataset.lower() in _research_scout_text_blob(paper) for dataset in intent.get("datasets") or [])
    has_experiment_terms = any(
        term in _research_scout_text_blob(paper)
        for term in ["benchmark", "dataset", "experiment", "ablation", "evaluation", "state-of-the-art", "实验", "消融", "基准"]
    )
    matched_constraints = [
        match
        for group in ("venue", "institution", "author")
        for match in (constraint_matches.get(group, {}) or {}).get("matched", [])
    ]

    relevance_score = 2 + min(len(query_matches), 3)
    if matched_constraints:
        relevance_score += 1
    novelty_score = 3 + (1 if is_recent else 0) + (1 if any(pref in intent.get("preferences", []) for pref in ["novel_or_interesting", "recent"]) else 0)
    reproducibility_score = 2 + (1 if has_pdf else 0) + (1 if any(term in _research_scout_text_blob(paper) for term in ["code", "github", "dataset", "benchmark"]) else 0)
    impact_score = 2 + (1 if citation_count >= 25 else 0) + (1 if citation_count >= 100 else 0) + (1 if paper.source in {"semantic_scholar", "openalex"} else 0)
    experiment_score = 2 + (1 if has_dataset else 0) + (1 if has_experiment_terms else 0) + (1 if concepts else 0)
    risk_score = 2
    if not has_pdf:
        risk_score += 1
    if not paper.abstract:
        risk_score += 1
    if intent.get("constraint_mode") == "hard" and any(
        constraint_matches.get(group, {}).get("status") == "unknown"
        for group in ("venue", "institution", "author")
        if constraint_matches.get(group, {}).get("requested")
    ):
        risk_score += 1

    novelty_confidence = "medium" if paper.abstract or year else "low"
    reproducibility_confidence = "medium" if has_pdf or has_open_metadata else "low"
    impact_confidence = "high" if citation_count else "low"
    experiment_confidence = "medium" if paper.abstract else "low"
    relevance_confidence = "high" if query_matches or matched_constraints else "medium"
    risk_confidence = "medium" if paper.abstract or has_pdf else "low"

    evaluation = {
        "novelty": _research_scout_score_dimension(
            score=novelty_score,
            reason="近期论文或用户明确偏好新颖性会提高初筛创新性评分。",
            evidence=[*( [f"{paper.year} 年论文"] if paper.year else [] ), *( ["用户要求偏新颖/近期"] if any(pref in intent.get("preferences", []) for pref in ["novel_or_interesting", "recent"]) else [] )],
            confidence=novelty_confidence,
        ),
        "relevance": _research_scout_score_dimension(
            score=relevance_score,
            reason="根据题名、摘要、作者、venue 与用户检索词的重合度进行相关性初筛。",
            evidence=[*( [f"匹配关键词：{', '.join(query_matches[:4])}"] if query_matches else [] ), *( [f"匹配约束：{', '.join(matched_constraints[:3])}"] if matched_constraints else [] )],
            confidence=relevance_confidence,
        ),
        "reproducibility": _research_scout_score_dimension(
            score=reproducibility_score,
            reason="开放 PDF、代码/数据集/benchmark 线索会提高可复现性评分。",
            evidence=[*( ["有开放 PDF"] if has_pdf else [] ), *( ["摘要或元数据出现代码/数据集/benchmark 线索"] if any(term in _research_scout_text_blob(paper) for term in ["code", "github", "dataset", "benchmark"]) else [] )],
            confidence=reproducibility_confidence,
        ),
        "impact": _research_scout_score_dimension(
            score=impact_score,
            reason="基于检索源提供的引用数和索引来源估计影响力。",
            evidence=[*( [f"引用数约 {citation_count}"] if citation_count else [] ), f"来源：{paper.source or 'unknown'}"],
            confidence=impact_confidence,
        ),
        "experiment_quality": _research_scout_score_dimension(
            score=experiment_score,
            reason="根据摘要中实验、数据集、benchmark、消融等线索估计实验完整度。",
            evidence=[*( ["匹配用户指定数据集"] if has_dataset else [] ), *( ["摘要出现实验/benchmark/消融线索"] if has_experiment_terms else [] ), *( [f"OpenAlex concepts: {', '.join(concepts[:3])}"] if concepts else [] )],
            confidence=experiment_confidence,
        ),
        "risk": _research_scout_score_dimension(
            score=risk_score,
            reason="分数越高表示初筛风险越高，主要来自 PDF/摘要缺失或硬约束无法确认。",
            evidence=[
                *( ["未发现开放 PDF"] if not has_pdf else [] ),
                *( ["摘要缺失"] if not paper.abstract else [] ),
                *( ["硬约束尚未完全确认"] if risk_score >= 4 else [] ),
            ],
            confidence=risk_confidence,
        ),
    }
    positive_average = (
        evaluation["novelty"]["score"]
        + evaluation["relevance"]["score"]
        + evaluation["reproducibility"]["score"]
        + evaluation["impact"]["score"]
        + evaluation["experiment_quality"]["score"]
    ) / 5
    risk_penalty = evaluation["risk"]["score"] * 0.35
    priority_value = positive_average - risk_penalty
    evaluation["reading_priority"] = "high" if priority_value >= 3.2 else "medium" if priority_value >= 2.35 else "low"
    evaluation["focus"] = intent.get("evaluation_focus") or []
    evaluation["source"] = "heuristic"
    return evaluation


def _research_scout_candidate(paper: PaperResult, query: str, rank: int, intent: dict[str, Any]) -> dict[str, Any]:
    metadata = getattr(paper, "metadata", {}) or {}
    remote_id = metadata.get("remote_id") or paper.arxiv_id or paper.doi or paper.source_url or paper.title
    rationale = _research_scout_rationale(paper, query, rank)
    venue = _research_scout_venue_from_metadata(metadata)
    institutions = _research_scout_institutions_from_metadata(metadata)
    metadata_provenance = _research_scout_metadata_provenance(metadata)
    enrichment = metadata.get("enrichment") if isinstance(metadata.get("enrichment"), dict) else {}
    constraint_matches = _research_scout_constraint_matches(paper, intent)
    evaluation = _research_scout_candidate_evaluation(paper, query, intent, constraint_matches)
    return {
        "rank": rank,
        "title": paper.title,
        "authors": _compact_author_list(paper.authors or []),
        "abstract": paper.abstract or "",
        "year": paper.year,
        "venue": venue,
        "institutions": institutions,
        "journal_ref": metadata.get("journal_ref"),
        "comment": metadata.get("comment"),
        "pdf_first_page_affiliations": metadata.get("pdf_first_page_affiliations") or [],
        "metadata_provenance": metadata_provenance,
        "enrichment": enrichment,
        "source": paper.source,
        "source_url": paper.source_url,
        "pdf_url": paper.pdf_url,
        "arxiv_id": paper.arxiv_id,
        "doi": paper.doi,
        "citation_count": paper.citation_count,
        "categories": paper.categories or [],
        "remote_id": remote_id,
        "ingest_token": create_remote_ingest_token(paper),
        "constraint_matches": constraint_matches,
        "evaluation": evaluation,
        **rationale,
    }


def _research_scout_provider_label(source: str | None) -> str:
    labels = {
        "arxiv": "arXiv PDF",
        "semantic_scholar": "Semantic Scholar",
        "openalex": "OpenAlex",
        "google_scholar": "Google Scholar/SerpApi",
        "cvf_openaccess": "CVF OpenAccess",
    }
    return labels.get(source or "", source or "scholarly")


def _research_scout_result_source_order(paper: PaperResult) -> int:
    if paper.source == "cvf_openaccess":
        return 0
    if paper.source == "arxiv" or paper.arxiv_id:
        return 1
    if paper.pdf_url:
        return 2
    if paper.source in {"semantic_scholar", "openalex"}:
        return 3
    return 4


def _score_research_scout_paper(
    paper: PaperResult,
    query: str,
    planned_queries: list[str],
    intent: dict[str, Any],
) -> float:
    score = 0.0
    retrieval_query = " ".join([query, *planned_queries])
    query_matches = _research_scout_query_matches(paper, retrieval_query)
    score += min(len(query_matches), 6) * 10

    if paper.source == "cvf_openaccess":
        score += 18
    if paper.source == "arxiv":
        score += 16
    if paper.arxiv_id:
        score += 14
    if paper.pdf_url:
        score += 10

    citation_count = max(int(paper.citation_count or 0), 0)
    if citation_count:
        score += min(18, citation_count ** 0.5)

    year = int(paper.year or 0)
    year_from, year_to = _research_scout_year_range(intent)
    if year and year_from and year < year_from:
        score -= 80
    if year and year_to and year > year_to:
        score -= 80
    if year >= 2025:
        score += 7
    elif year >= 2023:
        score += 5
    elif year >= 2020:
        score += 2

    constraint_matches = _research_scout_constraint_matches(paper, intent)
    for group in ("venue", "institution", "author"):
        match = constraint_matches.get(group, {}) or {}
        if match.get("matched"):
            score += 12
        elif intent.get("constraint_mode") == "hard" and match.get("requested"):
            score -= 10

    if paper.abstract:
        score += 3
    return score


def _rank_research_scout_papers(
    papers: list[PaperResult],
    query: str,
    planned_queries: list[str],
    intent: dict[str, Any],
    limit: int,
) -> list[PaperResult]:
    deduped = deduplicate_papers(papers)
    ranked = sorted(
        enumerate(deduped),
        key=lambda item: (
            -_score_research_scout_paper(item[1], query, planned_queries, intent),
            _research_scout_result_source_order(item[1]),
            -(item[1].year or 0),
            item[0],
        ),
    )
    return [paper for _, paper in ranked[:limit]]


def _research_scout_constraint_filter(
    papers: list[PaperResult],
    intent: dict[str, Any],
) -> tuple[list[PaperResult], dict[str, int]]:
    year_from, year_to = _research_scout_year_range(intent)
    hard_mode = _research_scout_constraint_mode(intent) == "hard"
    stats = {
        "year": 0,
        "venue": 0,
        "institution": 0,
        "author": 0,
        "unknown": 0,
    }
    filtered: list[PaperResult] = []
    for paper in papers:
        if paper.year and year_from and paper.year < year_from:
            stats["year"] += 1
            continue
        if paper.year and year_to and paper.year > year_to:
            stats["year"] += 1
            continue
        matches = _research_scout_constraint_matches(paper, intent)
        excluded = False
        if hard_mode:
            for group in ("venue", "institution", "author"):
                requested = matches.get(group, {}).get("requested") or []
                status = matches.get(group, {}).get("status")
                if requested and status != "matched":
                    stats[group] += 1
                    excluded = True
                    break
        if excluded:
            continue
        filtered.append(paper)
    return filtered, stats


async def _search_research_scout_cvf_stage(
    query: str,
    planned_queries: list[str],
    intent: dict[str, Any],
    max_results: int,
) -> list[PaperResult]:
    venues = _research_scout_cvf_venues(intent)
    if not venues:
        return []
    year_from, year_to = _research_scout_year_range(intent)
    if not year_from or not year_to:
        return []
    years = list(range(year_from, year_to + 1))
    tasks = []
    for venue in venues:
        for year in years:
            for planned_query in planned_queries or [query]:
                tasks.append(search_cvf_openaccess(
                    venue=venue,
                    year=year,
                    query=planned_query,
                    max_results=max_results,
                ))
    groups = await asyncio.gather(*tasks, return_exceptions=True)
    papers: list[PaperResult] = []
    for group in groups:
        if isinstance(group, Exception):
            logger.warning("Research Scout CVF query failed: %s", group)
            continue
        papers.extend(group)
    return deduplicate_papers(papers)


async def _run_research_scout_search_stage(
    planned_queries: list[str],
    *,
    source: str,
    max_results: int,
    sort_by: str = "relevance",
    year_from: int | None = None,
    year_to: int | None = None,
    venue: str | None = None,
) -> list[PaperResult]:
    groups = await asyncio.gather(*[
        search_scholarly_papers(
            planned_query,
            source=source,
            max_results=max_results,
            sort_by=sort_by,
            year_from=year_from,
            year_to=year_to,
            venue=venue,
        )
        for planned_query in planned_queries
    ], return_exceptions=True)

    papers: list[PaperResult] = []
    for group in groups:
        if isinstance(group, Exception):
            logger.warning("Research Scout %s query failed: %s", source, group)
            continue
        papers.extend(group)
    return papers


async def _retrieve_research_scout_papers(
    query: str,
    planned_queries: list[str],
    intent: dict[str, Any],
    limit: int,
    count_info: dict[str, Any] | None = None,
) -> tuple[list[PaperResult], dict[str, Any]]:
    pool_target = min(
        max(limit * RESEARCH_SCOUT_POOL_MULTIPLIER, limit + 12, 24),
        max(limit, RESEARCH_SCOUT_MAX_FINAL_RESULTS) * 5,
    )
    per_query_limit = min(
        RESEARCH_SCOUT_MAX_PER_QUERY_RESULTS,
        max(12, (pool_target + max(len(planned_queries), 1) - 1) // max(len(planned_queries), 1)),
    )
    year_from, year_to = _research_scout_year_range(intent)
    primary_venue = (intent.get("venues") or [None])[0]
    cvf_papers = await _search_research_scout_cvf_stage(
        query,
        planned_queries,
        intent,
        max_results=per_query_limit,
    )
    cvf_unique = deduplicate_papers(cvf_papers)
    arxiv_papers = await _run_research_scout_search_stage(
        planned_queries,
        source="arxiv_enriched",
        max_results=per_query_limit,
        year_from=year_from,
        year_to=year_to,
        venue=primary_venue,
    )
    arxiv_unique = deduplicate_papers(arxiv_papers)

    fallback_used = len(deduplicate_papers([*cvf_unique, *arxiv_unique])) < limit
    fallback_papers: list[PaperResult] = []
    if fallback_used:
        fallback_papers = await _run_research_scout_search_stage(
            planned_queries,
            source="scholarly",
            max_results=per_query_limit,
            year_from=year_from,
            year_to=year_to,
            venue=primary_venue,
        )

    merged = [*cvf_unique, *arxiv_unique, *fallback_papers]
    filtered, exclusion_stats = _research_scout_constraint_filter(merged, intent)
    ranked = _rank_research_scout_papers(filtered, query, planned_queries, intent, limit)
    expanded_queries: list[str] = []
    expanded_papers: list[PaperResult] = []
    if len(ranked) < limit:
        expanded_queries = [
            item for item in _fallback_research_scout_queries(query, intent, limit=8)
            if item not in planned_queries
        ]
        if expanded_queries:
            expanded_papers = await _run_research_scout_search_stage(
                expanded_queries,
                source="scholarly",
                max_results=min(RESEARCH_SCOUT_MAX_PER_QUERY_RESULTS, max(per_query_limit, limit)),
                year_from=year_from,
                year_to=year_to,
                venue=primary_venue,
            )
            merged = [*merged, *expanded_papers]
            filtered, exclusion_stats = _research_scout_constraint_filter(merged, intent)
            ranked = _rank_research_scout_papers(filtered, query, [*planned_queries, *expanded_queries], intent, limit)
    provider_labels = list(dict.fromkeys(_research_scout_provider_label(paper.source) for paper in ranked))
    fallback_labels = list(dict.fromkeys(_research_scout_provider_label(paper.source) for paper in fallback_papers))
    unique_pool_count = len(deduplicate_papers(merged))
    underfilled_by = max(0, limit - len(ranked))
    metadata = {
        "strategy": "arxiv_first_then_scholarly_fallback" if fallback_used else "arxiv_first_enriched",
        "fallback_used": fallback_used,
        "planned_queries": planned_queries,
        "expanded_queries": expanded_queries,
        "providers": provider_labels or ["arXiv PDF", "Semantic Scholar", "OpenAlex"],
        "fallback_providers": fallback_labels,
        "year_from": year_from,
        "year_to": year_to,
        "venues": intent.get("venues") or [],
        "constraint_mode": _research_scout_constraint_mode(intent),
        "constraint_exclusions": exclusion_stats,
        "requested_count": (count_info or {}).get("requested_count"),
        "default_count": (count_info or {}).get("default_count"),
        "final_limit": limit,
        "max_final_limit": (count_info or {}).get("max_final_limit", RESEARCH_SCOUT_MAX_FINAL_RESULTS),
        "count_capped": bool((count_info or {}).get("capped")),
        "pool_target": pool_target,
        "per_query_limit": per_query_limit,
        "unique_pool_count": unique_pool_count,
        "underfilled_by": underfilled_by,
        "stage_counts": {
            "cvf_openaccess": len(cvf_unique),
            "arxiv_enriched": len(arxiv_unique),
            "scholarly_fallback": len(deduplicate_papers(fallback_papers)) if fallback_used else 0,
            "expanded_fallback": len(deduplicate_papers(expanded_papers)) if expanded_papers else 0,
            "pool": unique_pool_count,
            "filtered": len(filtered),
            "ranked": len(ranked),
        },
        "candidate_count": len(ranked),
    }
    return ranked, metadata


async def _apply_llm_research_scout_evaluations(
    candidates: list[dict[str, Any]],
    query: str,
    intent: dict[str, Any],
) -> list[dict[str, Any]]:
    if not candidates:
        return candidates
    evaluation_targets = []
    for item in candidates[:6]:
        evaluation_targets.append({
            "rank": item.get("rank"),
            "title": item.get("title"),
            "year": item.get("year"),
            "venue": item.get("venue"),
            "authors": item.get("authors"),
            "institutions": item.get("institutions"),
            "citation_count": item.get("citation_count"),
            "pdf_available": bool(item.get("pdf_url")),
            "constraint_matches": item.get("constraint_matches"),
            "heuristic_evaluation": item.get("evaluation"),
            "abstract": (item.get("abstract") or "")[:1200],
        })
    prompt = (
        "你是科研论文初筛评估器。请只基于输入 JSON 中的题名、摘要、作者、venue、机构、引用、PDF 状态、约束匹配和 heuristic_evaluation，"
        "为每篇候选输出结构化 JSON。不要引入外部知识，不要声称已读全文。"
        "如果证据不足，confidence 必须为 low，reason 需说明无法确认。"
        "每个维度 score 为 1-5；risk 分数越高表示风险越高。"
        "只输出 JSON 对象，不要 Markdown。格式："
        '{"evaluations":[{"rank":1,"evaluation":{"novelty":{"score":3,"reason":"...","evidence":["..."],"confidence":"medium"},"relevance":{...},"reproducibility":{...},"impact":{...},"experiment_quality":{...},"risk":{...},"reading_priority":"high","focus":["novelty"]}}]}'
        "\n\n输入："
        + json.dumps(
            {
                "query": query,
                "intent": intent,
                "candidates": evaluation_targets,
            },
            ensure_ascii=False,
        )
    )
    try:
        raw = await llm_service.chat(
            messages=[
                {"role": "system", "content": "你只返回可解析 JSON。禁止编造输入之外的论文事实。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.15,
            max_tokens=2600,
        )
        parsed = _extract_json_object(raw)
    except Exception as exc:
        logger.warning("Research Scout LLM evaluation failed, using heuristic evaluation: %s", exc)
        return candidates

    evaluations = parsed.get("evaluations") if isinstance(parsed, dict) else None
    if not isinstance(evaluations, list):
        return candidates
    by_rank = {
        int(item.get("rank")): item.get("evaluation")
        for item in evaluations
        if isinstance(item, dict) and str(item.get("rank", "")).isdigit()
    }
    enriched = []
    for item in candidates:
        rank = item.get("rank")
        fallback = item.get("evaluation") or {}
        if rank in by_rank:
            item = {
                **item,
                "evaluation": _coerce_research_scout_evaluation(by_rank[rank], fallback),
            }
        enriched.append(item)
    return enriched


def _research_scout_reference(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": candidate.get("title"),
        "arxiv_id": candidate.get("arxiv_id"),
        "year": candidate.get("year"),
        "venue": candidate.get("venue"),
        "url": candidate.get("source_url"),
        "pdf_url": candidate.get("pdf_url"),
        "source": "research_scout",
        "provider": candidate.get("source"),
        "rank": candidate.get("rank"),
        "why_useful": candidate.get("why_useful"),
    }


def _tool_trace_step(
    step_id: str,
    tool: str,
    label: str,
    status: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": step_id,
        "tool": tool,
        "label": label,
        "status": status,
        "summary": summary,
        "details": details or {},
    }


def _research_scout_tool_trace(
    query: str,
    intent: dict[str, Any] | None,
    candidates: list[dict[str, Any]],
    planned_queries: list[str] | None = None,
    retrieval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(retrieval, dict) and isinstance(retrieval.get("agent_trace"), dict):
        return retrieval["agent_trace"]
    candidate_count = len(candidates)
    llm_evaluated = sum(1 for item in candidates[:6] if (item.get("evaluation") or {}).get("source") == "llm")
    high_priority = [
        item.get("title")
        for item in candidates
        if (item.get("evaluation") or {}).get("reading_priority") == "high"
    ][:3]
    retrieval = retrieval or {}
    fallback_used = bool(retrieval.get("fallback_used"))
    providers = retrieval.get("providers") or ["arXiv PDF", "Semantic Scholar enrichment", "OpenAlex enrichment"]
    stage_counts = retrieval.get("stage_counts") or {}
    final_limit = retrieval.get("final_limit") or candidate_count
    requested_count = retrieval.get("requested_count")
    pool_count = retrieval.get("unique_pool_count")
    capped_note = "；请求数量已按系统上限截断" if retrieval.get("count_capped") else ""
    underfilled_note = f"；仍缺 {retrieval.get('underfilled_by')} 篇" if retrieval.get("underfilled_by") else ""
    search_summary = (
        f"arXiv-first 检索候选不足，已扩展到 Semantic Scholar/OpenAlex/Google Scholar 等学术来源，目标 {final_limit} 篇，候选池 {pool_count or candidate_count} 篇，最终找到 {candidate_count} 篇{capped_note}{underfilled_note}。"
        if fallback_used
        else f"已优先检索 arXiv PDF，并用 Semantic Scholar/OpenAlex 增强元数据，目标 {final_limit} 篇，候选池 {pool_count or candidate_count} 篇，最终找到 {candidate_count} 篇{capped_note}{underfilled_note}。"
    )
    steps = [
        _tool_trace_step(
            "parse-intent",
            "parse_intent",
            "拆解检索意图",
            "completed",
            "已提取主题、任务、方法、数据集、约束和评估重点。",
            {
                "topic": (intent or {}).get("topic"),
                "constraint_mode": (intent or {}).get("constraint_mode"),
                "venues": (intent or {}).get("venues") or [],
                "institutions": (intent or {}).get("institutions") or [],
                "authors": (intent or {}).get("authors") or [],
                "evaluation_focus": (intent or {}).get("evaluation_focus") or [],
            },
        ),
        _tool_trace_step(
            "search-papers",
            "search_papers",
            "检索论文候选",
            "completed",
            search_summary,
            {
                "query": query,
                "planned_queries": retrieval.get("planned_queries") or planned_queries or [query],
                "expanded_queries": retrieval.get("expanded_queries") or [],
                "requested_count": requested_count,
                "final_limit": final_limit,
                "max_final_limit": retrieval.get("max_final_limit"),
                "count_capped": bool(retrieval.get("count_capped")),
                "pool_target": retrieval.get("pool_target"),
                "per_query_limit": retrieval.get("per_query_limit"),
                "unique_pool_count": retrieval.get("unique_pool_count"),
                "underfilled_by": retrieval.get("underfilled_by") or 0,
                "providers": providers,
                "strategy": retrieval.get("strategy") or "arxiv_first_enriched",
                "fallback_used": fallback_used,
                "fallback_providers": retrieval.get("fallback_providers") or [],
                "stage_counts": stage_counts,
                "candidate_count": candidate_count,
            },
        ),
        _tool_trace_step(
            "evaluate-papers",
            "evaluate_papers",
            "评估候选论文",
            "completed",
            f"已完成 {candidate_count} 篇候选的结构化评估，其中 {llm_evaluated} 篇由 LLM 校准。",
            {
                "candidate_count": candidate_count,
                "llm_evaluated": llm_evaluated,
                "dimensions": ["novelty", "relevance", "reproducibility", "impact", "experiment_quality", "risk"],
            },
        ),
        _tool_trace_step(
            "rank-recommendations",
            "rank_recommendations",
            "生成阅读优先级",
            "completed" if candidate_count else "skipped",
            "已生成优先阅读候选。" if candidate_count else "没有候选，跳过排序。",
            {
                "top_candidates": high_priority,
            },
        ),
        _tool_trace_step(
            "paper-actions",
            "import_paper",
            "等待用户确认入库",
            "available" if candidate_count else "skipped",
            "候选卡片可一键入库、加入分类或加入研究方向；不会自动执行副作用操作。",
            {
                "available_actions": ["import_paper", "add_to_folder", "add_to_project"] if candidate_count else [],
            },
        ),
    ]
    return {
        "enabled": True,
        "workflow": "research_scout",
        "steps": steps,
    }


def _format_research_scout_intent(intent: dict[str, Any]) -> str:
    fields = []
    labels = {
        "topic": "Topic",
        "years": "Years",
        "methods": "Methods",
        "datasets": "Datasets",
        "tasks": "Tasks",
        "preferences": "Preferences",
        "venues": "Venues",
        "institutions": "Institutions",
        "authors": "Authors",
        "constraint_mode": "Constraint mode",
        "evaluation_focus": "Evaluation focus",
    }
    for key, label in labels.items():
        value = intent.get(key)
        if isinstance(value, list) and value:
            fields.append(f"{label}: {', '.join(str(item) for item in value)}")
        elif isinstance(value, str) and value:
            fields.append(f"{label}: {value}")
    return "\n".join(fields)


def _research_scout_context_candidate_limit(candidate_count: int, retrieval: dict[str, Any] | None = None) -> int:
    if candidate_count <= 0:
        return 0
    retrieval = retrieval or {}
    raw_limit = retrieval.get("final_limit") or retrieval.get("requested_count") or candidate_count
    try:
        requested_limit = int(raw_limit)
    except (TypeError, ValueError):
        requested_limit = candidate_count
    bounded_limit = max(1, min(requested_limit, RESEARCH_SCOUT_MAX_FINAL_RESULTS))
    return min(candidate_count, bounded_limit)


def _format_research_scout_context(
    candidates: list[dict[str, Any]],
    intent: dict[str, Any],
    *,
    context_limit: int | None = None,
    retrieval: dict[str, Any] | None = None,
) -> str:
    if not candidates:
        return ""
    retrieval = retrieval or {}
    total_candidates = len(candidates)
    if context_limit is None:
        context_limit = _research_scout_context_candidate_limit(total_candidates, retrieval)
    safe_context_limit = max(0, min(int(context_limit or 0), total_candidates, RESEARCH_SCOUT_MAX_FINAL_RESULTS))
    context_diagnostics = [
        f"ranked_candidates={total_candidates}",
        f"included_candidates={safe_context_limit}",
    ]
    if retrieval.get("requested_count"):
        context_diagnostics.append(f"requested_count={retrieval.get('requested_count')}")
    if retrieval.get("final_limit"):
        context_diagnostics.append(f"final_limit={retrieval.get('final_limit')}")
    if retrieval.get("underfilled_by"):
        context_diagnostics.append(f"underfilled_by={retrieval.get('underfilled_by')}")
    blocks = []
    for item in candidates[:safe_context_limit]:
        abstract = (item.get("abstract") or "")[:900]
        evaluation = item.get("evaluation") or {}
        constraint_matches = item.get("constraint_matches") or {}
        evaluation_summary = ", ".join(
            f"{key}={value.get('score')}/5 ({value.get('confidence')})"
            for key, value in evaluation.items()
            if isinstance(value, dict) and "score" in value
        )
        constraint_summary = "; ".join(
            f"{key}: {value.get('status')} matched={', '.join(value.get('matched') or []) or 'none'}"
            for key, value in constraint_matches.items()
            if isinstance(value, dict) and key in {"venue", "institution", "author"}
        )
        blocks.append(
            "\n".join([
                f"[PAPER-{item['rank']}] {item.get('title') or 'Untitled'}",
                f"Source: {item.get('source') or 'unknown'} | Venue: {item.get('venue') or 'unknown'} | Year: {item.get('year') or 'unknown'} | Citations: {item.get('citation_count') or 0}",
                f"Authors: {', '.join(item.get('authors') or [])}",
                f"Institutions: {', '.join(item.get('institutions') or []) or 'unknown'}",
                f"Constraint matches: {constraint_summary or 'none requested'}",
                f"Evaluation: {evaluation_summary or 'not available'} | reading_priority={evaluation.get('reading_priority') or 'unknown'}",
                f"Why interesting: {item.get('why_interesting')}",
                f"Why useful: {item.get('why_useful')}",
                f"Abstract: {abstract}",
            ])
        )
    return (
        f"Parsed user intent:\n{_format_research_scout_intent(intent)}\n\n"
        f"Context diagnostics: {' | '.join(context_diagnostics)}\n\n"
        "Candidate papers:\n" + "\n\n".join(blocks)
    )


def _format_research_scout_retrieval_note(retrieval: dict[str, Any]) -> str:
    if not retrieval:
        return ""
    requested = retrieval.get("requested_count")
    final_limit = retrieval.get("final_limit")
    candidate_count = retrieval.get("candidate_count")
    pool_count = retrieval.get("unique_pool_count")
    pool_target = retrieval.get("pool_target")
    capped = bool(retrieval.get("count_capped"))
    underfilled_by = int(retrieval.get("underfilled_by") or 0)
    parts = [
        f"requested_count={requested if requested else 'not specified'}",
        f"final_limit={final_limit}",
        f"ranked_candidates={candidate_count}",
        f"unique_pool_count={pool_count}",
        f"pool_target={pool_target}",
    ]
    if capped:
        parts.append(f"requested count capped at {retrieval.get('max_final_limit')}")
    if underfilled_by:
        parts.append(f"underfilled_by={underfilled_by}")
    return "Retrieval diagnostics: " + " | ".join(parts)


def _research_scout_constraints(
    query: str,
    search_depth: str,
    intent: dict[str, Any],
    count_info: dict[str, Any],
) -> ResearchScoutConstraints:
    year_from, year_to = _research_scout_year_range(intent)
    return ResearchScoutConstraints(
        original_query=query,
        search_depth=search_depth,
        requested_count=count_info.get("requested_count"),
        final_limit=int(count_info.get("final_limit") or RESEARCH_SCOUT_LIMITS.get(search_depth, 8)),
        year_from=year_from,
        year_to=year_to,
        venues=[str(item) for item in intent.get("venues") or []],
        institutions=[str(item) for item in intent.get("institutions") or []],
        authors=[str(item) for item in intent.get("authors") or []],
        datasets=[str(item) for item in intent.get("datasets") or []],
        tasks=[str(item) for item in intent.get("tasks") or []],
        methods=[str(item) for item in intent.get("methods") or []],
        preferences=[str(item) for item in intent.get("preferences") or []],
        constraint_mode=_research_scout_constraint_mode(intent),  # type: ignore[arg-type]
    )


async def _research_scout_tool_analyze_query(
    args: EmptyToolArgs,
    state: ResearchScoutAgentState,
) -> ResearchScoutToolObservation:
    state.intent = _research_scout_intent(state.constraints.original_query, state.constraints.search_depth)
    return ResearchScoutToolObservation(
        tool="analyze_research_query",
        summary="已分析 query，并抽取主题、年份、会议、机构、任务和评估偏好。",
        result_count=1,
        details={
            "intent": state.intent,
            "constraints": state.constraints.model_dump(),
        },
    )


async def _research_scout_tool_expand_queries(
    args: EmptyToolArgs,
    state: ResearchScoutAgentState,
) -> ResearchScoutToolObservation:
    state.planned_queries = await _plan_research_scout_queries(
        state.constraints.original_query,
        state.intent,
        state.constraints.search_depth,
        final_limit=state.constraints.final_limit,
    )
    return ResearchScoutToolObservation(
        tool="expand_paper_queries",
        summary=f"已生成 {len(state.planned_queries)} 个学术检索 query。",
        result_count=len(state.planned_queries),
        details={"planned_queries": state.planned_queries},
    )


async def _research_scout_tool_search_papers(
    args: EmptyToolArgs,
    state: ResearchScoutAgentState,
) -> ResearchScoutToolObservation:
    count_info = {
        "requested_count": state.constraints.requested_count,
        "default_count": RESEARCH_SCOUT_LIMITS.get(state.constraints.search_depth, RESEARCH_SCOUT_LIMITS["standard"]),
        "final_limit": state.constraints.final_limit,
        "max_final_limit": RESEARCH_SCOUT_MAX_FINAL_RESULTS,
        "capped": bool(state.constraints.requested_count and state.constraints.requested_count > RESEARCH_SCOUT_MAX_FINAL_RESULTS),
    }
    papers, retrieval = await _retrieve_research_scout_papers(
        state.constraints.original_query,
        state.planned_queries or [state.constraints.original_query],
        state.intent,
        state.constraints.final_limit,
        count_info,
    )
    state.papers = papers
    state.filtered_papers = papers
    state.retrieval = retrieval
    state.expanded_queries = retrieval.get("expanded_queries") or []
    exclusions = retrieval.get("constraint_exclusions") or {}
    return ResearchScoutToolObservation(
        tool="search_papers",
        summary=(
            f"已执行 CVF/arXiv/学术源检索，目标 {state.constraints.final_limit} 篇，"
            f"候选池 {retrieval.get('unique_pool_count') or len(papers)} 篇，最终 {len(papers)} 篇。"
        ),
        result_count=len(papers),
        excluded_count=sum(int(value or 0) for value in exclusions.values()),
        details={
            "retrieval": retrieval,
            "year_from": state.constraints.year_from,
            "year_to": state.constraints.year_to,
            "venues": state.constraints.venues,
        },
    )


async def _research_scout_tool_filter_candidates(
    args: EmptyToolArgs,
    state: ResearchScoutAgentState,
) -> ResearchScoutToolObservation:
    state.filtered_papers, exclusions = _research_scout_constraint_filter(state.papers, state.intent)
    state.retrieval["constraint_exclusions"] = exclusions
    return ResearchScoutToolObservation(
        tool="filter_candidates",
        summary=f"已按年份、会议、机构和作者约束过滤，保留 {len(state.filtered_papers)} 篇。",
        result_count=len(state.filtered_papers),
        excluded_count=sum(int(value or 0) for value in exclusions.values()),
        details={"constraint_exclusions": exclusions, "constraint_mode": state.constraints.constraint_mode},
    )


async def _research_scout_tool_rank_candidates(
    args: EmptyToolArgs,
    state: ResearchScoutAgentState,
) -> ResearchScoutToolObservation:
    state.filtered_papers = _rank_research_scout_papers(
        state.filtered_papers or state.papers,
        state.constraints.original_query,
        [*state.planned_queries, *state.expanded_queries],
        state.intent,
        state.constraints.final_limit,
    )
    state.retrieval["candidate_count"] = len(state.filtered_papers)
    state.retrieval.setdefault("stage_counts", {})["ranked"] = len(state.filtered_papers)
    return ResearchScoutToolObservation(
        tool="rank_candidates",
        summary=f"已排序并截取 {len(state.filtered_papers)} 篇候选。",
        result_count=len(state.filtered_papers),
        details={"top_titles": [paper.title for paper in state.filtered_papers[:5]]},
    )


async def _research_scout_tool_prepare_cards(
    args: EmptyToolArgs,
    state: ResearchScoutAgentState,
) -> ResearchScoutToolObservation:
    candidates = [
        _research_scout_candidate(paper, state.constraints.original_query, index + 1, state.intent)
        for index, paper in enumerate(state.filtered_papers or state.papers)
    ]
    state.candidates = await _apply_llm_research_scout_evaluations(candidates, state.constraints.original_query, state.intent)
    state.references = [_research_scout_reference(item) for item in state.candidates]
    context_limit = _research_scout_context_candidate_limit(len(state.candidates), state.retrieval)
    state.retrieval["context_candidate_limit"] = context_limit
    if not state.candidates:
        state.system_context = [{
            "role": "system",
            "content": (
                "当前处于 Research Scout 论文猎手模式，但综合学术检索没有返回可用论文。"
                "请坦诚说明没有找到候选，并给出 3 个更容易命中的英文检索式。"
            ),
        }]
    else:
        state.system_context = [{
            "role": "system",
            "content": (
                "当前处于 Research Scout 论文猎手模式。你不是普通聊天助手，而是科研论文发现助手。"
                "请基于以下候选论文和结构化评估，推荐最值得用户优先阅读的论文。"
                "必须区分：为什么有趣、为什么对用户有用、风险/局限、下一步检索方向。"
                "如果单位、作者或 venue 约束没有证据确认，必须明确说“当前元数据无法确认”，不要编造 affiliation。"
                "评价创新性、可复现性、影响力和实验质量时只能依据 Evaluation 中的分数、证据和置信度。"
                "回答末尾必须给出“优先阅读 Top 3”，每项用 [PAPER-N] 编号并说明先读原因。"
                "引用候选时使用 [PAPER-N] 编号，不要编造候选列表之外的论文。\n\n"
                f"{_format_research_scout_retrieval_note(state.retrieval)}\n\n"
                f"{_format_research_scout_context(state.candidates, state.intent, context_limit=context_limit, retrieval=state.retrieval)}"
            ),
        }]
    return ResearchScoutToolObservation(
        tool="prepare_candidate_cards",
        summary=f"已准备 {len(state.candidates)} 张候选卡片和用户确认操作。",
        result_count=len(state.candidates),
        details={
            "candidate_count": len(state.candidates),
            "context_candidate_limit": context_limit,
            "side_effects": "confirmation_required",
        },
    )


def _research_scout_agent_registry() -> ResearchScoutToolRegistry:
    registry = ResearchScoutToolRegistry()
    registry.register(ResearchScoutToolDefinition(
        name="analyze_research_query",
        label="分析检索意图",
        args_model=EmptyToolArgs,
        executor=_research_scout_tool_analyze_query,
    ))
    registry.register(ResearchScoutToolDefinition(
        name="expand_paper_queries",
        label="拓展检索关键词",
        args_model=EmptyToolArgs,
        executor=_research_scout_tool_expand_queries,
    ))
    registry.register(ResearchScoutToolDefinition(
        name="search_papers",
        label="调用论文检索工具",
        args_model=EmptyToolArgs,
        executor=_research_scout_tool_search_papers,
    ))
    registry.register(ResearchScoutToolDefinition(
        name="filter_candidates",
        label="过滤约束不匹配候选",
        args_model=EmptyToolArgs,
        executor=_research_scout_tool_filter_candidates,
    ))
    registry.register(ResearchScoutToolDefinition(
        name="rank_candidates",
        label="排序候选论文",
        args_model=EmptyToolArgs,
        executor=_research_scout_tool_rank_candidates,
    ))
    registry.register(ResearchScoutToolDefinition(
        name="prepare_candidate_cards",
        label="生成候选卡片",
        args_model=EmptyToolArgs,
        executor=_research_scout_tool_prepare_cards,
    ))
    registry.register(ResearchScoutToolDefinition(
        name="import_paper",
        label="等待用户确认入库",
        args_model=EmptyToolArgs,
        executor=lambda args, state: ResearchScoutToolObservation(
            tool="import_paper",
            status="available",
            summary="候选卡片可一键入库、加入分类或加入研究方向；不会自动执行副作用操作。",
            details={"available_actions": ["import_paper", "add_to_folder", "add_to_project"]},
        ),
        side_effect=True,
    ))
    return registry


def _research_scout_default_actions() -> list[ResearchScoutToolCall]:
    return [
        ResearchScoutToolCall(tool="analyze_research_query", thought_summary="先拆解 query 和硬约束。"),
        ResearchScoutToolCall(tool="expand_paper_queries", thought_summary="让 AI 拓展英文检索关键词和任务别名。"),
        ResearchScoutToolCall(tool="search_papers", thought_summary="按结构化约束调用 CVF/arXiv/学术源检索。"),
        ResearchScoutToolCall(tool="filter_candidates", thought_summary="排除年份、会议或机构不匹配候选。"),
        ResearchScoutToolCall(tool="rank_candidates", thought_summary="根据相关性、PDF、venue 和引用排序。"),
        ResearchScoutToolCall(tool="prepare_candidate_cards", thought_summary="生成候选卡片和最终回答上下文。"),
    ]


def _research_scout_complete_action_plan(actions: list[ResearchScoutToolCall]) -> list[ResearchScoutToolCall]:
    required = _research_scout_default_actions()
    seen: set[str] = set()
    completed: list[ResearchScoutToolCall] = []
    for action in actions:
        if action.tool in seen:
            continue
        seen.add(action.tool)
        completed.append(action)
    for action in required:
        if action.tool not in seen:
            completed.append(action)
            seen.add(action.tool)
    return completed[:8]


async def _plan_research_scout_agent_actions(state: ResearchScoutAgentState, registry: ResearchScoutToolRegistry) -> list[ResearchScoutToolCall]:
    prompt = (
        "你是 Research Scout 的受控工具规划器。请根据用户找论文请求，选择工具执行顺序。"
        "只能使用给定工具名；不要编造工具；不要执行 import_paper 等副作用工具。"
        "通常需要 analyze_research_query -> expand_paper_queries -> search_papers -> filter_candidates -> rank_candidates -> prepare_candidate_cards。"
        "如果用户要求 CVPR/ICCV/ECCV 或年份，仍然通过 search_papers 工具传递结构化约束。"
        "只输出 JSON：{\"actions\":[{\"tool\":\"...\",\"arguments\":{},\"thought_summary\":\"...\"}]}"
        "\n\n用户请求："
        f"{state.constraints.original_query}"
        "\n\n约束："
        + json.dumps(state.constraints.model_dump(), ensure_ascii=False)
        + "\n\n可用工具："
        + json.dumps(registry.schemas(), ensure_ascii=False)
    )
    try:
        from app.services.research_scout_agent import parse_research_scout_action_json

        raw = await llm_service.chat(
            messages=[
                {"role": "system", "content": "你只返回可解析 JSON。不要 Markdown。不要输出未注册工具。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.05,
            max_tokens=1200,
        )
        actions = parse_research_scout_action_json(raw)
        allowed = {item["name"] for item in registry.schemas()}
        safe_actions = [
            action for action in actions
            if action.tool in allowed and action.tool != "import_paper"
        ]
        if safe_actions:
            return _research_scout_complete_action_plan(safe_actions)
    except Exception as exc:
        logger.warning("Research Scout agent action planning failed, using default tool loop: %s", exc)
    return _research_scout_default_actions()


def _research_scout_trace_from_agent(state: ResearchScoutAgentState) -> dict[str, Any]:
    steps = [event.model_dump() for event in state.trace_events]
    steps.append(_tool_trace_step(
        "paper-actions",
        "import_paper",
        "等待用户确认入库",
        "available" if state.candidates else "skipped",
        "候选卡片可一键入库、加入分类或加入研究方向；不会自动执行副作用操作。",
        {"available_actions": ["import_paper", "add_to_folder", "add_to_project"] if state.candidates else []},
    ))
    return {
        "enabled": True,
        "workflow": "research_scout_agent",
        "stop_reason": state.stop_reason,
        "tools": _research_scout_agent_registry().schemas(),
        "steps": steps,
    }


async def _build_research_scout_context(query: str, search_depth: str, intent: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]], list[str], dict[str, Any]]:
    count_info = _research_scout_final_limit(query, search_depth)
    limit = int(count_info["final_limit"])
    constraints = _research_scout_constraints(query, search_depth, intent, count_info)
    state = ResearchScoutAgentState(constraints=constraints, intent=intent)
    registry = _research_scout_agent_registry()
    agent = ResearchScoutAgent(registry, max_steps=8)
    actions = await _plan_research_scout_agent_actions(state, registry)
    try:
        state = await agent.run(state, actions)
    except Exception as exc:
        logger.warning("Research Scout agent discovery failed: %s", exc)
        planned_queries = await _plan_research_scout_queries(query, intent, search_depth, final_limit=limit)
        papers, retrieval = [], {
            "strategy": "arxiv_first_then_scholarly_fallback",
            "fallback_used": True,
            "planned_queries": planned_queries,
            "providers": [],
            "fallback_providers": [],
            "requested_count": count_info.get("requested_count"),
            "default_count": count_info.get("default_count"),
            "final_limit": limit,
            "max_final_limit": count_info.get("max_final_limit"),
            "count_capped": count_info.get("capped"),
            "pool_target": 0,
            "per_query_limit": 0,
            "unique_pool_count": 0,
            "underfilled_by": limit,
            "stage_counts": {"arxiv_enriched": 0, "scholarly_fallback": 0, "expanded_fallback": 0, "pool": 0, "ranked": 0},
            "candidate_count": 0,
        }
        state.planned_queries = planned_queries
        state.retrieval = retrieval
        state.stop_reason = "fallback_after_agent_failure"
    state.retrieval["agent_stop_reason"] = state.stop_reason
    state.retrieval["agent_trace"] = _research_scout_trace_from_agent(state)
    return state.candidates, state.references, state.system_context, state.planned_queries, state.retrieval


async def _retrieval_quality_snapshot(*, rag_enabled: bool) -> dict:
    if not rag_enabled:
        return {"rag_enabled": False, "paper_count": 0, "embedding_coverage": 0.0}
    try:
        from app.services.hybrid_search import HybridSearchService

        async with AsyncSessionLocal() as session:
            service = HybridSearchService(session)
            return {
                "rag_enabled": True,
                "paper_count": await service.paper_count(),
                "embedding_coverage": round(await service.embedding_coverage(), 4),
            }
    except Exception as exc:
        logger.warning("读取检索质量状态失败: %s", exc)
        return {"rag_enabled": True, "paper_count": 0, "embedding_coverage": 0.0, "error": str(exc)}


def _retrieval_status(
    references: list[dict],
    *,
    web_search_enabled: bool,
    subject: str = "资料",
    retrieval_quality: dict | None = None,
) -> str:
    local_count = sum(reference.get("source") == "local_library" for reference in references)
    web_count = sum(reference.get("source") == "web" for reference in references)
    quality_notes: list[str] = []
    if retrieval_quality and retrieval_quality.get("rag_enabled"):
        coverage = float(retrieval_quality.get("embedding_coverage") or 0.0)
        paper_count = int(retrieval_quality.get("paper_count") or 0)
        if paper_count == 0:
            quality_notes.append("当前知识库为空")
        elif local_count == 0:
            quality_notes.append("知识库本轮未命中可引用资料")
        if 0 < paper_count and coverage < 0.8:
            quality_notes.append(f"向量覆盖率约 {coverage:.0%}，语义召回可能不完整")
    suffix = f"（{'；'.join(quality_notes)}，建议到设置-数据-知识库维护补索引）" if quality_notes else ""
    if web_search_enabled and not web_count:
        return f"已完成{subject}检索：知识库 {local_count} 篇；联网增强未获取到有效网页来源{suffix}，正在基于现有资料生成回答..."
    if web_search_enabled:
        return f"已完成{subject}检索：知识库 {local_count} 篇，联网来源 {web_count} 条{suffix}，正在生成回答..."
    return f"已完成{subject}检索：知识库 {local_count} 篇{suffix}，正在生成回答..."


async def _append_retrieval_context(
    context: list[dict[str, str]],
    query: str,
    *,
    rag_enabled: bool,
    web_search_enabled: bool,
    search_depth: str,
) -> list[dict]:
    """按统一策略叠加知识库和联网结果。"""
    limits = _retrieval_limits(search_depth)
    references = []

    if rag_enabled:
        async with AsyncSessionLocal() as rag_session:
            rag = RAGService(rag_session)
            results = await rag.search_similar(query, top_k=limits["rag_papers"])
            if results:
                rag_context = await rag.build_rag_context(query, max_papers=limits["rag_papers"])
                context.insert(0, {
                    "role": "system",
                    "content": f"你是一个科研助手。以下是相关知识库中的论文，请在回答时引用它们：{rag_context}",
                })
                references = [
                    {
                        "title": paper.title,
                        "arxiv_id": paper.arxiv_id,
                        "year": paper.year,
                        "similarity": round(score, 4),
                        "source": "local_library",
                    }
                    for paper, score in results
                ]

    if web_search_enabled:
        try:
            web_results = await search_web_results(
                query,
                max_results=limits["web_results"],
                search_depth=search_depth,
            )
        except Exception as exc:
            logger.warning(f"联网搜索失败: {exc}")
            web_results = []
        web_context = format_web_context(web_results)
        if web_context:
            context.insert(0, {
                "role": "system",
                "content": (
                    "以下是联网检索获得的网页来源。请仅在来源能支持结论时引用对应的 [WEB-N] 编号，"
                    "并区分网页来源与知识库论文：\n\n"
                    f"{web_context[:7000]}"
                ),
            })
            references.extend(result.as_reference() for result in web_results)
        else:
            context.insert(0, {
                "role": "system",
                "content": "用户已开启联网增强，但本轮联网搜索未返回可用来源。请明确说明未获取到有效联网结果，并将知识库内容标注为知识库检索结果，不要暗示已经完成网络检索。",
            })

    return references


class SendMessageResponse(BaseModel):
    message: MessageResponse
    reply: MessageResponse
    session_title: str
    compression_notice: Optional[str] = None


def _is_workspace_scoped_session(session: ChatSession) -> bool:
    metadata = session.metadata_json or {}
    return metadata.get("scope") == "workspace" and bool(metadata.get("workspace_id"))


@router.delete("/{session_id}/messages/{message_id}")
async def delete_message(session_id: str, message_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除消息。"""
    from uuid import UUID
    try: sid=UUID(session_id); mid=UUID(message_id)
    except ValueError: raise HTTPException(status_code=400)
    s = (await db.execute(select(ChatSession).where(ChatSession.id==sid, ChatSession.user_id==user.id))).scalar_one_or_none()
    if not s: raise HTTPException(status_code=404)
    m = (await db.execute(select(ChatMessage).where(ChatMessage.id==mid, ChatMessage.session_id==sid))).scalar_one_or_none()
    if not m: raise HTTPException(status_code=404)
    await db.delete(m); await db.commit()
    return {"deleted": True}

@router.delete("/{session_id}/messages")
async def clear_messages(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """清空对话所有消息。"""
    from uuid import UUID
    try: sid=UUID(session_id)
    except ValueError: raise HTTPException(status_code=400)
    s = (await db.execute(select(ChatSession).where(ChatSession.id==sid, ChatSession.user_id==user.id))).scalar_one_or_none()
    if not s: raise HTTPException(status_code=404)
    msgs = (await db.execute(select(ChatMessage).where(ChatMessage.session_id==sid))).scalars().all()
    for m in msgs: await db.delete(m)
    await db.commit()
    return {"deleted": len(msgs)}

# --- 会话管理 ---

@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(req: SessionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建新对话。"""
    session = ChatSession(user_id=user.id, title=req.title, rag_enabled=req.rag_enabled)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=str(session.id), title=session.title, rag_enabled=session.rag_enabled,
        message_count=0, created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
    )


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取所有对话列表。"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = [session for session in result.scalars().all() if not _is_workspace_scoped_session(session)]

    return [
        SessionResponse(
            id=str(s.id), title=s.title, rag_enabled=s.rag_enabled,
            message_count=len(s.messages) if s.messages else 0,
            last_message=s.messages[-1].content[:100] if s.messages else None,
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.updated_at.isoformat() if s.updated_at else "",
        )
        for s in sessions
    ]


@router.delete("/{session_id}")
async def delete_session(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除对话。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    await db.delete(session)
    await db.commit()
    return {"deleted": True}


# --- 消息 ---

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取对话消息。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == sid)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return [
        MessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            references=_visible_chat_references(m.references),
            tool_trace=_tool_trace_from_references(m.references),
            created_at=m.created_at.isoformat() if m.created_at else "",
        )
        for m in messages
    ]


@router.post("/{session_id}/send", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    req: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送消息并获取 AI 回复。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    # 更新 RAG 设置
    rag_enabled = req.rag_enabled if req.rag_enabled is not None else session.rag_enabled
    if req.rag_enabled is not None:
        session.rag_enabled = req.rag_enabled
    effective_mode = _effective_assistant_mode(req)
    scout_enabled = effective_mode == "research_scout"
    effective_search_depth = "deep" if scout_enabled else req.search_depth

    # 保存用户消息
    user_msg = ChatMessage(session_id=sid, role="user", content=req.content)
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 构建上下文（使用三层记忆架构，参考 mem0/MemoryLLM/lethes）
    from app.services.memory_service import MemoryService
    memory = MemoryService(db)
    context = await memory.build_context(
        session,
        req.content,
        extra_context=req.extra_context or "",
    )
    upload_visual_context, upload_visual_refs = _uploaded_pdf_visual_context_from_messages(session.messages or [])
    if upload_visual_context:
        context.insert(0, {"role": "system", "content": upload_visual_context})

    references = await _append_retrieval_context(
        context,
        req.content,
        rag_enabled=rag_enabled,
        web_search_enabled=_web_search_enabled_for_mode(req, effective_mode),
        search_depth=effective_search_depth,
    )
    references.extend(upload_visual_refs)
    scout_candidates: list[dict[str, Any]] = []
    scout_intent: dict[str, Any] | None = None
    tool_trace: dict[str, Any] | None = None
    scout_planned_queries: list[str] = []
    scout_retrieval: dict[str, Any] = {}
    if scout_enabled:
        scout_intent = _research_scout_intent(req.content, effective_search_depth)
        scout_candidates, scout_refs, scout_context, scout_planned_queries, scout_retrieval = await _build_research_scout_context(req.content, effective_search_depth, scout_intent)
        tool_trace = _research_scout_tool_trace(req.content, scout_intent, scout_candidates, scout_planned_queries, scout_retrieval)
        context = [*scout_context, *context]
        references.extend(scout_refs)
    elif _chat_tool_planner_enabled(req, effective_mode):
        tool_context, tool_refs, tool_trace = await _build_chat_agent_tool_context(
            req.content,
            db=db,
            user=user,
            session_id=session_id,
            conversation_context=context,
            tool_mode="force" if req.tool_mode == "force" else "auto",
        )
        if tool_context:
            context.insert(0, {
                "role": "system",
                "content": (
                    "以下是本轮 Agent 工具规划与执行得到的结构化观察。回答时请基于这些观察，"
                    "不要声称已经执行需要用户确认的副作用操作：\n\n"
                    f"{tool_context}"
                ),
            })
        references.extend(tool_refs)

    # 调用 LLM
    try:
        reply_content = await llm_service.chat(
            messages=context,
            temperature=0.55 if scout_enabled else 0.7,
            max_tokens=4096,
        )

        # 保存 AI 回复
        reply_msg = ChatMessage(
            session_id=sid, role="assistant",
            content=reply_content, references=_references_with_tool_trace(references, tool_trace),
        )
        db.add(reply_msg)

        # 自动更新标题（用第一条用户消息的前30字）
        if session.title == "新对话":
            session.title = req.content[:30] + ("..." if len(req.content) > 30 else "")

        await db.commit()
        await db.refresh(reply_msg)

        return SendMessageResponse(
            message=MessageResponse(
                id=str(user_msg.id), role="user", content=user_msg.content,
                created_at=user_msg.created_at.isoformat() if user_msg.created_at else "",
            ),
            reply=MessageResponse(
                id=str(reply_msg.id), role="assistant", content=reply_msg.content,
                references=_visible_chat_references(reply_msg.references),
                tool_trace=tool_trace,
                created_at=reply_msg.created_at.isoformat() if reply_msg.created_at else "",
            ),
            session_title=session.title,
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")


@router.post("/{session_id}/send-stream")
async def send_message_stream(
    session_id: str,
    req: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """流式发送消息并获取 AI 回复。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    rag_enabled = req.rag_enabled if req.rag_enabled is not None else session.rag_enabled
    if req.rag_enabled is not None:
        session.rag_enabled = req.rag_enabled
    effective_mode = _effective_assistant_mode(req)
    scout_enabled = effective_mode == "research_scout"
    effective_search_depth = "deep" if scout_enabled else req.search_depth

    # 保存用户消息
    user_msg = ChatMessage(session_id=sid, role="user", content=req.content)
    db.add(user_msg)
    await db.commit()

    # 构建上下文（三层记忆架构）
    from app.services.memory_service import MemoryService
    memory = MemoryService(db)
    context = await memory.build_context(session, req.content, extra_context=req.extra_context or "")
    upload_visual_context, upload_visual_refs = _uploaded_pdf_visual_context_from_messages(session.messages or [])
    if upload_visual_context:
        context.insert(0, {"role": "system", "content": upload_visual_context})

    references = await _append_retrieval_context(
        context,
        req.content,
        rag_enabled=rag_enabled,
        web_search_enabled=_web_search_enabled_for_mode(req, effective_mode),
        search_depth=effective_search_depth,
    )
    references.extend(upload_visual_refs)
    scout_candidates: list[dict[str, Any]] = []
    scout_intent: dict[str, Any] | None = None
    tool_trace: dict[str, Any] | None = None
    scout_planned_queries: list[str] = []
    scout_retrieval: dict[str, Any] = {}
    if scout_enabled:
        scout_intent = _research_scout_intent(req.content, effective_search_depth)
        scout_candidates, scout_refs, scout_context, scout_planned_queries, scout_retrieval = await _build_research_scout_context(req.content, effective_search_depth, scout_intent)
        tool_trace = _research_scout_tool_trace(req.content, scout_intent, scout_candidates, scout_planned_queries, scout_retrieval)
        context = [*scout_context, *context]
        references.extend(scout_refs)
    elif _chat_tool_planner_enabled(req, effective_mode):
        tool_context, tool_refs, tool_trace = await _build_chat_agent_tool_context(
            req.content,
            db=db,
            user=user,
            session_id=session_id,
            conversation_context=context,
            tool_mode="force" if req.tool_mode == "force" else "auto",
        )
        if tool_context:
            context.insert(0, {
                "role": "system",
                "content": (
                    "以下是本轮 Agent 工具规划与执行得到的结构化观察。回答时请基于这些观察，"
                    "不要声称已经执行需要用户确认的副作用操作：\n\n"
                    f"{tool_context}"
                ),
            })
        references.extend(tool_refs)
    retrieval_quality = await _retrieval_quality_snapshot(rag_enabled=rag_enabled)
    llm_context = _build_llm_context_for_request(context, req)

    # 流式响应
    async def generate():
        full_content = ""
        if scout_enabled:
            yield _stream_event(
                "status",
                f"论文猎手正在检索 arXiv、Semantic Scholar、OpenAlex 等学术来源，已找到 {len(scout_candidates)} 篇候选...",
            )
        yield _stream_event(
            "status",
            (
                f"论文猎手已整理 {len(scout_candidates)} 篇候选论文，正在生成阅读优先级与推荐理由..."
                if scout_enabled
                else _retrieval_status(
                    references,
                    web_search_enabled=bool(req.web_search),
                    retrieval_quality=retrieval_quality,
                )
            ),
        )
        yield _stream_event(
            "meta",
            {
                "references": references,
                "research_scout": {
                    "enabled": scout_enabled,
                    "auto_routed": req.assistant_mode != "research_scout",
                    "query": req.content,
                    "intent": scout_intent,
                    "planned_queries": scout_planned_queries,
                    "retrieval": scout_retrieval,
                    "candidates": scout_candidates,
                    "candidate_count": len(scout_candidates),
                } if scout_enabled else None,
                "tool_trace": tool_trace,
                "model": _active_model_stream_metadata(
                    rag_enabled=rag_enabled,
                    web_search_enabled=_web_search_enabled_for_mode(req, effective_mode),
                    search_depth=effective_search_depth,
                    attachments=req.attachments,
                ),
            },
        )
        try:
            if req.show_thinking:
                async for event in llm_service.chat_stream_with_thinking(messages=llm_context):
                    if event["type"] == "reasoning":
                        yield _stream_event("reasoning", event["content"])
                    elif event["type"] == "content":
                        full_content += event["content"]
                        yield _stream_event("content", event["content"])
            else:
                async for token in llm_service.chat_stream(messages=llm_context):
                    if not token:
                        continue
                    full_content += token
                    yield _stream_event("content", token)
        except Exception as exc:
            logger.exception(f"对话流式生成失败: {exc}")
            full_content, appended = _stream_failure_content(full_content)
            yield _stream_event("error", appended)

        if not full_content.strip():
            full_content = EMPTY_STREAM_FALLBACK
            yield _stream_event("error", full_content)

        # 保存 AI 回复
        reply_msg = ChatMessage(
            session_id=sid,
            role="assistant",
            content=full_content,
            references=_references_with_tool_trace(references, tool_trace),
        )
        db.add(reply_msg)
        if session.title == "新对话":
            session.title = req.content[:30]
        await db.commit()
        await db.refresh(reply_msg)
        yield _stream_event(
            "saved",
            {
                "reply_id": str(reply_msg.id),
                "created_at": reply_msg.created_at.isoformat() if reply_msg.created_at else "",
            },
        )
        yield _stream_event("done")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{session_id}/tools/confirm")
async def confirm_chat_tool(
    session_id: str,
    req: ConfirmToolRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """确认并执行需要用户授权的对话工具。"""
    from uuid import UUID

    try:
        sid = UUID(session_id)
        mid = UUID(req.message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.id == mid,
            ChatMessage.session_id == sid,
            ChatMessage.role == "assistant",
        )
    )
    assistant_message = result.scalar_one_or_none()
    if not assistant_message:
        raise HTTPException(status_code=404, detail="消息未找到")

    confirmation_arg_models = {
        "import_paper": ImportPaperArgs,
        "add_to_folder": AddToFolderArgs,
        "create_research_project": CreateResearchProjectArgs,
    }
    arg_model = confirmation_arg_models.get(req.tool)
    if not arg_model:
        raise HTTPException(status_code=400, detail="不支持的确认工具")

    try:
        arguments = arg_model.model_validate(req.arguments).model_dump()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"工具参数无效: {exc}")

    expected_token = chat_tool_confirmation_token(req.tool, arguments)
    if req.confirmation_token != expected_token:
        raise HTTPException(status_code=400, detail="确认令牌不匹配")

    trace = _tool_trace_from_references(assistant_message.references)
    pending_steps = (trace or {}).get("steps") if isinstance(trace, dict) else []
    pending_found = False
    for step in pending_steps or []:
        if not isinstance(step, dict):
            continue
        details = step.get("details") if isinstance(step.get("details"), dict) else {}
        if (
            step.get("tool") == req.tool
            and step.get("status") == "waiting_confirmation"
            and details.get("confirmation_token") == req.confirmation_token
        ):
            pending_found = True
            break
    if not pending_found:
        raise HTTPException(status_code=409, detail="未找到可确认的待执行工具动作")

    registry = default_chat_tool_registry()
    state = ChatAgentRuntimeState(
        user_query=f"confirm {req.tool}",
        db=db,
        user=user,
        session_id=session_id,
    )
    runtime = ChatAgentToolRuntime(registry, max_steps=1)
    state = await runtime.run(
        state,
        [
            ChatToolCall(
                tool=req.tool,
                arguments=arguments,
                confirmation_token=req.confirmation_token,
                thought_summary=f"用户已确认执行 {req.tool}。",
            )
        ],
        allow_side_effects=True,
    )
    observation = state.observations[-1] if state.observations else None
    confirmed_trace = chat_tool_trace_payload(state, registry)
    return {
        "ok": bool(observation and observation.status == "completed"),
        "observation": observation.model_dump() if observation else None,
        "tool_trace": confirmed_trace,
        "references": state.references,
    }


# --- 文件上传 ---

@router.post("/extract-file")
async def extract_file_text(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """仅提取文件内容，不发送消息。返回提取的文本供前端展示。"""
    content_type = file.content_type or ""
    filename = file.filename or "file"
    file_bytes = await file.read()

    if len(file_bytes) > MAX_CHAT_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=f"文件不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB")

    extracted_text = ""
    file_type = "unknown"
    data_url: str | None = None

    if "image" in content_type or filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        file_type = "image"
        import base64
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        mime = content_type or "image/png"
        extracted_text = f"[图片: {filename}]\n请描述你在这张图片中看到了什么，特别关注任何文字、图表或数据。"
        data_url = f"data:{mime};base64,{b64}"
        logger.info(f"图片上传: {filename} ({len(file_bytes)} bytes)")

    elif "pdf" in content_type or filename.lower().endswith('.pdf'):
        file_type = "pdf"
        extracted_text, visual_payload, visual_blocks = await _extract_pdf_text_and_visual_evidence(file_bytes, filename)
        if visual_blocks:
            extracted_text = f"{extracted_text}\n{_format_uploaded_pdf_visual_context(filename, visual_blocks)}"

    else:
        try:
            extracted_text = file_bytes.decode("utf-8")[:50000]
            file_type = "text"
        except:
            raise HTTPException(status_code=400, detail="不支持的文件类型")

    return {
        "filename": filename,
        "file_type": file_type,
        "file_size": len(file_bytes),
        "extracted_text": extracted_text[:50000],
        "data_url": data_url if file_type == "image" else None,
        "mime_type": content_type or None,
        "text_length": len(extracted_text),
        "visual_evidence": visual_payload if file_type == "pdf" else None,
    }


@router.post("/{session_id}/upload")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传图片或 PDF 到对话中，提取内容传给 AI。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    content_type = file.content_type or ""
    filename = file.filename or "file"
    file_bytes = await file.read()

    if len(file_bytes) > MAX_CHAT_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=f"文件不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB")

    extracted_text = ""
    file_desc = ""

    try:
        if "image" in content_type or filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            # 图片：保存 base64，让 V4 Pro 多模态识别
            import base64
            b64 = base64.b64encode(file_bytes).decode("utf-8")
            mime = content_type or "image/png"
            data_uri = f"data:{mime};base64,{b64}"
            extracted_text = f"[用户上传了图片: {filename}]\n请描述你在这张图片中看到了什么，特别关注任何文字、图表或数据。"
            # 将图片信息存入消息 metadata
            file_desc = data_uri[:200]  # 截断 preview
            logger.info(f"收到图片: {filename} ({len(file_bytes)} bytes)")

        elif "pdf" in content_type or filename.lower().endswith('.pdf'):
            extracted_text, visual_payload, visual_blocks = await _extract_pdf_text_and_visual_evidence(file_bytes, filename)
            visual_context = _format_uploaded_pdf_visual_context(filename, visual_blocks)
            if extracted_text:
                extracted_text = f"{extracted_text}\n{visual_context}"
                ready_visual = len(visual_blocks)
                file_desc = f"[用户上传了 PDF: {filename}，已提取全文 ({len(extracted_text)} 字符)，视觉证据 {ready_visual} 条]"
            else:
                file_desc = f"[用户上传了 PDF: {filename}，无法提取文本，可能是扫描图片版]"
                extracted_text = f"[PDF: {filename}] 内容无法提取，请上传可选中文字的原生 PDF。{visual_context}"

        else:
            # 其他文件：尝试当作文本读取
            try:
                extracted_text = file_bytes.decode("utf-8")[:4000]
                file_desc = f"[用户上传了文件: {filename}]"
            except:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {content_type}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

    # 保存用户消息（含文件描述）
    user_msg = ChatMessage(
        session_id=sid, role="user",
        content=extracted_text,
        references=[
            {"type": "file", "filename": filename, "size": len(file_bytes)},
            *_uploaded_pdf_visual_references(filename, locals().get("visual_blocks", [])),
        ],
    )
    db.add(user_msg)

    # 构建上下文并调用 LLM
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == sid).order_by(ChatMessage.created_at)
    )
    all_msgs = result.scalars().all()
    context = [{"role": m.role, "content": m.content} for m in all_msgs[-20:]]
    context.append({"role": "user", "content": extracted_text})

    try:
        reply_content = await llm_service.chat(messages=context, temperature=0.7, max_tokens=4096)
        reply_msg = ChatMessage(session_id=sid, role="assistant", content=reply_content)
        db.add(reply_msg)
        await db.commit()
        await db.refresh(reply_msg)

        return {
            "message": {
                "id": str(user_msg.id), "role": "user", "content": file_desc or extracted_text[:200],
                "created_at": user_msg.created_at.isoformat() if user_msg.created_at else "",
            },
            "reply": {
                "id": str(reply_msg.id), "role": "assistant", "content": reply_content,
                "created_at": reply_msg.created_at.isoformat() if reply_msg.created_at else "",
            },
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")
