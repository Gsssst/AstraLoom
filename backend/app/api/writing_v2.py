"""写作助手 V2 API — Pipeline、项目管理、Diff 润色、引用验证、LaTeX 导入。"""

import json
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.core.security import get_current_user, get_optional_user
from app.services.llm import llm_service
from app.services.writing_pipeline import WritingPipeline
from app.services.diff_engine import diff_engine, PolishVersionManager
from app.services.citation_verifier import citation_verifier
from app.services.smart_citation_service import smart_citation_service
from app.services.latex_processor import latex_processor
from app.services.writing_project_service import WritingProjectService
from app.services.writing_service import WritingAssistantService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/writing", tags=["写作 V2"])


# ============== Request/Response Models ==============

class PipelineRequest(BaseModel):
    task_type: str = Field(..., description="任务类型: polish, abstract, related_work, literature_review, compare_papers, grant_write, full_chapter")
    input_data: dict = Field(default_factory=dict, description="任务输入参数")
    phases: Optional[List[str]] = None
    show_thinking: bool = Field(default=False, description="是否展示思考过程")


class DiffPolishRequest(BaseModel):
    text: str = Field(..., description="需要润色的文本")
    style: str = Field(default="academic", description="润色风格")


class DiffActionRequest(BaseModel):
    hunks: List[dict] = Field(..., description="Diff hunks 列表")
    accept_indices: Optional[List[int]] = None
    reject_indices: Optional[List[int]] = None


class CitationVerifyRequest(BaseModel):
    answer: str = Field(..., description="AI 回复文本")


class ProjectCreateRequest(BaseModel):
    title: str = Field(..., max_length=300)
    description: str = ""
    template_type: str = Field(default="blank")
    writing_type: str = Field(default="paper")
    research_project_id: Optional[str] = None
    collection_ids: List[str] = Field(default_factory=list)
    target_venue: str = ""
    target_year: str = ""


class ReviewDraftRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=300)
    max_papers: int = Field(default=8, ge=1, le=20)
    language: str = Field(default="chinese")


class SectionUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    order: Optional[int] = None


class SmartCitationRequest(BaseModel):
    text: str = Field(..., description="写作段落文本")


class CitationMatchRequest(BaseModel):
    sentence: str = Field(..., min_length=1, description="需要校验引用支撑的句子")
    paper_id: Optional[str] = Field(default=None, description="本地论文 ID")
    arxiv_id: Optional[str] = Field(default=None, description="arXiv ID")
    title: Optional[str] = Field(default=None, description="引用论文标题")


class SectionCitationCheckRequest(BaseModel):
    section_id: Optional[str] = Field(default=None, description="章节 ID")
    text: str = Field(..., description="需要校验引用的章节文本")


# ============== Pipeline 流式端点 ==============

@router.post("/pipeline/stream")
async def pipeline_stream(req: PipelineRequest):
    """SSE 流式 Pipeline 执行 — 所有 V2 写作任务的核心端点。"""
    pipeline = WritingPipeline(llm_service, AsyncSessionLocal)

    async def generate():
        async for event in pipeline.run(
            task_type=req.task_type,
            input_data=req.input_data,
            phases=req.phases,
        ):
            yield event.to_sse()
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============== Diff 润色 ==============

@router.post("/polish/diff")
async def polish_with_diff(req: DiffPolishRequest):
    """润色文本并返回 diff — 支持逐条接受/拒绝和多轮迭代。"""
    from app.services.agents.writer_agent import WriterAgent

    writer = WriterAgent(llm_service)

    # 使用 Pipeline 的 WorkingMemory 来执行润色
    from app.services.writing_pipeline import WorkingMemory
    memory = WorkingMemory()
    memory.metadata["task_type"] = "polish"
    memory.metadata["input"] = {"text": req.text, "style": req.style}

    polished = ""
    async for event in writer.execute(memory):
        if event.type == "content" and event.phase == "writer":
            polished += event.content

    if not polished:
        raise HTTPException(status_code=500, detail="润色生成失败")

    # 计算 diff
    diff_data = diff_engine.compute_diff(req.text, polished)
    unified_diff = diff_engine.to_unified_diff(req.text, polished)

    return {
        "original": req.text,
        "polished": polished,
        "diff": diff_data,
        "unified_diff": unified_diff,
    }


@router.post("/polish/apply-diff")
async def apply_diff_actions(req: DiffActionRequest):
    """应用 diff 操作（接受/拒绝 hunks）。"""
    result = diff_engine.apply_hunks(req.hunks, set(req.accept_indices or []))
    return {"result": result}


