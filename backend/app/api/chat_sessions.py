"""多对话会话管理 API。"""

import json
import logging
from typing import Any, List, Literal, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.user import User
from app.core.security import get_current_user
from app.services.llm import OPENAI_COMPATIBLE_PROVIDER, llm_service
from app.services.rag_service import RAGService
from app.services.web_search import format_web_context, search_web_results
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat-sessions", tags=["对话会话"])


async def _extract_pdf_text(file_bytes: bytes, filename: str) -> str:
    """从 PDF 中提取文本，依次尝试多种方式。"""
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(file_bytes)
    tmp.close()
    tmp_path = tmp.name
    extracted_text = ""
    page_count = 0

    try:
        # 方式1: pdfplumber
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(tmp_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: text_parts.append(t)
            if any(t.strip() for t in text_parts):
                extracted_text = "\n\n".join(text_parts)
                logger.info(f"pdfplumber 提取: {filename} → {len(extracted_text)} 字符")
        except Exception as e:
            logger.warning(f"pdfplumber 失败: {e}")

        # 方式2: fitz
        if not extracted_text:
            try:
                import fitz
                text_parts = []
                doc = fitz.open(tmp_path)
                page_count = len(doc)
                for page in doc: text_parts.append(page.get_text())
                doc.close()
                if any(t.strip() for t in text_parts):
                    extracted_text = "\n\n".join(text_parts)
                    logger.info(f"fitz 提取: {filename} → {len(extracted_text)} 字符")
            except Exception as e:
                logger.warning(f"fitz 失败: {e}")

        # 方式3: pikepdf 修复后 fitz
        if not extracted_text:
            try:
                import pikepdf
                repaired = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                pdf = pikepdf.open(tmp_path)
                pdf.save(repaired.name)
                pdf.close()
                import fitz
                text_parts = []
                doc = fitz.open(repaired.name)
                page_count = len(doc)
                for page in doc: text_parts.append(page.get_text())
                doc.close()
                os.unlink(repaired.name)
                if any(t.strip() for t in text_parts):
                    extracted_text = "\n\n".join(text_parts)
                    logger.info(f"pikepdf 修复后提取: {filename} → {len(extracted_text)} 字符")
            except Exception as e:
                logger.warning(f"pikepdf 失败: {e}")

    finally:
        try: os.unlink(tmp_path)
        except: pass

    if extracted_text and len(extracted_text.strip()) > 100:
        return extracted_text[:50000]
    else:
        logger.error(f"PDF 提取完全失败: {filename}")
        return ""


class SessionCreate(BaseModel):
    title: str = Field(default="新对话", max_length=300)
    rag_enabled: bool = True


class SessionResponse(BaseModel):
    id: str
    title: str
    rag_enabled: bool
    message_count: int = 0
    last_message: Optional[str] = None
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    references: Optional[list] = None
    created_at: str


class ChatImageAttachment(BaseModel):
    filename: str = Field(default="image")
    mime_type: str = Field(default="image/png")
    data_url: str = Field(..., max_length=14_000_000)

    @field_validator("data_url")
    @classmethod
    def validate_data_url(cls, value: str) -> str:
        if not value.startswith("data:image/") or ";base64," not in value[:80]:
            raise ValueError("图片附件必须是 data:image/*;base64 格式")
        return value


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)
    rag_enabled: Optional[bool] = None
    extra_context: Optional[str] = Field(default=None, description="额外上下文（如文件内容），不显示在对话中")
    attachments: list[ChatImageAttachment] = Field(default_factory=list, max_length=4)
    web_search: Optional[bool] = Field(default=False, description="是否启用联网搜索")
    search_depth: Literal["quick", "standard", "deep"] = Field(default="standard", description="检索深度")
    show_thinking: bool = Field(default=False, description="是否展示思考过程")


RETRIEVAL_DEPTH_LIMITS = {
    "quick": {"rag_papers": 2, "web_results": 2, "web_queries": 1},
    "standard": {"rag_papers": 3, "web_results": 5, "web_queries": 3},
    "deep": {"rag_papers": 5, "web_results": 8, "web_queries": 5},
}

EMPTY_STREAM_FALLBACK = "⚠️ 模型本轮未返回可展示内容，请重新发送问题或稍后重试。"
INTERRUPTED_STREAM_FALLBACK = "\n\n> ⚠️ 回答生成中途出现异常，以上内容可能不完整，请重试。"


