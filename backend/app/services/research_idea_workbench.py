"""Evidence-grounded Research Idea Workbench.

This service intentionally does not build on the legacy one-shot research
pipeline. It persists inspectable artifacts at each stage so the UI can show
how a research proposal was formed.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.paper import Paper
from app.db.models.research import ResearchIdea, ResearchIdeaRun, ResearchProject
from app.services.hybrid_search import HybridSearchService
from app.services.llm import llm_service

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[dict[str, Any]], Optional[Awaitable[None]]]

STAGES = {
    "briefing": (4, "正在整理研究简报"),
    "retrieving": (18, "正在从论文库收集背景与灵感证据"),
    "mapping_gaps": (38, "正在提取可验证的研究空白"),
    "gap_review": (48, "Gap Map 已就绪，等待选择推进方向"),
    "generating": (56, "正在通过多条路径生成候选假设"),
    "deduplicating": (68, "正在合并重复方向"),
    "reviewing": (82, "正在进行六维评审"),
    "selecting": (94, "正在整理最值得推进的 Proposal"),
    "complete": (100, "Idea 工作台已完成"),
}
GAP_FEEDBACK_RATINGS = {"strong", "promising", "weak", "reject"}
GAP_FEEDBACK_LABELS = {
    "valuable",
    "too_broad",
    "evidence_weak",
    "already_done",
    "misaligned",
    "needs_narrowing",
    "high_potential",
}

REVIEW_WEIGHTS = {
    "novelty": 0.25,
    "evidence_grounding": 0.20,
    "feasibility": 0.20,
    "testability": 0.15,
    "impact": 0.15,
    "clarity": 0.05,
}


class ResearchIdeaWorkbenchService:
    """Build evidence-grounded research proposals through visible stages."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.search = HybridSearchService(session)

    async def create_run(
        self,
        project: ResearchProject,
        num_ideas: int = 3,
        external_search: bool = True,
    ) -> ResearchIdeaRun:
        run = ResearchIdeaRun(
            project_id=project.id,
            status="pending",
            stage="briefing",
            progress=0,
            message="等待启动",
            config_json={
                "num_ideas": num_ideas,
                "external_search": external_search,
                "evidence_scope": "local_and_external" if external_search else "local_library",
            },
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def execute(
        self,
        project: ResearchProject,
        run: ResearchIdeaRun,
        num_ideas: int = 3,
        on_progress: ProgressCallback | None = None,
    ) -> list[ResearchIdea]:
        """Execute the pipeline and persist every inspectable artifact."""
        try:
            await self._transition(run, "briefing", status="running", callback=on_progress)
            brief = self._project_brief(project)

            await self._transition(run, "retrieving", callback=on_progress)
            evidence_map = await self.collect_evidence(
                project,
                brief,
                external_search=bool((run.config_json or {}).get("external_search", True)),
            )
            await self._save_artifact(run, "evidence_map", evidence_map, on_progress)

            await self._transition(run, "mapping_gaps", callback=on_progress)
            gap_map = await self.extract_gap_map(brief, evidence_map)
            await self._save_artifact(run, "gap_map", gap_map, on_progress)

            ideas = await self._execute_from_gap_map(
                project,
                run,
                brief,
                evidence_map,
                gap_map,
                num_ideas,
                on_progress=on_progress,
            )
            await self._transition(run, "complete", status="complete", callback=on_progress)
            return ideas
        except Exception as exc:
            logger.exception("Research Idea Workbench run failed: %s", exc)
            run.status = "failed"
            run.error = str(exc)
            run.message = "Idea 工作台运行失败，请稍后重试"
            await self.session.commit()
            await self._emit(
                on_progress,
                {"type": "error", "message": run.message, "detail": run.error},
            )
            raise

    async def execute_gap_preview(
        self,
        project: ResearchProject,
        run: ResearchIdeaRun,
        on_progress: ProgressCallback | None = None,
    ) -> ResearchIdeaRun:
        """Execute through Gap Map extraction and pause for user selection."""
        try:
            await self._transition(run, "briefing", status="running", callback=on_progress)
            brief = self._project_brief(project)

            await self._transition(run, "retrieving", callback=on_progress)
            evidence_map = await self.collect_evidence(
                project,
                brief,
                external_search=bool((run.config_json or {}).get("external_search", True)),
            )
            await self._save_artifact(run, "evidence_map", evidence_map, on_progress)

            await self._transition(run, "mapping_gaps", callback=on_progress)
            gap_map = await self.extract_gap_map(brief, evidence_map)
            await self._save_artifact(run, "gap_map", gap_map, on_progress)

            await self._transition(run, "gap_review", status="pending", callback=on_progress)
            return run
        except Exception as exc:
            logger.exception("Research Idea Workbench gap preview failed: %s", exc)
            run.status = "failed"
            run.error = str(exc)
            run.message = "Gap Map 预览失败，请稍后重试"
            await self.session.commit()
            await self._emit(
                on_progress,
                {"type": "error", "message": run.message, "detail": run.error},
            )
            raise

    async def continue_from_gap_review(
        self,
        project: ResearchProject,
        run: ResearchIdeaRun,
        *,
        gap_selection: dict[str, Any] | None = None,
        generation_constraints: dict[str, Any] | None = None,
        num_ideas: int = 3,
        on_progress: ProgressCallback | None = None,
    ) -> list[ResearchIdea]:
        """Continue a persisted Gap Map run after user selection."""
        try:
            brief = self._project_brief(project)
            evidence_map = run.evidence_map or await self.collect_evidence(
                project,
                brief,
                external_search=bool((run.config_json or {}).get("external_search", True)),
            )
            if not run.evidence_map:
                await self._save_artifact(run, "evidence_map", evidence_map, on_progress)
            gap_map = run.gap_map or await self.extract_gap_map(brief, evidence_map)
            if not run.gap_map:
                await self._save_artifact(run, "gap_map", gap_map, on_progress)
            selection = self.normalize_gap_selection(gap_map, gap_selection, generation_constraints)
            config = dict(run.config_json or {})
            config["num_ideas"] = num_ideas
            config["gap_selection"] = selection["gap_selection"]
            config["generation_constraints"] = selection["generation_constraints"]
            run.config_json = config
            await self.session.commit()

            constrained_gap_map = self.apply_gap_selection(gap_map, selection)
            run.gap_map = constrained_gap_map
            await self.session.commit()
            await self._emit(on_progress, {"type": "artifact", "artifact": "gap_map", "data": constrained_gap_map})

            await self._transition(run, "generating", status="running", callback=on_progress)
            ideas = await self._execute_from_gap_map(
                project,
                run,
                brief,
                evidence_map,
                constrained_gap_map,
                num_ideas,
                on_progress=on_progress,
            )
            await self._transition(run, "complete", status="complete", callback=on_progress)
            return ideas
        except Exception as exc:
            logger.exception("Research Idea Workbench continuation failed: %s", exc)
            run.status = "failed"
            run.error = str(exc)
            run.message = "Gap Map 继续生成失败，请稍后重试"
            await self.session.commit()
            await self._emit(
                on_progress,
                {"type": "error", "message": run.message, "detail": run.error},
            )
            raise

    async def save_gap_feedback(
        self,
        run: ResearchIdeaRun,
        gap_index: int,
        feedback: dict[str, Any] | None,
    ) -> ResearchIdeaRun:
        """Persist user edits and feedback for a single Gap Map item."""
        gap_map = dict(run.gap_map or {})
        gaps = list(gap_map.get("gaps") or [])
        if gap_index < 0 or gap_index >= len(gaps):
            raise ValueError("Gap Map 条目不存在")
        evidence_ids = self._available_evidence_ids(run.evidence_map or {})
        gaps[gap_index] = self.normalize_gap_feedback(gaps[gap_index], feedback or {}, evidence_ids)
        run.gap_map = {**gap_map, "gaps": gaps, "feedback_summary": self.summarize_gap_feedback({"gaps": gaps})}
        config = dict(run.config_json or {})
        config["gap_feedback"] = run.gap_map["feedback_summary"]
        run.config_json = config
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def refine_gap(
        self,
        project: ResearchProject,
        run: ResearchIdeaRun,
        gap_index: int,
        *,
        focus_note: str = "",
    ) -> ResearchIdeaRun:
        """Refine one Gap Map item using current evidence and user feedback."""
        gap_map = dict(run.gap_map or {})
        gaps = list(gap_map.get("gaps") or [])
        if gap_index < 0 or gap_index >= len(gaps):
            raise ValueError("Gap Map 条目不存在")
        brief = self._project_brief(project)
        evidence_map = run.evidence_map or {}
        current_gap = gaps[gap_index] if isinstance(gaps[gap_index], dict) else {}
        focus_note = str(focus_note or "").strip()[:600]
        linked_evidence = self._evidence_items_by_ids(evidence_map, current_gap.get("evidence_ids") or [])
        prompt = f"""你是科研 Gap Map 编辑器。请只细化一个研究空白，不要生成 proposal。
要求：
- 保留与证据相关的边界，避免扩大主题。
- 如果用户反馈认为 gap 太宽泛或证据不足，需要让问题更窄、更可验证。
- 输出严格 JSON：
{{"title":"...", "limitation":"...", "opportunity":"...", "research_question":"...", "evidence_ids":["paper uuid"], "uncertainty":"...", "evidence_rationale":"为什么这些证据支持该 gap"}}

研究简报：{json.dumps(brief, ensure_ascii=False)}
当前 Gap：{json.dumps(current_gap, ensure_ascii=False)}
用户反馈：{json.dumps(current_gap.get("user_feedback") or {}, ensure_ascii=False)}
用户细化要求：{focus_note}
相关证据：{json.dumps(linked_evidence, ensure_ascii=False)}
"""
        source = "llm"
        data = await self._chat_json(prompt)
        refined = data.get("gap") if isinstance(data, dict) and isinstance(data.get("gap"), dict) else data
        if not isinstance(refined, dict) or not any(refined.get(key) for key in ("title", "limitation", "research_question")):
            source = "fallback"
            refined = self._fallback_refined_gap(brief, current_gap, focus_note)
        normalized = self._normalize_gap(refined, brief, evidence_map)
        if not normalized.get("evidence_ids"):
            normalized["evidence_ids"] = list(current_gap.get("evidence_ids") or [])[:4]
        updated = {
            **current_gap,
            **normalized,
            "user_feedback": current_gap.get("user_feedback") or {},
            "refinement": {
                "source": source,
                "focus_note": focus_note,
                "previous_title": current_gap.get("title"),
            },
        }
        gaps[gap_index] = updated
        run.gap_map = {**gap_map, "gaps": gaps, "feedback_summary": self.summarize_gap_feedback({"gaps": gaps})}
        config = dict(run.config_json or {})
        config["gap_feedback"] = run.gap_map["feedback_summary"]
        run.config_json = config
        run.stage = "gap_review"
        run.progress = STAGES["gap_review"][0]
        run.message = "Gap Map 已更新，等待选择推进方向"
        if run.status != "failed":
            run.status = "pending"
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def _execute_from_gap_map(
        self,
        project: ResearchProject,
        run: ResearchIdeaRun,
        brief: dict[str, Any],
        evidence_map: dict[str, Any],
        gap_map: dict[str, Any],
        num_ideas: int,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> list[ResearchIdea]:
        generation_context = self.generation_context_from_run(run, gap_map)
        if run.stage != "generating":
            await self._transition(run, "generating", callback=on_progress)
        candidates = await self.generate_candidates(brief, evidence_map, gap_map, num_ideas, generation_context=generation_context)
        tree_candidates, tree_summary = await self.expand_candidate_tree(
            candidates,
            brief,
            evidence_map,
            gap_map,
            generation_context=generation_context,
            rounds=2,
            beam_width=max(num_ideas * 2, 4),
        )
        await self._emit(
            on_progress,
            {"type": "artifact", "artifact": "search_tree", "data": tree_summary},
        )

        await self._transition(run, "deduplicating", callback=on_progress)
        unique_candidates, duplicate_groups = self.deduplicate_candidates(tree_candidates)
        run.candidate_pool = unique_candidates
        await self.session.commit()
        await self._emit(
            on_progress,
            {"type": "artifact", "artifact": "candidate_pool", "data": unique_candidates},
        )

        await self._transition(run, "reviewing", callback=on_progress)
        reviewed = await self.review_candidates(brief, evidence_map, unique_candidates)
        similar_work_context = await self.collect_similar_work(
            brief,
            evidence_map,
            reviewed,
            external_search=bool((run.config_json or {}).get("external_search", True)),
        )
        novelty_checked = self.novelty_check_candidates(
            reviewed,
            evidence_map,
            similar_work_pool=similar_work_context["items"],
            source_coverage=similar_work_context["source_coverage"],
        )
        adversarial_reviewed = self.adversarial_review_candidates(novelty_checked)
        reviewed = self.apply_quality_adjustments(adversarial_reviewed)
        selected, diversity_summary = self.select_diverse_proposals(reviewed, num_ideas)
        selected = [{**candidate, "gap_selection": generation_context.get("gap_selection")} for candidate in selected]
        run.candidate_pool = reviewed
        run.review_summary = {
            "rubric": REVIEW_WEIGHTS,
            "duplicates": duplicate_groups,
            "search_tree": tree_summary,
            "reviewed_count": len(reviewed),
            "novelty": self._summarize_novelty(reviewed),
            "adversarial": self._summarize_adversarial(reviewed),
            "source_coverage": similar_work_context["source_coverage"],
            "diversity_selection": diversity_summary,
            "gap_selection": generation_context.get("gap_selection"),
            "generation_constraints": generation_context.get("generation_constraints"),
            "gap_feedback": generation_context.get("gap_feedback") or [],
        }
        await self.session.commit()
        await self._emit(
            on_progress,
            {"type": "artifact", "artifact": "review_summary", "data": run.review_summary},
        )

        await self._transition(run, "selecting", callback=on_progress)
        ideas = await self.persist_top_proposals(run, selected, evidence_map, num_ideas)
        return ideas

    async def _transition(
        self,
        run: ResearchIdeaRun,
        stage: str,
        *,
        status: str | None = None,
        callback: ProgressCallback | None = None,
    ) -> None:
        progress, message = STAGES[stage]
        run.stage = stage
        run.progress = progress
        run.message = message
        if status:
            run.status = status
        await self.session.commit()
        await self._emit(
            callback,
            {
                "type": "stage",
                "stage": stage,
                "status": run.status,
                "progress": progress,
                "message": message,
            },
        )

    async def _save_artifact(
        self,
        run: ResearchIdeaRun,
        artifact: str,
        data: Any,
        callback: ProgressCallback | None,
    ) -> None:
        setattr(run, artifact, data)
        await self.session.commit()
        await self._emit(callback, {"type": "artifact", "artifact": artifact, "data": data})

    @staticmethod
    async def _emit(callback: ProgressCallback | None, event: dict[str, Any]) -> None:
        if not callback:
            return
        result = callback(event)
        if inspect.isawaitable(result):
            await result

    @staticmethod
    def _project_brief(project: ResearchProject) -> dict[str, Any]:
        return {
            "name": project.name,
            "description": project.description or "",
            "keywords": project.keywords or [],
            "user_seed": (project.metadata_json or {}).get("user_seed", ""),
            "seed_collections": (project.metadata_json or {}).get("seed_collections", []),
        }

    async def collect_evidence(
        self,
        project: ResearchProject,
        brief: dict[str, Any],
        *,
        external_search: bool = True,
    ) -> dict[str, Any]:
        """Collect local evidence and make its role explicit."""
        manual_ids = []
        for value in project.paper_ids or []:
            try:
                manual_ids.append(UUID(str(value)))
            except ValueError:
                continue

        manual_papers = []
        if manual_ids:
            result = await self.session.execute(select(Paper).where(Paper.id.in_(manual_ids)))
            manual_papers = list(result.scalars().all())

        query = " ".join(
            part for part in [brief["name"], brief["description"], " ".join(brief["keywords"])] if part
        )
        paper_scores = await self.search.search(query, top_k=12, mode="hybrid")
        retrieved = await self.search.fetch_papers(paper_scores)
        score_by_id = {str(paper.id): score for paper, score in retrieved}

        seen = {str(paper.id) for paper in manual_papers}
        background = []
        inspiration = []
        for paper, score in retrieved:
            if str(paper.id) in seen:
                continue
            seen.add(str(paper.id))
            target = background if len(background) < 6 else inspiration
            target.append(self._evidence_item(paper, "background" if target is background else "inspiration", score))

        if len(background) + len(inspiration) < 4:
            result = await self.session.execute(select(Paper).order_by(Paper.created_at.desc()).limit(8))
            for paper in result.scalars().all():
                if str(paper.id) in seen:
                    continue
                seen.add(str(paper.id))
                target = background if len(background) < 6 else inspiration
                target.append(self._evidence_item(paper, "background" if target is background else "inspiration", 0.0))

        collection_by_paper: dict[str, list[dict[str, str]]] = {}
        for collection in brief.get("seed_collections", []) or []:
            for paper_id in collection.get("paper_ids", []) or []:
                collection_by_paper.setdefault(str(paper_id), []).append({
                    "id": str(collection.get("id", "")),
                    "name": str(collection.get("name", "未命名分类")),
                })
        seeds = [
            self._evidence_item(
                paper,
                "seed",
                score_by_id.get(str(paper.id), 1.0),
                collections=collection_by_paper.get(str(paper.id), []),
            )
            for paper in manual_papers
        ]
        external, source_errors = await self._collect_external_evidence(query) if external_search else ([], {})
        local_keys = {self._evidence_dedup_key(item) for item in [*seeds, *background, *inspiration]}
        for item in external:
            key = self._evidence_dedup_key(item)
            if key in local_keys:
                continue
            local_keys.add(key)
            inspiration.append(item)

        return {
            "scope": "local_and_external" if external_search else "local_library",
            "query": query,
            "seed": seeds,
            "background": background,
            "inspiration": inspiration,
            "source_errors": source_errors,
            "counts": {
                "seed": len(seeds),
                "background": len(background),
                "inspiration": len(inspiration),
                "external": len(external),
            },
            "collection_sources": [
                {
                    "id": str(collection.get("id", "")),
                    "name": str(collection.get("name", "未命名分类")),
                    "paper_count": len(collection.get("paper_ids", []) or []),
                }
                for collection in (brief.get("seed_collections", []) or [])
            ],
        }

    @staticmethod
    def _evidence_item(
        paper: Paper,
        category: str,
        score: float,
        *,
        collections: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        abstract = re.sub(r"\s+", " ", paper.abstract or "").strip()
        reason = {
            "seed": "用户主动选入的核心论文",
            "background": "与研究简报高度相关，可用于界定现有方法与限制",
            "inspiration": "可用于跨论文组合或寻找不同技术路径",
        }[category]
        item = {
            "paper_id": str(paper.id),
            "title": paper.title,
            "year": paper.year,
            "arxiv_id": paper.arxiv_id,
            "category": category,
            "score": round(float(score), 4),
            "abstract_excerpt": abstract[:700],
            "relevance": reason,
            "source": "local_library",
            "source_url": paper.source_url,
        }
        if collections:
            item["collection_ids"] = [collection["id"] for collection in collections if collection.get("id")]
            item["collection_names"] = [collection["name"] for collection in collections if collection.get("name")]
        return item

    async def _collect_external_evidence(self, query: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """Collect scholarly evidence without making the run depend on network health."""
        from app.services.paper_search import arxiv_service, semantic_scholar_service

        sources = {
            "semantic_scholar": semantic_scholar_service.search(query, max_results=5),
            "arxiv": arxiv_service.search(query, max_results=5, sort_by="relevance"),
        }
        results = await asyncio.gather(*sources.values(), return_exceptions=True)
        evidence = []
        errors = {}
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                errors[source] = str(result)
                logger.warning("Workbench external source %s failed: %s", source, result)
                continue
            for paper in result:
                evidence.append(self._external_evidence_item(paper, source))
        unique = []
        seen = set()
        for item in evidence:
            key = self._evidence_dedup_key(item)
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique[:8], errors

    async def collect_similar_work(
        self,
        brief: dict[str, Any],
        evidence_map: dict[str, Any],
        candidates: list[dict[str, Any]],
        *,
        external_search: bool = True,
    ) -> dict[str, Any]:
        """Build a reusable similar-work pool for candidate novelty checks."""
        local_items = [
            {**item, "relation": "generation_evidence"}
            for category in ("seed", "background", "inspiration")
            for item in evidence_map.get(category, [])
            if isinstance(item, dict)
        ]
        external_items: list[dict[str, Any]] = []
        source_errors = dict(evidence_map.get("source_errors") or {})
        query = self._similar_work_query(brief, candidates)
        if external_search and query:
            external_items, new_errors = await self._collect_external_evidence(query)
            source_errors.update(new_errors)

        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in [*local_items, *external_items]:
            key = self._evidence_dedup_key(item)
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(item)

        source_counts: dict[str, int] = {}
        for item in unique:
            source = str(item.get("source") or item.get("category") or "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        coverage = {
            "query": query,
            "local_count": len(local_items),
            "external_count": len(external_items),
            "total_count": len(unique),
            "sources": source_counts,
            "source_errors": source_errors,
        }
        return {"items": unique, "source_coverage": coverage}

    @staticmethod
    def _similar_work_query(brief: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
        parts = [
            str(brief.get("name") or ""),
            " ".join(str(item) for item in (brief.get("keywords") or [])[:4]),
        ]
        for candidate in candidates[:3]:
            parts.append(str(candidate.get("title") or ""))
            hypothesis = str(candidate.get("hypothesis") or "")
            if hypothesis:
                parts.append(" ".join(re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]+", hypothesis)[:8]))
        tokens = []
        seen = set()
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]+|[\u4e00-\u9fff]{2,}", " ".join(parts)):
            key = token.lower()
            if key in seen:
                continue
            seen.add(key)
            tokens.append(token)
            if len(tokens) >= 16:
                break
        return " ".join(tokens)

    @staticmethod
    def _external_evidence_item(paper: Any, source: str) -> dict[str, Any]:
        identity = paper.doi or paper.arxiv_id or ResearchIdeaWorkbenchService._title_key(paper.title)
        return {
            "paper_id": f"ext:{source}:{identity}",
            "title": paper.title,
            "year": paper.year,
            "arxiv_id": paper.arxiv_id,
            "doi": paper.doi,
            "category": "inspiration",
            "score": 0.65 if source == "arxiv" else 0.7,
            "abstract_excerpt": re.sub(r"\s+", " ", paper.abstract or "").strip()[:700],
            "relevance": "联网补充的近期或跨领域文献，用于新颖性检查与灵感扩展",
            "source": source,
            "source_url": paper.source_url,
        }

    @staticmethod
    def _evidence_dedup_key(item: dict[str, Any]) -> str:
        title_key = ResearchIdeaWorkbenchService._title_key(item.get("title", ""))
        return str(title_key or item.get("doi") or item.get("arxiv_id") or item.get("paper_id", "")).lower()

    @staticmethod
    def _title_key(title: str) -> str:
        return "-".join(re.findall(r"[a-z0-9\u4e00-\u9fff]+", (title or "").lower()))[:180]

    async def extract_gap_map(
        self, brief: dict[str, Any], evidence_map: dict[str, Any]
    ) -> dict[str, Any]:
        evidence_text = self._format_evidence(evidence_map, limit=10)
        prompt = f"""你是严谨的科研导师。基于研究简报与论文证据提取可验证的研究空白。
不要编造论文中没有出现的结论。输出严格 JSON：
{{"summary":"...", "gaps":[{{"title":"...", "limitation":"...", "opportunity":"...",
"research_question":"...", "evidence_ids":["paper uuid"], "uncertainty":"..."}}]}}
生成 3-5 个 gap。

研究简报：{json.dumps(brief, ensure_ascii=False)}
论文证据：
{evidence_text}
"""
        data = await self._chat_json(prompt)
        gaps = data.get("gaps") if isinstance(data, dict) else None
        if not isinstance(gaps, list) or not gaps:
            return self._fallback_gap_map(brief, evidence_map)
        return {
            "summary": str(data.get("summary") or f"围绕「{brief['name']}」识别出的研究机会"),
            "gaps": [self._normalize_gap(gap, brief, evidence_map) for gap in gaps[:5]],
        }

    def normalize_gap_selection(
        self,
        gap_map: dict[str, Any],
        gap_selection: dict[str, Any] | None,
        generation_constraints: dict[str, Any] | None,
    ) -> dict[str, Any]:
        gaps = gap_map.get("gaps") or []
        available_titles = [str(gap.get("title") or "") for gap in gaps if isinstance(gap, dict)]
        requested_selected = self._string_list((gap_selection or {}).get("selected_gap_titles"), limit=8)
        requested_blocked = self._string_list((gap_selection or {}).get("blocked_gap_titles"), limit=8)
        available = set(available_titles)
        selected = [title for title in requested_selected if title in available]
        blocked = [title for title in requested_blocked if title in available and title not in selected]
        if not selected:
            selected = [title for title in available_titles if title not in blocked] or available_titles
        constraints = self._normalize_generation_constraints(generation_constraints)
        focus_note = str((gap_selection or {}).get("focus_note") or "").strip()[:600]
        return {
            "gap_selection": {
                "selected_gap_titles": selected,
                "blocked_gap_titles": blocked,
                "focus_note": focus_note,
                "selection_mode": "user_selected" if requested_selected or blocked or focus_note else "default_all_gaps",
            },
            "generation_constraints": constraints,
        }

    def normalize_gap_feedback(
        self,
        current_gap: Any,
        feedback: dict[str, Any],
        available_evidence_ids: set[str],
    ) -> dict[str, Any]:
        data = feedback if isinstance(feedback, dict) else {}
        gap = current_gap if isinstance(current_gap, dict) else {}

        def text_field(key: str, limit: int = 1200) -> str:
            raw = data.get(key)
            if raw is None:
                raw = gap.get(key)
            return str(raw or "").strip()[:limit]

        requested_evidence = data.get("evidence_ids")
        if requested_evidence is None:
            requested_evidence = gap.get("evidence_ids") or []
        evidence_ids = []
        for item in self._string_list(requested_evidence, limit=8):
            if not available_evidence_ids or item in available_evidence_ids:
                evidence_ids.append(item)
        rating = str(data.get("rating") or (gap.get("user_feedback") or {}).get("rating") or "promising").strip()
        if rating not in GAP_FEEDBACK_RATINGS:
            rating = "promising"
        raw_labels = data["labels"] if "labels" in data else (gap.get("user_feedback") or {}).get("labels")
        labels = [
            label
            for label in self._string_list(raw_labels, limit=8)
            if label in GAP_FEEDBACK_LABELS
        ]
        note = str(data.get("note") if data.get("note") is not None else (gap.get("user_feedback") or {}).get("note") or "").strip()[:600]
        return {
            **gap,
            "title": text_field("title", 240) or str(gap.get("title") or "未命名 Gap"),
            "limitation": text_field("limitation"),
            "opportunity": text_field("opportunity"),
            "research_question": text_field("research_question"),
            "evidence_ids": evidence_ids,
            "uncertainty": text_field("uncertainty", 800),
            "evidence_rationale": text_field("evidence_rationale", 800),
            "user_feedback": {
                "rating": rating,
                "labels": labels,
                "note": note,
            },
        }

    @staticmethod
    def _normalize_generation_constraints(value: dict[str, Any] | None) -> dict[str, str]:
        data = value if isinstance(value, dict) else {}

        def choice(key: str, allowed: set[str], default: str) -> str:
            raw = str(data.get(key) or default).strip()
            return raw if raw in allowed else default

        return {
            "research_mode": choice("research_mode", {"balanced", "theory", "experiment", "system", "application"}, "balanced"),
            "risk_appetite": choice("risk_appetite", {"conservative", "balanced", "high_risk"}, "balanced"),
            "resource_budget": choice("resource_budget", {"low_compute", "reproducible", "large_model"}, "reproducible"),
        }

    @staticmethod
    def _string_list(value: Any, *, limit: int = 8) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value[:limit] if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _format_generation_constraints(context: dict[str, Any] | None) -> str:
        data = context if isinstance(context, dict) else {}
        selection = data.get("gap_selection") or {}
        constraints = data.get("generation_constraints") or {}
        return json.dumps({
            "selected_gap_titles": selection.get("selected_gap_titles") or [],
            "blocked_gap_titles": selection.get("blocked_gap_titles") or [],
            "focus_note": selection.get("focus_note") or "",
            "research_mode": constraints.get("research_mode") or "balanced",
            "risk_appetite": constraints.get("risk_appetite") or "balanced",
            "resource_budget": constraints.get("resource_budget") or "reproducible",
            "gap_feedback": data.get("gap_feedback") or [],
        }, ensure_ascii=False)

    def apply_gap_selection(self, gap_map: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
        gap_selection = selection.get("gap_selection") or {}
        selected_titles = set(gap_selection.get("selected_gap_titles") or [])
        blocked_titles = set(gap_selection.get("blocked_gap_titles") or [])
        selected_gaps = []
        blocked_gaps = []
        for gap in gap_map.get("gaps") or []:
            title = str(gap.get("title") or "")
            annotated = {
                **gap,
                "selection_status": "selected" if title in selected_titles else "blocked" if title in blocked_titles else "unselected",
            }
            if title in selected_titles:
                selected_gaps.append(annotated)
            elif title in blocked_titles:
                blocked_gaps.append(annotated)
        if not selected_gaps:
            selected_gaps = [
                {**gap, "selection_status": "selected"}
                for gap in (gap_map.get("gaps") or [])
                if str(gap.get("title") or "") not in blocked_titles
            ]
        return {
            **gap_map,
            "gaps": selected_gaps,
            "blocked_gaps": blocked_gaps,
            "selection": gap_selection,
            "generation_constraints": selection.get("generation_constraints") or {},
            "summary": f"{gap_map.get('summary') or 'Gap Map'}（已按用户选择约束生成）",
        }

    def generation_context_from_run(self, run: ResearchIdeaRun, gap_map: dict[str, Any]) -> dict[str, Any]:
        config = dict(run.config_json or {})
        feedback_summary = self.summarize_gap_feedback(gap_map)
        if config.get("gap_selection") or config.get("generation_constraints"):
            return {
                "gap_selection": config.get("gap_selection") or self.normalize_gap_selection(gap_map, None, None)["gap_selection"],
                "generation_constraints": config.get("generation_constraints") or self._normalize_generation_constraints(None),
                "gap_feedback": feedback_summary,
            }
        normalized = self.normalize_gap_selection(gap_map, None, None)
        normalized["gap_feedback"] = feedback_summary
        return normalized

    async def generate_candidates(
        self,
        brief: dict[str, Any],
        evidence_map: dict[str, Any],
        gap_map: dict[str, Any],
        num_ideas: int,
        *,
        generation_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        requested = max(num_ideas * 3, 8)
        constraints_text = self._format_generation_constraints(generation_context)
        prompt = f"""你是研究 Idea 工作台。基于 Gap Map 与证据生成 {requested} 个候选假设。
候选必须来自多条路径：grounded（从 gap 推导）、inspiration（跨论文组合）、seed_refinement（优化用户种子想法；若无种子则可省略）。
输出严格 JSON：
{{"candidates":[{{"title":"...", "path":"grounded|inspiration|seed_refinement",
"gap":"...", "hypothesis":"可证伪假设", "approach":"技术草图", "evidence_ids":["paper uuid"],
"risks":["..."], "falsification_test":"...", "minimum_experiment":{{"dataset":"...",
"baselines":["..."], "metrics":["..."], "steps":["..."]}}}}]}}
禁止只输出宽泛方向，每条必须可以设计最小实验验证。

研究简报：{json.dumps(brief, ensure_ascii=False)}
Gap Map：{json.dumps(gap_map, ensure_ascii=False)}
用户选择与生成约束：{constraints_text}
证据：{self._format_evidence(evidence_map, limit=10)}
"""
        data = await self._chat_json(prompt)
        candidates = data.get("candidates") if isinstance(data, dict) else None
        if not isinstance(candidates, list) or not candidates:
            candidates = self._fallback_candidates(brief, evidence_map, gap_map, requested, generation_context=generation_context)
        normalized = [self._normalize_candidate(item, brief, evidence_map, index) for index, item in enumerate(candidates)]
        if len(normalized) < requested:
            normalized.extend(self._fallback_candidates(brief, evidence_map, gap_map, requested - len(normalized), offset=len(normalized), generation_context=generation_context))
        return normalized[:requested]

    @classmethod
    def deduplicate_candidates(
        cls, candidates: list[dict[str, Any]], threshold: float = 0.72
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        unique: list[dict[str, Any]] = []
        duplicate_groups: list[dict[str, Any]] = []
        for candidate in candidates:
            duplicate_of = None
            for existing in unique:
                if cls._candidate_similarity(candidate, existing) >= threshold:
                    duplicate_of = existing
                    break
            if duplicate_of:
                duplicate_groups.append(
                    {"kept": duplicate_of["title"], "merged": candidate["title"], "reason": "hypothesis_overlap"}
                )
            else:
                unique.append(candidate)
        return unique, duplicate_groups

    @staticmethod
    def _candidate_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
        left_tokens = ResearchIdeaWorkbenchService._dedup_tokens(f"{left.get('title', '')} {left.get('hypothesis', '')}")
        right_tokens = ResearchIdeaWorkbenchService._dedup_tokens(f"{right.get('title', '')} {right.get('hypothesis', '')}")
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)

    @staticmethod
    def _dedup_tokens(text: str) -> set[str]:
        """Use words and CJK bigrams so Chinese hypotheses are not over-merged."""
        normalized = (text or "").lower()
        words = set(re.findall(r"[a-z0-9]+(?:[-_.][a-z0-9]+)*", normalized))
        cjk_bigrams = {
            block[index:index + 2]
            for block in re.findall(r"[\u4e00-\u9fff]+", normalized)
            for index in range(max(len(block) - 1, 0))
        }
        return words | cjk_bigrams

    async def expand_candidate_tree(
        self,
        candidates: list[dict[str, Any]],
        brief: dict[str, Any] | None = None,
        evidence_map: dict[str, Any] | None = None,
        gap_map: dict[str, Any] | None = None,
        generation_context: dict[str, Any] | None = None,
        *,
        rounds: int = 2,
        beam_width: int = 6,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Bounded progressive tree search over candidate proposals."""
        roots = [self._with_tree_metadata(candidate, round_number=0, operator="root") for candidate in candidates]
        all_candidates = list(roots)
        frontier = roots[:beam_width]
        operators = ("strong_baseline", "failure_mode", "cost_aware", "mechanism_shift", "cross_domain_transfer")
        llm_evolved_count = 0
        for round_number in range(1, max(1, rounds)):
            next_frontier = await self.evolve_candidate_frontier(
                frontier[:beam_width],
                brief or {},
                evidence_map or {},
                gap_map or {},
                generation_context or {},
                round_number=round_number,
                target_count=max(beam_width, len(frontier[:beam_width])),
            )
            llm_evolved_count += sum(1 for item in next_frontier if item.get("tree", {}).get("source") == "llm")
            fallback_needed = max(0, beam_width - len(next_frontier))
            fallback_frontier = []
            for parent in frontier[:beam_width]:
                for operator in operators:
                    if fallback_needed <= 0 and next_frontier:
                        break
                    child = self._mutate_candidate(parent, operator, round_number)
                    fallback_frontier.append(child)
                    fallback_needed -= 1
                if fallback_needed <= 0 and next_frontier:
                    break
            expanded = [*next_frontier, *fallback_frontier]
            if not expanded:
                for parent in frontier[:beam_width]:
                    expanded.extend(self._mutate_candidate(parent, operator, round_number) for operator in operators[:3])
            all_candidates.extend(expanded)
            frontier = sorted(expanded, key=self._candidate_potential, reverse=True)[:beam_width]
        summary = {
            "rounds": rounds,
            "beam_width": beam_width,
            "root_count": len(roots),
            "expanded_count": max(0, len(all_candidates) - len(roots)),
            "operators": list(operators),
            "llm_evolved_count": llm_evolved_count,
            "fallback_count": max(0, len(all_candidates) - len(roots) - llm_evolved_count),
        }
        return all_candidates, summary

    async def evolve_candidate_frontier(
        self,
        frontier: list[dict[str, Any]],
        brief: dict[str, Any],
        evidence_map: dict[str, Any],
        gap_map: dict[str, Any],
        generation_context: dict[str, Any],
        *,
        round_number: int,
        target_count: int,
    ) -> list[dict[str, Any]]:
        if not frontier or target_count <= 0:
            return []
        constraints_text = self._format_generation_constraints(generation_context)
        prompt = f"""你是科研 Idea 树搜索中的审稿人与改写者。请 critique 当前候选，并演化出最多 {target_count} 个更强且彼此不同的候选。
可用 operator：mechanism_shift、strong_baseline、failure_mode、cost_aware、cross_domain_transfer。
输出严格 JSON：
{{"evolved":[{{"parent_title":"...", "operator":"mechanism_shift|strong_baseline|failure_mode|cost_aware|cross_domain_transfer",
"critique":"指出父候选最关键弱点", "improvement":"本轮如何改进", "selection_angle":"为什么这个方向值得保留",
"title":"...", "path":"grounded|inspiration|seed_refinement", "gap":"...", "hypothesis":"可证伪假设",
"approach":"技术草图", "evidence_ids":["paper uuid"], "risks":["..."], "falsification_test":"...",
"minimum_experiment":{{"dataset":"...", "baselines":["..."], "metrics":["..."], "steps":["..."]}}}}]}}
候选之间必须覆盖不同机制、数据场景或风险类型，禁止只改标题。

研究简报：{json.dumps(brief, ensure_ascii=False)}
Gap Map：{json.dumps(gap_map, ensure_ascii=False)}
用户选择与生成约束：{constraints_text}
证据：{self._format_evidence(evidence_map, limit=8)}
父候选：{json.dumps(frontier, ensure_ascii=False)}
"""
        data = await self._chat_json(prompt)
        evolved = data.get("evolved") if isinstance(data, dict) else None
        if not isinstance(evolved, list) or not evolved:
            return []
        parent_by_title = {str(parent.get("title")): parent for parent in frontier}
        normalized = []
        for index, item in enumerate(evolved[:target_count]):
            if not isinstance(item, dict):
                continue
            parent = parent_by_title.get(str(item.get("parent_title"))) or frontier[index % len(frontier)]
            candidate = self._normalize_candidate(item, brief, evidence_map, index)
            candidate["critique"] = str(item.get("critique") or "需要补强假设边界、强基线或实验可证伪性。")
            candidate["improvement"] = str(item.get("improvement") or "在父候选基础上加入更清晰的验证路径。")
            candidate["selection_angle"] = str(item.get("selection_angle") or "提供与父候选不同的推进角度。")
            operator = str(item.get("operator") or "mechanism_shift")
            normalized.append(self._with_tree_metadata(
                candidate,
                round_number=round_number,
                operator=operator,
                parent=parent,
                source="llm",
            ))
        return normalized

    def _with_tree_metadata(
        self,
        candidate: dict[str, Any],
        *,
        round_number: int,
        operator: str,
        parent: dict[str, Any] | None = None,
        source: str = "deterministic",
    ) -> dict[str, Any]:
        parent_tree = parent.get("tree", {}) if parent else {}
        lineage = list(parent_tree.get("lineage", []))
        if parent:
            lineage.append(parent.get("title", "parent"))
        return {
            **candidate,
            "tree": {
                "round": round_number,
                "operator": operator,
                "parent_title": parent.get("title") if parent else None,
                "lineage": lineage,
                "source": source,
            },
        }

    def _mutate_candidate(self, parent: dict[str, Any], operator: str, round_number: int) -> dict[str, Any]:
        experiment = dict(parent.get("minimum_experiment") or {})
        baselines = list(experiment.get("baselines") or [])
        metrics = list(experiment.get("metrics") or [])
        steps = list(experiment.get("steps") or [])
        risks = list(parent.get("risks") or [])

        if operator == "strong_baseline":
            baselines = list(dict.fromkeys([*baselines, "最新强基线", "无改动消融"]))
            metrics = list(dict.fromkeys([*metrics, "显著性检验"]))
            steps = list(dict.fromkeys([*steps, "在统一预算下复现强基线"]))
            suffix = "强基线验证"
            hypothesis_addition = "并且在强基线控制下仍保持收益"
        elif operator == "failure_mode":
            metrics = list(dict.fromkeys([*metrics, "失败率", "鲁棒性指标"]))
            steps = list(dict.fromkeys([*steps, "构造失败案例切片", "分析反例是否推翻假设"]))
            risks = list(dict.fromkeys([*risks, "失败案例可能暴露假设边界过窄"]))
            suffix = "失败模式审计"
            hypothesis_addition = "并能解释关键失败模式"
        else:
            metrics = list(dict.fromkeys([*metrics, "推理成本", "训练成本"]))
            steps = list(dict.fromkeys([*steps, "记录计算资源与延迟", "绘制效果-成本权衡曲线"]))
            risks = list(dict.fromkeys([*risks, "改进收益可能被额外计算成本抵消"]))
            suffix = "成本约束版本"
            hypothesis_addition = "同时保持可接受的资源成本"

        child = {
            **parent,
            "title": f"{parent.get('title', '候选假设')} · {suffix}",
            "hypothesis": f"{parent.get('hypothesis', '')}，{hypothesis_addition}。",
            "approach": f"{parent.get('approach', '')} 重点加入「{suffix}」检查。",
            "risks": risks,
            "minimum_experiment": {
                **experiment,
                "baselines": baselines or ["当前最强可复现基线"],
                "metrics": metrics or ["主要任务指标", "效率指标"],
                "steps": steps or ["复现基线", "运行改进版本", "误差分析"],
            },
        }
        return self._with_tree_metadata(child, round_number=round_number, operator=operator, parent=parent)

    def _candidate_potential(self, candidate: dict[str, Any]) -> float:
        evidence_bonus = min(len(candidate.get("evidence_ids", []) or []), 4) * 0.12
        experiment = candidate.get("minimum_experiment") or {}
        baseline_bonus = min(len(experiment.get("baselines", []) or []), 3) * 0.08
        metric_bonus = min(len(experiment.get("metrics", []) or []), 4) * 0.06
        specificity = min(len(self._dedup_tokens(candidate.get("hypothesis", ""))) / 20, 1.0)
        return evidence_bonus + baseline_bonus + metric_bonus + specificity

    def novelty_check_candidates(
        self,
        candidates: list[dict[str, Any]],
        evidence_map: dict[str, Any],
        *,
        similar_work_pool: list[dict[str, Any]] | None = None,
        source_coverage: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        evidence_items = similar_work_pool or [
            item
            for category in ("seed", "background", "inspiration")
            for item in evidence_map.get(category, [])
        ]
        coverage = source_coverage or {
            "query": "",
            "local_count": len(evidence_items),
            "external_count": 0,
            "total_count": len(evidence_items),
            "sources": {},
            "source_errors": dict(evidence_map.get("source_errors") or {}),
        }
        return [
            {**candidate, "novelty_check": self._novelty_check(candidate, evidence_items, coverage)}
            for candidate in candidates
        ]

    def _novelty_check(
        self,
        candidate: dict[str, Any],
        evidence_items: list[dict[str, Any]],
        source_coverage: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        candidate_tokens = self._dedup_tokens(
            f"{candidate.get('title', '')} {candidate.get('hypothesis', '')} {candidate.get('approach', '')}"
        )
        ranked = []
        for item in evidence_items:
            score = self._similar_work_score(candidate, candidate_tokens, item)
            if score["score"] <= 0:
                continue
            ranked.append({**score, "item": item})
        ranked.sort(key=lambda value: value["score"], reverse=True)

        nearest = ranked[0]["item"] if ranked else None
        best_similarity = ranked[0]["score"] if ranked else 0.0
        title_similarity = ranked[0]["title_similarity"] if ranked else 0.0

        novelty_score = round(max(0.0, 1.0 - best_similarity), 3)
        if best_similarity >= 0.58 or title_similarity >= 0.72:
            status = "too_similar"
            collision_risk = "high"
            rationale = "候选与已有证据论文高度重合，可能只是已有工作的变体。"
        elif best_similarity >= 0.34 or title_similarity >= 0.46:
            status = "incremental"
            collision_risk = "medium"
            rationale = "候选与已有工作存在明显重叠，适合作为增量改进但需要强调区别。"
        else:
            status = "likely_novel"
            collision_risk = "low"
            rationale = "候选与当前证据集重叠较低，具备进一步做新颖性检查的价值。"

        return {
            "status": status,
            "score": novelty_score,
            "max_similarity": round(best_similarity, 3),
            "collision_risk": collision_risk,
            "nearest_evidence": {
                "paper_id": nearest.get("paper_id"),
                "title": nearest.get("title"),
                "source": nearest.get("source"),
            } if nearest else None,
            "similar_work": [
                self._similar_work_summary(value["item"], value)
                for value in ranked[:5]
            ],
            "source_coverage": source_coverage or {
                "query": "",
                "local_count": len(evidence_items),
                "external_count": 0,
                "total_count": len(evidence_items),
                "sources": {},
                "source_errors": {},
            },
            "rationale": rationale,
        }

    def _similar_work_score(
        self,
        candidate: dict[str, Any],
        candidate_tokens: set[str],
        item: dict[str, Any],
    ) -> dict[str, Any]:
        title_tokens = self._dedup_tokens(str(item.get("title") or ""))
        evidence_tokens = self._dedup_tokens(
            f"{item.get('title', '')} {item.get('abstract_excerpt', '')}"
        )
        candidate_title_tokens = self._dedup_tokens(str(candidate.get("title") or ""))
        lexical = self._jaccard(candidate_tokens, evidence_tokens)
        title_similarity = self._jaccard(candidate_title_tokens, title_tokens)
        source_bonus = self._similar_work_source_bonus(item)
        recency_bonus = self._similar_work_recency_bonus(item)
        score = min(1.0, lexical * 0.64 + title_similarity * 0.28 + source_bonus + recency_bonus)
        if title_similarity >= 0.92:
            score = max(score, 0.82)
        elif title_similarity >= 0.72:
            score = max(score, 0.62)
        return {
            "score": round(score, 3),
            "lexical_similarity": round(lexical, 3),
            "title_similarity": round(title_similarity, 3),
            "source_bonus": round(source_bonus, 3),
            "recency_bonus": round(recency_bonus, 3),
        }

    @staticmethod
    def _jaccard(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)

    @staticmethod
    def _similar_work_source_bonus(item: dict[str, Any]) -> float:
        category = str(item.get("category") or "")
        source = str(item.get("source") or "")
        if category == "seed":
            return 0.08
        if category == "background":
            return 0.05
        if source in {"semantic_scholar", "arxiv"}:
            return 0.035
        if category == "inspiration":
            return 0.025
        return 0.0

    @staticmethod
    def _similar_work_recency_bonus(item: dict[str, Any]) -> float:
        try:
            year = int(item.get("year") or 0)
        except (TypeError, ValueError):
            return 0.0
        if year >= 2025:
            return 0.025
        if year >= 2022:
            return 0.012
        return 0.0

    @staticmethod
    def _similar_work_summary(item: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
        relation = "nearest_collision_candidate" if score["score"] >= 0.58 else "similar_prior_work" if score["score"] >= 0.34 else "background_neighbor"
        reason = "标题和假设高度重合" if score["title_similarity"] >= 0.72 else "候选文本与论文摘要存在明显重叠" if score["lexical_similarity"] >= 0.34 else "作为相关工作需要人工复核"
        return {
            "paper_id": str(item.get("paper_id") or ""),
            "title": item.get("title") or "未命名论文",
            "year": item.get("year"),
            "source": item.get("source") or item.get("category"),
            "source_url": item.get("source_url"),
            "score": score["score"],
            "lexical_similarity": score["lexical_similarity"],
            "title_similarity": score["title_similarity"],
            "relation": relation,
            "reason": reason,
        }

    def adversarial_review_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {**candidate, "adversarial_review": self._adversarial_review(candidate)}
            for candidate in candidates
        ]

    def _adversarial_review(self, candidate: dict[str, Any]) -> dict[str, Any]:
        objections = []
        required_fixes = []
        experiment = candidate.get("minimum_experiment") or {}
        baselines = experiment.get("baselines") or []
        metrics = experiment.get("metrics") or []
        steps = experiment.get("steps") or []
        evidence_ids = candidate.get("evidence_ids") or []
        falsification = candidate.get("falsification_test") or ""

        if len(evidence_ids) < 2:
            objections.append("证据覆盖偏薄，至少需要两篇相关论文支撑研究空白。")
            required_fixes.append("补充核心论文或联网检索相似工作。")
        if not baselines or all("强" not in str(item) and "baseline" not in str(item).lower() for item in baselines):
            objections.append("baseline 设置可能偏弱，难以证明方法真实有效。")
            required_fixes.append("加入最新强基线和无改动消融。")
        if not metrics:
            objections.append("缺少明确指标，实验结果难以判定。")
            required_fixes.append("指定主指标、效率指标和稳定性指标。")
        if len(steps) < 3:
            objections.append("实验步骤不够具体，复现实操性不足。")
            required_fixes.append("补充复现、消融、误差分析和失败案例步骤。")
        if len(self._dedup_tokens(falsification)) < 6:
            objections.append("可证伪条件过弱，失败时难以判断假设是否被推翻。")
            required_fixes.append("写清楚否定假设的量化判据。")

        novelty_status = (candidate.get("novelty_check") or {}).get("status")
        if novelty_status == "too_similar":
            objections.append("新颖性检查显示与已有工作过于相似。")
            required_fixes.append("明确和最近相似论文的机制差异。")
        elif novelty_status == "incremental":
            objections.append("该想法可能是增量改进，需要更强对比论证。")

        penalty = min(2.5, round(len(objections) * 0.35, 2))
        verdict = "advance" if penalty <= 0.7 else "revise" if penalty <= 1.8 else "reject"
        return {
            "verdict": verdict,
            "penalty": penalty,
            "objections": objections,
            "required_fixes": list(dict.fromkeys(required_fixes)),
            "summary": "；".join(objections[:2]) if objections else "未发现明显硬伤，但仍需人工复核新颖性与实验设置。",
        }

    def apply_quality_adjustments(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        adjusted = []
        for candidate in candidates:
            review = candidate.get("review") or {}
            scores = dict(review.get("scores") or {})
            novelty = candidate.get("novelty_check") or {}
            adversarial = candidate.get("adversarial_review") or {}
            if "novelty" in scores:
                scores["novelty"] = round(max(1.0, min(10.0, scores["novelty"] * (0.72 + novelty.get("score", 0.5) * 0.28))), 1)
            if "evidence_grounding" in scores and len(candidate.get("evidence_ids") or []) < 2:
                scores["evidence_grounding"] = round(max(1.0, scores["evidence_grounding"] - 0.8), 1)
            adjusted_review = {**review, "scores": scores}
            base_score = self._weighted_score(scores)
            adjusted_score = round(max(1.0, base_score - float(adversarial.get("penalty", 0))), 2)
            adjusted.append({
                **candidate,
                "review": adjusted_review,
                "score": adjusted_score,
                "base_score": base_score,
            })
        return sorted(adjusted, key=lambda item: item["score"], reverse=True)

    def select_diverse_proposals(
        self,
        candidates: list[dict[str, Any]],
        num_ideas: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        suppressed: list[dict[str, Any]] = []
        remaining = [
            {**candidate, "diversity_facets": self._candidate_diversity_facets(candidate)}
            for candidate in candidates
        ]
        target = max(0, num_ideas)
        while remaining and len(selected) < target:
            ranked = []
            for candidate in remaining:
                penalty, overlaps = self._selection_diversity_penalty(candidate, selected)
                facet_bonus = self._selection_facet_bonus(candidate, selected)
                selection_score = round(float(candidate.get("score") or 0) - penalty + facet_bonus, 2)
                ranked.append((selection_score, penalty, facet_bonus, overlaps, candidate))
            ranked.sort(key=lambda item: (item[0], float(item[4].get("score") or 0)), reverse=True)
            selection_score, penalty, facet_bonus, overlaps, chosen = ranked[0]
            chosen = {
                **chosen,
                "selection_score": selection_score,
                "selection_rationale": self._selection_rationale(chosen, penalty, facet_bonus, overlaps),
                "suppressed_duplicates": [],
            }
            selected.append(chosen)
            next_remaining = []
            for _, item_penalty, _, item_overlaps, candidate in ranked[1:]:
                similarity = self._candidate_similarity(chosen, candidate)
                candidate_facets = set(candidate.get("diversity_facets") or [])
                chosen_facets = set(chosen.get("diversity_facets") or [])
                facet_overlap = len(candidate_facets & chosen_facets) / len(candidate_facets | chosen_facets) if candidate_facets and chosen_facets else 0.0
                if similarity >= 0.72 or facet_overlap >= 0.62:
                    suppressed_item = {
                        "title": candidate.get("title"),
                        "kept": chosen.get("title"),
                        "reason": "diversity_near_duplicate",
                        "similarity": round(similarity, 3),
                        "facet_overlap": round(facet_overlap, 3),
                    }
                    chosen["suppressed_duplicates"].append(suppressed_item)
                    suppressed.append(suppressed_item)
                else:
                    candidate["_last_diversity_penalty"] = item_penalty
                    candidate["_last_diversity_overlaps"] = item_overlaps
                    next_remaining.append(candidate)
            remaining = next_remaining
        summary = {
            "selected": [
                {
                    "title": candidate.get("title"),
                    "selection_score": candidate.get("selection_score"),
                    "diversity_facets": candidate.get("diversity_facets", []),
                    "rationale": candidate.get("selection_rationale"),
                }
                for candidate in selected
            ],
            "suppressed": suppressed[:20],
            "strategy": "score_minus_overlap_plus_new_facets",
        }
        return selected, summary

    def _candidate_diversity_facets(self, candidate: dict[str, Any]) -> list[str]:
        facets: list[str] = []
        path = str(candidate.get("path") or "").strip()
        if path:
            facets.append(f"path:{path}")
        operator = str((candidate.get("tree") or {}).get("operator") or "").strip()
        if operator:
            facets.append(f"operator:{operator}")
        experiment = candidate.get("minimum_experiment") or {}
        dataset = str(experiment.get("dataset") or "").strip()
        if dataset:
            facets.append(f"dataset:{self._facet_key(dataset)[:36]}")
        for metric in (experiment.get("metrics") or [])[:2]:
            facets.append(f"metric:{self._facet_key(str(metric))[:28]}")
        for risk in (candidate.get("risks") or [])[:2]:
            facets.append(f"risk:{self._facet_key(str(risk))[:28]}")
        evidence_ids = [str(item) for item in (candidate.get("evidence_ids") or []) if item]
        if evidence_ids:
            facets.append(f"evidence:{','.join(evidence_ids[:2])}")
        novelty_status = str((candidate.get("novelty_check") or {}).get("status") or "").strip()
        if novelty_status:
            facets.append(f"novelty:{novelty_status}")
        return list(dict.fromkeys(facets))[:8]

    @staticmethod
    def _facet_key(text: str) -> str:
        return "-".join(re.findall(r"[a-z0-9\u4e00-\u9fff]+", text.lower())) or "unknown"

    def _selection_diversity_penalty(
        self,
        candidate: dict[str, Any],
        selected: list[dict[str, Any]],
    ) -> tuple[float, list[str]]:
        if not selected:
            return 0.0, []
        candidate_facets = set(candidate.get("diversity_facets") or [])
        overlaps: list[str] = []
        max_similarity = 0.0
        max_facet_overlap = 0.0
        for item in selected:
            similarity = self._candidate_similarity(candidate, item)
            max_similarity = max(max_similarity, similarity)
            selected_facets = set(item.get("diversity_facets") or [])
            if candidate_facets and selected_facets:
                facet_overlap = len(candidate_facets & selected_facets) / len(candidate_facets | selected_facets)
                max_facet_overlap = max(max_facet_overlap, facet_overlap)
                overlaps.extend(sorted(candidate_facets & selected_facets))
        penalty = min(2.4, max_similarity * 1.5 + max_facet_overlap * 0.9)
        return round(penalty, 2), list(dict.fromkeys(overlaps))[:6]

    @staticmethod
    def _selection_facet_bonus(candidate: dict[str, Any], selected: list[dict[str, Any]]) -> float:
        if not selected:
            return 0.0
        used = {
            facet
            for item in selected
            for facet in (item.get("diversity_facets") or [])
        }
        new_facets = [facet for facet in (candidate.get("diversity_facets") or []) if facet not in used]
        return round(min(0.5, len(new_facets) * 0.08), 2)

    @staticmethod
    def _selection_rationale(
        candidate: dict[str, Any],
        penalty: float,
        facet_bonus: float,
        overlaps: list[str],
    ) -> str:
        parts = [f"综合评分 {candidate.get('score', 0)}"]
        if facet_bonus > 0:
            parts.append(f"贡献新的多样性维度 +{facet_bonus}")
        if penalty > 0:
            parts.append(f"与已选方向重叠扣 {penalty}")
        if overlaps:
            parts.append(f"重叠维度：{', '.join(overlaps[:3])}")
        tree = candidate.get("tree") or {}
        if tree.get("operator"):
            parts.append(f"来源：{tree.get('operator')}")
        return "；".join(parts)

    @staticmethod
    def _summarize_novelty(candidates: list[dict[str, Any]]) -> dict[str, Any]:
        summary = {"likely_novel": 0, "incremental": 0, "too_similar": 0}
        for candidate in candidates:
            status = (candidate.get("novelty_check") or {}).get("status")
            if status in summary:
                summary[status] += 1
        return summary

    @staticmethod
    def _summarize_adversarial(candidates: list[dict[str, Any]]) -> dict[str, Any]:
        verdicts = {"advance": 0, "revise": 0, "reject": 0}
        total_objections = 0
        for candidate in candidates:
            review = candidate.get("adversarial_review") or {}
            verdict = review.get("verdict")
            if verdict in verdicts:
                verdicts[verdict] += 1
            total_objections += len(review.get("objections") or [])
        return {"verdicts": verdicts, "total_objections": total_objections}

    async def review_candidates(
        self,
        brief: dict[str, Any],
        evidence_map: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        prompt = f"""你是严格的科研 Proposal 评审。逐条评审候选假设，输出严格 JSON：
{{"reviews":[{{"title":"候选标题", "scores":{{"novelty":1-10,"evidence_grounding":1-10,
"feasibility":1-10,"testability":1-10,"impact":1-10,"clarity":1-10}},
"rationale":"评审理由", "uncertainty":"主要不确定性", "recommendation":"advance|revise|reject"}}]}}
不要用虚假的精确性掩盖证据不足。

研究简报：{json.dumps(brief, ensure_ascii=False)}
证据：{self._format_evidence(evidence_map, limit=10)}
候选：{json.dumps(candidates, ensure_ascii=False)}
"""
        data = await self._chat_json(prompt)
        reviews = data.get("reviews") if isinstance(data, dict) else None
        review_by_title = {
            str(item.get("title")): item for item in reviews or [] if isinstance(item, dict) and item.get("title")
        }
        reviewed = []
        for index, candidate in enumerate(candidates):
            review = self._normalize_review(review_by_title.get(candidate["title"]), candidate, index)
            reviewed.append({**candidate, "review": review, "score": self._weighted_score(review["scores"])})
        return sorted(reviewed, key=lambda item: item["score"], reverse=True)

    async def persist_top_proposals(
        self,
        run: ResearchIdeaRun,
        reviewed: list[dict[str, Any]],
        evidence_map: dict[str, Any],
        num_ideas: int,
    ) -> list[ResearchIdea]:
        evidence_lookup = {
            item["paper_id"]: item
            for category in ("seed", "background", "inspiration")
            for item in evidence_map.get(category, [])
        }
        ideas = []
        for candidate in reviewed[:num_ideas]:
            evidence_ids = candidate.get("evidence_ids", [])
            evidence = [evidence_lookup[paper_id] for paper_id in evidence_ids if paper_id in evidence_lookup]
            collection_sources = self._collection_sources_for_evidence(evidence, evidence_map)
            review = candidate["review"]
            idea = ResearchIdea(
                project_id=run.project_id,
                generation_run_id=run.id,
                title=candidate["title"],
                description=f"{candidate['gap']}\n\n{candidate['hypothesis']}",
                approach=candidate["approach"],
                novelty=review["rationale"],
                feasibility_score=review["scores"]["feasibility"],
                novelty_score=review["scores"]["novelty"],
                referenced_papers={"paper_ids": evidence_ids, "collection_sources": collection_sources},
                hypothesis=candidate["hypothesis"],
                evidence_json={"items": evidence, "scope": evidence_map.get("scope"), "collection_sources": collection_sources},
                review_json={
                    **review,
                    "aggregate_score": candidate["score"],
                    "base_score": candidate.get("base_score", candidate["score"]),
                    "novelty_check": candidate.get("novelty_check"),
                    "adversarial_review": candidate.get("adversarial_review"),
                    "search_tree": candidate.get("tree"),
                    "selection_rationale": candidate.get("selection_rationale"),
                    "selection_score": candidate.get("selection_score"),
                    "diversity_facets": candidate.get("diversity_facets", []),
                    "suppressed_duplicates": candidate.get("suppressed_duplicates", []),
                    "gap_selection": candidate.get("gap_selection"),
                },
                experiment_plan=candidate["minimum_experiment"],
                status="draft",
            )
            self.session.add(idea)
            ideas.append(idea)
        await self.session.commit()
        for idea in ideas:
            await self.session.refresh(idea)
        return ideas

    def validate_idea(self, idea: ResearchIdea, project: ResearchProject | None = None) -> dict[str, Any]:
        """Summarize whether an idea is ready to move into experiments/writing.

        This intentionally avoids another model call. The validation loop is a
        deterministic review of artifacts already attached to the idea.
        """
        evidence_json = idea.evidence_json or {}
        evidence_items = [item for item in evidence_json.get("items", []) or [] if isinstance(item, dict)]
        review_json = idea.review_json or {}
        plan = idea.experiment_plan or {}
        referenced_ids = self._normalize_referenced_paper_ids(idea.referenced_papers)
        novelty = review_json.get("novelty_check") or {}
        adversarial = review_json.get("adversarial_review") or {}

        related_work = self._validation_related_work(evidence_items, novelty)
        collision_risk = self._validation_collision_risk(novelty, related_work)
        checklist = self._validation_experiment_checklist(plan)
        coverage = self._validation_coverage(evidence_items, referenced_ids, checklist)
        feasibility_risks = self._validation_feasibility_risks(
            idea,
            adversarial,
            collision_risk,
            checklist,
            coverage,
        )
        writing_readiness = self._validation_writing_readiness(
            collision_risk,
            checklist,
            coverage,
            feasibility_risks,
        )

        return {
            "idea_id": str(idea.id),
            "project_id": str(idea.project_id),
            "project_name": getattr(project, "name", None),
            "summary": self._validation_summary(writing_readiness, collision_risk, coverage),
            "collision_risk": collision_risk,
            "related_work": related_work,
            "feasibility_risks": feasibility_risks,
            "experiment_checklist": checklist,
            "writing_readiness": writing_readiness,
            "coverage": coverage,
            "next_actions": self._validation_next_actions(writing_readiness, feasibility_risks, checklist),
        }

    @staticmethod
    def _normalize_referenced_paper_ids(referenced_papers: Any) -> list[str]:
        if not isinstance(referenced_papers, dict):
            return []
        paper_ids = referenced_papers.get("paper_ids") or []
        return [str(item) for item in paper_ids if item]

    @staticmethod
    def _validation_related_work(
        evidence_items: list[dict[str, Any]],
        novelty: dict[str, Any],
    ) -> list[dict[str, Any]]:
        nearest = novelty.get("nearest_evidence") if isinstance(novelty, dict) else None
        similar_work = novelty.get("similar_work") if isinstance(novelty, dict) else None
        related: list[dict[str, Any]] = []
        seen: set[str] = set()

        if isinstance(similar_work, list):
            for item in similar_work:
                if not isinstance(item, dict):
                    continue
                paper_id = str(item.get("paper_id") or item.get("id") or item.get("title") or "")
                if not paper_id or paper_id in seen:
                    continue
                related.append({
                    "paper_id": paper_id,
                    "title": item.get("title") or "相似工作",
                    "year": item.get("year"),
                    "source": item.get("source"),
                    "score": item.get("score"),
                    "relation": item.get("relation") or "similar_prior_work",
                    "reason": item.get("reason") or "Novelty Check 检出的相似工作。",
                })
                seen.add(paper_id)
                if len(related) >= 5:
                    return related

        if isinstance(nearest, dict) and nearest.get("paper_id"):
            paper_id = str(nearest.get("paper_id"))
            if paper_id not in seen:
                related.append({
                    "paper_id": paper_id,
                    "title": nearest.get("title") or "最近相似证据",
                    "source": nearest.get("source"),
                    "relation": "nearest_collision_candidate",
                    "reason": "Novelty Check 中最相似的已有工作。",
                })
                seen.add(paper_id)

        ranked = sorted(
            evidence_items,
            key=lambda item: float(item.get("score") or 0),
            reverse=True,
        )
        for item in ranked:
            paper_id = str(item.get("paper_id") or item.get("id") or "")
            if not paper_id or paper_id in seen:
                continue
            related.append({
                "paper_id": paper_id,
                "title": item.get("title") or "未命名论文",
                "year": item.get("year"),
                "source": item.get("source"),
                "category": item.get("category"),
                "relation": "supporting_or_background_evidence",
                "reason": item.get("relevance") or item.get("abstract_excerpt") or "Idea 生成时引用的证据论文。",
            })
            seen.add(paper_id)
            if len(related) >= 5:
                break
        return related

    @staticmethod
    def _validation_collision_risk(
        novelty: dict[str, Any],
        related_work: list[dict[str, Any]],
    ) -> dict[str, Any]:
        status = str(novelty.get("status") or "unknown")
        score = float(novelty.get("score") or 0)
        max_similarity = float(novelty.get("max_similarity") or 0)
        if status == "too_similar":
            level = "high"
            label = "高撞车风险"
        elif status == "incremental":
            level = "medium"
            label = "增量风险"
        elif status == "likely_novel":
            level = "low"
            label = "当前证据下较新颖"
        else:
            level = "unknown"
            label = "缺少 novelty 检查"
        return {
            "level": level,
            "label": label,
            "status": status,
            "score": round(score, 3),
            "max_similarity": round(max_similarity, 3),
            "reason": novelty.get("rationale") or "尚未形成可解释的新颖性判断。",
            "nearest_related_work": related_work[0] if related_work else None,
        }

    @staticmethod
    def _validation_experiment_checklist(plan: dict[str, Any]) -> dict[str, Any]:
        def normalize_list(value: Any) -> list[str]:
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            if isinstance(value, str) and value.strip():
                return [value.strip()]
            return []

        dataset = str(plan.get("dataset") or "").strip()
        baselines = normalize_list(plan.get("baselines"))
        metrics = normalize_list(plan.get("metrics"))
        steps = normalize_list(plan.get("steps"))
        ablations = normalize_list(plan.get("ablations") or plan.get("ablation_plan"))
        if not ablations and baselines:
            ablations = ["核心模块消融", "无改动/无增强版本对照"]
        reproducibility = normalize_list(plan.get("reproducibility"))
        if not reproducibility and steps:
            reproducibility = ["记录数据切分、随机种子、关键超参和失败案例"]

        def group(label: str, items: list[str], minimum: int, missing_tip: str) -> dict[str, Any]:
            return {
                "label": label,
                "items": items,
                "present": len(items) >= minimum,
                "missing_tip": "" if len(items) >= minimum else missing_tip,
            }

        return {
            "dataset": {
                "label": "数据集",
                "items": [dataset] if dataset else [],
                "present": bool(dataset),
                "missing_tip": "" if dataset else "补充至少一个主数据集或任务基准。",
            },
            "baselines": group("强基线", baselines, 1, "补充最新强基线和简单基线。"),
            "metrics": group("评价指标", metrics, 1, "补充主指标、效率指标和稳定性指标。"),
            "steps": group("实验步骤", steps, 3, "补充复现、改进、消融和误差分析步骤。"),
            "ablations": group("消融设计", ablations, 1, "补充核心模块消融，避免只比较最终结果。"),
            "reproducibility": group("可复现记录", reproducibility, 1, "补充随机种子、超参、数据切分和运行成本记录。"),
        }

    @staticmethod
    def _validation_coverage(
        evidence_items: list[dict[str, Any]],
        referenced_ids: list[str],
        checklist: dict[str, Any],
    ) -> dict[str, Any]:
        complete_groups = [key for key, value in checklist.items() if value.get("present")]
        missing_groups = [key for key, value in checklist.items() if not value.get("present")]
        evidence_count = len(evidence_items)
        referenced_count = max(len(referenced_ids), len({item.get("paper_id") for item in evidence_items if item.get("paper_id")}))
        return {
            "evidence_count": evidence_count,
            "referenced_paper_count": referenced_count,
            "has_enough_evidence": evidence_count >= 2 or referenced_count >= 2,
            "experiment_complete_groups": complete_groups,
            "experiment_missing_groups": missing_groups,
            "experiment_completeness": round(len(complete_groups) / max(len(checklist), 1), 2),
        }

    @staticmethod
    def _validation_feasibility_risks(
        idea: ResearchIdea,
        adversarial: dict[str, Any],
        collision_risk: dict[str, Any],
        checklist: dict[str, Any],
        coverage: dict[str, Any],
    ) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        for item in adversarial.get("objections") or []:
            risks.append({"level": "medium", "type": "adversarial_review", "message": str(item)})
        if collision_risk.get("level") == "high":
            risks.append({"level": "high", "type": "collision", "message": "与最近相似工作重叠较高，需要先明确机制差异。"})
        elif collision_risk.get("level") == "medium":
            risks.append({"level": "medium", "type": "collision", "message": "该 idea 更像增量改进，需要更强 baseline 和差异论证。"})
        if not coverage.get("has_enough_evidence"):
            risks.append({"level": "high", "type": "evidence_gap", "message": "证据论文少于 2 篇，暂不适合直接写作。"})
        for key, value in checklist.items():
            if not value.get("present"):
                risks.append({
                    "level": "medium",
                    "type": f"missing_{key}",
                    "message": value.get("missing_tip") or f"缺少{value.get('label', key)}。",
                })
        if idea.feasibility_score is not None and float(idea.feasibility_score) < 6:
            risks.append({"level": "medium", "type": "low_feasibility_score", "message": "可行性评分偏低，需要先降低实验复杂度。"})
        return risks[:10]

    @staticmethod
    def _validation_writing_readiness(
        collision_risk: dict[str, Any],
        checklist: dict[str, Any],
        coverage: dict[str, Any],
        risks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        blocking_reasons: list[str] = []
        if collision_risk.get("level") == "high":
            blocking_reasons.append("撞车风险高")
        if not coverage.get("has_enough_evidence"):
            blocking_reasons.append("证据覆盖不足")
        missing_required = [
            checklist[key].get("label", key)
            for key in ("dataset", "baselines", "metrics", "steps")
            if not checklist.get(key, {}).get("present")
        ]
        if missing_required:
            blocking_reasons.append(f"实验计划缺少：{'、'.join(missing_required)}")

        high_risks = [risk for risk in risks if risk.get("level") == "high"]
        if blocking_reasons:
            status = "blocked"
            label = "暂不适合进入写作"
        elif high_risks or coverage.get("experiment_completeness", 0) < 0.8:
            status = "needs_validation"
            label = "需要补实验验证"
        else:
            status = "ready"
            label = "可以进入写作草稿"
        return {
            "status": status,
            "label": label,
            "reasons": blocking_reasons or ["证据和最小实验计划已覆盖主要推进条件。"],
        }

    @staticmethod
    def _validation_summary(
        writing_readiness: dict[str, Any],
        collision_risk: dict[str, Any],
        coverage: dict[str, Any],
    ) -> str:
        return (
            f"{writing_readiness.get('label')}；"
            f"{collision_risk.get('label')}；"
            f"证据 {coverage.get('evidence_count', 0)} 篇，"
            f"实验完整度 {int(float(coverage.get('experiment_completeness', 0)) * 100)}%。"
        )

    @staticmethod
    def _validation_next_actions(
        writing_readiness: dict[str, Any],
        risks: list[dict[str, Any]],
        checklist: dict[str, Any],
    ) -> list[str]:
        if writing_readiness.get("status") == "ready":
            return ["创建写作草稿", "记录第一轮实验结果", "准备 Related Work 对比表"]
        actions = []
        for risk in risks:
            message = risk.get("message")
            if message:
                actions.append(str(message))
        for value in checklist.values():
            tip = value.get("missing_tip")
            if tip:
                actions.append(str(tip))
        return list(dict.fromkeys(actions))[:5]

    def build_experiment_execution_pack(
        self,
        idea: ResearchIdea,
        project: Optional[ResearchProject] = None,
        experiments: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Summarize how an Idea should move from Proposal to experiment feedback."""
        validation = self.validate_idea(idea, project)
        plan = idea.experiment_plan or {}
        linked_experiments = [
            item for item in experiments or []
            if str(item.get("idea_id") or "") == str(idea.id)
        ]
        latest_feedback = linked_experiments[-1] if linked_experiments else None
        has_results = bool((latest_feedback or {}).get("results"))
        tasks = [
            self._execution_task(
                "dataset",
                "选择数据集",
                plan.get("dataset"),
                "先确定公开基准、验证集切分或用户自己的评测集合。",
            ),
            self._execution_task(
                "baselines",
                "复现强基线",
                plan.get("baselines"),
                "至少保留一个可复现强基线，避免 Proposal 只和弱 baseline 比。",
            ),
            self._execution_task(
                "metrics",
                "设定成功指标",
                plan.get("metrics"),
                "明确主指标、效率指标和失败判定阈值。",
            ),
            self._execution_task(
                "steps",
                "拆解实验步骤",
                plan.get("steps"),
                "把实验拆成复现、最小改动、消融和误差分析。",
            ),
        ]
        setup_ready = all(item["status"] == "ready" for item in tasks)
        experiment_completeness = float(validation["coverage"].get("experiment_completeness") or 0)
        evidence_ready = bool(validation["coverage"].get("has_enough_evidence"))
        readiness_score = round(
            (experiment_completeness * 0.45)
            + (0.25 if evidence_ready else 0)
            + (0.20 if setup_ready else 0)
            + (0.10 if has_results else 0),
            2,
        )
        if has_results:
            status = "needs_iteration"
            label = "已有反馈，适合演化"
        elif setup_ready and evidence_ready:
            status = "ready"
            label = "可以启动最小实验"
        else:
            status = "needs_setup"
            label = "需要补齐实验设置"

        review = idea.review_json or {}
        adversarial = review.get("adversarial_review") if isinstance(review.get("adversarial_review"), dict) else {}
        risks = [
            {"level": risk.get("level", "medium"), "message": risk.get("message", "")}
            for risk in validation.get("feasibility_risks", [])
            if risk.get("message")
        ]
        for objection in adversarial.get("objections", []) or []:
            risks.append({"level": "medium", "message": str(objection)})

        metrics = [
            {
                "name": str(metric),
                "target": "超过强基线，或明确解释失败原因与边界条件",
            }
            for metric in plan.get("metrics", []) or []
        ]
        return {
            "idea_id": str(idea.id),
            "project_id": str(idea.project_id),
            "readiness": {"status": status, "label": label, "score": readiness_score},
            "summary": self._execution_summary(status, setup_ready, evidence_ready, len(linked_experiments)),
            "minimum_tasks": tasks,
            "success_metrics": metrics or [{"name": "主任务指标", "target": "先补充可量化成功指标"}],
            "feedback": {"count": len(linked_experiments), "has_results": has_results, "latest": latest_feedback},
            "risks": risks[:6],
            "next_actions": self._execution_next_actions(status, tasks, has_results, validation),
            "validation": {
                "writing_readiness": validation.get("writing_readiness"),
                "coverage": validation.get("coverage"),
                "collision_risk": validation.get("collision_risk"),
            },
        }

    async def build_proposal_review_package(
        self,
        idea: ResearchIdea,
        project: Optional[ResearchProject] = None,
    ) -> dict[str, Any]:
        """Create and persist reviewer-style guidance for proposal revision."""
        validation = self.validate_idea(idea, project)
        execution = self.build_experiment_execution_pack(idea, project)
        review = idea.review_json or {}
        prompt = f"""你是严格但建设性的论文审稿人。请基于 Proposal、证据、验证和实验推进信息，输出结构化审稿包。
只输出合法 JSON，不要使用 Markdown 代码块。JSON 格式：
{{
  "summary": "一句话审稿结论",
  "contributions": ["最多 4 条潜在贡献"],
  "weakest_assumptions": ["最多 4 条最弱假设"],
  "reviewer_objections": ["最多 5 条拒稿/质疑点"],
  "required_experiments": ["最多 5 个必要实验"],
  "revision_plan": ["最多 5 个修订动作"],
  "writing_readiness": "ready|needs_revision|blocked",
  "next_revision_focus": "下一版 Proposal 应聚焦的一句话"
}}

Proposal：{json.dumps({
            "title": idea.title,
            "description": idea.description,
            "hypothesis": idea.hypothesis,
            "approach": idea.approach,
            "novelty": idea.novelty,
            "review": review,
            "experiment_plan": idea.experiment_plan,
            "evidence": idea.evidence_json,
            "evolution": idea.evolution_json,
        }, ensure_ascii=False)[:12000]}
验证：{json.dumps(validation, ensure_ascii=False)[:8000]}
实验推进：{json.dumps(execution, ensure_ascii=False)[:6000]}
"""
        parsed = await self._chat_json(prompt)
        package = self.normalize_proposal_review_package(parsed, idea, validation, execution)
        current_review = dict(idea.review_json or {})
        current_review["proposal_review"] = package
        idea.review_json = current_review
        await self.session.commit()
        await self.session.refresh(idea)
        return package

    def normalize_proposal_review_package(
        self,
        value: Any,
        idea: ResearchIdea,
        validation: Optional[dict[str, Any]] = None,
        execution: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        data = value if isinstance(value, dict) else {}
        validation = validation or self.validate_idea(idea)
        execution = execution or self.build_experiment_execution_pack(idea)
        readiness = (validation.get("writing_readiness") or {}).get("status")
        objections = self._string_list(data.get("reviewer_objections"), limit=5)
        if not objections:
            objections = self._string_list((idea.review_json or {}).get("adversarial_review", {}).get("objections"), limit=5)
        required_experiments = self._string_list(data.get("required_experiments"), limit=5)
        if not required_experiments:
            required_experiments = self._string_list(execution.get("next_actions"), limit=5)
        weakest = self._string_list(data.get("weakest_assumptions"), limit=4)
        if not weakest:
            weakest = self._string_list(validation.get("feasibility_risks"), limit=4)
        revision_plan = self._string_list(data.get("revision_plan"), limit=5)
        if not revision_plan:
            revision_plan = list(dict.fromkeys([*weakest, *required_experiments]))[:5]
        writing_readiness = str(data.get("writing_readiness") or ("ready" if readiness == "ready" and not objections else "needs_revision")).strip()
        if writing_readiness not in {"ready", "needs_revision", "blocked"}:
            writing_readiness = "needs_revision"
        next_focus = str(data.get("next_revision_focus") or "").strip()
        if not next_focus:
            next_focus = revision_plan[0] if revision_plan else "补强证据、实验设置和可证伪假设"
        return {
            "summary": str(data.get("summary") or f"{idea.title} 需要围绕证据、实验和 novelty 做一次审稿式修订。")[:600],
            "contributions": self._string_list(data.get("contributions"), limit=4) or [str(idea.novelty or idea.description or "潜在贡献仍需进一步明确。")[:240]],
            "weakest_assumptions": weakest[:4],
            "reviewer_objections": objections[:5],
            "required_experiments": required_experiments[:5],
            "revision_plan": revision_plan[:5],
            "writing_readiness": writing_readiness,
            "next_revision_focus": next_focus[:600],
        }

    async def revise_idea_from_review(
        self,
        idea: ResearchIdea,
        project: ResearchProject,
        *,
        focus: str = "",
    ) -> ResearchIdea:
        review_package = ((idea.review_json or {}).get("proposal_review") or {})
        if not isinstance(review_package, dict) or not review_package:
            review_package = await self.build_proposal_review_package(idea, project)
        focus_text = str(focus or "").strip() or str(review_package.get("next_revision_focus") or "").strip()
        if review_package.get("revision_plan"):
            focus_text = f"{focus_text}\n审稿修订计划：{'；'.join(review_package.get('revision_plan') or [])}".strip()
        child = await self.evolve_idea(idea, project, focus=focus_text)
        evolution = dict(child.evolution_json or {})
        evolution["source"] = "proposal_review"
        evolution["review_focus"] = review_package.get("next_revision_focus")
        evolution["review_objections"] = review_package.get("reviewer_objections") or []
        evolution["required_experiments"] = review_package.get("required_experiments") or []
        child.evolution_json = evolution
        await self.session.commit()
        await self.session.refresh(child)
        return child

    def compare_idea_versions(
        self,
        idea: ResearchIdea,
        parent: Optional[ResearchIdea] = None,
    ) -> dict[str, Any]:
        if not parent:
            return {
                "idea_id": str(idea.id),
                "has_parent": False,
                "current": self._idea_version_snapshot(idea),
                "parent": None,
                "changes": [],
                "revision_rationale": (idea.evolution_json or {}).get("rationale"),
            }
        fields = [
            ("title", "标题", parent.title, idea.title),
            ("hypothesis", "可证伪假设", parent.hypothesis, idea.hypothesis),
            ("approach", "技术路线", parent.approach, idea.approach),
            ("description", "描述", parent.description, idea.description),
        ]
        changes = [
            {"field": key, "label": label, "before": before or "", "after": after or ""}
            for key, label, before, after in fields
            if (before or "") != (after or "")
        ]
        parent_plan = parent.experiment_plan or {}
        child_plan = idea.experiment_plan or {}
        if parent_plan != child_plan:
            changes.append({"field": "experiment_plan", "label": "最小实验", "before": parent_plan, "after": child_plan})
        parent_evidence = len((parent.evidence_json or {}).get("items") or [])
        child_evidence = len((idea.evidence_json or {}).get("items") or [])
        if parent_evidence != child_evidence:
            changes.append({"field": "evidence_count", "label": "证据数量", "before": parent_evidence, "after": child_evidence})
        return {
            "idea_id": str(idea.id),
            "parent_idea_id": str(parent.id),
            "has_parent": True,
            "current": self._idea_version_snapshot(idea),
            "parent": self._idea_version_snapshot(parent),
            "changes": changes,
            "revision_rationale": (idea.evolution_json or {}).get("rationale"),
            "review_source": {
                "source": (idea.evolution_json or {}).get("source"),
                "review_focus": (idea.evolution_json or {}).get("review_focus"),
                "review_objections": (idea.evolution_json or {}).get("review_objections") or [],
                "required_experiments": (idea.evolution_json or {}).get("required_experiments") or [],
            },
        }

    @staticmethod
    def _idea_version_snapshot(idea: ResearchIdea) -> dict[str, Any]:
        review = idea.review_json or {}
        return {
            "id": str(idea.id),
            "title": idea.title,
            "status": idea.status,
            "hypothesis": idea.hypothesis,
            "approach": idea.approach,
            "experiment_plan": idea.experiment_plan or {},
            "evidence_count": len((idea.evidence_json or {}).get("items") or []),
            "review_score": review.get("aggregate_score") or ((idea.feasibility_score or 0) + (idea.novelty_score or 0)) / 2,
            "proposal_review": review.get("proposal_review"),
            "evolution": idea.evolution_json or {},
        }

    @staticmethod
    def _execution_task(key: str, label: str, value: Any, missing_tip: str) -> dict[str, Any]:
        if isinstance(value, list):
            detail = "、".join(str(item) for item in value if str(item).strip())
        else:
            detail = str(value or "").strip()
        return {
            "key": key,
            "label": label,
            "status": "ready" if detail else "missing",
            "detail": detail or missing_tip,
        }

    @staticmethod
    def _execution_summary(status: str, setup_ready: bool, evidence_ready: bool, feedback_count: int) -> str:
        if status == "needs_iteration":
            return f"已记录 {feedback_count} 条实验反馈，下一步应基于失败案例或结构化结果演化 Proposal。"
        if setup_ready and evidence_ready:
            return "最小实验设置和证据覆盖基本齐备，可以先跑低成本第一轮实验。"
        missing = []
        if not setup_ready:
            missing.append("实验设置")
        if not evidence_ready:
            missing.append("证据覆盖")
        return f"当前仍需补齐{'、'.join(missing)}，否则实验反馈难以支撑后续写作。"

    @staticmethod
    def _execution_next_actions(
        status: str,
        tasks: list[dict[str, Any]],
        has_results: bool,
        validation: dict[str, Any],
    ) -> list[str]:
        if has_results:
            return ["根据实验反馈演化 Proposal", "把失败案例写入风险与局限", "生成或更新写作草稿"]
        missing = [task for task in tasks if task["status"] != "ready"]
        if missing:
            return [f"补齐：{task['label']}" for task in missing][:4]
        actions = validation.get("next_actions") or []
        if status == "ready":
            return ["记录第一轮实验反馈", "生成实验代码", *actions[:2]]
        return actions[:4] or ["先完成验证闭环，再启动实验"]

    @staticmethod
    def _collection_sources_for_evidence(
        evidence: list[dict[str, Any]],
        evidence_map: dict[str, Any],
    ) -> list[dict[str, Any]]:
        by_id = {
            str(item.get("id")): {"id": str(item.get("id")), "name": item.get("name"), "paper_ids": set()}
            for item in evidence_map.get("collection_sources", []) or []
            if item.get("id")
        }
        for item in evidence:
            for collection_id, collection_name in zip(item.get("collection_ids", []) or [], item.get("collection_names", []) or []):
                entry = by_id.setdefault(str(collection_id), {"id": str(collection_id), "name": collection_name, "paper_ids": set()})
                entry["paper_ids"].add(item.get("paper_id"))
        return [
            {"id": entry["id"], "name": entry["name"], "evidence_count": len(entry["paper_ids"])}
            for entry in by_id.values()
            if entry["paper_ids"]
        ]

    async def evolve_idea(
        self,
        parent: ResearchIdea,
        project: ResearchProject,
        focus: str = "",
        experiment_feedback: Optional[dict[str, Any]] = None,
    ) -> ResearchIdea:
        """Create a traceable child proposal without mutating the parent."""
        evidence_json = parent.evidence_json or {"items": [], "scope": "unknown"}
        evidence_map = {
            "scope": evidence_json.get("scope"),
            "seed": evidence_json.get("items", []),
            "background": [],
            "inspiration": [],
        }
        prompt = f"""你是科研 Proposal 演化助手。请根据父 Proposal 的证据、评审不确定性和用户关注点，
创建一个更具体、更可验证的新版本。保留有价值的部分，明确说明改进原因。
输出严格 JSON：
{{"title":"...", "gap":"...", "hypothesis":"可证伪假设", "approach":"...",
"evidence_ids":["..."], "risks":["..."], "falsification_test":"...",
"minimum_experiment":{{"dataset":"...","baselines":["..."],"metrics":["..."],"steps":["..."]}},
"evolution_rationale":"相对父版本的核心改进"}}

父 Proposal：{json.dumps({
    "title": parent.title,
    "description": parent.description,
    "hypothesis": parent.hypothesis,
    "approach": parent.approach,
    "review": parent.review_json,
    "experiment_plan": parent.experiment_plan,
}, ensure_ascii=False)}
用户关注点：{focus or "优先改善评审中暴露出的主要不确定性"}
实验反馈：{json.dumps(experiment_feedback or {}, ensure_ascii=False)}
证据：{json.dumps(evidence_json, ensure_ascii=False)}
"""
        data = await self._chat_json(prompt)
        candidate = self._normalize_candidate(
            data,
            self._project_brief(project),
            evidence_map,
            0,
        )
        reviewed = await self.review_candidates(self._project_brief(project), evidence_map, [candidate])
        selected = reviewed[0]
        review = selected["review"]
        child = ResearchIdea(
            project_id=parent.project_id,
            generation_run_id=parent.generation_run_id,
            parent_idea_id=parent.id,
            title=selected["title"],
            description=f"{selected['gap']}\n\n{selected['hypothesis']}",
            approach=selected["approach"],
            novelty=review["rationale"],
            feasibility_score=review["scores"]["feasibility"],
            novelty_score=review["scores"]["novelty"],
            referenced_papers=parent.referenced_papers,
            hypothesis=selected["hypothesis"],
            evidence_json=evidence_json,
            review_json={**review, "aggregate_score": selected["score"]},
            experiment_plan=selected["minimum_experiment"],
            evolution_json={
                "parent_idea_id": str(parent.id),
                "round": int((getattr(parent, "evolution_json", None) or {}).get("round", 1)) + 1,
                "focus": focus,
                "experiment_feedback": experiment_feedback,
                "rationale": str(data.get("evolution_rationale") or "根据父版本评审反馈细化假设与最小实验方案。"),
            },
            status="draft",
        )
        self.session.add(child)
        await self.session.commit()
        await self.session.refresh(child)
        return child

    async def _chat_json(self, prompt: str) -> dict[str, Any]:
        try:
            response = await llm_service.chat(
                messages=[
                    {"role": "system", "content": "只输出合法 JSON，不要使用 Markdown 代码块。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.45,
            )
            return self._parse_json(response)
        except Exception as exc:
            logger.warning("Workbench structured LLM call failed, using fallback: %s", exc)
            return {}

    @staticmethod
    def _parse_json(response: str) -> dict[str, Any]:
        if not response:
            return {}
        text = response.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                return {}
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}

    @staticmethod
    def _format_evidence(evidence_map: dict[str, Any], limit: int) -> str:
        items = [
            item
            for category in ("seed", "background", "inspiration")
            for item in evidence_map.get(category, [])
        ][:limit]
        return "\n".join(
            f"- [{item['paper_id']}] ({item.get('category', item.get('source', 'evidence'))}) {item['title']}: {item.get('abstract_excerpt', '')}"
            for item in items
        ) or "- 当前论文库没有匹配证据，需要将结论标注为低置信度。"

    @staticmethod
    def _normalize_gap(
        gap: Any, brief: dict[str, Any], evidence_map: dict[str, Any]
    ) -> dict[str, Any]:
        data = gap if isinstance(gap, dict) else {}
        available = ResearchIdeaWorkbenchService._available_evidence_ids(evidence_map)
        evidence_ids = [str(item) for item in data.get("evidence_ids", []) if str(item) in available]
        return {
            "title": str(data.get("title") or f"{brief['name']} 的待验证空白"),
            "limitation": str(data.get("limitation") or "现有证据尚未覆盖关键边界条件。"),
            "opportunity": str(data.get("opportunity") or "设计一个可控实验来验证新的技术路径。"),
            "research_question": str(data.get("research_question") or f"如何改进 {brief['name']} 的可靠性？"),
            "evidence_ids": evidence_ids,
            "uncertainty": str(data.get("uncertainty") or "需要通过更完整的文献阅读与实验确认。"),
            "evidence_rationale": str(data.get("evidence_rationale") or data.get("rationale") or ""),
        }

    @staticmethod
    def _normalize_candidate(
        item: Any, brief: dict[str, Any], evidence_map: dict[str, Any], index: int
    ) -> dict[str, Any]:
        data = item if isinstance(item, dict) else {}
        available = ResearchIdeaWorkbenchService._available_evidence_ids(evidence_map)
        evidence_ids = [str(value) for value in data.get("evidence_ids", []) if str(value) in available]
        experiment = data.get("minimum_experiment") if isinstance(data.get("minimum_experiment"), dict) else {}
        return {
            "title": str(data.get("title") or f"{brief['name']} 候选假设 {index + 1}"),
            "path": str(data.get("path") or ("grounded" if index % 2 == 0 else "inspiration")),
            "gap": str(data.get("gap") or "现有方法在关键边界条件下仍缺乏系统验证。"),
            "hypothesis": str(data.get("hypothesis") or f"通过针对性约束可以提升 {brief['name']} 的可验证性能。"),
            "approach": str(data.get("approach") or "构建一个可替换模块，并在统一设置下与强基线对比。"),
            "evidence_ids": evidence_ids or list(available)[:2],
            "risks": [str(value) for value in data.get("risks", [])] or ["改进可能只在单一数据集上成立"],
            "falsification_test": str(data.get("falsification_test") or "若主要指标未稳定超过强基线，则否定该假设。"),
            "minimum_experiment": {
                "dataset": str(experiment.get("dataset") or "选择一个公开基准并保留验证集"),
                "baselines": [str(value) for value in experiment.get("baselines", [])] or ["当前最强可复现基线"],
                "metrics": [str(value) for value in experiment.get("metrics", [])] or ["主要任务指标", "效率指标"],
                "steps": [str(value) for value in experiment.get("steps", [])]
                or ["复现基线", "实现最小改动", "运行消融与误差分析"],
            },
        }

    @staticmethod
    def _normalize_review(review: Any, candidate: dict[str, Any], index: int) -> dict[str, Any]:
        data = review if isinstance(review, dict) else {}
        scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
        fallback = 7.0 - min(index, 4) * 0.35
        normalized_scores = {
            key: round(max(1.0, min(10.0, float(scores.get(key, fallback)))), 1)
            for key in REVIEW_WEIGHTS
        }
        return {
            "scores": normalized_scores,
            "rationale": str(data.get("rationale") or "该假设具备明确验证路径，但仍需扩大证据覆盖并验证泛化性。"),
            "uncertainty": str(data.get("uncertainty") or "当前结论受限于本地论文库覆盖范围。"),
            "recommendation": str(data.get("recommendation") or ("advance" if index < 3 else "revise")),
        }

    @staticmethod
    def _weighted_score(scores: dict[str, float]) -> float:
        return round(sum(float(scores[key]) * weight for key, weight in REVIEW_WEIGHTS.items()), 2)

    @staticmethod
    def _available_evidence_ids(evidence_map: dict[str, Any]) -> set[str]:
        return {
            str(item["paper_id"])
            for category in ("seed", "background", "inspiration")
            for item in evidence_map.get(category, [])
            if item.get("paper_id")
        }

    @staticmethod
    def _evidence_items_by_ids(evidence_map: dict[str, Any], evidence_ids: list[Any]) -> list[dict[str, Any]]:
        wanted = {str(item) for item in evidence_ids if item}
        if not wanted:
            return []
        items = []
        for category in ("seed", "background", "inspiration"):
            for item in evidence_map.get(category, []) or []:
                if str(item.get("paper_id")) in wanted:
                    items.append({
                        "paper_id": item.get("paper_id"),
                        "title": item.get("title"),
                        "category": item.get("category") or category,
                        "source": item.get("source"),
                        "relevance": item.get("relevance"),
                        "abstract_excerpt": item.get("abstract_excerpt"),
                    })
        return items

    @staticmethod
    def summarize_gap_feedback(gap_map: dict[str, Any]) -> list[dict[str, Any]]:
        summary = []
        for index, gap in enumerate(gap_map.get("gaps") or []):
            if not isinstance(gap, dict):
                continue
            feedback = gap.get("user_feedback") or {}
            labels = [str(label) for label in feedback.get("labels") or [] if label]
            if not feedback and not gap.get("refinement"):
                continue
            summary.append({
                "index": index,
                "title": str(gap.get("title") or ""),
                "rating": str(feedback.get("rating") or ""),
                "labels": labels,
                "note": str(feedback.get("note") or "")[:240],
                "refined": bool(gap.get("refinement")),
                "selection_status": gap.get("selection_status"),
            })
        return summary

    @staticmethod
    def _fallback_refined_gap(
        brief: dict[str, Any],
        current_gap: dict[str, Any],
        focus_note: str,
    ) -> dict[str, Any]:
        title = str(current_gap.get("title") or f"{brief['name']} 的待细化空白")
        feedback = current_gap.get("user_feedback") or {}
        labels = set(feedback.get("labels") or [])
        narrowing = "围绕一个明确数据切片和强基线重新界定边界"
        if "evidence_weak" in labels:
            narrowing = "先限定到已有证据能直接支撑的数据切片"
        elif "too_broad" in labels:
            narrowing = "把问题收窄到一个失败模式和一个可复现实验"
        elif "already_done" in labels:
            narrowing = "避开已覆盖设置，转向未系统验证的边界条件"
        focus_clause = f" 用户强调：{focus_note}" if focus_note else ""
        return {
            "title": f"{title}（细化版）",
            "limitation": f"{current_gap.get('limitation') or '当前表述仍偏宽泛。'} 需要{narrowing}。",
            "opportunity": f"{current_gap.get('opportunity') or '重新设计更窄的验证路径。'}{focus_clause}",
            "research_question": f"在{brief['name']}中，{narrowing}后是否仍能获得可复现收益？",
            "evidence_ids": current_gap.get("evidence_ids") or [],
            "uncertainty": "该细化来自用户反馈 fallback，需要后续结合全文证据复核。",
            "evidence_rationale": "沿用当前 Gap 的证据引用，并根据用户反馈收窄验证边界。",
        }

    @staticmethod
    def _fallback_gap_map(brief: dict[str, Any], evidence_map: dict[str, Any]) -> dict[str, Any]:
        evidence_ids = list(ResearchIdeaWorkbenchService._available_evidence_ids(evidence_map))
        return {
            "summary": f"围绕「{brief['name']}」从本地论文库整理出的初步 Gap Map",
            "gaps": [
                {
                    "title": "现有方法的边界条件缺少系统验证",
                    "limitation": "已有工作通常聚焦平均指标，对失败模式和适用边界解释不足。",
                    "opportunity": "围绕关键变量设计受控消融，建立可复现的边界分析。",
                    "research_question": f"哪些边界条件决定了 {brief['name']} 方法的真实收益？",
                    "evidence_ids": evidence_ids[:3],
                    "uncertainty": "需要阅读全文并补充最新外部文献后确认。",
                },
                {
                    "title": "准确率、效率与可靠性的联合优化不足",
                    "limitation": "现有方案常单独报告效果或效率，缺少统一权衡。",
                    "opportunity": "建立多目标评测协议并探索轻量改进。",
                    "research_question": f"能否在不牺牲可靠性的前提下降低 {brief['name']} 的成本？",
                    "evidence_ids": evidence_ids[1:4],
                    "uncertainty": "本地论文库可能未覆盖全部强基线。",
                },
            ],
        }

    @staticmethod
    def _fallback_candidates(
        brief: dict[str, Any],
        evidence_map: dict[str, Any],
        gap_map: dict[str, Any],
        count: int,
        *,
        offset: int = 0,
        generation_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        evidence_ids = list(ResearchIdeaWorkbenchService._available_evidence_ids(evidence_map))
        gaps = gap_map.get("gaps") or [{}]
        context = generation_context or {}
        selection = context.get("gap_selection") or {}
        constraints = context.get("generation_constraints") or {}
        usable_gaps = [
            gap for gap in gaps
            if (gap.get("user_feedback") or {}).get("rating") != "reject"
            and "misaligned" not in ((gap.get("user_feedback") or {}).get("labels") or [])
        ]
        if usable_gaps:
            gaps = usable_gaps
        focus_note = selection.get("focus_note") or ""
        budget = constraints.get("resource_budget") or "reproducible"
        mode = constraints.get("research_mode") or "balanced"
        strategies = [
            ("边界条件审计", "构建边界条件切片与失败模式分析，定位收益出现和消失的区域。"),
            ("轻量校准模块", "加入单一可替换的校准模块，在统一预算下验证可靠性收益。"),
            ("多目标预算约束", "同时约束主指标、推理成本与稳定性，比较不同预算下的 Pareto 前沿。"),
            ("跨场景泛化验证", "在分布变化和低资源设置中复测强基线，验证改进是否可迁移。"),
            ("反事实消融协议", "通过反事实替换和逐组件消融排除训练预算、数据泄漏等混杂因素。"),
        ]
        if mode == "theory":
            strategies.insert(0, ("机制假设建模", "明确关键变量之间的机制假设，并设计可证伪的理论或合成实验。"))
        elif mode == "system":
            strategies.insert(0, ("系统化管线改造", "把核心假设落到可替换系统模块，并记录端到端可靠性与成本。"))
        elif mode == "application":
            strategies.insert(0, ("应用场景验证", "围绕真实应用约束设置任务切片，评估收益是否可迁移。"))
        dataset = "低算力公开基准" if budget == "low_compute" else "可复现实验基准" if budget == "reproducible" else "大模型或高资源基准"
        candidates = []
        for step in range(count):
            index = offset + step
            gap = gaps[index % len(gaps)]
            path = ("grounded", "inspiration", "grounded")[index % 3]
            strategy_title, strategy = strategies[index % len(strategies)]
            feedback = gap.get("user_feedback") or {}
            feedback_note = feedback.get("note") or ""
            feedback_labels = ", ".join(feedback.get("labels") or [])
            feedback_clause = ""
            if feedback.get("rating") or feedback_labels or feedback_note:
                feedback_clause = f" Gap 反馈：rating={feedback.get('rating') or '未标注'}; labels={feedback_labels or '无'}; note={feedback_note or '无'}。"
            candidates.append(
                {
                    "title": f"{brief['name']}：{strategy_title}",
                    "path": path,
                    "gap": gap.get("limitation") or "现有方法缺少边界验证。",
                    "hypothesis": f"针对「{gap.get('title') or brief['name']}」采用{strategy_title}后，可在{dataset}上获得可复现的改进信号。",
                    "approach": f"先复现强基线，再{strategy}" + (f" 用户关注：{focus_note}" if focus_note else "") + feedback_clause,
                    "evidence_ids": gap.get("evidence_ids") or evidence_ids[:2],
                    "risks": ["收益可能来自训练预算差异", "本地论文覆盖不足"],
                    "falsification_test": "统一训练和推理预算后，若主要指标和效率指标均未稳定改善，则否定假设。",
                    "minimum_experiment": {
                        "dataset": dataset,
                        "baselines": ["可复现强基线", "无改动消融"],
                        "metrics": ["主要任务指标", "推理成本", "稳定性"],
                        "steps": ["复现基线", "实现最小模块", "统一预算对比", "误差分析"],
                    },
                }
            )
        return candidates