@router.post("/polish/save-version")
async def save_polish_version(
    req: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """保存润色版本到数据库。"""
    manager = PolishVersionManager(AsyncSessionLocal)
    version = await manager.create_version(
        section_id=req.get("section_id", ""),
        original=req.get("original", ""),
        polished=req.get("polished", ""),
        diff_data=req.get("diff", {}),
        user_actions=req.get("user_actions"),
    )
    return version


@router.get("/polish/versions/{section_id}")
async def get_polish_versions(
    section_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取某章节的润色版本历史。"""
    manager = PolishVersionManager(AsyncSessionLocal)
    versions = await manager.get_versions(section_id)
    return {"versions": versions}


# ============== 引用验证 ==============

@router.post("/citations/verify")
async def verify_citations(req: CitationVerifyRequest):
    """验证 AI 回复中的引用真实性。"""
    import re
    # 提取引用标记 [1] [2] 等
    citation_pattern = re.compile(r'\[(\d+)\]\s*([^[]+?)(?=\[\d+\]|$)')
    citations = []
    for match in citation_pattern.finditer(req.answer):
        ref_text = match.group(2).strip()[:200]
        citations.append({"title": ref_text, "index": match.group(1)})

    if not citations:
        return {"verified": [], "status": "no_citations_found"}

    results = await citation_verifier.verify_batch(citations)
    verified = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            verified.append({"index": citations[i]["index"], "status": "error", "message": str(result)})
        else:
            result["index"] = citations[i]["index"]
            verified.append(result)

    return {"verified": verified, "total": len(verified)}


# ============== 智能引用推荐 ==============

@router.post("/citations/smart-recommend")
async def smart_citation_recommend(req: SmartCitationRequest):
    """上下文感知的智能引用推荐。"""
    smart_citation_service.db_factory = AsyncSessionLocal
    smart_citation_service.llm = llm_service
    result = await smart_citation_service.analyze_and_recommend(req.text)
    return result


@router.post("/citations/check-match")
async def check_citation_match(
    req: CitationMatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """检查引用是否存在，以及是否能支撑当前句子。"""
    from uuid import UUID
    from sqlalchemy import select
    from app.db.models.paper import Paper

    paper = None
    source = "local_library"
    if req.paper_id:
        try:
            result = await db.execute(select(Paper).where(Paper.id == UUID(req.paper_id)))
            paper = result.scalar_one_or_none()
        except ValueError:
            paper = None
    if not paper and req.arxiv_id:
        result = await db.execute(select(Paper).where(Paper.arxiv_id == req.arxiv_id))
        paper = result.scalar_one_or_none()
    if not paper and req.title:
        result = await db.execute(select(Paper).where(Paper.title.ilike(f"%{req.title[:120]}%")))
        paper = result.scalar_one_or_none()

    if paper:
        service = WritingAssistantService(db)
        match = service.score_sentence_paper_match(req.sentence, paper)
        role = service.classify_citation_role(req.sentence, paper)
        return {
            "exists": True,
            "source": source,
            "paper": {
                "id": str(paper.id),
                "title": paper.title,
                "year": paper.year,
                "arxiv_id": paper.arxiv_id,
                "doi": paper.doi,
            },
            **role,
            **match,
            "status": "matched" if match["match_status"] != "weak" else "weak_match",
        }

    verifier_result = None
    if req.title:
        verifier_result = await citation_verifier.verify(req.title, arxiv_id=req.arxiv_id or "")
    return {
        "exists": bool(verifier_result and verifier_result.get("verified")),
        "source": "external_verifier" if verifier_result else "not_found",
        "paper": None,
        "match_score": 0,
        "match_status": "weak",
        "match_label": "无法匹配",
        "match_terms": [],
        "match_explanation": "未在本地论文库中找到该引用，无法判断它是否支撑当前句子。",
        "status": "not_found",
        "verification": verifier_result,
    }


# ============== LaTeX 导入 ==============

@router.post("/latex/import")
async def import_latex_project(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导入 .tex 文件，创建写作项目。"""
    if not file.filename or not file.filename.endswith(".tex"):
        raise HTTPException(status_code=400, detail="请上传 .tex 文件")

    content = (await file.read()).decode("utf-8", errors="ignore")
    sections_raw = latex_processor.extract_sections(content)
    bib_path = latex_processor.extract_bibliography(content)

    # 自动创建写作项目
    service = WritingProjectService(db)
    project = await service.create_project(
        user_id=str(user.id),
        title=file.filename.replace(".tex", ""),
        template_type="blank",
    )

    # 将 LaTeX 章节写入项目
    for i, sec in enumerate(sections_raw):
        section_id = project["sections"][i]["id"] if i < len(project["sections"]) else None
        if not section_id:
            # 创建额外章节
            from app.db.models.writing import WritingSection
            section = WritingSection(
                project_id=project["id"],
                title=sec["title"],
                content=sec.get("content", ""),
                order=i,
            )
            db.add(section)
        else:
            await service.update_section(
                section_id=section_id,
                user_id=str(user.id),
                title=sec["title"],
                content=sec.get("content", ""),
            )

    await db.commit()

    return {
        "project": project,
        "sections_imported": len(sections_raw),
        "bib_file": bib_path,
    }


@router.post("/latex/compile-check")
async def latex_compile_check(file: UploadFile = File(...)):
    """LaTeX 编译检查。"""
    if not file.filename or not file.filename.endswith(".tex"):
        raise HTTPException(status_code=400, detail="请上传 .tex 文件")

    content = (await file.read()).decode("utf-8", errors="ignore")
    result = await latex_processor.compile_check(content)
    return result


# ============== 写作项目管理 ==============

@router.get("/projects/templates")
async def get_project_templates():
    """获取可用写作模板列表。"""
    return {"templates": WritingProjectService.get_templates()}


@router.post("/projects")
async def create_project(
    req: ProjectCreateRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建写作项目。"""
    service = WritingProjectService(db)
    has_context = bool(req.research_project_id or req.collection_ids or req.target_venue or req.target_year or req.writing_type != "paper")
    if has_context:
        try:
            return await service.create_project_from_context(
                user_id=str(user.id),
                title=req.title,
                description=req.description,
                template_type=req.template_type,
                writing_type=req.writing_type,
                research_project_id=req.research_project_id,
                collection_ids=req.collection_ids,
                target_venue=req.target_venue,
                target_year=req.target_year,
            )
        except ValueError as exc:
            detail = str(exc)
            status_code = 404 if "未找到" in detail else 400
            raise HTTPException(status_code=status_code, detail=detail)
    return await service.create_project(
        user_id=str(user.id),
        title=req.title,
        description=req.description,
        template_type=req.template_type,
    )


@router.post("/projects/from-topic")
async def create_project_from_topic(
    req: ReviewDraftRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从研究方向一键创建综述草稿项目。"""
    service = WritingProjectService(db)
    return await service.create_review_draft_from_topic(
        user_id=str(user.id),
        topic=req.topic,
        max_papers=req.max_papers,
        language=req.language,
    )


@router.get("/projects")
async def list_projects(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出用户的所有写作项目。"""
    service = WritingProjectService(db)
    return {"projects": await service.list_projects(str(user.id))}


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目详情。"""
    service = WritingProjectService(db)
    project = await service.get_project(project_id, str(user.id))
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")
    return project


@router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    req: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新项目。"""
    service = WritingProjectService(db)
    project = await service.update_project(project_id, str(user.id), **req)
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除项目。"""
    service = WritingProjectService(db)
    ok = await service.delete_project(project_id, str(user.id))
    if not ok:
        raise HTTPException(status_code=404, detail="项目未找到")
    return {"deleted": True}


@router.put("/projects/{project_id}/sections/{section_id}")
async def update_section(
    project_id: str,
    section_id: str,
    req: SectionUpdateRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新章节。"""
    service = WritingProjectService(db)
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    section = await service.update_section(section_id, str(user.id), **kwargs)
    if not section:
        raise HTTPException(status_code=404, detail="章节未找到")
    return section


@router.get("/projects/{project_id}/evidence-cards")
async def get_project_evidence_cards(
    project_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取写作项目证据卡片。"""
    service = WritingProjectService(db)
    result = await service.get_evidence_cards(project_id, str(user.id))
    if result is None:
        raise HTTPException(status_code=404, detail="项目未找到")
    return result


@router.post("/projects/{project_id}/citations/check-section")
async def check_project_section_citations(
    project_id: str,
    req: SectionCitationCheckRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查写作项目章节中的引用是否能被证据支撑。"""
    service = WritingProjectService(db)
    result = await service.check_section_citations(
        project_id=project_id,
        user_id=str(user.id),
        section_id=req.section_id,
        text=req.text,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="项目未找到")
    return result


@router.post("/projects/{project_id}/evidence-related-work-table")
async def build_project_evidence_related_work_table(
    project_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """基于项目证据卡生成 Related Work 对比表。"""
    service = WritingProjectService(db)
    result = await service.build_evidence_related_work_table(project_id, str(user.id))
    if result is None:
        raise HTTPException(status_code=404, detail="项目未找到")
    return result


@router.put("/projects/{project_id}/sections/reorder")
async def reorder_sections(
    project_id: str,
    req: dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """重排章节顺序。"""
    service = WritingProjectService(db)
    ok = await service.reorder_sections(project_id, str(user.id), req.get("section_ids", []))
    if not ok:
        raise HTTPException(status_code=400, detail="重排失败")
    return {"reordered": True}


@router.get("/projects/{project_id}/export")
async def export_project(
    project_id: str,
    format: str = Query(default="markdown", pattern="^(markdown|latex|docx|bibtex|references)$"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """多格式导出项目。"""
    service = WritingProjectService(db)
    project = await service.get_project(project_id, str(user.id))
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    if format == "markdown":
        md = await service.export_to_markdown(project_id, str(user.id))
        return {"format": "markdown", "data": md}

    elif format == "latex":
        tex = await service.export_to_latex(project_id, str(user.id))
        return {"format": "latex", "data": tex}

    elif format == "docx":
        file_stream = await service.export_to_docx_bytes(project_id, str(user.id))
        from fastapi.responses import StreamingResponse
        from datetime import datetime
        safe_title = project["title"].replace(" ", "_")[:50]
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={safe_title}_{datetime.now().strftime('%Y%m%d')}.docx"},
        )

    elif format == "bibtex":
        bibtex = await service.export_to_bibtex(project_id, str(user.id))
        return {"format": "bibtex", "data": bibtex or ""}

    elif format == "references":
        references = await service.export_reference_list(project_id, str(user.id))
        return {"format": "references", "data": references or ""}


@router.get("/projects/{project_id}/export/readiness")
async def get_project_export_readiness(
    project_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取写作项目导出预检结果。"""
    service = WritingProjectService(db)
    readiness = await service.build_export_readiness(project_id, str(user.id))
    if readiness is None:
        raise HTTPException(status_code=404, detail="项目未找到")
    return readiness


@router.get("/projects/{project_id}/workbench-summary")
async def get_project_workbench_summary(
    project_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目级写作工作台总览与下一步建议。"""
    service = WritingProjectService(db)
    summary = await service.build_workbench_summary(project_id, str(user.id))
    if summary is None:
        raise HTTPException(status_code=404, detail="项目未找到")
    return summary


@router.get("/projects/{project_id}/export/package")
async def get_project_publication_package(
    project_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取写作项目投稿导出包。"""
    service = WritingProjectService(db)
    package = await service.build_publication_package(project_id, str(user.id))
    if package is None:
        raise HTTPException(status_code=404, detail="项目未找到")
    return package


@router.post("/projects/{project_id}/submission-template")
async def bind_project_submission_template(
    project_id: str,
    venue: str = Form(default=""),
    year: str = Form(default=""),
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Inspect and bind an official/user-provided submission template to a writing project."""
    allowed_suffixes = (".tex", ".cls", ".sty", ".zip")
    filename = file.filename or "template"
    if not filename.lower().endswith(allowed_suffixes):
        raise HTTPException(status_code=400, detail="请上传 .tex、.cls、.sty 或 .zip 模板文件")
    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="模板文件过大，请上传 8MB 以内的模板包")

    inspection = latex_processor.inspect_submission_template(filename, content)
    service = WritingProjectService(db)
    project = await service.bind_submission_profile(
        project_id=project_id,
        user_id=str(user.id),
        venue=venue,
        year=year,
        template_inspection=inspection,
    )
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")
    return {
        "project": project,
        "inspection": inspection,
        "submission_profile": (project.get("metadata_json") or {}).get("submission_profile") or {},
    }


# ============== 升级现有的流行 API ==============

@router.post("/related-work-v2")
async def generate_related_work_v2(req: dict, db: AsyncSession = Depends(get_db)):
    """Related Work V2 — 使用多智能体 Pipeline（非流式包装）。"""
    pipeline = WritingPipeline(llm_service, AsyncSessionLocal)

    full_content = ""
    async for event in pipeline.run(
        task_type="related_work",
        input_data={"topic": req.get("topic", ""), "max_papers": req.get("max_papers", 5)},
    ):
        if event.type == "content":
            full_content += event.content

    return {"result": full_content}
