"""Reader Agent — 深度阅读论文，提取结构化信息到工作记忆。

参考 Full_Text_RWG 的 Reader: 全文深度阅读 -> 提取(问题/方法/结果/关系) -> 写入共享记忆。
"""

import asyncio
import json
import logging
from typing import AsyncIterator

from app.services.agents import BaseAgent
from app.services.writing_pipeline import PipelineEvent

logger = logging.getLogger(__name__)


class ReaderAgent(BaseAgent):
    """阅读器 Agent — 深度阅读指定论文，提取关键信息。"""

    @property
    def name(self) -> str:
        return "Reader"

    async def execute(self, memory, cancel_event=None) -> AsyncIterator[PipelineEvent]:
        self._check_cancelled(cancel_event)

        papers = memory.papers
        strategy = memory.metadata.get("reading_strategy", {})
        full_indices = strategy.get("full_read_indices", [])

        if not papers:
            yield PipelineEvent("status", phase="reader",
                                content="无待阅读论文")
            return

        total = len(papers)
        reading_notes = []
        paper_relations = []

        for i, paper in enumerate(papers):
            self._check_cancelled(cancel_event)
            paper_idx = i + 1

            is_full_read = paper_idx in full_indices
            read_mode = "精读全文" if is_full_read else "略读摘要"

            yield PipelineEvent("status", phase="reader",
                                content=f"[{paper_idx}/{total}] {read_mode}: {paper['title'][:60]}...")

            # 获取全文（精读模式）
            full_text = None
            if is_full_read and paper.get("id"):
                full_text = await self._load_full_text(paper["id"])

            # 提取结构化信息
            notes = await self._extract_paper_info(paper, full_text, is_full_read)
            notes["index"] = paper_idx
            reading_notes.append(notes)

            yield PipelineEvent("status", phase="reader",
                                content=f"✓ [{paper_idx}/{total}] {paper['title'][:40]}... 完成")

        # 论文关系分析
        if len(papers) >= 2 and self.llm:
            yield PipelineEvent("status", phase="reader", content="正在分析论文间关系...")
            paper_relations = await self._analyze_relations(reading_notes)
            yield PipelineEvent("status", phase="reader",
                                content=f"已识别 {len(paper_relations)} 条论文关系")

        memory.reading_notes = reading_notes
        memory.paper_relations = paper_relations

    async def _load_full_text(self, paper_id: str) -> str | None:
        """加载论文全文。"""
        try:
            from sqlalchemy import select
            from app.db.session import AsyncSessionLocal
            from app.db.models.paper import Paper
            from uuid import UUID

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Paper).where(Paper.id == UUID(paper_id))
                )
                paper = result.scalar_one_or_none()
                if paper and paper.full_text:
                    return paper.full_text[:8000]
        except Exception as e:
            logger.warning(f"加载全文失败 {paper_id}: {e}")
        return None

    async def _extract_paper_info(self, paper: dict, full_text: str | None,
                                   is_full_read: bool) -> dict:
        """提取论文的结构化信息。"""
        if not self.llm:
            return {
                "title": paper["title"],
                "problem": paper["abstract"][:200] if paper["abstract"] else "",
                "method": "",
                "results": "",
                "read_mode": "abstract_only" if not is_full_read else "full_text",
            }

        content = full_text[:3000] if full_text else paper.get("abstract", "")[:1000]
        prompt = f"""## 任务
{'深度' if is_full_read else '快速'}阅读以下论文，提取结构化信息。

## 论文
标题: {paper['title']}
作者: {paper.get('authors', '')}
年份: {paper.get('year', '')}
内容: {content[:3000]}

## 输出格式
严格输出 JSON：
{{"problem": "核心研究问题 (1-2句)", "method": "提出的方法/模型 (2-3句)", "results": "关键实验结果或贡献 (1-2句)", "limitations": "局限性 (简短)", "relationship_to_topic": "与研究主题的关系"}}
"""
        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1024,
            )
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                info = json.loads(response[start:end])
                info["title"] = paper["title"]
                info["read_mode"] = "full_text" if is_full_read else "abstract_only"
                return info
        except Exception as e:
            logger.warning(f"论文信息提取失败: {e}")

        return {
            "title": paper["title"],
            "problem": paper.get("abstract", "")[:200],
            "method": "",
            "results": "",
            "read_mode": "abstract_only" if not is_full_read else "full_text",
        }

    async def _analyze_relations(self, reading_notes: list) -> list:
        """分析论文间的关系。"""
        papers_text = "\n".join([
            f"[{n['index']}] {n.get('title', '')}: {n.get('method', '')[:200]}"
            for n in reading_notes
        ])

        prompt = f"""## 任务
分析以下论文之间的关系。对每对相关论文，标注关系类型。

## 论文
{papers_text}

## 关系类型
- cites: A 引用 B
- extends: A 扩展/改进 B 的方法
- contrasts: A 提出替代方案与 B 对比
- contemporary: 同年、类似方向

## 输出格式
严格输出 JSON 数组：
[{{"from": 论文索引, "to": 论文索引, "relation": "关系类型", "description": "一句话说明"}}, ...]
如果没有明确关系，输出空数组 []。
"""
        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1024,
            )
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except Exception as e:
            logger.warning(f"论文关系分析失败: {e}")
        return []
