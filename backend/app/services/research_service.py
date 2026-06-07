"""科研 Pipeline 服务 — Idea 生成、讨论、代码生成。"""

import json
import logging
import re
from difflib import unified_diff
from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.services.llm import llm_service
from app.services.rag_service import RAGService
from app.db.models.paper import Paper
from app.db.models.research import ResearchCodeProjectVersion, ResearchProject, ResearchIdea
from app.services.research_idea_workbench import ResearchIdeaWorkbenchService

logger = logging.getLogger(__name__)

COPILOT_MODES = {"mentor", "skeptic", "experiment_designer", "writer"}
COPILOT_MODE_PROMPTS = {
    "mentor": "你是资深研究导师，目标是帮助学生把 Proposal 细化成更清晰、可推进的研究方案。",
    "skeptic": "你是严格审稿人，优先攻击 novelty、证据缺口、可行性、实验设置和潜在撞车风险。",
    "experiment_designer": "你是实验设计专家，优先给出最小实验、强基线、指标、消融和失败判定。",
    "writer": "你是论文写作顾问，优先帮助整理贡献点、related work 角度、claim 边界和写作准备度。",
}

PROPOSAL_BOARD_STATUSES = [
    ("needs_evidence", "需要补证据"),
    ("needs_experiment_design", "需要补实验设计"),
    ("ready_for_experiment", "准备跑实验"),
    ("needs_evolution", "已有反馈，适合演化"),
    ("ready_for_writing", "准备写作"),
    ("draft_review", "待筛选"),
    ("implemented", "已有代码"),
    ("rejected", "已淘汰"),
]
CODE_PROJECT_MAX_FILES = 24
CODE_PROJECT_MAX_FILE_CHARS = 24000
CODE_PROJECT_DEFAULT_FILES = {
    "README.md",
    "requirements.txt",
    "configs/default.yaml",
    "src/data.py",
    "src/model.py",
    "src/train.py",
    "src/evaluate.py",
    "scripts/run_baseline.sh",
    "scripts/run_experiment.sh",
    "analysis/plot_results.py",
}


class ResearchPipelineService:
    """科研自动化 Pipeline 服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_ideas(
        self,
        project: ResearchProject,
        num_ideas: int = 3,
    ) -> List[ResearchIdea]:
        """基于知识库中相关论文，生成创新性研究 Idea。"""
        keywords = project.keywords or []
        keyword_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)

        # 使用新的智能论文筛选服务（参考 AI-Researcher + SciPIP）
        from app.services.paper_selection import PaperSelectionService

        selector = PaperSelectionService(self.session)
        relevant_papers = await selector.select_papers(
            topic_name=project.name,
            topic_description=project.description or "",
            keywords=keywords,
            manual_paper_ids=project.paper_ids,
            max_papers=10,
        )

        if not relevant_papers:
            logger.warning(f"未找到与项目 '{project.name}' 相关的论文，请先入库或收藏相关方向的论文")
            return []

        # 统计来源分布
        sources = {}
        for _, _, src in relevant_papers:
            src_type = src.split(":")[0] if ":" in src else src
            sources[src_type] = sources.get(src_type, 0) + 1
        logger.info(f"论文来源分布: {sources}，共 {len(relevant_papers)} 篇")

        # 确保论文有较完整的内容（类似报告生成）
        from app.services.report_service import ensure_full_text
        for p, _, _ in relevant_papers[:8]:
            try:
                await ensure_full_text(p)
            except Exception:
                pass

        # 构建结构化论文上下文（参考 SciPIP/AI-Researcher 做法）
        papers_context = "\n\n---\n\n".join([
            f"### 论文 [{i+1}]: {p.title} ({p.year or 'N/A'})\n"
            f"**作者**: {', '.join(p.authors[:5]) if isinstance(p.authors, list) else str(p.authors)[:200]}\n"
            f"**摘要**: {p.abstract or 'N/A'}\n"
            f"**全文摘要**: {p.full_text[:2000] if p.full_text else p.abstract[:600] if p.abstract else 'N/A'}\n"
            f"**标签**: {', '.join(p.tags[:5]) if p.tags else 'N/A'}\n"
            f"**选择来源**: {src} | 相关度: {score:.2f}"
            for i, (p, score, src) in enumerate(relevant_papers[:8])
        ])

        # 6. 双路径 Idea 生成（参考 SciPIP 双路径策略）
        logger.info(f"开始双路径 Idea 生成，共 {len(relevant_papers)} 篇论文")

        # 路径 A: 文献推理 — 基于论文 gap 推导可行方案
        path_a_prompt = f"""你是一位资深 AI 研究科学家。请仔细分析以下论文，找出它们未解决的问题和研究空白，然后基于这些 gap 推导出 {num_ideas} 个具体可行的研究方案。

## 研究方向
名称: {project.name}
描述: {project.description or '未提供'}
关键词: {keyword_str}

## 相关论文（含全文内容）
{papers_context}

## 要求 — 文献推理路径
对每个 Idea，详细思考以下问题后给出答案：
1. 现有工作的**共同局限**是什么？（指出 2-3 个）
2. 有哪些**被忽略的研究角度**？
3. 技术上可以**如何改进**？

请用 JSON 输出，每个 Idea 包含：
- "title": 一句话标题
- "background_gap": 指出现有工作的 gap（2-3句）
- "description": 核心思路（3-4句，具体）
- "innovation": 与现有工作的本质区别
- "approach": 技术路线（具体步骤）
- "feasibility": 可行性 1-10
- "novelty": 创新性 1-10
- "clarity": 方案清晰度 1-10
- "impact": 潜在影响力 1-10

直接输出 JSON 数组，用中文。
"""
        response_a = await llm_service.chat(
            messages=[{"role": "user", "content": path_a_prompt}],
            temperature=0.6, max_tokens=4096,
        )

        # 路径 B: 自由头脑风暴 — 不受论文限制，产生突破性想法
        path_b_prompt = f"""你是一位极具创造力的 AI 研究科学家。请为研究方向「{project.name}」自由头脑风暴 {num_ideas} 个极具创新性的研究想法。

## 研究方向
名称: {project.name}
描述: {project.description or '未提供'}
关键词: {keyword_str}

## 领域概述（仅供了解背景，不要被其限制）
        {chr(10).join([f'- {p.title}: {p.abstract[:200] if p.abstract else ""}' for p, _, _ in relevant_papers[:5]])}

## 要求 — 头脑风暴路径
- 跳出已有论文的框架，大胆想象
- 可以跨领域借鉴思想（如将 CV 方法用于 NLP）
- 可以是全新问题定义、全新评价指标、全新范式
- 甚至可以对现有假设提出挑战

请用 JSON 输出，每个 Idea 包含：
- "title": 一句话标题
- "inspiration": 灵感来源
- "description": 核心思路（3-4句）
- "innovation": 为什么这是全新的
- "approach": 技术路线（具体步骤）
- "feasibility": 可行性 1-10
- "novelty": 创新性 1-10
- "clarity": 方案清晰度 1-10
- "impact": 潜在影响力 1-10

直接输出 JSON 数组，用中文。
"""
        response_b = await llm_service.chat(
            messages=[{"role": "user", "content": path_b_prompt}],
            temperature=1.0, max_tokens=4096,
        )

        # 7. 合并双路径结果，让 LLM 做最终筛选和融合
        merge_prompt = f"""你是一位资深研究导师。以下是同一个研究方向的两组 Idea：

## 路径 A: 文献推理（可行性高）
{response_a}

## 路径 B: 头脑风暴（创新性高）
{response_b}

