"""项目空间 API。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["项目空间"])


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    description: str = ""


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = None
    metadata_json: Optional[dict] = None


class WorkspaceMemberRequest(BaseModel):
    account: str = Field(..., min_length=1, description="用户名或邮箱")
    role: str = Field(default="viewer", pattern="^(editor|viewer)$")


def _permission_error(exc: PermissionError):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    req: WorkspaceCreateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    return await service.create_space(user, req.name, req.description)


@router.get("")
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    return {"workspaces": await service.list_spaces(user)}


@router.get("/{space_id}")
async def get_workspace(
    space_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    space = await service.get_space_detail(space_id, user)
    if not space:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return space


@router.patch("/{space_id}")
async def update_workspace(
    space_id: str,
    req: WorkspaceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        space = await service.update_space(
            space_id,
            user,
            **{key: value for key, value in req.model_dump().items() if value is not None},
        )
    except PermissionError as exc:
        _permission_error(exc)
    if not space:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return space


@router.delete("/{space_id}")
async def delete_workspace(
    space_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        deleted = await service.delete_space(space_id, user)
    except PermissionError as exc:
        _permission_error(exc)
    if deleted is None:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return {"deleted": True}


@router.post("/{space_id}/members")
async def add_workspace_member(
    space_id: str,
    req: WorkspaceMemberRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        space = await service.add_member(space_id, user, req.account, req.role)
    except PermissionError as exc:
        _permission_error(exc)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not space:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return space


@router.delete("/{space_id}/members/{user_id}")
async def remove_workspace_member(
    space_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        space = await service.remove_member(space_id, user, user_id)
    except PermissionError as exc:
        _permission_error(exc)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not space:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return space
