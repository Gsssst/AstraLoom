"""智能引用推荐服务 — 上下文感知的引用定位 + 多源检索。

参考 ScholarCopilot 的 "生成→暂停→检索→继续" 动态切换机制，
分析写作文本，自动判断哪些位置需要引用，并推荐最匹配的论文。
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SmartCitationService:
    """上下文感知的智能引用推荐。"""

    def __init__(self, db_session_factory=None, llm_service=None):
        self.db_factory = db_session_factory
        self.llm = llm_service

    async def analyze_and_recommend(self, text: str, top_k: int = 5) -> dict:
        """分析文本中的引用需求并推荐论文。

        Returns:
            {
                "citation_positions": [
                    {
                        "sentence": "需要引用的句子",
                        "reason": "为什么需要引用",
                        "position": 100,  # 文本中的大致位置
                    }
                ],
                "recommendations": [
                    {
                        "position_index": 0,  # 对应当前 citation_position
                        "papers": [
                            {
                                "title": "...",
                                "authors": "...",
                                "year": 2024,
                                "similarity": 0.89,
                                "source": "local" | "semantic_scholar" | "arxiv",
                                "bibtex": "...",
                                "positioning_hint": "支持关于XX的论述",
                            }
                        ]
                    }
                ]
            }
        """
        # Step 1: 检测引用位置
        citation_positions = await self._detect_citation_positions(text)
        if not citation_positions:
            return {"citation_positions": [], "recommendations": []}

        # Step 2: 为每个位置推荐论文
        recommendations = []
        for pos in citation_positions:
            papers = await self._retrieve_papers_for_claim(
                pos["sentence"], top_k=top_k
            )
            recommendations.append({
                "position_index": pos["index"],
                "sentence": pos["sentence"],
                "reason": pos["reason"],
                "papers": papers,
            })

        return {
            "citation_positions": citation_positions,
            "recommendations": recommendations,
        }

    async def _detect_citation_positions(self, text: str) -> list:
        """检测文本中需要引用的位置（声明句/方法句/对比句）。"""
        if not self.llm or len(text) < 50:
            return []

        prompt = f"""## 任务
分析以下学术文本，识别哪些句子或声明需要引用支持。返回需要引用的位置。

## 判断标准
- 事实性声明（"研究表明..."、"已有工作显示..."）
- 方法对比（"与XX相比..."、"不同于XX..."）
- 性能声明（"达到了SOTA..."、"超过了..."）
- 领域背景（"近年来..."、"随着..."）
- 不标记：作者的原创贡献声明（"我们提出..."、"本文..."）

## 文本
{text[:3000]}

## 输出格式
严格输出 JSON 数组，最多 5 个位置：
[{{"sentence": "需要引用的原句", "reason": "为什么需要引用 (简短)", "index": 0}}, ...]

如果没有需要引用的位置，输出 []。
"""
        try:
            import json
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
            logger.warning(f"引用位置检测失败: {e}")
        return []

    async def _retrieve_papers_for_claim(self, claim: str, top_k: int = 3) -> list:
        """为单个声明检索最匹配的论文（多源）。"""
        papers = []

        # 源 1: 本地知识库
        local_papers = await self._search_local(claim, top_k)
        for p in local_papers:
            p["source"] = "local"
        papers.extend(local_papers)

        # 源 2: Semantic Scholar (异步，不阻塞)
        if len(papers) < top_k:
            try:
                ss_papers = await self._search_semantic_scholar(claim, top_k)
                for p in ss_papers:
                    p["source"] = "semantic_scholar"
                papers.extend(ss_papers)
            except Exception as e:
                logger.warning(f"Semantic Scholar 检索失败: {e}")

        # 源 3: arXiv
        if len(papers) < top_k:
            try:
                ax_papers = await self._search_arxiv(claim, top_k)
                for p in ax_papers:
                    p["source"] = "arxiv"
                papers.extend(ax_papers)
            except Exception as e:
                logger.warning(f"arXiv 检索失败: {e}")

        # 去重 + 排序
        seen = set()
        unique = []
        for p in sorted(papers, key=lambda x: x.get("similarity", 0), reverse=True):
            key = p.get("title", "")[:80].lower()
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique[:top_k]

    async def _search_local(self, query: str, top_k: int) -> list:
        """本地知识库检索。"""
        if not self.db_factory:
            return []

        try:
            from app.db.session import AsyncSessionLocal
            from app.services.rag_service import RAGService

            async with AsyncSessionLocal() as session:
                rag = RAGService(session)
                results = await rag.search_similar(query, top_k=top_k)
                return [
                    {
                        "title": p.title,
                        "authors": ", ".join(p.authors[:5]) if isinstance(p.authors, list) else str(p.authors),
                        "year": p.year,
                        "abstract_snippet": p.abstract[:200] if p.abstract else "",
                        "arxiv_id": p.arxiv_id,
                        "similarity": round(score, 4),
                    }
                    for p, score in results
                ]
        except Exception:
            return []

    async def _search_semantic_scholar(self, query: str, top_k: int) -> list:
        """Semantic Scholar 检索。"""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params={"query": query[:200], "limit": top_k},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        {
                            "title": p.get("title", ""),
                            "authors": ", ".join(
                                [a.get("name", "") for a in p.get("authors", [])[:3]]
                            ),
                            "year": p.get("year"),
                            "abstract_snippet": p.get("abstract", "")[:200] if p.get("abstract") else "",
                            "arxiv_id": p.get("externalIds", {}).get("ArXiv", ""),
                            "similarity": 0.7,  # 默认值
                        }
                        for p in data.get("data", [])
                    ]
        except Exception:
            return []

    async def _search_arxiv(self, query: str, top_k: int) -> list:
        """arXiv 检索。"""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://export.arxiv.org/api/query",
                    params={
                        "search_query": query[:200],
                        "max_results": top_k,
                        "sortBy": "relevance",
                    },
                )
                if resp.status_code == 200:
                    import feedparser
                    feed = feedparser.parse(resp.text)
                    results = []
                    for entry in feed.entries[:top_k]:
                        arxiv_id = entry.id.split("/abs/")[-1] if "/abs/" in entry.id else ""
                        results.append({
                            "title": entry.title.strip().replace("\n", " "),
                            "authors": ", ".join(
                                [a.name for a in getattr(entry, "authors", [])[:3]]
                            ),
                            "year": int(entry.published[:4]) if entry.published else None,
                            "abstract_snippet": entry.summary[:200] if entry.summary else "",
                            "arxiv_id": arxiv_id,
                            "similarity": 0.65,
                        })
                    return results
        except Exception:
            return []


# 全局单例
smart_citation_service = SmartCitationService()
