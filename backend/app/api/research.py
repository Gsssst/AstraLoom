"""科研 Pipeline API — 项目管理、Idea 工作台、讨论、代码生成。"""

import asyncio
import io
import hashlib
import json
import logging
import zipfile
from typing import Any, List, Literal, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
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
    discussion_log: Optional[list] = None
    generated_code: Optional[str] = None
    generated_code_project: Optional[dict[str, Any]] = None
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
    discussion_log: Optional[list] = None
    generated_code: Optional[str] = None
    generated_code_project: Optional[dict[str, Any]] = None
    created_at: str

    model_config = {"from_attributes": True}


class GenerateIdeasRequest(BaseModel):
    num_ideas: int = Field(default=3, ge=1, le=5)
    external_search: bool = True


class GapSelectionRequest(BaseModel):
    selected_gap_titles: list[str] = Field(default_factory=list)
    blocked_gap_titles: list[str] = Field(default_factory=list)
    focus_note: str = ""


class GenerationConstraintsRequest(BaseModel):
    research_mode: Literal["balanced", "theory", "experiment", "system", "application"] = "balanced"
    risk_appetite: Literal["conservative", "balanced", "high_risk"] = "balanced"
    resource_budget: Literal["low_compute", "reproducible", "large_model"] = "reproducible"


class ContinueGapReviewRequest(BaseModel):
    num_ideas: int = Field(default=3, ge=1, le=5)
    gap_selection: GapSelectionRequest = Field(default_factory=GapSelectionRequest)
    generation_constraints: GenerationConstraintsRequest = Field(default_factory=GenerationConstraintsRequest)


class GapFeedbackRequest(BaseModel):
    title: Optional[str] = None
    limitation: Optional[str] = None
    opportunity: Optional[str] = None
    research_question: Optional[str] = None
    uncertainty: Optional[str] = None
    evidence_rationale: Optional[str] = None
    evidence_ids: Optional[list[str]] = None
    rating: Literal["strong", "promising", "weak", "reject"] = "promising"
    labels: list[Literal["valuable", "too_broad", "evidence_weak", "already_done", "misaligned", "needs_narrowing", "high_potential"]] = Field(default_factory=list)
    note: str = ""


class GapRefineRequest(BaseModel):
    focus_note: str = ""


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
    mode: Literal["mentor", "skeptic", "experiment_designer", "writer"] = "mentor"


class DiscussResponse(BaseModel):
    reply: str
    discussion_log: Optional[list] = None
    mode: str = "mentor"
    context_summary: Optional[dict[str, Any]] = None
    risks: list[str] = []
    next_actions: list[str] = []
    suggested_questions: list[str] = []
    evolution_focus: Optional[str] = None


class CodeProjectFile(BaseModel):
    path: str
    language: str = "text"
    purpose: str = ""
    content: str


class CodeProjectEntrypoint(BaseModel):
    name: str
    path: str
    command: str
    purpose: str = ""


class CodeProjectManifest(BaseModel):
    name: str
    framework: str
    summary: str
    setup: list[str] = []
    run_commands: list[str] = []
    entrypoints: list[CodeProjectEntrypoint] = []
    safety_notes: list[str] = []
    files: list[CodeProjectFile]


class CodeGenResponse(BaseModel):
    code: str
    idea_id: str
    code_project: CodeProjectManifest


class CodeProjectVersionSummary(BaseModel):
    id: str
    idea_id: str
    version: int
    project_name: str
    framework: str
    summary: Optional[str] = None
    file_count: int
    created_at: str


class CodeProjectVersionDetail(CodeProjectVersionSummary):
    code_project: CodeProjectManifest


class CodeProjectFileDiff(BaseModel):
    path: str
    status: Literal["added", "removed", "modified", "unchanged"]
    language: str = "text"
    purpose: str = ""
    before_line_count: int = 0
    after_line_count: int = 0
    before_content: Optional[str] = None
    after_content: Optional[str] = None
    diff: str = ""


