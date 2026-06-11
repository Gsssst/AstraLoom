"""组会报告生成服务。"""

import asyncio
import json
import logging
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.services.llm import llm_service
from app.services.arxiv_pdf_cache import ensure_cached_arxiv_pdf
from app.db.models.paper import Paper

logger = logging.getLogger(__name__)
_full_text_tasks: dict[str, asyncio.Task[str]] = {}
PDF_STRUCTURED_METADATA_KEY = "pdf_structured_content"
PDF_STRUCTURED_METADATA_VERSION = 1
MAX_STRUCTURED_BLOCKS = 80
MAX_STRUCTURED_BLOCK_CHARS = 1800
MAX_STRUCTURED_TABLE_ROWS = 40
MAX_STRUCTURED_TABLE_COLS = 12
SUPPORTED_PDF_STRUCTURED_BACKENDS = {"lightweight", "command", "auto"}


@dataclass
class StructuredPdfBlock:
    """A page-aware PDF block that can be used as retrieval evidence."""

    block_type: str
    text: str
    page: Optional[int] = None
    source: str = "pdfplumber"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "type": self.block_type,
            "page": self.page,
            "source": self.source,
            "text": self.text[:MAX_STRUCTURED_BLOCK_CHARS],
            "metadata": self.metadata,
        }

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

    def to_metadata(self) -> dict[str, Any]:
        bounded_blocks = self.blocks[:MAX_STRUCTURED_BLOCKS]
        return {
            "version": self.version,
            "source_path": self.source_path,
            "parser": self.parser,
            "page_count": self.page_count,
            "table_count": self.table_count,
            "caption_count": self.caption_count,
            "visual_count": self.visual_count,
            "blocks": [block.to_metadata() for block in bounded_blocks],
        }

    def to_evidence_blocks(self) -> list[dict[str, Any]]:
        return [
            {
                "type": block.block_type,
                "page": block.page,
                "source": block.source,
                "text": block.text,
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
    """Convert a pdfplumber table into compact Markdown."""
    rows = [
        [_clean_table_cell(cell) for cell in row[:MAX_STRUCTURED_TABLE_COLS]]
        for row in table[:MAX_STRUCTURED_TABLE_ROWS]
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
    if len(table) > MAX_STRUCTURED_TABLE_ROWS:
        lines.append(f"\n_Table truncated to first {MAX_STRUCTURED_TABLE_ROWS} rows._")
    return "\n".join(lines).strip()


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
            return value.strip()
    table = item.get("table")
    if isinstance(table, list):
        return table_to_markdown(table)
    return ""


def _iter_external_parser_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("blocks", "elements", "chunks", "items"):
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
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        blocks.append(StructuredPdfBlock(
            block_type=_normalize_external_block_type(raw_type),
            page=page,
            source=parser,
            text=text[:MAX_STRUCTURED_BLOCK_CHARS],
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
                        )[:MAX_STRUCTURED_BLOCK_CHARS],
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


def extract_pdf_structured_content(path: str) -> StructuredPdfExtraction:
    """Extract structured PDF content with optional advanced parser fallback."""
    backend = str(settings.PDF_STRUCTURED_PARSER_BACKEND or "lightweight").strip().lower()
    if backend not in SUPPORTED_PDF_STRUCTURED_BACKENDS:
        logger.warning("未知 PDF 结构化解析后端 %s，使用轻量解析", backend)
        backend = "lightweight"

    if backend in {"command", "auto"}:
        try:
            return extract_pdf_structured_content_with_command(path)
        except Exception as exc:
            if backend == "command":
                logger.warning("高级 PDF 解析失败，回退轻量解析: %s", exc)
            else:
                logger.info("高级 PDF 解析不可用，使用轻量解析: %s", exc)

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


async def ensure_structured_pdf_content(paper: Paper) -> Optional[StructuredPdfExtraction]:
    """Return cached structured PDF metadata or lazily parse the local PDF."""
    cached = structured_pdf_metadata_from_paper(paper)
    if cached:
        return cached

    pdf_path = getattr(paper, "pdf_path", None)
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
    metadata[PDF_STRUCTURED_METADATA_KEY] = extraction.to_metadata()
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
        full_text = (await asyncio.to_thread(_extract_pdf_text, cached_pdf.path))[:50000]
        if len(full_text.strip()) < 200:
            logger.warning(f"PDF 未提取到有效正文: {clean_id}")
            return paper.abstract or ""

        structured_extraction = await asyncio.to_thread(extract_pdf_structured_content, cached_pdf.path)
        metadata = dict(getattr(paper, "metadata_json", None) or {})
        if structured_extraction.blocks:
            metadata[PDF_STRUCTURED_METADATA_KEY] = structured_extraction.to_metadata()

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