请从两组中选出最好的 {num_ideas} 个 Idea，可以保留、合并或改进。最终输出 JSON 数组，每个元素包含：
- "title"
- "description"
- "innovation"
- "approach"
- "feasibility": 1-10
- "novelty": 1-10
- "source": "literature" 或 "brainstorm" 或 "merged"

直接输出 JSON 数组，用中文。
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": merge_prompt}],
                temperature=0.5, max_tokens=4096,
            )

            # 4. 解析 JSON 响应
            logger.info(f"LLM 原始响应 (前200字): {response[:200]}...")
            ideas = self._parse_ideas_json(response, project.id, [
                (p, score) for p, score, _ in relevant_papers[:8]
            ])
            logger.info(f"解析得到 {len(ideas)} 个 Idea")

            # 保存到数据库
            created_ideas = []
            for idea_data in ideas:
                idea = ResearchIdea(**idea_data)
                self.session.add(idea)
                created_ideas.append(idea)

            await self.session.commit()
            logger.info(f"为项目 '{project.name}' 生成 {len(created_ideas)} 个 Idea")
            return created_ideas

        except Exception as e:
            logger.error(f"Idea 合并解析失败: {e}")
            await self.session.rollback()
            return []

    def _parse_ideas_json(
        self,
        response: str,
        project_id,
        relevant_papers: list,
    ) -> list[dict]:
        """解析 LLM 返回的 JSON Idea 列表（含 4 维评分）。"""
        import json

        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                data = [data]
        except json.JSONDecodeError:
            logger.warning("JSON 解析失败，尝试文本解析")
            return self._parse_ideas_text(response, project_id, relevant_papers)

        paper_refs = {
            str(i + 1): {"title": p.title, "arxiv_id": p.arxiv_id}
            for i, (p, _) in enumerate(relevant_papers)
        }

        ideas = []
        for item in data:
            if not isinstance(item, dict):
                continue
            # 构建详细描述（含 gap 分析和灵感来源）
            desc_parts = []
            if item.get("background_gap"):
                desc_parts.append(f"【研究空白】{item['background_gap']}")
            if item.get("inspiration"):
                desc_parts.append(f"【灵感来源】{item['inspiration']}")
            desc_parts.append(f"【核心思路】{item.get('description', '')}")
            if item.get("innovation"):
                desc_parts.append(f"【创新点】{item['innovation']}")

            ideas.append({
                "project_id": project_id,
                "title": str(item.get("title", "Untitled"))[:500],
                "description": "\n\n".join(desc_parts)[:4000],
                "approach": str(item.get("approach", "")),
                "novelty": str(item.get("innovation", "")),
                "feasibility_score": float(item.get("feasibility", 7)),
                "novelty_score": float(item.get("novelty", 8)),
                "referenced_papers": paper_refs,
                "status": "draft",
                "metadata": {
                    "source": item.get("source", "merged"),
                    "clarity": float(item.get("clarity", 7)),
                    "impact": float(item.get("impact", 7)),
                },
            })
        return ideas

    def _parse_ideas_text(
        self,
        response: str,
        project_id,
        relevant_papers: list,
    ) -> list[dict]:
        """文本解析（fallback）。"""
        ideas = []
        blocks = response.split("---")
        paper_refs = {
            str(i + 1): {"title": p.title, "arxiv_id": p.arxiv_id}
            for i, (p, _) in enumerate(relevant_papers)
        }

        for block in blocks:
            block = block.strip()
            if not block or len(block) < 50:
                continue
            title = block.split("\n")[0].strip().lstrip("0123456789.。#- ")[:100]
            ideas.append({
                "project_id": project_id,
                "title": title[:500],
                "description": block[:3000],
                "approach": "",
                "novelty": "",
                "feasibility_score": 7.0,
                "novelty_score": 8.0,
                "referenced_papers": paper_refs,
                "status": "draft",
            })
        return ideas

    async def discuss_idea(
        self,
        idea: ResearchIdea,
        user_message: str,
        discussion_history: Optional[list] = None,
        *,
        project: Optional[ResearchProject] = None,
        mode: str = "mentor",
    ) -> dict[str, Any]:
        """多轮讨论细化 Idea，并返回可驱动后续演化的结构化元数据。"""
        selected_mode = mode if mode in COPILOT_MODES else "mentor"
        context = self.build_copilot_context(idea, project, discussion_history)
        system_prompt = self._copilot_system_prompt(selected_mode, context)

        messages = [{"role": "system", "content": system_prompt}]
        for item in self._recent_chat_messages(discussion_history or [], limit=8):
            messages.append(item)
        messages.append({"role": "user", "content": user_message})

        response = await llm_service.chat(
            messages=messages,
            temperature=0.65 if selected_mode != "skeptic" else 0.55,
            max_tokens=2400,
        )

        parsed = self._parse_copilot_response(response)
        metadata = self._normalize_copilot_metadata(parsed, context, selected_mode)
        reply = str(parsed.get("reply") or response or "").strip()
        if not reply:
            reply = "我暂时没有生成有效回复。建议先补齐验证闭环和最小实验信息后再继续讨论。"

        current_log = list(idea.discussion_log or [])
        current_log.append({"role": "user", "content": user_message, "mode": selected_mode})
        current_log.append({"role": "assistant", "content": reply, "mode": selected_mode, "metadata": metadata})
        idea.discussion_log = current_log
        idea.status = "discussing"
        await self.session.commit()

        return {"reply": reply, "discussion_log": current_log, "mode": selected_mode, **metadata}

    def build_copilot_context(
        self,
        idea: ResearchIdea,
        project: Optional[ResearchProject] = None,
        discussion_history: Optional[list] = None,
    ) -> dict[str, Any]:
        workbench = ResearchIdeaWorkbenchService(self.session)
        validation = workbench.validate_idea(idea, project)
        execution_pack = workbench.build_experiment_execution_pack(idea, project, experiments=[])
        evidence = self._summarize_evidence(idea.evidence_json)
        review = self._summarize_review(idea.review_json)
        lineage = self._summarize_lineage(idea)
        history = [
            {"role": item.get("role"), "content": str(item.get("content") or "")[:700], "mode": item.get("mode")}
            for item in (discussion_history or [])[-6:]
            if isinstance(item, dict) and item.get("content")
        ]
        missing = []
        if not evidence["items"]:
            missing.append("evidence")
        if not idea.experiment_plan:
            missing.append("experiment_plan")
        if not idea.review_json:
            missing.append("review")
        if not idea.parent_idea_id and not idea.evolution_json:
            missing.append("lineage")

        return {
            "idea": {
                "id": str(idea.id),
                "title": idea.title,
                "description": idea.description,
                "hypothesis": idea.hypothesis,
                "approach": idea.approach,
                "novelty": idea.novelty,
                "feasibility_score": idea.feasibility_score,
                "novelty_score": idea.novelty_score,
                "status": idea.status,
            },
            "project": {
                "id": str(project.id) if project else str(idea.project_id),
                "name": getattr(project, "name", None),
                "description": getattr(project, "description", None),
                "keywords": getattr(project, "keywords", None),
            },
            "evidence": evidence,
            "review": review,
            "experiment_plan": idea.experiment_plan or {},
            "validation": self._summarize_validation(validation),
            "execution": self._summarize_execution(execution_pack),
            "lineage": lineage,
            "evolution": idea.evolution_json or {},
            "recent_discussion": history,
            "context_summary": {
                "evidence_count": evidence["count"],
                "has_validation": True,
                "has_execution_pack": True,
                "has_lineage": bool(lineage.get("parent_idea_id") or lineage.get("evolution_round")),
                "missing": missing,
            },
        }

    def latest_copilot_evolution_focus(self, idea: ResearchIdea) -> str:
        for item in reversed(idea.discussion_log or []):
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            focus = str(metadata.get("evolution_focus") or "").strip()
            if focus:
                return focus
        return ""

    def build_iteration_timeline(
        self,
        idea: ResearchIdea,
        project: Optional[ResearchProject] = None,
        *,
        project_ideas: Optional[list[ResearchIdea]] = None,
        experiments: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Derive a bounded read-only Proposal lifecycle timeline."""
        workbench = ResearchIdeaWorkbenchService(self.session)
        validation = workbench.validate_idea(idea, project)
        execution = workbench.build_experiment_execution_pack(idea, project, experiments=experiments or [])
        created_at = self._iso_timestamp(getattr(idea, "created_at", None))
        events: list[dict[str, Any]] = [{
            "id": f"{idea.id}:created",
            "type": "created",
            "title": "Proposal 创建",
            "summary": idea.title,
            "timestamp": created_at,
            "severity": "info",
            "tags": self._timeline_tags([
                f"状态 {idea.status}",
                f"证据 {len((idea.evidence_json or {}).get('items', []) or [])}",
                f"可行性 {idea.feasibility_score}/10" if idea.feasibility_score is not None else "",
                f"新颖性 {idea.novelty_score}/10" if idea.novelty_score is not None else "",
            ]),
            "details": {
                "description": idea.description,
                "hypothesis": idea.hypothesis,
                "approach": idea.approach,
            },
        }]

        if idea.parent_idea_id or idea.evolution_json:
            evolution = idea.evolution_json or {}
            events.append({
                "id": f"{idea.id}:evolution",
                "type": "evolution",
                "title": "由上一版演化而来",
                "summary": evolution.get("rationale") or "该 Proposal 保留父版本并生成了可追溯子版本。",
                "timestamp": created_at,
                "severity": "info",
                "tags": self._timeline_tags([
                    f"第 {evolution.get('round') or 2} 轮",
                    "实验反馈驱动" if evolution.get("experiment_feedback") else "",
                    f"父版本 {idea.parent_idea_id}" if idea.parent_idea_id else "",
                ]),
                "details": {
                    "focus": evolution.get("focus"),
                    "parent_idea_id": str(idea.parent_idea_id) if idea.parent_idea_id else evolution.get("parent_idea_id"),
                    "experiment_feedback": evolution.get("experiment_feedback"),
                },
            })

        readiness = validation.get("writing_readiness") or {}
        collision = validation.get("collision_risk") or {}
        events.append({
            "id": f"{idea.id}:validation",
            "type": "validation",
            "title": "验证闭环状态",
            "summary": validation.get("summary") or readiness.get("label") or "已生成验证摘要。",
            "timestamp": created_at,
            "severity": self._timeline_severity(readiness.get("status"), collision.get("level")),
            "tags": self._timeline_tags([
                readiness.get("label"),
                collision.get("label"),
                f"实验完整度 {round(float((validation.get('coverage') or {}).get('experiment_completeness') or 0) * 100)}%",
            ]),
            "details": {
                "next_actions": validation.get("next_actions") or [],
                "feasibility_risks": validation.get("feasibility_risks") or [],
                "related_work": (validation.get("related_work") or [])[:5],
            },
        })

        execution_readiness = execution.get("readiness") or {}
        events.append({
            "id": f"{idea.id}:execution",
            "type": "execution",
            "title": "实验推进状态",
            "summary": execution.get("summary") or execution_readiness.get("label") or "已生成实验推进摘要。",
            "timestamp": created_at,
            "severity": "success" if execution_readiness.get("status") == "ready" else "warning",
            "tags": self._timeline_tags([
                execution_readiness.get("label"),
                f"推进度 {round(float(execution_readiness.get('score') or 0) * 100)}%",
                f"反馈 {(execution.get('feedback') or {}).get('count') or 0}",
            ]),
            "details": {
                "minimum_tasks": execution.get("minimum_tasks") or [],
                "success_metrics": execution.get("success_metrics") or [],
                "next_actions": execution.get("next_actions") or [],
                "risks": execution.get("risks") or [],
            },
        })

        events.extend(self._discussion_timeline_events(idea, created_at))
        events.extend(self._experiment_timeline_events(idea, experiments or [], created_at))
        events.extend(self._child_version_timeline_events(idea, project_ideas or [], created_at))

        events = sorted(events, key=lambda event: (event.get("timestamp") or "", event.get("id") or ""))
        return {
            "idea_id": str(idea.id),
            "project_id": str(idea.project_id),
            "title": idea.title,
            "summary": {
                "event_count": len(events),
                "discussion_milestones": len([event for event in events if event["type"] == "discussion"]),
                "experiment_count": len([event for event in events if event["type"] == "experiment"]),
                "child_version_count": len([event for event in events if event["type"] == "child_version"]),
                "latest_event_type": events[-1]["type"] if events else None,
            },
            "events": events,
        }

    def build_proposal_progress_board(
        self,
        project: ResearchProject,
        ideas: list[ResearchIdea],
        *,
        experiments: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Build a deterministic board that explains what each Proposal needs next."""
        experiments = experiments or []
        items = sorted(
            [self._proposal_board_item(project, idea, experiments) for idea in ideas],
            key=lambda item: item["priority"],
            reverse=True,
        )
        status_meta = {key: label for key, label in PROPOSAL_BOARD_STATUSES}
        groups = [
            {
                "status": key,
                "label": label,
                "count": len(group_items),
                "items": group_items,
            }
            for key, label in PROPOSAL_BOARD_STATUSES
            for group_items in [[item for item in items if item["status"] == key]]
        ]
        actionable = [item for item in items if item["status"] not in {"implemented", "rejected"}]
        recommended = actionable[0] if actionable else None
        return {
            "project_id": str(project.id),
            "summary": {
                "total": len(items),
                "actionable": len(actionable),
                "recommended": recommended["idea_id"] if recommended else None,
                "counts": {key: len([item for item in items if item["status"] == key]) for key in status_meta},
            },
            "groups": groups,
        }

    def _proposal_board_item(
        self,
        project: ResearchProject,
        idea: ResearchIdea,
        experiments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        workbench = ResearchIdeaWorkbenchService(self.session)
        validation = workbench.validate_idea(idea, project)
        execution = workbench.build_experiment_execution_pack(idea, project, experiments=experiments)
        linked_experiments = [item for item in experiments if str(item.get("idea_id") or "") == str(idea.id)]
        has_experiment_results = any(item.get("results") for item in linked_experiments)
        coverage = validation.get("coverage") or {}
        readiness = validation.get("writing_readiness") or {}
        collision = validation.get("collision_risk") or {}
        execution_readiness = execution.get("readiness") or {}
        evidence_count = int(coverage.get("evidence_count") or len((idea.evidence_json or {}).get("items", []) or []))
        experiment_completeness = float(coverage.get("experiment_completeness") or 0)
        review_score = float((idea.review_json or {}).get("aggregate_score") or (((idea.novelty_score or 0) + (idea.feasibility_score or 0)) / 2))
        blockers = self._proposal_board_blockers(validation, execution)
        status, action = self._proposal_board_status_and_action(
            idea,
            validation,
            execution,
            has_experiment_results,
            blockers,
        )
        priority = self._proposal_board_priority(
            status,
            review_score,
            evidence_count,
            experiment_completeness,
            has_experiment_results,
            collision.get("level"),
            idea.status,
        )
        return {
            "idea_id": str(idea.id),
            "title": idea.title,
            "status": status,
            "label": dict(PROPOSAL_BOARD_STATUSES).get(status, status),
            "priority": priority,
            "manual_status": idea.status,
            "recommended_action": action,
            "blockers": blockers[:5],
            "signals": {
                "review_score": round(review_score, 2),
                "evidence_count": evidence_count,
                "experiment_completeness": round(experiment_completeness, 2),
                "writing_readiness": readiness.get("status"),
                "collision_level": collision.get("level"),
                "execution_status": execution_readiness.get("status"),
                "experiment_feedback_count": len(linked_experiments),
                "has_experiment_results": has_experiment_results,
                "discussion_turns": len(idea.discussion_log or []),
                "evolution_round": (idea.evolution_json or {}).get("round") or (2 if idea.parent_idea_id else 1),
            },
            "summary": self._proposal_board_summary(idea, validation, execution),
            "created_at": self._iso_timestamp(getattr(idea, "created_at", None)),
        }

    @staticmethod
    def _proposal_board_blockers(validation: dict[str, Any], execution: dict[str, Any]) -> list[str]:
        blockers = []
        coverage = validation.get("coverage") or {}
        if not coverage.get("has_enough_evidence"):
            blockers.append("证据覆盖不足")
        for risk in validation.get("feasibility_risks") or []:
            message = risk.get("message") if isinstance(risk, dict) else str(risk)
            if message:
                blockers.append(str(message))
        for task in execution.get("minimum_tasks") or []:
            if task.get("status") != "ready":
                blockers.append(f"补齐实验设置：{task.get('label')}")
        return list(dict.fromkeys(blockers))

    @staticmethod
    def _proposal_board_status_and_action(
        idea: ResearchIdea,
        validation: dict[str, Any],
        execution: dict[str, Any],
        has_experiment_results: bool,
        blockers: list[str],
    ) -> tuple[str, dict[str, str]]:
        coverage = validation.get("coverage") or {}
        readiness = validation.get("writing_readiness") or {}
        execution_readiness = execution.get("readiness") or {}
        if idea.status == "rejected":
            return "rejected", {"type": "restore", "label": "恢复待筛选", "target": "decision"}
        if idea.status == "implemented":
            return "implemented", {"type": "timeline", "label": "查看迭代轨迹", "target": "timeline"}
        if has_experiment_results:
            return "needs_evolution", {"type": "evolve", "label": "根据反馈演化", "target": "copilot"}
        if readiness.get("status") == "ready" and execution_readiness.get("status") == "ready":
            return "ready_for_writing", {"type": "writing", "label": "生成写作草稿", "target": "writing"}
        if not coverage.get("has_enough_evidence"):
            return "needs_evidence", {"type": "evidence", "label": "补充证据", "target": "evidence"}
        if execution_readiness.get("status") == "needs_setup" or any("实验设置" in item for item in blockers):
            return "needs_experiment_design", {"type": "execution", "label": "完善实验推进包", "target": "execution"}
        if execution_readiness.get("status") == "ready":
            return "ready_for_experiment", {"type": "experiment", "label": "记录第一轮实验", "target": "experiment"}
        return "draft_review", {"type": "copilot", "label": "用 Copilot 继续评审", "target": "copilot"}

    @staticmethod
    def _proposal_board_priority(
        status: str,
        review_score: float,
        evidence_count: int,
        experiment_completeness: float,
        has_experiment_results: bool,
        collision_level: Any,
        manual_status: str,
    ) -> int:
        if manual_status == "rejected":
            return 0
        if manual_status == "implemented":
            return 20
        score = (review_score * 7) + min(evidence_count, 6) * 4 + experiment_completeness * 20
        if has_experiment_results:
            score += 18
        if status == "ready_for_writing":
            score += 16
        elif status == "ready_for_experiment":
            score += 10
        elif status == "needs_evolution":
            score += 14
        elif status == "needs_evidence":
            score -= 8
        if collision_level == "high":
            score -= 18
        elif collision_level == "medium":
            score -= 6
        return max(0, min(100, round(score)))

    @staticmethod
    def _proposal_board_summary(
        idea: ResearchIdea,
        validation: dict[str, Any],
        execution: dict[str, Any],
    ) -> str:
        validation_summary = validation.get("summary") or ""
        execution_label = ((execution.get("readiness") or {}).get("label") or "")
        if validation_summary and execution_label:
            return f"{validation_summary}；{execution_label}"
        return validation_summary or execution_label or idea.description or "暂无推进摘要"

    def _discussion_timeline_events(self, idea: ResearchIdea, fallback_timestamp: str) -> list[dict[str, Any]]:
        assistant_entries = [
            item for item in (idea.discussion_log or [])
            if isinstance(item, dict) and item.get("role") == "assistant" and item.get("content")
        ][-8:]
        events = []
        for index, item in enumerate(assistant_entries, start=1):
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            mode = item.get("mode") or "mentor"
            focus = metadata.get("evolution_focus")
            events.append({
                "id": f"{idea.id}:discussion:{index}",
                "type": "discussion",
                "title": f"Copilot 讨论 · {mode}",
                "summary": str(item.get("content") or "")[:240],
                "timestamp": self._iso_timestamp(item.get("timestamp")) or fallback_timestamp,
                "severity": "info",
                "tags": self._timeline_tags([mode, "可演化" if focus else "", f"风险 {len(metadata.get('risks') or [])}"]),
                "details": {
                    "risks": metadata.get("risks") or [],
                    "next_actions": metadata.get("next_actions") or [],
                    "suggested_questions": metadata.get("suggested_questions") or [],
                    "evolution_focus": focus,
                },
            })
        return events

    def _experiment_timeline_events(
        self,
        idea: ResearchIdea,
        experiments: list[dict[str, Any]],
        fallback_timestamp: str,
    ) -> list[dict[str, Any]]:
        events = []
        for index, experiment in enumerate([item for item in experiments if str(item.get("idea_id") or "") == str(idea.id)], start=1):
            events.append({
                "id": f"{idea.id}:experiment:{experiment.get('experiment_id') or index}",
                "type": "experiment",
                "title": f"实验反馈 · {experiment.get('name') or '未命名实验'}",
                "summary": experiment.get("notes") or f"数据集：{experiment.get('dataset') or '未填写'}",
                "timestamp": self._iso_timestamp(experiment.get("timestamp")) or fallback_timestamp,
                "severity": "success" if experiment.get("results") else "info",
                "tags": self._timeline_tags([experiment.get("dataset"), "已有结果" if experiment.get("results") else "无结果"]),
                "details": {
                    "experiment_id": experiment.get("experiment_id"),
                    "results": experiment.get("results") or {},
                    "notes": experiment.get("notes"),
                    "hyperparams": experiment.get("hyperparams") or {},
                },
            })
        return events

    def _child_version_timeline_events(
        self,
        idea: ResearchIdea,
        project_ideas: list[ResearchIdea],
        fallback_timestamp: str,
    ) -> list[dict[str, Any]]:
        children = [item for item in project_ideas if str(getattr(item, "parent_idea_id", "") or "") == str(idea.id)]
        events = []
        for child in children[:12]:
            evolution = child.evolution_json or {}
            events.append({
                "id": f"{idea.id}:child:{child.id}",
                "type": "child_version",
                "title": "生成下一版 Proposal",
                "summary": child.title,
                "timestamp": self._iso_timestamp(getattr(child, "created_at", None)) or fallback_timestamp,
                "severity": "info",
                "tags": self._timeline_tags([f"第 {evolution.get('round') or 2} 轮", child.status]),
                "details": {
                    "child_idea_id": str(child.id),
                    "rationale": evolution.get("rationale"),
                    "focus": evolution.get("focus"),
                },
            })
        return events

    @staticmethod
    def _timeline_tags(values: list[Any]) -> list[str]:
        return [str(value) for value in values if str(value or "").strip()][:6]

    @staticmethod
    def _timeline_severity(readiness_status: Any, collision_level: Any) -> str:
        if readiness_status == "ready":
            return "success"
        if readiness_status == "blocked" or collision_level == "high":
            return "danger"
        return "warning"

    @staticmethod
    def _iso_timestamp(value: Any) -> str:
        if isinstance(value, datetime):
            timestamp = value
        elif isinstance(value, str) and value.strip():
            return value
        else:
            timestamp = datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.isoformat()

    def _copilot_system_prompt(self, mode: str, context: dict[str, Any]) -> str:
        return f"""{COPILOT_MODE_PROMPTS[mode]}

你正在协助用户迭代一个已经持久化的 Research Proposal。请基于下方 JSON 上下文回答，优先利用证据、验证闭环、实验推进包、谱系和历史讨论。不要编造不存在的论文或实验结果；如果上下文缺失，请明确指出缺口。

请只输出合法 JSON，不要使用 Markdown 代码块。JSON 格式：
{{
  "reply": "给用户看的 markdown 回复",
  "risks": ["最多 4 个关键风险"],
  "next_actions": ["最多 5 个下一步动作"],
  "suggested_questions": ["最多 4 个建议追问"],
  "evolution_focus": "如果要演化下一版 Proposal，应该聚焦的一句话"
}}

上下文：
{json.dumps(context, ensure_ascii=False)[:14000]}
"""

    @staticmethod
    def _recent_chat_messages(history: list, limit: int = 8) -> list[dict[str, str]]:
        messages = []
        for item in history[-limit:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = str(item.get("content") or "").strip()
            if role not in {"user", "assistant"} or not content:
                continue
            messages.append({"role": role, "content": content[:1200]})
        return messages

    @staticmethod
    def _parse_copilot_response(response: str) -> dict[str, Any]:
        if not response:
            return {}
        text = response.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"reply": response}
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    return parsed if isinstance(parsed, dict) else {"reply": response}
                except json.JSONDecodeError:
                    pass
        return {"reply": response}

    @staticmethod
    def _normalize_copilot_metadata(
        parsed: dict[str, Any],
        context: dict[str, Any],
        mode: str,
    ) -> dict[str, Any]:
        validation = context.get("validation") or {}
        execution = context.get("execution") or {}
        risks = ResearchPipelineService._string_list(parsed.get("risks"), limit=4)
        if not risks:
            risks = ResearchPipelineService._string_list(validation.get("feasibility_risks"), limit=4)
        next_actions = ResearchPipelineService._string_list(parsed.get("next_actions"), limit=5)
        if not next_actions:
            next_actions = ResearchPipelineService._string_list(execution.get("next_actions"), limit=5)
        suggested_questions = ResearchPipelineService._string_list(parsed.get("suggested_questions"), limit=4)
        if not suggested_questions:
            suggested_questions = ResearchPipelineService._fallback_questions(mode)
        evolution_focus = str(parsed.get("evolution_focus") or "").strip()
        if not evolution_focus:
            evolution_focus = ResearchPipelineService._fallback_evolution_focus(context, mode)
        return {
            "context_summary": context.get("context_summary") or {},
            "risks": risks,
            "next_actions": next_actions,
            "suggested_questions": suggested_questions,
            "evolution_focus": evolution_focus,
        }

    @staticmethod
    def _string_list(value: Any, limit: int) -> list[str]:
        if isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, dict):
                    text = item.get("message") or item.get("label") or item.get("title") or item.get("detail")
                else:
                    text = item
                text = str(text or "").strip()
                if text:
                    items.append(text)
            return list(dict.fromkeys(items))[:limit]
        if isinstance(value, str) and value.strip():
            return [value.strip()[:400]]
        return []

    @staticmethod
    def _fallback_questions(mode: str) -> list[str]:
        if mode == "skeptic":
            return ["这个 Proposal 最可能和哪类已有工作撞车？", "最弱的实验假设是什么？", "审稿人会质疑哪一个 claim？"]
        if mode == "experiment_designer":
            return ["第一轮最小实验应该如何设计？", "需要哪些强基线和消融？", "失败判定标准是什么？"]
        if mode == "writer":
            return ["贡献点应该如何收窄？", "related work 应该怎样组织？", "哪些证据还不足以支撑写作？"]
        return ["下一版 Proposal 应该优先改哪一点？", "这个想法的关键风险是什么？", "如何把它变成可证伪实验？"]

    @staticmethod
    def _fallback_evolution_focus(context: dict[str, Any], mode: str) -> str:
        idea = context.get("idea") or {}
        validation = context.get("validation") or {}
        title = idea.get("title") or "当前 Proposal"
        if mode == "skeptic":
            collision = validation.get("collision_risk") or {}
            return f"降低「{title}」的撞车风险，并补强 novelty 与证据边界：{collision.get('reason') or '优先处理最强审稿质疑'}"
        if mode == "experiment_designer":
            return f"把「{title}」演化为包含强基线、指标、消融和失败判定的最小实验方案"
        if mode == "writer":
            return f"收窄「{title}」的可写作贡献点，并补齐支撑 claim 的证据与实验"
        return f"基于当前验证与讨论，把「{title}」演化成更具体、可证伪、证据更充分的下一版 Proposal"

    @staticmethod
    def _summarize_evidence(evidence_json: Any) -> dict[str, Any]:
        data = evidence_json if isinstance(evidence_json, dict) else {}
        items = data.get("items") or []
        summarized = []
        for item in items[:8]:
            if not isinstance(item, dict):
                continue
            summarized.append({
                "paper_id": item.get("paper_id") or item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "score": item.get("score"),
                "source": item.get("source") or item.get("source_label"),
                "relevance": item.get("relevance") or item.get("relevance_explanation"),
                "abstract_excerpt": str(item.get("abstract_excerpt") or item.get("abstract") or "")[:500],
            })
        return {"count": len(items), "scope": data.get("scope"), "items": summarized}

    @staticmethod
    def _summarize_review(review_json: Any) -> dict[str, Any]:
        review = review_json if isinstance(review_json, dict) else {}
        scores = review.get("scores") if isinstance(review.get("scores"), dict) else {}
        adversarial = review.get("adversarial_review") if isinstance(review.get("adversarial_review"), dict) else {}
        novelty_check = review.get("novelty_check") if isinstance(review.get("novelty_check"), dict) else {}
        return {
            "scores": scores,
            "aggregate_score": review.get("aggregate_score"),
            "rationale": review.get("rationale"),
            "novelty_check": novelty_check,
            "adversarial_objections": adversarial.get("objections", [])[:5] if isinstance(adversarial.get("objections"), list) else [],
        }

    @staticmethod
    def _summarize_validation(validation: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": validation.get("summary"),
            "writing_readiness": validation.get("writing_readiness"),
            "collision_risk": validation.get("collision_risk"),
            "coverage": validation.get("coverage"),
            "feasibility_risks": ResearchPipelineService._string_list(validation.get("feasibility_risks"), limit=5),
            "next_actions": ResearchPipelineService._string_list(validation.get("next_actions"), limit=5),
            "related_work": (validation.get("related_work") or [])[:5],
        }

    @staticmethod
    def _summarize_execution(execution_pack: dict[str, Any]) -> dict[str, Any]:
        return {
            "readiness": execution_pack.get("readiness"),
            "summary": execution_pack.get("summary"),
            "minimum_tasks": execution_pack.get("minimum_tasks", [])[:5],
            "success_metrics": execution_pack.get("success_metrics", [])[:5],
            "risks": ResearchPipelineService._string_list(execution_pack.get("risks"), limit=5),
            "next_actions": ResearchPipelineService._string_list(execution_pack.get("next_actions"), limit=5),
        }

    @staticmethod
    def _summarize_lineage(idea: ResearchIdea) -> dict[str, Any]:
        evolution = idea.evolution_json if isinstance(idea.evolution_json, dict) else {}
        return {
            "parent_idea_id": str(idea.parent_idea_id) if idea.parent_idea_id else None,
            "evolution_round": evolution.get("round"),
            "evolution_focus": evolution.get("focus"),
            "evolution_rationale": evolution.get("rationale"),
        }

    async def generate_code(
        self,
        idea: ResearchIdea,
        framework: str = "pytorch",
    ) -> dict[str, Any]:
        """为 Idea 生成结构化实验项目包。"""
        prompt = self._code_project_prompt(idea, framework)

        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=8192,
            )
            try:
                parsed = self._parse_json_object(response)
            except Exception as exc:
                logger.warning("实验项目包 JSON 解析失败，使用 fallback: %s", exc)
                parsed = self._fallback_code_project(idea, framework)

            code_project = self.normalize_code_project(parsed, idea, framework)
            legacy_code = self.representative_code_from_project(code_project)
            idea.generated_code_project = code_project
            idea.generated_code = legacy_code
            idea.status = "implemented"
            await self.create_code_project_version(idea, code_project, legacy_code)
            await self.session.commit()

            return code_project
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            await self.session.rollback()
            raise

    async def create_code_project_version(
        self,
        idea: ResearchIdea,
        code_project: dict[str, Any],
        representative_code: str,
    ) -> ResearchCodeProjectVersion:
        """保存一次结构化实验项目包版本快照。"""
        result = await self.session.execute(
            select(func.max(ResearchCodeProjectVersion.version))
            .where(ResearchCodeProjectVersion.idea_id == idea.id)
        )
        next_version = int(result.scalar_one_or_none() or 0) + 1
        files = code_project.get("files") if isinstance(code_project, dict) else []
        version = ResearchCodeProjectVersion(
            idea_id=idea.id,
            version=next_version,
            project_name=str(code_project.get("name") or idea.title)[:300],
            framework=str(code_project.get("framework") or "pytorch")[:80],
            summary=str(code_project.get("summary") or "")[:2000],
            file_count=len(files) if isinstance(files, list) else 0,
            project_manifest=code_project,
            representative_code=representative_code,
        )
        self.session.add(version)
        return version

    async def list_code_project_versions(self, idea: ResearchIdea) -> list[ResearchCodeProjectVersion]:
        """列出 Idea 的实验项目包版本。"""
        result = await self.session.execute(
            select(ResearchCodeProjectVersion)
            .where(ResearchCodeProjectVersion.idea_id == idea.id)
            .order_by(ResearchCodeProjectVersion.version.desc())
        )
        return list(result.scalars().all())

    async def get_code_project_version(
        self,
        idea: ResearchIdea,
        version_number: int,
    ) -> Optional[ResearchCodeProjectVersion]:
        """读取 Idea 的某个实验项目包版本。"""
        result = await self.session.execute(
            select(ResearchCodeProjectVersion)
            .where(
                ResearchCodeProjectVersion.idea_id == idea.id,
                ResearchCodeProjectVersion.version == version_number,
            )
        )
        return result.scalar_one_or_none()

    async def compare_code_project_versions(
        self,
        idea: ResearchIdea,
        from_version: int,
        to_version: int,
    ) -> dict[str, Any]:
        """比较两个实验项目包版本。"""
        if from_version == to_version:
            raise ValueError("请选择两个不同版本进行比较")
        left = await self.get_code_project_version(idea, from_version)
        right = await self.get_code_project_version(idea, to_version)
        if not left or not right:
            raise LookupError("实验项目包版本不存在")
        return self.diff_code_project_manifests(
            left.project_manifest,
            right.project_manifest,
            from_version=from_version,
            to_version=to_version,
        )

    @classmethod
    def diff_code_project_manifests(
        cls,
        left: dict[str, Any],
        right: dict[str, Any],
        *,
        from_version: int,
        to_version: int,
    ) -> dict[str, Any]:
        """按文件路径比较两个结构化项目包。"""
        left_files = cls._code_project_file_map(left)
        right_files = cls._code_project_file_map(right)
        paths = sorted(set(left_files) | set(right_files))
        items = []
        counts = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}
        for path in paths:
            before = left_files.get(path)
            after = right_files.get(path)
            if before is None:
                status = "added"
            elif after is None:
                status = "removed"
            elif before.get("content") != after.get("content"):
                status = "modified"
            else:
                status = "unchanged"
            counts[status] += 1
            before_content = str(before.get("content") or "") if before else ""
            after_content = str(after.get("content") or "") if after else ""
            item = {
                "path": path,
                "status": status,
                "language": str((after or before or {}).get("language") or "text"),
                "purpose": str((after or before or {}).get("purpose") or ""),
                "before_line_count": cls._line_count(before_content) if before else 0,
                "after_line_count": cls._line_count(after_content) if after else 0,
                "before_content": before_content if status in {"removed", "modified"} else None,
                "after_content": after_content if status in {"added", "modified"} else None,
                "diff": cls._unified_file_diff(path, before_content, after_content) if status == "modified" else "",
            }
            items.append(item)
        return {
            "from_version": from_version,
            "to_version": to_version,
            "summary": counts,
            "files": items,
        }

    @classmethod
    def _code_project_file_map(cls, project: dict[str, Any]) -> dict[str, dict[str, Any]]:
        files = project.get("files") if isinstance(project, dict) else []
        result: dict[str, dict[str, Any]] = {}
        if not isinstance(files, list):
            return result
        for item in files:
            if not isinstance(item, dict):
                continue
            path = cls.safe_code_project_path(item.get("path"))
            if not path:
                continue
            result[path] = {
                "path": path,
                "language": item.get("language") or cls._infer_code_language(path),
                "purpose": item.get("purpose") or "",
                "content": str(item.get("content") or ""),
            }
        return result

    @staticmethod
    def _line_count(content: str) -> int:
        return 0 if not content else len(content.splitlines())

    @staticmethod
    def _unified_file_diff(path: str, before: str, after: str) -> str:
        diff = unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
            n=3,
        )
        return "\n".join(list(diff)[:220])

    def _code_project_prompt(self, idea: ResearchIdea, framework: str) -> str:
        plan = idea.experiment_plan if isinstance(idea.experiment_plan, dict) else {}
        evidence = self._summarize_evidence(idea.evidence_json)
        review = self._summarize_review(idea.review_json)
        return f"""你是科研代码项目架构师。请为以下论文 Proposal 生成一个可审阅、可下载的实验项目包，而不是单个代码片段。

## Proposal
标题: {idea.title}
描述: {idea.description or ''}
假设: {idea.hypothesis or ''}
技术路线: {idea.approach or ''}
创新点: {idea.novelty or ''}

## 实验计划
{json.dumps(plan, ensure_ascii=False, indent=2)}

## 证据摘要
{json.dumps(evidence, ensure_ascii=False, indent=2)}

## 评审摘要
{json.dumps(review, ensure_ascii=False, indent=2)}

## 输出要求
使用 {framework}，输出严格 JSON object，不要 markdown，不要解释文字。JSON schema:
{{
  "name": "short-project-name",
  "framework": "{framework}",
  "summary": "这个实验项目验证什么假设",
  "setup": ["python -m venv .venv", "pip install -r requirements.txt"],
  "run_commands": ["python src/train.py --config configs/default.yaml", "python src/evaluate.py --config configs/default.yaml"],
  "entrypoints": [
    {{"name": "train", "path": "src/train.py", "command": "python src/train.py --config configs/default.yaml", "purpose": "训练 baseline 和 proposed method"}}
  ],
  "safety_notes": ["代码仅供审阅，运行前检查数据路径和依赖"],
  "files": [
    {{"path": "README.md", "language": "markdown", "purpose": "项目说明", "content": "..."}},
    {{"path": "requirements.txt", "language": "text", "purpose": "依赖", "content": "..."}},
    {{"path": "configs/default.yaml", "language": "yaml", "purpose": "实验配置", "content": "..."}},
    {{"path": "src/data.py", "language": "python", "purpose": "数据加载与模拟数据", "content": "..."}},
    {{"path": "src/model.py", "language": "python", "purpose": "模型与方法", "content": "..."}},
    {{"path": "src/train.py", "language": "python", "purpose": "训练入口", "content": "..."}},
    {{"path": "src/evaluate.py", "language": "python", "purpose": "评估入口", "content": "..."}},
    {{"path": "scripts/run_experiment.sh", "language": "shell", "purpose": "一键运行脚本", "content": "..."}},
    {{"path": "analysis/plot_results.py", "language": "python", "purpose": "结果分析", "content": "..."}}
  ]
}}

约束:
- 文件路径必须是相对路径，不能包含 .. 或绝对路径。
- 至少包含 README.md、requirements.txt、configs/default.yaml、src/train.py、src/evaluate.py。
- 代码不要下载远程脚本，不要执行 shell 注入，不要读取用户私密路径。
- 如真实数据不可用，使用清晰的 mock dataset，并在 README 中说明替换方式。
"""

    @staticmethod
    def _parse_json_object(response: str) -> dict[str, Any]:
        text = response.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.S)
            if not match:
                raise
            parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise ValueError("expected JSON object")
        return parsed

    @classmethod
    def normalize_code_project(cls, raw: Any, idea: ResearchIdea, framework: str = "pytorch") -> dict[str, Any]:
        data = raw if isinstance(raw, dict) else {}
        fallback = cls._fallback_code_project(idea, framework)
        files = []
        seen_paths = set()
        raw_files = data.get("files") if isinstance(data.get("files"), list) else []
        for item in raw_files:
            if not isinstance(item, dict):
                continue
            path = cls.safe_code_project_path(item.get("path"))
            if not path or path in seen_paths:
                continue
            content = str(item.get("content") or "")[:CODE_PROJECT_MAX_FILE_CHARS]
            if not content.strip():
                continue
            seen_paths.add(path)
            files.append({
                "path": path,
                "language": cls._infer_code_language(path, item.get("language")),
                "purpose": str(item.get("purpose") or cls._default_file_purpose(path))[:300],
                "content": content,
            })
            if len(files) >= CODE_PROJECT_MAX_FILES:
                break

        fallback_files = {item["path"]: item for item in fallback["files"]}
        for required_path in CODE_PROJECT_DEFAULT_FILES:
            if required_path in fallback_files and required_path not in seen_paths and len(files) < CODE_PROJECT_MAX_FILES:
                files.append(fallback_files[required_path])
                seen_paths.add(required_path)

        if not files:
            files = fallback["files"]

        entrypoints = cls._normalize_entrypoints(data.get("entrypoints"), files, fallback["entrypoints"])
        run_commands = cls._string_list(data.get("run_commands"), limit=8) or fallback["run_commands"]
        setup = cls._string_list(data.get("setup"), limit=8) or fallback["setup"]
        safety_notes = cls._string_list(data.get("safety_notes"), limit=8) or fallback["safety_notes"]
        return {
            "name": cls._safe_project_name(data.get("name") or idea.title),
            "framework": str(data.get("framework") or framework or "pytorch")[:80],
            "summary": str(data.get("summary") or fallback["summary"])[:1200],
            "setup": setup,
            "run_commands": run_commands,
            "entrypoints": entrypoints,
            "safety_notes": safety_notes,
            "files": sorted(files, key=lambda item: item["path"]),
        }

    @classmethod
    def _fallback_code_project(cls, idea: ResearchIdea, framework: str = "pytorch") -> dict[str, Any]:
        project_name = cls._safe_project_name(idea.title)
        plan = idea.experiment_plan if isinstance(idea.experiment_plan, dict) else {}
        dataset = str(plan.get("dataset") or "MockResearchDataset")
        baselines = plan.get("baselines") if isinstance(plan.get("baselines"), list) else ["baseline"]
        metrics = plan.get("metrics") if isinstance(plan.get("metrics"), list) else ["accuracy"]
        steps = plan.get("steps") if isinstance(plan.get("steps"), list) else ["Train baseline", "Train proposed method", "Compare metrics"]
        requirements = "torch\nnumpy\npandas\nscikit-learn\nmatplotlib\npyyaml\n"
        config = f"""project: {project_name}
framework: {framework}
dataset: {dataset}
seed: 42
epochs: 3
batch_size: 32
learning_rate: 0.001
metrics:
{chr(10).join(f"  - {metric}" for metric in metrics)}
baselines:
{chr(10).join(f"  - {baseline}" for baseline in baselines)}
"""
        readme = f"""# {idea.title}

This generated experiment project is a reviewable starting point for the Proposal.

## Hypothesis
{idea.hypothesis or idea.description or "Define the falsifiable hypothesis before running full experiments."}

## Approach
{idea.approach or "Implement the proposed method and compare it against strong baselines."}

## Dataset
Default configuration uses `{dataset}`. If the real dataset is unavailable, `src/data.py` creates a mock dataset so the pipeline can be inspected end to end.

## Experiment Steps
{chr(10).join(f"- {step}" for step in steps)}

## Run
```bash
pip install -r requirements.txt
python src/train.py --config configs/default.yaml --variant baseline
python src/train.py --config configs/default.yaml --variant proposed
python src/evaluate.py --config configs/default.yaml
python analysis/plot_results.py --input outputs/results.json
```

## Safety
Review generated code before running. Replace mock data paths and verify dependencies in an isolated environment.
"""
        data_py = '''"""Data utilities for the generated experiment project."""

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset


def build_mock_dataset(num_samples=256, input_dim=32, num_classes=2, seed=42):
    rng = np.random.default_rng(seed)
    features = rng.normal(size=(num_samples, input_dim)).astype("float32")
    weights = rng.normal(size=(input_dim, num_classes)).astype("float32")
    labels = np.argmax(features @ weights, axis=1).astype("int64")
    return TensorDataset(torch.from_numpy(features), torch.from_numpy(labels))


def build_dataloaders(batch_size=32, seed=42):
    train = build_mock_dataset(seed=seed)
    valid = build_mock_dataset(num_samples=96, seed=seed + 1)
    return {
        "train": DataLoader(train, batch_size=batch_size, shuffle=True),
        "valid": DataLoader(valid, batch_size=batch_size),
    }
'''
        model_py = '''"""Baseline and proposed models for the generated experiment project."""

import torch
from torch import nn


class BaselineModel(nn.Module):
    def __init__(self, input_dim=32, num_classes=2):
        super().__init__()
        self.net = nn.Linear(input_dim, num_classes)

    def forward(self, x):
        return self.net(x)


class ProposedModel(nn.Module):
    def __init__(self, input_dim=32, num_classes=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        return self.net(x)


def build_model(variant="proposed"):
    if variant == "baseline":
        return BaselineModel()
    return ProposedModel()
'''
        train_py = '''"""Train baseline or proposed variant."""

import argparse
import json
from pathlib import Path

import torch
import yaml
from torch import nn

from data import build_dataloaders
from model import build_model


def accuracy(logits, labels):
    return (logits.argmax(dim=-1) == labels).float().mean().item()


def train(config, variant):
    loaders = build_dataloaders(batch_size=config.get("batch_size", 32), seed=config.get("seed", 42))
    model = build_model(variant)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.get("learning_rate", 1e-3))
    loss_fn = nn.CrossEntropyLoss()
    history = []
    for epoch in range(config.get("epochs", 3)):
        model.train()
        for features, labels in loaders["train"]:
            optimizer.zero_grad()
            loss = loss_fn(model(features), labels)
            loss.backward()
            optimizer.step()
        model.eval()
        scores = []
        with torch.no_grad():
            for features, labels in loaders["valid"]:
                scores.append(accuracy(model(features), labels))
        history.append({"epoch": epoch + 1, "valid_accuracy": sum(scores) / max(len(scores), 1)})
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{variant}_history.json"
    output_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"saved {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--variant", default="proposed", choices=["baseline", "proposed"])
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    train(config, args.variant)


if __name__ == "__main__":
    main()
'''
        evaluate_py = '''"""Evaluate generated experiment outputs."""

import json
from pathlib import Path


def read_last_score(path):
    if not path.exists():
        return None
    history = json.loads(path.read_text(encoding="utf-8"))
    if not history:
        return None
    return history[-1].get("valid_accuracy")


def main():
    output_dir = Path("outputs")
    baseline = read_last_score(output_dir / "baseline_history.json")
    proposed = read_last_score(output_dir / "proposed_history.json")
    results = {"baseline_accuracy": baseline, "proposed_accuracy": proposed}
    if baseline is not None and proposed is not None:
        results["delta"] = proposed - baseline
    output_dir.mkdir(exist_ok=True)
    (output_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
'''
        plot_py = '''"""Plot result summary for the generated experiment project."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="outputs/results.json")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    labels = ["baseline", "proposed"]
    values = [data.get("baseline_accuracy") or 0, data.get("proposed_accuracy") or 0]
    Path("outputs").mkdir(exist_ok=True)
    plt.bar(labels, values)
    plt.ylabel("validation accuracy")
    plt.tight_layout()
    plt.savefig("outputs/result_summary.png")
    print("saved outputs/result_summary.png")


if __name__ == "__main__":
    main()
'''
        shell = """#!/usr/bin/env bash
set -euo pipefail
python src/train.py --config configs/default.yaml --variant baseline
python src/train.py --config configs/default.yaml --variant proposed
python src/evaluate.py --config configs/default.yaml
python analysis/plot_results.py --input outputs/results.json
"""
        files = [
            {"path": "README.md", "language": "markdown", "purpose": "Project overview and run guide", "content": readme},
            {"path": "requirements.txt", "language": "text", "purpose": "Python dependencies", "content": requirements},
            {"path": "configs/default.yaml", "language": "yaml", "purpose": "Default experiment configuration", "content": config},
            {"path": "src/data.py", "language": "python", "purpose": "Dataset loading and mock data", "content": data_py},
            {"path": "src/model.py", "language": "python", "purpose": "Baseline and proposed models", "content": model_py},
            {"path": "src/train.py", "language": "python", "purpose": "Training entrypoint", "content": train_py},
            {"path": "src/evaluate.py", "language": "python", "purpose": "Evaluation entrypoint", "content": evaluate_py},
            {"path": "scripts/run_baseline.sh", "language": "shell", "purpose": "Baseline run command", "content": "#!/usr/bin/env bash\nset -euo pipefail\npython src/train.py --config configs/default.yaml --variant baseline\n"},
            {"path": "scripts/run_experiment.sh", "language": "shell", "purpose": "End-to-end experiment script", "content": shell},
            {"path": "analysis/plot_results.py", "language": "python", "purpose": "Result plotting", "content": plot_py},
        ]
        return {
            "name": project_name,
            "framework": framework or "pytorch",
            "summary": f"Structured experiment package for testing: {idea.title}",
            "setup": ["python -m venv .venv", "source .venv/bin/activate", "pip install -r requirements.txt"],
            "run_commands": [
                "python src/train.py --config configs/default.yaml --variant baseline",
                "python src/train.py --config configs/default.yaml --variant proposed",
                "python src/evaluate.py --config configs/default.yaml",
                "python analysis/plot_results.py --input outputs/results.json",
            ],
            "entrypoints": [
                {"name": "train baseline", "path": "src/train.py", "command": "python src/train.py --config configs/default.yaml --variant baseline", "purpose": "Train baseline model"},
                {"name": "train proposed", "path": "src/train.py", "command": "python src/train.py --config configs/default.yaml --variant proposed", "purpose": "Train proposed method"},
                {"name": "evaluate", "path": "src/evaluate.py", "command": "python src/evaluate.py --config configs/default.yaml", "purpose": "Compare outputs"},
            ],
            "safety_notes": [
                "Generated code is an artifact for review; inspect before running.",
                "Run inside an isolated environment and replace mock data with verified dataset paths.",
                "No code is executed automatically by this application.",
            ],
            "files": files,
        }

    @staticmethod
    def safe_code_project_path(value: Any) -> Optional[str]:
        path = str(value or "").strip().replace("\\", "/")
        path = re.sub(r"/+", "/", path)
        if not path or path.startswith("/") or path.startswith("~") or "\x00" in path:
            return None
        parts = [part for part in path.split("/") if part not in {"", "."}]
        if not parts or any(part == ".." for part in parts):
            return None
        safe_parts = []
        for part in parts:
            cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", part).strip()
            if not cleaned:
                return None
            safe_parts.append(cleaned[:80])
        return "/".join(safe_parts)[:240]

    @staticmethod
    def representative_code_from_project(project: dict[str, Any]) -> str:
        files = project.get("files") if isinstance(project, dict) else []
        preferred = ["src/train.py", "experiment.py", "main.py"]
        if isinstance(files, list):
            for path in preferred:
                for item in files:
                    if isinstance(item, dict) and item.get("path") == path:
                        return str(item.get("content") or "")
            for item in files:
                if isinstance(item, dict) and str(item.get("language") or "").lower() == "python":
                    return str(item.get("content") or "")
        return ""

    @classmethod
    def _normalize_entrypoints(cls, value: Any, files: list[dict[str, Any]], fallback: list[dict[str, Any]]) -> list[dict[str, str]]:
        file_paths = {item["path"] for item in files}
        entrypoints = []
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    continue
                path = cls.safe_code_project_path(item.get("path"))
                if not path or path not in file_paths:
                    continue
                command = str(item.get("command") or "").strip()[:400]
                if not command:
                    continue
                entrypoints.append({
                    "name": str(item.get("name") or path)[:120],
                    "path": path,
                    "command": command,
                    "purpose": str(item.get("purpose") or "")[:300],
                })
                if len(entrypoints) >= 8:
                    break
        return entrypoints or fallback[:3]

    @staticmethod
    def _safe_project_name(value: Any) -> str:
        text = str(value or "research-code-project").strip().lower()
        text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
        text = text.strip("-")
        return (text or "research-code-project")[:80]

    @staticmethod
    def _infer_code_language(path: str, value: Any = None) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip().lower()[:40]
        suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        return {
            "py": "python",
            "md": "markdown",
            "txt": "text",
            "yaml": "yaml",
            "yml": "yaml",
            "sh": "shell",
            "json": "json",
            "toml": "toml",
        }.get(suffix, "text")

    @staticmethod
    def _default_file_purpose(path: str) -> str:
        if path == "README.md":
            return "Project overview and run instructions"
        if path == "requirements.txt":
            return "Python dependencies"
        if path.endswith(".yaml") or path.endswith(".yml"):
            return "Experiment configuration"
        if path.startswith("src/"):
            return "Experiment source file"
        if path.startswith("scripts/"):
            return "Run script"
        if path.startswith("analysis/"):
            return "Analysis script"
        return "Generated project file"
