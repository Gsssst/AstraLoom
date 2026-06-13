"""论文入库管道 — 元数据提取、去重、存储。"""

import logging
from typing import List, Optional
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
import difflib

from app.db.models.paper import Paper, Category, PaperCategory
from app.db.session import AsyncSessionLocal
from app.services.paper_search import (
    PaperResult,
    resolve_remote_paper,
    search_scholarly_papers,
)

logger = logging.getLogger(__name__)


class PaperIngestionService:
    """论文入库服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_duplicate(self, paper: PaperResult) -> Optional[Paper]:
        """三级去重检查：arXiv ID → DOI → 标题相似度。

        返回 None 表示不重复，返回 Paper 对象表示已存在。
        """
        # Level 1: arXiv ID 精确匹配
        if paper.arxiv_id:
            result = await self.session.execute(
                select(Paper).where(Paper.arxiv_id == paper.arxiv_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.info(f"去重（arXiv ID）: {paper.arxiv_id}")
                return existing

        # Level 2: DOI 精确匹配
        if paper.doi:
            result = await self.session.execute(
                select(Paper).where(Paper.doi == paper.doi)
            )
            existing = result.scalar_one_or_none()
            if existing:
                logger.info(f"去重（DOI）: {paper.doi}")
                return existing

        # Level 3: 标题相似度模糊匹配
        result = await self.session.execute(select(Paper))
        all_papers = result.scalars().all()

        paper_title = paper.title.lower().strip()
        for existing in all_papers:
            existing_title = existing.title.lower().strip()
            similarity = difflib.SequenceMatcher(
                None, paper_title, existing_title
            ).ratio()
            if similarity > 0.85:
                logger.info(
                    f"去重（标题相似度 {similarity:.2f}）: '{paper.title[:50]}...' ≈ '{existing.title[:50]}...'"
                )
                return existing

        return None

    async def ingest_paper(
        self,
        paper: PaperResult,
        auto_download: bool = True,
        imported_by_user=None,
    ) -> tuple[Optional[Paper], bool]:
        """入库单篇论文。

        Returns:
            (Paper, is_new): Paper 对象和是否为新入库
        """
        # 去重
        existing = await self.check_duplicate(paper)
        if existing:
            # 更新引用计数等动态字段
            metadata_changed = False
            if paper.citation_count > existing.citation_count:
                existing.citation_count = paper.citation_count
                metadata_changed = True
            if paper.pdf_url and not (existing.metadata_json or {}).get("pdf_url"):
                existing.metadata_json = {**(existing.metadata_json or {}), "pdf_url": paper.pdf_url}
                metadata_changed = True
            if metadata_changed:
                await self.session.commit()
            return existing, False

        # 创建新论文记录
        metadata_json = {
            **(paper.metadata or {}),
            **({"pdf_url": paper.pdf_url} if paper.pdf_url else {}),
        }
        new_paper = Paper(
            title=paper.title,
            authors=paper.authors,
            year=paper.year,
            abstract=paper.abstract,
            doi=paper.doi,
            arxiv_id=paper.arxiv_id,
            source=paper.source,
            source_url=paper.source_url,
            citation_count=paper.citation_count,
            metadata_json=metadata_json,
            imported_by_user_id=getattr(imported_by_user, "id", None) if imported_by_user else None,
            imported_by_username=self._importer_username(imported_by_user),
        )

        self.session.add(new_paper)
        await self.session.commit()
        await self.session.refresh(new_paper)
        from app.services.hybrid_search import invalidate_bm25_index
        invalidate_bm25_index()

        # 自动创建 arXiv 分类
        if paper.categories:
            await self._assign_categories(new_paper, paper.categories)

        # 提交入库后自动处理任务：全文、结构化解析、视觉证据/OCR、向量和检索索引。
        await self.enqueue_processing(new_paper)

        logger.info(f"新论文入库: {paper.title[:80]}... ({paper.arxiv_id or paper.doi})")
        return new_paper, True

    async def ingest_batch(
        self,
        papers: List[PaperResult],
        auto_download: bool = True,
        imported_by_user=None,
    ) -> dict:
        """批量入库论文。

        Returns:
            {"success": int, "skipped": int, "error": int, "paper_ids": [...], "errors": [...]}
        """
        result = {"success": 0, "skipped": 0, "error": 0, "paper_ids": [], "errors": []}

        for paper in papers:
            try:
                ingested, is_new = await self.ingest_paper(
                    paper,
                    auto_download=auto_download,
                    imported_by_user=imported_by_user,
                )
                if ingested:
                    result["paper_ids"].append(str(ingested.id))
                if is_new:
                    result["success"] += 1
                else:
                    result["skipped"] += 1
            except Exception as e:
                logger.error(f"论文入库失败 '{paper.title[:50]}...': {e}")
                result["error"] += 1
                result["errors"].append({"title": paper.title, "error": str(e)})

        return result

    async def search_and_ingest(
        self,
        query: str,
        max_results: int = 20,
        source: str = "arxiv",
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        auto_download: bool = True,
        imported_by_user=None,
    ) -> dict:
        """搜索论文并自动入库。"""
        papers = await search_scholarly_papers(
            query=query,
            source=source,
            max_results=max_results,
            year_from=year_from,
            year_to=year_to,
        )

        if not papers:
            return {"success": 0, "skipped": 0, "error": 0, "paper_ids": [], "errors": [], "total_found": 0}

        result = await self.ingest_batch(papers, auto_download=auto_download, imported_by_user=imported_by_user)
        result["total_found"] = len(papers)
        return result

    async def ingest_by_ids(
        self,
        arxiv_ids: List[str],
        auto_download: bool = True,
        imported_by_user=None,
    ) -> dict:
        """通过 arXiv ID 列表检索并入库。"""
        papers = []
        for aid in arxiv_ids:
            paper = await resolve_remote_paper("arxiv", aid)
            if paper:
                papers.append(paper)
            else:
                logger.warning(f"arXiv ID 未找到: {aid}")

        return await self.ingest_batch(papers, auto_download=auto_download, imported_by_user=imported_by_user)

    async def ingest_remote(
        self,
        source: str,
        remote_id: str,
        auto_download: bool = False,
        imported_by_user=None,
    ) -> tuple[Optional[Paper], bool]:
        """Resolve a provider identifier and ingest one trusted remote preview."""

        paper = await resolve_remote_paper(source, remote_id)
        if not paper:
            return None, False
        return await self.ingest_paper(paper, auto_download=auto_download, imported_by_user=imported_by_user)

    def _importer_username(self, user) -> str | None:
        if not user:
            return None
        return getattr(user, "username", None) or getattr(user, "display_name", None)

    async def enqueue_processing(self, paper: Paper) -> None:
        from app.services.paper_processing_pipeline import mark_paper_processing_queued

        try:
            await mark_paper_processing_queued(self.session, paper)
            from app.tasks.paper_tasks import process_paper_pipeline

            task = process_paper_pipeline.delay(str(paper.id))
            logger.info("论文入库后自动处理任务已提交: %s (task_id=%s)", paper.id, task.id)
        except Exception as e:
            logger.warning("提交论文自动处理任务失败 %s: %s", getattr(paper, "id", ""), e)

    async def _assign_categories(self, paper: Paper, category_names: List[str]):
        """为论文设置分类标签。"""
        for name in category_names:
            # 查找或创建分类
            result = await self.session.execute(
                select(Category).where(Category.name == name)
            )
            category = result.scalar_one_or_none()

            if not category:
                category = Category(name=name)
                self.session.add(category)
                await self.session.flush()

            # 创建关联
            pc = PaperCategory(paper_id=paper.id, category_id=category.id)
            self.session.add(pc)

        await self.session.commit()


async def get_ingestion_service() -> PaperIngestionService:
    """依赖注入：获取入库服务实例。"""
    async with AsyncSessionLocal() as session:
        yield PaperIngestionService(session)
