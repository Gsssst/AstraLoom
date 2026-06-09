"""Research toolbox API."""

from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.models.paper import Paper
from app.db.models.toolbox import ResearchTool, ResearchToolPaper
from app.db.session import get_db

router = APIRouter(prefix="/toolbox", tags=["工具箱"])

ToolKind = Literal["algorithm", "model", "dataset", "metric", "framework", "codebase", "protocol", "other"]
ToolMaturity = Literal["mature", "experimental", "concept", "unknown"]
ToolPaperRelation = Literal["introduced", "used", "compared", "improved", "baseline", "dataset", "metric", "other"]


class ToolPaperBrief(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    source: str
    relation: ToolPaperRelation
    evidence_note: Optional[str] = None


class ResearchToolResponse(BaseModel):
    id: str
    name: str
    kind: ToolKind
    summary: Optional[str] = None
    use_cases: Optional[str] = None
    limitations: Optional[str] = None
    tags: list[str] = []
    maturity: ToolMaturity
    created_by_user_id: Optional[str] = None
    created_at: str
    updated_at: str
    papers: list[ToolPaperBrief] = []


class ResearchToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=240)
    kind: ToolKind = "algorithm"
    summary: Optional[str] = Field(default=None, max_length=4000)
    use_cases: Optional[str] = Field(default=None, max_length=4000)
    limitations: Optional[str] = Field(default=None, max_length=4000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    maturity: ToolMaturity = "unknown"


class ResearchToolUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=240)
    kind: Optional[ToolKind] = None
    summary: Optional[str] = Field(default=None, max_length=4000)
    use_cases: Optional[str] = Field(default=None, max_length=4000)
    limitations: Optional[str] = Field(default=None, max_length=4000)
    tags: Optional[list[str]] = Field(default=None, max_length=20)
    maturity: Optional[ToolMaturity] = None


class ToolPaperLinkRequest(BaseModel):
    paper_id: str
    relation: ToolPaperRelation = "used"
    evidence_note: Optional[str] = Field(default=None, max_length=2000)


class ToolListResponse(BaseModel):
    items: list[ResearchToolResponse]
    total: int


def _normalize_tags(tags: list[str] | None) -> list[str]:
    seen = set()
    normalized: list[str] = []
    for tag in tags or []:
        clean = str(tag).strip()
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(clean[:60])
    return normalized[:20]


def _tool_to_response(tool: ResearchTool) -> ResearchToolResponse:
    papers: list[ToolPaperBrief] = []
    for link in tool.paper_links or []:
        paper = getattr(link, "paper", None)
        if not paper:
            continue
        papers.append(
            ToolPaperBrief(
                id=str(paper.id),
                title=paper.title,
                year=paper.year,
                source=paper.source,
                relation=link.relation,
                evidence_note=link.evidence_note,
            )
        )
    return ResearchToolResponse(
        id=str(tool.id),
        name=tool.name,
        kind=tool.kind,
        summary=tool.summary,
        use_cases=tool.use_cases,
        limitations=tool.limitations,
        tags=tool.tags or [],
        maturity=tool.maturity,
        created_by_user_id=str(tool.created_by_user_id) if tool.created_by_user_id else None,
        created_at=tool.created_at.isoformat() if tool.created_at else "",
        updated_at=tool.updated_at.isoformat() if tool.updated_at else "",
        papers=papers,
    )


