"""混合检索服务 — BM25 + Dense + Cross-Encoder 重排序。参考 PaperQA2/OpenScholar。"""

import asyncio
import logging
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Tuple

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.paper import Category, Paper, PaperCategory
from app.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)
MIN_DENSE_FUSION_COVERAGE = 0.8
QUALITY_BOOST_WEIGHT = 0.18
MMR_LAMBDA = 0.82

# BM25 索引（进程内缓存）
_bm25_index: dict = {"corpus": [], "model": None, "paper_ids": [], "fingerprint": None}


def tokenize_academic_text(text: str) -> List[str]:
    """Normalize English academic terms and preserve searchable CJK characters."""
    return re.findall(r"[a-z0-9]+(?:[-_.][a-z0-9]+)*|[\u4e00-\u9fff]", (text or "").lower())


def invalidate_bm25_index() -> None:
    """Invalidate the process-local lexical index after library mutations."""
    global _bm25_index
    _bm25_index = {"corpus": [], "model": None, "paper_ids": [], "fingerprint": None}


def bm25_index_status() -> dict:
    """Return the current process-local BM25 cache state."""
    fingerprint = _bm25_index.get("fingerprint")
    return {
        "ready": _bm25_index.get("model") is not None,
        "indexed_papers": len(_bm25_index.get("paper_ids") or []),
        "corpus_documents": len(_bm25_index.get("corpus") or []),
        "fingerprint": list(fingerprint) if isinstance(fingerprint, tuple) else fingerprint,
    }


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1 + exp_value)


def expand_academic_query(query: str, limit: int = 4) -> list[str]:
    """Build deterministic academic query variants without adding LLM latency."""
    cleaned = re.sub(r"\s+", " ", query or "").strip()
    if not cleaned:
        return []
    variants = [cleaned]
    tokens = tokenize_academic_text(cleaned)
    informative = [
        token for token in tokens
        if len(token) >= 4 and token not in {"paper", "study", "method", "model", "using", "with"}
    ]
    if informative:
        variants.append(" ".join(informative[:8]))
    acronym_terms = re.findall(r"\b[A-Z][A-Z0-9]{1,8}\b", query or "")
    if acronym_terms:
        variants.append(" ".join(acronym_terms + informative[:5]))
    if len(informative) >= 3:
        variants.append(" ".join(informative[-6:]))
    deduped = []
    seen = set()
    for variant in variants:
        key = variant.lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(variant)
    return deduped[:limit]


def _paper_quality_score(paper: Paper) -> float:
    """Bounded readiness score used as a small tie-breaker after relevance."""
    checks = [
        bool(paper.title),
        bool(paper.abstract and len(paper.abstract) >= 120),
        bool(paper.authors),
        bool(paper.year),
        bool(paper.arxiv_id or paper.doi),
        bool(paper.full_text and len(paper.full_text) >= 800),
        bool(paper.embedding is not None),
    ]
    metadata_score = sum(1 for ready in checks if ready) / len(checks)
    citation_score = min(1.0, math.log1p(max(0, int(paper.citation_count or 0))) / math.log1p(500))
    current_year = datetime.now(timezone.utc).year
    recency_score = 0.0
    if paper.year:
        recency_score = max(0.0, min(1.0, 1 - max(0, current_year - int(paper.year)) / 12))
    return max(0.0, min(1.0, metadata_score * 0.65 + citation_score * 0.2 + recency_score * 0.15))


def _token_jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _paper_similarity(left: Paper, right: Paper) -> float:
    if left.arxiv_id and right.arxiv_id and left.arxiv_id == right.arxiv_id:
        return 1.0
    if left.doi and right.doi and left.doi == right.doi:
        return 1.0
    title_sim = _token_jaccard(set(tokenize_academic_text(left.title or "")), set(tokenize_academic_text(right.title or "")))
    tag_sim = _token_jaccard(set(left.tags or []), set(right.tags or []))
    return max(title_sim, tag_sim * 0.8)


