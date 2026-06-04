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
    "generating": (56, "正在通过多条路径生成候选假设"),
    "deduplicating": (68, "正在合并重复方向"),
    "reviewing": (82, "正在进行六维评审"),
    "selecting": (94, "正在整理最值得推进的 Proposal"),
    "complete": (100, "Idea 工作台已完成"),
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

            await self._transition(run, "generating", callback=on_progress)
            candidates = await self.generate_candidates(brief, evidence_map, gap_map, num_ideas)
            tree_candidates, tree_summary = self.expand_candidate_tree(candidates, rounds=2, beam_width=max(num_ideas * 2, 4))
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
            novelty_checked = self.novelty_check_candidates(reviewed, evidence_map)
            adversarial_reviewed = self.adversarial_review_candidates(novelty_checked)
            reviewed = self.apply_quality_adjustments(adversarial_reviewed)
            run.candidate_pool = reviewed
            run.review_summary = {
                "rubric": REVIEW_WEIGHTS,
                "duplicates": duplicate_groups,
                "search_tree": tree_summary,
                "reviewed_count": len(reviewed),
                "novelty": self._summarize_novelty(reviewed),
                "adversarial": self._summarize_adversarial(reviewed),
            }
            await self.session.commit()
            await self._emit(
                on_progress,
                {"type": "artifact", "artifact": "review_summary", "data": run.review_summary},
            )

            await self._transition(run, "selecting", callback=on_progress)
            ideas = await self.persist_top_proposals(run, reviewed, evidence_map, num_ideas)
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

        seeds = [
            self._evidence_item(paper, "seed", score_by_id.get(str(paper.id), 1.0))
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
        }

    @staticmethod
    def _evidence_item(paper: Paper, category: str, score: float) -> dict[str, Any]:
        abstract = re.sub(r"\s+", " ", paper.abstract or "").strip()
        reason = {
            "seed": "用户主动选入的核心论文",
            "background": "与研究简报高度相关，可用于界定现有方法与限制",
            "inspiration": "可用于跨论文组合或寻找不同技术路径",
        }[category]
        return {
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

    async def generate_candidates(
        self,
        brief: dict[str, Any],
        evidence_map: dict[str, Any],
        gap_map: dict[str, Any],
        num_ideas: int,
    ) -> list[dict[str, Any]]:
        requested = max(num_ideas * 3, 8)
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
证据：{self._format_evidence(evidence_map, limit=10)}
"""
        data = await self._chat_json(prompt)
        candidates = data.get("candidates") if isinstance(data, dict) else None
        if not isinstance(candidates, list) or not candidates:
            candidates = self._fallback_candidates(brief, evidence_map, gap_map, requested)
        normalized = [self._normalize_candidate(item, brief, evidence_map, index) for index, item in enumerate(candidates)]
        if len(normalized) < requested:
            normalized.extend(self._fallback_candidates(brief, evidence_map, gap_map, requested - len(normalized), offset=len(normalized)))
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

    def expand_candidate_tree(
        self,
        candidates: list[dict[str, Any]],
        *,
        rounds: int = 2,
        beam_width: int = 6,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Lightweight progressive tree search over candidate proposals."""
        roots = [self._with_tree_metadata(candidate, round_number=0, operator="root") for candidate in candidates]
        all_candidates = list(roots)
        frontier = roots[:beam_width]
        operators = ("strong_baseline", "failure_mode", "cost_aware")
        for round_number in range(1, max(1, rounds)):
            next_frontier = []
            for parent in frontier[:beam_width]:
                for operator in operators:
                    child = self._mutate_candidate(parent, operator, round_number)
                    next_frontier.append(child)
            all_candidates.extend(next_frontier)
            frontier = sorted(next_frontier, key=self._candidate_potential, reverse=True)[:beam_width]
        summary = {
            "rounds": rounds,
            "beam_width": beam_width,
            "root_count": len(roots),
            "expanded_count": max(0, len(all_candidates) - len(roots)),
            "operators": list(operators),
        }
        return all_candidates, summary

    def _with_tree_metadata(
        self,
        candidate: dict[str, Any],
        *,
        round_number: int,
        operator: str,
        parent: dict[str, Any] | None = None,
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
    ) -> list[dict[str, Any]]:
        evidence_items = [
            item
            for category in ("seed", "background", "inspiration")
            for item in evidence_map.get(category, [])
        ]
        return [
            {**candidate, "novelty_check": self._novelty_check(candidate, evidence_items)}
            for candidate in candidates
        ]

    def _novelty_check(self, candidate: dict[str, Any], evidence_items: list[dict[str, Any]]) -> dict[str, Any]:
        candidate_tokens = self._dedup_tokens(
            f"{candidate.get('title', '')} {candidate.get('hypothesis', '')} {candidate.get('approach', '')}"
        )
        nearest = None
        best_similarity = 0.0
        for item in evidence_items:
            evidence_tokens = self._dedup_tokens(
                f"{item.get('title', '')} {item.get('abstract_excerpt', '')}"
            )
            if not candidate_tokens or not evidence_tokens:
                similarity = 0.0
            else:
                similarity = len(candidate_tokens & evidence_tokens) / len(candidate_tokens | evidence_tokens)
            if similarity > best_similarity:
                best_similarity = similarity
                nearest = item

        novelty_score = round(max(0.0, 1.0 - best_similarity), 3)
        if best_similarity >= 0.46:
            status = "too_similar"
            rationale = "候选与已有证据论文高度重合，可能只是已有工作的变体。"
        elif best_similarity >= 0.26:
            status = "incremental"
            rationale = "候选与已有工作存在明显重叠，适合作为增量改进但需要强调区别。"
        else:
            status = "likely_novel"
            rationale = "候选与当前证据集重叠较低，具备进一步做新颖性检查的价值。"

        return {
            "status": status,
            "score": novelty_score,
            "max_similarity": round(best_similarity, 3),
            "nearest_evidence": {
                "paper_id": nearest.get("paper_id"),
                "title": nearest.get("title"),
                "source": nearest.get("source"),
            } if nearest else None,
            "rationale": rationale,
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
                referenced_papers={"paper_ids": evidence_ids},
                hypothesis=candidate["hypothesis"],
                evidence_json={"items": evidence, "scope": evidence_map.get("scope")},
                review_json={
                    **review,
                    "aggregate_score": candidate["score"],
                    "base_score": candidate.get("base_score", candidate["score"]),
                    "novelty_check": candidate.get("novelty_check"),
                    "adversarial_review": candidate.get("adversarial_review"),
                    "search_tree": candidate.get("tree"),
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
            f"- [{item['paper_id']}] ({item['category']}) {item['title']}: {item.get('abstract_excerpt', '')}"
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
    ) -> list[dict[str, Any]]:
        evidence_ids = list(ResearchIdeaWorkbenchService._available_evidence_ids(evidence_map))
        gaps = gap_map.get("gaps") or [{}]
        strategies = [
            ("边界条件审计", "构建边界条件切片与失败模式分析，定位收益出现和消失的区域。"),
            ("轻量校准模块", "加入单一可替换的校准模块，在统一预算下验证可靠性收益。"),
            ("多目标预算约束", "同时约束主指标、推理成本与稳定性，比较不同预算下的 Pareto 前沿。"),
            ("跨场景泛化验证", "在分布变化和低资源设置中复测强基线，验证改进是否可迁移。"),
            ("反事实消融协议", "通过反事实替换和逐组件消融排除训练预算、数据泄漏等混杂因素。"),
        ]
        candidates = []
        for step in range(count):
            index = offset + step
            gap = gaps[index % len(gaps)]
            path = ("grounded", "inspiration", "grounded")[index % 3]
            strategy_title, strategy = strategies[index % len(strategies)]
            candidates.append(
                {
                    "title": f"{brief['name']}：{strategy_title}",
                    "path": path,
                    "gap": gap.get("limitation") or "现有方法缺少边界验证。",
                    "hypothesis": f"针对「{gap.get('title') or brief['name']}」采用{strategy_title}后，可在统一实验条件下获得可复现的改进信号。",
                    "approach": f"先复现强基线，再{strategy}",
                    "evidence_ids": gap.get("evidence_ids") or evidence_ids[:2],
                    "risks": ["收益可能来自训练预算差异", "本地论文覆盖不足"],
                    "falsification_test": "统一训练和推理预算后，若主要指标和效率指标均未稳定改善，则否定假设。",
                    "minimum_experiment": {
                        "dataset": "选择与课题匹配的公开基准",
                        "baselines": ["可复现强基线", "无改动消融"],
                        "metrics": ["主要任务指标", "推理成本", "稳定性"],
                        "steps": ["复现基线", "实现最小模块", "统一预算对比", "误差分析"],
                    },
                }
            )
        return candidates
