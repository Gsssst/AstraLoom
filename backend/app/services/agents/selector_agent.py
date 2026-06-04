"""Selector Agent — 分析用户写作意图，选择检索策略，输出论文阅读计划。

参考 Full_Text_RWG 的 Selector: 按技术路线分组、决定全读/略读策略。
"""

import asyncio
import json
import logging
from typing import AsyncIterator

from app.services.agents import BaseAgent
from app.services.writing_pipeline import PipelineEvent

logger = logging.getLogger(__name__)


class SelectorAgent(BaseAgent):
    """选择器 Agent — 分析写作需求，制定论文阅读策略。"""

    @property
    def name(self) -> str:
        return "Selector"

    async def execute(self, memory, cancel_event=None) -> AsyncIterator[PipelineEvent]:
        self._check_cancelled(cancel_event)

        task_type = memory.metadata.get("task_type", "related_work")
        input_data = memory.metadata.get("input", {})
        topic = input_data.get("topic", "") or input_data.get("text", "")

        if not topic:
            yield PipelineEvent("error", phase="selector",
                                content={"message": "无法确定研究主题"})
            return

        # Step 1: 从知识库检索相关论文
        yield PipelineEvent("status", phase="selector",
                            content="正在检索相关论文...")

        papers = await self._retrieve_papers(topic, task_type)
        if not papers:
            yield PipelineEvent("status", phase="selector",
                                content="知识库中暂无相关论文，将基于模型知识生成")
            memory.papers = []
            return

        memory.papers = papers
        yield PipelineEvent("status", phase="selector",
                            content=f"找到 {len(papers)} 篇相关论文")

        # Step 2: 按技术路线分类
        if len(papers) >= 3 and self.llm:
            yield PipelineEvent("status", phase="selector",
                                content="正在分析论文技术路线...")
            groups = await self._classify_papers(papers, topic)
            memory.metadata["paper_groups"] = groups
            yield PipelineEvent("status", phase="selector",
                                content=f"已识别 {len(groups)} 个技术方向")

        # Step 3: 决定阅读策略
        strategy = self._decide_reading_strategy(papers, task_type)
        memory.metadata["reading_strategy"] = strategy
        yield PipelineEvent("status", phase="selector",
                            content=f"阅读策略: {strategy['full_read']} 篇精读, "
                                    f"{strategy['skim']} 篇略读")

    async def _retrieve_papers(self, topic: str, task_type: str) -> list:
        """从知识库检索相关论文。"""
        if not self.db_factory:
            return []

        try:
            from app.db.session import AsyncSessionLocal
            from app.services.rag_service import RAGService

            top_k = 10 if task_type in ("literature_review", "related_work", "full_chapter") else 5

            async with AsyncSessionLocal() as session:
                rag = RAGService(session)
                results = await rag.search_similar(topic, top_k=top_k)
                return [
                    {
                        "id": str(p.id),
                        "title": p.title,
                        "authors": ", ".join(p.authors[:5]) if isinstance(p.authors, list) else str(p.authors),
                        "year": p.year,
                        "abstract": p.abstract[:400] if p.abstract else "",
                        "arxiv_id": p.arxiv_id,
                        "similarity": round(score, 4),
                        "has_full_text": bool(p.full_text),
                    }
                    for p, score in results
                ]
        except Exception as e:
            logger.warning(f"论文检索失败: {e}")
            return []

    async def _classify_papers(self, papers: list, topic: str) -> list:
        """使用 LLM 将论文按技术路线分类。"""
        papers_text = "\n".join([
            f"[{i+1}] {p['title']} ({p['year']}): {p['abstract'][:200]}"
            for i, p in enumerate(papers)
        ])

        prompt = f"""## 任务
将以下论文按技术路线分为 2-3 组。每组包含技术路线相似的论文。

## 研究主题
{topic}

## 论文列表
{papers_text}

## 输出格式
严格输出 JSON 数组：
[{{"group_name": "技术路线名称", "description": "一句话描述", "paper_indices": [1, 3, 5]}}, ...]
"""
        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1024,
            )
            # 提取 JSON
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except Exception as e:
            logger.warning(f"论文分类失败: {e}")
        return [{"group_name": "相关研究", "paper_indices": list(range(1, len(papers) + 1))}]

    def _decide_reading_strategy(self, papers: list, task_type: str) -> dict:
        """根据任务类型和论文数量决定阅读策略。"""
        total = len(papers)
        if total <= 3:
            return {"full_read": total, "skim": 0, "full_read_indices": list(range(1, total + 1))}

        if task_type in ("related_work", "full_chapter"):
            full_read = min(total, 5)
        elif task_type == "literature_review":
            full_read = min(total, 8)
        else:
            full_read = min(total, 3)

        # 优先精读高相似度 + 有全文的论文
        sorted_papers = sorted(
            enumerate(papers, 1),
            key=lambda x: (x[1]["has_full_text"], x[1]["similarity"]),
            reverse=True,
        )
        full_indices = [i for i, _ in sorted_papers[:full_read]]

        return {"full_read": full_read, "skim": total - full_read, "full_read_indices": full_indices}
