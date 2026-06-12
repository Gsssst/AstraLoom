"""论文 API — 搜索、详情、入库、分类管理。"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional, List, Any, AsyncIterator, Literal
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.paper import Paper, Category, PaperCategory, UserPaper
from app.services.paper_search import (
    PaperResult,
    create_remote_ingest_token,
    read_remote_ingest_token,
    search_scholarly_papers,
    semantic_scholar_service,
)
from app.services.paper_ingestion import PaperIngestionService
from app.services.rag_service import RAGService
from app.services.paper_enhance import PaperEnhanceService
from app.services.llm import llm_service
from app.core.config import settings
from app.core.security import get_current_user, get_optional_user, require_admin
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/papers", tags=["论文"])


# --- Response Models ---

class PaperBrief(BaseModel):
    id: str
    title: str
    authors: Optional[list]
    year: Optional[int]
    abstract: Optional[str]
    abstract_full: Optional[str] = None
    arxiv_id: Optional[str]
    doi: Optional[str]
    source: str
    citation_count: int
    created_at: str
    remote_id: Optional[str] = None
    remote_ingest_token: Optional[str] = None
    pdf_url: Optional[str] = None
    source_url: Optional[str] = None
    read_status: Optional[str] = None
    imported_by_user_id: Optional[str] = None
    imported_by_username: Optional[str] = None
    importance_label: Optional[Literal["important", "interesting"]] = None
    importance_note: Optional[str] = None
    has_pdf: bool = False
    has_full_text: bool = False
    has_embedding: bool = False
    has_tags: bool = False
    processing_status: Optional[str] = None

    model_config = {"from_attributes": True}


class StructuredPdfParseStatus(BaseModel):
    ready: bool = False
    parser: Optional[str] = None
    source_path: Optional[str] = None
    page_count: int = 0
    parsed_at: Optional[str] = None
    table_count: int = 0
    caption_count: int = 0
    visual_count: int = 0
    ocr_count: int = 0
    formula_count: int = 0
    block_count: int = 0
    block_counts: dict[str, int] = Field(default_factory=dict)
    table_quality: Optional[dict] = None
    parser_health: Optional[dict] = None
    table_repair: Optional[dict] = None
    last_error: Optional[dict] = None
    last_table_repair_error: Optional[dict] = None


class PaperDetail(PaperBrief):
    pdf_path: Optional[str]
    full_text_preview: Optional[str] = None
    tags: Optional[Any] = None
    categories: list = []
    metadata_json: Optional[dict] = None
    similar_papers: list = []
    structured_parse_status: Optional[StructuredPdfParseStatus] = None


class PaperImportanceRequest(BaseModel):
    label: Optional[Literal["important", "interesting"]] = Field(default=None, description="共享标记类型")
    note: Optional[str] = Field(default=None, max_length=500, description="标记说明")


class PaperImportanceResponse(BaseModel):
    id: str
    importance_label: Optional[Literal["important", "interesting"]] = None
    importance_note: Optional[str] = None


class PaperSearchResponse(BaseModel):
    items: List[PaperBrief]
    total: int
    page: int
    page_size: int


class PaperProcessingStatus(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    source: str
    imported_by_username: Optional[str] = None
    has_pdf: bool
    has_full_text: bool
    has_embedding: bool
    has_tags: bool
    status: Literal["ready", "needs_full_text", "needs_embedding", "needs_tags", "needs_processing"]
    missing: list[str] = []
    repair_actions: list[dict] = []
    structured_parse_status: Optional[StructuredPdfParseStatus] = None


class PaperProcessingStatusResponse(BaseModel):
    items: list[PaperProcessingStatus]
    total: int
    ready: int
    needs_processing: int


class PaperInsightResponse(BaseModel):
    paper_id: str
    generated_at: str
    evidence_coverage: Literal["abstract_only", "full_text"]
    contribution: str = ""
    reusable_methods: str = ""
    reproducible_experiments: str = ""
    limitations: str = ""
    research_gaps: str = ""
    research_fit: str = ""
    raw: str = ""


class IngestRequest(BaseModel):
    arxiv_ids: Optional[List[str]] = None
    search_query: Optional[str] = None
    max_results: int = Field(default=20, ge=1, le=50)
    source: str = Field(default="arxiv")
    auto_download: bool = True


class IngestResponse(BaseModel):
    success: int
    skipped: int
    error: int
    total_found: int
    paper_ids: list = []
    errors: list = []


class PersonalIngestRequest(BaseModel):
    source: Literal["arxiv", "semantic_scholar", "openalex", "google_scholar"]
    remote_id: str = Field(..., min_length=1, max_length=300)
    remote_ingest_token: Optional[str] = None
    auto_download: bool = False


class CategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    parent_id: Optional[str]
    children: list = []

    model_config = {"from_attributes": True}


class MaintenancePaperSample(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    source: Optional[str] = None
    arxiv_id: Optional[str] = None


class RetrievalMaintenanceHealth(BaseModel):
    total_papers: int
    full_text_papers: int
    missing_full_text: int
    embedding_papers: int
    missing_embeddings: int
    arxiv_papers: int
    full_text_coverage: float
    embedding_coverage: float
    bm25_index: dict
    missing_full_text_samples: list[MaintenancePaperSample] = []
    missing_embedding_samples: list[MaintenancePaperSample] = []


class MaintenanceActionResult(BaseModel):
    processed: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[dict] = []


class MaintenanceJobStatus(BaseModel):
    id: Optional[str] = None
    kind: str
    state: Literal["queued", "running", "success", "failed", "cancelled", "unknown"] = "queued"
    status: str = "queued"
    total: int = 0
    processed: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    progress_percent: int = 0
    current_paper: Optional[dict] = None
    errors: list[dict] = []
    message: str = ""
    result: Optional[MaintenanceActionResult] = None


class MaintenanceJobStartResponse(BaseModel):
    job_id: str
    status_endpoint: str
    job: MaintenanceJobStatus


class MaintenanceRecommendation(BaseModel):
    id: str
    title: str
    severity: Literal["high", "medium", "low"] = "medium"
    reason: str
    action_label: str
    action_endpoint: str
    sample_papers: list[MaintenancePaperSample] = []


class RetrievalDiagnosticHit(BaseModel):
    id: str
    title: str
    score: float
    year: Optional[int] = None
    source: Optional[str] = None
    arxiv_id: Optional[str] = None
    has_full_text: bool
    has_embedding: bool
    match_sources: list[str] = []


class RetrievalDiagnosticsResponse(BaseModel):
    query: str
    query_terms: list[str] = []
    top_k: int
    summary: str
    bm25: list[RetrievalDiagnosticHit]
    dense: list[RetrievalDiagnosticHit]
    hybrid: list[RetrievalDiagnosticHit]
    branch_explanations: dict[str, list[str]] = {}
    recommended_actions: list[MaintenanceRecommendation] = []
    errors: dict[str, str] = {}


def _maintenance_sample(paper: Paper) -> MaintenancePaperSample:
    return MaintenancePaperSample(
        id=str(paper.id),
        title=paper.title,
        year=paper.year,
        source=paper.source,
        arxiv_id=paper.arxiv_id,
    )


async def _paper_count(db: AsyncSession, *criteria) -> int:
    query = select(func.count(Paper.id))
    for criterion in criteria:
        query = query.where(criterion)
    result = await db.execute(query)
    return int(result.scalar() or 0)


async def _missing_samples(db: AsyncSession, criterion, limit: int = 5) -> list[MaintenancePaperSample]:
    result = await db.execute(
        select(Paper)
        .where(criterion)
        .order_by(Paper.created_at.desc())
        .limit(limit)
    )
    return [_maintenance_sample(paper) for paper in result.scalars().all()]


def _coverage_severity(coverage: float) -> Literal["high", "medium", "low"]:
    if coverage < 0.5:
        return "high"
    if coverage < 0.85:
        return "medium"
    return "low"


async def _maintenance_recommendations(db: AsyncSession, *, include_samples: bool = True) -> list[MaintenanceRecommendation]:
    from app.services.hybrid_search import bm25_index_status
    from app.services.report_service import structured_pdf_parse_status_from_paper

    total = await _paper_count(db)
    if total <= 0:
        return []

    full_text_papers = await _paper_count(db, Paper.full_text.is_not(None), func.length(Paper.full_text) > 500)
    embedding_papers = await _paper_count(db, Paper.embedding.is_not(None))
    missing_full_text = max(total - full_text_papers, 0)
    missing_embeddings = max(total - embedding_papers, 0)
    structured_candidates_result = await db.execute(
        select(Paper)
        .where((Paper.pdf_path.is_not(None)) | (Paper.arxiv_id.is_not(None)))
        .order_by(Paper.created_at.desc())
        .limit(200)
    )
    structured_candidates = structured_candidates_result.scalars().all()
    structured_parse_needed = []
    table_repair_needed = []
    for paper in structured_candidates:
        structured_status = structured_pdf_parse_status_from_paper(paper)
        if not structured_status.get("ready") or structured_status.get("last_error"):
            structured_parse_needed.append(paper)
        else:
            table_quality = structured_status.get("table_quality") or {}
            table_repair = structured_status.get("table_repair") or {}
            if (
                int(table_quality.get("low_quality_table_count") or 0) > 0
                and not table_repair.get("has_repaired_tables")
            ):
                table_repair_needed.append(paper)
    missing_structured_parse = len(structured_parse_needed)
    low_quality_table_parse = len(table_repair_needed)
    full_text_coverage = full_text_papers / total
    embedding_coverage = embedding_papers / total
    bm25_status = bm25_index_status()

    recommendations: list[MaintenanceRecommendation] = []
    if missing_full_text:
        samples = await _missing_samples(
            db,
            ((Paper.full_text.is_(None)) | (func.length(Paper.full_text) <= 500)) & Paper.arxiv_id.is_not(None),
            limit=3,
        ) if include_samples else []
        recommendations.append(MaintenanceRecommendation(
            id="backfill-full-text",
            title="补全文解析",
            severity=_coverage_severity(full_text_coverage),
            reason=f"当前全文覆盖率约 {full_text_coverage:.0%}。论文页 AI 问答只能真正解释 Introduction/Method 等章节，前提是这些论文已经解析出全文。",
            action_label="补 5 篇全文",
            action_endpoint="/papers/maintenance/backfill-full-text?limit=5",
            sample_papers=samples,
        ))

    if missing_embeddings:
        samples = await _missing_samples(db, Paper.embedding.is_(None), limit=3) if include_samples else []
        recommendations.append(MaintenanceRecommendation(
            id="backfill-embeddings",
            title="补向量索引",
            severity=_coverage_severity(embedding_coverage),
            reason=f"当前向量覆盖率约 {embedding_coverage:.0%}。覆盖率偏低时 Hybrid 会弱化或降级语义检索，复杂语义问题更容易漏召回。",
            action_label="补 20 篇向量",
            action_endpoint="/papers/maintenance/backfill-embeddings?limit=20",
            sample_papers=samples,
        ))

    if missing_structured_parse:
        samples = [_maintenance_sample(paper) for paper in structured_parse_needed[:3]] if include_samples else []
        recommendations.append(MaintenanceRecommendation(
            id="backfill-structured-pdf",
            title="结构化解析 PDF",
            severity="medium",
            reason=f"当前有 {missing_structured_parse} 篇论文可刷新 PDF 结构化解析。表格、图注、OCR 和公式证据依赖这一步。",
            action_label="解析 5 篇 PDF",
            action_endpoint="/papers/maintenance/backfill-structured-pdf?limit=5",
            sample_papers=samples,
        ))

    if low_quality_table_parse:
        samples = [_maintenance_sample(paper) for paper in table_repair_needed[:3]] if include_samples else []
        recommendations.append(MaintenanceRecommendation(
            id="repair-low-quality-tables",
            title="修复低质量表格",
            severity="high",
            reason=f"当前有 {low_quality_table_parse} 篇论文的表格解析质量偏低。精确数值问答需要先用高精度表格解析器修复 cell 结构。",
            action_label="修复 5 篇表格",
            action_endpoint="/papers/maintenance/repair-tables?limit=5",
            sample_papers=samples,
        ))

    if not bm25_status.get("ready") or int(bm25_status.get("indexed_papers") or 0) < total:
        recommendations.append(MaintenanceRecommendation(
            id="rebuild-bm25",
            title="重建关键词索引",
            severity="medium",
            reason=f"BM25 当前索引 {int(bm25_status.get('indexed_papers') or 0)} / {total} 篇。关键词检索依赖这个进程内索引，入库后建议重建一次。",
            action_label="重建 BM25",
            action_endpoint="/papers/maintenance/rebuild-bm25",
            sample_papers=[],
        ))

    return recommendations


def _query_match_sources(query: str, paper: Paper) -> list[str]:
    from app.services.hybrid_search import tokenize_academic_text

    tokens = [token for token in tokenize_academic_text(query) if len(token) > 1]
    fields = {
        "title": paper.title or "",
        "abstract": paper.abstract or "",
        "full_text": paper.full_text or "",
    }
    matches: list[str] = []
    for field, value in fields.items():
        lowered = value.lower()
        if any(token in lowered for token in tokens):
            matches.append(field)
    return matches


def _diagnostic_branch_explanations(
    *,
    query_terms: list[str],
    bm25_hits: list[RetrievalDiagnosticHit],
    dense_hits: list[RetrievalDiagnosticHit],
    hybrid_hits: list[RetrievalDiagnosticHit],
    bm25_status: dict,
    embedding_coverage: float,
    errors: dict[str, str],
) -> dict[str, list[str]]:
    explanations: dict[str, list[str]] = {"bm25": [], "dense": [], "hybrid": []}
    if not query_terms:
        for branch in explanations:
            explanations[branch].append("查询词过短或无法被标准化，检索器没有可用关键词。")

    if errors.get("bm25"):
        explanations["bm25"].append(f"BM25 分支执行失败：{errors['bm25']}")
    elif not bm25_status.get("ready"):
        explanations["bm25"].append("BM25 索引尚未构建，关键词检索无法稳定工作。")
    elif not bm25_hits:
        explanations["bm25"].append("标题和摘要中没有明显词面重叠。BM25 当前主要索引标题与摘要，若相关内容只在正文里，需要先补全文或改用更具体关键词。")
    else:
        weak_hits = sum(1 for hit in bm25_hits if not hit.match_sources)
        if weak_hits:
            explanations["bm25"].append(f"{weak_hits} 个 BM25 命中没有直接字段标记，可能来自分词近似匹配或摘要截断。")

    if errors.get("dense"):
        explanations["dense"].append(f"Dense 分支执行失败：{errors['dense']}")
    elif embedding_coverage <= 0:
        explanations["dense"].append("知识库还没有可用向量，语义检索无法运行。")
    elif embedding_coverage < 0.8:
        explanations["dense"].append(f"向量覆盖率只有 {embedding_coverage:.0%}，语义检索只覆盖部分论文，容易漏掉未生成向量的论文。")
    elif not dense_hits:
        explanations["dense"].append("语义分支没有找到正相似度候选，可能是查询过宽、语义表达与摘要差异较大，或向量质量不足。")

    if errors.get("hybrid"):
        explanations["hybrid"].append(f"Hybrid 分支执行失败：{errors['hybrid']}")
    elif not hybrid_hits:
        explanations["hybrid"].append("Hybrid 没有可用候选，通常意味着 BM25 与 Dense 都缺少支持信号。建议先检查关键词、补向量，并确认相关论文已入库。")
    elif embedding_coverage < 0.8:
        explanations["hybrid"].append(f"因为向量覆盖率低于 80%（当前 {embedding_coverage:.0%}），Hybrid 会更依赖 BM25，语义召回能力会下降。")

    return {branch: notes for branch, notes in explanations.items() if notes}


def _diagnostic_summary(hybrid_hits: list[RetrievalDiagnosticHit], explanations: dict[str, list[str]]) -> str:
    if hybrid_hits:
        missing_full_text = sum(1 for hit in hybrid_hits if not hit.has_full_text)
        missing_embedding = sum(1 for hit in hybrid_hits if not hit.has_embedding)
        notes = [f"Hybrid 找到 {len(hybrid_hits)} 个候选。"]
        if missing_full_text:
            notes.append(f"其中 {missing_full_text} 个缺全文，论文页问答可能无法回答章节级问题。")
        if missing_embedding:
            notes.append(f"其中 {missing_embedding} 个缺向量，语义检索质量会受影响。")
        return "".join(notes)
    if explanations:
        return "本轮没有找到稳定候选，建议优先查看分支解释和维护建议。"
    return "本轮没有找到候选，也没有检测到明确的系统性维护问题。"


def _maintenance_job_status_from_result(job_id: str, async_result) -> MaintenanceJobStatus:
    from app.services.maintenance_jobs import TABLE_REPAIR_JOB_KIND

    celery_state = str(getattr(async_result, "state", "") or "PENDING").upper()
    raw_info = getattr(async_result, "info", None)
    payload = raw_info if isinstance(raw_info, dict) else {}
    result_payload = getattr(async_result, "result", None) if celery_state == "SUCCESS" else None
    if isinstance(result_payload, dict):
        payload = result_payload

    state_map = {
        "PENDING": "queued",
        "RECEIVED": "queued",
        "STARTED": "running",
        "PROGRESS": "running",
        "RETRY": "running",
        "SUCCESS": "success",
        "FAILURE": "failed",
        "REVOKED": "cancelled",
    }
    state = state_map.get(celery_state, "unknown")
    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else []
    message = str(payload.get("message") or "")
    if celery_state == "FAILURE" and not message:
        message = str(raw_info or "维护任务执行失败")
    if celery_state == "FAILURE" and not errors:
        errors = [{"reason": message}]

    result = payload.get("result")
    action_result = MaintenanceActionResult(**result) if isinstance(result, dict) else None
    processed = int(payload.get("processed") or (action_result.processed if action_result else 0) or 0)
    total = int(payload.get("total") or processed or 0)
    progress_percent = int(payload.get("progress_percent") or 0)
    if not progress_percent and total:
        progress_percent = int(round((processed / total) * 100))
    if state == "success":
        progress_percent = 100

    return MaintenanceJobStatus(
        id=job_id,
        kind=str(payload.get("kind") or TABLE_REPAIR_JOB_KIND),
        state=state,
        status=str(payload.get("status") or state),
        total=total,
        processed=processed,
        success=int(payload.get("success") or (action_result.success if action_result else 0) or 0),
        failed=int(payload.get("failed") or (action_result.failed if action_result else 0) or 0),
        skipped=int(payload.get("skipped") or (action_result.skipped if action_result else 0) or 0),
        progress_percent=max(0, min(progress_percent, 100)),
        current_paper=payload.get("current_paper") if isinstance(payload.get("current_paper"), dict) else None,
        errors=errors,
        message=message,
        result=action_result,
    )


async def _format_diagnostic_hits(
    db: AsyncSession,
    query: str,
    scored: list[tuple[str, float]],
) -> list[RetrievalDiagnosticHit]:
    from uuid import UUID

    ordered_ids = []
    for paper_id, _score in scored:
        try:
            ordered_ids.append(UUID(paper_id))
        except (ValueError, TypeError):
            continue
    if not ordered_ids:
        return []

    result = await db.execute(select(Paper).where(Paper.id.in_(ordered_ids)))
    papers = {str(paper.id): paper for paper in result.scalars().all()}
    hits: list[RetrievalDiagnosticHit] = []
    for paper_id, score in scored:
        paper = papers.get(paper_id)
        if not paper:
            continue
        hits.append(
            RetrievalDiagnosticHit(
                id=paper_id,
                title=paper.title,
                score=round(float(score), 4),
                year=paper.year,
                source=paper.source,
                arxiv_id=paper.arxiv_id,
                has_full_text=bool(paper.full_text and len(paper.full_text) > 500),
                has_embedding=paper.embedding is not None,
                match_sources=_query_match_sources(query, paper),
            )
        )
    return hits


def _paper_brief(paper, *, remote: bool = False) -> PaperBrief:
    metadata = getattr(paper, "metadata", {}) if remote else getattr(paper, "metadata_json", {})
    processing = _paper_processing_flags(paper) if not remote else {}
    return PaperBrief(
        id="" if remote else str(paper.id),
        title=paper.title,
        authors=paper.authors,
        year=paper.year,
        abstract=paper.abstract[:500] if paper.abstract else None,
        abstract_full=paper.abstract or None,
        arxiv_id=paper.arxiv_id,
        doi=paper.doi,
        source=paper.source,
        citation_count=paper.citation_count,
        created_at="" if remote else paper.created_at.isoformat() if paper.created_at else "",
        remote_id=(getattr(paper, "metadata", {}) or {}).get("remote_id") if remote else None,
        remote_ingest_token=create_remote_ingest_token(paper) if remote else None,
        pdf_url=getattr(paper, "pdf_url", None) if remote else (metadata or {}).get("pdf_url"),
        source_url=getattr(paper, "source_url", None),
        imported_by_user_id=None if remote else str(getattr(paper, "imported_by_user_id", None)) if getattr(paper, "imported_by_user_id", None) else None,
        imported_by_username=None if remote else getattr(paper, "imported_by_username", None),
        importance_label=None if remote else getattr(paper, "importance_label", None),
        importance_note=None if remote else getattr(paper, "importance_note", None),
        has_pdf=bool(processing.get("has_pdf", False)),
        has_full_text=bool(processing.get("has_full_text", False)),
        has_embedding=bool(processing.get("has_embedding", False)),
        has_tags=bool(processing.get("has_tags", False)),
        processing_status=processing.get("status"),
    )


def _paper_imported_by_user(paper: Paper, user) -> bool:
    if not user:
        return False
    if paper.imported_by_user_id and str(paper.imported_by_user_id) == str(user.id):
        return True
    return bool(not paper.imported_by_user_id and paper.imported_by_username == user.username)


def _has_tags(tags: Any) -> bool:
    if not tags:
        return False
    if isinstance(tags, dict):
        return any(bool(value) for value in tags.values())
    if isinstance(tags, list):
        return len(tags) > 0
    return bool(tags)


def _paper_processing_flags(paper: Paper) -> dict[str, Any]:
    metadata = getattr(paper, "metadata_json", None) or {}
    has_pdf = bool(getattr(paper, "pdf_path", None) or metadata.get("pdf_url"))
    has_full_text = bool(getattr(paper, "full_text", None) and len(paper.full_text) > 500)
    has_embedding = getattr(paper, "embedding", None) is not None
    has_tags = _has_tags(getattr(paper, "tags", None))
    missing = []
    if not has_full_text:
        missing.append("full_text")
    if not has_embedding:
        missing.append("embedding")
    if not has_tags:
        missing.append("tags")
    if not missing:
        status = "ready"
    elif missing == ["tags"]:
        status = "needs_tags"
    elif missing == ["embedding"]:
        status = "needs_embedding"
    elif "full_text" in missing and len(missing) == 1:
        status = "needs_full_text"
    else:
        status = "needs_processing"
    return {
        "has_pdf": has_pdf,
        "has_full_text": has_full_text,
        "has_embedding": has_embedding,
        "has_tags": has_tags,
        "missing": missing,
        "status": status,
    }


def _paper_processing_status(paper: Paper) -> PaperProcessingStatus:
    from app.services.report_service import structured_pdf_parse_status_from_paper

    flags = _paper_processing_flags(paper)
    structured_status = structured_pdf_parse_status_from_paper(paper)
    actions = []
    if not flags["has_full_text"] and paper.arxiv_id:
        actions.append({"key": "full_text", "label": "补全文", "endpoint": f"/papers/{paper.id}/load-full-text"})
    if flags["has_pdf"] or paper.arxiv_id:
        actions.append({"key": "structured_parse", "label": "重解析 PDF", "endpoint": f"/papers/{paper.id}/reparse-structured-pdf"})
    if not flags["has_embedding"]:
        actions.append({"key": "embedding", "label": "生成向量", "endpoint": f"/papers/{paper.id}/embedding"})
    if not flags["has_tags"]:
        actions.append({"key": "tags", "label": "AI 标签", "endpoint": f"/papers/{paper.id}/auto-tag"})
    return PaperProcessingStatus(
        id=str(paper.id),
        title=paper.title,
        year=paper.year,
        source=paper.source,
        imported_by_username=paper.imported_by_username,
        has_pdf=flags["has_pdf"],
        has_full_text=flags["has_full_text"],
        has_embedding=flags["has_embedding"],
        has_tags=flags["has_tags"],
        status=flags["status"],
        missing=flags["missing"],
        repair_actions=actions,
        structured_parse_status=StructuredPdfParseStatus(**structured_status),
    )


def _parse_bool_filter(value: Optional[str]) -> Optional[bool]:
    if value in (None, "", "all"):
        return None
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False
    return None


@router.get("/suggest")
async def suggest_titles(q: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db)):
    """搜索建议（标题自动补全）。"""
    result = await db.execute(select(Paper.title).where(Paper.title.ilike(f"%{q}%")).order_by(Paper.title).limit(8))
    return [r[0] for r in result.all()]

# --- API Endpoints ---

@router.get("/search", response_model=PaperSearchResponse)
async def search_papers(
    q: str = Query(default="", description="搜索关键词"),
    source: str = Query(default="all", description="数据源: local, arxiv, semantic_scholar, openalex, google_scholar, scholarly, all"),
    category: Optional[str] = Query(default=None, description="分类筛选"),
    year_from: Optional[int] = Query(default=None, ge=1900, le=2030),
    year_to: Optional[int] = Query(default=None, ge=1900, le=2030),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    sort: str = Query(default="created_desc", description="排序: created_desc, created_asc, year_desc, year_asc, title"),
    search_mode: str = Query(default="hybrid", pattern="^(hybrid|dense|bm25)$", description="检索模式: hybrid, dense, bm25"),
    owner: Optional[str] = Query(default=None, pattern="^(mine)$", description="归属筛选: mine"),
    importer: Optional[str] = Query(default=None, max_length=100, description="导入账号筛选"),
    local_source: Optional[str] = Query(default=None, max_length=50, description="本地论文来源筛选"),
    has_full_text: Optional[str] = Query(default=None, description="全文可用筛选: true/false/all"),
    has_embedding: Optional[str] = Query(default=None, description="向量可用筛选: true/false/all"),
    read_status: Optional[Literal["unread", "reading", "completed"]] = Query(default=None, description="当前用户阅读状态筛选"),
    importance_label: Optional[Literal["important", "interesting"]] = Query(default=None, description="共享标记筛选"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    """搜索论文 — 支持混合检索（BM25 + Dense）。"""
    items = []
    total = 0
    if source == "google_scholar" and not settings.SERPAPI_API_KEY.strip():
        raise HTTPException(status_code=400, detail="Google Scholar 检索需要先配置 SERPAPI_API_KEY")

    sort_map = {
        "created_desc": Paper.created_at.desc(),
        "created_asc": Paper.created_at.asc(),
        "year_desc": Paper.year.desc(),
        "year_asc": Paper.year.asc(),
        "title": Paper.title.asc(),
    }
    order_by = sort_map.get(sort, Paper.created_at.desc())
    full_text_filter = _parse_bool_filter(has_full_text)
    embedding_filter = _parse_bool_filter(has_embedding)

    def apply_local_filters(query):
        if category:
            query = query.join(PaperCategory).join(Category).where(Category.name == category)
        if year_from: query = query.where(Paper.year >= year_from)
        if year_to: query = query.where(Paper.year <= year_to)
        if importer:
            query = query.where(Paper.imported_by_username == importer)
        if local_source:
            query = query.where(Paper.source == local_source)
        if importance_label:
            query = query.where(Paper.importance_label == importance_label)
        if full_text_filter is True:
            query = query.where(Paper.full_text.is_not(None), func.length(Paper.full_text) > 500)
        elif full_text_filter is False:
            query = query.where((Paper.full_text.is_(None)) | (func.length(Paper.full_text) <= 500))
        if embedding_filter is True:
            query = query.where(Paper.embedding.is_not(None))
        elif embedding_filter is False:
            query = query.where(Paper.embedding.is_(None))
        if owner == "mine":
            if not user:
                query = query.where(Paper.id.is_(None))
            else:
                query = query.where(
                    (Paper.imported_by_user_id == user.id)
                    | (
                        (Paper.imported_by_user_id.is_(None))
                        & (Paper.imported_by_username == user.username)
                    )
                )
        if read_status:
            if not user:
                query = query.where(Paper.id.is_(None))
            else:
                query = query.join(UserPaper).where(
                    UserPaper.user_id == user.id,
                    UserPaper.read_status == read_status,
                )
        return query

    # 本地数据库搜索
    if source in ("local", "all"):
        if q:
            from app.services.hybrid_search import HybridSearchService
            hs = HybridSearchService(db)
            candidate_limit = min(max(page * page_size, 100), 500)
            scored = await hs.search(q, top_k=candidate_limit, mode=search_mode)
            paper_scores = await hs.fetch_papers(
                scored,
                category=category,
                year_from=year_from,
                year_to=year_to,
            )
            if owner == "mine":
                if not user:
                    paper_scores = []
                else:
                    paper_scores = [
                        (paper, score)
                        for paper, score in paper_scores
                        if _paper_imported_by_user(paper, user)
                    ]
            if importer:
                paper_scores = [(paper, score) for paper, score in paper_scores if paper.imported_by_username == importer]
            if local_source:
                paper_scores = [(paper, score) for paper, score in paper_scores if paper.source == local_source]
            if importance_label:
                paper_scores = [
                    (paper, score) for paper, score in paper_scores
                    if getattr(paper, "importance_label", None) == importance_label
                ]
            if full_text_filter is not None:
                paper_scores = [
                    (paper, score) for paper, score in paper_scores
                    if _paper_processing_flags(paper)["has_full_text"] is full_text_filter
                ]
            if embedding_filter is not None:
                paper_scores = [
                    (paper, score) for paper, score in paper_scores
                    if _paper_processing_flags(paper)["has_embedding"] is embedding_filter
                ]
            if read_status:
                if not user:
                    paper_scores = []
                else:
                    status_result = await db.execute(
                        select(UserPaper.paper_id).where(
                            UserPaper.user_id == user.id,
                            UserPaper.read_status == read_status,
                        )
                    )
                    status_ids = {row[0] for row in status_result.all()}
                    paper_scores = [(paper, score) for paper, score in paper_scores if paper.id in status_ids]
            total = len(paper_scores)
            for paper, _score in paper_scores[page_size * (page - 1):page_size * page]:
                items.append(_paper_brief(paper))
        else:
            # 无查询：按字段排序浏览论文库
            query = select(Paper)
            query = apply_local_filters(query)
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            query = query.order_by(order_by).offset((page - 1) * page_size).limit(page_size)
            result = await db.execute(query)
            items.extend(_paper_brief(paper) for paper in result.scalars().all())

    # 远程 arXiv 搜索（不存库，仅预览）
    if source in ("arxiv", "all") and not q:
        # 返回空时说明只是浏览本地库
        pass
    elif source in ("arxiv", "semantic_scholar", "openalex", "google_scholar", "scholarly", "all") and q:
        # 远程搜索预览
        remote_page_size = min(page_size, 20)
        remote_papers = await search_scholarly_papers(
            query=q,
            source=source,
            max_results=remote_page_size,
            start=(page - 1) * remote_page_size,
            category=category,
            year_from=year_from,
            year_to=year_to,
        )
        for remote_paper in remote_papers:
            items.append(_paper_brief(remote_paper, remote=True))
        total += len(remote_papers)

    return PaperSearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_papers(
    req: IngestRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """论文入库 — 支持按 arXiv ID 或搜索查询入库。"""
    if not req.arxiv_ids and not req.search_query:
        raise HTTPException(status_code=400, detail="请提供 arxiv_ids 或 search_query")

    service = PaperIngestionService(db)

    if req.arxiv_ids:
        result = await service.ingest_by_ids(
            arxiv_ids=req.arxiv_ids,
            auto_download=req.auto_download,
            imported_by_user=user,
        )
    else:
        result = await service.search_and_ingest(
            query=req.search_query,
            max_results=req.max_results,
            source=req.source,
            auto_download=req.auto_download,
            imported_by_user=user,
        )

    return IngestResponse(
        success=result["success"],
        skipped=result["skipped"],
        error=result["error"],
        total_found=result.get("total_found", len(req.arxiv_ids or [])),
        paper_ids=result.get("paper_ids", []),
        errors=result.get("errors", []),
    )


# --- 固定路径路由（必须在 /{paper_id} 之前） ---

@router.post("/ingest-personal", response_model=IngestResponse)
async def ingest_personal_paper(
    req: PersonalIngestRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Resolve one remote preview, store it if needed, and save it for the current user."""

    service = PaperIngestionService(db)
    preview = read_remote_ingest_token(req.remote_ingest_token) if req.remote_ingest_token else None
    if preview and preview.source == req.source and preview.metadata.get("remote_id") == req.remote_id:
        paper, is_new = await service.ingest_paper(preview, auto_download=req.auto_download, imported_by_user=user)
    else:
        paper, is_new = await service.ingest_remote(
            source=req.source,
            remote_id=req.remote_id,
            auto_download=req.auto_download,
            imported_by_user=user,
        )
    if not paper:
        raise HTTPException(status_code=404, detail="未能从远程学术源解析这篇论文，请稍后重试")
    await PaperEnhanceService(db).save_paper(str(user.id), str(paper.id))
    return IngestResponse(
        success=1 if is_new else 0,
        skipped=0 if is_new else 1,
        error=0,
        total_found=1,
        paper_ids=[str(paper.id)],
    )

