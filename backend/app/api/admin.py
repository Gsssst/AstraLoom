"""管理员治理 API。"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_admin
from app.db.models.paper import Paper
from app.db.models.research import ResearchProject
from app.db.models.user import User
from app.db.models.workspace import ProjectSpace, ProjectSpaceActivity
from app.services.workspace_service import WorkspaceService
from app.db.models.writing import WritingProject
from app.db.session import get_db

router = APIRouter(prefix="/admin", tags=["管理员"])


class AdminUserUpdateRequest(BaseModel):
    role: Optional[str] = Field(default=None, pattern="^(admin|user)$")
    is_active: Optional[bool] = None


@router.get("/overview")
async def get_admin_overview(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """获取管理员总览。"""
    del admin
    counts = {}
    for key, statement in {
        "users": select(func.count(User.id)),
        "active_users": select(func.count(User.id)).where(User.is_active.is_(True)),
        "admins": select(func.count(User.id)).where(User.role == "admin"),
        "papers": select(func.count(Paper.id)),
        "research_projects": select(func.count(ResearchProject.id)),
        "writing_projects": select(func.count(WritingProject.id)),
        "project_spaces": select(func.count(ProjectSpace.id)).where(ProjectSpace.status != "deleted"),
    }.items():
        result = await db.execute(statement)
        counts[key] = int(result.scalar() or 0)

    return {
        "counts": counts,
        "risk_hints": _overview_risk_hints(counts),
    }


@router.get("/users")
async def list_admin_users(
    query: str = Query(default="", max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """列出用户。"""
    del admin
    statement = select(User).order_by(User.created_at.desc()).limit(limit)
    if query.strip():
        q = f"%{query.strip()}%"
        statement = (
            select(User)
            .where(or_(User.username.ilike(q), User.email.ilike(q), User.display_name.ilike(q)))
            .order_by(User.created_at.desc())
            .limit(limit)
        )
    result = await db.execute(statement)
    users = result.scalars().all()
    return {"users": [_user_to_admin_dict(user) for user in users]}


@router.patch("/users/{user_id}")
async def update_admin_user(
    user_id: str,
    req: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """更新用户角色或启停状态。"""
    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="用户不存在")

    result = await db.execute(select(User).where(User.id == uid))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.is_active is False and str(target.id) == str(admin.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能停用当前管理员账号")

    if req.role is not None and target.role == "admin" and req.role != "admin":
        await _ensure_not_last_admin(db, target.id)

    if req.is_active is False and target.role == "admin":
        await _ensure_not_last_admin(db, target.id)

    if req.role is not None:
        target.role = req.role
    if req.is_active is not None:
        target.is_active = req.is_active

    await db.commit()
    await db.refresh(target)
    return _user_to_admin_dict(target)


@router.get("/workspaces")
async def list_admin_workspaces(
    query: str = Query(default="", max_length=100),
    limit: int = Query(default=100, ge=1, le=300),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """列出项目空间治理信息。"""
    del admin
    statement = (
        select(ProjectSpace)
        .where(ProjectSpace.status != "deleted")
        .options(selectinload(ProjectSpace.members))
        .order_by(ProjectSpace.updated_at.desc())
        .limit(limit)
    )
    if query.strip():
        q = f"%{query.strip()}%"
        statement = (
            select(ProjectSpace)
            .where(ProjectSpace.status != "deleted", ProjectSpace.name.ilike(q))
            .options(selectinload(ProjectSpace.members))
            .order_by(ProjectSpace.updated_at.desc())
            .limit(limit)
        )

    result = await db.execute(statement)
    spaces = result.scalars().unique().all()
    owner_ids = [space.owner_id for space in spaces]
    owners = {}
    if owner_ids:
        owner_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
        owners = {user.id: user for user in owner_result.scalars().all()}

    return {
        "workspaces": [
            _workspace_to_admin_dict(space, owners.get(space.owner_id))
            for space in spaces
        ]
    }


@router.get("/workspaces/{space_id}")
async def get_admin_workspace_detail(
    space_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """管理员查看项目空间内容。"""
    service = WorkspaceService(db)
    detail = await service.get_space_admin_detail(space_id, admin)
    if not detail:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return detail


@router.get("/workspace-activities")
async def list_admin_workspace_activities(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    result = await db.execute(
        select(ProjectSpaceActivity)
        .order_by(desc(ProjectSpaceActivity.created_at))
        .limit(max(1, min(limit, 100)))
    )
    service = WorkspaceService(db)
    return {"activities": await service.activities_to_dict(result.scalars().all())}


async def _ensure_not_last_admin(db: AsyncSession, target_user_id) -> None:
    result = await db.execute(
        select(func.count(User.id)).where(
            User.role == "admin",
            User.is_active.is_(True),
            User.id != target_user_id,
        )
    )
    remaining_admins = int(result.scalar() or 0)
    if remaining_admins == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除最后一个活跃管理员")


def _user_to_admin_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "avatar": user.avatar,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else "",
        "updated_at": user.updated_at.isoformat() if user.updated_at else "",
    }


def _workspace_to_admin_dict(space: ProjectSpace, owner: Optional[User]) -> dict:
    role_counts = _workspace_role_counts(space)
    return {
        "id": str(space.id),
        "name": space.name,
        "description": space.description or "",
        "status": space.status,
        "owner": _user_to_admin_dict(owner) if owner else None,
        "member_count": len(space.members or []),
        "role_counts": role_counts,
        "created_at": space.created_at.isoformat() if space.created_at else "",
        "updated_at": space.updated_at.isoformat() if space.updated_at else "",
    }


def _workspace_role_counts(space: ProjectSpace) -> dict:
    counts = {"owner": 0, "editor": 0, "viewer": 0}
    for member in space.members or []:
        counts[member.role] = counts.get(member.role, 0) + 1
    return counts


def _overview_risk_hints(counts: dict) -> list[str]:
    hints = []
    if counts.get("admins", 0) <= 1:
        hints.append("当前只有 1 个管理员，建议至少保留 2 个管理员账号用于应急。")
    if counts.get("project_spaces", 0) == 0:
        hints.append("还没有项目空间，团队协作能力尚未真正启用。")
    return hints
