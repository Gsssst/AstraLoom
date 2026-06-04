"""论文智能筛选服务 — 参考 AI-Researcher + SciPIP 的论文选择策略。"""

import logging
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.paper import Paper, UserPaper
from app.services.llm import llm_service
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

# 顶级会议/期刊关键词（arXiv 论文的交叉列表可以帮助判断）
TOP_VENUE_KEYWORDS = [
    "NeurIPS", "ICML", "ICLR", "ACL", "EMNLP", "NAACL", "CVPR", "ICCV",
    "ECCV", "AAAI", "IJCAI", "SIGKDD", "WWW", "SIGIR", "CHI", "UIST",
    "Nature", "Science", "JMLR", "TPAMI", "TACL", "TMLR",
]


class PaperSelectionService:
    """论文智能筛选 — 多路召回 + 实体匹配 + LLM 重排序。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def select_papers(
        self,
        topic_name: str,
        topic_description: str = "",
        keywords: List[str] = None,
        manual_paper_ids: List[str] = None,
        max_papers: int = 10,
    ) -> List[Tuple[Paper, float, str]]:
        """智能筛选论文，返回 (论文, 分数, 来源) 列表。"""

        from uuid import UUID
        seen_ids = set()
        all_candidates: List[Tuple[Paper, float, str]] = []

        # ====== 第 0 层：手动选择的论文（优先级最高）======
        if manual_paper_ids:
            for pid in manual_paper_ids:
                try:
                    result = await self.session.execute(select(Paper).where(Paper.id == UUID(pid)))
                    paper = result.scalar_one_or_none()
                    if paper and paper.id not in seen_ids:
                        all_candidates.append((paper, 1.0, "manual"))
                        seen_ids.add(paper.id)
                except Exception:
                    pass

        # ====== 第 1 层：实体感知检索（参考 SciPIP Entities）======
        # 用 LLM 从研究方向中提取关键实体
        entities = await self._extract_entities(topic_name, topic_description, keywords or [])

        # 用这些实体做精确搜索
        if entities:
            for entity_group in [entities["methods"], entities["tasks"], entities["datasets"]]:
                for entity in entity_group[:3]:
                    entity_papers = await self._search_by_entity(entity)
                    for p, score in entity_papers:
                        if p.id not in seen_ids:
                            all_candidates.append((p, score * 0.95, f"entity:{entity}"))
                            seen_ids.add(p.id)
                            if len(all_candidates) >= max_papers * 3:
                                break

        # ====== 第 2 层：多查询语义搜索（参考 AI-Researcher 迭代查询）======
        # 生成多个搜索查询变体
        search_queries = await self._generate_search_queries(topic_name, topic_description, keywords or [])

        rag = RAGService(self.session)
        for query in search_queries[:5]:
            results = await rag.search_keyword_and_semantic(query=query, top_k=8)
            for p, score in results:
                if p.id not in seen_ids:
                    all_candidates.append((p, score * 0.85, f"semantic:{query[:30]}"))
                    seen_ids.add(p.id)

        # ====== 第 3 层：arXiv 联网检索（始终执行，获取最新论文）======
        try:
            from app.services.paper_search import arxiv_service
            for query in search_queries[:2]:
                try:
                    fresh = await arxiv_service.search(query=query, max_results=5, sort_by="date")
                    for fp in fresh:
                        paper_id = f"arxiv:{fp.arxiv_id}"
                        if paper_id not in seen_ids:
                            temp_paper = Paper(
                                title=fp.title, authors=fp.authors, year=fp.year,
                                abstract=fp.abstract, arxiv_id=fp.arxiv_id,
                                source="arxiv", citation_count=fp.citation_count,
                                tags=fp.categories[:5] if fp.categories else [],
                            )
                            all_candidates.append((temp_paper, 0.78, f"arxiv:{fp.arxiv_id}"))
                            seen_ids.add(paper_id)
                except Exception: continue
                import asyncio; await asyncio.sleep(3)
        except Exception as e:
            logger.warning(f"arXiv 检索失败: {e}")

        # ====== 第 4 层：Semantic Scholar 搜索（引用数据更丰富）======
        try:
            from app.services.paper_search import semantic_scholar_service
            for query in search_queries[:1]:
                try:
                    s2_papers = await semantic_scholar_service.search(query=query, max_results=5)
                    for fp in s2_papers:
                        paper_id = f"s2:{fp.doi or fp.title}"
                        if paper_id not in seen_ids and fp.title and len(fp.title) > 10:
                            temp_paper = Paper(
                                title=fp.title, authors=fp.authors, year=fp.year,
                                abstract=fp.abstract, doi=fp.doi, arxiv_id=fp.arxiv_id,
                                source="semantic_scholar", citation_count=fp.citation_count,
                            )
                            all_candidates.append((temp_paper, 0.76, f"s2:{fp.doi or fp.title[:50]}"))
                            seen_ids.add(paper_id)
                except Exception: continue
                import asyncio; await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Semantic Scholar 检索失败: {e}")

        # ====== 第 4 层：高收藏论文（社会信号 = 质量信号）======
        try:
            saved_result = await self.session.execute(
                select(Paper, func.count(UserPaper.id).label('save_count'))
                .join(UserPaper, UserPaper.paper_id == Paper.id)
                .where(UserPaper.saved == True)
                .group_by(Paper.id)
                .order_by(func.count(UserPaper.id).desc())
                .limit(15)
            )
            for paper, count in saved_result.all():
                if paper.id not in seen_ids:
                    score = min(0.8, 0.4 + count * 0.05)
                    all_candidates.append((paper, score, f"saved:{count}"))
                    seen_ids.add(paper.id)
        except Exception:
            pass

        # ====== 第 5 层：LLM 重排序（参考 AI-Researcher）======
        if len(all_candidates) > max_papers:
            selected = await self._llm_rerank(
                topic_name, topic_description, all_candidates, max_papers
            )
        else:
            selected = all_candidates[:max_papers]

        # ====== 第 6 层：多样性采样 ======
        selected = self._diversity_sample(selected, max_papers)

        return selected[:max_papers]

    async def _extract_entities(self, topic: str, description: str, keywords: List[str]) -> dict:
        """用 LLM 提取研究方向的关键实体（方法、任务、数据集）。"""
        prompt = f"""从以下研究方向中提取关键学术实体。只输出 JSON，不要其他内容。

