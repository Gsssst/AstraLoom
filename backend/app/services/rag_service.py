"""RAG 服务 — 向量语义搜索 + 检索增强生成。"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.paper import Paper
from app.db.session import AsyncSessionLocal
from app.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)


class RAGService:
    """检索增强生成服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        use_hybrid: bool = True,
    ) -> List[Tuple[Paper, float]]:
        """语义搜索：混合检索（BM25 + Dense）+ 重排序。"""

        from app.services.hybrid_search import HybridSearchService, RerankService

        # 混合检索
        hs = HybridSearchService(self.session)
        scored = await hs.search_hybrid(query, top_k=top_k * 2)
        papers_with_scores = await hs.fetch_papers(scored)

        # Cross-Encoder 重排序
        if len(papers_with_scores) > top_k and use_hybrid:
            try:
                reranker = RerankService()
                papers = [p for p, _ in papers_with_scores]
                papers_with_scores = await reranker.rerank(query, papers, top_k=top_k)
            except Exception as e:
                logger.warning(f"重排序失败，使用原始结果: {e}")

        # 过滤低分
        result = [(p, s) for p, s in papers_with_scores[:top_k] if s >= similarity_threshold]
        logger.info(f"混合搜索: '{query[:50]}...' → {len(result)} 篇")
        return result

    async def search_keyword_and_semantic(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Tuple[Paper, float]]:
        """混合搜索：关键词 + 语义，合并结果。"""
        # 关键词搜索
        kw_result = await self.session.execute(
            select(Paper).where(
                Paper.title.ilike(f"%{query}%") | Paper.abstract.ilike(f"%{query}%")
            ).limit(top_k)
        )
        keyword_papers = {p.id: p for p in kw_result.scalars().all()}

        # 语义搜索
        semantic_results = await self.search_similar(query, top_k=top_k)

        # 合并（语义结果优先，去重）
        seen_ids = set()
        merged = []

        for paper, score in semantic_results:
            if paper.id not in seen_ids:
                merged.append((paper, score))
                seen_ids.add(paper.id)

        for paper in keyword_papers.values():
            if paper.id not in seen_ids:
                merged.append((paper, 0.0))
                seen_ids.add(paper.id)

        return merged[:top_k]

    async def build_rag_context(
        self,
        query: str,
        max_papers: int = 3,
        max_chars: int = 3000,
    ) -> str:
        """为 RAG 构建注入了相关论文的上下文字符串。"""
        results = await self.search_similar(query, top_k=max_papers)

        if not results:
            return ""

        context_parts = ["\n\n--- 相关论文上下文 ---\n"]
        total_chars = 0

        for i, (paper, score) in enumerate(results, 1):
            snippet = f"""
[{i}] {paper.title} ({paper.year or 'N/A'})
    作者: {', '.join(paper.authors[:3]) if isinstance(paper.authors, list) else paper.authors or '未知'}
    arXiv: {paper.arxiv_id or 'N/A'}
    相似度: {score:.2%}
    摘要: {paper.abstract[:500] if paper.abstract else '暂无摘要'}
"""
            if total_chars + len(snippet) > max_chars:
                break
            context_parts.append(snippet)
            total_chars += len(snippet)

        context_parts.append("--- 请基于以上论文回答用户问题，引用时请注明论文编号 ---\n")
        return "".join(context_parts)

    async def generate_embeddings_for_paper(self, paper: Paper) -> bool:
        """为单篇论文生成并存储向量嵌入。"""
        if paper.embedding is not None:
            return True  # 已有嵌入

        paper_title = paper.title[:50] if paper.title else "unknown"
        text_for_embedding = f"Title: {paper.title}\n\nAbstract: {paper.abstract or ''}"
        try:
            embedding = await generate_embedding(text_for_embedding)
            paper.embedding = embedding
            await self.session.commit()
            logger.info(f"论文嵌入已生成: {paper_title}...")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"论文嵌入生成失败 ({paper_title}): {e}")
            return False

    async def generate_embeddings_for_all(self) -> dict:
        """为所有未嵌入的论文生成向量。"""
        result = await self.session.execute(
            select(Paper).where(Paper.embedding.is_(None)).limit(50)
        )
        papers = result.scalars().all()

        success = 0
        for paper in papers:
            if await self.generate_embeddings_for_paper(paper):
                success += 1

        return {"total": len(papers), "success": success, "failed": len(papers) - success}


async def get_rag_service(db: AsyncSession) -> RAGService:
    return RAGService(db)