class HybridSearchService:
    """混合检索：BM25 + Dense + Cross-Encoder 重排序。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_index_fingerprint(self) -> tuple[int, str]:
        result = await self.session.execute(
            select(func.count(Paper.id), func.max(Paper.updated_at))
        )
        count, latest_update = result.one()
        return int(count or 0), latest_update.isoformat() if latest_update else ""

    async def _ensure_bm25_index(self):
        """确保 BM25 索引是最新的。"""
        global _bm25_index
        fingerprint = await self._get_index_fingerprint()
        if _bm25_index["fingerprint"] == fingerprint:
            return

        from rank_bm25 import BM25Okapi

        result = await self.session.execute(
            select(Paper.id, Paper.title, Paper.abstract)
        )
        papers = result.all()
        corpus = []
        paper_ids = []
        for pid, title, abstract in papers:
            title_tokens = tokenize_academic_text(title or "")
            abstract_tokens = tokenize_academic_text(abstract or "")
            tokenized = title_tokens * 3 + abstract_tokens
            corpus.append(tokenized)
            paper_ids.append(pid)

        _bm25_index = {
            "corpus": corpus,
            "model": BM25Okapi(corpus) if corpus else None,
            "paper_ids": paper_ids,
            "fingerprint": fingerprint,
        }
        logger.info(f"BM25 索引已构建: {len(corpus)} 篇论文")

    async def rebuild_index(self):
        """强制重建 BM25 索引（论文入库后调用）。"""
        invalidate_bm25_index()
        await self._ensure_bm25_index()

    async def paper_count(self) -> int:
        result = await self.session.execute(select(func.count(Paper.id)))
        return int(result.scalar() or 0)

    async def search_bm25(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """BM25 关键词检索。"""
        await self._ensure_bm25_index()
        model = _bm25_index["model"]
        if not model:
            return []
        tokenized = tokenize_academic_text(query)
        if not tokenized:
            return []
        scores = model.get_scores(tokenized)
        # 归一化到 [0, 1]
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                paper_id = str(_bm25_index["paper_ids"][idx])
                norm_score = float(scores[idx] / max_score)
                results.append((paper_id, norm_score))
        return results

    async def search_dense(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Dense 向量检索（现有 pgvector 方式）。"""
        embedded_count = await self.session.execute(
            select(func.count(Paper.id)).where(Paper.embedding.is_not(None))
        )
        if not embedded_count.scalar():
            return []
        query_embedding = await generate_embedding(query)
        result = await self.session.execute(
            select(Paper.id, 1 - Paper.embedding.cosine_distance(query_embedding))
            .where(Paper.embedding.is_not(None))
            .order_by(Paper.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        rows = result.all()
        return [(str(pid), float(score)) for pid, score in rows if score > 0]

    async def embedding_coverage(self) -> float:
        """Return the fraction of papers with stored embeddings."""
        result = await self.session.execute(
            select(func.count(Paper.id), func.count(Paper.embedding))
        )
        total, embedded = result.one()
        return float(embedded or 0) / float(total or 1)

    async def search_hybrid(
        self, query: str, top_k: int = 10, alpha: float = 0.7, rrf_k: int = 60
    ) -> List[Tuple[str, float]]:
        """混合检索：BM25 + Dense 加权 RRF 融合。"""
        try:
            coverage = await self.embedding_coverage()
        except Exception as exc:
            logger.warning(f"向量覆盖率读取失败，按完整覆盖率融合: {exc}")
            coverage = 1.0
        if coverage < MIN_DENSE_FUSION_COVERAGE:
            logger.info(
                f"向量覆盖率 {coverage:.1%} 低于 {MIN_DENSE_FUSION_COVERAGE:.0%}，Hybrid 降级为 BM25"
            )
            return await self._search_expanded_bm25(query, top_k, rrf_k=rrf_k)

        normalized_coverage = min(max(float(coverage), 0.0), 1.0)
        dense_weight = alpha * normalized_coverage ** 2
        lexical_weight = 1 - dense_weight
        combined: dict[str, float] = {}
        variants = expand_academic_query(query)
        for query_index, variant in enumerate(variants):
            variant_weight = 1 / (1 + query_index * 0.35)
            results = await asyncio.gather(
                self.search_bm25(variant, top_k * 2),
                self.search_dense(variant, top_k * 2),
                return_exceptions=True,
            )
            bm25_results, dense_results = results
            if isinstance(bm25_results, Exception):
                logger.warning(f"BM25 检索失败，降级为 Dense: {bm25_results}")
                bm25_results = []
            if isinstance(dense_results, Exception):
                logger.warning(f"Dense 检索失败，降级为 BM25: {dense_results}")
                dense_results = []
            for rank, (pid, score) in enumerate(bm25_results, 1):
                combined[pid] = combined.get(pid, 0.0) + variant_weight * lexical_weight * (1 + min(score, 1.0) * 0.1) / (rrf_k + rank)
            for rank, (pid, score) in enumerate(dense_results, 1):
                combined[pid] = combined.get(pid, 0.0) + variant_weight * dense_weight * (1 + min(score, 1.0) * 0.1) / (rrf_k + rank)

        sorted_results = sorted(combined.items(), key=lambda item: item[1], reverse=True)[:top_k]
        if not sorted_results:
            return []
        max_score = sorted_results[0][1]
        return [(pid, score / max_score) for pid, score in sorted_results]

    async def _search_expanded_bm25(self, query: str, top_k: int, rrf_k: int = 60) -> List[Tuple[str, float]]:
        combined: dict[str, float] = defaultdict(float)
        for query_index, variant in enumerate(expand_academic_query(query)):
            weight = 1 / (1 + query_index * 0.35)
            for rank, (pid, score) in enumerate(await self.search_bm25(variant, top_k * 2), 1):
                combined[pid] += weight * (1 + min(score, 1.0) * 0.1) / (rrf_k + rank)
        sorted_results = sorted(combined.items(), key=lambda item: item[1], reverse=True)[:top_k]
        if not sorted_results:
            return []
        max_score = sorted_results[0][1]
        return [(pid, score / max_score) for pid, score in sorted_results]

    async def search(
        self, query: str, top_k: int = 10, mode: str = "hybrid"
    ) -> List[Tuple[str, float]]:
        """Dispatch an explicit local retrieval mode."""
        if mode == "bm25":
            return await self.search_bm25(query, top_k)
        if mode == "dense":
            return await self.search_dense(query, top_k)
        if mode == "hybrid":
            return await self.search_hybrid(query, top_k)
        raise ValueError(f"Unsupported search mode: {mode}")

    async def fetch_papers(
        self,
        paper_scores: List[Tuple[str, float]],
        category: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> List[Tuple[Paper, float]]:
        """根据 ID 列表获取 Paper 对象。"""
        from uuid import UUID
        ids = [UUID(pid) for pid, _ in paper_scores if pid and not pid.startswith("ext:")]
        if not ids:
            return []
        query = select(Paper).where(Paper.id.in_(ids))
        if category:
            query = query.join(PaperCategory).join(Category).where(Category.name == category)
        if year_from:
            query = query.where(Paper.year >= year_from)
        if year_to:
            query = query.where(Paper.year <= year_to)
        result = await self.session.execute(query)
        papers = {str(p.id): p for p in result.scalars().all()}
        ranked = [
            (papers[pid], min(1.0, float(score) * (1 - QUALITY_BOOST_WEIGHT) + _paper_quality_score(papers[pid]) * QUALITY_BOOST_WEIGHT))
            for pid, score in paper_scores
            if pid in papers
        ]
        return self._select_diverse_papers(ranked, len(ranked))

    def _select_diverse_papers(self, papers_with_scores: List[Tuple[Paper, float]], top_k: int) -> List[Tuple[Paper, float]]:
        if len(papers_with_scores) <= 2:
            return papers_with_scores[:top_k]
        pool = sorted(papers_with_scores, key=lambda item: item[1], reverse=True)
        selected: list[Tuple[Paper, float]] = []
        while pool and len(selected) < top_k:
            best_index = 0
            best_score = -1.0
            for index, (paper, score) in enumerate(pool):
                redundancy = max((_paper_similarity(paper, chosen) for chosen, _ in selected), default=0.0)
                mmr_score = MMR_LAMBDA * score - (1 - MMR_LAMBDA) * redundancy
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_index = index
            selected.append(pool.pop(best_index))
        return selected


class RerankService:
    """Cross-Encoder 重排序服务。"""

    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            from sentence_transformers import CrossEncoder
            cls._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("Cross-Encoder 模型已加载")
        return cls._model

    async def rerank(
        self, query: str, papers: List[Paper], top_k: int = 5
    ) -> List[Tuple[Paper, float]]:
        """对候选论文列表进行交叉编码器重排序。"""
        model = self._get_model()
        pairs = []
        for p in papers[:20]:  # 最多重排 20 篇
            text = f"{p.title or ''} {p.abstract[:500] if p.abstract else ''}"[:1000]
            pairs.append([query, text])

        scores = model.predict(pairs)
        scored = sorted(
            [(p, _sigmoid(float(s))) for p, s in zip(papers[:20], scores)],
            key=lambda x: x[1], reverse=True,
        )
        return scored[:top_k]