研究方向: {topic}
描述: {description}
关键词: {', '.join(keywords)}

请提取：
- "methods": 涉及的具体方法/模型名（如 Transformer, RLHF, Diffusion Model）
- "tasks": 研究任务（如 machine translation, object detection）
- "datasets": 常用数据集/benchmark（如 ImageNet, WMT14）

格式: {{"methods": ["...", "..."], "tasks": ["...", "..."], "datasets": ["...", "..."]}}
每个类别最多 5 个实体。如果是未知的实体，不要编造，留空即可。
"""
        try:
            import json
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=512,
            )
            text = response.strip()
            if "```" in text:
                text = text.split("```")[1].replace("json", "").strip()
            data = json.loads(text)
            return {
                "methods": data.get("methods", [])[:5],
                "tasks": data.get("tasks", [])[:5],
                "datasets": data.get("datasets", [])[:5],
            }
        except Exception as e:
            logger.warning(f"实体提取失败: {e}")
            return {"methods": [], "tasks": [], "datasets": []}

    async def _search_by_entity(self, entity: str) -> List[Tuple[Paper, float]]:
        """通过实体名称精确搜索论文（关键词 + 语义混合）。"""
        from sqlalchemy import or_, text

        # 标题/摘要包含该实体
        result = await self.session.execute(
            select(Paper).where(
                or_(
                    Paper.title.ilike(f"%{entity}%"),
                    Paper.abstract.ilike(f"%{entity}%"),
                )
            ).limit(5)
        )
        papers = [(p, 0.9) for p in result.scalars().all() if p.embedding is not None]
        return papers[:5]

    async def _generate_search_queries(self, topic: str, description: str, keywords: List[str]) -> List[str]:
        """用 LLM 生成多个搜索查询变体（参考 AI-Researcher 迭代查询策略）。"""
        prompt = f"""你是一个学术文献检索专家。请为以下研究方向生成 5 个不同的英文搜索查询，