class CodeProjectVersionCompareResponse(BaseModel):
    idea_id: str
    from_version: int
    to_version: int
    summary: dict[str, int]
    files: list[CodeProjectFileDiff]


class IdeaDecisionRequest(BaseModel):
    status: str = Field(..., pattern="^(draft|pinned|rejected)$")


class IdeaCompareRequest(BaseModel):
    idea_ids: List[str] = Field(..., min_length=2, max_length=4)


class IdeaEvolveRequest(BaseModel):
    focus: str = Field(default="", max_length=1000)


class IdeaDiscussEvolveRequest(BaseModel):
    focus: str = Field(default="", max_length=1000)


class ExternalEvidenceImportRequest(BaseModel):
    paper_id: str = Field(..., min_length=1)
    auto_download: bool = True


class FeedbackEvolveRequest(BaseModel):
    experiment_id: str = Field(..., min_length=1)
    focus: str = Field(default="", max_length=1000)


class IdeaTimelineEvent(BaseModel):
    id: str
    type: str
    title: str
    summary: str
    timestamp: str
    severity: str = "info"
    tags: list[str] = []
    details: dict[str, Any] = {}


class IdeaTimelineResponse(BaseModel):
    idea_id: str
    project_id: str
    title: str
    summary: dict[str, Any]
    events: list[IdeaTimelineEvent]


class ProposalBoardItem(BaseModel):
    idea_id: str
    title: str
    status: str
    label: str
    priority: int
    manual_status: str
    recommended_action: dict[str, str]
    blockers: list[str] = []
    signals: dict[str, Any]
    summary: str
    created_at: str


class ProposalBoardGroup(BaseModel):
    status: str
    label: str
    count: int
    items: list[ProposalBoardItem]


class ProposalBoardResponse(BaseModel):
    project_id: str
    summary: dict[str, Any]
    groups: list[ProposalBoardGroup]


class WritingDraftResponse(BaseModel):
    project: dict
    evidence_status: str
    evidence_count: int
    local_paper_count: int


class RelatedPaperRecommendation(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    arxiv_id: Optional[str] = None
    source: str
    score: float


class RelatedPaperRecommendationResponse(BaseModel):
    items: list[RelatedPaperRecommendation]
    cached: bool
    refreshed_at: Optional[str] = None


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
        discussion_log=idea.discussion_log or [],
        generated_code=idea.generated_code,
        generated_code_project=idea.generated_code_project,
        created_at=idea.created_at.isoformat() if idea.created_at else "",
    )


def _idea_brief(idea: ResearchIdea) -> IdeaBrief:
    response = _idea_response(idea)
    return IdeaBrief(**response.model_dump(exclude={"project_id"}))


def _code_project_version_summary(version) -> CodeProjectVersionSummary:
    return CodeProjectVersionSummary(
        id=str(version.id),
        idea_id=str(version.idea_id),
        version=version.version,
        project_name=version.project_name,
        framework=version.framework,
        summary=version.summary,
        file_count=version.file_count,
        created_at=version.created_at.isoformat() if version.created_at else "",
    )


def _code_project_version_detail(version) -> CodeProjectVersionDetail:
    summary = _code_project_version_summary(version)
    return CodeProjectVersionDetail(
        **summary.model_dump(),
        code_project=version.project_manifest,
    )


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


async def _cancel_idea_run(
    db: AsyncSession,
    run: ResearchIdeaRun,
    *,
    message: str = "已停止生成候选 Proposal",
) -> ResearchIdeaRun:
    if run.status not in {"pending", "running"}:
        return run
    run.status = "cancelled"
    run.message = message
    run.error = None
    await db.commit()
    await db.refresh(run)
    return run


