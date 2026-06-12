"""Document visual evidence extraction and normalization utilities.

This module keeps the first implementation intentionally parser-first:
it builds ready evidence from existing structured PDF blocks and optional
parser metadata, and only exposes a bounded vision-adapter interface for
future crop-level OCR. It does not send whole PDFs to a model.
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.paper import Paper

logger = logging.getLogger(__name__)

DOCUMENT_VISUAL_EVIDENCE_KEY = "document_visual_evidence"
DOCUMENT_VISUAL_EVIDENCE_ERROR_KEY = "document_visual_evidence_error"
DOCUMENT_VISUAL_EVIDENCE_VERSION = 1
DEFAULT_LIMITS = {
    "max_pages": 20,
    "max_assets": 40,
    "max_crops": 12,
    "max_model_calls": 0,
    "max_text_chars": 4000,
}
VISUAL_READY_TYPES = {"figure", "chart", "architecture", "image", "page_render", "visual"}
VISUAL_TABLE_TYPES = {"table", "visual_table"}
PARSER_ALIASES = {"docling", "command", "mineru", "paddleocr", "pp_structure", "pdfplumber", "fitz"}


@dataclass
class VisualEvidenceItem:
    """A normalized, page-aware evidence item for document visuals/tables."""

    id: str
    kind: str
    page: Optional[int] = None
    bbox: Optional[list[float]] = None
    caption: Optional[str] = None
    asset_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    parser: str = "structured"
    confidence: float = 0.5
    status: str = "ready"
    text: str = ""
    markdown: str = ""
    summary: str = ""
    key_facts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self, *, max_text_chars: int = 4000) -> dict[str, Any]:
        asset_token = visual_asset_public_token(self.asset_path) if self.asset_path else None
        thumbnail_token = visual_asset_public_token(self.thumbnail_path) if self.thumbnail_path else None
        return {
            "id": self.id,
            "kind": self.kind,
            "page": self.page,
            "bbox": self.bbox,
            "caption": self.caption,
            "asset_path": self.asset_path,
            "thumbnail_path": self.thumbnail_path,
            "asset_token": asset_token,
            "thumbnail_token": thumbnail_token,
            "parser": self.parser,
            "confidence": round(float(self.confidence), 4),
            "status": self.status,
            "text": (self.text or "")[:max_text_chars],
            "markdown": (self.markdown or "")[:max_text_chars],
            "summary": (self.summary or "")[:max_text_chars],
            "key_facts": self.key_facts[:12],
            "metadata": self.metadata,
        }

    @classmethod
    def from_metadata(cls, payload: dict[str, Any]) -> "VisualEvidenceItem":
        return cls(
            id=str(payload.get("id") or ""),
            kind=str(payload.get("kind") or "visual"),
            page=_coerce_positive_int(payload.get("page")),
            bbox=_normalize_bbox(payload.get("bbox")),
            caption=_clean_optional_text(payload.get("caption")),
            asset_path=_clean_optional_text(payload.get("asset_path")),
            thumbnail_path=_clean_optional_text(payload.get("thumbnail_path")),
            parser=str(payload.get("parser") or "metadata"),
            confidence=_coerce_confidence(payload.get("confidence"), default=0.5),
            status=str(payload.get("status") or "ready"),
            text=str(payload.get("text") or ""),
            markdown=str(payload.get("markdown") or ""),
            summary=str(payload.get("summary") or ""),
            key_facts=[str(item) for item in (payload.get("key_facts") or []) if str(item).strip()],
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )


def visual_evidence_limits() -> dict[str, int]:
    """Return configured visual evidence bounds."""

    return {
        "max_pages": max(1, int(getattr(settings, "PDF_VISUAL_EVIDENCE_MAX_PAGES", DEFAULT_LIMITS["max_pages"]) or DEFAULT_LIMITS["max_pages"])),
        "max_assets": max(1, int(getattr(settings, "PDF_VISUAL_EVIDENCE_MAX_ASSETS", DEFAULT_LIMITS["max_assets"]) or DEFAULT_LIMITS["max_assets"])),
        "max_crops": max(0, int(getattr(settings, "PDF_VISUAL_EVIDENCE_MAX_CROPS", DEFAULT_LIMITS["max_crops"]) or DEFAULT_LIMITS["max_crops"])),
        "max_model_calls": max(0, int(getattr(settings, "PDF_VISUAL_EVIDENCE_MAX_MODEL_CALLS", DEFAULT_LIMITS["max_model_calls"]) or DEFAULT_LIMITS["max_model_calls"])),
        "max_text_chars": max(500, int(getattr(settings, "PDF_VISUAL_EVIDENCE_MAX_TEXT_CHARS", DEFAULT_LIMITS["max_text_chars"]) or DEFAULT_LIMITS["max_text_chars"])),
    }


def visual_evidence_asset_root() -> Path:
    root = Path(getattr(settings, "PDF_VISUAL_EVIDENCE_ASSET_DIR", "") or os.path.join(settings.UPLOAD_DIR, "visual-evidence"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def private_visual_asset_path(scope: str, item_id: str, suffix: str = ".png") -> str:
    safe_scope = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(scope or "document")).strip("-") or "document"
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(item_id or "asset")).strip("-") or "asset"
    directory = visual_evidence_asset_root() / safe_scope
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory / f"{safe_id}{suffix}")


def visual_asset_public_token(path: str) -> str:
    """Return a stable non-path token for future authenticated asset routes."""

    return hashlib.sha256(str(path or "").encode("utf-8")).hexdigest()[:24]


def _asset_path_is_private(path: str) -> bool:
    if not path:
        return False
    try:
        root = visual_evidence_asset_root().resolve()
        candidate = Path(path).expanduser().resolve()
        return candidate.is_file() and candidate.is_relative_to(root)
    except OSError:
        return False


def resolve_visual_asset_path_from_paper(paper: Paper, token: str) -> Optional[Path]:
    """Resolve an authenticated paper visual-evidence asset token to a private file."""

    if not re.fullmatch(r"[a-f0-9]{24,64}", token or ""):
        return None
    payload = document_visual_evidence_from_paper(paper)
    for item in visual_evidence_items_from_payload(payload):
        for path in (item.thumbnail_path, item.asset_path):
            if path and visual_asset_public_token(path) == token and _asset_path_is_private(path):
                return Path(path).resolve()
    return None


def document_visual_evidence_from_paper(paper: Paper) -> Optional[dict[str, Any]]:
    metadata = getattr(paper, "metadata_json", None) or {}
    payload = metadata.get(DOCUMENT_VISUAL_EVIDENCE_KEY)
    if not isinstance(payload, dict):
        return None
    if payload.get("version") != DOCUMENT_VISUAL_EVIDENCE_VERSION:
        return None
    pdf_path = getattr(paper, "pdf_path", None)
    source_path = payload.get("source_path")
    if pdf_path and source_path and source_path != pdf_path:
        return None
    return payload


def visual_evidence_items_from_payload(payload: Optional[dict[str, Any]]) -> list[VisualEvidenceItem]:
    if not isinstance(payload, dict):
        return []
    items = payload.get("items") or payload.get("assets") or []
    if not isinstance(items, list):
        return []
    normalized = []
    for item in items:
        if isinstance(item, dict):
            evidence = VisualEvidenceItem.from_metadata(item)
            if evidence.id and evidence.status == "ready":
                normalized.append(evidence)
    return normalized


def ready_visual_evidence_items_from_paper(paper: Paper) -> list[VisualEvidenceItem]:
    return visual_evidence_items_from_payload(document_visual_evidence_from_paper(paper))


def visual_evidence_status_from_paper(paper: Paper) -> dict[str, Any]:
    metadata = getattr(paper, "metadata_json", None) or {}
    payload = document_visual_evidence_from_paper(paper)
    error = metadata.get(DOCUMENT_VISUAL_EVIDENCE_ERROR_KEY)
    if not payload:
        return {
            "ready": False,
            "status": "missing",
            "parser": None,
            "source_path": getattr(paper, "pdf_path", None),
            "parsed_at": None,
            "item_count": 0,
            "visual_count": 0,
            "table_count": 0,
            "ocr_count": 0,
            "summary_count": 0,
            "failed": bool(error),
            "last_error": error if isinstance(error, dict) else None,
            "limits": visual_evidence_limits(),
            "parser_health": visual_evidence_runtime_health(),
        }

    items = visual_evidence_items_from_payload(payload)
    visual_count = sum(1 for item in items if item.kind in VISUAL_READY_TYPES or item.kind not in VISUAL_TABLE_TYPES)
    table_count = sum(1 for item in items if item.kind in VISUAL_TABLE_TYPES)
    ocr_count = sum(1 for item in items if item.text or item.markdown)
    summary_count = sum(1 for item in items if item.summary)
    asset_count = sum(1 for item in items if item.asset_path or item.thumbnail_path)
    missing_summary_count = sum(1 for item in items if item.kind not in VISUAL_TABLE_TYPES and not (item.summary or item.text))
    missing_ocr_count = sum(1 for item in items if item.kind in VISUAL_TABLE_TYPES and not item.markdown)
    low_confidence_table_count = sum(1 for item in items if item.kind in VISUAL_TABLE_TYPES and item.confidence < 0.6)
    status = str(payload.get("status") or ("ready" if items else "empty"))
    return {
        "ready": bool(items) and status == "ready",
        "status": status,
        "parser": payload.get("parser"),
        "source_path": payload.get("source_path"),
        "parsed_at": payload.get("parsed_at"),
        "page_count": payload.get("page_count") or 0,
        "item_count": len(items),
        "visual_count": visual_count,
        "table_count": table_count,
        "ocr_count": ocr_count,
        "summary_count": summary_count,
        "asset_count": asset_count,
        "missing_summary_count": missing_summary_count,
        "missing_ocr_count": missing_ocr_count,
        "low_confidence_table_count": low_confidence_table_count,
        "failed": status == "failed" or bool(error),
        "last_error": payload.get("last_error") or (error if isinstance(error, dict) else None),
        "limits": payload.get("limits") if isinstance(payload.get("limits"), dict) else visual_evidence_limits(),
        "parser_health": visual_evidence_runtime_health(),
    }


def visual_evidence_runtime_health() -> dict[str, Any]:
    import importlib.util

    return {
        "enabled": bool(getattr(settings, "PDF_VISUAL_EVIDENCE_ENABLED", True)),
        "asset_dir": str(visual_evidence_asset_root()),
        "available": {
            "fitz": importlib.util.find_spec("fitz") is not None,
            "docling": importlib.util.find_spec("docling") is not None,
            "command": bool(str(getattr(settings, "PDF_STRUCTURED_PARSER_COMMAND", "") or "").strip()),
            "vision_model": bool(getattr(settings, "PDF_VISUAL_EVIDENCE_ENABLE_VISION", False)),
        },
        "limits": visual_evidence_limits(),
    }


def visual_evidence_blocks_from_paper(paper: Paper) -> list[dict[str, Any]]:
    return [visual_evidence_item_to_block(item) for item in ready_visual_evidence_items_from_paper(paper)]


def visual_evidence_item_to_block(item: VisualEvidenceItem) -> dict[str, Any]:
    text = visual_evidence_text(item)
    asset_path = visual_asset_route_for_item(item, item.asset_path)
    thumbnail_path = visual_asset_route_for_item(item, item.thumbnail_path)
    return {
        "type": "visual_table" if item.kind in VISUAL_TABLE_TYPES else "visual_evidence",
        "page": item.page,
        "source": item.parser or "document_visual_evidence",
        "text": text,
        "metadata": {
            **(item.metadata or {}),
            "asset_id": item.id,
            "kind": item.kind,
            "caption": item.caption,
            "bbox": item.bbox,
            "asset_token": visual_asset_public_token(item.asset_path) if item.asset_path else None,
            "thumbnail_token": visual_asset_public_token(item.thumbnail_path) if item.thumbnail_path else None,
            "asset_path": asset_path,
            "thumbnail_path": thumbnail_path,
            "confidence": item.confidence,
            "visual_evidence": True,
            "summary": item.summary,
            "key_facts": item.key_facts,
        },
    }


def visual_evidence_text(item: VisualEvidenceItem) -> str:
    label = "PDF visual table evidence" if item.kind in VISUAL_TABLE_TYPES else "PDF visual evidence"
    lines = [f"[{label}, page {item.page or 'unknown'}, kind {item.kind}, asset {item.id}]"]
    if item.caption:
        lines.append(f"Caption: {item.caption}")
    if item.markdown:
        lines.append(item.markdown)
    elif item.text:
        lines.append(item.text)
    if item.summary:
        lines.append(f"Visual summary: {item.summary}")
    if item.key_facts:
        lines.append("Key facts: " + "; ".join(item.key_facts[:8]))
    if item.asset_path:
        lines.append(f"Asset token: {visual_asset_public_token(item.asset_path)}")
    return "\n".join(line for line in lines if line).strip()


def visual_asset_route_for_item(item: VisualEvidenceItem, path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    scope = str((item.metadata or {}).get("document_scope") or "")
    if not re.fullmatch(r"[0-9a-fA-F-]{32,36}", scope):
        return None
    return f"/api/papers/visual-evidence-assets/{scope}/{visual_asset_public_token(path)}"


def visual_evidence_payload_from_items(
    *,
    source_path: str,
    parser: str,
    page_count: int,
    items: list[VisualEvidenceItem],
    status: str = "ready",
    last_error: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    limits = visual_evidence_limits()
    bounded = items[:limits["max_assets"]]
    return {
        "version": DOCUMENT_VISUAL_EVIDENCE_VERSION,
        "source_path": source_path,
        "parser": parser,
        "status": status,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "page_count": page_count,
        "limits": limits,
        "item_count": len(bounded),
        "items": [item.to_metadata(max_text_chars=limits["max_text_chars"]) for item in bounded],
        "last_error": last_error,
    }


def render_visual_evidence_assets(pdf_path: str, items: list[VisualEvidenceItem], scope: str) -> list[VisualEvidenceItem]:
    """Generate bounded private page/crop assets for parser-located regions when PyMuPDF is available."""

    if not pdf_path or not items:
        return items
    limits = visual_evidence_limits()
    try:
        import fitz
    except Exception as exc:
        for item in items:
            item.metadata = {**(item.metadata or {}), "asset_status": "unavailable", "asset_error": f"fitz unavailable: {exc}"[:300]}
        return items

    crop_budget = limits["max_crops"]
    page_cache: dict[int, str] = {}
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        for item in items:
            item.metadata = {**(item.metadata or {}), "asset_status": "failed", "asset_error": str(exc)[:300]}
        return items

    try:
        for item in items:
            page_number = _coerce_positive_int(item.page)
            if not page_number or page_number > limits["max_pages"] or page_number > doc.page_count:
                continue
            page_asset = page_cache.get(page_number)
            if not page_asset:
                page = doc.load_page(page_number - 1)
                page_asset = private_visual_asset_path(scope, f"page-{page_number}")
                if not Path(page_asset).exists():
                    matrix = fitz.Matrix(1.5, 1.5)
                    page.get_pixmap(matrix=matrix, alpha=False).save(page_asset)
                page_cache[page_number] = page_asset

            item.metadata = {**(item.metadata or {}), "page_asset_path": page_asset, "page_asset_token": visual_asset_public_token(page_asset)}
            if not item.asset_path:
                item.asset_path = page_asset
                item.metadata["crop_strategy"] = item.metadata.get("crop_strategy") or "page-fallback"

            if crop_budget <= 0 or not item.bbox:
                continue

            page = doc.load_page(page_number - 1)
            clip = _fitz_clip_from_bbox(page.rect, item.bbox)
            if not clip:
                item.metadata = {**(item.metadata or {}), "crop_status": "fallback", "crop_error": "invalid bbox"}
                continue
            crop_asset = private_visual_asset_path(scope, item.id)
            if not Path(crop_asset).exists():
                matrix = fitz.Matrix(2.0, 2.0)
                page.get_pixmap(matrix=matrix, clip=clip, alpha=False).save(crop_asset)
            item.asset_path = crop_asset
            item.thumbnail_path = crop_asset
            item.metadata = {
                **(item.metadata or {}),
                "crop_status": "ready",
                "crop_strategy": "parser-region",
                "fallback_asset_path": page_asset,
                "fallback_asset_token": visual_asset_public_token(page_asset),
            }
            crop_budget -= 1
        return items
    finally:
        doc.close()


def _fitz_clip_from_bbox(page_rect: Any, bbox: list[float]) -> Any:
    """Convert parser bbox into a safe PyMuPDF Rect, accepting normalized or point coordinates."""

    if not bbox or len(bbox) != 4:
        return None
    try:
        import fitz

        x0, y0, x1, y1 = [float(value) for value in bbox]
        if max(abs(x0), abs(y0), abs(x1), abs(y1)) <= 1.5:
            x0, x1 = x0 * float(page_rect.width), x1 * float(page_rect.width)
            y0, y1 = y0 * float(page_rect.height), y1 * float(page_rect.height)
        rect = fitz.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        rect = rect & page_rect
        if rect.is_empty or rect.width < 2 or rect.height < 2:
            return None
        return rect
    except Exception:
        return None


async def _persist_visual_evidence_metadata(
    paper: Paper,
    payload: dict[str, Any],
    db: Optional[AsyncSession] = None,
) -> None:
    metadata = dict(getattr(paper, "metadata_json", None) or {})
    metadata[DOCUMENT_VISUAL_EVIDENCE_KEY] = payload
    if payload.get("status") != "failed":
        metadata.pop(DOCUMENT_VISUAL_EVIDENCE_ERROR_KEY, None)
    elif payload.get("last_error"):
        metadata[DOCUMENT_VISUAL_EVIDENCE_ERROR_KEY] = payload["last_error"]
    paper.metadata_json = metadata
    if db is not None:
        await db.execute(update(Paper).where(Paper.id == paper.id).values(metadata_json=metadata))
        return

    try:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await session.execute(update(Paper).where(Paper.id == paper.id).values(metadata_json=metadata))
            await session.commit()
    except Exception as exc:
        logger.warning("Document visual evidence metadata persistence failed %s: %s", getattr(paper, "id", ""), exc)


async def ensure_document_visual_evidence(
    paper: Paper,
    db: Optional[AsyncSession] = None,
    *,
    force: bool = False,
) -> Optional[dict[str, Any]]:
    """Return ready cached visual evidence, or build it from parser output."""

    cached = document_visual_evidence_from_paper(paper)
    if cached and not force and cached.get("status") == "ready":
        return cached

    try:
        from app.services.report_service import (
            ensure_structured_pdf_content,
            resolve_paper_pdf_path,
            structured_pdf_metadata_from_paper,
        )

        pdf_path = await resolve_paper_pdf_path(paper, db)
        if not pdf_path:
            raise ValueError("PDF 不可用：当前论文没有本地 PDF 路径，也没有可恢复的 arXiv PDF")
        structured = structured_pdf_metadata_from_paper(paper)
        if force or not structured:
            structured = await ensure_structured_pdf_content(paper)
        if not structured:
            raise RuntimeError("PDF 结构化解析未返回可用内容")
        scope = str(getattr(paper, "id", "") or "paper")
        items = await asyncio.to_thread(visual_evidence_items_from_structured_extraction, structured, scope)
        items = await asyncio.to_thread(render_visual_evidence_assets, pdf_path, items, scope)
        items = await enrich_visual_evidence_items_with_vision(items)
        status = "ready" if items else "empty"
        payload = visual_evidence_payload_from_items(
            source_path=pdf_path,
            parser=structured.parser,
            page_count=structured.page_count,
            items=items,
            status=status,
        )
        await _persist_visual_evidence_metadata(paper, payload, db)
        return payload
    except Exception as exc:
        logger.warning("Document visual evidence extraction failed %s: %s", getattr(paper, "id", ""), exc)
        payload = visual_evidence_payload_from_items(
            source_path=str(getattr(paper, "pdf_path", "") or ""),
            parser=str(getattr(settings, "PDF_STRUCTURED_PARSER_BACKEND", "auto")),
            page_count=0,
            items=[],
            status="failed",
            last_error={
                "message": str(exc)[:1000],
                "failed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        await _persist_visual_evidence_metadata(paper, payload, db)
        return payload


async def force_document_visual_evidence_reparse(
    paper: Paper,
    db: Optional[AsyncSession] = None,
) -> dict[str, Any]:
    payload = await ensure_document_visual_evidence(paper, db, force=True)
    return visual_evidence_status_from_paper(paper) if payload else visual_evidence_status_from_paper(paper)


def visual_evidence_items_from_structured_extraction(extraction: Any, scope: str = "paper") -> list[VisualEvidenceItem]:
    """Create visual evidence items from existing structured PDF extraction."""

    limits = visual_evidence_limits()
    items: list[VisualEvidenceItem] = []
    captions_by_page: dict[int, list[Any]] = {}
    blocks = list(getattr(extraction, "blocks", []) or [])
    for block in blocks:
        if getattr(block, "block_type", None) == "caption" and isinstance(getattr(block, "page", None), int):
            captions_by_page.setdefault(block.page, []).append(block)

    for index, block in enumerate(blocks, 1):
        page = _coerce_positive_int(getattr(block, "page", None))
        if page and page > limits["max_pages"]:
            continue
        metadata = getattr(block, "metadata", None) or {}
        block_type = str(getattr(block, "block_type", "") or "structured")
        parser = str(getattr(block, "source", None) or getattr(extraction, "parser", None) or "structured")
        text = str(getattr(block, "text", "") or "").strip()
        if not text:
            continue
        kind = _kind_from_block(block_type, text, metadata)
        if not _is_visual_or_table_kind(kind, block_type, metadata):
            continue
        caption = _caption_for_block(block, captions_by_page)
        item_id = _evidence_id(scope, page, kind, index, text)
        bbox = _normalize_bbox(metadata.get("bbox") or metadata.get("box"))
        asset_path = metadata.get("asset_path") or metadata.get("image_path")
        markdown = text if kind in VISUAL_TABLE_TYPES and "|" in text else ""
        item_text = text if kind not in VISUAL_TABLE_TYPES else ""
        summary = _summary_from_block(kind, text, caption)
        items.append(VisualEvidenceItem(
            id=item_id,
            kind=kind,
            page=page,
            bbox=bbox,
            caption=caption,
            asset_path=str(asset_path) if asset_path else None,
            thumbnail_path=str(metadata.get("thumbnail_path")) if metadata.get("thumbnail_path") else None,
            parser=parser,
            confidence=_confidence_for_block(block_type, parser, metadata),
            text=item_text,
            markdown=markdown,
            summary=summary,
            key_facts=_key_facts_from_text(text),
            metadata={
                **metadata,
                "document_scope": scope,
                "structured_block_type": block_type,
                "source_parser": parser,
                "crop_strategy": "parser-region" if bbox else "page-caption-fallback",
            },
        ))
        if len(items) >= limits["max_assets"]:
            break
    return items


async def extract_visual_evidence_from_pdf_bytes(
    file_bytes: bytes,
    filename: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Parse an uploaded PDF into attachment-scoped visual evidence."""

    import tempfile
    from app.services.report_service import extract_pdf_structured_content

    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        extraction = await asyncio.to_thread(extract_pdf_structured_content, tmp_path)
        scope = f"upload-{hashlib.sha256((filename + str(len(file_bytes))).encode('utf-8')).hexdigest()[:12]}"
        items = visual_evidence_items_from_structured_extraction(extraction, scope)
        items = render_visual_evidence_assets(tmp_path, items, scope)
        items = await enrich_visual_evidence_items_with_vision(items)
        payload = visual_evidence_payload_from_items(
            source_path=filename,
            parser=extraction.parser,
            page_count=extraction.page_count,
            items=items,
            status="ready" if items else "empty",
        )
        blocks = [visual_evidence_item_to_block(item) for item in items]
        return payload, blocks
    except Exception as exc:
        payload = visual_evidence_payload_from_items(
            source_path=filename,
            parser=str(getattr(settings, "PDF_STRUCTURED_PARSER_BACKEND", "auto")),
            page_count=0,
            items=[],
            status="failed",
            last_error={"message": str(exc)[:1000], "failed_at": datetime.now(timezone.utc).isoformat()},
        )
        return payload, []
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def format_visual_evidence_context(blocks: list[dict[str, Any]], *, limit: int = 8) -> str:
    lines = []
    for index, block in enumerate(blocks[:limit], 1):
        metadata = block.get("metadata") if isinstance(block.get("metadata"), dict) else {}
        page = block.get("page")
        kind = metadata.get("kind") or block.get("type")
        caption = metadata.get("caption")
        confidence = metadata.get("confidence")
        lines.append(
            f"### [V{index}] {kind} page {page or 'unknown'} confidence {confidence if confidence is not None else 'unknown'}"
        )
        if caption:
            lines.append(f"Caption: {caption}")
        lines.append(str(block.get("text") or "")[:visual_evidence_limits()["max_text_chars"]])
    return "\n".join(lines).strip()


