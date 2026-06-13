"""每日 arXiv 摘要推送服务。"""

import logging
import re
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, func

from app.services.llm import llm_service
from app.services.paper_search import (
    PaperResult,
    canonical_paper_key,
    create_remote_ingest_token,
    deduplicate_papers,
    search_scholarly_papers,
)
from app.db.models.notification import Notification
from app.db.models.paper import Paper, UserPaper
from app.db.models.research import ResearchProject

logger = logging.getLogger(__name__)


class DigestService:
    """每日 arXiv 摘要推送。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch_daily_papers(
        self,
        keywords: list[str],
        max_per_keyword: int = 5,
        freshness_hours: int | None = 72,
    ) -> list[dict]:
        """Retrieve diverse scholarly candidates and filter precisely dated stale papers."""
        all_papers: list[PaperResult] = []
        for keyword in keywords:
            try:
                papers = await search_scholarly_papers(
                    query=keyword,
                    source="scholarly",
                    max_results=max(max_per_keyword * 2, 6),
                    sort_by="date",
                )
                all_papers.extend(papers)
            except Exception as exc:
                logger.warning("获取关键词 '%s' 失败: %s", keyword, exc)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=freshness_hours or 0)
        candidates = []
        for paper in deduplicate_papers(all_papers):
            published_at = self._parse_datetime(paper.published_at)
            if freshness_hours is not None and published_at and published_at < cutoff:
                continue
            candidates.append({
                "title": paper.title,
                "arxiv_id": paper.arxiv_id,
                "authors": paper.authors[:3] if paper.authors else [],
                "year": paper.year,
                "published_at": paper.published_at,
                "abstract_snippet": paper.abstract[:400] if paper.abstract else "",
                "source": paper.source,
                "source_url": paper.source_url,
                "pdf_url": paper.pdf_url,
                "remote_id": (paper.metadata or {}).get("remote_id"),
                "remote_ingest_token": create_remote_ingest_token(paper),
                "canonical_key": canonical_paper_key(paper),
                "citation_count": paper.citation_count,
            })
        return candidates[:max(15, len(keywords) * max_per_keyword * 2)]

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _tokens(*values: str) -> set[str]:
        text = " ".join(value or "" for value in values).lower()
        return {
            token
            for token in re.findall(r"[a-z0-9][a-z0-9._-]+|[\u4e00-\u9fff]{2,}", text)
            if len(token) > 1
        }

    @staticmethod
    def _canonical_key_from_metadata(paper: dict) -> str:
        if paper.get("canonical_key"):
            return str(paper["canonical_key"])
        if paper.get("arxiv_id"):
            return f"arxiv:{re.sub(r'v\d+$', '', str(paper['arxiv_id']).lower())}"
        if paper.get("remote_id"):
            return f"{paper.get('source', 'remote')}:{paper['remote_id']}"
        title = re.sub(r"[^a-z0-9]+", "", str(paper.get("title", "")).lower())
        return f"title:{title}"

    async def _collect_preference_signals(self, user_id) -> dict:
        """Collect bounded profile and prior-feedback signals for one user's radar."""
        profile_terms: set[str] = set()
        interest_terms: set[str] = set()
        dismissed_keys: set[str] = set()
        positive_keys: set[str] = set()

        try:
            result = await self.session.execute(
                select(ResearchProject)
                .where(
                    ResearchProject.user_id == user_id,
                    ResearchProject.status == "active",
                )
                .limit(20)
            )
            for project in result.scalars().all() or []:
                profile_terms.update(self._tokens(*(project.keywords or [])))
        except Exception as exc:
            logger.debug("读取研究方向信号失败: %s", exc)

        try:
            result = await self.session.execute(
                select(Paper)
                .join(UserPaper, UserPaper.paper_id == Paper.id)
                .where(
                    UserPaper.user_id == user_id,
                    or_(UserPaper.saved == True, UserPaper.read_status != "unread"),
                )
                .limit(100)
            )
            for paper in result.scalars().all() or []:
                interest_terms.update(self._tokens(paper.title, paper.abstract or "", *(paper.tags or [])))
        except Exception as exc:
            logger.debug("读取论文偏好信号失败: %s", exc)

        try:
            result = await self.session.execute(
                select(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.category == "digest",
                )
                .order_by(Notification.created_at.desc())
                .limit(50)
            )
            for notification in result.scalars().all() or []:
                feedback_map = (notification.metadata_json or {}).get("feedback", {}) or {}
                for key, feedback in feedback_map.items():
                    action = feedback.get("action") if isinstance(feedback, dict) else feedback
                    if action == "dismissed":
                        dismissed_keys.add(key)
                    elif action in {"interested", "later"}:
                        positive_keys.add(key)
        except Exception as exc:
            logger.debug("读取推送反馈信号失败: %s", exc)

        return {
            "profile_terms": set(list(profile_terms)[:80]),
            "interest_terms": set(list(interest_terms)[:160]),
            "dismissed_keys": dismissed_keys,
            "positive_keys": positive_keys,
        }

    async def rank_papers(self, *, user_id, keywords: list[str], papers: list[dict]) -> list[dict]:
        """Apply a bounded and explainable personalized ranking heuristic."""
        signals = await self._collect_preference_signals(user_id)
        subscription_terms = self._tokens(*keywords)
        now = datetime.now(timezone.utc)
        ranked = []
        for paper in papers:
            canonical_key = self._canonical_key_from_metadata(paper)
            if canonical_key in signals["dismissed_keys"]:
                continue
            paper_terms = self._tokens(paper.get("title", ""), paper.get("abstract_snippet", ""))
            keyword_overlap = paper_terms & subscription_terms
            profile_overlap = paper_terms & signals["profile_terms"]
            interest_overlap = paper_terms & signals["interest_terms"]
            score = 0.2
            reasons = []
            if keyword_overlap:
                score += min(0.38, 0.12 * len(keyword_overlap))
                reasons.append("匹配订阅关键词")
            if profile_overlap:
                score += min(0.2, 0.06 * len(profile_overlap))
                reasons.append("符合活跃研究方向")
            if interest_overlap:
                score += min(0.16, 0.03 * len(interest_overlap))
                reasons.append("与你收藏或阅读的主题接近")
            if canonical_key in signals["positive_keys"]:
                score += 0.08
                reasons.append("你曾关注过相关推荐")
            published_at = self._parse_datetime(paper.get("published_at"))
            if published_at:
                age_hours = max(0, (now - published_at).total_seconds() / 3600)
                if age_hours <= 24:
                    score += 0.2
                    reasons.append("近 24 小时发布")
                elif age_hours <= 72:
                    score += 0.12
                    reasons.append("近期发布")
            else:
                score += 0.03
                reasons.append("来源暂未提供精确发布日期")
            if paper.get("source") == "arxiv":
                score += 0.04
                reasons.append("arXiv 原始来源")
            paper["canonical_key"] = canonical_key
            paper["recommendation_score"] = round(score, 4)
            paper["recommendation_reasons"] = reasons[:4] or ["与订阅主题相关"]
            ranked.append(paper)
        return sorted(ranked, key=lambda item: item["recommendation_score"], reverse=True)[:15]

    async def generate_digest_from_papers(self, keywords: list[str], papers: list[dict]) -> str:
        """根据已经获取的论文生成摘要，避免重复请求 arXiv。"""
        if not papers:
            return "今天 arXiv 暂无相关新论文。"

        papers_text = "\n".join([
            f"- **{p['title']}** ({p['year']}) — arXiv:{p['arxiv_id']}\n"
            f"  {p['abstract_snippet']}..."
            for p in papers
        ])

        prompt = f"""你是一个科研助手。以下是今天聚合学术来源中与用户关注方向相关的论文：

{papers_text}

请用中文生成一份简洁的每日论文摘要（200 字内）：
1. 今日亮点（选 2-3 篇最值得关注的）
2. 趋势观察
3. 推荐阅读优先级
"""
        try:
            return await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5, max_tokens=1024,
            )
        except Exception as e:
            return f"arXiv 摘要生成失败: {e}"

    async def generate_digest(self, keywords: list[str]) -> str:
        """获取论文并生成每日 arXiv 摘要。"""
        papers = await self.fetch_daily_papers(keywords)
        return await self.generate_digest_from_papers(keywords, papers)

    async def dispatch_in_app_digest(
        self,
        *,
        user_id,
        keywords: list[str],
        is_test: bool = False,
        notify_on_empty: bool = False,
    ) -> dict:
        """创建站内摘要通知；定时任务和手动测试共用这一条路径。"""
        papers = await self.fetch_daily_papers(
            keywords,
            max_per_keyword=3,
            freshness_hours=None if is_test else 72,
        )
        papers = await self.rank_papers(user_id=user_id, keywords=keywords, papers=papers)
        from app.services.paper_library_state import existing_state_for_preview, local_paper_lookup_for_remote_previews

        local_lookup = await local_paper_lookup_for_remote_previews(self.session, papers)
        papers = [
            {
                **paper,
                **existing_state_for_preview(paper, local_lookup),
            }
            for paper in papers
        ]
        if not papers and not notify_on_empty:
            return {
                "delivered": False,
                "notification_id": None,
                "paper_count": 0,
                "keywords": keywords,
                "message": "当前没有匹配的新论文，已跳过站内通知。",
            }

        summary = await self.generate_digest_from_papers(keywords, papers)
        now = datetime.now(timezone.utc)
        title_prefix = "🧪 测试推送" if is_test else "📬 每日论文摘要"
        notification = Notification(
            user_id=user_id,
            title=f"{title_prefix} — {now.strftime('%Y-%m-%d')}",
            content=summary,
            category="digest",
            metadata_json={
                "papers": [
                    {
                        "title": paper["title"],
                        "arxiv_id": paper["arxiv_id"],
                        "authors": paper.get("authors", []),
                        "year": paper.get("year"),
                        "abstract_snippet": paper.get("abstract_snippet", ""),
                        "published_at": paper.get("published_at"),
                        "source": paper.get("source", "arxiv"),
                        "source_url": paper.get("source_url"),
                        "pdf_url": paper.get("pdf_url"),
                        "remote_id": paper.get("remote_id"),
                        "remote_ingest_token": paper.get("remote_ingest_token"),
                        "canonical_key": paper.get("canonical_key"),
                        "in_library": bool(paper.get("in_library")),
                        "local_paper_id": paper.get("local_paper_id"),
                        "local_match_key": paper.get("local_match_key"),
                        "recommendation_score": paper.get("recommendation_score"),
                        "recommendation_reasons": paper.get("recommendation_reasons", []),
                    }
                    for paper in papers
                ],
                "keywords": keywords,
                "is_test": is_test,
                "paper_count": len(papers),
                "feedback": {},
            },
        )
        self.session.add(notification)
        await self.session.flush()
        return {
            "delivered": True,
            "notification_id": str(notification.id),
            "paper_count": len(papers),
            "keywords": keywords,
            "message": (
                f"测试通知已创建，共找到 {len(papers)} 篇相关论文。"
                if papers
                else "测试通知已创建，但当前没有匹配的新论文。"
            ),
            "sent_at": now.isoformat(),
        }


