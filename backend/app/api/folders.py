"""文件夹管理 API。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.db.models.paper import Folder, Paper, PaperFolderItem, UserPaper
from app.core.security import get_current_user

router = APIRouter(prefix="/folders", tags=["文件夹"])

class FolderCreate(BaseModel):
    name: str = Field(..., max_length=200)
    parent_id: Optional[str] = None
    description: Optional[str] = None


class FolderPaperRequest(BaseModel):
    paper_ids: List[str] = Field(..., min_length=1, max_length=100)

class FolderResponse(BaseModel):
    id: str; name: str; parent_id: Optional[str]; children: list = []
    paper_count: int = 0
    diagnostics: Optional[dict] = None
    model_config = {"from_attributes": True}


def _readiness_from_counts(
    *,
    paper_count: int,
    full_text_count: int,
    embedding_count: int,
    read_status_counts: dict[str, int],
) -> dict:
    full_text_coverage = full_text_count / paper_count if paper_count else 0
    embedding_coverage = embedding_count / paper_count if paper_count else 0
    completed_count = read_status_counts.get("completed", 0)
    warnings = []
    if paper_count < 3:
        warnings.append("分类论文少于 3 篇，Idea 生成可能缺少对比证据")
    if full_text_coverage < 0.5:
        warnings.append("全文覆盖率偏低，模型可能只能基于摘要推断")
    if embedding_coverage < 0.5:
        warnings.append("向量覆盖率偏低，相关论文检索命中会受影响")
    if paper_count and completed_count == 0:
        warnings.append("该分类还没有已读论文，建议先完成核心论文阅读")
    return {
        "paper_count": paper_count,
        "full_text_count": full_text_count,
        "full_text_coverage": round(full_text_coverage, 3),
        "embedding_count": embedding_count,
        "embedding_coverage": round(embedding_coverage, 3),
        "read_status_counts": read_status_counts,
        "ready_for_idea": paper_count >= 3 and full_text_coverage >= 0.5 and embedding_coverage >= 0.5,
        "warnings": warnings,
    }


async def _folder_diagnostics(db: AsyncSession, folder_id, user_id) -> dict:
    result = await db.execute(
        select(Paper, UserPaper.read_status)
        .join(PaperFolderItem, PaperFolderItem.paper_id == Paper.id)
        .outerjoin(UserPaper, (UserPaper.paper_id == Paper.id) & (UserPaper.user_id == user_id))
        .where(PaperFolderItem.folder_id == folder_id, PaperFolderItem.user_id == user_id)
    )
    rows = result.all()
    paper_count = len(rows)
    full_text_count = sum(1 for paper, _status in rows if paper.full_text and len(paper.full_text) > 500)
    embedding_count = sum(1 for paper, _status in rows if paper.embedding is not None)
    read_status_counts = {"unread": 0, "reading": 0, "completed": 0}
    for _paper, status in rows:
        read_status_counts[status if status in read_status_counts else "unread"] += 1
    return _readiness_from_counts(
        paper_count=paper_count,
        full_text_count=full_text_count,
        embedding_count=embedding_count,
        read_status_counts=read_status_counts,
    )

def build_tree(folder: Folder, user_id, counts: dict | None = None, diagnostics: dict | None = None) -> dict:
    return {"id": str(folder.id), "name": folder.name, "parent_id": str(folder.parent_id) if folder.parent_id else None,
            "children": [build_tree(c, user_id, counts, diagnostics) for c in (folder.children or []) if c.user_id == user_id], "paper_count": (counts or {}).get(str(folder.id), 0),
            "diagnostics": (diagnostics or {}).get(str(folder.id))}


def _paper_brief(paper: Paper, read_status: str | None = None) -> dict:
    return {
        "id": str(paper.id),
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "abstract": paper.abstract[:500] if paper.abstract else None,
        "abstract_full": paper.abstract,
        "arxiv_id": paper.arxiv_id,
        "doi": paper.doi,
        "source": paper.source,
        "citation_count": paper.citation_count,
        "created_at": paper.created_at.isoformat() if paper.created_at else "",
        "read_status": read_status,
    }


async def _owned_folder(db: AsyncSession, folder_id: str, user) -> Folder:
    from uuid import UUID
    try:
        fid = UUID(folder_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid folder_id")
    folder = (await db.execute(
        select(Folder).where(Folder.id == fid, Folder.user_id == user.id)
    )).scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="分类未找到")
    return folder

@router.get("/", response_model=List[dict])
async def list_folders(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    stats_result = await db.execute(
        select(PaperFolderItem.folder_id, func.count(PaperFolderItem.paper_id))
        .where(PaperFolderItem.user_id == user.id)
        .group_by(PaperFolderItem.folder_id)
    )
    counts = {str(folder_id): int(count or 0) for folder_id, count in stats_result.all()}
    result = await db.execute(
        select(Folder).where(
            Folder.parent_id.is_(None),
            Folder.user_id == user.id,
        ).options(selectinload(Folder.children))
    )
    folders = result.scalars().all()
    diagnostics = {str(folder.id): await _folder_diagnostics(db, folder.id, user.id) for folder in folders}
    return [build_tree(f, user.id, counts, diagnostics) for f in folders]

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
    return {"id": str(folder.id), "name": folder.name, "paper_count": 0}


@router.get("/{folder_id}/papers")
async def list_folder_papers(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """列出某个用户分类下的论文。"""
    folder = await _owned_folder(db, folder_id, user)
    result = await db.execute(
        select(Paper, UserPaper.read_status)
        .join(PaperFolderItem, PaperFolderItem.paper_id == Paper.id)
        .outerjoin(UserPaper, (UserPaper.paper_id == Paper.id) & (UserPaper.user_id == user.id))
        .where(PaperFolderItem.folder_id == folder.id, PaperFolderItem.user_id == user.id)
        .order_by(PaperFolderItem.created_at.desc())
    )
    return [_paper_brief(paper, read_status) for paper, read_status in result.all()]


@router.get("/{folder_id}/diagnostics")
async def get_folder_diagnostics(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """获取分类覆盖率与 Idea 生成准备度。"""
    folder = await _owned_folder(db, folder_id, user)
    diagnostics = await _folder_diagnostics(db, folder.id, user.id)
    return {"folder_id": str(folder.id), "name": folder.name, **diagnostics}


@router.get("/{folder_id}/paper-ids")
async def list_folder_paper_ids(folder_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """返回分类论文 ID，用于研究方向种子论文导入。"""
    folder = await _owned_folder(db, folder_id, user)
    result = await db.execute(
        select(PaperFolderItem.paper_id)
        .where(PaperFolderItem.folder_id == folder.id, PaperFolderItem.user_id == user.id)
        .order_by(PaperFolderItem.created_at.desc())
    )
    return {"folder_id": str(folder.id), "paper_ids": [str(pid) for pid in result.scalars().all()]}


@router.post("/{folder_id}/papers")
async def add_papers_to_folder(folder_id: str, req: FolderPaperRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """把论文加入用户分类。"""
    from uuid import UUID
    folder = await _owned_folder(db, folder_id, user)
    paper_ids = []
    for raw_id in req.paper_ids:
        try:
            paper_ids.append(UUID(raw_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid paper_id")
    if not paper_ids:
        return {"added": 0, "skipped": 0}

    paper_result = await db.execute(select(Paper.id).where(Paper.id.in_(paper_ids)))
    existing_paper_ids = set(paper_result.scalars().all())
    missing = [str(pid) for pid in paper_ids if pid not in existing_paper_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"论文不存在: {', '.join(missing[:3])}")

    existing_result = await db.execute(
        select(PaperFolderItem.paper_id).where(
            PaperFolderItem.folder_id == folder.id,
            PaperFolderItem.user_id == user.id,
            PaperFolderItem.paper_id.in_(paper_ids),
        )
    )
    existing_items = set(existing_result.scalars().all())
    added = 0
    for pid in paper_ids:
        user_paper = (await db.execute(
            select(UserPaper).where(UserPaper.user_id == user.id, UserPaper.paper_id == pid)
        )).scalar_one_or_none()
        if not user_paper:
            db.add(UserPaper(user_id=user.id, paper_id=pid, saved=True))
        else:
            user_paper.saved = True
        if pid not in existing_items:
            db.add(PaperFolderItem(folder_id=folder.id, paper_id=pid, user_id=user.id))
            added += 1
    await db.commit()
    return {"folder_id": str(folder.id), "added": added, "skipped": len(paper_ids) - added}


@router.delete("/{folder_id}/papers/{paper_id}")
async def remove_paper_from_folder(folder_id: str, paper_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """从分类中移除论文，不影响论文收藏状态。"""
    from uuid import UUID
    folder = await _owned_folder(db, folder_id, user)
    try:
        pid = UUID(paper_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid paper_id")
    item = (await db.execute(
        select(PaperFolderItem).where(
            PaperFolderItem.folder_id == folder.id,
            PaperFolderItem.paper_id == pid,
            PaperFolderItem.user_id == user.id,
        )
    )).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="分类论文未找到")
    await db.delete(item)
    await db.commit()
    return {"removed": True, "folder_id": str(folder.id), "paper_id": str(pid)}

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
