"""科研 Pipeline 服务 — Idea 生成、讨论、代码生成。"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.llm import llm_service
from app.services.rag_service import RAGService
from app.db.models.paper import Paper
from app.db.models.research import ResearchProject, ResearchIdea
from app.services.research_idea_workbench import ResearchIdeaWorkbenchService

logger = logging.getLogger(__name__)

COPILOT_MODES = {"mentor", "skeptic", "experiment_designer", "writer"}
COPILOT_MODE_PROMPTS = {
    "mentor": "你是资深研究导师，目标是帮助学生把 Proposal 细化成更清晰、可推进的研究方案。",
    "skeptic": "你是严格审稿人，优先攻击 novelty、证据缺口、可行性、实验设置和潜在撞车风险。",
    "experiment_designer": "你是实验设计专家，优先给出最小实验、强基线、指标、消融和失败判定。",
    "writer": "你是论文写作顾问，优先帮助整理贡献点、related work 角度、claim 边界和写作准备度。",
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
    ) -> str:
        """为 Idea 生成实验代码框架。"""
        prompt = f"""请为以下研究 Idea 生成 {framework} 实验代码框架。

## Idea: {idea.title}

{idea.description or ''}

## 要求
- 使用 {framework} 框架
- 包含完整的训练循环、数据加载、模型定义
- 添加详细的中文注释
- 代码应可直接运行（使用模拟数据如需要）
- 包含必要的 import 语句

请直接输出代码，不要其他解释。
"""

        try:
            code = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4096,
            )

            # 提取代码块
            if "```" in code:
                code_blocks = code.split("```")
                # 取第一个代码块
                for i, block in enumerate(code_blocks):
                    if block.startswith("python") or (i % 2 == 1 and not block.startswith("python")):
                        code = block.replace("python\n", "").strip()
                        break

            # 保存到数据库
            idea.generated_code = code
            idea.status = "implemented"
            await self.session.commit()

            return code
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            await self.session.rollback()
            raise