class ExperimentService:
    """实验记录板服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_experiment(
        self,
        project_id: str,
        name: str,
        hyperparams: dict,
        dataset: str,
        results: dict,
        notes: str = "",
        idea_id: str | None = None,
    ) -> dict:
        """记录一次实验。"""
        from app.db.models.research import ResearchProject
        from uuid import UUID, uuid4

        result = await self.session.execute(
            select(ResearchProject).where(ResearchProject.id == UUID(project_id))
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # 追加实验记录（保留已有数据）
        existing = dict(project.metadata_json or {})
        exp_list = list(existing.get("experiments", []))
        experiment = {
            "experiment_id": str(uuid4()),
            "idea_id": idea_id,
            "name": name,
            "hyperparams": hyperparams,
            "dataset": dataset,
            "results": results,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        exp_list.append(experiment)
        existing["experiments"] = exp_list
        project.metadata_json = existing
        await self.session.commit()

        return {"success": True, "experiment_count": len(exp_list), "experiment": experiment}

    async def get_experiments(self, project_id: str) -> list[dict]:
        """获取项目的实验记录。"""
        from app.db.models.research import ResearchProject
        from uuid import UUID

        result = await self.session.execute(
            select(ResearchProject).where(ResearchProject.id == UUID(project_id))
        )
        project = result.scalar_one_or_none()
        if not project:
            return []

        experiments = project.metadata_json or {}
        return experiments.get("experiments", [])


class ShareService:
    """研究分享服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_share_link(self, project_id: str) -> str:
        """生成分享链接（使用简单的 UUID token）。"""
        from uuid import uuid4, UUID
        from app.db.models.research import ResearchProject

        result = await self.session.execute(
            select(ResearchProject).where(ResearchProject.id == UUID(project_id))
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # 生成随机分享 token
        token = str(uuid4())[:8]
        # 保留已有数据
        existing = dict(project.metadata_json or {})
        existing["share_token"] = token
        project.metadata_json = existing
        await self.session.commit()

        return token

    async def get_shared_project(self, token: str) -> dict | None:
        """通过分享 token 获取项目数据。"""
        from app.db.models.research import ResearchProject, ResearchIdea
        from sqlalchemy import select, or_

        result = await self.session.execute(
            select(ResearchProject)
        )
        for project in result.scalars().all():
            meta = project.metadata_json or {}
            if meta.get("share_token") == token:
                ideas_result = await self.session.execute(
                    select(ResearchIdea).where(ResearchIdea.project_id == project.id)
                )
                ideas = ideas_result.scalars().all()
                return {
                    "project": {
                        "name": project.name,
                        "description": project.description,
                        "keywords": project.keywords,
                    },
                    "ideas": [
                        {"title": i.title, "description": i.description,
                         "feasibility_score": i.feasibility_score,
                         "novelty_score": i.novelty_score}
                        for i in ideas
                    ],
                }
        return None
