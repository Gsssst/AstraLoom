"""组会报告生成服务。"""

import asyncio
import importlib.util
import json
import logging
import re
import shlex
import subprocess
from html.parser import HTMLParser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.services.llm import llm_service
from app.services.arxiv_pdf_cache import ArxivPdfCacheError, ensure_cached_arxiv_pdf
from app.db.models.paper import Paper

logger = logging.getLogger(__name__)
_full_text_tasks: dict[str, asyncio.Task[str]] = {}
PDF_STRUCTURED_METADATA_KEY = "pdf_structured_content"
PDF_STRUCTURED_PARSE_ERROR_KEY = "pdf_structured_parse_error"
PDF_STRUCTURED_METADATA_VERSION = 1
MAX_STRUCTURED_BLOCKS = 80
MAX_STRUCTURED_BLOCK_CHARS = 1800
MAX_STRUCTURED_TABLE_BLOCK_CHARS = 20000
SUPPORTED_PDF_STRUCTURED_BACKENDS = {"lightweight", "command", "docling", "auto"}
GENERIC_TABLE_HEADER_PATTERN = re.compile(r"^column\s+\d+$", re.IGNORECASE)
MERGED_NUMERIC_CELL_PATTERN = re.compile(r"(?:[+-]?\d+(?:\.\d+)?%?\s+){2,}[+-]?\d+(?:\.\d+)?%?")


def sanitize_pdf_storage_value(value: Any) -> Any:
    """Remove invalid PostgreSQL text/json characters from parser output."""

    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, list):
        return [sanitize_pdf_storage_value(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_pdf_storage_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(sanitize_pdf_storage_value(key)): sanitize_pdf_storage_value(item)
            for key, item in value.items()
        }
    return value


def structured_block_text_limit(block_type: str) -> int:
    return MAX_STRUCTURED_TABLE_BLOCK_CHARS if block_type == "table" else MAX_STRUCTURED_BLOCK_CHARS


@dataclass
class StructuredPdfBlock:
    """A page-aware PDF block that can be used as retrieval evidence."""

    block_type: str
    text: str
    page: Optional[int] = None
    source: str = "pdfplumber"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        text_limit = MAX_STRUCTURED_TABLE_BLOCK_CHARS if self.block_type == "table" else MAX_STRUCTURED_BLOCK_CHARS
        return sanitize_pdf_storage_value({
            "type": self.block_type,
            "page": self.page,
            "source": self.source,
            "text": self.text[:text_limit],
            "metadata": self.metadata,
        })

    @classmethod
    def from_metadata(cls, payload: dict[str, Any]) -> "StructuredPdfBlock":
        return cls(
            block_type=str(payload.get("type") or "structured"),
            page=payload.get("page"),
            source=str(payload.get("source") or "metadata"),
            text=str(payload.get("text") or ""),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )


@dataclass
class StructuredPdfExtraction:
    """Bounded structured extraction summary for one PDF."""

    source_path: str
    page_count: int
    blocks: list[StructuredPdfBlock]
    parser: str = "pdfplumber"
    version: int = PDF_STRUCTURED_METADATA_VERSION

    @property
    def table_count(self) -> int:
        return sum(1 for block in self.blocks if block.block_type == "table")

    @property
    def caption_count(self) -> int:
        return sum(1 for block in self.blocks if block.block_type == "caption")

    @property
    def visual_count(self) -> int:
        return sum(1 for block in self.blocks if block.block_type == "visual")

    @property
    def table_quality(self) -> dict[str, Any]:
        return structured_table_quality_from_blocks(self.blocks)

    def to_metadata(self) -> dict[str, Any]:
        bounded_blocks = self.blocks[:MAX_STRUCTURED_BLOCKS]
        return sanitize_pdf_storage_value({
            "version": self.version,
            "source_path": self.source_path,
            "parser": self.parser,
            "parsed_at": datetime.now(timezone.utc).isoformat(),
            "page_count": self.page_count,
            "table_count": self.table_count,
            "caption_count": self.caption_count,
            "visual_count": self.visual_count,
            "table_quality": structured_table_quality_from_blocks(bounded_blocks),
            "blocks": [block.to_metadata() for block in bounded_blocks],
        })

    def to_evidence_blocks(self) -> list[dict[str, Any]]:
        return [
            {
                "type": block.block_type,
                "page": block.page,
                "source": block.source,
                "text": evidence_text_from_structured_block(block),
                "metadata": block.metadata,
            }
            for block in self.blocks[:MAX_STRUCTURED_BLOCKS]
            if block.text.strip()
        ]

    @classmethod
    def from_metadata(cls, payload: dict[str, Any]) -> Optional["StructuredPdfExtraction"]:
        if not isinstance(payload, dict):
            return None
        if payload.get("version") != PDF_STRUCTURED_METADATA_VERSION:
            return None
        blocks_payload = payload.get("blocks")
        if not isinstance(blocks_payload, list):
            return None
        return cls(
            source_path=str(payload.get("source_path") or ""),
            page_count=int(payload.get("page_count") or 0),
            parser=str(payload.get("parser") or "metadata"),
            blocks=[
                StructuredPdfBlock.from_metadata(item)
                for item in blocks_payload
                if isinstance(item, dict) and str(item.get("text") or "").strip()
            ],
        )


async def ensure_full_text(paper: Paper) -> str:
    """确保论文有全文：先检查 DB，没有则从 arXiv 异步下载 PDF 并解析。

    修复：使用 httpx 异步下载 + asyncio.to_thread PDF 解析，
    避免 urllib 同步阻塞调用冻结整个 asyncio 事件循环。
    """
    if paper.full_text and len(paper.full_text) > 500:
        return paper.full_text

    if not paper.arxiv_id:
        return paper.abstract or ""

    task_key = str(getattr(paper, "id", None) or paper.arxiv_id)
    task = _full_text_tasks.get(task_key)
    if task is None:
        task = asyncio.create_task(_download_and_parse_full_text(paper))
        _full_text_tasks[task_key] = task

        def _clear_completed_task(completed_task: asyncio.Task[str]) -> None:
            if _full_text_tasks.get(task_key) is completed_task:
                _full_text_tasks.pop(task_key, None)

        task.add_done_callback(_clear_completed_task)

    # A foreground request may time out, but the shared preload should continue.
    return await asyncio.shield(task)


def _extract_pdf_text(path: str) -> str:
    """Extract PDF text with installed parsers before optional fallbacks."""
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            text_parts = [text for page in pdf.pages if (text := page.extract_text())]
        full_text = "\n\n".join(text_parts).strip()
        if full_text:
            return full_text
    except Exception as exc:
        logger.warning(f"pdfplumber 解析失败，尝试 fitz: {exc}")

    try:
        import fitz

        doc = fitz.open(path)
        try:
            return "\n\n".join(page.get_text() for page in doc).strip()
        finally:
            doc.close()
    except Exception as exc:
        logger.warning(f"fitz 解析失败: {exc}")
        return ""


def _clean_table_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("|", "\\|")


def _deduplicate_header_names(header: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    deduped: list[str] = []
    for index, name in enumerate(header, 1):
        base = name or f"Column {index}"
        count = seen.get(base, 0) + 1
        seen[base] = count
        deduped.append(base if count == 1 else f"{base} {count}")
    return deduped


def table_to_markdown(table: list[list[Any]]) -> str:
    """Convert a pdfplumber table into Markdown without dropping rows or columns."""
    rows = [
        [_clean_table_cell(cell) for cell in row]
        for row in table
        if row and any(_clean_table_cell(cell) for cell in row)
    ]
    if not rows:
        return ""

    max_cols = max(len(row) for row in rows)
    normalized = [row + [""] * (max_cols - len(row)) for row in rows]
    header = _deduplicate_header_names(normalized[0])
    body = normalized[1:] or [[""] * max_cols]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * max_cols) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines).strip()


