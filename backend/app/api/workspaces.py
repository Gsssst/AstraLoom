"""项目空间 API。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.models.chat import ChatMessage, ChatSession
from app.db.session import get_db
from app.services.llm import llm_service
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


class WorkspaceResourceRequest(BaseModel):
    resource_type: str = Field(..., description="papers, research_projects, writing_projects")
    resource_id: str = Field(..., min_length=1)
    metadata_json: Optional[dict] = None


class WorkspaceAssistantSendRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)


class WorkspaceIssueCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=8000)
    issue_type: str = Field(default="feedback", pattern="^(feedback|bug|idea|question|task)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    labels: list[str] = Field(default_factory=list, max_length=8)
    resource_reference: Optional[dict] = None


class WorkspaceIssueUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = Field(default=None, max_length=8000)
    status: Optional[str] = Field(default=None, pattern="^(open|closed)$")
    issue_type: Optional[str] = Field(default=None, pattern="^(feedback|bug|idea|question|task)$")
    priority: Optional[str] = Field(default=None, pattern="^(low|medium|high|urgent)$")
    labels: Optional[list[str]] = Field(default=None, max_length=8)
    assignee_id: Optional[str] = None
    resource_reference: Optional[dict] = None


class WorkspaceIssueCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class WorkspaceAssistantMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    references: Optional[list] = None
    created_at: str


class WorkspaceAssistantStateResponse(BaseModel):
    session_id: str
    title: str
    quick_prompts: list[str]
    messages: list[WorkspaceAssistantMessageResponse]
    references: list[dict]
    resource_summary: dict


class WorkspaceAssistantSendResponse(BaseModel):
    message: WorkspaceAssistantMessageResponse
    reply: WorkspaceAssistantMessageResponse
    session_id: str
    references: list[dict]


WORKSPACE_ASSISTANT_QUICK_PROMPTS = [
    "总结当前项目空间的研究进展，并指出最重要的下一步。",
    "分析这个项目还缺哪些论文、证据或实验支撑。",
    "基于当前空间资源，给出未来一周的研究推进计划。",
    "根据空间里的论文、方向和草稿，生成一个写作提纲。",
]


def _permission_error(exc: PermissionError):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


def _message_to_assistant_response(message: ChatMessage) -> WorkspaceAssistantMessageResponse:
    return WorkspaceAssistantMessageResponse(
        id=str(message.id),
        role=message.role,
        content=message.content,
        references=message.references,
        created_at=message.created_at.isoformat() if message.created_at else "",
    )


async def _workspace_assistant_session(
    db: AsyncSession,
    *,
    user_id,
    space_id: str,
    title: str,
) -> ChatSession:
    metadata = {"scope": "workspace", "workspace_id": str(space_id)}
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.updated_at.desc())
    )
    for session in result.scalars().unique().all():
        session_meta = session.metadata_json or {}
        if session_meta.get("scope") == metadata["scope"] and str(session_meta.get("workspace_id")) == metadata["workspace_id"]:
            return session
    session = ChatSession(
        user_id=user_id,
        title=f"{title} AI 助手",
        rag_enabled=False,
        metadata_json=metadata,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


def _assistant_llm_messages(context: str, history: list[ChatMessage], user_content: str) -> list[dict]:
    recent_history = history[-8:] if history else []
    messages: list[dict] = [{"role": "system", "content": context}]
    messages.extend({"role": item.role, "content": item.content} for item in recent_history)
    messages.append({"role": "user", "content": user_content})
    return messages


async def _workspace_assistant_messages(db: AsyncSession, session_id) -> list[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()


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


@router.get("/resource-links")
async def get_resource_workspace_links(
    resource_type: str,
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        return await service.resource_link_status(user, resource_type, resource_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


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


@router.get("/{space_id}/assistant", response_model=WorkspaceAssistantStateResponse)
async def get_workspace_assistant_state(
    space_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    access = await service.get_space_for_user(space_id, user)
    if not access:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    space, _role = access
    session = await _workspace_assistant_session(db, user_id=user.id, space_id=str(space.id), title=space.name)
    context, references, resource_summary = await service.build_assistant_context(space)
    _ = context
    messages = await _workspace_assistant_messages(db, session.id)
    return WorkspaceAssistantStateResponse(
        session_id=str(session.id),
        title=session.title,
        quick_prompts=WORKSPACE_ASSISTANT_QUICK_PROMPTS,
        messages=[_message_to_assistant_response(message) for message in messages],
        references=references,
        resource_summary=resource_summary,
    )


@router.get("/{space_id}/issues")
async def list_workspace_issues(
    space_id: str,
    status_filter: Optional[str] = None,
    issue_type: Optional[str] = None,
    priority: Optional[str] = None,
    label: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    issues = await service.list_issues(
        space_id,
        user,
        status_filter=status_filter,
        issue_type=issue_type,
        priority=priority,
        label=label,
        limit=limit,
    )
    if issues is None:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return issues


@router.post("/{space_id}/issues", status_code=status.HTTP_201_CREATED)
async def create_workspace_issue(
    space_id: str,
    req: WorkspaceIssueCreateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    issue = await service.create_issue(
        space_id,
        user,
        title=req.title,
        description=req.description,
        issue_type=req.issue_type,
        priority=req.priority,
        labels=req.labels,
        resource_reference=req.resource_reference,
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return issue


@router.get("/{space_id}/issues/{issue_id}")
async def get_workspace_issue(
    space_id: str,
    issue_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    issue = await service.get_issue_detail(space_id, issue_id, user)
    if issue is None:
        raise HTTPException(status_code=404, detail="反馈 Issue 未找到")
    return issue


@router.patch("/{space_id}/issues/{issue_id}")
async def update_workspace_issue(
    space_id: str,
    issue_id: str,
    req: WorkspaceIssueUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        issue = await service.update_issue(
            space_id,
            issue_id,
            user,
            **{key: value for key, value in req.model_dump().items() if value is not None},
        )
    except PermissionError as exc:
        _permission_error(exc)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if issue is None:
        raise HTTPException(status_code=404, detail="反馈 Issue 未找到")
    return issue


@router.post("/{space_id}/issues/{issue_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_workspace_issue_comment(
    space_id: str,
    issue_id: str,
    req: WorkspaceIssueCommentRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    comment = await service.add_issue_comment(space_id, issue_id, user, req.content)
    if comment is None:
        raise HTTPException(status_code=404, detail="反馈 Issue 未找到")
    return comment


@router.post("/{space_id}/assistant/send", response_model=WorkspaceAssistantSendResponse)
async def send_workspace_assistant_message(
    space_id: str,
    req: WorkspaceAssistantSendRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    access = await service.get_space_for_user(space_id, user)
    if not access:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    space, _role = access
    session = await _workspace_assistant_session(db, user_id=user.id, space_id=str(space.id), title=space.name)
    history = await _workspace_assistant_messages(db, session.id)
    context, references, _resource_summary = await service.build_assistant_context(space)

    user_msg = ChatMessage(session_id=session.id, role="user", content=req.content)
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    try:
        llm_messages = _assistant_llm_messages(context, history, req.content)
        reply_content = await llm_service.chat(messages=llm_messages, temperature=0.4, max_tokens=3000)
        reply_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=reply_content,
            references=references,
        )
        db.add(reply_msg)
        await db.commit()
        await db.refresh(reply_msg)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"项目空间 AI 助手调用失败: {exc}")

    return WorkspaceAssistantSendResponse(
        message=_message_to_assistant_response(user_msg),
        reply=_message_to_assistant_response(reply_msg),
        session_id=str(session.id),
        references=references,
    )


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


@router.get("/{space_id}/activities")
async def list_workspace_activities(
    space_id: str,
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    activities = await service.list_activities(space_id, user, limit=limit)
    if activities is None:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return {"activities": activities}


@router.get("/{space_id}/resource-candidates")
async def list_workspace_resource_candidates(
    space_id: str,
    resource_type: str,
    q: str = "",
    limit: int = 12,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        items = await service.search_resource_candidates(
            space_id=space_id,
            user=user,
            resource_type=resource_type,
            q=q,
            limit=limit,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if items is None:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return {"items": items}


@router.post("/{space_id}/resources")
async def link_workspace_resource(
    space_id: str,
    req: WorkspaceResourceRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        space = await service.link_resource(
            space_id,
            user,
            req.resource_type,
            req.resource_id,
            req.metadata_json,
        )
    except PermissionError as exc:
        _permission_error(exc)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not space:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return space


@router.delete("/{space_id}/resources/{resource_type}/{resource_id}")
async def unlink_workspace_resource(
    space_id: str,
    resource_type: str,
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkspaceService(db)
    try:
        space = await service.unlink_resource(space_id, user, resource_type, resource_id)
    except PermissionError as exc:
        _permission_error(exc)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not space:
        raise HTTPException(status_code=404, detail="项目空间未找到")
    return space