def _related_paper_cache_key(project: ResearchProject) -> str:
    payload = {
        "name": project.name or "",
        "description": project.description or "",
        "keywords": sorted(str(item) for item in (project.keywords or [])),
        "paper_ids": sorted(str(item) for item in (project.paper_ids or [])),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _related_paper_cache(project: ResearchProject) -> dict[str, Any] | None:
    metadata = project.metadata_json or {}
    cache = metadata.get("related_paper_recommendations")
    return cache if isinstance(cache, dict) else None


def _serialize_related_papers(papers: list[tuple[Any, float, str]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(p.id) if getattr(p, "id", None) else f"ext:{p.arxiv_id}",
            "title": p.title,
            "year": p.year,
            "arxiv_id": p.arxiv_id,
            "source": src,
            "score": round(score, 3),
        }
        for p, score, src in papers
    ]


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


@router.get("/projects/{project_id}/recommended-papers", response_model=RelatedPaperRecommendationResponse)
async def get_recommended_papers(
    project_id: str,
    refresh: bool = Query(default=False, description="是否强制刷新推荐缓存"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取推荐的论文（异步，不阻塞页面加载）。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user)
    cache_key = _related_paper_cache_key(project)
    cache = _related_paper_cache(project)
    if not refresh and cache and cache.get("key") == cache_key and isinstance(cache.get("items"), list):
        return RelatedPaperRecommendationResponse(
            items=cache["items"],
            cached=True,
            refreshed_at=cache.get("refreshed_at"),
        )

    from app.services.paper_selection import PaperSelectionService
    selector = PaperSelectionService(db)
    papers = await selector.select_papers(
        topic_name=project.name, topic_description=project.description or "",
        keywords=project.keywords, manual_paper_ids=project.paper_ids, max_papers=8,
    )
    items = _serialize_related_papers(papers)
    from datetime import datetime, timezone

    refreshed_at = datetime.now(timezone.utc).isoformat()
    project.metadata_json = {
        **(project.metadata_json or {}),
        "related_paper_recommendations": {
            "key": cache_key,
            "items": items,
            "refreshed_at": refreshed_at,
        },
    }
    await db.commit()
    return RelatedPaperRecommendationResponse(items=items, cached=False, refreshed_at=refreshed_at)


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


@router.post("/projects/{project_id}/idea-runs/gap-preview", response_model=IdeaRunResponse, status_code=201)
async def create_gap_preview_run(
    project_id: str,
    req: GenerateIdeasRequest = GenerateIdeasRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建一次停在 Gap Map 选择阶段的工作台运行。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user, require_editor=True)
    service = ResearchIdeaWorkbenchService(db)
    run = await service.create_run(project, num_ideas=req.num_ideas, external_search=req.external_search)
    run = await service.execute_gap_preview(project, run)
    return _run_response(run)


@router.post("/projects/{project_id}/idea-runs/{run_id}/continue-from-gaps", response_model=IdeaRunResponse)
async def continue_idea_run_from_gaps(
    project_id: str,
    run_id: str,
    req: ContinueGapReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """从已预览的 Gap Map 和用户约束继续生成 Proposal。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user, require_editor=True)
    run = await _get_owned_run(db, run_id, current_user)
    if run.project_id != project.id:
        raise HTTPException(status_code=404, detail="Idea 工作台运行未找到")
    if not run.gap_map:
        raise HTTPException(status_code=400, detail="当前运行还没有可继续的 Gap Map")
    service = ResearchIdeaWorkbenchService(db)
    ideas = await service.continue_from_gap_review(
        project,
        run,
        gap_selection=req.gap_selection.model_dump(),
        generation_constraints=req.generation_constraints.model_dump(),
        num_ideas=req.num_ideas,
    )
    return _run_response(run, ideas)


@router.patch("/projects/{project_id}/idea-runs/{run_id}/gaps/{gap_index}/feedback", response_model=IdeaRunResponse)
async def update_idea_run_gap_feedback(
    project_id: str,
    run_id: str,
    gap_index: int,
    req: GapFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """保存单个 Gap Map 条目的编辑与反馈。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user, require_editor=True)
    run = await _get_owned_run(db, run_id, current_user)
    if run.project_id != project.id:
        raise HTTPException(status_code=404, detail="Idea 工作台运行未找到")
    if not run.gap_map:
        raise HTTPException(status_code=400, detail="当前运行还没有可编辑的 Gap Map")
    service = ResearchIdeaWorkbenchService(db)
    try:
        run = await service.save_gap_feedback(run, gap_index, req.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _run_response(run)


@router.post("/projects/{project_id}/idea-runs/{run_id}/gaps/{gap_index}/refine", response_model=IdeaRunResponse)
async def refine_idea_run_gap(
    project_id: str,
    run_id: str,
    gap_index: int,
    req: GapRefineRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """基于用户反馈和证据细化单个 Gap Map 条目。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user, require_editor=True)
    run = await _get_owned_run(db, run_id, current_user)
    if run.project_id != project.id:
        raise HTTPException(status_code=404, detail="Idea 工作台运行未找到")
    if not run.gap_map:
        raise HTTPException(status_code=400, detail="当前运行还没有可细化的 Gap Map")
    service = ResearchIdeaWorkbenchService(db)
    try:
        run = await service.refine_gap(project, run, gap_index, focus_note=req.focus_note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _run_response(run)


@router.post("/projects/{project_id}/idea-runs/stream")
async def create_idea_run_stream(
    project_id: str,
    request: Request,
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
            except asyncio.CancelledError:
                await _cancel_idea_run(db, run)
                await queue.put({"type": "cancelled", "run": _run_response(run).model_dump(), "ideas": []})
                raise
            except Exception:
                await queue.put({"type": "done", "run": _run_response(run).model_dump(), "ideas": []})

        task = asyncio.create_task(execute())
        try:
            yield _stream_event("run", {"run": _run_response(run).model_dump()})
            while True:
                if request and await request.is_disconnected():
                    task.cancel()
                    break
                event = await queue.get()
                yield _stream_event(event.get("type", "message"), event)
                if event.get("type") in {"done", "cancelled"}:
                    break
        finally:
            if not task.done():
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            await _cancel_idea_run(db, run)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/projects/{project_id}/idea-runs/{run_id}/cancel", response_model=IdeaRunResponse)
async def cancel_idea_run(
    project_id: str,
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """停止一个项目所有者正在运行的 Idea 工作台任务。"""
    project = await _get_workspace_accessible_project(db, project_id, current_user, require_editor=True)
    run = await _get_owned_run(db, run_id, current_user)
    if run.project_id != project.id:
        raise HTTPException(status_code=404, detail="Idea 工作台运行未找到")
    run = await _cancel_idea_run(db, run)
    return _run_response(run)


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


@router.get("/projects/{project_id}/proposal-board", response_model=ProposalBoardResponse)
async def get_project_proposal_board(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回研究方向下 Proposal 的推进状态、优先级和下一步动作看板。"""
    project = await _get_owned_project(db, project_id, current_user)
    result = await db.execute(
        select(ResearchIdea)
        .where(ResearchIdea.project_id == project.id)
        .order_by(ResearchIdea.created_at.desc())
    )
    ideas = list(result.scalars().all())
    experiments = await ExperimentService(db).get_experiments(str(project.id))
    board = ResearchPipelineService(db).build_proposal_progress_board(
        project,
        ideas,
        experiments=experiments,
    )
    return ProposalBoardResponse(**board)


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


@router.get("/ideas/{idea_id}/timeline", response_model=IdeaTimelineResponse)
async def get_idea_iteration_timeline(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回 Proposal 从创建、讨论、验证、实验反馈到版本演化的只读时间线。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    project = await _get_owned_project(db, str(idea.project_id), current_user)
    result = await db.execute(select(ResearchIdea).where(ResearchIdea.project_id == idea.project_id))
    project_ideas = list(result.scalars().all())
    experiments = await ExperimentService(db).get_experiments(str(project.id))
    timeline = ResearchPipelineService(db).build_iteration_timeline(
        idea,
        project,
        project_ideas=project_ideas,
        experiments=experiments,
    )
    return IdeaTimelineResponse(**timeline)


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
    project = await _get_owned_project(db, str(idea.project_id), current_user)

    service = ResearchPipelineService(db)
    history = idea.discussion_log or []
    result = await service.discuss_idea(
        idea,
        req.message,
        history[-10:] if len(history) > 10 else history,
        project=project,
        mode=req.mode,
    )

    return DiscussResponse(**result)


@router.post("/ideas/{idea_id}/discuss/evolve", response_model=IdeaResponse, status_code=201)
async def evolve_idea_from_discussion(
    idea_id: str,
    req: IdeaDiscussEvolveRequest = IdeaDiscussEvolveRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """把 Copilot 讨论结论转成一个可追溯 Proposal 子版本。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    if idea.status not in {"draft", "pinned"}:
        raise HTTPException(status_code=409, detail="仅待筛选或已收藏的 Proposal 可以继续演化")
    project = await _get_owned_project(db, str(idea.project_id), current_user)
    focus = req.focus.strip() or ResearchPipelineService(db).latest_copilot_evolution_focus(idea)
    if not focus:
        focus = "基于最近 Copilot 讨论，补强证据、实验设置和 Proposal 可证伪性"
    try:
        child = await ResearchIdeaWorkbenchService(db).evolve_idea(idea, project, focus=focus)
        return _idea_response(child)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Proposal 演化失败: {str(exc)}")


@router.post("/ideas/{idea_id}/generate-code", response_model=CodeGenResponse)
async def generate_code(
    idea_id: str,
    framework: str = Query(default="pytorch", description="深度学习框架"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """为 Idea 生成结构化实验代码项目包。"""
    idea = await _get_owned_idea(db, idea_id, current_user)

    service = ResearchPipelineService(db)
    try:
        code_project = await service.generate_code(idea, framework=framework)
        code = service.representative_code_from_project(code_project)
        return CodeGenResponse(code=code, idea_id=idea_id, code_project=code_project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码生成失败: {str(e)}")


@router.get("/ideas/{idea_id}/code-project/versions", response_model=list[CodeProjectVersionSummary])
async def list_code_project_versions(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """列出 Idea 的实验项目包版本历史。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    versions = await ResearchPipelineService(db).list_code_project_versions(idea)
    return [_code_project_version_summary(version) for version in versions]


@router.get("/ideas/{idea_id}/code-project/versions/compare", response_model=CodeProjectVersionCompareResponse)
async def compare_code_project_versions(
    idea_id: str,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """比较 Idea 的两个实验项目包版本。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    try:
        comparison = await ResearchPipelineService(db).compare_code_project_versions(
            idea,
            from_version=from_version,
            to_version=to_version,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="实验项目包版本不存在")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return CodeProjectVersionCompareResponse(idea_id=idea_id, **comparison)


@router.get("/ideas/{idea_id}/code-project/versions/{version_number}", response_model=CodeProjectVersionDetail)
async def get_code_project_version(
    idea_id: str,
    version_number: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """读取 Idea 的某个实验项目包版本。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    version = await ResearchPipelineService(db).get_code_project_version(idea, version_number)
    if not version:
        raise HTTPException(status_code=404, detail="实验项目包版本不存在")
    return _code_project_version_detail(version)


@router.get("/ideas/{idea_id}/code-project/download")
async def download_code_project(
    idea_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """下载 Idea 生成的实验项目包 zip。"""
    idea = await _get_owned_idea(db, idea_id, current_user)
    service = ResearchPipelineService(db)
    project = service.normalize_code_project(idea.generated_code_project, idea) if idea.generated_code_project else None
    if not project:
        raise HTTPException(status_code=404, detail="该 Proposal 还没有生成实验项目包")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        manifest = {key: value for key, value in project.items() if key != "files"}
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for file_item in project.get("files", []):
            path = service.safe_code_project_path(file_item.get("path"))
            if not path:
                continue
            archive.writestr(path, str(file_item.get("content") or ""))
    buffer.seek(0)
    filename = f"{project.get('name') or 'research-code-project'}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
