"""Automatic paper-library processing lifecycle orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.paper import Paper

logger = logging.getLogger(__name__)

ArtifactState = Literal["ready", "missing", "pending", "running", "failed", "stale"]

PIPELINE_METADATA_KEY = "paper_processing_pipeline"
AUTOMATION_VERSION = 1
FULL_TEXT_MIN_CHARS = 500
RUNNING_STEP_TTL_SECONDS = 2 * 60 * 60


@dataclass(frozen=True)
class ProcessingLabel:
    key: str
    label: str
    state: ArtifactState
    ready: bool = False
    detail: str = ""
    count: Optional[int] = None
    action: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "state": self.state,
            "ready": self.ready,
            "detail": self.detail,
        }
        if self.count is not None:
            payload["count"] = self.count
        if self.action:
            payload["action"] = self.action
        return payload


@dataclass(frozen=True)
class PaperProcessingSnapshot:
    status: Literal["ready", "processing", "needs_processing", "failed"]
    labels: list[ProcessingLabel] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    automation: dict[str, Any] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ready": self.ready,
            "labels": [label.to_dict() for label in self.labels],
            "missing": list(self.missing),
            "failed": list(self.failed),
            "automation": dict(self.automation),
        }


@dataclass
class PaperProcessingResult:
    paper_id: str
    title: str
    attempted: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    failed: list[dict[str, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    before: Optional[PaperProcessingSnapshot] = None
    after: Optional[PaperProcessingSnapshot] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "attempted": self.attempted,
            "completed": self.completed,
            "failed": self.failed,
            "skipped": self.skipped,
            "before": self.before.to_dict() if self.before else None,
            "after": self.after.to_dict() if self.after else None,
        }


def _pipeline_metadata(paper: Paper) -> dict[str, Any]:
    metadata = getattr(paper, "metadata_json", None) or {}
    pipeline = metadata.get(PIPELINE_METADATA_KEY)
    return pipeline if isinstance(pipeline, dict) else {}


def _parse_pipeline_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def paper_processing_running_state(
    paper: Paper,
    *,
    now: Optional[datetime] = None,
    ttl_seconds: int = RUNNING_STEP_TTL_SECONDS,
) -> dict[str, Any]:
    """Classify running metadata as fresh or stale for scheduler decisions."""

    pipeline = _pipeline_metadata(paper)
    running_steps = [
        str(step)
        for step in (pipeline.get("running_steps") or [])
        if step
    ]
    queued_steps = [
        str(step)
        for step in (pipeline.get("queued_steps") or [])
        if step
    ]
    active_steps = sorted({*running_steps, *queued_steps})
    if not active_steps:
        return {
            "running": False,
            "fresh": False,
            "stale": False,
            "running_steps": [],
            "queued_steps": [],
            "active_steps": [],
            "last_checked_at": pipeline.get("last_checked_at"),
            "age_seconds": None,
        }

    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    last_checked = _parse_pipeline_datetime(pipeline.get("last_checked_at"))
    age_seconds = (current - last_checked).total_seconds() if last_checked else None
    stale = last_checked is None or age_seconds > ttl_seconds
    return {
        "running": True,
        "fresh": not stale,
        "stale": stale,
        "running_steps": running_steps,
        "queued_steps": queued_steps,
        "active_steps": active_steps,
        "last_checked_at": pipeline.get("last_checked_at"),
        "age_seconds": age_seconds,
    }


def paper_has_fresh_running_steps(
    paper: Paper,
    *,
    now: Optional[datetime] = None,
    ttl_seconds: int = RUNNING_STEP_TTL_SECONDS,
) -> bool:
    return bool(paper_processing_running_state(paper, now=now, ttl_seconds=ttl_seconds).get("fresh"))


async def clear_stale_paper_processing_steps(
    db: AsyncSession,
    paper: Paper,
    *,
    now: Optional[datetime] = None,
    ttl_seconds: int = RUNNING_STEP_TTL_SECONDS,
) -> bool:
    state = paper_processing_running_state(paper, now=now, ttl_seconds=ttl_seconds)
    if not state.get("stale"):
        return False
    await _store_pipeline_metadata(db, paper, clear_running=True)
    return True


def _has_tags(tags: Any) -> bool:
    if not tags:
        return False
    if isinstance(tags, dict):
        return any(bool(value) for value in tags.values())
    if isinstance(tags, list):
        return len(tags) > 0
    return bool(tags)


def _visual_evidence_needs_extraction(status: dict[str, Any]) -> bool:
    return (
        not status.get("ready")
        or bool(status.get("failed"))
        or int(status.get("missing_ocr_count") or 0) > 0
        or int(status.get("missing_summary_count") or 0) > 0
        or int(status.get("low_confidence_table_count") or 0) > 0
    )


def paper_processing_snapshot(paper: Paper, *, bm25_status: Optional[dict[str, Any]] = None) -> PaperProcessingSnapshot:
    """Return a compact readiness snapshot for one paper."""

    from app.services.document_visual_evidence import visual_evidence_status_from_paper
    from app.services.hybrid_search import bm25_index_status
    from app.services.report_service import structured_pdf_parse_status_from_paper

    metadata = getattr(paper, "metadata_json", None) or {}
    pdf_url = metadata.get("pdf_url") if isinstance(metadata, dict) else None
    can_process_pdf = bool(getattr(paper, "pdf_path", None) or getattr(paper, "arxiv_id", None))
    has_pdf = bool(can_process_pdf or pdf_url)
    can_load_full_text = bool(getattr(paper, "arxiv_id", None))
    has_full_text = bool(getattr(paper, "full_text", None) and len(paper.full_text) > FULL_TEXT_MIN_CHARS)
    has_embedding = getattr(paper, "embedding", None) is not None
    has_tags = _has_tags(getattr(paper, "tags", None))
    structured = structured_pdf_parse_status_from_paper(paper)
    visual = visual_evidence_status_from_paper(paper)
    bm25 = bm25_status if bm25_status is not None else bm25_index_status()
    pipeline = _pipeline_metadata(paper)
    running_steps = set(pipeline.get("running_steps") or [])
    queued_steps = set(pipeline.get("queued_steps") or [])
    active_steps = running_steps | queued_steps
    failed_steps = pipeline.get("failed_steps") if isinstance(pipeline.get("failed_steps"), dict) else {}
    visual_step_error = failed_steps.get("visual_evidence") if isinstance(failed_steps.get("visual_evidence"), dict) else {}
    visual_needs_extraction = _visual_evidence_needs_extraction(visual)
    visual_error_message = (
        ((visual.get("last_error") or {}).get("message") or visual_step_error.get("message"))
        if visual_needs_extraction
        else None
    )
    visual_is_active = "visual_evidence" in active_steps

    labels: list[ProcessingLabel] = [
        ProcessingLabel(
            key="pdf",
            label="PDF",
            state="ready" if has_pdf else "missing",
            ready=has_pdf,
            detail="本地或可恢复 PDF" if has_pdf else "无 PDF 来源",
        ),
        ProcessingLabel(
            key="full_text",
            label="全文",
            state="ready" if has_full_text else ("running" if "full_text" in active_steps else "missing"),
            ready=has_full_text,
            detail=f"{len(paper.full_text or '')} 字符" if has_full_text else ("等待后台提取" if can_load_full_text else "无可自动下载的 PDF"),
            action="load_full_text" if can_load_full_text else None,
        ),
        ProcessingLabel(
            key="structured_parse",
            label="结构化",
            state=(
                "ready"
                if structured.get("ready") and not structured.get("last_error")
                else "failed"
                if structured.get("last_error") and can_process_pdf
                else "running"
                if "structured_parse" in active_steps
                else "missing"
                if can_process_pdf
                else "pending"
            ),
            ready=bool(structured.get("ready") and not structured.get("last_error")),
            detail=(structured.get("last_error") or {}).get("message") or str(structured.get("parser") or ("等待后台解析" if can_process_pdf else "无可自动解析的本地 PDF")),
            count=int(structured.get("block_count") or 0),
            action="structured_parse" if can_process_pdf else None,
        ),
        ProcessingLabel(
            key="visual_evidence",
            label="视觉证据",
            state=(
                "ready"
                if visual.get("ready") and not visual_needs_extraction
                else "running"
                if visual_is_active
                else "failed"
                if (visual.get("failed") or visual_step_error) and can_process_pdf
                else "missing"
                if can_process_pdf
                else "pending"
            ),
            ready=bool(visual.get("ready") and not visual_needs_extraction),
            detail=(
                "后台正在补视觉 OCR"
                if visual_is_active
                else visual_error_message or (f"项目 {int(visual.get('item_count') or 0)}" if can_process_pdf else "无可自动解析的本地 PDF")
            ),
            count=int(visual.get("item_count") or 0),
            action="visual_evidence" if can_process_pdf else None,
        ),
        ProcessingLabel(
            key="embedding",
            label="向量",
            state="ready" if has_embedding else ("running" if "embedding" in active_steps else "missing"),
            ready=has_embedding,
            detail="可语义检索" if has_embedding else "等待后台生成",
            action="embedding",
        ),
        ProcessingLabel(
            key="bm25",
            label="关键词索引",
            state="ready" if bm25.get("ready") else "stale",
            ready=bool(bm25.get("ready")),
            detail=f"已索引 {int(bm25.get('indexed_papers') or 0)} 篇" if bm25.get("ready") else "等待后台刷新",
            count=int(bm25.get("indexed_papers") or 0),
            action="bm25",
        ),
    ]

    failed = [label.key for label in labels if label.state == "failed"]
    missing = [
        label.key
        for label in labels
        if label.key != "pdf" and label.state in {"missing", "stale"} and label.action
    ]
    if failed:
        status: Literal["ready", "processing", "needs_processing", "failed"] = "failed"
    elif any(label.state == "running" for label in labels):
        status = "processing"
    elif missing:
        status = "needs_processing"
    else:
        status = "ready"

    return PaperProcessingSnapshot(
        status=status,
        labels=labels,
        missing=missing,
        failed=failed,
        automation={
            "version": pipeline.get("version") or AUTOMATION_VERSION,
            "last_checked_at": pipeline.get("last_checked_at"),
            "last_completed_at": pipeline.get("last_completed_at"),
            "last_error": pipeline.get("last_error"),
            "queued_steps": list(queued_steps),
            "running_steps": list(running_steps),
            "failed_steps": failed_steps,
        },
    )


def paper_processing_flags(paper: Paper) -> dict[str, Any]:
    """Compatibility flags for existing paper list fields."""

    snapshot = paper_processing_snapshot(paper)
    labels = {label.key: label for label in snapshot.labels}
    return {
        "has_pdf": bool(labels.get("pdf") and labels["pdf"].ready),
        "has_full_text": bool(labels.get("full_text") and labels["full_text"].ready),
        "has_embedding": bool(labels.get("embedding") and labels["embedding"].ready),
        "has_tags": _has_tags(getattr(paper, "tags", None)),
        "missing": list(snapshot.missing),
        "failed": list(snapshot.failed),
        "status": snapshot.status,
        "labels": [label.to_dict() for label in snapshot.labels],
        "automation": snapshot.automation,
    }


async def _store_pipeline_metadata(
    db: AsyncSession,
    paper: Paper,
    *,
    queued_steps: Optional[list[str]] = None,
    running_steps: Optional[list[str]] = None,
    completed_step: Optional[str] = None,
    failed_step: Optional[str] = None,
    error: Optional[str] = None,
    clear_running: bool = False,
) -> None:
    metadata = dict(getattr(paper, "metadata_json", None) or {})
    pipeline = dict(metadata.get(PIPELINE_METADATA_KEY) or {})
    now = datetime.now(timezone.utc).isoformat()
    queued = set(pipeline.get("queued_steps") or [])
    running = set(pipeline.get("running_steps") or [])
    if queued_steps is not None:
        queued.update(queued_steps)
    if running_steps is not None:
        running.update(running_steps)
        queued.difference_update(running_steps)
    if completed_step:
        queued.discard(completed_step)
        running.discard(completed_step)
    if failed_step:
        queued.discard(failed_step)
        running.discard(failed_step)
    if clear_running:
        queued.clear()
        running.clear()

    failed_steps = pipeline.get("failed_steps") if isinstance(pipeline.get("failed_steps"), dict) else {}
    if completed_step:
        failed_steps.pop(completed_step, None)
    if failed_step:
        failed_steps[failed_step] = {"message": (error or "")[:1000], "failed_at": now}

    pipeline.update(
        {
            "version": AUTOMATION_VERSION,
            "last_checked_at": now,
            "queued_steps": sorted(queued),
            "running_steps": sorted(running),
            "failed_steps": failed_steps,
        }
    )
    if completed_step:
        pipeline["last_completed_at"] = now
    if error:
        pipeline["last_error"] = {"message": error[:1000], "failed_at": now, "step": failed_step}
    elif not failed_steps:
        pipeline.pop("last_error", None)
    metadata[PIPELINE_METADATA_KEY] = pipeline
    paper.metadata_json = metadata
    await db.commit()


async def mark_paper_processing_queued(
    db: AsyncSession,
    paper: Paper,
    *,
    steps: Optional[list[str]] = None,
) -> None:
    """Record that backend processing has been submitted for this paper."""

    await _store_pipeline_metadata(
        db,
        paper,
        queued_steps=steps or ["full_text", "structured_parse", "visual_evidence", "embedding", "bm25"],
    )


class PaperProcessingPipeline:
    """Idempotent paper processing orchestrator."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def snapshot(self, paper: Paper) -> PaperProcessingSnapshot:
        return paper_processing_snapshot(paper)

    async def process_paper(
        self,
        paper_id: str | UUID,
        *,
        max_steps: int = 5,
        include_visual: bool = True,
        rebuild_bm25: bool = True,
    ) -> PaperProcessingResult:
        pid = UUID(str(paper_id))
        result = await self.session.execute(select(Paper).where(Paper.id == pid))
        paper = result.scalar_one_or_none()
        if not paper:
            raise ValueError("paper not found")

        output = PaperProcessingResult(paper_id=str(paper.id), title=paper.title)
        output.before = paper_processing_snapshot(paper)
        steps_run = 0

        async def run_step(step: str, fn) -> None:
            nonlocal steps_run
            if steps_run >= max_steps:
                output.skipped.append(step)
                return
            output.attempted.append(step)
            await _store_pipeline_metadata(self.session, paper, running_steps=[step])
            try:
                ok = await fn()
                if ok:
                    output.completed.append(step)
                    await _store_pipeline_metadata(self.session, paper, completed_step=step)
                else:
                    output.skipped.append(step)
                    await _store_pipeline_metadata(self.session, paper, completed_step=step)
            except Exception as exc:
                logger.warning("Paper processing step failed %s %s: %s", paper.id, step, exc)
                output.failed.append({"step": step, "reason": str(exc)})
                await _store_pipeline_metadata(self.session, paper, failed_step=step, error=str(exc))
            finally:
                steps_run += 1
                await self.session.refresh(paper)

        snapshot = paper_processing_snapshot(paper)
        if "full_text" in snapshot.missing:
            async def _full_text() -> bool:
                from app.services.report_service import ensure_full_text

                text = await ensure_full_text(paper)
                if text and len(text) > FULL_TEXT_MIN_CHARS and not paper.full_text:
                    paper.full_text = text
                    await self.session.commit()
                return bool(text and len(text) > FULL_TEXT_MIN_CHARS)

            await run_step("full_text", _full_text)

        snapshot = paper_processing_snapshot(paper)
        if "structured_parse" in snapshot.missing or "structured_parse" in snapshot.failed:
            async def _structured() -> bool:
                from app.services.report_service import force_structured_pdf_reparse

                refreshed = await force_structured_pdf_reparse(paper, self.session)
                await self.session.commit()
                return bool(refreshed.get("ready"))

            await run_step("structured_parse", _structured)

        snapshot = paper_processing_snapshot(paper)
        if include_visual and ("visual_evidence" in snapshot.missing or "visual_evidence" in snapshot.failed):
            async def _visual() -> bool:
                from app.services.document_visual_evidence import (
                    ensure_document_visual_evidence,
                    visual_evidence_status_from_paper,
                )

                await ensure_document_visual_evidence(paper, self.session, force=True)
                await self.session.commit()
                status = visual_evidence_status_from_paper(paper)
                if status.get("ready") and not _visual_evidence_needs_extraction(status):
                    return True
                missing_ocr = int(status.get("missing_ocr_count") or 0)
                missing_summary = int(status.get("missing_summary_count") or 0)
                low_confidence = int(status.get("low_confidence_table_count") or 0)
                last_error = status.get("last_error") if isinstance(status.get("last_error"), dict) else {}
                reason = last_error.get("message") if isinstance(last_error, dict) else None
                if not reason:
                    parts = []
                    if missing_ocr:
                        parts.append(f"{missing_ocr} 个表格缺 OCR")
                    if missing_summary:
                        parts.append(f"{missing_summary} 个图片缺摘要")
                    if low_confidence:
                        parts.append(f"{low_confidence} 个表格置信度低")
                    reason = "、".join(parts) or "视觉证据未达到可回答状态"
                raise RuntimeError(f"视觉证据未完成：{reason}")

            await run_step("visual_evidence", _visual)

        snapshot = paper_processing_snapshot(paper)
        if "embedding" in snapshot.missing:
            async def _embedding() -> bool:
                from app.services.rag_service import RAGService

                return bool(await RAGService(self.session).generate_embeddings_for_paper(paper))

            await run_step("embedding", _embedding)

        snapshot = paper_processing_snapshot(paper)
        if rebuild_bm25 and "bm25" in snapshot.missing:
            async def _bm25() -> bool:
                from app.services.hybrid_search import HybridSearchService

                await HybridSearchService(self.session).rebuild_index()
                return True

            await run_step("bm25", _bm25)

        output.after = paper_processing_snapshot(paper)
        if not output.attempted:
            await _store_pipeline_metadata(self.session, paper)
            output.after = paper_processing_snapshot(paper)
        return output

    async def reconcile_batch(
        self,
        *,
        limit: int = 5,
        candidate_multiplier: int = 6,
        include_visual: bool = True,
        rebuild_bm25: bool = True,
        running_ttl_seconds: int = RUNNING_STEP_TTL_SECONDS,
    ) -> dict[str, Any]:
        result = await self.session.execute(
            select(Paper)
            .order_by(Paper.updated_at.desc())
            .limit(max(limit * candidate_multiplier, limit))
        )
        candidates = result.scalars().all()
        selected: list[Paper] = []
        skipped_running: list[dict[str, Any]] = []
        stale_running_cleared = 0
        now = datetime.now(timezone.utc)
        for paper in candidates:
            running_state = paper_processing_running_state(
                paper,
                now=now,
                ttl_seconds=running_ttl_seconds,
            )
            if running_state.get("fresh"):
                skipped_running.append(
                    {
                        "paper_id": str(paper.id),
                        "title": paper.title,
                        "running_steps": running_state.get("active_steps") or [],
                        "last_checked_at": running_state.get("last_checked_at"),
                    }
                )
                continue
            if running_state.get("stale"):
                if await clear_stale_paper_processing_steps(
                    self.session,
                    paper,
                    now=now,
                    ttl_seconds=running_ttl_seconds,
                ):
                    stale_running_cleared += 1
            snapshot = paper_processing_snapshot(paper)
            if snapshot.status != "ready":
                selected.append(paper)
            if len(selected) >= limit:
                break

        summary: dict[str, Any] = {
            "processed": len(selected),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "skipped_running": len(skipped_running),
            "stale_running_cleared": stale_running_cleared,
            "items": [],
            "errors": [],
        }
        for paper in selected:
            paper_id = str(paper.id)
            paper_title = paper.title
            try:
                processed = await self.process_paper(
                    paper.id,
                    include_visual=include_visual,
                    rebuild_bm25=rebuild_bm25,
                )
                summary["items"].append(processed.to_dict())
                if processed.failed:
                    summary["failed"] += 1
                    summary["errors"].extend(processed.failed)
                elif processed.completed:
                    summary["success"] += 1
                else:
                    summary["skipped"] += 1
            except Exception as exc:
                await self.session.rollback()
                summary["failed"] += 1
                summary["errors"].append({"paper_id": paper_id, "title": paper_title, "reason": str(exc)})
        return summary


async def select_papers_needing_processing(db: AsyncSession, *, limit: int = 20) -> list[Paper]:
    """Return recent papers whose derived processing snapshot is not ready."""

    result = await db.execute(
        select(Paper)
        .where(func.length(func.coalesce(Paper.title, "")) > 0)
        .order_by(Paper.updated_at.desc())
        .limit(limit * 6)
    )
    papers = []
    for paper in result.scalars().all():
        if paper_processing_snapshot(paper).status != "ready":
            papers.append(paper)
        if len(papers) >= limit:
            break
    return papers
