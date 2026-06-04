"""项目空间服务。"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.paper import Paper, UserPaper
from app.db.models.research import ResearchProject
from app.db.models.user import User
from app.db.models.workspace import ProjectSpace, ProjectSpaceMember
from app.db.models.writing import WritingProject


VALID_SPACE_ROLES = {"owner", "editor", "viewer"}


class WorkspaceService:
    """统一科研项目空间服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_space(
        self,
        user: User,
        name: str,
        description: str = "",
        metadata_json: Optional[dict] = None,
    ) -> dict:
        space = ProjectSpace(
            name=name.strip(),
            description=description.strip() or None,
            owner_id=user.id,
            metadata_json=metadata_json or {"resource_links": []},
        )
        self.session.add(space)
        await self.session.flush()
        self.session.add(ProjectSpaceMember(space_id=space.id, user_id=user.id, role="owner"))
        await self.session.commit()
        await self.session.refresh(space)
        return await self.space_to_dict(space, user.id, include_summary=False)

    async def list_spaces(self, user: User) -> list[dict]:
        result = await self.session.execute(
            select(ProjectSpace)
            .join(ProjectSpaceMember, ProjectSpaceMember.space_id == ProjectSpace.id)
            .where(ProjectSpaceMember.user_id == user.id, ProjectSpace.status != "deleted")
            .options(selectinload(ProjectSpace.members))
            .order_by(ProjectSpace.updated_at.desc())
        )
        spaces = result.scalars().unique().all()
        return [await self.space_to_dict(space, user.id, include_summary=False) for space in spaces]

    async def get_space_for_user(self, space_id: str, user: User) -> tuple[ProjectSpace, str] | None:
        try:
            sid = UUID(space_id)
        except ValueError:
            return None
        result = await self.session.execute(
            select(ProjectSpace)
            .join(ProjectSpaceMember, ProjectSpaceMember.space_id == ProjectSpace.id)
            .where(
                ProjectSpace.id == sid,
                ProjectSpace.status != "deleted",
                ProjectSpaceMember.user_id == user.id,
            )
            .options(selectinload(ProjectSpace.members))
        )
        space = result.scalars().unique().one_or_none()
        if not space:
            return None
        return space, self._role_for(space, user.id)

    async def get_space_detail(self, space_id: str, user: User) -> dict | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, role = access
        data = await self.space_to_dict(space, user.id, include_summary=True)
        data["role"] = role
        return data

    async def update_space(self, space_id: str, user: User, **updates) -> dict | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, role = access
        if role != "owner":
            raise PermissionError("只有项目空间 owner 可以更新空间")
        if updates.get("name") is not None:
            space.name = str(updates["name"]).strip()
        if updates.get("description") is not None:
            space.description = str(updates["description"]).strip() or None
        if updates.get("metadata_json") is not None:
            space.metadata_json = updates["metadata_json"] or {}
        await self.session.commit()
        await self.session.refresh(space)
        return await self.space_to_dict(space, user.id, include_summary=True)

    async def delete_space(self, space_id: str, user: User) -> bool | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, role = access
        if role != "owner":
            raise PermissionError("只有项目空间 owner 可以删除空间")
        space.status = "deleted"
        await self.session.commit()
        return True

    async def add_member(self, space_id: str, user: User, account: str, role: str = "viewer") -> dict | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, current_role = access
        if current_role != "owner":
            raise PermissionError("只有项目空间 owner 可以管理成员")
        role = role if role in VALID_SPACE_ROLES and role != "owner" else "viewer"
        account = account.strip()
        result = await self.session.execute(
            select(User).where(or_(User.username == account, User.email == account))
        )
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise LookupError("用户不存在")
        existing = await self.session.execute(
            select(ProjectSpaceMember).where(
                ProjectSpaceMember.space_id == space.id,
                ProjectSpaceMember.user_id == target_user.id,
            )
        )
        member = existing.scalar_one_or_none()
        if member:
            if member.role == "owner":
                raise PermissionError("不能修改 owner 角色")
            member.role = role
        else:
            self.session.add(ProjectSpaceMember(space_id=space.id, user_id=target_user.id, role=role))
        await self.session.commit()
        detail = await self.get_space_detail(str(space.id), user)
        return detail

    async def remove_member(self, space_id: str, user: User, member_user_id: str) -> dict | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, current_role = access
        if current_role != "owner":
            raise PermissionError("只有项目空间 owner 可以管理成员")
        try:
            uid = UUID(member_user_id)
        except ValueError:
            raise LookupError("成员不存在")
        if uid == space.owner_id:
            raise PermissionError("不能移除项目空间 owner")
        result = await self.session.execute(
            select(ProjectSpaceMember).where(
                ProjectSpaceMember.space_id == space.id,
                ProjectSpaceMember.user_id == uid,
            )
        )
        member = result.scalar_one_or_none()
        if member:
            await self.session.delete(member)
            await self.session.commit()
        return await self.get_space_detail(str(space.id), user)

    async def space_to_dict(self, space: ProjectSpace, user_id, include_summary: bool) -> dict:
        members = await self._members_to_dict(space)
        data = {
            "id": str(space.id),
            "name": space.name,
            "description": space.description or "",
            "status": space.status,
            "owner_id": str(space.owner_id),
            "role": self._role_for(space, user_id),
            "metadata_json": space.metadata_json or {},
            "members": members,
            "member_count": len(members),
            "created_at": space.created_at.isoformat() if space.created_at else "",
            "updated_at": space.updated_at.isoformat() if space.updated_at else "",
        }
        if include_summary:
            data["summary"] = await self.build_summary(space)
            data["next_actions"] = self._next_actions(data["summary"])
        return data

    async def build_summary(self, space: ProjectSpace) -> dict:
        links = list((space.metadata_json or {}).get("resource_links") or [])
        linked = await self._linked_resources(links)
        recent = await self._recent_resources(space.owner_id)
        return {
            "linked_resources": linked,
            "recent_resources": recent,
            "counts": {
                "linked_papers": len(linked["papers"]),
                "linked_research_projects": len(linked["research_projects"]),
                "linked_writing_projects": len(linked["writing_projects"]),
                "recent_papers": len(recent["papers"]),
                "recent_research_projects": len(recent["research_projects"]),
                "recent_writing_projects": len(recent["writing_projects"]),
            },
        }

    async def _members_to_dict(self, space: ProjectSpace) -> list[dict]:
        user_ids = [member.user_id for member in (space.members or [])]
        if not user_ids:
            return []
        result = await self.session.execute(select(User).where(User.id.in_(user_ids)))
        users = {user.id: user for user in result.scalars().all()}
        rows = []
        for member in sorted(space.members or [], key=lambda item: item.created_at):
            user = users.get(member.user_id)
            rows.append({
                "user_id": str(member.user_id),
                "username": user.username if user else "unknown",
                "email": user.email if user else "",
                "display_name": user.display_name if user else None,
                "avatar": user.avatar if user else None,
                "role": member.role,
            })
        return rows

    async def _linked_resources(self, links: list[dict]) -> dict:
        grouped = {"papers": [], "research_projects": [], "writing_projects": []}
        for link in links:
            rtype = link.get("type")
            rid = link.get("id")
            if not rid:
                continue
            item = await self._resource_brief(rtype, rid)
            if item and rtype in grouped:
                grouped[rtype].append(item)
        return grouped

    async def _recent_resources(self, owner_id) -> dict:
        paper_result = await self.session.execute(
            select(Paper)
            .join(UserPaper, UserPaper.paper_id == Paper.id)
            .where(UserPaper.user_id == owner_id)
            .order_by(UserPaper.updated_at.desc())
            .limit(5)
        )
        research_result = await self.session.execute(
            select(ResearchProject)
            .where(ResearchProject.user_id == owner_id)
            .order_by(ResearchProject.updated_at.desc())
            .limit(5)
        )
        writing_result = await self.session.execute(
            select(WritingProject)
            .where(WritingProject.user_id == str(owner_id))
            .order_by(WritingProject.updated_at.desc())
            .limit(5)
        )
        return {
            "papers": [self._paper_brief(paper) for paper in paper_result.scalars().all()],
            "research_projects": [self._research_brief(project) for project in research_result.scalars().all()],
            "writing_projects": [self._writing_brief(project) for project in writing_result.scalars().all()],
        }

    async def _resource_brief(self, rtype: str, rid: str) -> Optional[dict]:
        try:
            uid = UUID(rid)
        except ValueError:
            return None
        if rtype == "papers":
            result = await self.session.execute(select(Paper).where(Paper.id == uid))
            paper = result.scalar_one_or_none()
            return self._paper_brief(paper) if paper else None
        if rtype == "research_projects":
            result = await self.session.execute(select(ResearchProject).where(ResearchProject.id == uid))
            project = result.scalar_one_or_none()
            return self._research_brief(project) if project else None
        if rtype == "writing_projects":
            result = await self.session.execute(select(WritingProject).where(WritingProject.id == str(uid)))
            project = result.scalar_one_or_none()
            return self._writing_brief(project) if project else None
        return None

    def _role_for(self, space: ProjectSpace, user_id) -> str:
        for member in space.members or []:
            if str(member.user_id) == str(user_id):
                return member.role
        return "none"

    def _paper_brief(self, paper: Paper) -> dict:
        return {
            "id": str(paper.id),
            "title": paper.title,
            "subtitle": f"{paper.year or 'N/A'} · {paper.arxiv_id or paper.source or 'paper'}",
            "type": "papers",
            "path": f"/papers/{paper.id}",
        }

    def _research_brief(self, project: ResearchProject) -> dict:
        return {
            "id": str(project.id),
            "title": project.name,
            "subtitle": project.description or "研究方向",
            "type": "research_projects",
            "path": f"/research/{project.id}",
        }

    def _writing_brief(self, project: WritingProject) -> dict:
        return {
            "id": str(project.id),
            "title": project.title,
            "subtitle": project.description or project.template_type,
            "type": "writing_projects",
            "path": f"/writing?project={project.id}",
        }

    def _next_actions(self, summary: dict) -> list[dict]:
        counts = summary.get("counts") or {}
        actions = []
        if counts.get("recent_papers", 0) == 0 and counts.get("linked_papers", 0) == 0:
            actions.append({"label": "去论文库入库论文", "path": "/papers", "kind": "papers"})
        if counts.get("recent_research_projects", 0) == 0:
            actions.append({"label": "创建研究方向", "path": "/research", "kind": "research"})
        if counts.get("recent_writing_projects", 0) == 0:
            actions.append({"label": "创建写作草稿", "path": "/writing", "kind": "writing"})
        if not actions:
            actions.append({"label": "从空间继续推进写作", "path": "/writing", "kind": "writing"})
            actions.append({"label": "查看论文推送中心", "path": "/papers/digests", "kind": "papers"})
        return actions