async def analyze_visual_crop_with_model(image_path: str, prompt: str = "") -> dict[str, Any]:
    """Analyze one bounded crop with the configured OpenAI-compatible vision provider."""

    if not bool(getattr(settings, "PDF_VISUAL_EVIDENCE_ENABLE_VISION", False)):
        return {
            "status": "unavailable",
            "reason": "vision model adapter is disabled",
            "summary": "",
            "confidence": 0.0,
            "key_facts": [],
        }
    if not _asset_path_is_private(image_path):
        return {"status": "failed", "reason": "crop asset is not in the private visual evidence directory", "confidence": 0.0}
    data_url = data_url_from_asset(image_path)
    if not data_url:
        return {"status": "failed", "reason": "crop asset is unreadable", "confidence": 0.0}

    from app.services.llm import OPENAI_COMPATIBLE_PROVIDER, llm_service

    active = llm_service.get_active_option()
    if active.get("provider") != OPENAI_COMPATIBLE_PROVIDER:
        return {"status": "unavailable", "reason": "active LLM provider does not support image input", "confidence": 0.0}

    instruction = prompt or (
        "Return strict JSON only with keys: status, kind, ocr_text, markdown, summary, key_facts, confidence. "
        "Use markdown only for tables. Do not invent numbers that are not visible."
    )
    raw = await llm_service.chat(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        temperature=0.0,
        max_tokens=1200,
    )
    return normalize_vision_adapter_result(parse_vision_json(raw), provider=active.get("provider"), model=active.get("model"))


