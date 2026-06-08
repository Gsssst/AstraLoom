"""组会报告生成服务。"""

import asyncio
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.llm import llm_service
from app.services.arxiv_pdf_cache import ensure_cached_arxiv_pdf
from app.db.models.paper import Paper

logger = logging.getLogger(__name__)
_full_text_tasks: dict[str, asyncio.Task[str]] = {}


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

        # 保存到数据库（持久化，避免下次请求重新下载）
        paper.full_text = full_text
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import update
            async with AsyncSessionLocal() as s:
                await s.execute(
                    update(Paper).where(Paper.id == paper.id).values(
                        full_text=full_text,
                        pdf_path=cached_pdf.path,
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
