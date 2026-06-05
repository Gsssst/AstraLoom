"""项目空间服务。"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.paper import Paper, UserPaper
from app.db.models.research import ResearchProject
from app.db.models.user import User
from app.db.models.workspace import ProjectSpace, ProjectSpaceActivity, ProjectSpaceMember, ProjectSpaceResource
from app.db.models.writing import WritingProject


VALID_SPACE_ROLES = {"owner", "editor", "viewer"}
VALID_RESOURCE_TYPES = {"papers", "research_projects", "writing_projects"}
SPACE_ROLE_RANK = {"none": 0, "viewer": 1, "editor": 2, "owner": 3}


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
        self._record_activity(space, user, "space_created", metadata={"name": space.name})
        await self.session.commit()
        await self.session.refresh(space)
        return await self.space_to_dict(space, user.id, include_summary=False)

    async def list_spaces(self, user: User) -> list[dict]:
        result = await self.session.execute(
            select(ProjectSpace)
            .join(ProjectSpaceMember, ProjectSpaceMember.space_id == ProjectSpace.id)
            .where(ProjectSpaceMember.user_id == user.id, ProjectSpace.status != "deleted")
            .options(selectinload(ProjectSpace.members), selectinload(ProjectSpace.resources))
            .order_by(ProjectSpace.updated_at.desc())
        )
        spaces = result.scalars().unique().all()
        return [await self.space_to_dict(space, user.id, include_summary=True) for space in spaces]

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
        self._record_activity(space, user, "space_updated", metadata={"fields": sorted(updates.keys())})
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
        self._record_activity(space, user, "space_deleted")
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
        action = "member_updated"
        if member:
            if member.role == "owner":
                raise PermissionError("不能修改 owner 角色")
            member.role = role
        else:
            self.session.add(ProjectSpaceMember(space_id=space.id, user_id=target_user.id, role=role))
            action = "member_added"
        self._record_activity(
            space,
            user,
            action,
            resource_type="members",
            resource_id=str(target_user.id),
            metadata={"target_username": target_user.username, "role": role},
        )
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
            self._record_activity(space, user, "member_removed", resource_type="members", resource_id=str(uid))
            await self.session.commit()
        return await self.get_space_detail(str(space.id), user)

    async def link_resource(
        self,
        space_id: str,
        user: User,
        resource_type: str,
        resource_id: str,
        metadata_json: Optional[dict] = None,
    ) -> dict | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, role = access
        if role not in {"owner", "editor"}:
            raise PermissionError("只有 owner 或 editor 可以绑定空间资源")
        resource_type = self._normalize_resource_type(resource_type)
        if not resource_type:
            raise LookupError("不支持的资源类型")
        resource = await self._resource_brief(resource_type, resource_id)
        if not resource:
            raise LookupError("资源不存在或无法访问")

        existing = await self.session.execute(
            select(ProjectSpaceResource).where(
                ProjectSpaceResource.space_id == space.id,
                ProjectSpaceResource.resource_type == resource_type,
                ProjectSpaceResource.resource_id == str(resource_id),
            )
        )
        link = existing.scalar_one_or_none()
        if link:
            link.metadata_json = metadata_json or link.metadata_json or {}
        else:
            link = ProjectSpaceResource(
                space_id=space.id,
                resource_type=resource_type,
                resource_id=str(resource_id),
                added_by=user.id,
                metadata_json=metadata_json or {},
            )
            self.session.add(link)
        self._record_activity(
            space,
            user,
            "resource_linked",
            resource_type=resource_type,
            resource_id=str(resource_id),
            metadata={"title": resource.get("title")},
        )
        await self.session.commit()
        return await self.get_space_detail(str(space.id), user)

    async def unlink_resource(
        self,
        space_id: str,
        user: User,
        resource_type: str,
        resource_id: str,
    ) -> dict | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, role = access
        if role not in {"owner", "editor"}:
            raise PermissionError("只有 owner 或 editor 可以移除空间资源")
        resource_type = self._normalize_resource_type(resource_type)
        if not resource_type:
            raise LookupError("不支持的资源类型")
        result = await self.session.execute(
            select(ProjectSpaceResource).where(
                ProjectSpaceResource.space_id == space.id,
                ProjectSpaceResource.resource_type == resource_type,
                ProjectSpaceResource.resource_id == str(resource_id),
            )
        )
        link = result.scalar_one_or_none()
        if link:
            await self.session.delete(link)
            self._record_activity(
                space,
                user,
                "resource_unlinked",
                resource_type=resource_type,
                resource_id=str(resource_id),
            )
            await self.session.commit()
        return await self.get_space_detail(str(space.id), user)

    async def list_activities(self, space_id: str, user: User, limit: int = 30) -> list[dict] | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, _role = access
        result = await self.session.execute(
            select(ProjectSpaceActivity)
            .where(ProjectSpaceActivity.space_id == space.id)
            .order_by(desc(ProjectSpaceActivity.created_at))
            .limit(max(1, min(limit, 100)))
        )
        return await self.activities_to_dict(result.scalars().all())

    async def search_resource_candidates(
        self,
        space_id: str,
        user: User,
        resource_type: str,
        q: str = "",
        limit: int = 12,
    ) -> list[dict] | None:
        access = await self.get_space_for_user(space_id, user)
        if not access:
            return None
        space, _role = access
        resource_type = self._normalize_resource_type(resource_type)
        if not resource_type:
            raise LookupError("不支持的资源类型")
        limit = max(1, min(limit, 30))
        q = (q or "").strip()

        if resource_type == "papers":
            items = await self._search_paper_candidates(q, limit)
        elif resource_type == "research_projects":
            items = await self._search_research_candidates(user, q, limit)
        elif resource_type == "writing_projects":
            items = await self._search_writing_candidates(user, q, limit)
        else:
            items = []

        linked = self._linked_resource_key_set(space)
        for item in items:
            item["linked"] = (item["type"], item["id"]) in linked
        return items

    async def resource_link_status(
        self,
        user: User,
        resource_type: str,
        resource_id: str,
    ) -> dict:
        resource_type = self._normalize_resource_type(resource_type)
        if not resource_type:
            raise LookupError("不支持的资源类型")
        result = await self.session.execute(
            select(ProjectSpace)
            .join(ProjectSpaceMember, ProjectSpaceMember.space_id == ProjectSpace.id)
            .where(ProjectSpaceMember.user_id == user.id, ProjectSpace.status != "deleted")
            .options(selectinload(ProjectSpace.members), selectinload(ProjectSpace.resources))
            .order_by(ProjectSpace.updated_at.desc())
        )
        spaces = result.scalars().unique().all()
        rows = []
        target_key = (resource_type, str(resource_id))
        for space in spaces:
            role = self._role_for(space, user.id)
            linked = target_key in self._linked_resource_key_set(space)
            rows.append({
                "id": str(space.id),
                "name": space.name,
                "description": space.description or "",
                "role": role,
                "linked": linked,
                "can_edit": role in {"owner", "editor"},
                "member_count": len(space.members or []),
            })
        return {
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "spaces": rows,
        }

    async def resource_role_for_user(
        self,
        user_id,
        resource_type: str,
        resource_id: str,
    ) -> str:
        resource_type = self._normalize_resource_type(resource_type) or ""
        if resource_type not in VALID_RESOURCE_TYPES or not resource_id:
            return "none"
        try:
            normalized_user_id = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
        except ValueError:
            return "none"
        result = await self.session.execute(
            select(ProjectSpaceMember.role)
            .join(ProjectSpace, ProjectSpace.id == ProjectSpaceMember.space_id)
            .join(ProjectSpaceResource, ProjectSpaceResource.space_id == ProjectSpace.id)
            .where(
                ProjectSpace.status != "deleted",
                ProjectSpaceMember.user_id == normalized_user_id,
                ProjectSpaceResource.resource_type == resource_type,
                ProjectSpaceResource.resource_id == str(resource_id),
            )
        )
        roles = [role for role in result.scalars().all() if role in SPACE_ROLE_RANK]
        return max(roles, key=lambda role: SPACE_ROLE_RANK[role], default="none")

    def role_can_read_resource(self, role: str) -> bool:
        return SPACE_ROLE_RANK.get(role, 0) >= SPACE_ROLE_RANK["viewer"]

    def role_can_edit_resource(self, role: str) -> bool:
        return SPACE_ROLE_RANK.get(role, 0) >= SPACE_ROLE_RANK["editor"]

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
            data["dashboard"] = self.build_dashboard(data["summary"])
            data["next_actions"] = self._next_actions(data["summary"])
            data["activities"] = await self.recent_activities_for_space(space, limit=20)
        return data

    async def build_summary(self, space: ProjectSpace) -> dict:
        links = self._resource_links_from_space(space)
        linked = await self._linked_resources(links)
        recent = await self._recent_resources(space.owner_id)
        recent_activity_count = await self._recent_activity_count(space)
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
                "recent_activities": recent_activity_count,
            },
        }

    async def _recent_activity_count(self, space: ProjectSpace) -> int:
        result = await self.session.execute(
            select(ProjectSpaceActivity.id)
            .where(ProjectSpaceActivity.space_id == space.id)
            .order_by(desc(ProjectSpaceActivity.created_at))
            .limit(20)
        )
        return len(result.scalars().all())

    def build_dashboard(self, summary: dict) -> dict:
        counts = summary.get("counts") or {}
        linked_papers = int(counts.get("linked_papers") or 0)
        linked_research = int(counts.get("linked_research_projects") or 0)
        linked_writing = int(counts.get("linked_writing_projects") or 0)
        activity_count = int(counts.get("recent_activities") or 0)
        progress_score = min(
            100,
            (25 if linked_papers else 0)
            + (25 if linked_research else 0)
            + (30 if linked_writing else 0)
            + min(linked_papers, 4) * 3
            + min(activity_count, 5) * 2,
        )
        if linked_writing:
            stage = "drafting"
            stage_label = "写作推进中"
        elif linked_research:
            stage = "researching"
            stage_label = "研究方向探索中"
        elif linked_papers:
            stage = "reading"
            stage_label = "论文积累中"
        else:
            stage = "setup"
            stage_label = "待搭建"
        status_cards = [
            self._dashboard_status_card("papers", "论文线索", linked_papers, "先积累核心论文和背景论文", "/papers"),
            self._dashboard_status_card("research_projects", "研究方向", linked_research, "把论文证据收敛成可验证 Idea", "/research"),
            self._dashboard_status_card("writing_projects", "写作草稿", linked_writing, "沉淀综述、Related Work 或实验报告", "/writing"),
            self._dashboard_status_card("activity", "最近活动", activity_count, "空间协作和资源变更会在这里留下记录", None),
        ]
        return {
            "progress_score": progress_score,
            "stage": stage,
            "stage_label": stage_label,
            "resource_balance": {
                "papers": linked_papers,
                "research_projects": linked_research,
                "writing_projects": linked_writing,
                "activity": activity_count,
            },
            "status_cards": status_cards,
        }

    def _dashboard_status_card(self, key: str, label: str, count: int, hint: str, path: Optional[str]) -> dict:
        if count > 0:
            status = "ready"
            status_label = "已就绪"
        else:
            status = "empty"
            status_label = "待补充"
        return {
            "key": key,
            "label": label,
            "count": count,
            "status": status,
            "status_label": status_label,
            "hint": hint,
            "path": path,
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
            rtype = self._normalize_resource_type(link.get("type") or link.get("resource_type"))
            rid = link.get("id")
            if not rid:
                continue
            item = await self._resource_brief(rtype, rid)
            if item and rtype in grouped:
                item["link_id"] = link.get("link_id")
                item["linked_at"] = link.get("linked_at")
                item["linked_by"] = link.get("linked_by")
                item["legacy"] = bool(link.get("legacy"))
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

    async def _search_paper_candidates(self, q: str, limit: int) -> list[dict]:
        query = select(Paper)
        if q:
            needle = f"%{q}%"
            query = query.where(
                or_(
                    Paper.title.ilike(needle),
                    Paper.abstract.ilike(needle),
                    Paper.arxiv_id.ilike(needle),
                    Paper.doi.ilike(needle),
                    Paper.source.ilike(needle),
                )
            )
            query = query.order_by(Paper.year.desc().nullslast(), Paper.updated_at.desc())
        else:
            query = query.order_by(Paper.updated_at.desc())
        result = await self.session.execute(query.limit(limit))
        return [self._paper_brief(paper) for paper in result.scalars().all()]

    async def _search_research_candidates(self, user: User, q: str, limit: int) -> list[dict]:
        query = select(ResearchProject).where(ResearchProject.user_id == user.id)
        if q:
            needle = f"%{q}%"
            query = query.where(or_(ResearchProject.name.ilike(needle), ResearchProject.description.ilike(needle)))
        result = await self.session.execute(query.order_by(ResearchProject.updated_at.desc()).limit(limit))
        return [self._research_brief(project) for project in result.scalars().all()]

    async def _search_writing_candidates(self, user: User, q: str, limit: int) -> list[dict]:
        query = select(WritingProject).where(WritingProject.user_id == str(user.id))
        if q:
            needle = f"%{q}%"
            query = query.where(or_(WritingProject.title.ilike(needle), WritingProject.description.ilike(needle)))
        result = await self.session.execute(query.order_by(WritingProject.updated_at.desc()).limit(limit))
        return [self._writing_brief(project) for project in result.scalars().all()]

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

    def _resource_links_from_space(self, space: ProjectSpace) -> list[dict]:
        links: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for resource in sorted(getattr(space, "resources", []) or [], key=lambda item: item.created_at, reverse=True):
            rtype = self._normalize_resource_type(resource.resource_type)
            rid = str(resource.resource_id)
            if not rtype or (rtype, rid) in seen:
                continue
            seen.add((rtype, rid))
            links.append({
                "link_id": str(resource.id),
                "type": rtype,
                "id": rid,
                "linked_by": str(resource.added_by) if resource.added_by else None,
                "linked_at": resource.created_at.isoformat() if resource.created_at else "",
            })

        for link in list((space.metadata_json or {}).get("resource_links") or []):
            rtype = self._normalize_resource_type(link.get("type") or link.get("resource_type"))
            rid = str(link.get("id") or "")
            if not rtype or not rid or (rtype, rid) in seen:
                continue
            seen.add((rtype, rid))
            links.append({**link, "type": rtype, "id": rid, "legacy": True})
        return links

    def _linked_resource_key_set(self, space: ProjectSpace) -> set[tuple[str, str]]:
        return {
            (link["type"], str(link["id"]))
            for link in self._resource_links_from_space(space)
            if link.get("type") and link.get("id")
        }

    async def recent_activities_for_space(self, space: ProjectSpace, limit: int = 20) -> list[dict]:
        result = await self.session.execute(
            select(ProjectSpaceActivity)
            .where(ProjectSpaceActivity.space_id == space.id)
            .order_by(desc(ProjectSpaceActivity.created_at))
            .limit(max(1, min(limit, 100)))
        )
        return await self.activities_to_dict(result.scalars().all())

    async def activities_to_dict(self, activities: list[ProjectSpaceActivity]) -> list[dict]:
        actor_ids = [activity.actor_id for activity in activities if activity.actor_id]
        users: dict = {}
        if actor_ids:
            result = await self.session.execute(select(User).where(User.id.in_(actor_ids)))
            users = {user.id: user for user in result.scalars().all()}
        rows = []
        for activity in activities:
            actor = users.get(activity.actor_id)
            rows.append({
                "id": str(activity.id),
                "space_id": str(activity.space_id),
                "actor_id": str(activity.actor_id) if activity.actor_id else None,
                "actor_name": (actor.display_name or actor.username) if actor else "系统",
                "action": activity.action,
                "resource_type": activity.resource_type,
                "resource_id": activity.resource_id,
                "metadata_json": activity.metadata_json or {},
                "created_at": activity.created_at.isoformat() if activity.created_at else "",
            })
        return rows

    def _role_for(self, space: ProjectSpace, user_id) -> str:
        for member in space.members or []:
            if str(member.user_id) == str(user_id):
                return member.role
        return "none"

    def _normalize_resource_type(self, resource_type: Optional[str]) -> Optional[str]:
        aliases = {
            "paper": "papers",
            "papers": "papers",
            "research": "research_projects",
            "research_project": "research_projects",
            "research_projects": "research_projects",
            "writing": "writing_projects",
            "writing_project": "writing_projects",
            "writing_projects": "writing_projects",
        }
        normalized = aliases.get(str(resource_type or "").strip())
        return normalized if normalized in VALID_RESOURCE_TYPES else None

    def _record_activity(
        self,
        space: ProjectSpace,
        actor: User,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ProjectSpaceActivity:
        activity = ProjectSpaceActivity(
            space_id=space.id,
            actor_id=actor.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self.session.add(activity)
        return activity

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