async def enrich_visual_evidence_items_with_vision(items: list[VisualEvidenceItem]) -> list[VisualEvidenceItem]:
    """Run bounded crop/page OCR for selected visual evidence items when configured."""

    if not items:
        return items
    limits = visual_evidence_limits()
    budget = limits["max_model_calls"]
    if budget <= 0:
        return [_mark_vision_skipped(item, "max_model_calls is 0") for item in items]
    if not bool(getattr(settings, "PDF_VISUAL_EVIDENCE_ENABLE_VISION", False)):
        return [_mark_vision_skipped(item, "vision model adapter is disabled") for item in items]

    enriched: list[VisualEvidenceItem] = []
    calls_used = 0
    for item in items:
        candidate_path = item.thumbnail_path or item.asset_path
        if calls_used >= budget or not candidate_path or not _should_vision_analyze_item(item):
            enriched.append(item)
            continue
        result = await analyze_visual_crop_with_model(candidate_path, _vision_prompt_for_item(item))
        calls_used += 1
        enriched.append(_apply_vision_result_to_item(item, result))
    for item in enriched:
        item.metadata = {**(item.metadata or {}), "vision_model_calls_used": calls_used, "vision_model_call_limit": budget}
    return enriched


def _mark_vision_skipped(item: VisualEvidenceItem, reason: str) -> VisualEvidenceItem:
    if not _should_vision_analyze_item(item):
        return item
    item.metadata = {
        **(item.metadata or {}),
        "vision_ocr_status": "skipped",
        "vision_ocr_reason": reason,
    }
    return item


