"""引用验证器 — 多源交叉验证 AI 生成的引用真实性。

参考 OpenDraft 和 Prismer.AI 的引用验证策略：
- 并行查询 Semantic Scholar + CrossRef + arXiv
- 2/3 多数投票判定验证状态
- 24h Redis 缓存
- 幻觉引用模糊匹配修复建议
"""

import asyncio
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class CitationVerifier:
    """引用真实性验证器。"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._cache_ttl = 86400  # 24 小时

    async def verify(self, title: str, authors: str = "",
                     year: Optional[int] = None, arxiv_id: str = "",
                     doi: str = "") -> dict:
        """验证单条引用的真实性。

        Returns:
            {
                "status": "verified" | "uncertain" | "likely_hallucination",
                "confidence": "high" | "medium" | "low",
                "sources": {
                    "semantic_scholar": "match" | "no_match" | "error",
                    "crossref": "match" | "no_match" | "error",
                    "arxiv": "match" | "no_match" | "error"
                },
                "verified_title": "实际标题（如果有差异）",
                "doi": "验证后的 DOI",
                "suggestion": "修复建议（如果是幻觉引用）"
            }
        """
        # 检查缓存
        cache_key = f"cite_verify:{title[:80]}"
        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    import json
                    return json.loads(cached)
            except Exception:
                pass

        # 并行查询三个 API
        ss_task = self._query_semantic_scholar(title, authors)
        cr_task = self._query_crossref(title, authors)
        ax_task = self._query_arxiv(title, arxiv_id) if arxiv_id else asyncio.sleep(0)

        ss_result, cr_result, _ = await asyncio.gather(
            ss_task, cr_task, ax_task,
            return_exceptions=True,
        )

        # 处理异常结果
        if isinstance(ss_result, Exception):
            ss_result = "error"
        if isinstance(cr_result, Exception):
            cr_result = "error"

        # 处理 arXiv 结果
        ax_result = "no_match"
        if arxiv_id:
            try:
                ax_result = await self._query_arxiv(title, arxiv_id)
            except Exception:
                ax_result = "error"

        # 2/3 多数投票
        matches = sum(1 for r in [ss_result, cr_result, ax_result] if r == "match")
        errors = sum(1 for r in [ss_result, cr_result, ax_result] if r == "error")

        sources = {
            "semantic_scholar": ss_result,
            "crossref": cr_result,
            "arxiv": ax_result if arxiv_id else "not_queried",
        }

        if errors == 3:
            status, confidence = "uncertain", "low"
        elif matches >= 2:
            status, confidence = "verified", "high" if matches == 3 else "medium"
        elif matches == 1:
            status, confidence = "uncertain", "low"
        else:
            status, confidence = "likely_hallucination", "low"

        result = {
            "status": status,
            "confidence": confidence,
            "sources": sources,
            "verified_title": title,
            "doi": doi,
            "suggestion": None,
        }

        # 幻觉引用 → 尝试模糊匹配修复建议
        if status == "likely_hallucination":
            suggestion = await self._find_similar_paper(title)
            if suggestion:
                result["suggestion"] = suggestion

        # 缓存结果
        if self.redis:
            try:
                import json
                self.redis.setex(cache_key, self._cache_ttl, json.dumps(result))
            except Exception:
                pass

        return result

    async def verify_batch(self, citations: List[dict]) -> List[dict]:
        """批量验证引用。"""
        tasks = [
            self.verify(
                title=c.get("title", ""),
                authors=c.get("authors", ""),
                year=c.get("year"),
                arxiv_id=c.get("arxiv_id", ""),
                doi=c.get("doi", ""),
            )
            for c in citations
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _query_semantic_scholar(self, title: str, authors: str = "") -> str:
        """通过 Semantic Scholar API 查询。"""
        try:
            query = title[:200]
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {"query": query, "limit": 3}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for paper in data.get("data", []):
                        paper_title = paper.get("title", "")
                        if self._title_similar(title, paper_title) > 0.6:
                            return "match"
                    return "no_match"
                return "error"
        except Exception as e:
            logger.warning(f"Semantic Scholar 查询失败: {e}")
            return "error"

    async def _query_crossref(self, title: str, authors: str = "") -> str:
        """通过 CrossRef API 查询。"""
        try:
            query = title[:200]
            url = "https://api.crossref.org/works"
            params = {"query.bibliographic": query, "rows": 3}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("message", {}).get("items", [])
                    for item in items:
                        item_title = item.get("title", [""])[0] if item.get("title") else ""
                        if self._title_similar(title, item_title) > 0.6:
                            return "match"
                    return "no_match"
                return "error"
        except Exception as e:
            logger.warning(f"CrossRef 查询失败: {e}")
            return "error"

    async def _query_arxiv(self, title: str, arxiv_id: str) -> str:
        """通过 arXiv API 查询。"""
        try:
            clean_id = arxiv_id.replace("arxiv:", "").split("v")[0]
            url = f"https://export.arxiv.org/api/query?search_query=id:{clean_id}&max_results=1"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    text = resp.text
                    if f"arXiv:{clean_id}" in text or title.lower()[:50] in text.lower():
                        return "match"
                    return "no_match"
                return "error"
        except Exception as e:
            logger.warning(f"arXiv 查询失败: {e}")
            return "error"

    async def _find_similar_paper(self, title: str) -> Optional[dict]:
        """为幻觉引用查找最相似的真实论文。"""
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {"query": title[:200], "limit": 3}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for paper in data.get("data", []):
                        paper_title = paper.get("title", "")
                        sim = self._title_similar(title, paper_title)
                        if sim > 0.5:
                            return {
                                "title": paper_title,
                                "similarity": round(sim, 3),
                                "paper_id": paper.get("paperId"),
                                "url": f"https://api.semanticscholar.org/CorpusID:{paper.get('corpusId')}",
                            }
        except Exception:
            pass
        return None

    @staticmethod
    def _title_similar(t1: str, t2: str) -> float:
        """标题相似度（基于 SequenceMatcher）。"""
        import difflib
        return difflib.SequenceMatcher(
            None,
            t1.lower().strip()[:150],
            t2.lower().strip()[:150],
        ).ratio()


# 全局单例
citation_verifier = CitationVerifier()