以帮助在论文数据库中找到最相关的前沿论文。

研究方向: {topic}
描述: {description or '无'}
关键词: {', '.join(keywords) if keywords else '无'}

要求：
- 查询应该覆盖不同的子方向和技术角度
- 有些查询应该更具体（关注特定方法），有些更宽泛（关注整体领域）
- 用英文术语（论文数据库中的论文标题/摘要多为英文）
- 每个查询 5-15 个单词

直接输出 5 行，每行一个查询，不要编号，不要其他内容。
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5, max_tokens=300,
            )
            queries = [line.strip() for line in response.strip().split("\n") if line.strip() and len(line.strip()) > 3]
            # 添加原始关键词作为基础查询
            if keywords:
                queries.insert(0, " ".join(keywords))
            queries.append(topic)
            return list(dict.fromkeys(queries))[:8]  # 去重
        except Exception as e:
            logger.warning(f"查询生成失败: {e}")
            base = " ".join(keywords) if keywords else topic
            return [base, f"{base} latest advances", f"{base} state of the art"]

    async def _llm_rerank(
        self,
        topic: str,
        description: str,
        candidates: List[Tuple[Paper, float, str]],
        top_k: int,
    ) -> List[Tuple[Paper, float, str]]:
        """用 LLM 对候选论文进行重排序（参考 AI-Researcher 的 LLM reranking）。"""
        papers_text = "\n".join([
            f"[{i}] {p.title} ({p.year or 'N/A'}) | 来源: {src} | 评分: {score:.2f}\n"
            f"   摘要: {p.abstract[:200] if p.abstract else 'N/A'}"
            for i, (p, score, src) in enumerate(candidates[:30])
        ])

        prompt = f"""你是一位学术论文审稿人。请根据与以下研究方向的**相关性**，对候选论文进行排名。

研究方向: {topic}
描述: {description or '无'}

候选论文（共 {len(candidates[:30])} 篇）:
{papers_text}

请选出最相关的 {min(top_k + 5, len(candidates[:30]))} 篇论文，按相关性从高到低排列。
输出格式: 每行一个编号，如 "3,7,12,5,8,..."（只输出编号，逗号分隔）

直接输出编号列表，不要其他内容。
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=200,
            )
            # 解析排名
            ranks = []
            for part in response.strip().replace(" ", "").split(","):
                try:
                    idx = int(part) - 1  # 转为 0-based
                    if 0 <= idx < len(candidates):
                        ranks.append(candidates[idx])
                except ValueError:
                    continue

            if len(ranks) >= top_k // 2:
                return ranks[:top_k]
        except Exception as e:
            logger.warning(f"LLM 重排序失败: {e}")

        # 回退：按原分数排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]

    def _diversity_sample(
        self,
        candidates: List[Tuple[Paper, float, str]],
        max_papers: int,
    ) -> List[Tuple[Paper, float, str]]:
        """多样性采样：确保选出的论文覆盖不同子主题。"""
        if len(candidates) <= max_papers:
            return candidates

        selected = []
        seen_tags = set()

        # 优先选择有不同标签的论文
        for paper, score, src in candidates:
            tags = set(paper.tags[:3]) if paper.tags else set()
            if not tags or not tags.intersection(seen_tags) or len(selected) < max_papers // 2:
                selected.append((paper, score, src))
                seen_tags.update(tags)
                if len(selected) >= max_papers:
                    break

        # 如果还不够，从剩下的里面补
        remaining = [(p, s, src) for p, s, src in candidates if (p, s, src) not in selected]
        selected.extend(remaining[:max_papers - len(selected)])

        return selected[:max_papers]
