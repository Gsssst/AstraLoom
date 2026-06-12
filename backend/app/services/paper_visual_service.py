"""PDF visual asset extraction and evidence helpers.

This module intentionally starts with bounded page-level visual assets. It gives
paper Q&A a reliable multimodal evidence surface today, while leaving room for
future figure/table bbox detectors or ColPali-style page retrieval.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.paper import Paper

logger = logging.getLogger(__name__)

PDF_VISUAL_ASSETS_METADATA_KEY = "pdf_visual_assets_v1"
PDF_VISUAL_ASSETS_VERSION = 2


@dataclass
class PaperVisualAsset:
    """A page-aware visual asset extracted from a paper PDF."""

    asset_id: str
    paper_id: str
    page: int
    kind: str = "page"
    image_path: str = ""
    thumbnail_path: Optional[str] = None
    bbox: Optional[list[float]] = None
    caption: Optional[str] = None
    source: str = "fitz"
    summary: Optional[str] = None
    key_facts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "paper_id": self.paper_id,
            "page": self.page,
            "kind": self.kind,
            "image_path": self.image_path,
            "thumbnail_path": self.thumbnail_path,
            "bbox": self.bbox,
            "caption": self.caption,
            "source": self.source,
            "summary": self.summary,
            "key_facts": self.key_facts,
            "metadata": self.metadata,
        }

    @classmethod
    def from_metadata(cls, payload: dict[str, Any]) -> "PaperVisualAsset":
        return cls(
            asset_id=str(payload.get("asset_id") or ""),
            paper_id=str(payload.get("paper_id") or ""),
            page=int(payload.get("page") or 0),
            kind=str(payload.get("kind") or "page"),
            image_path=str(payload.get("image_path") or ""),
            thumbnail_path=payload.get("thumbnail_path") if isinstance(payload.get("thumbnail_path"), str) else None,
            bbox=payload.get("bbox") if isinstance(payload.get("bbox"), list) else None,
            caption=payload.get("caption") if isinstance(payload.get("caption"), str) else None,
            source=str(payload.get("source") or "metadata"),
            summary=payload.get("summary") if isinstance(payload.get("summary"), str) else None,
            key_facts=payload.get("key_facts") if isinstance(payload.get("key_facts"), list) else [],
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )


def _visual_root() -> Path:
    return Path(settings.UPLOAD_DIR).resolve() / "paper-visual-assets"


def _safe_asset_id(*parts: Any) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _caption_kind(caption: str) -> str:
    lower = caption.lower()
    if re.search(r"\btable\s*\.?\s*\d+|表\s*\d+", lower):
        return "table"
    if re.search(r"\bfig(?:ure)?\s*\.?\s*\d+|图\s*\d+", lower):
        return "figure"
    return "visual"


def _visual_summary_text(asset: PaperVisualAsset) -> str:
    parts = [
        f"[PDF visual asset, page {asset.page}, kind {asset.kind}, asset {asset.asset_id}]",
    ]
    if asset.caption:
        parts.append(f"Caption: {asset.caption}")
    if asset.summary:
        parts.append(f"Visual summary: {asset.summary}")
    if asset.key_facts:
        parts.append("Key facts: " + "; ".join(str(item) for item in asset.key_facts[:8]))
    if asset.bbox:
        parts.append(f"BBox: {asset.bbox}")
    if asset.image_path:
        parts.append(f"Image path: {asset.image_path}")
    if asset.thumbnail_path:
        parts.append(f"Thumbnail path: {asset.thumbnail_path}")
    return "\n".join(parts)


def visual_assets_from_paper(paper: Paper) -> list[PaperVisualAsset]:
    metadata = getattr(paper, "metadata_json", None) or {}
    payload = metadata.get(PDF_VISUAL_ASSETS_METADATA_KEY)
    if not isinstance(payload, dict) or payload.get("version") != PDF_VISUAL_ASSETS_VERSION:
        return []
    assets = payload.get("assets")
    if not isinstance(assets, list):
        return []
    parsed = []
    for item in assets:
        if isinstance(item, dict):
            asset = PaperVisualAsset.from_metadata(item)
            if asset.asset_id and asset.page:
                parsed.append(asset)
    return parsed


def visual_asset_status_from_paper(paper: Paper) -> dict[str, Any]:
    metadata = getattr(paper, "metadata_json", None) or {}
    payload = metadata.get(PDF_VISUAL_ASSETS_METADATA_KEY)
    assets = visual_assets_from_paper(paper)
    summarized = [asset for asset in assets if asset.summary or asset.key_facts]
    return {
        "ready": bool(assets),
        "version": payload.get("version") if isinstance(payload, dict) else None,
        "parser": payload.get("parser") if isinstance(payload, dict) else None,
        "extracted_at": payload.get("extracted_at") if isinstance(payload, dict) else None,
        "asset_count": len(assets),
        "page_asset_count": sum(1 for asset in assets if asset.kind == "page"),
        "figure_asset_count": sum(1 for asset in assets if asset.kind == "figure"),
        "table_asset_count": sum(1 for asset in assets if asset.kind == "table"),
        "summary_count": len(summarized),
        "summary_missing": bool(assets) and len(summarized) < min(len(assets), settings.PDF_VISUAL_SUMMARY_MAX_ASSETS),
        "enabled": bool(settings.PDF_VISUAL_ASSET_ENABLED),
        "summary_enabled": bool(settings.PDF_VISUAL_SUMMARY_ENABLED),
        "last_error": payload.get("last_error") if isinstance(payload, dict) else None,
    }


def visual_evidence_blocks_from_paper(paper: Paper) -> list[dict[str, Any]]:
    blocks = []
    for asset in visual_assets_from_paper(paper):
        text = _visual_summary_text(asset)
        blocks.append({
            "type": "visual_summary" if asset.summary or asset.key_facts else "visual_asset",
            "page": asset.page,
            "source": asset.source,
            "text": text,
            "metadata": {
                "asset_id": asset.asset_id,
                "kind": asset.kind,
                "bbox": asset.bbox,
                "caption": asset.caption,
                "image_path": asset.image_path,
                "thumbnail_path": asset.thumbnail_path,
                "has_visual_summary": bool(asset.summary or asset.key_facts),
                **(asset.metadata or {}),
            },
        })
    return blocks


def _caption_region_bbox(page_width: float, page_height: float, kind: str) -> list[float]:
    """Return a broad, deterministic page-region bbox for caption-linked assets.

    This is a conservative bridge until a layout detector provides exact figure
    polygons. It avoids exposing full-page renders as figure/table evidence.
    """

    margin_x = page_width * 0.06
    if kind == "table":
        return [
            margin_x,
            page_height * 0.18,
            page_width - margin_x,
            page_height * 0.92,
        ]
    if kind == "figure":
        return [
            margin_x,
            page_height * 0.06,
            page_width - margin_x,
            page_height * 0.78,
        ]
    return [
        margin_x,
        page_height * 0.08,
        page_width - margin_x,
        page_height * 0.9,
    ]


def _save_region_crop(
    *,
    doc: Any,
    page_index: int,
    bbox: list[float],
    matrix: Any,
    image_path: Path,
) -> bool:
    page = doc.load_page(page_index)
    rect = page.rect
    try:
        import fitz

        clip = fitz.Rect(
            max(rect.x0, bbox[0]),
            max(rect.y0, bbox[1]),
            min(rect.x1, bbox[2]),
            min(rect.y1, bbox[3]),
        )
        if clip.is_empty or clip.width < 24 or clip.height < 24:
            return False
        pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
        pix.save(str(image_path))
        return True
    except Exception as exc:
        logger.debug("Failed to crop visual region on page %s: %s", page_index + 1, exc)
        return False


def _caption_assets_from_structured_blocks(
    *,
    paper_id: str,
    page_assets: dict[int, PaperVisualAsset],
    structured_blocks: list[dict[str, Any]],
    limit_remaining: int,
    doc: Any | None = None,
    target_dir: Path | None = None,
    matrix: Any | None = None,
    extension: str = "png",
) -> list[PaperVisualAsset]:
    assets: list[PaperVisualAsset] = []
    seen: set[tuple[int, str]] = set()
    for block in structured_blocks:
        if len(assets) >= limit_remaining:
            break
        if not isinstance(block, dict) or block.get("type") != "caption":
            continue
        page = block.get("page")
        text = re.sub(r"\s+", " ", str(block.get("text") or "")).strip()
        if not isinstance(page, int) or page not in page_assets or not text:
            continue
        cleaned_caption = re.sub(r"^\[PDF caption[^\]]*\]\s*", "", text).strip()
        kind = _caption_kind(cleaned_caption)
        if kind not in {"figure", "table"}:
            continue
        dedupe_key = (page, cleaned_caption[:160])
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        page_asset = page_assets[page]
        asset_id = _safe_asset_id(paper_id, page, kind, cleaned_caption[:120])
        crop_bbox = None
        crop_path = None
        crop_strategy = "page_fallback"
        if doc is not None and target_dir is not None and matrix is not None:
            try:
                pdf_page = doc.load_page(page - 1)
                crop_bbox = _caption_region_bbox(float(pdf_page.rect.width), float(pdf_page.rect.height), kind)
                candidate_path = target_dir / f"{asset_id}-crop.{extension}"
                if not candidate_path.exists():
                    cropped = _save_region_crop(
                        doc=doc,
                        page_index=page - 1,
                        bbox=crop_bbox,
                        matrix=matrix,
                        image_path=candidate_path,
                    )
                else:
                    cropped = True
                if cropped:
                    crop_path = candidate_path
                    crop_strategy = "caption_page_region"
            except Exception as exc:
                logger.debug("Caption-linked crop failed for %s page %s: %s", paper_id, page, exc)
        assets.append(PaperVisualAsset(
            asset_id=asset_id,
            paper_id=paper_id,
            page=page,
            kind=kind,
            image_path=str(crop_path) if crop_path else page_asset.image_path,
            thumbnail_path=str(crop_path) if crop_path else page_asset.thumbnail_path,
            bbox=crop_bbox if crop_path else None,
            caption=cleaned_caption[:1000],
            source=f"caption+{crop_strategy}",
            metadata={
                "linked_page_asset_id": page_asset.asset_id,
                "fallback_image_path": page_asset.image_path if not crop_path else None,
                "crop_strategy": crop_strategy,
                "caption_type": (block.get("metadata") or {}).get("caption_type") if isinstance(block.get("metadata"), dict) else None,
            },
        ))
    return assets


def _extract_visual_assets_sync(paper: Paper, pdf_path: str, structured_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    if not settings.PDF_VISUAL_ASSET_ENABLED:
        return {"version": PDF_VISUAL_ASSETS_VERSION, "enabled": False, "assets": []}

    try:
        import fitz
    except Exception as exc:
        raise RuntimeError(f"PyMuPDF/fitz is not available for visual extraction: {exc}") from exc

    paper_id = str(paper.id)
    target_dir = _visual_root() / paper_id
    target_dir.mkdir(parents=True, exist_ok=True)

    max_pages = max(1, int(settings.PDF_VISUAL_ASSET_MAX_PAGES or 1))
    max_assets = max(1, int(settings.PDF_VISUAL_ASSET_MAX_ASSETS or 1))
    scale = max(0.5, min(float(settings.PDF_VISUAL_ASSET_RENDER_SCALE or 1.0), 3.0))
    image_format = str(settings.PDF_VISUAL_ASSET_IMAGE_FORMAT or "png").lower()
    if image_format not in {"png", "jpg", "jpeg"}:
        image_format = "png"
    extension = "jpg" if image_format == "jpeg" else image_format

    doc = fitz.open(pdf_path)
    page_assets: dict[int, PaperVisualAsset] = {}
    try:
        page_count = doc.page_count
        render_count = min(page_count, max_pages)
        matrix = fitz.Matrix(scale, scale)
        for page_index in range(render_count):
            page_number = page_index + 1
            page = doc.load_page(page_index)
            asset_id = _safe_asset_id(paper_id, "page", page_number)
            image_path = target_dir / f"{asset_id}.{extension}"
            if not image_path.exists():
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                pix.save(str(image_path))
            page_assets[page_number] = PaperVisualAsset(
                asset_id=asset_id,
                paper_id=paper_id,
                page=page_number,
                kind="page",
                image_path=str(image_path),
                thumbnail_path=str(image_path),
                source="fitz_page_render",
                metadata={
                    "width": int(page.rect.width),
                    "height": int(page.rect.height),
                    "render_scale": scale,
                },
            )

        assets = list(page_assets.values())[:max_assets]
        caption_assets = _caption_assets_from_structured_blocks(
            paper_id=paper_id,
            page_assets=page_assets,
            structured_blocks=structured_blocks,
            limit_remaining=max(0, max_assets - len(assets)),
            doc=doc,
            target_dir=target_dir,
            matrix=matrix,
            extension=extension,
        )
        assets.extend(caption_assets)

        return {
            "version": PDF_VISUAL_ASSETS_VERSION,
            "enabled": True,
            "parser": "fitz_page_render",
            "source_path": pdf_path,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "page_count": len(page_assets),
            "asset_count": len(assets),
            "assets": [asset.to_metadata() for asset in assets[:max_assets]],
        }
    finally:
        doc.close()


async def ensure_paper_visual_assets(
    paper: Paper,
    db: Optional[AsyncSession] = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Return persisted visual asset metadata, extracting from PDF when needed."""

    existing = (getattr(paper, "metadata_json", None) or {}).get(PDF_VISUAL_ASSETS_METADATA_KEY)
    if existing and not force:
        return existing

    from app.services.report_service import (
        ensure_structured_pdf_content,
        resolve_paper_pdf_path,
        structured_pdf_evidence_blocks_from_paper,
    )

    pdf_path = await resolve_paper_pdf_path(paper)
    if not pdf_path or not os.path.exists(pdf_path):
        payload = {
            "version": PDF_VISUAL_ASSETS_VERSION,
            "enabled": bool(settings.PDF_VISUAL_ASSET_ENABLED),
            "assets": [],
            "last_error": {"message": "PDF is unavailable for visual extraction"},
        }
    else:
        try:
            structured_blocks = structured_pdf_evidence_blocks_from_paper(paper)
            if not structured_blocks:
                extraction = await ensure_structured_pdf_content(paper)
                structured_blocks = extraction.to_evidence_blocks() if extraction else []
            payload = await asyncio.to_thread(_extract_visual_assets_sync, paper, pdf_path, structured_blocks)
        except Exception as exc:
            logger.warning("PDF visual asset extraction failed for %s: %s", getattr(paper, "id", None), exc)
            payload = {
                "version": PDF_VISUAL_ASSETS_VERSION,
                "enabled": bool(settings.PDF_VISUAL_ASSET_ENABLED),
                "assets": [],
                "last_error": {"message": str(exc)[:500]},
            }

    metadata = dict(getattr(paper, "metadata_json", None) or {})
    metadata[PDF_VISUAL_ASSETS_METADATA_KEY] = payload
    paper.metadata_json = metadata
    if db is not None:
        db.add(paper)
        await db.commit()
        await db.refresh(paper)
    return payload


