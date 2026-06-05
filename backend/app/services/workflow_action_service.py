"""Cross-module workflow action recommendations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification
from app.db.models.paper import Paper, UserPaper
from app.db.models.research import ResearchIdea, ResearchProject
from app.db.models.user import User
from app.db.models.workspace import ProjectSpace, ProjectSpaceMember
from app.db.models.writing import WritingProject


PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


class WorkflowActionService:
    """Build generated next actions across research workflow modules."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_actions(self, user: User) -> dict:
        actions: list[dict[str, Any]] = []
        actions.extend(await self._paper_actions(user))
        actions.extend(await self._digest_actions(user))
        actions.extend(await self._research_actions(user))
        actions.extend(await self._writing_actions(user))
        actions.extend(await self._workspace_actions(user))
        return self.build_response(actions)

    def build_response(self, actions: list[dict[str, Any]]) -> dict:
        ordered = sorted(
            actions,
            key=lambda item: (PRIORITY_RANK.get(item.get("priority"), 9), item.get("group", ""), item.get("title", "")),
        )
        groups: dict[str, int] = {}
        for item in ordered:
            groups[item["group"]] = groups.get(item["group"], 0) + 1
        return {
            "summary": {
                "total": len(ordered),
                "high_priority": sum(1 for item in ordered if item.get("priority") == "high"),
                "groups": groups,
            },
            "actions": ordered,
        }

    def action(
        self,
        action_id: str,
        group: str,
        priority: str,
        title: str,
        description: str,
        path: str,
        source: str,
        metadata: dict | None = None,
        action_type: str = "navigate",
        action_label: str | None = None,
        method: str | None = None,
        endpoint: str | None = None,
        requires_admin: bool = False,
    ) -> dict[str, Any]:
        return {
            "id": action_id,
            "group": group,
            "priority": priority,
            "title": title,
            "description": description,
            "path": path,
            "source": source,
            "metadata": metadata or {},
            "action_type": action_type,
            "action_label": action_label or ("执行" if action_type == "api" else "进入"),
            "method": method,
            "endpoint": endpoint,
            "requires_admin": requires_admin,
        }

    async def _paper_actions(self, user: User) -> list[dict[str, Any]]:
        saved_count = await self._scalar_count(
            select(func.count(UserPaper.id)).where(UserPaper.user_id == user.id, UserPaper.saved == True)
        )
        unread_count = await self._scalar_count(
            select(func.count(UserPaper.id)).where(
                UserPaper.user_id == user.id,
                UserPaper.saved == True,
                UserPaper.read_status.in_(["unread", "reading"]),
            )
        )
        missing_full_text = await self._scalar_count(
            select(func.count(Paper.id))
            .join(UserPaper, UserPaper.paper_id == Paper.id)
            .where(
                UserPaper.user_id == user.id,
                UserPaper.saved == True,
                or_(Paper.full_text.is_(None), Paper.full_text == ""),
            )
        )
        missing_embeddings = await self._scalar_count(
            select(func.count(Paper.id))
            .join(UserPaper, UserPaper.paper_id == Paper.id)
            .where(UserPaper.user_id == user.id, UserPaper.saved == True, Paper.embedding.is_(None))
        )

        actions = []
        if saved_count == 0:
            actions.append(self.action(
                "papers:start-library",
                "papers",
                "high",
                "先建立论文基底",
                "当前还没有收藏论文，建议从论文库检索或推送中心挑选几篇核心论文入库。",
                "/papers",
                "paper-library",
                {"count": saved_count},
            ))
        if unread_count:
            actions.append(self.action(
                "papers:continue-reading",
                "papers",
                "medium",
                "继续阅读待读论文",
                f"有 {unread_count} 篇收藏论文仍处于未读或阅读中，可以先完成关键论文阅读。",
                "/papers",
                "reading-status",
                {"count": unread_count},
            ))
        if missing_full_text:
            actions.append(self.action(
                "papers:full-text",
                "papers",
                "high" if missing_full_text >= 5 else "medium",
                "补全文以增强问答证据",
                f"有 {missing_full_text} 篇收藏论文缺少全文，论文问答和写作引用会受到影响。",
                "/settings",
                "knowledge-maintenance",
                {"count": missing_full_text},
                action_type="api",
                action_label="补 5 篇全文",
                method="POST",
                endpoint="/papers/maintenance/backfill-full-text?limit=5",
                requires_admin=True,
            ))
        if missing_embeddings:
            actions.append(self.action(
                "papers:embeddings",
                "papers",
                "medium",
                "补向量以提升检索命中",
                f"有 {missing_embeddings} 篇收藏论文缺少向量，建议补齐后再做大范围检索。",
                "/settings",
                "knowledge-maintenance",
                {"count": missing_embeddings},
                action_type="api",
                action_label="补 20 篇向量",
                method="POST",
                endpoint="/papers/maintenance/backfill-embeddings?limit=20",
                requires_admin=True,
            ))
        return actions[:4]

    async def _digest_actions(self, user: User) -> list[dict[str, Any]]:
        unread_digests = await self._scalar_count(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id,
                Notification.category == "digest",
                Notification.is_read == False,
            )
        )
        if not unread_digests:
            return []
        return [self.action(
            "digests:review",
            "papers",
            "medium",
            "筛选今日论文推送",
            f"推送中心还有 {unread_digests} 条未读论文摘要，可选择感兴趣、稍后读或忽略。",
            "/papers/digests",
            "paper-digest",
            {"count": unread_digests},
        )]

    async def _research_actions(self, user: User) -> list[dict[str, Any]]:
        active_projects = await self._scalar_count(
            select(func.count(ResearchProject.id)).where(ResearchProject.user_id == user.id, ResearchProject.status == "active")
        )
        draft_ideas = await self._scalar_count(
            select(func.count(ResearchIdea.id))
            .join(ResearchProject, ResearchProject.id == ResearchIdea.project_id)
            .where(ResearchProject.user_id == user.id, ResearchIdea.status == "draft")
        )
        actions = []
        if active_projects == 0:
            actions.append(self.action(
                "research:create-direction",
                "research",
                "medium",
                "创建研究方向",
                "还没有活跃研究方向。可以从论文证据或推送结果开始生成候选 idea。",
                "/research",
                "research-workflow",
            ))
        else:
            actions.append(self.action(
                "research:continue-projects",
                "research",
                "low",
                "推进活跃研究方向",
                f"当前有 {active_projects} 个活跃研究方向，可以继续生成 idea、实验方案或反馈演化。",
                "/research",
                "research-workflow",
                {"count": active_projects},
            ))
        if draft_ideas:
            actions.append(self.action(
                "research:review-draft-ideas",
                "research",
                "medium",
                "评审草稿 Idea",
                f"有 {draft_ideas} 个草稿 idea 等待证据评审、实验设计或演化。",
                "/research",
                "idea-review",
                {"count": draft_ideas},
            ))
        return actions[:3]

    async def _writing_actions(self, user: User) -> list[dict[str, Any]]:
        draft_projects = await self._scalar_count(
            select(func.count(WritingProject.id)).where(WritingProject.user_id == str(user.id), WritingProject.status == "draft")
        )
        if draft_projects:
            return [self.action(
                "writing:continue-drafts",
                "writing",
                "medium",
                "继续写作草稿",
                f"有 {draft_projects} 个写作草稿处于 draft 状态，可以继续补证据、生成 Related Work 或导出。",
                "/writing",
                "writing-workflow",
                {"count": draft_projects},
            )]
        return [self.action(
            "writing:create-draft",
            "writing",
            "low",
            "从证据创建写作草稿",
            "还没有待推进的写作草稿。可以从研究方向或论文证据开始生成综述草稿。",
            "/writing",
            "writing-workflow",
        )]

    async def _workspace_actions(self, user: User) -> list[dict[str, Any]]:
        active_spaces = await self._scalar_count(
            select(func.count(ProjectSpace.id))
            .join(ProjectSpaceMember, ProjectSpaceMember.space_id == ProjectSpace.id)
            .where(ProjectSpaceMember.user_id == user.id, ProjectSpace.status != "deleted")
        )
        if active_spaces:
            return [self.action(
                "workspaces:review-dashboard",
                "workspaces",
                "low",
                "查看项目空间看板",
                f"你参与了 {active_spaces} 个项目空间，可以从空间看板检查资源、成员和下一步建议。",
                "/workspaces",
                "workspace-dashboard",
                {"count": active_spaces},
            )]
        return [self.action(
            "workspaces:create-space",
            "workspaces",
            "low",
            "创建项目空间",
            "可以把论文、研究方向和写作草稿收进一个项目空间，形成协作上下文。",
            "/workspaces",
            "workspace-dashboard",
        )]

    async def _scalar_count(self, query) -> int:
        result = await self.session.execute(query)
        return int(result.scalar() or 0)
