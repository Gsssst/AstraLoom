"""写作项目管理服务 — 项目 CRUD、章节管理、模板系统、多格式导出。"""

import logging
import re
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# 预定义写作模板
TEMPLATES = {
    "blank": {
        "name": "空白模板",
        "description": "从零开始的空白论文",
        "sections": [],
    },
    "acl": {
        "name": "ACL",
        "description": "ACL/EMNLP/NAACL 会议论文模板",
        "sections": [
            {"title": "Abstract", "level": 1},
            {"title": "Introduction", "level": 1},
            {"title": "Related Work", "level": 1},
            {"title": "Method", "level": 1},
            {"title": "Experiments", "level": 1},
            {"title": "Conclusion", "level": 1},
        ],
    },
    "cvpr": {
        "name": "CVPR",
        "description": "CVPR/ICCV/ECCV 会议论文模板",
        "sections": [
            {"title": "Abstract", "level": 1},
            {"title": "Introduction", "level": 1},
            {"title": "Related Work", "level": 1},
            {"title": "Method", "level": 1},
            {"title": "Experiments", "level": 1},
            {"title": "Conclusion", "level": 1},
        ],
    },
    "neurips": {
        "name": "NeurIPS",
        "description": "NeurIPS/ICML/ICLR 会议论文模板",
        "sections": [
            {"title": "Abstract", "level": 1},
            {"title": "Introduction", "level": 1},
            {"title": "Related Work", "level": 1},
            {"title": "Preliminaries", "level": 1},
            {"title": "Method", "level": 1},
            {"title": "Experiments", "level": 1},
            {"title": "Conclusion", "level": 1},
        ],
    },
    "icml": {
        "name": "ICML",
        "sections": [
            {"title": "Abstract", "level": 1},
            {"title": "Introduction", "level": 1},
            {"title": "Background", "level": 1},
            {"title": "Proposed Method", "level": 1},
            {"title": "Theoretical Analysis", "level": 1},
            {"title": "Experiments", "level": 1},
            {"title": "Conclusion", "level": 1},
        ],
    },
    "nsfc": {
        "name": "NSFC 申请书",
        "description": "国家自然科学基金申请书模板",
        "sections": [
            {"title": "立项依据与研究内容", "level": 1},
            {"title": "研究目标", "level": 1},
            {"title": "研究内容", "level": 1},
            {"title": "拟采取的研究方案", "level": 1},
            {"title": "技术路线", "level": 1},
            {"title": "可行性分析", "level": 1},
            {"title": "特色与创新之处", "level": 1},
            {"title": "预期成果", "level": 1},
            {"title": "研究基础", "level": 1},
        ],
    },
    "survey": {
        "name": "综述草稿",
        "description": "从研究方向生成文献综述草稿",
        "sections": [
            {"title": "Abstract", "level": 1},
            {"title": "Introduction", "level": 1},
            {"title": "Related Work", "level": 1},
            {"title": "Related Work Comparison Table", "level": 1},
            {"title": "Research Gaps", "level": 1},
            {"title": "References", "level": 1},
        ],
    },
}