def evidence_text_from_structured_block(block: StructuredPdfBlock) -> str:
    """Use repaired cell metadata for table evidence when available."""
    if block.block_type != "table":
        return block.text
    metadata = block.metadata or {}
    rows = _normalize_table_rows(metadata.get("rows"))
    if not rows:
        headers = metadata.get("headers")
        cells = metadata.get("cells")
        if isinstance(headers, list) and isinstance(cells, list):
            rows = [headers, *_normalize_table_rows(cells)]
    if rows:
        markdown = table_to_markdown(rows)
        if markdown:
            caption = str(metadata.get("caption") or "").strip()
            prefix = f"[PDF repaired table, page {block.page or 'unknown'}, table {metadata.get('table_index') or '?'}]"
            if caption:
                prefix += f"\nCaption: {caption}"
            return f"{prefix}\n{markdown}"[:MAX_STRUCTURED_TABLE_BLOCK_CHARS]
    return block.text


def _markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r"-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        rows.append(cells)
    return rows


def structured_table_quality_from_blocks(blocks: list[StructuredPdfBlock]) -> dict[str, Any]:
    """Compute lightweight quality signals for persisted table blocks."""
    table_blocks = [block for block in blocks if block.block_type == "table"]
    warnings: list[str] = []
    if not table_blocks:
        return {
            "table_count": 0,
            "low_quality_table_count": 0,
            "average_rows": 0.0,
            "empty_cell_ratio": 0.0,
            "generic_header_ratio": 0.0,
            "merged_numeric_cell_count": 0,
            "inconsistent_row_count": 0,
            "quality": "none",
            "flags": [],
            "warnings": [],
        }

    total_rows = 0
    total_cells = 0
    empty_cells = 0
    generic_headers = 0
    header_cells = 0
    low_quality = 0
    merged_numeric_cell_count = 0
    inconsistent_row_count = 0
    malformed_table_count = 0
    flags: set[str] = set()
    for block in table_blocks:
        rows = _markdown_table_rows(block.text)
        total_rows += len(rows)
        cells = [cell for row in rows for cell in row]
        total_cells += len(cells)
        empty_cells += sum(1 for cell in cells if not cell.strip())
        header = rows[0] if rows else []
        header_cells += len(header)
        generic_headers += sum(1 for cell in header if GENERIC_TABLE_HEADER_PATTERN.match(cell.strip()))
        merged_numeric = sum(1 for cell in cells if MERGED_NUMERIC_CELL_PATTERN.search(cell.strip()))
        merged_numeric_cell_count += merged_numeric
        widths = [len(row) for row in rows if row]
        expected_width = max(set(widths), key=widths.count) if widths else 0
        inconsistent_rows = sum(1 for width in widths if expected_width and width != expected_width)
        inconsistent_row_count += inconsistent_rows
        if not rows or not header or expected_width <= 1:
            malformed_table_count += 1
        non_empty_cells = sum(1 for cell in cells if cell.strip())
        empty_ratio = (sum(1 for cell in cells if not cell.strip()) / len(cells)) if cells else 1.0
        block_generic_header_ratio = (
            sum(1 for cell in header if GENERIC_TABLE_HEADER_PATTERN.match(cell.strip())) / len(header)
            if header else 1.0
        )
        if merged_numeric:
            flags.add("merged_numeric_cells")
        if inconsistent_rows:
            flags.add("inconsistent_row_widths")
        if len(rows) < 2 or not header:
            flags.add("malformed_markdown_table")
        if block_generic_header_ratio >= 0.35:
            flags.add("generic_headers")
        if empty_ratio >= 0.35:
            flags.add("many_empty_cells")
        if (
            len(rows) < 2
            or non_empty_cells <= 4
            or empty_ratio >= 0.35
            or block_generic_header_ratio >= 0.35
            or merged_numeric > 0
            or inconsistent_rows > max(1, len(rows) // 4)
            or expected_width <= 1
        ):
            low_quality += 1

    empty_cell_ratio = round(empty_cells / total_cells, 3) if total_cells else 1.0
    generic_header_ratio = round(generic_headers / header_cells, 3) if header_cells else 0.0
    average_rows = round(total_rows / len(table_blocks), 2)
    low_quality_ratio = low_quality / len(table_blocks)
    if low_quality_ratio >= 0.5:
        quality = "low"
        warnings.append("多数表格疑似解析不完整")
    elif low_quality:
        quality = "medium"
        warnings.append("部分表格疑似解析不完整")
    else:
        quality = "high"
    if generic_header_ratio >= 0.2:
        warnings.append("存在较多泛化列名，表头识别质量偏低")
    if empty_cell_ratio >= 0.25:
        warnings.append("表格空单元格比例偏高")
    if merged_numeric_cell_count:
        warnings.append("检测到疑似粘连的连续数值单元格")
    if inconsistent_row_count:
        warnings.append("检测到行列数量不一致，表格结构可能错位")
    if malformed_table_count:
        warnings.append("检测到 Markdown 表格结构不完整")

    return {
        "table_count": len(table_blocks),
        "low_quality_table_count": low_quality,
        "average_rows": average_rows,
        "empty_cell_ratio": empty_cell_ratio,
        "generic_header_ratio": generic_header_ratio,
        "merged_numeric_cell_count": merged_numeric_cell_count,
        "inconsistent_row_count": inconsistent_row_count,
        "malformed_table_count": malformed_table_count,
        "quality": quality,
        "flags": sorted(flags),
        "warnings": warnings,
    }


CAPTION_PATTERN = re.compile(
    r"(?im)^\s*((?:fig(?:ure)?|table)\s*\.?\s*\d+[a-z]?[^\n]{0,500}(?:\n(?!\s*(?:fig(?:ure)?|table)\s*\.?\s*\d+|\s*\d+\s+[A-Z]).{0,500}){0,2})"
)


def extract_caption_blocks(text: str, page_number: int) -> list[StructuredPdfBlock]:
    """Extract figure/table captions from page text."""
    blocks: list[StructuredPdfBlock] = []
    for match in CAPTION_PATTERN.finditer(text or ""):
        caption = re.sub(r"\s+", " ", match.group(1)).strip()
        if len(caption) < 12:
            continue
        caption_type = "table_caption" if caption.lower().startswith("table") else "figure_caption"
        blocks.append(StructuredPdfBlock(
            block_type="caption",
            page=page_number,
            source="pdfplumber",
            text=f"[PDF caption, page {page_number}] {caption}"[:MAX_STRUCTURED_BLOCK_CHARS],
            metadata={"caption_type": caption_type},
        ))
    return blocks


def parser_subprocess_environment() -> dict[str, str]:
    """Build environment for optional external PDF parser commands."""
    import os

    env = dict(os.environ)
    runtime_values = {
        "HF_ENDPOINT": settings.HF_ENDPOINT,
        "HF_HOME": settings.HF_HOME,
        "TRANSFORMERS_CACHE": settings.TRANSFORMERS_CACHE,
        "SENTENCE_TRANSFORMERS_HOME": settings.SENTENCE_TRANSFORMERS_HOME,
    }
    for key, value in runtime_values.items():
        if str(value or "").strip():
            env[key] = str(value).strip()
    return env


def parser_runtime_health() -> dict[str, Any]:
    """Return operational health for configured structured PDF parsers."""
    command = str(settings.PDF_STRUCTURED_PARSER_COMMAND or "").strip()
    return {
        "configured_backend": settings.PDF_STRUCTURED_PARSER_BACKEND,
        "supported_backends": sorted(SUPPORTED_PDF_STRUCTURED_BACKENDS),
        "available": {
            "pdfplumber": importlib.util.find_spec("pdfplumber") is not None,
            "fitz": importlib.util.find_spec("fitz") is not None,
            "docling": importlib.util.find_spec("docling") is not None,
            "command": bool(command),
        },
        "command_configured": bool(command),
        "hf_endpoint": settings.HF_ENDPOINT,
        "hf_home": settings.HF_HOME,
        "transformers_cache": settings.TRANSFORMERS_CACHE,
        "sentence_transformers_home": settings.SENTENCE_TRANSFORMERS_HOME,
    }


def _coerce_page_number(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        return parsed if parsed > 0 else None
    return None


def _normalize_external_block_type(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "structured").lower()).strip("_")
    aliases = {
        "table_caption": "caption",
        "figure_caption": "caption",
        "fig_caption": "caption",
        "image": "visual",
        "picture": "visual",
        "figure": "visual",
        "chart": "visual",
        "ocr": "ocr",
        "formula": "formula",
        "equation": "formula",
    }
    return aliases.get(normalized, normalized or "structured")


def _external_block_text(item: dict[str, Any]) -> str:
    for key in ("text", "markdown", "content", "html"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            if key == "html":
                rows = html_table_to_rows(value)
                if rows:
                    return table_to_markdown(rows)
            return value.strip()
    table = item.get("table")
    if isinstance(table, list):
        return table_to_markdown(table)
    rows = _table_rows_from_parser_item(item)
    if rows:
        return table_to_markdown(rows)
    return ""


class _HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._current_row: Optional[list[str]] = None
        self._current_cell: Optional[list[str]] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() == "tr":
            self._current_row = []
        elif tag.lower() in {"td", "th"} and self._current_row is not None:
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            cell = re.sub(r"\s+", " ", "".join(self._current_cell)).strip()
            self._current_row.append(cell)
            self._current_cell = None
        elif lowered == "tr" and self._current_row is not None:
            if any(cell.strip() for cell in self._current_row):
                self.rows.append(self._current_row)
            self._current_row = None


def html_table_to_rows(html: str) -> list[list[str]]:
    parser = _HtmlTableParser()
    try:
        parser.feed(html or "")
    except Exception:
        return []
    return parser.rows


def _normalize_table_rows(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    rows: list[list[str]] = []
    for row in value:
        if isinstance(row, dict):
            cells = row.get("cells") or row.get("row") or row.get("values")
            if not isinstance(cells, list):
                cells = list(row.values())
        else:
            cells = row
        if isinstance(cells, list):
            normalized = []
            for cell in cells:
                if isinstance(cell, dict):
                    normalized.append(str(cell.get("text") or cell.get("value") or cell.get("content") or "").strip())
                else:
                    normalized.append(str(cell or "").strip())
            if any(normalized):
                rows.append(normalized)
    return rows


def _normalize_table_cells(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    if value and all(isinstance(item, list) for item in value):
        return _normalize_table_rows(value)
    positioned: dict[int, dict[int, str]] = {}
    for item in value:
        if not isinstance(item, dict):
            continue
        row = item.get("row") if item.get("row") is not None else item.get("row_index")
        col = item.get("col") if item.get("col") is not None else item.get("col_index")
        if not isinstance(row, int) or not isinstance(col, int):
            continue
        positioned.setdefault(row, {})[col] = str(item.get("text") or item.get("value") or item.get("content") or "").strip()
    rows: list[list[str]] = []
    for row_index in sorted(positioned):
        cols = positioned[row_index]
        if not cols:
            continue
        max_col = max(cols)
        row = [cols.get(col_index, "") for col_index in range(max_col + 1)]
        if any(row):
            rows.append(row)
    return rows


def _table_rows_from_parser_item(item: dict[str, Any]) -> list[list[str]]:
    for key in ("rows", "table", "data"):
        rows = _normalize_table_rows(item.get(key))
        if rows:
            return rows
    rows = _normalize_table_cells(item.get("cells"))
    if rows:
        return rows
    html = item.get("html") or item.get("table_html")
    if isinstance(html, str) and html.strip():
        return html_table_to_rows(html)
    markdown = item.get("markdown") or item.get("text")
    if isinstance(markdown, str):
        rows = _markdown_table_rows(markdown)
        if rows:
            return rows
    return []


def _iter_external_parser_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("tables", "blocks", "elements", "chunks", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    pages = payload.get("pages")
    items: list[dict[str, Any]] = []
    if isinstance(pages, list):
        for page_index, page in enumerate(pages, 1):
            if not isinstance(page, dict):
                continue
            page_number = _coerce_page_number(page.get("page") or page.get("page_number")) or page_index
            page_blocks = page.get("blocks") or page.get("elements") or []
            if isinstance(page_blocks, list):
                for block in page_blocks:
                    if isinstance(block, dict):
                        merged = dict(block)
                        merged.setdefault("page", page_number)
                        items.append(merged)
            page_text = page.get("text") or page.get("markdown")
            if isinstance(page_text, str) and page_text.strip():
                items.append({"type": "text", "text": page_text, "page": page_number})
    return items


def structured_extraction_from_external_payload(
    payload: Any,
    *,
    source_path: str,
    parser: str = "command",
) -> StructuredPdfExtraction:
    """Normalize external parser JSON into the internal structured format."""
    blocks: list[StructuredPdfBlock] = []
    max_page = 0
    for index, item in enumerate(_iter_external_parser_items(payload), 1):
        text = _external_block_text(item)
        if not text:
            continue
        page = _coerce_page_number(
            item.get("page")
            or item.get("page_number")
            or item.get("page_index")
            or item.get("pageNumber")
        )
        if page:
            max_page = max(max_page, page)
        raw_type = item.get("type") or item.get("category") or item.get("kind") or item.get("label")
        block_type = _normalize_external_block_type(raw_type)
        if block_type == "structured" and _table_rows_from_parser_item(item):
            block_type = "table"
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        blocks.append(StructuredPdfBlock(
            block_type=block_type,
            page=page,
            source=parser,
            text=text[:structured_block_text_limit(block_type)],
            metadata={**metadata, "external_index": index},
        ))
        if len(blocks) >= MAX_STRUCTURED_BLOCKS:
            break

    payload_page_count = payload.get("page_count") if isinstance(payload, dict) else None
    return StructuredPdfExtraction(
        source_path=source_path,
        page_count=_coerce_page_number(payload_page_count) or max_page,
        blocks=blocks,
        parser=parser,
    )


def _object_to_plain_dict(value: Any) -> Optional[dict[str, Any]]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            return dumped if isinstance(dumped, dict) else None
        except Exception:
            return None
    if hasattr(value, "dict"):
        try:
            dumped = value.dict()
            return dumped if isinstance(dumped, dict) else None
        except Exception:
            return None
    return None


def _docling_page_from_item(item: Any) -> Optional[int]:
    payload = _object_to_plain_dict(item) or {}
    for key in ("page", "page_no", "page_number", "page_index"):
        page = _coerce_page_number(payload.get(key))
        if page:
            return page

    prov = payload.get("prov") or getattr(item, "prov", None)
    if isinstance(prov, list) and prov:
        first = prov[0]
        first_payload = _object_to_plain_dict(first) or {}
        page = _coerce_page_number(first_payload.get("page_no") or first_payload.get("page"))
        if page:
            return page
    elif prov:
        prov_payload = _object_to_plain_dict(prov) or {}
        page = _coerce_page_number(prov_payload.get("page_no") or prov_payload.get("page"))
        if page:
            return page
    return None


def _docling_bbox_from_item(item: Any) -> Optional[list[float]]:
    payload = _object_to_plain_dict(item) or {}
    for key in ("bbox", "box", "bounding_box"):
        value = payload.get(key) or getattr(item, key, None)
        bbox = _normalize_bbox_value(value)
        if bbox:
            return bbox
    prov = payload.get("prov") or getattr(item, "prov", None)
    prov_items = prov if isinstance(prov, list) else [prov] if prov else []
    for prov_item in prov_items:
        prov_payload = _object_to_plain_dict(prov_item) or {}
        for key in ("bbox", "box", "bounding_box"):
            bbox = _normalize_bbox_value(prov_payload.get(key) or getattr(prov_item, key, None))
            if bbox:
                return bbox
    return None


def _normalize_bbox_value(value: Any) -> Optional[list[float]]:
    payload = _object_to_plain_dict(value)
    if payload:
        for keys in (("l", "t", "r", "b"), ("left", "top", "right", "bottom"), ("x0", "y0", "x1", "y1")):
            if all(key in payload for key in keys):
                try:
                    return [round(float(payload[key]), 3) for key in keys]
                except (TypeError, ValueError):
                    return None
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            return [round(float(item), 3) for item in value]
        except (TypeError, ValueError):
            return None
    return None


def _docling_text_from_item(item: Any) -> str:
    payload = _object_to_plain_dict(item) or {}
    for key in ("text", "caption", "content", "markdown", "html"):
        value = payload.get(key) or getattr(item, key, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if hasattr(item, "export_to_markdown"):
        try:
            markdown = item.export_to_markdown()
            if isinstance(markdown, str) and markdown.strip():
                return markdown.strip()
        except Exception:
            return ""
    return ""


def _docling_item_type(item: Any, fallback: str) -> str:
    payload = _object_to_plain_dict(item) or {}
    raw = (
        payload.get("type")
        or payload.get("label")
        or payload.get("category")
        or getattr(item, "label", None)
        or fallback
    )
    return _normalize_external_block_type(raw)


def structured_extraction_from_docling_document(document: Any, *, source_path: str) -> StructuredPdfExtraction:
    """Normalize a Docling document object into internal structured blocks."""
    blocks: list[StructuredPdfBlock] = []
    page_count = 0

    if hasattr(document, "export_to_dict"):
        try:
            exported = document.export_to_dict()
            external = structured_extraction_from_external_payload(
                exported,
                source_path=source_path,
                parser="docling",
            )
            blocks.extend(external.blocks)
            page_count = max(page_count, external.page_count)
        except Exception as exc:
            logger.warning("Docling dict 导出归一化失败: %s", exc)

    collection_specs = [
        ("texts", "text"),
        ("tables", "table"),
        ("pictures", "visual"),
        ("figures", "visual"),
        ("formulas", "formula"),
        ("groups", "structured"),
    ]
    seen: set[tuple[str, Optional[int], str]] = {
        (block.block_type, block.page, block.text)
        for block in blocks
    }
    for attr, fallback_type in collection_specs:
        items = getattr(document, attr, None)
        if isinstance(items, dict):
            iterable = list(items.values())
        elif isinstance(items, list):
            iterable = items
        else:
            continue
        for item in iterable:
            text = _docling_text_from_item(item)
            if not text:
                continue
            block_type = _docling_item_type(item, fallback_type)
            page = _docling_page_from_item(item)
            bbox = _docling_bbox_from_item(item)
            key = (block_type, page, text[:MAX_STRUCTURED_BLOCK_CHARS])
            if key in seen:
                continue
            seen.add(key)
            metadata = {"docling_collection": attr}
            if bbox:
                metadata["bbox"] = bbox
            blocks.append(StructuredPdfBlock(
                block_type=block_type,
                page=page,
                source="docling",
                text=text[:structured_block_text_limit(block_type)],
                metadata=metadata,
            ))
            if len(blocks) >= MAX_STRUCTURED_BLOCKS:
                break
        if len(blocks) >= MAX_STRUCTURED_BLOCKS:
            break

    if hasattr(document, "export_to_markdown") and len(blocks) < MAX_STRUCTURED_BLOCKS:
        try:
            markdown = document.export_to_markdown()
        except Exception:
            markdown = ""
        if isinstance(markdown, str) and markdown.strip():
            text = markdown.strip()[:MAX_STRUCTURED_BLOCK_CHARS]
            key = ("docling_markdown", None, text)
            if key not in seen:
                blocks.append(StructuredPdfBlock(
                    block_type="docling_markdown",
                    page=None,
                    source="docling",
                    text=text,
                    metadata={"docling_export": "markdown"},
                ))

    pages = getattr(document, "pages", None)
    if isinstance(pages, dict):
        page_count = max(page_count, len(pages))
    elif isinstance(pages, list):
        page_count = max(page_count, len(pages))
    else:
        page_count = max(page_count, max((block.page or 0 for block in blocks), default=0))

    return StructuredPdfExtraction(
        source_path=source_path,
        page_count=page_count,
        blocks=blocks[:MAX_STRUCTURED_BLOCKS],
        parser="docling",
    )


def extract_pdf_structured_content_lightweight(path: str) -> StructuredPdfExtraction:
    """Extract LLM-readable structured PDF blocks with installed parsers."""
    blocks: list[StructuredPdfBlock] = []
    page_count = 0
    parser = "pdfplumber"

    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            for page_number, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                blocks.extend(extract_caption_blocks(page_text, page_number))

                try:
                    tables = page.extract_tables() or []
                except Exception as exc:
                    logger.warning("PDF 第 %s 页表格解析失败: %s", page_number, exc)
                    tables = []

                for table_index, table in enumerate(tables, 1):
                    markdown = table_to_markdown(table)
                    if not markdown:
                        continue
                    blocks.append(StructuredPdfBlock(
                        block_type="table",
                        page=page_number,
                        source="pdfplumber",
                        text=(
                            f"[PDF table, page {page_number}, table {table_index}]\n"
                            f"{markdown}"
                        )[:MAX_STRUCTURED_TABLE_BLOCK_CHARS],
                        metadata={"table_index": table_index},
                    ))
    except Exception as exc:
        logger.warning(f"pdfplumber 结构化解析失败，尝试 fitz 图片检测: {exc}")
        parser = "fitz"

    try:
        import fitz

        doc = fitz.open(path)
        try:
            page_count = page_count or doc.page_count
            for page_index in range(doc.page_count):
                page = doc.load_page(page_index)
                page_number = page_index + 1
                images = page.get_images(full=True) or []
                if images:
                    blocks.append(StructuredPdfBlock(
                        block_type="visual",
                        page=page_number,
                        source="fitz",
                        text=(
                            f"[PDF visual placeholder, page {page_number}] "
                            f"Detected {len(images)} embedded image(s). "
                            "No OCR or pixel-level visual analysis has been performed."
                        ),
                        metadata={"image_count": len(images)},
                    ))
        finally:
            doc.close()
    except Exception as exc:
        logger.warning(f"fitz 图片检测失败: {exc}")

    return StructuredPdfExtraction(
        source_path=path,
        page_count=page_count,
        blocks=blocks[:MAX_STRUCTURED_BLOCKS],
        parser=parser,
    )


def _parser_command_args(path: str) -> list[str]:
    command = str(settings.PDF_STRUCTURED_PARSER_COMMAND or "").strip()
    if not command:
        return []
    args = shlex.split(command)
    return [arg.format(pdf_path=path) for arg in args]


def extract_pdf_structured_content_with_command(path: str) -> StructuredPdfExtraction:
    """Run an optional external parser command and normalize its JSON output."""
    args = _parser_command_args(path)
    if not args:
        raise RuntimeError("PDF_STRUCTURED_PARSER_COMMAND is not configured")

    timeout = max(1.0, float(settings.PDF_STRUCTURED_PARSER_TIMEOUT_SECONDS or 120.0))
    max_output = max(1024, int(settings.PDF_STRUCTURED_PARSER_MAX_OUTPUT_BYTES or 5_000_000))
    completed = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=False,
        timeout=timeout,
        env=parser_subprocess_environment(),
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"advanced parser exited {completed.returncode}: {stderr}")
    if len(completed.stdout) > max_output:
        raise RuntimeError(f"advanced parser output exceeds {max_output} bytes")
    try:
        payload = json.loads(completed.stdout.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"advanced parser returned invalid JSON: {exc}") from exc

    extraction = structured_extraction_from_external_payload(
        payload,
        source_path=path,
        parser="command",
    )
    if not extraction.blocks:
        raise RuntimeError("advanced parser returned no usable structured blocks")
    return extraction


def extract_pdf_structured_content_with_docling(path: str) -> StructuredPdfExtraction:
    """Run optional Docling conversion and normalize its document output."""
    parser_subprocess_environment()
    try:
        from docling.document_converter import DocumentConverter
    except Exception as exc:
        raise RuntimeError(f"Docling is not installed or unavailable: {exc}") from exc

    converter = DocumentConverter()
    result = converter.convert(path)
    document = getattr(result, "document", result)
    extraction = structured_extraction_from_docling_document(document, source_path=path)
    if not extraction.blocks:
        raise RuntimeError("Docling returned no usable structured blocks")
    return extraction


def extract_pdf_structured_content(path: str) -> StructuredPdfExtraction:
    """Extract structured PDF content with optional advanced parser fallback."""
    backend = str(settings.PDF_STRUCTURED_PARSER_BACKEND or "lightweight").strip().lower()
    if backend not in SUPPORTED_PDF_STRUCTURED_BACKENDS:
        logger.warning("未知 PDF 结构化解析后端 %s，使用轻量解析", backend)
        backend = "lightweight"

    extraction: Optional[StructuredPdfExtraction] = None
    if backend in {"docling", "auto"}:
        try:
            extraction = extract_pdf_structured_content_with_docling(path)
        except Exception as exc:
            if backend == "docling":
                logger.warning("Docling PDF 解析失败，回退轻量解析: %s", exc)
            else:
                logger.info("Docling PDF 解析不可用，尝试其他解析后端: %s", exc)
        if extraction:
            return extraction

    if backend in {"command", "auto"}:
        try:
            extraction = extract_pdf_structured_content_with_command(path)
        except Exception as exc:
            if backend == "command":
                logger.warning("高级 PDF 解析失败，回退轻量解析: %s", exc)
            else:
                logger.info("高级 PDF 解析不可用，使用轻量解析: %s", exc)
        if extraction:
            return extraction

    return extract_pdf_structured_content_lightweight(path)


def structured_pdf_metadata_from_paper(paper: Paper) -> Optional[StructuredPdfExtraction]:
    metadata = getattr(paper, "metadata_json", None) or {}
    extraction = StructuredPdfExtraction.from_metadata(metadata.get(PDF_STRUCTURED_METADATA_KEY))
    pdf_path = getattr(paper, "pdf_path", None)
    if extraction and pdf_path and extraction.source_path and extraction.source_path != pdf_path:
        return None
    return extraction


def structured_pdf_evidence_blocks_from_paper(paper: Paper) -> list[dict[str, Any]]:
    extraction = structured_pdf_metadata_from_paper(paper)
    return extraction.to_evidence_blocks() if extraction else []


def structured_pdf_parse_status_from_paper(paper: Paper) -> dict[str, Any]:
    """Return UI/API friendly structured PDF parse status."""
    metadata = getattr(paper, "metadata_json", None) or {}
    payload = metadata.get(PDF_STRUCTURED_METADATA_KEY)
    error = metadata.get(PDF_STRUCTURED_PARSE_ERROR_KEY)
    blocks = payload.get("blocks") if isinstance(payload, dict) else []
    block_counts: dict[str, int] = {}
    parsed_blocks: list[StructuredPdfBlock] = []
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "structured")
            block_counts[block_type] = block_counts.get(block_type, 0) + 1
            if str(block.get("text") or "").strip():
                parsed_blocks.append(StructuredPdfBlock.from_metadata(block))

    pdf_path = getattr(paper, "pdf_path", None)
    source_path = payload.get("source_path") if isinstance(payload, dict) else pdf_path
    source_matches = not pdf_path or not source_path or source_path == pdf_path
    ready = bool(
        isinstance(payload, dict)
        and payload.get("version") == PDF_STRUCTURED_METADATA_VERSION
        and isinstance(blocks, list)
        and source_matches
    )

    return {
        "ready": ready,
        "parser": payload.get("parser") if isinstance(payload, dict) else None,
        "source_path": source_path,
        "page_count": payload.get("page_count") if isinstance(payload, dict) else 0,
        "parsed_at": payload.get("parsed_at") if isinstance(payload, dict) else None,
        "table_count": payload.get("table_count") if isinstance(payload, dict) else block_counts.get("table", 0),
        "caption_count": payload.get("caption_count") if isinstance(payload, dict) else block_counts.get("caption", 0),
        "visual_count": payload.get("visual_count") if isinstance(payload, dict) else block_counts.get("visual", 0),
        "ocr_count": block_counts.get("ocr", 0),
        "formula_count": block_counts.get("formula", 0),
        "block_count": len(blocks) if isinstance(blocks, list) else 0,
        "block_counts": block_counts,
        "table_quality": (
            payload.get("table_quality")
            if isinstance(payload, dict) and isinstance(payload.get("table_quality"), dict)
            else structured_table_quality_from_blocks(parsed_blocks)
        ),
        "parser_health": parser_runtime_health(),
        "last_error": error if isinstance(error, dict) else None,
    }


async def _persist_structured_pdf_metadata(
    paper: Paper,
    metadata: dict[str, Any],
    db: Optional[AsyncSession] = None,
) -> None:
    metadata = sanitize_pdf_storage_value(metadata)
    paper.metadata_json = metadata
    if db is not None:
        await db.execute(update(Paper).where(Paper.id == paper.id).values(metadata_json=metadata))
        return

    try:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as s:
            await s.execute(
                update(Paper).where(Paper.id == paper.id).values(metadata_json=metadata)
            )
            await s.commit()
    except Exception as exc:
        logger.warning("PDF 结构化元数据持久化失败 %s: %s", getattr(paper, "id", ""), exc)


async def persist_paper_pdf_path(
    paper: Paper,
    pdf_path: str,
    db: Optional[AsyncSession] = None,
) -> None:
    """Persist a recovered local PDF path for future parsing/viewing."""
    paper.pdf_path = pdf_path
    if db is not None:
        await db.execute(update(Paper).where(Paper.id == paper.id).values(pdf_path=pdf_path))
        return

    try:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as s:
            await s.execute(update(Paper).where(Paper.id == paper.id).values(pdf_path=pdf_path))
            await s.commit()
    except Exception as exc:
        logger.warning("PDF 路径持久化失败 %s: %s", getattr(paper, "id", ""), exc)


async def resolve_paper_pdf_path(
    paper: Paper,
    db: Optional[AsyncSession] = None,
    *,
    persist: bool = True,
) -> Optional[str]:
    """Return a local PDF path, recovering arXiv cache paths when missing."""
    existing_path = str(getattr(paper, "pdf_path", None) or "").strip()
    if existing_path:
        return existing_path

    arxiv_id = str(getattr(paper, "arxiv_id", None) or "").strip()
    if not arxiv_id:
        return None

    cached_pdf = await ensure_cached_arxiv_pdf(arxiv_id)
    if persist:
        await persist_paper_pdf_path(paper, cached_pdf.path, db)
    else:
        paper.pdf_path = cached_pdf.path
    logger.info("PDF 路径已恢复: %s -> %s", arxiv_id, cached_pdf.path)
    return cached_pdf.path


async def force_structured_pdf_reparse(paper: Paper, db: Optional[AsyncSession] = None) -> dict[str, Any]:
    """Force structured PDF parsing and persist status or latest failure."""
    metadata = dict(getattr(paper, "metadata_json", None) or {})
    try:
        pdf_path = await resolve_paper_pdf_path(paper, db)
        if not pdf_path:
            raise ValueError("PDF 不可用：当前论文没有本地 PDF 路径，也没有可恢复的 arXiv PDF")
        extraction = await asyncio.to_thread(extract_pdf_structured_content, pdf_path)
        metadata[PDF_STRUCTURED_METADATA_KEY] = extraction.to_metadata()
        metadata.pop(PDF_STRUCTURED_PARSE_ERROR_KEY, None)
    except Exception as exc:
        metadata[PDF_STRUCTURED_PARSE_ERROR_KEY] = {
            "message": str(exc)[:1000],
            "parser_backend": settings.PDF_STRUCTURED_PARSER_BACKEND,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        await _persist_structured_pdf_metadata(paper, metadata, db)
        raise

    await _persist_structured_pdf_metadata(paper, metadata, db)
    return structured_pdf_parse_status_from_paper(paper)


async def ensure_structured_pdf_content(paper: Paper) -> Optional[StructuredPdfExtraction]:
    """Return cached structured PDF metadata or lazily parse the local PDF."""
    cached = structured_pdf_metadata_from_paper(paper)
    if cached:
        return cached

    try:
        pdf_path = await resolve_paper_pdf_path(paper)
    except (ArxivPdfCacheError, ValueError) as exc:
        logger.warning("PDF 路径恢复失败 %s: %s", getattr(paper, "arxiv_id", ""), exc)
        return None
    if not pdf_path:
        return None

    try:
        extraction = await asyncio.to_thread(extract_pdf_structured_content, pdf_path)
    except Exception as exc:
        logger.warning("PDF 结构化解析失败 %s: %s", pdf_path, exc)
        return None

    if not extraction.blocks:
        return extraction

    metadata = dict(getattr(paper, "metadata_json", None) or {})
    metadata[PDF_STRUCTURED_METADATA_KEY] = sanitize_pdf_storage_value(extraction.to_metadata())
    paper.metadata_json = metadata
    try:
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as s:
            await s.execute(
                update(Paper).where(Paper.id == paper.id).values(metadata_json=metadata)
            )
            await s.commit()
    except Exception as exc:
        logger.warning(f"PDF 结构化元数据持久化失败 {getattr(paper, 'id', '')}: {exc}")
    return extraction


def extract_pdf_page_texts(path: str) -> list[str]:
    """Extract PDF text page by page for evidence navigation."""
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            return [(page.extract_text() or "").strip() for page in pdf.pages]
    except Exception as exc:
        logger.warning(f"pdfplumber 按页解析失败，尝试 fitz: {exc}")

    try:
        import fitz

        doc = fitz.open(path)
        try:
            return [page.get_text().strip() for page in doc]
        finally:
            doc.close()
    except Exception as exc:
        logger.warning(f"fitz 按页解析失败: {exc}")
        return []


async def _download_and_parse_full_text(paper: Paper) -> str:
    """Download, parse, and persist one paper PDF."""
    clean_id = paper.arxiv_id

    try:
        cached_pdf = await ensure_cached_arxiv_pdf(clean_id)
        paper.pdf_path = cached_pdf.path
        logger.info("PDF 缓存可用: %s (%s)", clean_id, cached_pdf.path)

        # PDF 解析放到线程池，避免阻塞 asyncio 事件循环。
        full_text = sanitize_pdf_storage_value((await asyncio.to_thread(_extract_pdf_text, cached_pdf.path))[:50000])
        if len(full_text.strip()) < 200:
            logger.warning(f"PDF 未提取到有效正文: {clean_id}")
            return paper.abstract or ""

        structured_extraction = await asyncio.to_thread(extract_pdf_structured_content, cached_pdf.path)
        metadata = dict(getattr(paper, "metadata_json", None) or {})
        if structured_extraction.blocks:
            metadata[PDF_STRUCTURED_METADATA_KEY] = sanitize_pdf_storage_value(structured_extraction.to_metadata())
        metadata = sanitize_pdf_storage_value(metadata)

        # 保存到数据库（持久化，避免下次请求重新下载）
        paper.full_text = full_text
        paper.metadata_json = metadata
        try:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as s:
                await s.execute(
                    update(Paper).where(Paper.id == paper.id).values(
                        full_text=full_text,
                        pdf_path=cached_pdf.path,
                        metadata_json=metadata,
                    )
                )
                await s.commit()
        except Exception as exc:
            logger.warning(f"PDF 正文持久化失败 {clean_id}: {exc}")

        logger.info(f"PDF 异步解析完成并持久化: {clean_id} → {len(full_text)} 字符")
        return full_text

    except Exception as e:
        logger.warning(f"PDF 下载/解析失败 {clean_id}: {e}")
        return paper.abstract or ""


class ReportService:
    """组会报告生成。"""

    REPORT_PRESETS = {
        "default": "",
        "compare": "请不要逐篇罗列。请横向比较这些论文的研究问题、方法路线、实验设置、结论差异和适用边界，并给出对比表式的文字总结。",
        "method_lineage": "请按方法演进脉络组织报告，讲清楚从早期思路到最新方案的技术路线变化、每篇论文解决的关键瓶颈和仍未解决的问题。",
        "reproduction": "请从实验复现角度组织报告，重点提取数据集、指标、baseline、关键实现步骤、依赖资源、复现风险和推荐复现顺序。",
        "review": "请按审稿/批判性分析视角组织报告，重点评价创新性、实验充分性、证据强弱、潜在漏洞、可替代解释和可追问问题。",
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    def _custom_prompt_text(self, custom_prompt: str | None) -> str:
        return (custom_prompt or "").strip()[:4000]

    def _combined_report_prompt(self, custom_prompt: str | None, report_preset: str = "default") -> str:
        preset_text = self.REPORT_PRESETS.get(report_preset or "default", "")
        custom_text = self._custom_prompt_text(custom_prompt)
        return "\n\n".join(part for part in [preset_text, custom_text] if part).strip()[:5000]

    def _paper_context(self, paper: Paper, *, full_text_limit: int = 10000) -> str:
        return f"""标题: {paper.title}
作者: {', '.join(paper.authors[:5]) if isinstance(paper.authors, list) else str(paper.authors)[:200]}
年份: {paper.year or 'N/A'}
arXiv: {paper.arxiv_id or 'N/A'}
摘要: {paper.abstract or '无'}
全文: {paper.full_text[:full_text_limit] if paper.full_text else '无全文'}"""

    async def summarize_paper_sections(self, paper: Paper) -> dict:
        """AI 总结论文各个部分（学术深度版）。"""
        prompt = f"""你是一位资深学术研究者，正在撰写详细的论文阅读报告。请基于以下论文内容，进行全面深入的结构化总结。使用学术风格的中文撰写，每个部分充实详细。

{self._paper_context(paper)}

按以下 Markdown 格式严格输出，每个部分 3-5 个要点，每个要点用 `- ` 开头：

## 研究背景与动机
- 要点1：该领域的研究现状
- 要点2：存在的核心问题或挑战
- 要点3：之前的代表性工作及其局限性
- 要点4：本文要解决的关键问题

## 核心方法与技术方案
- 整体架构描述
- 核心技术细节（关键模块、损失函数、训练策略等）
- 与之前方法的本质区别
- 主要创新点

## 实验设计与主要结果
- 使用的数据集/benchmark
- 对比的baseline方法
- 主要实验结果和具体数据指标
- 消融实验揭示的关键结论

## 优势与局限性
- 该方法的优势和亮点
- 存在的局限性或不足
- 不适用的场景

## 启示与后续方向
- 对相关领域的启发
- 值得进一步探索的研究方向
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=2048,
            )

            # 解析 Markdown 格式的各个部分
            sections = {"背景与动机": "", "核心方法": "", "实验结果": "", "优势与局限": "", "启示": ""}
            key_map = {
                "背景": "背景与动机", "研究背景": "背景与动机", "动机": "背景与动机",
                "方法": "核心方法", "核心方法": "核心方法", "技术方案": "核心方法",
                "实验": "实验结果", "结果": "实验结果",
                "优势": "优势与局限", "局限": "优势与局限", "不足": "优势与局限",
                "启示": "启示", "后续": "启示", "方向": "启示",
            }
            current_key = None
            for line in response.split("\n"):
                stripped = line.strip()
                if not stripped:
                    continue
                # 检测 ## 标题
                matched = False
                for kw, mapped in key_map.items():
                    if f"## {kw}" in stripped or f"## {kw}" in stripped.replace(" ", ""):
                        current_key = mapped
                        matched = True
                        break
                if not matched and current_key:
                    sections[current_key] += line + "\n"

            return {k: v.strip() for k, v in sections.items()}
        except Exception as e:
            logger.error(f"论文总结失败: {e}")
            return {"背景与动机": "", "方法": "", "结果": "", "局限": "", "启示": f"总结失败: {str(e)}"}

    async def generate_custom_report(self, papers: list[Paper], title: str, custom_prompt: str) -> str:
        """Generate one report across all selected papers using user-provided instructions."""
        paper_blocks = []
        for index, paper in enumerate(papers, 1):
            paper_blocks.append(f"## 论文 {index}\n{self._paper_context(paper, full_text_limit=6000)}")
        prompt = f"""你是一位资深学术研究者，正在准备组会汇报材料。

报告标题: {title}

用户自定义汇报要求如下。它们优先于默认逐篇论文汇报结构；如果用户要求横向比较、主题式汇报、方法脉络、批判性分析或其他结构，请按用户要求组织。必须基于给定论文资料，不要编造文献不存在的实验或结论。

{custom_prompt}

可用论文资料:

{chr(10).join(paper_blocks)}

请输出一份中文 Markdown 报告。"""
        return await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )

    async def generate_report(
        self,
        paper_ids: List[str],
        title: str = "组会报告",
        custom_prompt: str | None = None,
        report_preset: str = "default",
    ) -> dict:
        """生成组会报告（含结构化总结）。"""
        from uuid import UUID

        papers = []
        for pid in paper_ids:
            try:
                result = await self.session.execute(select(Paper).where(Paper.id == UUID(pid)))
                paper = result.scalar_one_or_none()
                if paper:
                    papers.append(paper)
            except Exception:
                continue

        if not papers:
            return {"error": "未找到论文"}

        # 1. 先并行确保所有论文都有全文
        import asyncio
        await asyncio.gather(*[ensure_full_text(p) for p in papers], return_exceptions=True)
        # 2. commit 全文到 DB
        await self.session.commit()

        custom_prompt_text = self._combined_report_prompt(custom_prompt, report_preset)
        if custom_prompt_text:
            custom_report = await self.generate_custom_report(papers, title, custom_prompt_text)
            return {
                "title": title,
                "papers": [
                    {
                        "title": paper.title,
                        "authors": ", ".join(paper.authors[:5]) if isinstance(paper.authors, list) else str(paper.authors),
                        "year": paper.year,
                        "arxiv_id": paper.arxiv_id,
                        "sections": {},
                    }
                    for paper in papers
                ],
                "paper_count": len(papers),
                "custom_prompt": custom_prompt_text,
                "report_preset": report_preset,
                "custom_report": custom_report,
                "generated_at": str(__import__("datetime").datetime.now()),
            }

        # 3. 并行生成所有论文的结构化总结
        tasks = [self.summarize_paper_sections(p) for p in papers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        report_sections = []
        for paper, sections in zip(papers, results):
            if isinstance(sections, Exception):
                sections = {"背景": "", "方法": "", "结果": "", "分析": f"总结失败: {str(sections)}"}
            report_sections.append({
                "title": paper.title,
                "authors": ", ".join(paper.authors[:5]) if isinstance(paper.authors, list) else str(paper.authors),
                "year": paper.year,
                "arxiv_id": paper.arxiv_id,
                "sections": sections,
            })

        return {
            "title": title,
            "papers": report_sections,
            "paper_count": len(report_sections),
            "generated_at": str(__import__("datetime").datetime.now()),
        }