async def _get_tool(db: AsyncSession, tool_id: str) -> ResearchTool:
    try:
        parsed_id = UUID(tool_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="工具 ID 格式无效") from exc
    result = await db.execute(
        select(ResearchTool)
        .options(selectinload(ResearchTool.paper_links).selectinload(ResearchToolPaper.paper))
        .where(ResearchTool.id == parsed_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")
    return tool


@router.get("/tools", response_model=ToolListResponse)
async def list_tools(
    q: str = Query(default=""),
    kind: Optional[ToolKind] = Query(default=None),
    tag: Optional[str] = Query(default=None, max_length=60),
    maturity: Optional[ToolMaturity] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    query = select(ResearchTool).options(
        selectinload(ResearchTool.paper_links).selectinload(ResearchToolPaper.paper)
    )
    if q.strip():
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                ResearchTool.name.ilike(pattern),
                ResearchTool.summary.ilike(pattern),
                ResearchTool.use_cases.ilike(pattern),
                ResearchTool.limitations.ilike(pattern),
            )
        )
    if kind:
        query = query.where(ResearchTool.kind == kind)
    if maturity:
        query = query.where(ResearchTool.maturity == maturity)
    if tag:
        query = query.where(cast(ResearchTool.tags, String).ilike(f"%{tag.strip()}%"))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    result = await db.execute(query.order_by(ResearchTool.updated_at.desc()).offset(offset).limit(limit))
    return ToolListResponse(items=[_tool_to_response(tool) for tool in result.scalars().all()], total=total)


@router.post("/tools", response_model=ResearchToolResponse, status_code=201)
async def create_tool(
    req: ResearchToolCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tool = ResearchTool(
        name=req.name.strip(),
        kind=req.kind,
        summary=(req.summary or "").strip() or None,
        use_cases=(req.use_cases or "").strip() or None,
        limitations=(req.limitations or "").strip() or None,
        tags=_normalize_tags(req.tags),
        maturity=req.maturity,
        created_by_user_id=current_user.id,
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return _tool_to_response(tool)


@router.patch("/tools/{tool_id}", response_model=ResearchToolResponse)
async def update_tool(
    tool_id: str,
    req: ResearchToolUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    tool = await _get_tool(db, tool_id)
    data = req.model_dump(exclude_unset=True)
    for field in ("name", "summary", "use_cases", "limitations"):
        if field in data:
            value = data[field]
            setattr(tool, field, value.strip() if isinstance(value, str) and value.strip() else None)
    if "name" in data and not tool.name:
        raise HTTPException(status_code=400, detail="工具名称不能为空")
    if "kind" in data:
        tool.kind = data["kind"]
    if "maturity" in data:
        tool.maturity = data["maturity"]
    if "tags" in data:
        tool.tags = _normalize_tags(data["tags"])
    await db.commit()
    await db.refresh(tool)
    return _tool_to_response(await _get_tool(db, tool_id))


@router.delete("/tools/{tool_id}")
async def delete_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    tool = await _get_tool(db, tool_id)
    await db.delete(tool)
    await db.commit()
    return {"ok": True}


@router.post("/tools/{tool_id}/papers", response_model=ResearchToolResponse)
async def link_tool_paper(
    tool_id: str,
    req: ToolPaperLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tool = await _get_tool(db, tool_id)
    try:
        paper_id = UUID(req.paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="论文 ID 格式无效") from exc
    paper_result = await db.execute(select(Paper).where(Paper.id == paper_id))
    if not paper_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="论文不存在")

    result = await db.execute(
        select(ResearchToolPaper).where(
            ResearchToolPaper.tool_id == tool.id,
            ResearchToolPaper.paper_id == paper_id,
        )
    )
    link = result.scalar_one_or_none()
    if link:
        link.relation = req.relation
        link.evidence_note = (req.evidence_note or "").strip() or None
    else:
        db.add(
            ResearchToolPaper(
                tool_id=tool.id,
                paper_id=paper_id,
                relation=req.relation,
                evidence_note=(req.evidence_note or "").strip() or None,
                created_by_user_id=current_user.id,
            )
        )
    await db.commit()
    return _tool_to_response(await _get_tool(db, tool_id))


@router.delete("/tools/{tool_id}/papers/{paper_id}")
async def unlink_tool_paper(
    tool_id: str,
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    tool = await _get_tool(db, tool_id)
    try:
        parsed_paper_id = UUID(paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="论文 ID 格式无效") from exc
    result = await db.execute(
        select(ResearchToolPaper).where(
            ResearchToolPaper.tool_id == tool.id,
            ResearchToolPaper.paper_id == parsed_paper_id,
        )
    )
    link = result.scalar_one_or_none()
    if link:
        await db.delete(link)
        await db.commit()
    return {"ok": True}


@router.get("/papers/{paper_id}/tools", response_model=list[ResearchToolResponse])
async def list_paper_tools(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    try:
        parsed_paper_id = UUID(paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="论文 ID 格式无效") from exc
    result = await db.execute(
        select(ResearchTool)
        .join(ResearchToolPaper, ResearchToolPaper.tool_id == ResearchTool.id)
        .options(selectinload(ResearchTool.paper_links).selectinload(ResearchToolPaper.paper))
        .where(ResearchToolPaper.paper_id == parsed_paper_id)
        .order_by(ResearchTool.updated_at.desc())
    )
    return [_tool_to_response(tool) for tool in result.scalars().unique().all()]