def _should_vision_analyze_item(item: VisualEvidenceItem) -> bool:
    if not item.asset_path and not item.thumbnail_path:
        return False
    if item.kind in VISUAL_TABLE_TYPES:
        return True
    if item.kind in VISUAL_READY_TYPES or item.kind in {"figure", "chart", "architecture", "image"}:
        return not (item.summary and item.text)
    return False


def _vision_prompt_for_item(item: VisualEvidenceItem) -> str:
    caption = item.caption or ""
    if item.kind in VISUAL_TABLE_TYPES:
        return (
            "You are reading a cropped PDF table or the page containing a table. "
            "Return strict JSON only with keys: status, kind, ocr_text, markdown, summary, key_facts, confidence. "
            "Set kind to table. Put the extracted table in GitHub-flavored markdown. "
            "Preserve row/column labels and numeric values exactly as visible. "
            "If the image does not contain a readable table, set status to empty or failed. "
            "Do not invent missing values. "
            f"Known caption/context: {caption}"
        )
    return (
        "You are reading a cropped PDF figure/chart/diagram. "
        "Return strict JSON only with keys: status, kind, ocr_text, markdown, summary, key_facts, confidence. "
        "Use markdown only if the image contains a table; otherwise leave markdown empty. "
        "Summarize only visible content and OCR visible labels. Do not infer hidden details. "
        f"Known caption/context: {caption}"
    )


