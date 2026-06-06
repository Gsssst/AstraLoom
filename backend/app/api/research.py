"""科研 Pipeline API — 项目管理、Idea 工作台、讨论、代码生成。"""

import asyncio
import json
import logging
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.research import ResearchProject, ResearchIdea, ResearchIdeaRun
from app.db.models.paper import Folder, PaperFolderItem
from app.services.research_service import ResearchPipelineService
from app.services.research_idea_workbench import ResearchIdeaWorkbenchService
from app.services.writing_project_service import WritingProjectService
from app.services.workspace_service import WorkspaceService
from app.services.digest_service import DigestService, ExperimentService, ShareService
from app.services.paper_ingestion import PaperIngestionService
from app.services.paper_search import PaperResult
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["科研"])


# --- Authorization helpers ---

def _parse_uuid(value: str, field_name: str):
    from uuid import UUID
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


async def _get_owned_project(db: AsyncSession, project_id: str, user) -> ResearchProject:
    pid = _parse_uuid(project_id, "project_id")
    result = await db.execute(
        select(ResearchProject).where(
            ResearchProject.id == pid,
            ResearchProject.user_id == user.id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")
    return project


async def _get_workspace_accessible_project(
    db: AsyncSession,
    project_id: str,
    user,
    *,
    require_editor: bool = False,
) -> ResearchProject:
    pid = _parse_uuid(project_id, "project_id")
    result = await db.execute(
        select(ResearchProject)
        .where(ResearchProject.id == pid)
        .options(selectinload(ResearchProject.ideas))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")
    if project.user_id == user.id:
        return project

    workspace = WorkspaceService(db)
    role = await workspace.resource_role_for_user(user.id, "research_projects", str(project.id))
    if require_editor and not workspace.role_can_edit_resource(role):
        raise HTTPException(status_code=403, detail="需要项目空间 editor 或 owner 权限")
    if not require_editor and not workspace.role_can_read_resource(role):
        raise HTTPException(status_code=404, detail="项目未找到")
    return project


async def _get_owned_idea(db: AsyncSession, idea_id: str, user) -> ResearchIdea:
    iid = _parse_uuid(idea_id, "idea_id")
    result = await db.execute(
        select(ResearchIdea)
        .join(ResearchProject, ResearchIdea.project_id == ResearchProject.id)
        .where(
            ResearchIdea.id == iid,
            ResearchProject.user_id == user.id,
        )
    )
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea 未找到")
    return idea


async def _get_owned_run(db: AsyncSession, run_id: str, user) -> ResearchIdeaRun:
    rid = _parse_uuid(run_id, "run_id")
    result = await db.execute(
        select(ResearchIdeaRun)
        .join(ResearchProject, ResearchIdeaRun.project_id == ResearchProject.id)
        .where(
            ResearchIdeaRun.id == rid,
            ResearchProject.user_id == user.id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Idea 工作台运行未找到")
    return run


# --- Models ---

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    paper_ids: Optional[List[str]] = None
    collection_ids: Optional[List[str]] = None


class IdeaBrief(BaseModel):
    id: str
    title: str
    description: Optional[str]
    feasibility_score: Optional[float]
    novelty_score: Optional[float]
    status: str
    generation_run_id: Optional[str] = None
    parent_idea_id: Optional[str] = None
    hypothesis: Optional[str] = None
    approach: Optional[str] = None
    novelty: Optional[str] = None
    referenced_papers: Optional[dict] = None
    evidence_json: Optional[dict] = None
    review_json: Optional[dict] = None
    experiment_plan: Optional[dict] = None
    evolution_json: Optional[dict] = None
    generated_code: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    keywords: Optional[list]
    paper_ids: Optional[list] = None
    status: str
    ideas_count: int = 0
    ideas: list[IdeaBrief] = []
    created_at: str

    model_config = {"from_attributes": True}


class IdeaResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str]
    feasibility_score: Optional[float]
    novelty_score: Optional[float]
    status: str
    referenced_papers: Optional[dict]
    generation_run_id: Optional[str] = None
    parent_idea_id: Optional[str] = None
    hypothesis: Optional[str] = None
    approach: Optional[str] = None
    novelty: Optional[str] = None
    evidence_json: Optional[dict] = None
    review_json: Optional[dict] = None
    experiment_plan: Optional[dict] = None
    evolution_json: Optional[dict] = None
    generated_code: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class GenerateIdeasRequest(BaseModel):
    num_ideas: int = Field(default=3, ge=1, le=5)
    external_search: bool = True


class IdeaRunResponse(BaseModel):
    id: str
    project_id: str
    status: str
    stage: str
    progress: int
    message: Optional[str] = None
    config_json: Optional[dict] = None
    evidence_map: Optional[dict] = None
    gap_map: Optional[dict] = None
    candidate_pool: Optional[list] = None
    review_summary: Optional[dict] = None
    error: Optional[str] = None
    ideas: list[IdeaResponse] = []
    created_at: str


class DiscussRequest(BaseModel):
    message: str = Field(..., description="用户消息")


class DiscussResponse(BaseModel):
    reply: str
    discussion_log: Optional[list] = None


class CodeGenResponse(BaseModel):
    code: str
    idea_id: str


class IdeaDecisionRequest(BaseModel):
    status: str = Field(..., pattern="^(draft|pinned|rejected)$")


class IdeaCompareRequest(BaseModel):
    idea_ids: List[str] = Field(..., min_length=2, max_length=4)


class IdeaEvolveRequest(BaseModel):
    focus: str = Field(default="", max_length=1000)


class ExternalEvidenceImportRequest(BaseModel):
    paper_id: str = Field(..., min_length=1)
    auto_download: bool = True


class FeedbackEvolveRequest(BaseModel):
    experiment_id: str = Field(..., min_length=1)
    focus: str = Field(default="", max_length=1000)


class WritingDraftResponse(BaseModel):
    project: dict
    evidence_status: str
    evidence_count: int
    local_paper_count: int


def _idea_response(idea: ResearchIdea) -> IdeaResponse:
    return IdeaResponse(
        id=str(idea.id),
        project_id=str(idea.project_id),
        generation_run_id=str(idea.generation_run_id) if idea.generation_run_id else None,
        parent_idea_id=str(idea.parent_idea_id) if idea.parent_idea_id else None,
        title=idea.title,
        description=idea.description,
        hypothesis=idea.hypothesis,
        approach=idea.approach,
        novelty=idea.novelty,
        feasibility_score=idea.feasibility_score,
        novelty_score=idea.novelty_score,
        status=idea.status,
        referenced_papers=idea.referenced_papers,
        evidence_json=idea.evidence_json,
        review_json=idea.review_json,
        experiment_plan=idea.experiment_plan,
        evolution_json=idea.evolution_json,
        generated_code=idea.generated_code,
        created_at=idea.created_at.isoformat() if idea.created_at else "",
    )


def _idea_brief(idea: ResearchIdea) -> IdeaBrief:
    response = _idea_response(idea)
    return IdeaBrief(**response.model_dump(exclude={"project_id"}))


def _run_response(run: ResearchIdeaRun, ideas: Optional[list[ResearchIdea]] = None) -> IdeaRunResponse:
    persisted_ideas = ideas if ideas is not None else run.__dict__.get("ideas", [])
    return IdeaRunResponse(
        id=str(run.id),
        project_id=str(run.project_id),
        status=run.status,
        stage=run.stage,
        progress=run.progress,
        message=run.message,
        config_json=run.config_json,
        evidence_map=run.evidence_map,
        gap_map=run.gap_map,
        candidate_pool=run.candidate_pool,
        review_summary=run.review_summary,
        error=run.error,
        ideas=[_idea_response(idea) for idea in (persisted_ideas or [])],
        created_at=run.created_at.isoformat() if run.created_at else "",
    )


def _stream_event(event_type: str, data: Any = None) -> str:
    payload = {"type": event_type}
    if isinstance(data, dict):
        payload.update(data)
    elif data is not None:
        payload["data"] = data
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# --- API ---

async def _resolve_seed_collections(db: AsyncSession, user, collection_ids: Optional[List[str]]) -> list[dict[str, Any]]:
    if not collection_ids:
        return []
    from uuid import UUID
    resolved = []
    seen = set()
    for raw_id in collection_ids:
        if raw_id in seen:
            continue
        seen.add(raw_id)
        try:
            folder_id = UUID(raw_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid collection_id")
        folder = (await db.execute(
            select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id)
        )).scalar_one_or_none()
        if not folder:
            raise HTTPException(status_code=404, detail="论文分类未找到")
        paper_result = await db.execute(
            select(PaperFolderItem.paper_id)
            .where(PaperFolderItem.folder_id == folder.id, PaperFolderItem.user_id == user.id)
            .order_by(PaperFolderItem.created_at.desc())
        )
        resolved.append({
            "id": str(folder.id),
            "name": folder.name,
            "paper_ids": [str(pid) for pid in paper_result.scalars().all()],
        })
    return resolved

@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    req: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建研究方向项目。"""
    seed_collections = await _resolve_seed_collections(db, current_user, req.collection_ids)
    collection_paper_ids = [
        paper_id
        for collection in seed_collections
        for paper_id in collection.get("paper_ids", [])
    ]
    paper_ids = list(dict.fromkeys([*(req.paper_ids or []), *collection_paper_ids]))
    project = ResearchProject(
        name=req.name,
        description=req.description,
        keywords=req.keywords,
        paper_ids=paper_ids,
        metadata_json={"seed_collections": seed_collections} if seed_collections else None,
        user_id=current_user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        keywords=project.keywords,
        status=project.status,
        created_at=project.created_at.isoformat() if project.created_at else "",
    )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """列出当前用户的研究方向。"""
    result = await db.execute(
        select(ResearchProject)
        .where(ResearchProject.user_id == current_user.id)
        .options(selectinload(ResearchProject.ideas))
        .order_by(ResearchProject.created_at.desc())
    )
    projects = result.scalars().all()

    return [
        ProjectResponse(
            id=str(p.id),
            name=p.name,
            description=p.description,
            keywords=p.keywords,
            status=p.status,
            ideas_count=len(p.ideas) if p.ideas else 0,
            ideas=[
                _idea_brief(i)
                for i in (p.ideas or [])
            ],
            created_at=p.created_at.isoformat() if p.created_at else "",
        )
        for p in projects
    ]


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """获取研究方向详情。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        keywords=project.keywords,
        paper_ids=project.paper_ids,
        status=project.status,
        ideas_count=len(project.ideas) if project.ideas else 0,
        ideas=[
            _idea_brief(i)
            for i in (project.ideas or [])
        ],
        created_at=project.created_at.isoformat() if project.created_at else "",
    )


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """删除研究方向及其所有 Idea。"""
    project = await _get_owned_project(db, project_id, current_user)
    project_name = project.name

    await db.delete(project)
    await db.commit()
    return {"deleted": True, "name": project_name}


@router.get("/projects/{project_id}/recommended-papers")
async def get_recommended_papers(project_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """获取推荐的论文（异步，不阻塞页面加载）。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user)
    from app.services.paper_selection import PaperSelectionService
    selector = PaperSelectionService(db)
    papers = await selector.select_papers(
        topic_name=project.name, topic_description=project.description or "",
        keywords=project.keywords, manual_paper_ids=project.paper_ids, max_papers=8,
    )
    return [{"id": str(p.id) if hasattr(p, 'id') else f"ext:{p.arxiv_id}", "title": p.title, "year": p.year, "arxiv_id": p.arxiv_id, "source": src, "score": round(score, 3)} for p, score, src in papers]


@router.post("/projects/{project_id}/generate-ideas", response_model=List[IdeaResponse])
async def generate_ideas(
    project_id: str,
    req: GenerateIdeasRequest = GenerateIdeasRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """兼容入口：通过新的证据驱动工作台生成创新 Idea。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user, require_editor=True)

    service = ResearchIdeaWorkbenchService(db)
    try:
        run = await service.create_run(project, num_ideas=req.num_ideas, external_search=req.external_search)
        ideas = await service.execute(project, run, num_ideas=req.num_ideas)
        return [_idea_response(idea) for idea in ideas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Idea 生成失败: {str(e)}")


@router.post("/projects/{project_id}/idea-runs", response_model=IdeaRunResponse, status_code=201)
async def create_idea_run(
    project_id: str,
    req: GenerateIdeasRequest = GenerateIdeasRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建并同步执行一次可恢复的 Idea 工作台运行。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user, require_editor=True)
    service = ResearchIdeaWorkbenchService(db)
    run = await service.create_run(project, num_ideas=req.num_ideas, external_search=req.external_search)
    ideas = await service.execute(project, run, num_ideas=req.num_ideas)
    return _run_response(run, ideas)


@router.post("/projects/{project_id}/idea-runs/stream")
async def create_idea_run_stream(
    project_id: str,
    req: GenerateIdeasRequest = GenerateIdeasRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建 Idea 工作台运行，并以 SSE 返回阶段和中间产物。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user, require_editor=True)
    service = ResearchIdeaWorkbenchService(db)
    run = await service.create_run(project, num_ideas=req.num_ideas, external_search=req.external_search)

    async def generate():
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def push(event: dict[str, Any]) -> None:
            await queue.put(event)

        async def execute() -> None:
            try:
                ideas = await service.execute(project, run, num_ideas=req.num_ideas, on_progress=push)
                await queue.put({"type": "done", "run": _run_response(run, ideas).model_dump(), "ideas": [_idea_response(idea).model_dump() for idea in ideas]})
            except Exception:
                await queue.put({"type": "done", "run": _run_response(run).model_dump(), "ideas": []})

        task = asyncio.create_task(execute())
        try:
            yield _stream_event("run", {"run": _run_response(run).model_dump()})
            while True:
                event = await queue.get()
                yield _stream_event(event.get("type", "message"), event)
                if event.get("type") == "done":
                    break
        finally:
            await task

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/projects/{project_id}/idea-runs/latest", response_model=Optional[IdeaRunResponse])
async def get_latest_idea_run(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前项目最近一次 Idea 工作台运行。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user)
    result = await db.execute(
        select(ResearchIdeaRun)
        .where(ResearchIdeaRun.project_id == project.id)
        .order_by(ResearchIdeaRun.created_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    return _run_response(run) if run else None


@router.get("/idea-runs/{run_id}", response_model=IdeaRunResponse)
async def get_idea_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取一个项目所有者可访问的 Idea 工作台运行。"""
    run = await _get_owned_run(db, run_id, current_user)
    return _run_response(run)


@router.post("/projects/{project_id}/evidence/import")
async def import_external_evidence(
    project_id: str,
    req: ExternalEvidenceImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """将最近工作台运行中的外部论文一键入库并关联当前项目。"""
    project = await _get_owned_project(db, project_id, current_user)
    result = await db.execute(
        select(ResearchIdeaRun)
        .where(ResearchIdeaRun.project_id == project.id)
        .order_by(ResearchIdeaRun.created_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run or not run.evidence_map:
        raise HTTPException(status_code=404, detail="未找到可入库的证据地图")

    evidence_map = dict(run.evidence_map)
    matched = None
    for category in ("seed", "background", "inspiration"):
        for item in evidence_map.get(category, []):
            if item.get("paper_id") == req.paper_id:
                matched = item
                break
        if matched:
            break
    if not matched or not str(matched.get("paper_id", "")).startswith("ext:"):
        raise HTTPException(status_code=404, detail="外部证据未找到")

    paper_result = PaperResult(
        title=matched.get("title") or "Untitled external evidence",
        authors=[],
        abstract=matched.get("abstract_excerpt") or "",
        year=matched.get("year"),
        arxiv_id=matched.get("arxiv_id"),
        doi=matched.get("doi"),
        source=matched.get("source") or "external",
        source_url=matched.get("source_url"),
    )
    paper, is_new = await PaperIngestionService(db).ingest_paper(paper_result, auto_download=req.auto_download)
    if not paper:
        raise HTTPException(status_code=500, detail="论文入库失败")

    local_paper_id = str(paper.id)
    paper_ids = list(project.paper_ids or [])
    if local_paper_id not in paper_ids:
        paper_ids.append(local_paper_id)
        project.paper_ids = paper_ids
    for category in ("seed", "background", "inspiration"):
        evidence_map[category] = [
            {**item, "imported_paper_id": local_paper_id} if item.get("paper_id") == req.paper_id else item
            for item in evidence_map.get(category, [])
        ]
    run.evidence_map = evidence_map
    await db.commit()
    return {"paper_id": req.paper_id, "local_paper_id": local_paper_id, "is_new": is_new}


@router.post("/ideas/compare", response_model=List[IdeaResponse])
async def compare_ideas(
    req: IdeaCompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回同一用户可访问 Proposal 的结构化并排比较数据。"""
    idea_ids = list(dict.fromkeys(_parse_uuid(value, "idea_id") for value in req.idea_ids))
    if len(idea_ids) < 2:
        raise HTTPException(status_code=400, detail="至少选择两个不同的 Proposal")
    result = await db.execute(
        select(ResearchIdea)
        .join(ResearchProject, ResearchIdea.project_id == ResearchProject.id)
        .where(
            ResearchIdea.id.in_(idea_ids),
            ResearchProject.user_id == current_user.id,
        )
    )
    ideas = list(result.scalars().all())
    if len(ideas) != len(idea_ids):
        raise HTTPException(status_code=404, detail="Proposal 未找到")
    idea_by_id = {idea.id: idea for idea in ideas}
    return [_idea_response(idea_by_id[idea_id]) for idea_id in idea_ids]


@router.get("/ideas/{idea_id}", response_model=IdeaResponse)
async def get_idea(idea_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """获取 Idea 详情。"""
    idea = await _get_owned_idea(db, idea_id, current_user)

    return _idea_response(idea)


@router.get("/ideas/{idea_id}/validation", response_model=dict[str, Any])
async def validate_idea(idea_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """返回 Proposal 推进前验证闭环：撞车风险、证据缺口、实验清单和写作准备度。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    project = await _get_owned_project(db, str(idea.project_id), current_user)
    return ResearchIdeaWorkbenchService(db).validate_idea(idea, project)


@router.get("/ideas/{idea_id}/execution-pack", response_model=dict[str, Any])
async def get_idea_execution_pack(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回 Proposal 到实验反馈的推进包：最小实验、成功指标、风险、反馈和下一步。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    project = await _get_owned_project(db, str(idea.project_id), current_user)
    experiments = await ExperimentService(db).get_experiments(str(project.id))
    return ResearchIdeaWorkbenchService(db).build_experiment_execution_pack(
        idea,
        project,
        experiments=experiments,
    )


@router.post("/ideas/{idea_id}/writing-draft", response_model=WritingDraftResponse, status_code=201)
async def create_writing_draft_from_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """从一个证据驱动 Proposal 创建写作草稿。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    project = await _get_owned_project(db, str(idea.project_id), current_user)
    result = await WritingProjectService(db).create_review_draft_from_research_idea(
        user_id=str(current_user.id),
        research_project=project,
        idea=idea,
    )
    return WritingDraftResponse(**result)


@router.get("/ideas/{idea_id}/lineage", response_model=List[IdeaResponse])
async def get_idea_lineage(idea_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """返回当前 Proposal 的祖先和后代版本。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    result = await db.execute(select(ResearchIdea).where(ResearchIdea.project_id == idea.project_id))
    project_ideas = list(result.scalars().all())
    by_id = {item.id: item for item in project_ideas}
    children: dict[Any, list[ResearchIdea]] = {}
    for item in project_ideas:
        if item.parent_idea_id:
            children.setdefault(item.parent_idea_id, []).append(item)

    ancestors = []
    cursor = idea
    while cursor.parent_idea_id and cursor.parent_idea_id in by_id:
        cursor = by_id[cursor.parent_idea_id]
        ancestors.append(cursor)

    descendants = []
    queue = list(children.get(idea.id, []))
    while queue:
        child = queue.pop(0)
        descendants.append(child)
        queue.extend(children.get(child.id, []))
    return [_idea_response(item) for item in [*reversed(ancestors), idea, *descendants]]


@router.patch("/ideas/{idea_id}/decision", response_model=IdeaResponse)
async def update_idea_decision(
    idea_id: str,
    req: IdeaDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """收藏、淘汰或恢复一个 Proposal。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    if idea.status not in {"draft", "pinned", "rejected"}:
        raise HTTPException(status_code=409, detail="已进入实施阶段的 Proposal 不支持修改筛选状态")
    idea.status = req.status
    await db.commit()
    await db.refresh(idea)
    return _idea_response(idea)


@router.post("/ideas/{idea_id}/evolve", response_model=IdeaResponse, status_code=201)
async def evolve_idea(
    idea_id: str,
    req: IdeaEvolveRequest = IdeaEvolveRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """根据评审反馈和用户关注点创建一个可追溯的 Proposal 子版本。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    if idea.status not in {"draft", "pinned"}:
        raise HTTPException(status_code=409, detail="仅待筛选或已收藏的 Proposal 可以继续演化")
    project = await _get_owned_project(db, str(idea.project_id), current_user)
    service = ResearchIdeaWorkbenchService(db)
    try:
        child = await service.evolve_idea(idea, project, focus=req.focus.strip())
        return _idea_response(child)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Proposal 演化失败: {str(exc)}")


@router.post("/ideas/{idea_id}/discuss", response_model=DiscussResponse)
async def discuss_idea(
    idea_id: str,
    req: DiscussRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """与 AI 讨论细化 Idea。"""
    idea = await _get_owned_idea(db, idea_id, current_user)

    service = ResearchPipelineService(db)
    history = idea.discussion_log or []
    reply = await service.discuss_idea(idea, req.message, history[-10:] if len(history) > 10 else history)

    return DiscussResponse(reply=reply, discussion_log=idea.discussion_log)


@router.post("/ideas/{idea_id}/generate-code", response_model=CodeGenResponse)
async def generate_code(
    idea_id: str,
    framework: str = Query(default="pytorch", description="深度学习框架"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """为 Idea 生成实验代码。"""
    idea = await _get_owned_idea(db, idea_id, current_user)

    service = ResearchPipelineService(db)
    try:
        code = await service.generate_code(idea, framework=framework)
        return CodeGenResponse(code=code, idea_id=idea_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码生成失败: {str(e)}")


@router.delete("/ideas/{idea_id}")
async def delete_idea(idea_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """删除 Idea。"""
    idea = await _get_owned_idea(db, idea_id, current_user)

    await db.delete(idea)
    await db.commit()
    return {"deleted": True}


# --- arXiv 每日推送 ---

class DigestRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=1, description="关注的关键词列表")


@router.post("/arxiv-digest")
async def get_arxiv_digest(req: DigestRequest, db: AsyncSession = Depends(get_db)):
    """获取每日 arXiv 摘要。"""
    service = DigestService(db)
    papers = await service.fetch_daily_papers(req.keywords)
    summary = await service.generate_digest(req.keywords)
    return {"summary": summary, "papers": papers, "date": str(__import__("datetime").datetime.utcnow().date())}


# --- 实验记录 ---

class LogExperimentRequest(BaseModel):
    project_id: str
    idea_id: Optional[str] = None
    name: str = Field(..., description="实验名称")
    hyperparams: dict = Field(default_factory=dict)
    dataset: str = ""
    results: dict = Field(default_factory=dict)
    notes: str = ""


@router.post("/experiments")
async def log_experiment(req: LogExperimentRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """记录实验。"""
    project = await _get_owned_project(db, req.project_id, current_user)
    if req.idea_id:
        idea = await _get_owned_idea(db, req.idea_id, current_user)
        if idea.project_id != project.id:
            raise HTTPException(status_code=400, detail="Proposal 不属于当前项目")
    service = ExperimentService(db)
    try:
        return await service.log_experiment(req.project_id, req.name, req.hyperparams, req.dataset, req.results, req.notes, req.idea_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/experiments")
async def get_experiments(project_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """获取实验记录。"""
    await _get_owned_project(db, project_id, current_user)
    service = ExperimentService(db)
    return await service.get_experiments(project_id)


@router.post("/ideas/{idea_id}/evolve-from-feedback", response_model=IdeaResponse, status_code=201)
async def evolve_idea_from_feedback(
    idea_id: str,
    req: FeedbackEvolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """将已记录的实验结果作为下一轮 Proposal 演化输入。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    if idea.status not in {"draft", "pinned"}:
        raise HTTPException(status_code=409, detail="仅待筛选或已收藏的 Proposal 可以继续演化")
    project = await _get_owned_project(db, str(idea.project_id), current_user)
    experiments = await ExperimentService(db).get_experiments(str(project.id))
    feedback = next((item for item in experiments if item.get("experiment_id") == req.experiment_id), None)
    if not feedback or feedback.get("idea_id") != str(idea.id):
        raise HTTPException(status_code=404, detail="未找到绑定当前 Proposal 的实验反馈")
    try:
        child = await ResearchIdeaWorkbenchService(db).evolve_idea(
            idea,
            project,
            focus=req.focus.strip(),
            experiment_feedback=feedback,
        )
        return _idea_response(child)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"反馈演化失败: {str(exc)}")


# --- 研究分享 ---

@router.post("/projects/{project_id}/share")
async def share_project(project_id: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """生成研究分享链接。"""
    await _get_owned_project(db, project_id, current_user)
    service = ShareService(db)
    try:
        token = await service.generate_share_link(project_id)
        return {"share_token": token, "share_url": f"/share/{token}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/share/{token}")
async def view_shared(token: str, db: AsyncSession = Depends(get_db)):
    """查看分享的研究内容。"""
    service = ShareService(db)
    data = await service.get_shared_project(token)
    if not data:
        raise HTTPException(status_code=404, detail="分享链接无效")
    return data
