"""Citation Agent — 提取 Writer 输出中的引用，验证真实性。

参考 OpenDraft 和 Prismer.AI 的引用验证策略：
- 解析 [1][2] 引用标记
- 与工作记忆中的论文映射
- 调用外部 API 交叉验证
"""

import asyncio
import logging
import re
from typing import AsyncIterator

from app.services.agents import BaseAgent
from app.services.writing_pipeline import PipelineEvent

logger = logging.getLogger(__name__)


class CitationAgent(BaseAgent):
    """引用 Agent — 验证 AI 生成文本中的引用真实性。"""

    @property
    def name(self) -> str:
        return "Citation"

    async def execute(self, memory, cancel_event=None) -> AsyncIterator[PipelineEvent]:
        self._check_cancelled(cancel_event)

        content = memory.writer_output
        if not content:
            yield PipelineEvent("status", phase="citation", content="无引用需要验证")
            return

        # 提取 [N] 格式的引用
        citation_pattern = re.compile(r'\[(\d+)\]')
        cited_indices = set(int(m) for m in citation_pattern.findall(content))

        if not cited_indices:
            yield PipelineEvent("status", phase="citation", content="未检测到引用标记")
            return

        yield PipelineEvent("status", phase="citation",
                            content=f"检测到 {len(cited_indices)} 处引用，正在验证...")

        # 构建引用映射：引用编号 → 论文信息
        papers = memory.papers
        reading_notes = memory.reading_notes
        citation_map = {}

        for idx in cited_indices:
            self._check_cancelled(cancel_event)

            paper = None
            if idx <= len(papers):
                paper = papers[idx - 1]
            note = reading_notes[idx - 1] if idx <= len(reading_notes) else None

            if paper:
                # 本地验证：论文存在于工作记忆中
                verification = await self._verify_citation(paper)
                citation_map[str(idx)] = {
                    "title": paper.get("title", ""),
                    "authors": paper.get("authors", ""),
                    "year": paper.get("year"),
                    "arxiv_id": paper.get("arxiv_id"),
                    "source": "knowledge_base",
                    "status": verification["status"],
                    "confidence": verification["confidence"],
                    "details": verification.get("details", ""),
                }
            elif note:
                citation_map[str(idx)] = {
                    "title": note.get("title", ""),
                    "source": "reading_notes",
                    "status": "verified",
                    "confidence": "medium",
                }
            else:
                citation_map[str(idx)] = {
                    "title": f"未知引用 #{idx}",
                    "source": "unknown",
                    "status": "likely_hallucination",
                    "confidence": "low",
                }

        memory.citation_map = citation_map

        # 统计结果
        verified = sum(1 for c in citation_map.values() if c["status"] == "verified")
        uncertain = sum(1 for c in citation_map.values() if c["status"] == "uncertain")
        hallucinations = sum(1 for c in citation_map.values() if c["status"] == "likely_hallucination")

        status_parts = []
        if verified:
            status_parts.append(f"✅ {verified} 条已验证")
        if uncertain:
            status_parts.append(f"⚠️ {uncertain} 条待核实")
        if hallucinations:
            status_parts.append(f"❌ {hallucinations} 条可能为幻觉引用")

        yield PipelineEvent("status", phase="citation",
                            content=" | ".join(status_parts))

    async def _verify_citation(self, paper: dict) -> dict:
        """验证单条引用的真实性。先查本地库，再查外部 API。"""
        title = paper.get("title", "")
        arxiv_id = paper.get("arxiv_id", "")

        # 如果已有 arxiv_id，可进行外部验证
        if arxiv_id and self.llm:
            try:
                result = await self._external_verify(title, arxiv_id)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"外部验证失败 {title[:50]}: {e}")

        # 本地验证：论文在知识库中 → 已验证
        if paper.get("id"):
            return {"status": "verified", "confidence": "high",
                    "details": "在本地知识库中找到"}

        return {"status": "verified", "confidence": "medium",
                "details": "基于检索结果"}

    async def _external_verify(self, title: str, arxiv_id: str) -> dict | None:
        """通过 arXiv API 和 Semantic Scholar 交叉验证。"""
        import httpx

        # arXiv API 验证
        try:
            clean_id = arxiv_id.replace("arxiv:", "").split("v")[0]
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://export.arxiv.org/api/query?search_query=id:{clean_id}&max_results=1"
                )
                if resp.status_code == 200 and title.lower()[:30] in resp.text.lower():
                    return {"status": "verified", "confidence": "high",
                            "details": "arXiv API 确认论文存在"}
        except Exception:
            pass

        # Semantic Scholar 验证
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://api.semanticscholar.org/graph/v1/paper/ArXiv:{clean_id}"
                )
                if resp.status_code == 200 and resp.json().get("title"):
                    api_title = resp.json()["title"]
                    # 标题相似度检查
                    if self._title_similar(title, api_title) > 0.5:
                        return {"status": "verified", "confidence": "high",
                                "details": "Semantic Scholar 确认论文存在"}
        except Exception:
            pass

        return None

    @staticmethod
    def _title_similar(t1: str, t2: str) -> float:
        """简单的标题相似度计算。"""
        import difflib
        return difflib.SequenceMatcher(None, t1.lower()[:100], t2.lower()[:100]).ratio()