def _stream_event(event_type: str, content: Any = None) -> str:
    payload = {"type": event_type}
    if content is not None:
        payload["content"] = content
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_failure_content(full_content: str) -> tuple[str, str]:
    appended = INTERRUPTED_STREAM_FALLBACK if full_content else EMPTY_STREAM_FALLBACK
    return f"{full_content}{appended}", appended


def _image_text_fallback(attachments: list[ChatImageAttachment]) -> str:
    if not attachments:
        return ""
    names = ", ".join(item.filename for item in attachments)
    return (
        f"[图片附件: {names}]\n"
        "当前选择的模型不支持视觉图片输入，不能看到图片本体。"
        "请用户切换到 GPT-5.5（OpenAI 兼容）模型后再进行图片分析。"
    )


def _build_llm_context_for_request(
    context: list[dict[str, Any]],
    req: SendMessageRequest,
) -> list[dict[str, Any]]:
    """Attach current-turn images only when the active provider supports vision."""
    if not req.attachments:
        return context

    active_provider = llm_service.get_active_option().get("provider")
    if active_provider != OPENAI_COMPATIBLE_PROVIDER:
        fallback = _image_text_fallback(req.attachments)
        return [*context, {"role": "system", "content": fallback}] if fallback else context

    text = req.content.strip() or "请分析上传的图片。"
    content_parts: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for attachment in req.attachments:
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": attachment.data_url},
        })
    multimodal_message = {"role": "user", "content": content_parts}
    if context and context[-1].get("role") == "user" and context[-1].get("content") == req.content:
        return [*context[:-1], multimodal_message]
    return [*context, multimodal_message]


def _active_model_stream_metadata(
    *,
    rag_enabled: bool,
    web_search_enabled: bool,
    search_depth: str,
    attachments: list[ChatImageAttachment] | None = None,
) -> dict[str, Any]:
    """Return frontend-safe model metadata for the current streamed turn."""
    active_option = llm_service.get_active_option()
    provider = str(active_option.get("provider") or "")
    model = str(active_option.get("model") or "")
    label = str(active_option.get("label") or model or provider or "当前模型")
    supports_vision = provider == OPENAI_COMPATIBLE_PROVIDER
    image_count = sum(1 for item in attachments or [] if item.mime_type.startswith("image/"))

    return {
        "provider": provider,
        "label": label,
        "model": model,
        "configured": bool(active_option.get("configured")),
        "capabilities": {
            "rag": bool(rag_enabled),
            "web_search": bool(web_search_enabled),
            "thinking": bool(active_option.get("supports_thinking")),
            "vision": supports_vision,
        },
        "search_depth": search_depth,
        "image_attachments": image_count,
    }


def _retrieval_limits(search_depth: str) -> dict[str, int]:
    return RETRIEVAL_DEPTH_LIMITS.get(search_depth, RETRIEVAL_DEPTH_LIMITS["standard"])


async def _retrieval_quality_snapshot(*, rag_enabled: bool) -> dict:
    if not rag_enabled:
        return {"rag_enabled": False, "paper_count": 0, "embedding_coverage": 0.0}
    try:
        from app.services.hybrid_search import HybridSearchService

        async with AsyncSessionLocal() as session:
            service = HybridSearchService(session)
            return {
                "rag_enabled": True,
                "paper_count": await service.paper_count(),
                "embedding_coverage": round(await service.embedding_coverage(), 4),
            }
    except Exception as exc:
        logger.warning("读取检索质量状态失败: %s", exc)
        return {"rag_enabled": True, "paper_count": 0, "embedding_coverage": 0.0, "error": str(exc)}


def _retrieval_status(
    references: list[dict],
    *,
    web_search_enabled: bool,
    subject: str = "资料",
    retrieval_quality: dict | None = None,
) -> str:
    local_count = sum(reference.get("source") == "local_library" for reference in references)
    web_count = sum(reference.get("source") == "web" for reference in references)
    quality_notes: list[str] = []
    if retrieval_quality and retrieval_quality.get("rag_enabled"):
        coverage = float(retrieval_quality.get("embedding_coverage") or 0.0)
        paper_count = int(retrieval_quality.get("paper_count") or 0)
        if paper_count == 0:
            quality_notes.append("当前知识库为空")
        elif local_count == 0:
            quality_notes.append("知识库本轮未命中可引用资料")
        if 0 < paper_count and coverage < 0.8:
            quality_notes.append(f"向量覆盖率约 {coverage:.0%}，语义召回可能不完整")
    suffix = f"（{'；'.join(quality_notes)}，建议到设置-数据-知识库维护补索引）" if quality_notes else ""
    if web_search_enabled and not web_count:
        return f"已完成{subject}检索：知识库 {local_count} 篇；联网增强未获取到有效网页来源{suffix}，正在基于现有资料生成回答..."
    if web_search_enabled:
        return f"已完成{subject}检索：知识库 {local_count} 篇，联网来源 {web_count} 条{suffix}，正在生成回答..."
    return f"已完成{subject}检索：知识库 {local_count} 篇{suffix}，正在生成回答..."