def _apply_vision_result_to_item(item: VisualEvidenceItem, result: dict[str, Any]) -> VisualEvidenceItem:
    status = str(result.get("status") or "").lower()
    metadata = {
        **(item.metadata or {}),
        "vision_ocr_status": status or "unknown",
        "vision_provider": result.get("provider"),
        "vision_model": result.get("model"),
    }
    if status != "ready":
        reason = result.get("reason") or result.get("raw_status")
        if reason:
            metadata["vision_ocr_reason"] = str(reason)[:500]
        item.metadata = metadata
        return item

    markdown = str(result.get("markdown") or "").strip()
    ocr_text = str(result.get("ocr_text") or "").strip()
    summary = str(result.get("summary") or "").strip()
    key_facts = result.get("key_facts") if isinstance(result.get("key_facts"), list) else []
    confidence = _coerce_confidence(result.get("confidence"), default=item.confidence)

    if markdown:
        item.markdown = markdown
    if ocr_text:
        item.text = ocr_text
    if summary:
        item.summary = summary
    if key_facts:
        item.key_facts = [str(fact).strip() for fact in key_facts if str(fact).strip()][:12]
    item.confidence = max(item.confidence, confidence)
    item.metadata = metadata
    return item


def normalize_vision_adapter_result(payload: dict[str, Any], *, provider: Optional[str] = None, model: Optional[str] = None) -> dict[str, Any]:
    """Normalize model JSON into the visual evidence adapter contract."""

    if not isinstance(payload, dict):
        return {"status": "invalid", "confidence": 0.0}
    status = str(payload.get("status") or "ready").strip().lower()
    if status not in {"ready", "unavailable", "failed", "invalid", "empty"}:
        status = "ready"
    key_facts = payload.get("key_facts") or payload.get("facts") or []
    if isinstance(key_facts, str):
        key_facts = [item.strip() for item in re.split(r"[;\n]", key_facts) if item.strip()]
    if not isinstance(key_facts, list):
        key_facts = []
    return {
        "status": status,
        "kind": _normalize_kind(str(payload.get("kind") or payload.get("type") or "visual")),
        "ocr_text": str(payload.get("ocr_text") or payload.get("text") or "")[: visual_evidence_limits()["max_text_chars"]],
        "markdown": str(payload.get("markdown") or payload.get("table_markdown") or "")[: visual_evidence_limits()["max_text_chars"]],
        "summary": str(payload.get("summary") or payload.get("visual_summary") or "")[:1000],
        "key_facts": [str(item).strip() for item in key_facts if str(item).strip()][:12],
        "confidence": _coerce_confidence(payload.get("confidence"), default=0.5),
        "provider": provider,
        "model": model,
        "raw_status": payload.get("status"),
    }