@router.get("/categories/tree", response_model=List[CategoryResponse])
async def get_category_tree(db: AsyncSession = Depends(get_db)):
    """获取论文分类树。"""
    result = await db.execute(
        select(Category).where(Category.parent_id.is_(None)).options(
            selectinload(Category.children)
        )
    )
    roots = result.scalars().all()

    def build_tree(cat: Category) -> dict:
        return {
            "id": str(cat.id),
            "name": cat.name,
            "description": cat.description,
            "parent_id": str(cat.parent_id) if cat.parent_id else None,
            "children": [build_tree(child) for child in (cat.children or [])],
        }

    return [CategoryResponse(**build_tree(root)) for root in roots]


class SemanticSearchResult(BaseModel):
    paper: PaperBrief
    similarity: float


@router.get("/semantic-search", response_model=List[SemanticSearchResult])
async def semantic_search(
    q: str = Query(..., description="自然语言查询，例如'强化学习在 NLP 中的应用'"),
    top_k: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """语义搜索 — 用自然语言查询找到最相关的论文。"""
    rag = RAGService(db)
    results = await rag.search_similar(q, top_k=top_k)

    return [
        SemanticSearchResult(
            paper=_paper_brief(p),
            similarity=round(score, 4),
        )
        for p, score in results
    ]


@router.post("/generate-embeddings")
async def generate_all_embeddings(db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """为所有未嵌入的论文生成向量（批量，最多 50 篇）。"""
    rag = RAGService(db)
    result = await rag.generate_embeddings_for_all()
    return result


@router.get("/export-markdown")
async def export_all_papers(db: AsyncSession = Depends(get_db)):
    """导出所有论文为 Markdown。"""
    result = await db.execute(select(Paper).order_by(Paper.created_at.desc()))
    papers = result.scalars().all()
    md = "# 论文库导出\n\n"
    for p in papers:
        md += f"## {p.title}\n\n"
        md += f"- **作者**: {', '.join(p.authors) if isinstance(p.authors, list) else p.authors or 'N/A'}\n"
        md += f"- **年份**: {p.year or 'N/A'}\n"
        md += f"- **arXiv**: {p.arxiv_id or 'N/A'}\n"
        md += f"- **摘要**: {p.abstract or 'N/A'}\n\n"
        md += "---\n\n"
    return {"markdown": md}


@router.get("/search-evaluation")
async def evaluate_local_search(
    mode: str = Query(default="bm25", pattern="^(hybrid|dense|bm25)$"),
    top_k: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """运行版本化本地检索 benchmark。"""
    from app.services.retrieval_evaluation import evaluate_retrieval
    return await evaluate_retrieval(db, mode=mode, top_k=top_k)


@router.get("/maintenance/health", response_model=RetrievalMaintenanceHealth)
async def get_retrieval_maintenance_health(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """Inspect local paper-library retrieval health."""
    from app.services.hybrid_search import bm25_index_status

    total = await _paper_count(db)
    full_text_papers = await _paper_count(db, Paper.full_text.is_not(None), func.length(Paper.full_text) > 500)
    embedding_papers = await _paper_count(db, Paper.embedding.is_not(None))
    arxiv_papers = await _paper_count(db, Paper.arxiv_id.is_not(None))
    missing_full_text = max(total - full_text_papers, 0)
    missing_embeddings = max(total - embedding_papers, 0)

    return RetrievalMaintenanceHealth(
        total_papers=total,
        full_text_papers=full_text_papers,
        missing_full_text=missing_full_text,
        embedding_papers=embedding_papers,
        missing_embeddings=missing_embeddings,
        arxiv_papers=arxiv_papers,
        full_text_coverage=round(full_text_papers / total, 4) if total else 0.0,
        embedding_coverage=round(embedding_papers / total, 4) if total else 0.0,
        bm25_index=bm25_index_status(),
        missing_full_text_samples=await _missing_samples(
            db,
            (Paper.full_text.is_(None)) | (func.length(Paper.full_text) <= 500),
        ),
        missing_embedding_samples=await _missing_samples(db, Paper.embedding.is_(None)),
    )


@router.post("/maintenance/rebuild-bm25", response_model=MaintenanceActionResult)
async def rebuild_retrieval_bm25(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """Rebuild the process-local BM25 index immediately."""
    from app.services.hybrid_search import HybridSearchService, bm25_index_status

    before = bm25_index_status()
    await HybridSearchService(db).rebuild_index()
    after = bm25_index_status()
    return MaintenanceActionResult(
        processed=int(after.get("indexed_papers") or 0),
        success=1,
        skipped=0 if before != after else 1,
    )


@router.post("/maintenance/backfill-embeddings", response_model=MaintenanceActionResult)
async def backfill_retrieval_embeddings(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """Generate embeddings for papers that are missing vectors."""
    result = await db.execute(
        select(Paper).where(Paper.embedding.is_(None)).order_by(Paper.created_at.desc()).limit(limit)
    )
    papers = result.scalars().all()
    rag = RAGService(db)
    action = MaintenanceActionResult(processed=len(papers))
    for paper in papers:
        ok = await rag.generate_embeddings_for_paper(paper)
        if ok:
            action.success += 1
        else:
            action.failed += 1
            action.errors.append({"paper_id": str(paper.id), "title": paper.title})
    return action


@router.post("/maintenance/backfill-full-text", response_model=MaintenanceActionResult)
async def backfill_retrieval_full_text(
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """Parse missing arXiv full text in a bounded batch."""
    from app.services.report_service import ensure_full_text

    result = await db.execute(
        select(Paper)
        .where(
            ((Paper.full_text.is_(None)) | (func.length(Paper.full_text) <= 500))
            & Paper.arxiv_id.is_not(None)
        )
        .order_by(Paper.created_at.desc())
        .limit(limit)
    )
    papers = result.scalars().all()
    action = MaintenanceActionResult(processed=len(papers))
    for paper in papers:
        try:
            text = await ensure_full_text(paper)
            if text and len(text) > 500:
                paper.full_text = text
                action.success += 1
            elif text:
                action.skipped += 1
            else:
                action.failed += 1
                action.errors.append({"paper_id": str(paper.id), "title": paper.title, "reason": "empty full text"})
        except Exception as exc:
            action.failed += 1
            action.errors.append({"paper_id": str(paper.id), "title": paper.title, "reason": str(exc)})
    if action.success:
        await db.commit()
    return action


@router.post("/maintenance/backfill-structured-pdf", response_model=MaintenanceActionResult)
async def backfill_structured_pdf_parse(
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """Run bounded structured PDF parsing for papers that need parser metadata."""
    from app.services.report_service import (
        force_structured_pdf_reparse,
        structured_pdf_parse_status_from_paper,
    )

    result = await db.execute(
        select(Paper)
        .where((Paper.pdf_path.is_not(None)) | (Paper.arxiv_id.is_not(None)))
        .order_by(Paper.created_at.desc())
        .limit(limit * 4)
    )
    candidates = result.scalars().all()
    papers = []
    for candidate in candidates:
        status = structured_pdf_parse_status_from_paper(candidate)
        if not status.get("ready") or status.get("last_error"):
            papers.append(candidate)
        if len(papers) >= limit:
            break
    action = MaintenanceActionResult(processed=len(papers))
    for paper in papers:
        try:
            status = structured_pdf_parse_status_from_paper(paper)
            if status.get("ready") and not status.get("last_error"):
                action.skipped += 1
                continue
            refreshed = await force_structured_pdf_reparse(paper, db)
            if refreshed.get("ready"):
                action.success += 1
            else:
                action.skipped += 1
                action.errors.append({"paper_id": str(paper.id), "title": paper.title, "reason": "no structured blocks"})
        except Exception as exc:
            action.failed += 1
            action.errors.append({"paper_id": str(paper.id), "title": paper.title, "reason": str(exc)})
    if action.success or action.failed:
        await db.commit()
    return action


@router.get("/maintenance/jobs/{job_id}", response_model=MaintenanceJobStatus)
async def get_maintenance_job_status(
    job_id: str,
    user=Depends(require_admin),
):
    """Return normalized status for a queued maintenance job."""
    from app.tasks.celery_app import celery_app

    async_result = celery_app.AsyncResult(job_id)
    return _maintenance_job_status_from_result(job_id, async_result)


@router.post("/maintenance/repair-tables", response_model=MaintenanceJobStartResponse)
async def repair_low_quality_tables(
    limit: int = Query(default=5, ge=1, le=20),
    user=Depends(require_admin),
):
    """Queue bounded high-fidelity table repair for papers with low-quality parsed tables."""
    from app.services.maintenance_jobs import TABLE_REPAIR_JOB_KIND
    from app.tasks.paper_tasks import repair_low_quality_tables_task

    task = repair_low_quality_tables_task.delay(limit)
    job_id = str(task.id)
    return MaintenanceJobStartResponse(
        job_id=job_id,
        status_endpoint=f"/papers/maintenance/jobs/{job_id}",
        job=MaintenanceJobStatus(
            id=job_id,
            kind=TABLE_REPAIR_JOB_KIND,
            state="queued",
            status="queued",
            message="表格修复任务已进入队列",
        ),
    )


@router.get("/maintenance/recommendations", response_model=list[MaintenanceRecommendation])
async def get_retrieval_maintenance_recommendations(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """Return prioritized retrieval repair recommendations."""
    return await _maintenance_recommendations(db)


@router.get("/processing-status", response_model=PaperProcessingStatusResponse)
async def get_paper_processing_statuses(
    limit: int = Query(default=30, ge=1, le=100),
    status: Optional[Literal["all", "ready", "needs_processing"]] = Query(default="all"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    """Return derived processing readiness for local papers."""
    result = await db.execute(select(Paper).order_by(Paper.created_at.desc()).limit(limit))
    all_items = [_paper_processing_status(paper) for paper in result.scalars().all()]
    items = all_items
    if status == "ready":
        items = [item for item in all_items if item.status == "ready"]
    elif status == "needs_processing":
        items = [item for item in all_items if item.status != "ready"]
    return PaperProcessingStatusResponse(
        items=items,
        total=len(all_items),
        ready=sum(1 for item in all_items if item.status == "ready"),
        needs_processing=sum(1 for item in all_items if item.status != "ready"),
    )


@router.get("/maintenance/search-diagnostics", response_model=RetrievalDiagnosticsResponse)
async def diagnose_retrieval_query(
    q: str = Query(..., min_length=1, max_length=300),
    top_k: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """Compare BM25, dense, and hybrid retrieval branches for one query."""
    from app.services.hybrid_search import HybridSearchService, bm25_index_status, tokenize_academic_text

    service = HybridSearchService(db)
    errors: dict[str, str] = {}
    query_terms = tokenize_academic_text(q)

    async def run_branch(name: str, mode: str) -> list[RetrievalDiagnosticHit]:
        try:
            scored = await service.search(q, top_k=top_k, mode=mode)
            return await _format_diagnostic_hits(db, q, scored)
        except Exception as exc:
            logger.warning("检索诊断 %s 分支失败: %s", name, exc)
            errors[name] = str(exc)
            return []

    bm25_hits = await run_branch("bm25", "bm25")
    dense_hits = await run_branch("dense", "dense")
    hybrid_hits = await run_branch("hybrid", "hybrid")
    try:
        embedding_coverage = await service.embedding_coverage()
    except Exception:
        embedding_coverage = 0.0
    branch_explanations = _diagnostic_branch_explanations(
        query_terms=query_terms,
        bm25_hits=bm25_hits,
        dense_hits=dense_hits,
        hybrid_hits=hybrid_hits,
        bm25_status=bm25_index_status(),
        embedding_coverage=embedding_coverage,
        errors=errors,
    )
    return RetrievalDiagnosticsResponse(
        query=q,
        query_terms=query_terms,
        top_k=top_k,
        summary=_diagnostic_summary(hybrid_hits, branch_explanations),
        bm25=bm25_hits,
        dense=dense_hits,
        hybrid=hybrid_hits,
        branch_explanations=branch_explanations,
        recommended_actions=await _maintenance_recommendations(db, include_samples=False),
        errors=errors,
    )


# --- 动态路径路由（/{paper_id} 必须在固定路径之后） ---

@router.get("/{paper_id}", response_model=PaperDetail)
async def get_paper_detail(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    """获取论文详情。"""
    from uuid import UUID

    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(
        select(Paper).where(Paper.id == pid).options(
            selectinload(Paper.categories)
        )
    )
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    # 计算相似论文
    enhance = PaperEnhanceService(db)
    similar = await enhance.similar_papers(paper, top_k=3)

    # 后台预加载 PDF 全文（不阻塞响应）
    if user and user.role == "admin" and paper.arxiv_id and not paper.full_text:
        try:
            from app.services.report_service import ensure_full_text
            import asyncio
            asyncio.create_task(ensure_full_text(paper))
        except Exception:
            pass
    from app.services.report_service import structured_pdf_parse_status_from_paper

    return PaperDetail(
        id=str(paper.id),
        title=paper.title,
        authors=paper.authors,
        year=paper.year,
        abstract=paper.abstract,
        arxiv_id=paper.arxiv_id,
        doi=paper.doi,
        source=paper.source,
        source_url=paper.source_url,
        pdf_path=paper.pdf_path,
        citation_count=paper.citation_count,
        imported_by_user_id=str(paper.imported_by_user_id) if paper.imported_by_user_id else None,
        imported_by_username=paper.imported_by_username,
        importance_label=paper.importance_label,
        importance_note=paper.importance_note,
        full_text_preview=paper.full_text[:5000] if paper.full_text else None,
        tags=paper.tags,
        categories=[
            {"id": str(c.id), "name": c.name}
            for c in (paper.categories or [])
        ],
        metadata_json=paper.metadata_json,
        structured_parse_status=StructuredPdfParseStatus(**structured_pdf_parse_status_from_paper(paper)),
        created_at=paper.created_at.isoformat() if paper.created_at else "",
        similar_papers=[
            {"id": str(sp.id), "title": sp.title, "year": sp.year, "arxiv_id": sp.arxiv_id, "tags": sp.tags}
            for sp in similar
        ],
    )


@router.get("/{paper_id}/processing-status", response_model=PaperProcessingStatus)
async def get_paper_processing_status(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    """Return derived processing readiness for one paper."""
    from uuid import UUID

    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")
    return _paper_processing_status(paper)


def _parse_insight_sections(text: str) -> dict[str, str]:
    keys = {
        "核心贡献": "contribution",
        "可借鉴方法": "reusable_methods",
        "可复现实验": "reproducible_experiments",
        "局限": "limitations",
        "研究缺口": "research_gaps",
        "研究方向关联": "research_fit",
    }
    parsed = {value: "" for value in keys.values()}
    current = None
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched = False
        for title, key in keys.items():
            if title in line and (line.startswith("#") or line.startswith(title)):
                current = key
                matched = True
                break
        if not matched and current:
            parsed[current] += raw_line.strip("- ") + "\n"
    return {key: value.strip() for key, value in parsed.items()}


@router.get("/{paper_id}/insights", response_model=PaperInsightResponse)
async def get_paper_ai_insights(
    paper_id: str,
    refresh: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate or return cached AI insight cards for one paper."""
    from uuid import UUID

    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    metadata = dict(paper.metadata_json or {})
    cached = metadata.get("ai_insights")
    if cached and not refresh:
        return PaperInsightResponse(**cached)

    has_full_text = bool(paper.full_text and len(paper.full_text) > 500)
    context = paper.full_text[:9000] if has_full_text else paper.abstract or ""
    prompt = f"""你是一位资深科研导师。请基于下面论文资料，输出结构化中文洞察，必须避免编造。

标题: {paper.title}
作者: {', '.join(paper.authors[:5]) if isinstance(paper.authors, list) else paper.authors}
年份: {paper.year or 'N/A'}
摘要: {paper.abstract or '无'}
正文片段: {context or '无'}

请严格按以下 Markdown 二级标题输出，每部分 2-4 个要点：

## 核心贡献
## 可借鉴方法
## 可复现实验
## 局限
## 研究缺口
## 研究方向关联
"""
    raw = await llm_service.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
        max_tokens=2048,
    )
    sections = _parse_insight_sections(raw)
    payload = {
        "paper_id": str(paper.id),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_coverage": "full_text" if has_full_text else "abstract_only",
        "raw": raw,
        **sections,
    }
    metadata["ai_insights"] = payload
    paper.metadata_json = metadata
    await db.commit()
    return PaperInsightResponse(**payload)


# --- 论文增强 API ---

class AskPaperRequest(BaseModel):
    question: str = Field(..., description="关于论文的问题")
    history: Optional[list] = None
    rag_enabled: bool = Field(default=True, description="是否额外检索相关论文")
    web_search: bool = Field(default=False, description="是否启用联网增强")
    search_depth: Literal["quick", "standard", "deep"] = Field(default="standard", description="检索深度")
    show_thinking: bool = Field(default=False, description="是否展示思考过程")


class PaperUserState(BaseModel):
    saved: bool
    read_status: str
    personal_notes: Optional[str]
    personal_tags: Optional[list]


class ReadingStatusCounts(BaseModel):
    unread: int = 0
    reading: int = 0
    completed: int = 0


async def _build_paper_chat_context(paper, req: AskPaperRequest) -> tuple[list[dict[str, str]], list[dict]]:
    """以当前论文为主上下文，并按配置追加相关论文与网络来源。"""
    from app.api.chat_sessions import _append_retrieval_context
    from app.services.memory_service import build_paper_context_with_evidence

    context, evidence_refs = await build_paper_context_with_evidence(paper, req.question, req.history)
    references = await _append_retrieval_context(
        context,
        req.question,
        rag_enabled=req.rag_enabled,
        web_search_enabled=req.web_search,
        search_depth=req.search_depth,
    )
    return context, [*evidence_refs, *references]


def _paper_evidence_meta(references: list[dict]) -> dict:
    evidence = [ref for ref in references if ref.get("type") == "paper_evidence"]
    coverage = min(1.0, len(evidence) / 3)
    return {
        "evidence_count": len(evidence),
        "evidence_coverage": round(coverage, 4),
        "evidence_insufficient": len(evidence) == 0,
    }


PAPER_CHAT_RECOVERY_STATUS = "首轮生成未返回正文，正在切换稳定回答模式..."
PAPER_CHAT_INTERRUPTED_WARNING = "回答生成中断，以上内容可能不完整。"
PAPER_CHAT_PRIMARY_TIMEOUT_SECONDS = 30.0
PAPER_CHAT_RECOVERY_PROMPT = (
    "请停止继续展开分析，直接根据已有上下文输出简洁、完整的最终答案。"
    "优先回答用户问题；如果资料不足，请明确说明，不要返回空内容。"
)


async def _stream_thinking_until_first_visible_content(
    context: list[dict[str, str]],
    *,
    max_tokens: int,
) -> AsyncIterator[dict[str, str]]:
    """Stream thinking events, guarding only the wait for first visible content."""
    import asyncio

    stream = llm_service.chat_stream_with_thinking(
        messages=context,
        temperature=0.5,
        max_tokens=max_tokens,
    )
    deadline = time.monotonic() + PAPER_CHAT_PRIMARY_TIMEOUT_SECONDS
    emitted_content = False
    while True:
        try:
            if emitted_content:
                event = await anext(stream)
            else:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("paper chat primary stream produced no visible content before timeout")
                event = await asyncio.wait_for(anext(stream), timeout=remaining)
        except StopAsyncIteration:
            return

        if event["type"] == "content" and event["content"]:
            emitted_content = True
        yield event


async def _stream_paper_answer_events(
    context: list[dict[str, str]],
    *,
    show_thinking: bool,
    max_tokens: int,
) -> AsyncIterator[dict[str, str]]:
    """生成论文问答事件；首轮无正文时切换到稳定回答模式。"""
    emitted_content = False
    try:
        if show_thinking:
            async for event in _stream_thinking_until_first_visible_content(context, max_tokens=max_tokens):
                if event["type"] == "content" and event["content"]:
                    emitted_content = True
                yield event
        else:
            async for token in llm_service.chat_stream(
                messages=context,
                temperature=0.5,
                max_tokens=max_tokens,
            ):
                if not token:
                    continue
                emitted_content = True
                yield {"type": "content", "content": token}
    except Exception as exc:
        if emitted_content:
            logger.warning("论文问答已输出正文后中断: %s", exc)
            yield {"type": "warning", "content": PAPER_CHAT_INTERRUPTED_WARNING}
            return
        logger.warning(f"论文问答首轮未返回正文，切换稳定模式: {exc}")

    if emitted_content:
        return

    yield {"type": "status", "content": PAPER_CHAT_RECOVERY_STATUS}
    recovery_context = [
        *context,
        {"role": "system", "content": PAPER_CHAT_RECOVERY_PROMPT},
    ]
    async for token in llm_service.chat_stream(
        messages=recovery_context,
        temperature=0.3,
        max_tokens=max_tokens,
    ):
        if token:
            yield {"type": "content", "content": token}


@router.post("/{paper_id}/ask", response_model=dict)
async def ask_about_paper(paper_id: str, req: AskPaperRequest, db: AsyncSession = Depends(get_db)):
    """针对某篇论文进行 AI 问答。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    context, references = await _build_paper_chat_context(paper, req)
    answer = await llm_service.chat(
        messages=context,
        temperature=0.5,
        max_tokens=llm_service.paper_chat_max_tokens(),
    )
    return {"answer": answer, "references": references, "evidence": _paper_evidence_meta(references)}


@router.post("/{paper_id}/ask-stream")
async def ask_about_paper_stream(paper_id: str, req: AskPaperRequest, db: AsyncSession = Depends(get_db)):
    """流式论文问答。"""
    from uuid import UUID
    try: pid = UUID(paper_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper: raise HTTPException(status_code=404, detail="论文未找到")

    context, references = await _build_paper_chat_context(paper, req)
    max_tokens = llm_service.paper_chat_max_tokens()
    from app.api.chat_sessions import _retrieval_quality_snapshot
    retrieval_quality = await _retrieval_quality_snapshot(rag_enabled=req.rag_enabled)

    async def generate():
        from app.api.chat_sessions import (
            EMPTY_STREAM_FALLBACK,
            _retrieval_status,
            _stream_event,
            _stream_failure_content,
        )

        full = ""
        yield _stream_event(
            "status",
            _retrieval_status(
                references,
                web_search_enabled=req.web_search,
                subject="论文资料",
                retrieval_quality=retrieval_quality,
            ),
        )
        yield _stream_event("meta", {"references": references, "evidence": _paper_evidence_meta(references)})
        try:
            async for event in _stream_paper_answer_events(
                context,
                show_thinking=req.show_thinking,
                max_tokens=max_tokens,
            ):
                if event["type"] == "status":
                    yield _stream_event("status", event["content"])
                elif event["type"] == "reasoning":
                    yield _stream_event("reasoning", event["content"])
                elif event["type"] == "content":
                    full += event["content"]
                    yield _stream_event("content", event["content"])
                elif event["type"] == "warning":
                    yield _stream_event("warning", event["content"])
        except Exception as exc:
            logger.exception(f"论文问答流式生成失败: {exc}")
            full, appended = _stream_failure_content(full)
            yield _stream_event("error", appended)

        if not full.strip():
            full = EMPTY_STREAM_FALLBACK
            yield _stream_event("error", full)
        yield _stream_event("done")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{paper_id}/auto-tag")
async def auto_tag_paper(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """AI 多层次标签提取（参考 TopicGPT + LLM-TAKE）。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    from app.services.tagging_service import TaggingService
    tagger = TaggingService(db)
    tags = await tagger.generate_tags(paper)
    return {"tags": tags}


@router.post("/auto-tag-all")
async def auto_tag_all_papers(db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """批量多层次标签提取。"""
    from app.services.tagging_service import TaggingService
    tagger = TaggingService(db)
    return await tagger.tag_all_papers()


@router.post("/{paper_id}/save")
async def save_paper(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """收藏论文。"""
    enhance = PaperEnhanceService(db)
    await enhance.save_paper(str(user.id), paper_id)
    return {"saved": True}


@router.put("/{paper_id}/importance", response_model=PaperImportanceResponse)
async def update_paper_importance(
    paper_id: str,
    req: PaperImportanceRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """更新团队共享论文标记。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    if req.label is None:
        paper.importance_label = None
        paper.importance_note = None
    else:
        paper.importance_label = req.label
        paper.importance_note = (req.note or "").strip() or None
    await db.commit()
    await db.refresh(paper)
    return PaperImportanceResponse(
        id=str(paper.id),
        importance_label=paper.importance_label,
        importance_note=paper.importance_note,
    )


class ReadStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(unread|reading|completed)$")

@router.put("/{paper_id}/read-status")
async def update_read_status(paper_id: str, req: ReadStatusRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """更新论文阅读状态。"""
    from uuid import UUID
    try: pid = UUID(paper_id)
    except ValueError: raise HTTPException(status_code=400)
    result = await db.execute(select(UserPaper).where(UserPaper.user_id==user.id, UserPaper.paper_id==pid))
    up = result.scalar_one_or_none()
    if not up: up = UserPaper(user_id=user.id, paper_id=pid, saved=True); db.add(up)
    up.saved = True
    up.read_status = req.status; await db.commit()
    return {"read_status": req.status, "saved": True}

@router.get("/collection/reading-status-counts", response_model=ReadingStatusCounts)
async def get_reading_status_counts(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """获取当前用户阅读队列状态计数。"""
    result = await db.execute(
        select(UserPaper.read_status, func.count(UserPaper.id))
        .where(UserPaper.user_id == user.id)
        .group_by(UserPaper.read_status)
    )
    counts = {"unread": 0, "reading": 0, "completed": 0}
    for status, count in result.all():
        if status in counts:
            counts[status] = int(count or 0)
    return ReadingStatusCounts(**counts)

@router.get("/collection/reading-list")
async def get_reading_list(status: Literal["unread", "reading", "completed"] = Query(default="unread"), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """获取阅读列表。"""
    result = await db.execute(select(Paper).join(UserPaper).where(UserPaper.user_id==user.id, UserPaper.read_status==status).order_by(UserPaper.created_at.desc()).limit(50))
    papers = result.scalars().all()
    return [{**_paper_brief(p).model_dump(), "read_status": status} for p in papers]

@router.delete("/{paper_id}/save")
async def unsave_paper(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """取消收藏。"""
    enhance = PaperEnhanceService(db)
    await enhance.unsave_paper(str(user.id), paper_id)
    return {"saved": False}


@router.get("/{paper_id}/user-state", response_model=PaperUserState)
async def get_paper_user_state(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """获取用户对论文的个人状态。"""
    enhance = PaperEnhanceService(db)
    up = await enhance.get_user_paper(str(user.id), paper_id)
    if up:
        return PaperUserState(saved=up.saved, read_status=up.read_status, personal_notes=up.personal_notes, personal_tags=up.personal_tags)
    return PaperUserState(saved=False, read_status="unread", personal_notes=None, personal_tags=None)


class UpdateNoteRequest(BaseModel):
    note: str = Field(..., description="个人笔记")


@router.put("/{paper_id}/note")
async def update_paper_note(paper_id: str, req: UpdateNoteRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """更新论文个人笔记。"""
    enhance = PaperEnhanceService(db)
    await enhance.update_note(str(user.id), paper_id, req.note)
    return {"updated": True}


@router.get("/collection/saved", response_model=List[PaperBrief])
async def get_saved_papers(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """获取用户收藏的论文。"""
    enhance = PaperEnhanceService(db)
    papers = await enhance.get_saved_papers(str(user.id))
    return [_paper_brief(p) for p in papers]


@router.post("/{paper_id}/load-full-text")
async def load_full_text(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """强制加载论文全文（同步，可能需要10-30秒）。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    from app.services.report_service import ensure_full_text
    text = await ensure_full_text(paper)
    await db.commit()
    from app.services.report_service import structured_pdf_parse_status_from_paper
    return {
        "full_text_length": len(text) if text else 0,
        "success": bool(text),
        "structured_parse_status": structured_pdf_parse_status_from_paper(paper),
    }


@router.post("/{paper_id}/reparse-structured-pdf", response_model=StructuredPdfParseStatus)
async def reparse_structured_pdf(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """Force structured PDF parsing and refresh parser status metadata."""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    from app.services.report_service import force_structured_pdf_reparse, structured_pdf_parse_status_from_paper
    try:
        status = await force_structured_pdf_reparse(paper, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        status = structured_pdf_parse_status_from_paper(paper)
        status["last_error"] = status.get("last_error") or {"message": str(exc)}
        await db.commit()
        raise HTTPException(status_code=500, detail={"message": "结构化解析失败", "status": status})

    await db.commit()
    await db.refresh(paper)
    return StructuredPdfParseStatus(**structured_pdf_parse_status_from_paper(paper))


@router.get("/pdf-proxy/{arxiv_id:path}")
async def proxy_pdf(arxiv_id: str):
    """Serve an arXiv PDF from persistent cache, downloading through mirrors on miss."""
    from app.services.arxiv_pdf_cache import ArxivPdfCacheError, ensure_cached_arxiv_pdf

    try:
        cached_pdf = await ensure_cached_arxiv_pdf(arxiv_id)
        return FileResponse(
            path=cached_pdf.path,
            media_type="application/pdf",
            filename=f"{cached_pdf.arxiv_id.replace('/', '--')}.pdf",
            content_disposition_type="inline",
            headers={
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*",
                "X-PDF-Cache": "HIT" if cached_pdf.cache_hit else "MISS",
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ArxivPdfCacheError as exc:
        raise HTTPException(status_code=502, detail=f"arXiv PDF 加载失败: {exc}")


class SaveChatHistoryRequest(BaseModel):
    messages: list = Field(..., description="对话消息列表 [{role, content, timestamp}]")


class PaperAnnotationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    page: int = Field(..., ge=1)
    kind: str = Field(default="quote", pattern="^(quote|highlight|question|idea)$")
    note: Optional[str] = Field(default=None, max_length=1000)


class PaperAnnotationResponse(BaseModel):
    id: str
    text: str
    page: int
    kind: str = "quote"
    note: Optional[str] = None
    created_at: str


async def _get_or_create_user_paper_for_state(db: AsyncSession, user_id, paper_id):
    result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user_id,
            UserPaper.paper_id == paper_id,
        )
    )
    up = result.scalar_one_or_none()
    if not up:
        up = UserPaper(user_id=user_id, paper_id=paper_id, saved=True)
        db.add(up)
    return up


@router.get("/{paper_id}/annotations", response_model=List[PaperAnnotationResponse])
async def list_paper_annotations(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """获取当前用户对论文保存的 PDF 摘录/引用。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user.id,
            UserPaper.paper_id == pid,
        )
    )
    up = result.scalar_one_or_none()
    return up.personal_annotations if up and up.personal_annotations else []


@router.post("/{paper_id}/annotations", response_model=PaperAnnotationResponse)
async def create_paper_annotation(paper_id: str, req: PaperAnnotationRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """保存当前用户的 PDF 摘录/引用。"""
    from uuid import UUID, uuid4
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    up = await _get_or_create_user_paper_for_state(db, user.id, pid)
    up.saved = True
    annotation = {
        "id": str(uuid4()),
        "text": req.text.strip(),
        "page": req.page,
        "kind": req.kind,
        "note": req.note,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    up.personal_annotations = [*(up.personal_annotations or []), annotation]
    await db.commit()
    return annotation


@router.delete("/{paper_id}/annotations/{annotation_id}")
async def delete_paper_annotation(paper_id: str, annotation_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """删除当前用户的一条 PDF 摘录/引用。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user.id,
            UserPaper.paper_id == pid,
        )
    )
    up = result.scalar_one_or_none()
    if not up:
        raise HTTPException(status_code=404, detail="标注未找到")

    annotations = up.personal_annotations or []
    next_annotations = [item for item in annotations if item.get("id") != annotation_id]
    if len(next_annotations) == len(annotations):
        raise HTTPException(status_code=404, detail="标注未找到")

    up.personal_annotations = next_annotations
    await db.commit()
    return {"deleted": True, "annotation_id": annotation_id}


@router.get("/{paper_id}/chat-history")
async def get_chat_history(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """获取论文对话历史。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user.id,
            UserPaper.paper_id == pid,
        )
    )
    up = result.scalar_one_or_none()
    return {"messages": up.paper_chat_history if up else []}


@router.post("/{paper_id}/chat-history")
async def save_chat_history(paper_id: str, req: SaveChatHistoryRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """保存论文对话历史。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user.id,
            UserPaper.paper_id == pid,
        )
    )
    up = result.scalar_one_or_none()
    if not up:
        up = UserPaper(user_id=user.id, paper_id=pid, saved=True)
        db.add(up)

    up.paper_chat_history = req.messages
    await db.commit()
    return {"saved": True, "message_count": len(req.messages)}


@router.delete("/{paper_id}/chat-history")
async def clear_chat_history(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """清空论文对话历史，保留收藏、笔记和阅读状态。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user.id,
            UserPaper.paper_id == pid,
        )
    )
    up = result.scalar_one_or_none()
    deleted = len(up.paper_chat_history or []) if up else 0
    if up:
        up.paper_chat_history = []
        await db.commit()
    return {"deleted": deleted}


@router.post("/{paper_id}/embedding")
async def generate_paper_embedding(paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """为单篇论文生成向量嵌入。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    rag = RAGService(db)
    success = await rag.generate_embeddings_for_paper(paper)
    return {"paper_id": paper_id, "embedding_generated": success}


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """删除论文（从总库或仅从个人收藏移除）。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    # 先尝试从个人收藏移除
    result = await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user.id,
            UserPaper.paper_id == pid,
        )
    )
    up = result.scalar_one_or_none()
    if up:
        await db.delete(up)

    # 检查是否有其他人收藏了这篇论文
    remaining = await db.execute(
        select(UserPaper).where(UserPaper.paper_id == pid)
    )
    others = remaining.scalars().all()

    return {
        "deleted": True,
        "from_collection": True,
        "has_other_users": len(others) > 0,
    }


@router.delete("/{paper_id}/global")
async def delete_paper_global(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin),
):
    """从总论文库永久删除论文（需要管理员权限）。"""
    from uuid import UUID
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")

    result = await db.execute(select(Paper).where(Paper.id == pid))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")

    await db.delete(paper)
    await db.commit()
    return {"deleted": True, "global": True, "title": paper.title}


@router.get("/{paper_id}/citations")
async def get_citation_network(paper_id: str, db: AsyncSession = Depends(get_db)):
    """获取论文引用网络。"""
    from uuid import UUID
    try: pid = UUID(paper_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid paper_id")
    paper = (await db.execute(select(Paper).where(Paper.id == pid))).scalar_one_or_none()
    if not paper: raise HTTPException(status_code=404, detail="论文未找到")
    enhance = PaperEnhanceService(db)
    similar = await enhance.similar_papers(paper, top_k=8)
    return {
        "paper": {"id": str(paper.id), "title": paper.title, "year": paper.year, "arxiv_id": paper.arxiv_id},
        "related": [{"id": str(p.id), "title": p.title, "year": p.year, "arxiv_id": p.arxiv_id} for p in similar],
    }

class ExplainRequest(BaseModel):
    text: str = Field(..., description="需要解释的文本")
    paper_id: str = Field(..., description="论文 ID（提供上下文）")


@router.post("/explain-text")
async def explain_selected_text(req: ExplainRequest):
    """AI 解释选中的论文文本（划词翻译/解释）。"""
    prompt = f"""你是一位学术导师。请用简洁的中文解释以下这段学术文本，帮助读者理解：
- 先概括核心意思（1-2句）
- 然后解释关键术语
- 如果涉及公式或数据，简要说明其含义

选中文本：
{req.text[:2000]}

请控制在 200 字以内，直接输出解释，不要前缀。
"""
    try:
        answer = await llm_service.chat(messages=[{"role": "user", "content": prompt}], temperature=0.3, max_tokens=512)
        return {"explanation": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解释失败: {str(e)}")

class BatchTagRequest(BaseModel): paper_ids: List[str]; tags: List[str]

@router.post("/batch-tag")
async def batch_tag_papers(req: BatchTagRequest, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """批量添加标签。"""
    from uuid import UUID
    updated = 0
    for pid in req.paper_ids:
        try:
            p = (await db.execute(select(Paper).where(Paper.id == UUID(pid)))).scalar_one_or_none()
            if p:
                existing = list(p.tags.get("keywords", [])) if isinstance(p.tags, dict) else (p.tags or [])
                for t in req.tags:
                    if t not in existing: existing.append(t)
                p.tags = p.tags or {};
                if isinstance(p.tags, dict): p.tags["keywords"] = existing
                else: p.tags = existing
                updated += 1
        except: pass
    await db.commit()
    return {"updated": updated}

class ValidateRequest(BaseModel):
    answer: str = Field(..., description="AI 回复文本")
    references: list = Field(default_factory=list, description="引用列表")

@router.post("/validate-citations")
async def validate_citations_endpoint(req: ValidateRequest, db: AsyncSession = Depends(get_db)):
    """验证 AI 回复中的引用是否真实。"""
    from app.services.citation_validator import validate_citations
    return await validate_citations(db, req.answer, req.references)

@router.post("/import-bibtex")
async def import_bibtex(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """导入 BibTeX 文件。"""
    import re
    content = (await file.read()).decode("utf-8", errors="ignore")
    entries = re.findall(r'@\w+\{([^,]+),((?:[^@{]|{[^}]*})*)', content, re.DOTALL)
    imported = 0; skipped = 0
    for cite_key, fields in entries:
        try:
            title = re.search(r'title\s*=\s*\{([^}]+)\}', fields, re.IGNORECASE)
            author = re.search(r'author\s*=\s*\{([^}]+)\}', fields, re.IGNORECASE)
            year = re.search(r'year\s*=\s*\{(\d+)\}', fields, re.IGNORECASE)
            arxiv = re.search(r'eprint\s*=\s*\{([^}]+)\}', fields, re.IGNORECASE)
            if not title: continue
            existing = (await db.execute(select(Paper).where(Paper.title == title.group(1).strip()))).scalar_one_or_none()
            if existing: skipped += 1; continue
            p = Paper(title=title.group(1).strip(), authors=author.group(1).split(' and ') if author else [],
                       year=int(year.group(1)) if year else None, arxiv_id=arxiv.group(1) if arxiv else None, source="bibtex_import",
                       imported_by_user_id=user.id, imported_by_username=user.username)
            db.add(p); imported += 1
        except: skipped += 1
    await db.commit()
    if imported:
        from app.services.hybrid_search import invalidate_bm25_index
        invalidate_bm25_index()
    return {"imported": imported, "skipped": skipped}

@router.post("/import-zotero")
async def import_zotero_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    """导入 Zotero CSV 导出文件。"""
    import csv, io
    content = (await file.read()).decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(content))
    imported = 0; skipped = 0
    for row in reader:
        try:
            title = row.get("Title", "").strip()
            if not title: continue
            existing = (await db.execute(select(Paper).where(Paper.title == title))).scalar_one_or_none()
            if existing: skipped += 1; continue
            year = int(row["Publication Year"]) if row.get("Publication Year","").isdigit() else None
            authors = [a.strip() for a in row.get("Author","").split(";") if a.strip()]
            doi = row.get("DOI","").strip() or None
            p = Paper(title=title, authors=authors, year=year, doi=doi, abstract=row.get("Abstract Note","")[:500] or None, source="zotero_import",
                      imported_by_user_id=user.id, imported_by_username=user.username)
            db.add(p); imported += 1
        except: skipped += 1
    await db.commit()
    if imported:
        from app.services.hybrid_search import invalidate_bm25_index
        invalidate_bm25_index()
    return {"imported": imported, "skipped": skipped}