async def _append_retrieval_context(
    context: list[dict[str, str]],
    query: str,
    *,
    rag_enabled: bool,
    web_search_enabled: bool,
    search_depth: str,
) -> list[dict]:
    """按统一策略叠加知识库和联网结果。"""
    limits = _retrieval_limits(search_depth)
    references = []

    if rag_enabled:
        async with AsyncSessionLocal() as rag_session:
            rag = RAGService(rag_session)
            results = await rag.search_similar(query, top_k=limits["rag_papers"])
            if results:
                rag_context = await rag.build_rag_context(query, max_papers=limits["rag_papers"])
                context.insert(0, {
                    "role": "system",
                    "content": f"你是一个科研助手。以下是相关知识库中的论文，请在回答时引用它们：{rag_context}",
                })
                references = [
                    {
                        "title": paper.title,
                        "arxiv_id": paper.arxiv_id,
                        "year": paper.year,
                        "similarity": round(score, 4),
                        "source": "local_library",
                    }
                    for paper, score in results
                ]

    if web_search_enabled:
        try:
            web_results = await search_web_results(
                query,
                max_results=limits["web_results"],
                search_depth=search_depth,
            )
        except Exception as exc:
            logger.warning(f"联网搜索失败: {exc}")
            web_results = []
        web_context = format_web_context(web_results)
        if web_context:
            context.insert(0, {
                "role": "system",
                "content": (
                    "以下是联网检索获得的网页来源。请仅在来源能支持结论时引用对应的 [WEB-N] 编号，"
                    "并区分网页来源与知识库论文：\n\n"
                    f"{web_context[:7000]}"
                ),
            })
            references.extend(result.as_reference() for result in web_results)
        else:
            context.insert(0, {
                "role": "system",
                "content": "用户已开启联网增强，但本轮联网搜索未返回可用来源。请明确说明未获取到有效联网结果，并将知识库内容标注为知识库检索结果，不要暗示已经完成网络检索。",
            })

    return references


class SendMessageResponse(BaseModel):
    message: MessageResponse
    reply: MessageResponse
    session_title: str
    compression_notice: Optional[str] = None


@router.delete("/{session_id}/messages/{message_id}")
async def delete_message(session_id: str, message_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除消息。"""
    from uuid import UUID
    try: sid=UUID(session_id); mid=UUID(message_id)
    except ValueError: raise HTTPException(status_code=400)
    s = (await db.execute(select(ChatSession).where(ChatSession.id==sid, ChatSession.user_id==user.id))).scalar_one_or_none()
    if not s: raise HTTPException(status_code=404)
    m = (await db.execute(select(ChatMessage).where(ChatMessage.id==mid, ChatMessage.session_id==sid))).scalar_one_or_none()
    if not m: raise HTTPException(status_code=404)
    await db.delete(m); await db.commit()
    return {"deleted": True}

@router.delete("/{session_id}/messages")
async def clear_messages(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """清空对话所有消息。"""
    from uuid import UUID
    try: sid=UUID(session_id)
    except ValueError: raise HTTPException(status_code=400)
    s = (await db.execute(select(ChatSession).where(ChatSession.id==sid, ChatSession.user_id==user.id))).scalar_one_or_none()
    if not s: raise HTTPException(status_code=404)
    msgs = (await db.execute(select(ChatMessage).where(ChatMessage.session_id==sid))).scalars().all()
    for m in msgs: await db.delete(m)
    await db.commit()
    return {"deleted": len(msgs)}

# --- 会话管理 ---

@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(req: SessionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建新对话。"""
    session = ChatSession(user_id=user.id, title=req.title, rag_enabled=req.rag_enabled)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=str(session.id), title=session.title, rag_enabled=session.rag_enabled,
        message_count=0, created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
    )


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取所有对话列表。"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    return [
        SessionResponse(
            id=str(s.id), title=s.title, rag_enabled=s.rag_enabled,
            message_count=len(s.messages) if s.messages else 0,
            last_message=s.messages[-1].content[:100] if s.messages else None,
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.updated_at.isoformat() if s.updated_at else "",
        )
        for s in sessions
    ]


