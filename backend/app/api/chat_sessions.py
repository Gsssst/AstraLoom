"""多对话会话管理 API。"""

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
from app.services.paper_search import PaperResult, create_remote_ingest_token, deduplicate_papers, search_scholarly_papers
from app.services.rag_service import RAGService
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


RETRIEVAL_DEPTH_LIMITS = {
    "quick": {"rag_papers": 2, "web_results": 2, "web_queries": 1},
    "standard": {"rag_papers": 3, "web_results": 5, "web_queries": 3},
    "deep": {"rag_papers": 5, "web_results": 8, "web_queries": 5},
}
RESEARCH_SCOUT_LIMITS = {"quick": 5, "standard": 8, "deep": 12}
RESEARCH_SCOUT_INTENT_YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")
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
    constraint_mode = "hard" if any(hint in lowered for hint in RESEARCH_SCOUT_HARD_CONSTRAINT_HINTS) else "soft"
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


RESEARCH_SCOUT_QUERY_LIMITS = {"quick": 2, "standard": 3, "deep": 4}
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
    if "video grounding" in lowered or "视频定位" in query or "视频 grounding" in lowered:
        variants.extend(["video grounding", "temporal video grounding", "video moment retrieval"])
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


async def _plan_research_scout_queries(query: str, intent: dict[str, Any], search_depth: str) -> list[str]:
    limit = RESEARCH_SCOUT_QUERY_LIMITS.get(search_depth, RESEARCH_SCOUT_QUERY_LIMITS["standard"])
    fallback = _fallback_research_scout_queries(query, intent, limit=limit)
    prompt = (
        "你是学术论文检索 query planner。请根据用户问题生成适合 arXiv、Semantic Scholar、OpenAlex 的英文检索关键词。"
        "要求：只输出 JSON；queries 是 2-4 个英文短 query；优先使用学术常用术语、缩写、同义任务名；不要包含中文礼貌请求、数量词或无关解释。"
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
) -> dict[str, Any]:
    candidate_count = len(candidates)
    llm_evaluated = sum(1 for item in candidates[:6] if (item.get("evaluation") or {}).get("source") == "llm")
    high_priority = [
        item.get("title")
        for item in candidates
        if (item.get("evaluation") or {}).get("reading_priority") == "high"
    ][:3]
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
            f"已优先检索 arXiv PDF，并用 Semantic Scholar/OpenAlex 增强元数据，找到 {candidate_count} 篇候选。",
            {
                "query": query,
                "planned_queries": planned_queries or [query],
                "providers": ["arXiv PDF", "Semantic Scholar enrichment", "OpenAlex enrichment"],
                "strategy": "arxiv_first_enriched",
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


def _format_research_scout_context(candidates: list[dict[str, Any]], intent: dict[str, Any]) -> str:
    if not candidates:
        return ""
    blocks = []
    for item in candidates[:8]:
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
    return f"Parsed user intent:\n{_format_research_scout_intent(intent)}\n\nCandidate papers:\n" + "\n\n".join(blocks)


async def _build_research_scout_context(query: str, search_depth: str, intent: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]], list[str]]:
    limit = RESEARCH_SCOUT_LIMITS.get(search_depth, RESEARCH_SCOUT_LIMITS["standard"])
    planned_queries = await _plan_research_scout_queries(query, intent, search_depth)
    try:
        groups = await asyncio.gather(*[
            search_scholarly_papers(
                planned_query,
                source="arxiv_enriched",
                max_results=max(limit, 8),
                sort_by="relevance",
            )
            for planned_query in planned_queries
        ], return_exceptions=True)
        papers = []
        for group in groups:
            if isinstance(group, Exception):
                logger.warning("Research Scout planned query failed: %s", group)
                continue
            papers.extend(group)
        papers = deduplicate_papers(papers, limit)
    except Exception as exc:
        logger.warning("Research Scout scholarly discovery failed: %s", exc)
        papers = []

    candidates = [_research_scout_candidate(paper, query, index + 1, intent) for index, paper in enumerate(papers)]
    candidates = await _apply_llm_research_scout_evaluations(candidates, query, intent)
    references = [_research_scout_reference(item) for item in candidates]
    if not candidates:
        system_context = [{
            "role": "system",
            "content": (
                "当前处于 Research Scout 论文猎手模式，但综合学术检索没有返回可用论文。"
                "请坦诚说明没有找到候选，并给出 3 个更容易命中的英文检索式。"
            ),
        }]
    else:
        system_context = [{
            "role": "system",
            "content": (
                "当前处于 Research Scout 论文猎手模式。你不是普通聊天助手，而是科研论文发现助手。"
                "请基于以下候选论文和结构化评估，推荐最值得用户优先阅读的论文。"
                "必须区分：为什么有趣、为什么对用户有用、风险/局限、下一步检索方向。"
                "如果单位、作者或 venue 约束没有证据确认，必须明确说“当前元数据无法确认”，不要编造 affiliation。"
                "评价创新性、可复现性、影响力和实验质量时只能依据 Evaluation 中的分数、证据和置信度。"
                "回答末尾必须给出“优先阅读 Top 3”，每项用 [PAPER-N] 编号并说明先读原因。"
                "引用候选时使用 [PAPER-N] 编号，不要编造候选列表之外的论文。\n\n"
                f"{_format_research_scout_context(candidates, intent)}"
            ),
        }]
    return candidates, references, system_context, planned_queries


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
            id=str(m.id), role=m.role, content=m.content, references=m.references,
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
    if scout_enabled:
        scout_intent = _research_scout_intent(req.content, effective_search_depth)
        scout_candidates, scout_refs, scout_context, scout_planned_queries = await _build_research_scout_context(req.content, effective_search_depth, scout_intent)
        tool_trace = _research_scout_tool_trace(req.content, scout_intent, scout_candidates, scout_planned_queries)
        context = [*scout_context, *context]
        references.extend(scout_refs)

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
            content=reply_content, references=references,
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
                references=reply_msg.references,
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
    if scout_enabled:
        scout_intent = _research_scout_intent(req.content, effective_search_depth)
        scout_candidates, scout_refs, scout_context, scout_planned_queries = await _build_research_scout_context(req.content, effective_search_depth, scout_intent)
        tool_trace = _research_scout_tool_trace(req.content, scout_intent, scout_candidates, scout_planned_queries)
        context = [*scout_context, *context]
        references.extend(scout_refs)
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
        reply_msg = ChatMessage(session_id=sid, role="assistant", content=full_content, references=references)
        db.add(reply_msg)
        if session.title == "新对话":
            session.title = req.content[:30]
        await db.commit()
        yield _stream_event("done")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
