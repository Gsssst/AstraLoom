"""文件夹管理 API。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.db.models.paper import Folder, Paper
from app.core.security import get_current_user

router = APIRouter(prefix="/folders", tags=["文件夹"])

class FolderCreate(BaseModel):
    name: str = Field(..., max_length=200)
    parent_id: Optional[str] = None

class FolderResponse(BaseModel):
    id: str; name: str; parent_id: Optional[str]; children: list = []
    paper_count: int = 0
    model_config = {"from_attributes": True}

def build_tree(folder: Folder, user_id) -> dict:
    return {"id": str(folder.id), "name": folder.name, "parent_id": str(folder.parent_id) if folder.parent_id else None,
            "children": [build_tree(c, user_id) for c in (folder.children or []) if c.user_id == user_id], "paper_count": 0}

@router.get("/", response_model=List[dict])
async def list_folders(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(Folder).where(
            Folder.parent_id.is_(None),
            Folder.user_id == user.id,
        ).options(selectinload(Folder.children))
    )
    return [build_tree(f, user.id) for f in result.scalars().all()]

@router.post("/", status_code=201)
async def create_folder(req: FolderCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    from uuid import UUID
    try:
        parent_id = UUID(req.parent_id) if req.parent_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid parent_id")
    if parent_id:
        parent = (await db.execute(
            select(Folder).where(Folder.id == parent_id, Folder.user_id == user.id)
        )).scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="文件夹未找到")
    folder = Folder(name=req.name, parent_id=parent_id, user_id=user.id)
    db.add(folder); await db.commit(); await db.refresh(folder)
    return {"id": str(folder.id), "name": folder.name}

@router.delete("/{folder_id}")
async def delete_folder(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    from uuid import UUID
    try:
        fid = UUID(folder_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid folder_id")
    f = (await db.execute(
        select(Folder).where(Folder.id == fid, Folder.user_id == user.id)
    )).scalar_one_or_none()
    if not f: raise HTTPException(status_code=404, detail="文件夹未找到")
    await db.delete(f); await db.commit()
    return {"deleted": True}