@router.delete("/{session_id}")
async def delete_session(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除对话。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    await db.delete(session)
    await db.commit()
    return {"deleted": True}


# --- 消息 ---

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取对话消息。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == sid)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return [
        MessageResponse(
            id=str(m.id), role=m.role, content=m.content, references=m.references,
            created_at=m.created_at.isoformat() if m.created_at else "",
        )
        for m in messages
    ]


@router.post("/{session_id}/send", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    req: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送消息并获取 AI 回复。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    # 更新 RAG 设置
    rag_enabled = req.rag_enabled if req.rag_enabled is not None else session.rag_enabled
    if req.rag_enabled is not None:
        session.rag_enabled = req.rag_enabled

    # 保存用户消息
    user_msg = ChatMessage(session_id=sid, role="user", content=req.content)
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 构建上下文（使用三层记忆架构，参考 mem0/MemoryLLM/lethes）
    from app.services.memory_service import MemoryService
    memory = MemoryService(db)
    context = await memory.build_context(
        session,
        req.content,
        extra_context=req.extra_context or "",
    )

    references = await _append_retrieval_context(
        context,
        req.content,
        rag_enabled=rag_enabled,
        web_search_enabled=bool(req.web_search),
        search_depth=req.search_depth,
    )

    # 调用 LLM
    try:
        reply_content = await llm_service.chat(messages=context, temperature=0.7, max_tokens=4096)

        # 保存 AI 回复
        reply_msg = ChatMessage(
            session_id=sid, role="assistant",
            content=reply_content, references=references,
        )
        db.add(reply_msg)

        # 自动更新标题（用第一条用户消息的前30字）
        if session.title == "新对话":
            session.title = req.content[:30] + ("..." if len(req.content) > 30 else "")

        await db.commit()
        await db.refresh(reply_msg)

        return SendMessageResponse(
            message=MessageResponse(
                id=str(user_msg.id), role="user", content=user_msg.content,
                created_at=user_msg.created_at.isoformat() if user_msg.created_at else "",
            ),
            reply=MessageResponse(
                id=str(reply_msg.id), role="assistant", content=reply_msg.content,
                references=reply_msg.references,
                created_at=reply_msg.created_at.isoformat() if reply_msg.created_at else "",
            ),
            session_title=session.title,
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")


@router.post("/{session_id}/send-stream")
async def send_message_stream(
    session_id: str,
    req: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """流式发送消息并获取 AI 回复。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    rag_enabled = req.rag_enabled if req.rag_enabled is not None else session.rag_enabled
    if req.rag_enabled is not None:
        session.rag_enabled = req.rag_enabled

    # 保存用户消息
    user_msg = ChatMessage(session_id=sid, role="user", content=req.content)
    db.add(user_msg)
    await db.commit()

    # 构建上下文（三层记忆架构）
    from app.services.memory_service import MemoryService
    memory = MemoryService(db)
    context = await memory.build_context(session, req.content, extra_context=req.extra_context or "")

    references = await _append_retrieval_context(
        context,
        req.content,
        rag_enabled=rag_enabled,
        web_search_enabled=bool(req.web_search),
        search_depth=req.search_depth,
    )
    retrieval_quality = await _retrieval_quality_snapshot(rag_enabled=rag_enabled)
    llm_context = _build_llm_context_for_request(context, req)

    # 流式响应
    async def generate():
        full_content = ""
        yield _stream_event(
            "status",
            _retrieval_status(
                references,
                web_search_enabled=bool(req.web_search),
                retrieval_quality=retrieval_quality,
            ),
        )
        yield _stream_event(
            "meta",
            {
                "references": references,
                "model": _active_model_stream_metadata(
                    rag_enabled=rag_enabled,
                    web_search_enabled=bool(req.web_search),
                    search_depth=req.search_depth,
                    attachments=req.attachments,
                ),
            },
        )
        try:
            if req.show_thinking:
                async for event in llm_service.chat_stream_with_thinking(messages=llm_context):
                    if event["type"] == "reasoning":
                        yield _stream_event("reasoning", event["content"])
                    elif event["type"] == "content":
                        full_content += event["content"]
                        yield _stream_event("content", event["content"])
            else:
                async for token in llm_service.chat_stream(messages=llm_context):
                    if not token:
                        continue
                    full_content += token
                    yield _stream_event("content", token)
        except Exception as exc:
            logger.exception(f"对话流式生成失败: {exc}")
            full_content, appended = _stream_failure_content(full_content)
            yield _stream_event("error", appended)

        if not full_content.strip():
            full_content = EMPTY_STREAM_FALLBACK
            yield _stream_event("error", full_content)

        # 保存 AI 回复
        reply_msg = ChatMessage(session_id=sid, role="assistant", content=full_content, references=references)
        db.add(reply_msg)
        if session.title == "新对话":
            session.title = req.content[:30]
        await db.commit()
        yield _stream_event("done")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- 文件上传 ---

@router.post("/extract-file")
async def extract_file_text(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """仅提取文件内容，不发送消息。返回提取的文本供前端展示。"""
    content_type = file.content_type or ""
    filename = file.filename or "file"
    file_bytes = await file.read()

    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过 10MB")

    extracted_text = ""
    file_type = "unknown"
    data_url: str | None = None

    if "image" in content_type or filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        file_type = "image"
        import base64
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        mime = content_type or "image/png"
        extracted_text = f"[图片: {filename}]\n请描述你在这张图片中看到了什么，特别关注任何文字、图表或数据。"
        data_url = f"data:{mime};base64,{b64}"
        logger.info(f"图片上传: {filename} ({len(file_bytes)} bytes)")

    elif "pdf" in content_type or filename.lower().endswith('.pdf'):
        file_type = "pdf"
        extracted_text = await _extract_pdf_text(file_bytes, filename)

    else:
        try:
            extracted_text = file_bytes.decode("utf-8")[:50000]
            file_type = "text"
        except:
            raise HTTPException(status_code=400, detail="不支持的文件类型")

    return {
        "filename": filename,
        "file_type": file_type,
        "file_size": len(file_bytes),
        "extracted_text": extracted_text[:50000],
        "data_url": data_url if file_type == "image" else None,
        "mime_type": content_type or None,
        "text_length": len(extracted_text),
    }


@router.post("/{session_id}/upload")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传图片或 PDF 到对话中，提取内容传给 AI。"""
    from uuid import UUID
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == sid, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话未找到")

    content_type = file.content_type or ""
    filename = file.filename or "file"
    file_bytes = await file.read()

    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB 限制
        raise HTTPException(status_code=400, detail="文件不能超过 10MB")

    extracted_text = ""
    file_desc = ""

    try:
        if "image" in content_type or filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            # 图片：保存 base64，让 V4 Pro 多模态识别
            import base64
            b64 = base64.b64encode(file_bytes).decode("utf-8")
            mime = content_type or "image/png"
            data_uri = f"data:{mime};base64,{b64}"
            extracted_text = f"[用户上传了图片: {filename}]\n请描述你在这张图片中看到了什么，特别关注任何文字、图表或数据。"
            # 将图片信息存入消息 metadata
            file_desc = data_uri[:200]  # 截断 preview
            logger.info(f"收到图片: {filename} ({len(file_bytes)} bytes)")

        elif "pdf" in content_type or filename.lower().endswith('.pdf'):
            extracted_text = await _extract_pdf_text(file_bytes, filename)
            if extracted_text:
                file_desc = f"[用户上传了 PDF: {filename}，已提取全文 ({len(extracted_text)} 字符)]"
            else:
                file_desc = f"[用户上传了 PDF: {filename}，无法提取文本，可能是扫描图片版]"
                extracted_text = f"[PDF: {filename}] 内容无法提取，请上传可选中文字的原生 PDF。"

        else:
            # 其他文件：尝试当作文本读取
            try:
                extracted_text = file_bytes.decode("utf-8")[:4000]
                file_desc = f"[用户上传了文件: {filename}]"
            except:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {content_type}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

    # 保存用户消息（含文件描述）
    user_msg = ChatMessage(
        session_id=sid, role="user",
        content=extracted_text,
        references=[{"type": "file", "filename": filename, "size": len(file_bytes)}],
    )
    db.add(user_msg)

    # 构建上下文并调用 LLM
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == sid).order_by(ChatMessage.created_at)
    )
    all_msgs = result.scalars().all()
    context = [{"role": m.role, "content": m.content} for m in all_msgs[-20:]]
    context.append({"role": "user", "content": extracted_text})

    try:
        reply_content = await llm_service.chat(messages=context, temperature=0.7, max_tokens=4096)
        reply_msg = ChatMessage(session_id=sid, role="assistant", content=reply_content)
        db.add(reply_msg)
        await db.commit()
        await db.refresh(reply_msg)

        return {
            "message": {
                "id": str(user_msg.id), "role": "user", "content": file_desc or extracted_text[:200],
                "created_at": user_msg.created_at.isoformat() if user_msg.created_at else "",
            },
            "reply": {
                "id": str(reply_msg.id), "role": "assistant", "content": reply_content,
                "created_at": reply_msg.created_at.isoformat() if reply_msg.created_at else "",
            },
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")