class WritingProjectService:
    """写作项目管理服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- 模板 ---

    @staticmethod
    def get_templates() -> list:
        """获取可用模板列表。"""
        return [
            {"key": k, "name": v["name"], "description": v.get("description", ""),
             "section_count": len(v["sections"])}
            for k, v in TEMPLATES.items()
        ]

    @staticmethod
    def get_template_sections(template_type: str) -> list:
        """获取模板的预设章节。"""
        template = TEMPLATES.get(template_type, TEMPLATES["blank"])
        return template["sections"]

    # --- 项目 CRUD ---

    async def create_project(self, user_id: str, title: str,
                              description: str = "",
                              template_type: str = "blank",
                              metadata_json: Optional[dict] = None) -> dict:
        """创建新写作项目。"""
        from app.db.models.writing import WritingProject, WritingSection

        project = WritingProject(
            user_id=user_id,
            title=title,
            description=description,
            template_type=template_type,
            metadata_json=metadata_json or {},
        )
        self.session.add(project)
        await self.session.flush()

        # 从模板创建预设章节
        template_sections = self.get_template_sections(template_type)
        for i, sec in enumerate(template_sections):
            section = WritingSection(
                project_id=str(project.id),
                title=sec["title"],
                order=i,
            )
            self.session.add(section)

        await self.session.commit()
        await self.session.refresh(project)

        return self._project_to_dict(project)

    async def create_review_draft_from_topic(
        self,
        user_id: str,
        topic: str,
        max_papers: int = 8,
        language: str = "chinese",
    ) -> dict:
        """从研究方向创建综述草稿项目。"""
        from app.services.writing_service import WritingAssistantService

        writing = WritingAssistantService(self.session)
        table = await writing.generate_related_work_table(topic, max_papers=max_papers)
        rows = table.get("rows", [])
        paper_ids = [row["paper_id"] for row in rows if row.get("paper_id")]

        metadata = {
            "source": "topic_review_draft",
            "source_topic": topic,
            "language": language,
            "recommended_paper_ids": paper_ids,
            "recommended_arxiv_ids": [],
            "related_work_table": table.get("markdown", ""),
            "evidence_status": "sufficient" if rows else "insufficient",
        }
        project = await self.create_project(
            user_id=user_id,
            title=f"{topic} 综述草稿",
            description=f"由研究方向「{topic}」自动生成的综述初稿，基于本地论文库检索结果。",
            template_type="survey",
            metadata_json=metadata,
        )

        sections_by_title = {section["title"]: section for section in project.get("sections", [])}
        content_by_title = self._build_review_draft_sections(topic, rows, table)
        for title, content in content_by_title.items():
            section = sections_by_title.get(title)
            if section:
                await self.update_section(
                    section["id"],
                    user_id,
                    content=content,
                    status="draft",
                )

        updated = await self.get_project(project["id"], user_id)
        return {
            "project": updated,
            "related_work_table": table,
            "evidence_status": metadata["evidence_status"],
        }

    async def create_review_draft_from_research_idea(
        self,
        user_id: str,
        research_project,
        idea,
    ) -> dict:
        """从证据驱动 Research Idea 创建写作草稿。"""
        evidence_items = list((idea.evidence_json or {}).get("items") or [])
        local_paper_ids = self._extract_local_paper_ids(evidence_items)
        metadata = {
            "source": "research_idea",
            "source_project_id": str(research_project.id),
            "source_project_name": research_project.name,
            "source_idea_id": str(idea.id),
            "source_idea_title": idea.title,
            "recommended_paper_ids": local_paper_ids,
            "recommended_arxiv_ids": [
                item.get("arxiv_id") for item in evidence_items if item.get("arxiv_id")
            ],
            "evidence_items": evidence_items,
            "evidence_status": "sufficient" if local_paper_ids or evidence_items else "insufficient",
        }
        project = await self.create_project(
            user_id=user_id,
            title=f"{idea.title} 写作草稿",
            description=f"由研究方向「{research_project.name}」中的 Proposal 自动创建。",
            template_type="survey",
            metadata_json=metadata,
        )

        sections_by_title = {section["title"]: section for section in project.get("sections", [])}
        content_by_title = self._build_research_idea_draft_sections(research_project, idea, evidence_items)
        for title, content in content_by_title.items():
            section = sections_by_title.get(title)
            if section:
                await self.update_section(
                    section["id"],
                    user_id,
                    content=content,
                    status="draft",
                )

        updated = await self.get_project(project["id"], user_id)
        return {
            "project": updated,
            "evidence_status": metadata["evidence_status"],
            "evidence_count": len(evidence_items),
            "local_paper_count": len(local_paper_ids),
        }

    def _extract_local_paper_ids(self, evidence_items: list[dict]) -> list[str]:
        ids: list[str] = []
        for item in evidence_items:
            candidate = item.get("imported_paper_id") or item.get("paper_id")
            if candidate and self._looks_like_uuid(str(candidate)) and str(candidate) not in ids:
                ids.append(str(candidate))
        return ids

    def _looks_like_uuid(self, value: str) -> bool:
        return bool(re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", value or ""))

    def _build_research_idea_draft_sections(self, research_project, idea, evidence_items: list[dict]) -> dict:
        evidence_table = self._build_evidence_markdown_table(evidence_items)
        references = self._build_evidence_references(evidence_items)
        if not evidence_items:
            evidence_note = "当前 Proposal 暂无可用证据论文。请先运行 Idea 工作台或导入外部证据，再继续完善 Related Work。"
        else:
            evidence_note = f"当前草稿继承了 {len(evidence_items)} 条 Proposal 证据，其中本地论文可用于后续 BibTeX 导出。"

        review = idea.review_json or {}
        plan = idea.experiment_plan or {}
        scores = review.get("scores") or {}
        score_text = "、".join(f"{key}: {value}/10" for key, value in scores.items()) or "暂无六维评分"
        baselines = "、".join(plan.get("baselines") or []) or "待补充"
        metrics = "、".join(plan.get("metrics") or []) or "待补充"
        steps = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(plan.get("steps") or [])) or "待补充最小实验步骤。"

        related_work = (
            f"{evidence_note}\n\n"
            "下面的证据表按 Proposal 生成时的证据角色保留，写作时建议逐条确认其是否能够支撑对应论断。\n\n"
            f"{evidence_table}"
        )
        return {
            "Abstract": (
                f"本文围绕「{research_project.name}」中的 Proposal「{idea.title}」展开写作。"
                f"核心假设是：{idea.hypothesis or '待补充可证伪假设'}。"
                "当前草稿将 Proposal 的证据、方法定位和最小实验计划转换为可编辑写作结构。"
            ),
            "Introduction": (
                f"研究方向：{research_project.name}\n\n"
                f"{research_project.description or '暂无研究方向描述。'}\n\n"
                f"Proposal 描述：{idea.description or '暂无描述。'}\n\n"
                f"技术草图：{idea.approach or '待补充技术路线。'}"
            ),
            "Related Work": related_work,
            "Related Work Comparison Table": evidence_table,
            "Research Gaps": (
                f"创新点：{idea.novelty or '待补充'}\n\n"
                f"评审理由：{review.get('rationale') or '暂无评审理由'}\n\n"
                f"主要不确定性：{review.get('uncertainty') or '暂无'}\n\n"
                f"六维评分：{score_text}\n\n"
                f"最小实验数据集：{plan.get('dataset') or '待补充'}\n\n"
                f"基线方法：{baselines}\n\n"
                f"评测指标：{metrics}\n\n"
                f"实验步骤：\n{steps}"
            ),
            "References": references or "暂无引用。建议先导入或补全文证据论文。",
        }

    def _build_evidence_markdown_table(self, evidence_items: list[dict]) -> str:
        header = "| # | 证据论文 | 年份 | 角色 | 相关性 | 可用信息 |\n|---|---|---:|---|---:|---|"
        if not evidence_items:
            return f"{header}\n| - | 暂无证据 | - | - | - | 建议先运行 Idea 工作台或导入论文 |"
        rows = []
        for index, item in enumerate(evidence_items, start=1):
            title = self._escape_table_cell(item.get("title") or "Untitled")
            year = item.get("year") or "N/A"
            category = item.get("category") or "evidence"
            score = item.get("score")
            score_text = f"{float(score):.2f}" if isinstance(score, (int, float)) else "N/A"
            info = item.get("relevance") or item.get("abstract_excerpt") or item.get("source") or "待补充摘要/全文"
            rows.append(f"| {index} | {title} | {year} | {category} | {score_text} | {self._escape_table_cell(str(info)[:180])} |")
        return f"{header}\n" + "\n".join(rows)

    def _build_evidence_references(self, evidence_items: list[dict]) -> str:
        refs = []
        for index, item in enumerate(evidence_items, start=1):
            identifiers = []
            local_id = item.get("imported_paper_id") or item.get("paper_id")
            if local_id and self._looks_like_uuid(str(local_id)):
                identifiers.append(f"Paper ID: {local_id}")
            if item.get("arxiv_id"):
                identifiers.append(f"arXiv: {item['arxiv_id']}")
            if item.get("doi"):
                identifiers.append(f"DOI: {item['doi']}")
            suffix = f" ({'; '.join(identifiers)})" if identifiers else ""
            refs.append(f"[{index}] {item.get('title') or 'Untitled evidence'}{suffix}")
        return "\n".join(refs)

    def _escape_table_cell(self, value: str) -> str:
        return (value or "").replace("\n", " ").replace("|", "\\|")

    def _build_review_draft_sections(self, topic: str, rows: list[dict], table: dict) -> dict:
        if not rows:
            insufficient = (
                f"当前本地知识库暂未检索到与「{topic}」足够相关的论文。\n\n"
                "建议先在论文库中检索外部论文并入库，随后补全文与向量，再重新生成综述草稿。"
            )
            return {
                "Abstract": insufficient,
                "Introduction": insufficient,
                "Related Work": insufficient,
                "Related Work Comparison Table": table.get("markdown", ""),
                "Research Gaps": "证据不足，暂不生成研究空白判断。",
                "References": "暂无可引用论文。",
            }

        citations = ", ".join(f"[{row['index']}]" for row in rows[:5])
        top_titles = "、".join(row["title"] for row in rows[:3])
        related_lines = [
            f"- [{row['index']}] **{row['title']}** ({row.get('year') or 'N/A'}): {row.get('contribution', '')} 该工作可作为「{row.get('role_label')}」使用，{row.get('comparison_point', '')}"
            for row in rows
        ]
        gap_lines = [
            "- 若多篇论文集中在相同数据集或设定上，后续综述需要补充跨数据集、跨场景或真实应用中的证据。",
            "- 对摘要信息不足的论文，建议补全文后再判断其方法细节、实验指标和局限性。",
            "- 写作定稿前应逐句检查引用是否能支撑对应结论，避免只凭题名或摘要推测。",
        ]
        refs = [
            f"[{row['index']}] {row['title']} ({row.get('year') or 'N/A'}). Paper ID: {row['paper_id']}"
            for row in rows
        ]
        return {
            "Abstract": (
                f"本文围绕「{topic}」进行文献综述，初步整理了本地知识库中 {len(rows)} 篇相关论文。"
                f"草稿重点关注代表性工作（如 {top_titles}）之间的方法差异、证据角色和可对比点。"
                "当前版本适合作为写作起点，定稿前仍需结合全文证据补充更细粒度的实验和局限分析。"
            ),
            "Introduction": (
                f"「{topic}」是当前研究中值得系统梳理的方向。已有工作从不同方法路线、实验设置和应用场景展开探索，"
                f"其中 {citations} 可作为初步参考。为了避免简单罗列论文，本文将相关工作按贡献、证据角色和可对比点组织，"
                "并在后续章节进一步讨论仍需补足的研究空白。"
            ),
            "Related Work": "\n".join(related_lines),
            "Related Work Comparison Table": table.get("markdown", ""),
            "Research Gaps": "\n".join(gap_lines),
            "References": "\n".join(refs),
        }

    async def list_projects(self, user_id: str) -> list:
        """列出用户的所有项目。"""
        from app.db.models.writing import WritingProject, WritingSection
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(WritingProject)
            .where(WritingProject.user_id == user_id)
            .options(selectinload(WritingProject.sections))
            .order_by(WritingProject.updated_at.desc())
        )
        projects = result.scalars().all()
        return [self._project_to_dict(p) for p in projects]

    async def get_project(self, project_id: str, user_id: str) -> dict | None:
        """获取项目详情。"""
        from app.db.models.writing import WritingProject
        from sqlalchemy.orm import selectinload
        from app.services.workspace_service import WorkspaceService

        try:
            pid = UUID(project_id)
        except ValueError:
            return None

        result = await self.session.execute(
            select(WritingProject)
            .where(WritingProject.id == pid)
            .options(selectinload(WritingProject.sections))
        )
        project = result.scalar_one_or_none()
        if not project:
            return None
        if str(project.user_id) != str(user_id):
            role = await WorkspaceService(self.session).resource_role_for_user(user_id, "writing_projects", str(project.id))
            if not WorkspaceService(self.session).role_can_read_resource(role):
                return None
            data = self._project_to_dict(project)
            data["workspace_access_role"] = role
            return data
        return self._project_to_dict(project)

    async def update_project(self, project_id: str, user_id: str,
                              **kwargs) -> dict | None:
        """更新项目。"""
        from app.db.models.writing import WritingProject
        from app.services.workspace_service import WorkspaceService

        try:
            pid = UUID(project_id)
        except ValueError:
            return None

        result = await self.session.execute(
            select(WritingProject)
            .where(WritingProject.id == pid)
        )
        project = result.scalar_one_or_none()
        if not project:
            return None
        if str(project.user_id) != str(user_id):
            workspace = WorkspaceService(self.session)
            role = await workspace.resource_role_for_user(user_id, "writing_projects", str(project.id))
            if not workspace.role_can_edit_resource(role):
                return None

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        await self.session.commit()
        await self.session.refresh(project)
        return self._project_to_dict(project)

    async def bind_submission_profile(
        self,
        project_id: str,
        user_id: str,
        venue: str,
        year: str,
        template_inspection: dict,
    ) -> dict | None:
        """Bind target venue/year and inspected template metadata to a writing project."""
        project = await self.get_project(project_id, user_id)
        if not project:
            return None
        metadata = dict(project.get("metadata_json") or {})
        inspection = dict(template_inspection or {})
        profile = {
            "venue": (venue or "").strip(),
            "year": (year or "").strip(),
            "template_source": inspection.get("source_filename") or "",
            "template_status": inspection.get("status") or "needs_review",
            "status_label": inspection.get("status_label") or "需要人工确认",
            "document_class": inspection.get("document_class") or "",
            "main_tex": inspection.get("main_tex") or "",
            "class_files": inspection.get("class_files") or [],
            "style_files": inspection.get("style_files") or [],
            "packages": inspection.get("packages") or [],
            "venue_hints": inspection.get("venue_hints") or [],
            "warnings": inspection.get("warnings") or [],
        }
        if not profile["venue"] and profile["venue_hints"]:
            profile["venue"] = profile["venue_hints"][0]
        if not profile["venue"]:
            profile["warnings"] = [*profile["warnings"], "尚未填写目标会议/期刊。"]
        metadata["submission_profile"] = profile
        return await self.update_project(project_id, user_id, metadata_json=metadata)

    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """删除项目。"""
        from app.db.models.writing import WritingProject

        try:
            pid = UUID(project_id)
        except ValueError:
            return False

        result = await self.session.execute(
            select(WritingProject)
            .where(WritingProject.id == pid, WritingProject.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            return False

        await self.session.delete(project)
        await self.session.commit()
        return True

    # --- 章节管理 ---

    async def update_section(self, section_id: str, user_id: str,
                              **kwargs) -> dict | None:
        """更新章节内容/状态/标题。"""
        from app.db.models.writing import WritingSection, WritingProject
        from app.services.workspace_service import WorkspaceService

        try:
            sid = UUID(section_id)
        except ValueError:
            return None

        result = await self.session.execute(
            select(WritingSection)
            .join(WritingProject, WritingSection.project_id == WritingProject.id)
            .where(WritingSection.id == sid)
        )
        section = result.scalar_one_or_none()
        if not section:
            return None
        project_result = await self.session.execute(select(WritingProject).where(WritingProject.id == section.project_id))
        project = project_result.scalar_one_or_none()
        if not project:
            return None
        if str(project.user_id) != str(user_id):
            workspace = WorkspaceService(self.session)
            role = await workspace.resource_role_for_user(user_id, "writing_projects", str(project.id))
            if not workspace.role_can_edit_resource(role):
                return None

        for key, value in kwargs.items():
            if hasattr(section, key):
                setattr(section, key, value)

        # 自动计算字数
        if "content" in kwargs:
            section.word_count = len(kwargs["content"])

        await self.session.commit()
        await self.session.refresh(section)
        return self._section_to_dict(section)

    async def reorder_sections(self, project_id: str, user_id: str,
                                section_ids: List[str]) -> bool:
        """重排章节顺序。"""
        from app.db.models.writing import WritingProject, WritingSection
        from app.services.workspace_service import WorkspaceService

        try:
            pid = UUID(project_id)
        except ValueError:
            return False

        result = await self.session.execute(select(WritingProject).where(WritingProject.id == pid))
        project = result.scalar_one_or_none()
        if not project:
            return False
        if str(project.user_id) != str(user_id):
            workspace = WorkspaceService(self.session)
            role = await workspace.resource_role_for_user(user_id, "writing_projects", str(project.id))
            if not workspace.role_can_edit_resource(role):
                return False

        for i, sid in enumerate(section_ids):
            try:
                await self.session.execute(
                    update(WritingSection)
                    .where(WritingSection.id == UUID(sid), WritingSection.project_id == str(pid))
                    .values(order=i)
                )
            except (ValueError, Exception):
                continue

        await self.session.commit()
        return True

    # --- 证据卡片与引用校验 ---

    async def get_evidence_cards(self, project_id: str, user_id: str) -> dict | None:
        """获取写作项目关联证据卡片。"""
        from app.db.models.paper import Paper

        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        metadata = project.get("metadata_json") or {}
        evidence_items = list(metadata.get("evidence_items") or [])
        recommended_ids = list(dict.fromkeys(metadata.get("recommended_paper_ids") or []))
        recommended_arxiv_ids = list(dict.fromkeys(metadata.get("recommended_arxiv_ids") or []))

        local_ids = list(recommended_ids)
        for item in evidence_items:
            candidate = item.get("imported_paper_id") or item.get("paper_id")
            if candidate and self._looks_like_uuid(str(candidate)) and str(candidate) not in local_ids:
                local_ids.append(str(candidate))

        local_papers: dict[str, Paper] = {}
        for paper_id in local_ids:
            try:
                result = await self.session.execute(select(Paper).where(Paper.id == UUID(paper_id)))
                paper = result.scalar_one_or_none()
                if paper:
                    local_papers[str(paper.id)] = paper
            except ValueError:
                continue

        cards: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in evidence_items:
            local_id = item.get("imported_paper_id") or item.get("paper_id")
            paper = local_papers.get(str(local_id)) if local_id else None
            card = self._evidence_item_to_card(item, paper, len(cards) + 1)
            key = self._evidence_card_key(card)
            if key not in seen:
                seen.add(key)
                cards.append(card)

        if not evidence_items:
            for paper_id in recommended_ids:
                paper = local_papers.get(str(paper_id))
                if not paper:
                    continue
                card = self._paper_to_evidence_card(paper, len(cards) + 1)
                key = self._evidence_card_key(card)
                if key not in seen:
                    seen.add(key)
                    cards.append(card)

        for arxiv_id in recommended_arxiv_ids:
            if not arxiv_id:
                continue
            normalized = self._normalize_arxiv_id(str(arxiv_id))
            if any(self._normalize_arxiv_id(card.get("arxiv_id") or "") == normalized for card in cards):
                continue
            card = {
                "id": f"arxiv:{normalized}",
                "index": len(cards) + 1,
                "citation_marker": f"[{len(cards) + 1}]",
                "title": f"arXiv:{arxiv_id}",
                "year": None,
                "authors": "",
                "source": "external",
                "source_label": "外部 arXiv",
                "source_kind": "external",
                "paper_id": None,
                "external_paper_id": None,
                "arxiv_id": arxiv_id,
                "doi": None,
                "role": "supporting_evidence",
                "role_label": "支持证据",
                "snippet": "该论文尚未导入本地论文库，无法进行引用支撑强度校验。",
                "local_status": "external",
                "local_status_label": "未入库",
                "bibtex_ready": False,
            }
            seen.add(self._evidence_card_key(card))
            cards.append(card)

        coverage = {
            "total": len(cards),
            "local": sum(1 for card in cards if card["local_status"] == "local"),
            "external": sum(1 for card in cards if card["local_status"] == "external"),
            "bibtex_ready": sum(1 for card in cards if card.get("bibtex_ready")),
        }
        return {
            "project_id": project["id"],
            "source": metadata.get("source") or "manual",
            "evidence_status": metadata.get("evidence_status") or ("sufficient" if cards else "insufficient"),
            "coverage": coverage,
            "cards": cards,
        }

    async def check_section_citations(
        self,
        project_id: str,
        user_id: str,
        text: str,
        section_id: Optional[str] = None,
    ) -> dict | None:
        """检查章节中的引用是否能被项目证据支撑。"""
        from app.db.models.paper import Paper
        from app.services.writing_service import WritingAssistantService

        evidence = await self.get_evidence_cards(project_id, user_id)
        if not evidence:
            return None

        cards = evidence.get("cards") or []
        citations = self._extract_citation_mentions(text or "")
        checks: list[dict[str, Any]] = []
        writer = WritingAssistantService(self.session)

        if not citations:
            return {
                "project_id": project_id,
                "section_id": section_id,
                "checks": [{
                    "citation": None,
                    "status": "missing",
                    "label": "缺少引用",
                    "sentence": (text or "").strip()[:240],
                    "explanation": "该章节没有检测到 [1]、arXiv 或 Paper ID 引用标记。建议为关键结论补充证据引用。",
                    "card": None,
                }],
                "summary": self._citation_summary([{"status": "missing"}]),
                "recommendations": self._recommend_evidence_cards(cards),
            }

        for mention in citations:
            card = self._resolve_citation_card(mention, cards)
            sentence = self._citation_context(text or "", mention["start"], mention["end"])
            if not card:
                checks.append({
                    "citation": mention["raw"],
                    "status": "missing",
                    "label": "未找到证据卡",
                    "sentence": sentence,
                    "explanation": "该引用没有匹配到当前写作项目的证据卡，请检查编号或补充 References。",
                    "card": None,
                })
                continue

            if card.get("local_status") == "unknown":
                checks.append({
                    "citation": mention["raw"],
                    "status": "missing",
                    "label": "本地记录缺失",
                    "sentence": sentence,
                    "explanation": "证据卡保存了本地论文 ID，但当前数据库没有找到该论文。建议重新入库或替换引用。",
                    "card": card,
                })
                continue

            if card.get("local_status") != "local" or not card.get("paper_id"):
                checks.append({
                    "citation": mention["raw"],
                    "status": "unchecked",
                    "label": "外部证据未校验",
                    "sentence": sentence,
                    "explanation": "该证据尚未导入本地论文库，系统无法判断它是否支撑当前句子。建议先一键入库并补全文/补向量。",
                    "card": card,
                })
                continue

            try:
                result = await self.session.execute(select(Paper).where(Paper.id == UUID(card["paper_id"])))
                paper = result.scalar_one_or_none()
            except ValueError:
                paper = None

            if not paper:
                checks.append({
                    "citation": mention["raw"],
                    "status": "missing",
                    "label": "本地论文缺失",
                    "sentence": sentence,
                    "explanation": "证据卡记录了本地论文 ID，但当前数据库没有找到该论文。",
                    "card": card,
                })
                continue

            match = writer.score_sentence_paper_match(sentence, paper)
            role = writer.classify_citation_role(sentence, paper)
            checks.append({
                "citation": mention["raw"],
                "status": match["match_status"],
                "label": match["match_label"],
                "sentence": sentence,
                "explanation": match["match_explanation"],
                "match_score": match["match_score"],
                "match_terms": match["match_terms"],
                "role": role["role"],
                "role_label": role["role_label"],
                "card": card,
            })

        return {
            "project_id": project_id,
            "section_id": section_id,
            "checks": checks,
            "summary": self._citation_summary(checks),
            "recommendations": self._recommend_evidence_cards(cards),
        }

    async def build_evidence_related_work_table(self, project_id: str, user_id: str) -> dict | None:
        """基于写作项目证据卡生成 Related Work 对比表。"""
        evidence = await self.get_evidence_cards(project_id, user_id)
        if not evidence:
            return None

        cards = evidence.get("cards") or []
        coverage = evidence.get("coverage") or {}
        header = (
            "| 引用 | 论文 | 年份 | 证据角色 | 状态 | 标识符 | 写作使用建议 |\n"
            "|---|---|---:|---|---|---|---|"
        )
        rows = []
        for card in cards:
            identifiers = []
            if card.get("arxiv_id"):
                identifiers.append(f"arXiv:{card['arxiv_id']}")
            if card.get("doi"):
                identifiers.append(f"DOI:{card['doi']}")
            if card.get("paper_id"):
                identifiers.append(f"Paper ID:{card['paper_id']}")
            rows.append(
                "| {marker} | {title} | {year} | {role} | {status} | {ids} | {use} |".format(
                    marker=self._escape_table_cell(card.get("citation_marker") or ""),
                    title=self._escape_table_cell(card.get("title") or "Untitled"),
                    year=card.get("year") or "N/A",
                    role=self._escape_table_cell(card.get("role_label") or "支持证据"),
                    status=self._escape_table_cell(card.get("local_status_label") or "未知"),
                    ids=self._escape_table_cell("；".join(identifiers) or "待补充"),
                    use=self._escape_table_cell(self._evidence_writing_use(card)),
                )
            )

        if not rows:
            rows.append("| - | 暂无证据 | - | - | 证据不足 | - | 请先从论文库入库或从研究方向生成证据。 |")

        warnings = []
        total = coverage.get("total") or len(cards)
        local = coverage.get("local") or 0
        external = coverage.get("external") or 0
        if total == 0:
            warnings.append("当前项目没有证据卡，无法生成可信 Related Work 对比表。")
        if total and local / total < 0.5:
            warnings.append("本地入库证据覆盖率偏低，表格中外部证据尚未经过全文/向量校验。")
        if external:
            warnings.append(f"有 {external} 条外部证据尚未入库，建议入库后再用于最终定稿。")

        markdown = "\n".join([
            "### Evidence-backed Related Work Comparison",
            "",
            header,
            *rows,
        ])
        if warnings:
            markdown += "\n\n> 证据提示：" + " ".join(warnings)

        return {
            "project_id": project_id,
            "markdown": markdown,
            "coverage": {
                "total": total,
                "local": local,
                "external": external,
                "bibtex_ready": coverage.get("bibtex_ready") or 0,
            },
            "warnings": warnings,
            "status": "weak_evidence" if warnings else "ready",
        }

    # --- 导出 ---

    async def export_to_markdown(self, project_id: str, user_id: str) -> str | None:
        """导出为 Markdown。"""
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        lines = [f"# {project['title']}", "", f"*{project.get('description', '')}*", ""]
        for sec in project.get("sections", []):
            lines.append(f"## {sec['title']}")
            lines.append("")
            lines.append(sec.get("content", "") or "*（待撰写）*")
            lines.append("")

        return "\n".join(lines)

    async def export_to_latex(self, project_id: str, user_id: str) -> str | None:
        """导出为 LaTeX。"""
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        from app.services.latex_processor import latex_processor
        return latex_processor.render_to_tex(
            project["title"],
            project.get("sections", []),
            template="article",
        )

    async def export_to_docx_bytes(self, project_id: str, user_id: str):
        """导出为 Word (.docx) bytes。"""
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        from docx import Document
        from docx.shared import Pt
        import io

        doc = Document()
        style = doc.styles['Normal']
        style.font.name = 'Arial'
        style.font.size = Pt(11)

        doc.add_heading(project["title"], level=0)
        if project.get("description"):
            doc.add_paragraph(project["description"])

        for sec in project.get("sections", []):
            doc.add_heading(sec["title"], level=1)
            content = sec.get("content", "") or "（待撰写）"
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    doc.add_paragraph(line[2:], style='List Bullet')
                elif line:
                    doc.add_paragraph(line)

        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        return file_stream

    async def export_to_bibtex(self, project_id: str, user_id: str) -> str | None:
        """导出写作项目关联论文的 BibTeX。"""
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        from app.services.writing_service import WritingAssistantService

        papers = await self._collect_reference_papers(project)
        writer = WritingAssistantService(self.session)
        return "\n\n".join(writer._generate_bibtex(paper) for paper in papers)

    async def export_reference_list(self, project_id: str, user_id: str, style: str = "numeric") -> str | None:
        """导出可读参考文献列表。"""
        project = await self.get_project(project_id, user_id)
        if not project:
            return None
        papers = await self._collect_reference_papers(project)
        if not papers:
            return "暂无可导出的参考文献。请先在写作项目中关联证据论文或补充 References。"
        return self._format_reference_list(papers, style=style)

    async def build_export_readiness(self, project_id: str, user_id: str) -> dict | None:
        """生成投稿导出预检结果。"""
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        sections = project.get("sections") or []
        empty_sections = []
        short_sections = []
        citation_mentions = []
        unmatched_citations = []
        total_words = 0

        evidence = await self.get_evidence_cards(project_id, user_id)
        cards = (evidence or {}).get("cards") or []
        coverage = (evidence or {}).get("coverage") or {
            "total": 0, "local": 0, "external": 0, "bibtex_ready": 0,
        }
        metadata = project.get("metadata_json") or {}
        submission_profile = metadata.get("submission_profile") or {}

        for section in sections:
            title = section.get("title") or "Untitled"
            content = section.get("content") or ""
            word_count = self._count_words(content)
            total_words += word_count
            if not content.strip():
                empty_sections.append(title)
            elif word_count < 80 and title.lower() not in {"references", "related work comparison table"}:
                short_sections.append(title)
            for mention in self._extract_citation_mentions(content):
                citation_mentions.append({**mention, "section": title})
                if not self._resolve_citation_card(mention, cards):
                    unmatched_citations.append({"citation": mention["raw"], "section": title})

        papers = await self._collect_reference_papers(project)
        warnings = []
        if empty_sections:
            warnings.append(f"有 {len(empty_sections)} 个章节为空：{', '.join(empty_sections[:4])}")
        if short_sections:
            warnings.append(f"有 {len(short_sections)} 个章节内容偏短：{', '.join(short_sections[:4])}")
        if coverage.get("total", 0) == 0:
            warnings.append("项目没有证据卡，导出内容缺少可追溯论文支撑。")
        elif coverage.get("local", 0) < max(1, int(coverage.get("total", 0) * 0.5)):
            warnings.append("本地入库证据覆盖率偏低，建议先补全文/补向量后再定稿。")
        if coverage.get("total", 0) and coverage.get("bibtex_ready", 0) < coverage.get("total", 0):
            warnings.append("部分证据缺少可导出的 BibTeX，本次参考文献可能不完整。")
        if unmatched_citations:
            warnings.append(f"有 {len(unmatched_citations)} 个正文引用未匹配到证据卡。")
        if citation_mentions and not papers:
            warnings.append("正文已有引用标记，但没有解析到真实论文条目。")
        if not submission_profile:
            warnings.append("尚未绑定官方投稿模板；内置结构模板不能保证当前年度会议格式。")
        elif submission_profile.get("warnings"):
            warnings.append("投稿模板需要人工确认：" + " ".join(submission_profile.get("warnings", [])[:3]))

        status = "ready"
        if empty_sections:
            status = "incomplete"
        elif warnings:
            status = "needs_attention"

        return {
            "project_id": project_id,
            "status": status,
            "status_label": {
                "ready": "可导出",
                "needs_attention": "建议检查",
                "incomplete": "内容未完成",
            }[status],
            "warnings": warnings,
            "section_summary": {
                "total": len(sections),
                "empty": len(empty_sections),
                "short": len(short_sections),
                "total_words": total_words,
                "empty_sections": empty_sections,
                "short_sections": short_sections,
            },
            "evidence_coverage": coverage,
            "citation_summary": {
                "mentions": len(citation_mentions),
                "unmatched": len(unmatched_citations),
                "unmatched_items": unmatched_citations[:8],
            },
            "reference_summary": {
                "papers": len(papers),
                "bibtex_ready": coverage.get("bibtex_ready", 0),
            },
            "submission_profile": submission_profile or {
                "template_status": "missing",
                "status_label": "未绑定官方模板",
                "warnings": ["尚未上传或绑定官方投稿模板。"],
            },
        }

    async def build_publication_package(self, project_id: str, user_id: str) -> dict | None:
        """导出投稿包：正文、引用和导出预检信息。"""
        project = await self.get_project(project_id, user_id)
        if not project:
            return None
        markdown = await self.export_to_markdown(project_id, user_id) or ""
        latex = await self.export_to_latex(project_id, user_id) or ""
        bibtex = await self.export_to_bibtex(project_id, user_id) or ""
        references = await self.export_reference_list(project_id, user_id) or ""
        readiness = await self.build_export_readiness(project_id, user_id)
        base = self._safe_export_basename(project.get("title") or "writing-project")
        return {
            "project_id": project_id,
            "title": project.get("title") or "",
            "readiness": readiness,
            "formats": {
                "markdown": {"filename": f"{base}.md", "content": markdown},
                "latex": {"filename": f"{base}.tex", "content": latex},
                "bibtex": {"filename": f"{base}.bib", "content": bibtex},
                "references": {"filename": f"{base}_references.md", "content": references},
                "docx": {"filename": f"{base}.docx", "download_url": f"/api/writing/projects/{project_id}/export?format=docx"},
            },
        }

    # --- 进度统计 ---

    def _calc_progress(self, sections: list) -> dict:
        """计算项目进度统计。"""
        total = len(sections)
        if total == 0:
            return {"percentage": 100, "completed": 0, "total": 0}

        completed = sum(1 for s in sections if s.status == "complete")
        return {
            "percentage": round(completed / total * 100),
            "completed": completed,
            "total": total,
            "total_words": sum(s.word_count or 0 for s in sections),
        }

    async def _collect_reference_papers(self, project: dict) -> list:
        """从项目元数据和 References 章节解析真实论文。"""
        from app.db.models.paper import Paper

        metadata = project.get("metadata_json") or {}
        paper_ids = list(dict.fromkeys(str(item) for item in (metadata.get("recommended_paper_ids") or []) if item))
        arxiv_ids = list(dict.fromkeys(str(item) for item in (metadata.get("recommended_arxiv_ids") or []) if item))
        dois = []

        references = "\n".join(
            section.get("content") or ""
            for section in project.get("sections", [])
            if section.get("title", "").lower() == "references"
        )
        for match in re.findall(r"Paper ID:\s*([0-9a-fA-F-]{32,36})", references):
            if match not in paper_ids:
                paper_ids.append(match)
        for match in re.findall(r"arXiv[:\s]+([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", references, flags=re.I):
            if match not in arxiv_ids:
                arxiv_ids.append(match)
        for match in re.findall(r"DOI[:\s]+([^\s,;]+)", references, flags=re.I):
            doi = match.strip().rstrip(".")
            if doi and doi not in dois:
                dois.append(doi)

        papers = []
        seen = set()
        for pid in paper_ids:
            try:
                result = await self.session.execute(select(Paper).where(Paper.id == UUID(pid)))
                paper = result.scalar_one_or_none()
                if paper and str(paper.id) not in seen:
                    papers.append(paper)
                    seen.add(str(paper.id))
            except ValueError:
                continue

        for arxiv_id in arxiv_ids:
            result = await self.session.execute(select(Paper).where(Paper.arxiv_id == arxiv_id))
            paper = result.scalar_one_or_none()
            if paper and str(paper.id) not in seen:
                papers.append(paper)
                seen.add(str(paper.id))

        for doi in dois:
            result = await self.session.execute(select(Paper).where(Paper.doi == doi))
            paper = result.scalar_one_or_none()
            if paper and str(paper.id) not in seen:
                papers.append(paper)
                seen.add(str(paper.id))

        return papers

    def _format_reference_list(self, papers: list, style: str = "numeric") -> str:
        rows = []
        for index, paper in enumerate(papers, 1):
            prefix = f"[{index}] " if style == "numeric" else ""
            authors = self._format_authors(getattr(paper, "authors", None))
            year = getattr(paper, "year", None) or "n.d."
            ids = []
            if getattr(paper, "arxiv_id", None):
                ids.append(f"arXiv:{paper.arxiv_id}")
            if getattr(paper, "doi", None):
                ids.append(f"DOI:{paper.doi}")
            suffix = f" {'; '.join(ids)}." if ids else ""
            rows.append(f"{prefix}{authors} ({year}). {paper.title}.{suffix}")
        return "\n\n".join(rows)

    def _format_authors(self, authors) -> str:
        if isinstance(authors, list):
            values = [str(item) for item in authors if item]
        elif isinstance(authors, dict):
            raw = authors.get("names") or authors.get("authors") or authors.get("list") or []
            values = [str(item) for item in raw] if isinstance(raw, list) else [str(raw)]
        elif isinstance(authors, str):
            values = [authors]
        else:
            values = []
        return ", ".join(values[:6]) or "Unknown Authors"

    def _count_words(self, text: str) -> int:
        ascii_words = re.findall(r"[A-Za-z0-9_]+", text or "")
        cjk_chars = re.findall(r"[\u4e00-\u9fff]", text or "")
        return len(ascii_words) + len(cjk_chars)

    def _safe_export_basename(self, title: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", title.strip()).strip("_")
        return (safe or "writing_project")[:80]

    # --- Helper ---

    def _project_to_dict(self, project) -> dict:
        sections = sorted(
            [self._section_to_dict(s) for s in (project.sections or [])],
            key=lambda s: s["order"],
        )
        return {
            "id": str(project.id),
            "title": project.title,
            "description": project.description,
            "template_type": project.template_type,
            "status": project.status,
            "metadata_json": project.metadata_json or {},
            "sections": sections,
            "progress": self._calc_progress(project.sections or []),
            "created_at": project.created_at.isoformat() if project.created_at else "",
            "updated_at": project.updated_at.isoformat() if project.updated_at else "",
        }

    def _section_to_dict(self, section) -> dict:
        return {
            "id": str(section.id),
            "title": section.title,
            "content": section.content,
            "order": section.order,
            "status": section.status,
            "word_count": section.word_count or 0,
        }

    def _evidence_item_to_card(self, item: dict, paper, index: int) -> dict:
        local_id = item.get("imported_paper_id") or item.get("paper_id")
        has_local_id = bool(local_id and self._looks_like_uuid(str(local_id)))
        if paper:
            local_status = "local"
            local_status_label = "已入库"
        elif has_local_id:
            local_status = "unknown"
            local_status_label = "本地记录缺失"
        else:
            local_status = "external"
            local_status_label = "未入库"
        category = item.get("category") or item.get("role") or "supporting_evidence"
        role, role_label = self._normalize_evidence_role(category)
        title = item.get("title") or getattr(paper, "title", None) or "Untitled evidence"
        return {
            "id": f"evidence:{item.get('paper_id') or item.get('arxiv_id') or index}",
            "index": index,
            "citation_marker": f"[{index}]",
            "title": title,
            "year": item.get("year") or getattr(paper, "year", None),
            "authors": self._authors_to_text(getattr(paper, "authors", None) or item.get("authors")),
            "source": item.get("source") or getattr(paper, "source", None) or "evidence",
            "source_label": item.get("source") or ("本地论文库" if local_status == "local" else "外部证据"),
            "source_kind": item.get("category") or "evidence",
            "paper_id": str(getattr(paper, "id", local_id)) if (local_status in {"local", "unknown"} and local_id) else None,
            "external_paper_id": item.get("paper_id") if not self._looks_like_uuid(str(item.get("paper_id") or "")) else None,
            "arxiv_id": item.get("arxiv_id") or getattr(paper, "arxiv_id", None),
            "doi": item.get("doi") or getattr(paper, "doi", None),
            "role": role,
            "role_label": role_label,
            "snippet": item.get("relevance") or item.get("abstract_excerpt") or (getattr(paper, "abstract", "") or "")[:240],
            "local_status": local_status,
            "local_status_label": local_status_label,
            "bibtex_ready": local_status == "local",
        }

    def _paper_to_evidence_card(self, paper, index: int) -> dict:
        return {
            "id": f"paper:{paper.id}",
            "index": index,
            "citation_marker": f"[{index}]",
            "title": paper.title,
            "year": paper.year,
            "authors": self._authors_to_text(paper.authors),
            "source": paper.source,
            "source_label": "本地论文库",
            "source_kind": "recommended_paper",
            "paper_id": str(paper.id),
            "external_paper_id": None,
            "arxiv_id": paper.arxiv_id,
            "doi": paper.doi,
            "role": "supporting_evidence",
            "role_label": "支持证据",
            "snippet": (paper.abstract or "")[:240] or "该论文暂无摘要，建议补摘要/补全文后再做精细引用校验。",
            "local_status": "local",
            "local_status_label": "已入库",
            "bibtex_ready": True,
        }

    def _normalize_evidence_role(self, role: str) -> tuple[str, str]:
        mapping = {
            "seed": ("supporting_evidence", "核心证据"),
            "inspiration": ("supporting_evidence", "灵感证据"),
            "background": ("background", "背景资料"),
            "baseline": ("baseline_method", "基线方法"),
            "baseline_method": ("baseline_method", "基线方法"),
            "counterexample": ("counterexample", "反例/局限"),
            "limitation": ("counterexample", "反例/局限"),
        }
        return mapping.get((role or "").lower(), ("supporting_evidence", "支持证据"))

    def _authors_to_text(self, authors) -> str:
        if isinstance(authors, list):
            return ", ".join(str(author) for author in authors[:4])
        if isinstance(authors, dict):
            values = authors.get("names") or authors.get("authors") or []
            if isinstance(values, list):
                return ", ".join(str(author) for author in values[:4])
        return str(authors or "")

    def _evidence_card_key(self, card: dict) -> str:
        return (
            card.get("paper_id")
            or self._normalize_arxiv_id(card.get("arxiv_id") or "")
            or (card.get("doi") or "").lower()
            or (card.get("title") or "").lower()
        )

    def _normalize_arxiv_id(self, value: str) -> str:
        return re.sub(r"^arxiv[:\s]*", "", value or "", flags=re.I).strip().lower()

    def _extract_citation_mentions(self, text: str) -> list[dict]:
        mentions: list[dict[str, Any]] = []
        for match in re.finditer(r"\[(\d+)\]", text or ""):
            mentions.append({
                "type": "index",
                "raw": match.group(0),
                "value": int(match.group(1)),
                "start": match.start(),
                "end": match.end(),
            })
        for match in re.finditer(r"arXiv[:\s]+([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", text or "", flags=re.I):
            mentions.append({
                "type": "arxiv",
                "raw": match.group(0),
                "value": match.group(1),
                "start": match.start(),
                "end": match.end(),
            })
        for match in re.finditer(r"Paper ID:\s*([0-9a-fA-F-]{32,36})", text or "", flags=re.I):
            mentions.append({
                "type": "paper_id",
                "raw": match.group(0),
                "value": match.group(1),
                "start": match.start(),
                "end": match.end(),
            })
        return sorted(mentions, key=lambda item: item["start"])

    def _resolve_citation_card(self, mention: dict, cards: list[dict]) -> dict | None:
        if mention["type"] == "index":
            index = mention["value"]
            return cards[index - 1] if 1 <= index <= len(cards) else None
        if mention["type"] == "arxiv":
            normalized = self._normalize_arxiv_id(mention["value"])
            return next((card for card in cards if self._normalize_arxiv_id(card.get("arxiv_id") or "") == normalized), None)
        if mention["type"] == "paper_id":
            value = str(mention["value"]).lower()
            return next((card for card in cards if str(card.get("paper_id") or "").lower() == value), None)
        return None

    def _citation_context(self, text: str, start: int, end: int) -> str:
        before = max(text.rfind("。", 0, start), text.rfind(".", 0, start), text.rfind("\n", 0, start))
        after_candidates = [pos for pos in [text.find("。", end), text.find(".", end), text.find("\n", end)] if pos != -1]
        after = min(after_candidates) if after_candidates else min(len(text), end + 240)
        return text[before + 1:after + 1].strip()[:500] or text.strip()[:500]

    def _citation_summary(self, checks: list[dict]) -> dict:
        counts = {"strong": 0, "partial": 0, "weak": 0, "missing": 0, "unchecked": 0}
        for check in checks:
            status = check.get("status")
            counts[status if status in counts else "weak"] += 1
        total = len(checks)
        verified = counts["strong"] + counts["partial"]
        return {
            "total": total,
            **counts,
            "citation_coverage": round(verified / total, 3) if total else 0,
            "evidence_warning": counts["weak"] > 0 or counts["missing"] > 0 or counts["unchecked"] > 0,
        }

    def _recommend_evidence_cards(self, cards: list[dict], limit: int = 3) -> list[dict]:
        return [
            {
                "citation_marker": card.get("citation_marker"),
                "title": card.get("title"),
                "role_label": card.get("role_label"),
                "local_status_label": card.get("local_status_label"),
            }
            for card in cards[:limit]
        ]

    def _evidence_writing_use(self, card: dict) -> str:
        status = card.get("local_status")
        role = card.get("role_label") or "支持证据"
        if status == "local":
            return f"可作为{role}写入 Related Work；定稿前建议继续运行章节引用校验。"
        if status == "unknown":
            return "记录过本地 ID 但当前论文缺失，建议重新入库或替换引用。"
        return f"可作为{role}的线索；尚未入库，不能当作已验证证据。"
