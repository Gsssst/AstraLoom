"""Shared maintenance job execution helpers."""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.paper import Paper
from app.services import report_service

TABLE_REPAIR_JOB_KIND = "repair-low-quality-tables"
ProgressCallback = Callable[[dict[str, Any]], None]


def paper_sample_payload(paper: Paper) -> dict[str, Any]:
    return {
        "id": str(paper.id),
        "title": paper.title,
        "year": getattr(paper, "year", None),
        "source": getattr(paper, "source", None),
        "arxiv_id": getattr(paper, "arxiv_id", None),
    }


def table_repair_progress_payload(
    *,
    status: str,
    total: int,
    processed: int,
    success: int,
    failed: int,
    skipped: int,
    errors: list[dict[str, Any]] | None = None,
    current_paper: dict[str, Any] | None = None,
    message: str = "",
) -> dict[str, Any]:
    progress_percent = int(round((processed / total) * 100)) if total else 0
    return {
        "kind": TABLE_REPAIR_JOB_KIND,
        "status": status,
        "total": total,
        "processed": processed,
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "errors": errors or [],
        "current_paper": current_paper,
        "message": message,
        "progress_percent": progress_percent,
    }


async def select_low_quality_table_repair_candidates(
    db: AsyncSession,
    *,
    limit: int,
) -> list[Paper]:
    result = await db.execute(
        select(Paper)
        .where((Paper.pdf_path.is_not(None)) | (Paper.arxiv_id.is_not(None)))
        .order_by(Paper.created_at.desc())
        .limit(limit * 8)
    )
    candidates = result.scalars().all()
    papers: list[Paper] = []
    for candidate in candidates:
        status = report_service.structured_pdf_parse_status_from_paper(candidate)
        table_quality = status.get("table_quality") or {}
        table_repair = status.get("table_repair") or {}
        if (
            status.get("ready")
            and int(table_quality.get("low_quality_table_count") or 0) > 0
            and not table_repair.get("has_repaired_tables")
        ):
            papers.append(candidate)
        if len(papers) >= limit:
            break
    return papers


async def run_low_quality_table_repair(
    db: AsyncSession,
    *,
    limit: int,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    papers = await select_low_quality_table_repair_candidates(db, limit=limit)
    total = len(papers)
    processed = 0
    success = 0
    failed = 0
    skipped = 0
    errors: list[dict[str, Any]] = []

    def emit(status: str, *, current_paper: dict[str, Any] | None = None, message: str = "") -> None:
        if progress:
            progress(table_repair_progress_payload(
                status=status,
                total=total,
                processed=processed,
                success=success,
                failed=failed,
                skipped=skipped,
                errors=errors,
                current_paper=current_paper,
                message=message,
            ))

    emit("running", message="已筛选待修复表格论文")
    for paper in papers:
        current = paper_sample_payload(paper)
        emit("running", current_paper=current, message=f"正在修复：{paper.title}")
        try:
            refreshed = await report_service.force_table_repair(paper, db)
            repair_status = refreshed.get("table_repair") or {}
            if repair_status.get("has_repaired_tables"):
                success += 1
            else:
                skipped += 1
                errors.append({
                    "paper_id": str(paper.id),
                    "title": paper.title,
                    "reason": "no repaired table blocks",
                })
        except Exception as exc:
            failed += 1
            errors.append({"paper_id": str(paper.id), "title": paper.title, "reason": str(exc)})
        processed += 1
        emit("running", current_paper=current, message=f"已处理：{paper.title}")

    if success or failed:
        await db.commit()

    result = {
        "processed": total,
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }
    final_payload = table_repair_progress_payload(
        status="success",
        total=total,
        processed=processed,
        success=success,
        failed=failed,
        skipped=skipped,
        errors=errors,
        current_paper=None,
        message="表格修复任务完成",
    )
    final_payload["result"] = result
    return final_payload