def _image_data_url(path: str) -> str:
    suffix = Path(path).suffix.lower().lstrip(".") or "png"
    mime = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix}"
    with open(path, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


async def summarize_visual_asset(asset: PaperVisualAsset) -> PaperVisualAsset:
    """Optionally summarize an asset with the active image-capable provider."""

    if not settings.PDF_VISUAL_SUMMARY_ENABLED:
        return asset
    if not asset.image_path or not os.path.exists(asset.image_path):
        return asset
    try:
        from app.services.llm import llm_service

        prompt = (
            "请作为论文阅读助手，基于这张 PDF 页面/图表截图生成严谨的中文视觉摘要。"
            "重点提取：图表类型、方法模块、坐标轴/指标、实验结论、与 caption 一致的事实。"
            "如果图片无法判断，请明确说无法判断，不要编造。"
        )
        if asset.caption:
            prompt += f"\nCaption: {asset.caption}"
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": _image_data_url(asset.image_path)}},
        ]
        summary = await llm_service.chat(
            [{"role": "user", "content": content}],
            temperature=0.2,
            max_tokens=1200,
        )
        if summary:
            asset.summary = summary[:2000]
            asset.metadata = {
                **(asset.metadata or {}),
                "summary_model": llm_service.model,
                "summarized_at": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as exc:
        logger.warning("视觉摘要生成失败，保留资产但不写摘要: %s", exc)
        asset.metadata = {**(asset.metadata or {}), "summary_error": str(exc)[:300]}
    return asset


async def backfill_visual_summaries(
    paper: Paper,
    db: Optional[AsyncSession] = None,
    *,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    payload = await ensure_paper_visual_assets(paper, db=None)
    assets = visual_assets_from_paper(paper)
    if not assets:
        return {"processed": 0, "success": 0, "skipped": 1, "failed": 0, "reason": "no visual assets"}
    max_assets = min(limit or settings.PDF_VISUAL_SUMMARY_MAX_ASSETS, settings.PDF_VISUAL_SUMMARY_MAX_ASSETS)
    processed = success = failed = skipped = 0
    updated_assets: list[PaperVisualAsset] = []
    for asset in assets:
        if processed >= max_assets:
            updated_assets.append(asset)
            continue
        if asset.summary or asset.key_facts:
            skipped += 1
            updated_assets.append(asset)
            continue
        processed += 1
        summarized = await summarize_visual_asset(asset)
        if summarized.summary or summarized.key_facts:
            success += 1
        elif (summarized.metadata or {}).get("summary_error"):
            failed += 1
        else:
            skipped += 1
        updated_assets.append(summarized)
    metadata = dict(getattr(paper, "metadata_json", None) or {})
    payload = dict(payload or {})
    payload["assets"] = [asset.to_metadata() for asset in updated_assets]
    payload["summary_checked_at"] = datetime.now(timezone.utc).isoformat()
    metadata[PDF_VISUAL_ASSETS_METADATA_KEY] = payload
    paper.metadata_json = metadata
    if db is not None:
        db.add(paper)
        await db.commit()
        await db.refresh(paper)
    return {"processed": processed, "success": success, "skipped": skipped, "failed": failed}