def _coerce_positive_int(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float) and value.is_integer():
        return int(value) if value > 0 else None
    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        return parsed if parsed > 0 else None
    return None


def _coerce_confidence(value: Any, *, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(0.0, min(1.0, parsed))


def _normalize_bbox(value: Any) -> Optional[list[float]]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        return [round(float(item), 3) for item in value]
    except (TypeError, ValueError):
        return None


def _clean_optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def _kind_from_block(block_type: str, text: str, metadata: dict[str, Any]) -> str:
    explicit = str(metadata.get("kind") or metadata.get("category") or "").strip().lower()
    if explicit:
        return _normalize_kind(explicit)
    caption_type = str(metadata.get("caption_type") or "").lower()
    lowered = (text or "").lower()
    if block_type == "table":
        return "table"
    if block_type in {"ocr", "formula"}:
        return block_type
    if block_type in {"visual", "image", "picture"}:
        return "image"
    if caption_type == "table_caption" or re.search(r"\btable\s*\.?\s*\d+|表\s*\d+", lowered):
        return "table"
    if caption_type == "figure_caption" or re.search(r"\bfig(?:ure)?\s*\.?\s*\d+|图\s*\d+", lowered):
        if re.search(r"architecture|framework|pipeline|method|模型|架构|方法|流程", lowered):
            return "architecture"
        if re.search(r"chart|plot|curve|graph|柱状|曲线|图表", lowered):
            return "chart"
        return "figure"
    return _normalize_kind(block_type)


def _normalize_kind(kind: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", kind.lower()).strip("_")
    aliases = {
        "picture": "image",
        "fig": "figure",
        "table_caption": "table",
        "figure_caption": "figure",
        "visual": "image",
        "equation": "formula",
    }
    return aliases.get(normalized, normalized or "visual")


def _is_visual_or_table_kind(kind: str, block_type: str, metadata: dict[str, Any]) -> bool:
    if kind in VISUAL_READY_TYPES or kind in VISUAL_TABLE_TYPES or kind in {"ocr", "formula", "caption", "figure"}:
        return True
    if metadata.get("visual_evidence"):
        return True
    return block_type in {"visual", "table", "ocr", "formula", "caption"}


def _caption_for_block(block: Any, captions_by_page: dict[int, list[Any]]) -> Optional[str]:
    metadata = getattr(block, "metadata", None) or {}
    caption = _clean_optional_text(metadata.get("caption"))
    if caption:
        return caption
    text = str(getattr(block, "text", "") or "")
    if getattr(block, "block_type", None) == "caption":
        return re.sub(r"^\[PDF caption[^\]]*\]\s*", "", text).strip()[:500]
    page = _coerce_positive_int(getattr(block, "page", None))
    for caption_block in captions_by_page.get(page or -1, []):
        ctext = str(getattr(caption_block, "text", "") or "")
        if not ctext:
            continue
        return re.sub(r"^\[PDF caption[^\]]*\]\s*", "", ctext).strip()[:500]
    return None


def _summary_from_block(kind: str, text: str, caption: Optional[str]) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned)
    if caption and kind not in VISUAL_TABLE_TYPES:
        return caption[:500]
    if kind in VISUAL_TABLE_TYPES:
        return (caption or "Parsed table evidence")[:500]
    return cleaned[:500]


def _key_facts_from_text(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    facts: list[str] = []
    for pattern in (r"\b\d+(?:\.\d+)?%?\b", r"\b[A-Z][A-Za-z0-9_.-]{2,}\b"):
        for match in re.findall(pattern, cleaned):
            if match not in facts:
                facts.append(match)
            if len(facts) >= 8:
                return facts
    return facts


def _confidence_for_block(block_type: str, parser: str, metadata: dict[str, Any]) -> float:
    if metadata.get("confidence") is not None:
        return _coerce_confidence(metadata.get("confidence"), default=0.65)
    parser_lower = (parser or "").lower()
    if block_type == "table":
        quality = str(metadata.get("quality") or "").lower()
        if quality == "high":
            return 0.86
        if quality == "low":
            return 0.48
        return 0.72 if parser_lower in PARSER_ALIASES else 0.62
    if block_type == "caption":
        return 0.68
    if block_type in {"visual", "ocr"}:
        return 0.55
    return 0.5


def _evidence_id(scope: str, page: Optional[int], kind: str, index: int, text: str) -> str:
    digest = hashlib.sha1(f"{scope}:{page}:{kind}:{index}:{text[:120]}".encode("utf-8")).hexdigest()[:10]
    return f"ve-{digest}"


def data_url_from_asset(path: str) -> Optional[str]:
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return None
    suffix = Path(path).suffix.lower()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64,{base64.b64encode(raw).decode('utf-8')}"


def parse_vision_json(text: str) -> dict[str, Any]:
    """Parse strict vision JSON with a conservative fenced-block fallback."""

    raw = (text or "").strip()
    if not raw:
        return {"status": "empty", "confidence": 0.0}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"status": "invalid", "raw": raw[:1000], "confidence": 0.0}
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
        if match:
            try:
                parsed = json.loads(match.group(1))
                return parsed if isinstance(parsed, dict) else {"status": "invalid", "raw": raw[:1000], "confidence": 0.0}
            except json.JSONDecodeError:
                pass
    return {"status": "invalid", "raw": raw[:1000], "confidence": 0.0}
