"""论文增强服务 — 自动标签提取、论文问答、相似推荐。"""

import logging
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.services.llm import llm_service
from app.services.rag_service import RAGService
from app.db.models.paper import Paper, UserPaper

logger = logging.getLogger(__name__)


class PaperEnhanceService:
    """论文增强服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def auto_tag_paper(self, paper: Paper) -> List[str]:
        """AI 自动从摘要提取关键词标签。"""
        if paper.tags:
            return paper.tags

        prompt = f"""从以下学术论文的标题和摘要中提取 5-8 个英文关键词标签。
返回一个 JSON 字符串数组，如 ["keyword1", "keyword2", ...]。
只返回 JSON 数组，不要其他内容。

标题: {paper.title}
摘要: {paper.abstract[:800] if paper.abstract else ''}
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=256,
            )
            # 解析 JSON
            text = response.strip()
            if "```" in text:
                text = text.split("```")[1].replace("json", "").strip()
            tags = json.loads(text)
            if isinstance(tags, list):
                paper.tags = tags
                await self.session.commit()
                logger.info(f"论文 '{paper.title[:40]}...' 标签: {tags}")
                return tags
        except Exception as e:
            logger.warning(f"自动标签提取失败: {e}")

        # 回退：从标题和摘要中提取常见词
        default_tags = []
        if paper.abstract:
            common_terms = ["transformer", "attention", "language model", "neural network",
                          "deep learning", "reinforcement", "embedding", "convolution",
                          "generative", "diffusion", "alignment", "fine-tuning"]
            text_lower = (paper.title + " " + paper.abstract[:500]).lower()
            default_tags = [t for t in common_terms if t in text_lower][:5]

        if default_tags:
            paper.tags = default_tags
            await self.session.commit()

        return paper.tags or []

    async def auto_tag_all(self) -> dict:
        """为所有未标记的论文生成标签。"""
        result = await self.session.execute(
            select(Paper).where(Paper.tags.is_(None) | (func.json_array_length(Paper.tags) == 0)).limit(20)
        )
        papers = result.scalars().all()
        tagged = 0
        for paper in papers:
            tags = await self.auto_tag_paper(paper)
            if tags:
                tagged += 1
        return {"total": len(papers), "tagged": tagged}

    async def ask_about_paper(
        self,
        paper: Paper,
        question: str,
        conversation_history: list | None = None,
    ) -> str:
        """针对某篇论文进行 AI 问答。"""
        context = f"""## 论文信息
标题: {paper.title}
作者: {', '.join(paper.authors[:10]) if isinstance(paper.authors, list) else paper.authors or '未知'}
年份: {paper.year or 'N/A'}
arXiv ID: {paper.arxiv_id or 'N/A'}

摘要:
{paper.abstract or '无'}

全文片段:
{paper.full_text[:3000] if paper.full_text else '全文暂不可用（PDF 尚未下载或解析）'}
"""

        messages = [
            {"role": "system", "content": f"你是这篇论文的专家助手。请基于以下论文内容回答用户问题。如果问题超出论文范围，可以结合你的知识补充，但要明确区分。\n\n{context}"},
        ]

        if conversation_history:
            messages.extend(conversation_history[-6:])

        messages.append({"role": "user", "content": question})

        response = await llm_service.chat(
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
        )
        return response

    async def similar_papers(self, paper: Paper, top_k: int = 5) -> List[Paper]:
        """推荐相似论文（基于向量距离）。"""
        if paper.embedding is None:
            return []

        try:
            similar = await self.session.execute(
                select(Paper)
                .where(Paper.id != paper.id, Paper.embedding.is_not(None))
                .order_by(Paper.embedding.cosine_distance(paper.embedding))
                .limit(top_k)
            )
            return list(similar.scalars().all())
        except Exception as e:
            logger.warning(f"相似论文查询失败: {e}")
            return []

    async def get_user_paper(self, user_id: str, paper_id: str) -> UserPaper | None:
        """获取用户对论文的个人状态。"""
        from uuid import UUID
        result = await self.session.execute(
            select(UserPaper).where(
                UserPaper.user_id == UUID(user_id),
                UserPaper.paper_id == UUID(paper_id),
            )
        )
        return result.scalar_one_or_none()

    async def save_paper(self, user_id: str, paper_id: str) -> UserPaper:
        """收藏论文。"""
        from uuid import UUID
        up = await self.get_user_paper(user_id, paper_id)
        if up:
            up.saved = True
        else:
            up = UserPaper(
                user_id=UUID(user_id), paper_id=UUID(paper_id),
                saved=True, read_status="unread",
            )
            self.session.add(up)
        await self.session.commit()
        return up

    async def unsave_paper(self, user_id: str, paper_id: str) -> None:
        """取消收藏。"""
        up = await self.get_user_paper(user_id, paper_id)
        if up:
            up.saved = False
            await self.session.commit()

    async def update_note(self, user_id: str, paper_id: str, note: str) -> UserPaper:
        """更新个人笔记。"""
        from uuid import UUID
        up = await self.get_user_paper(user_id, paper_id)
        if not up:
            up = UserPaper(user_id=UUID(user_id), paper_id=UUID(paper_id), saved=True)
            self.session.add(up)
        up.personal_notes = note
        await self.session.commit()
        return up

    async def get_saved_papers(self, user_id: str) -> List[Paper]:
        """获取用户收藏的论文列表。"""
        from uuid import UUID
        result = await self.session.execute(
            select(Paper)
            .join(UserPaper, (UserPaper.paper_id == Paper.id) & (UserPaper.user_id == UUID(user_id)))
            .where(UserPaper.saved == True)
            .order_by(UserPaper.created_at.desc())
        )
        return list(result.scalars().all())
