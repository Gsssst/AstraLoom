"""对话 API — 提供 LLM 对话接口。"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm import llm_service
from app.services.rag_service import RAGService
from app.core.security import get_current_user
from app.db.session import get_db
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)
router = APIRouter(tags=["对话"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色：system, user, assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="对话消息列表")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=16384, ge=1, le=65536, description="最大生成 token 数")
    stream: bool = Field(default=False, description="是否流式返回")
    show_thinking: bool = Field(default=False, description="是否展示思考过程")


class ChatResponse(BaseModel):
    content: str = Field(..., description="助手回复内容")
    model: str = Field(default="deepseek-v4-pro", description="使用的模型")


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """标准对话补全接口，支持流式和非流式。

    兼容 OpenAI Chat Completions API 格式。
    """
    messages_dict = [msg.model_dump() for msg in request.messages]

    if request.stream:
        import json

        async def event_generator():
            try:
                if request.show_thinking:
                    async for event in llm_service.chat_stream_with_thinking(
                        messages=messages_dict,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                    ):
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                else:
                    async for token in llm_service.chat_stream(
                        messages=messages_dict,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                    ):
                        yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"流式对话错误: {e}")
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )
    else:
        try:
            content = await llm_service.chat(
                messages=messages_dict,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False,
            )
            return ChatResponse(content=content)
        except Exception as e:
            logger.error(f"对话错误: {e}")
            raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")


class RAGChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="对话消息列表")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    stream: bool = Field(default=False)
    enable_rag: bool = Field(default=True, description="是否启用论文知识库增强")


class RAGChatResponse(BaseModel):
    content: str
    model: str = "deepseek-v4-pro"
    references: list = Field(default_factory=list, description="引用的论文列表")


@router.post("/chat/rag", response_model=RAGChatResponse)
async def rag_chat_completions(request: RAGChatRequest):
    """RAG 增强对话 — 自动检索相关论文并注入上下文。"""
    try:
        messages_dict = [msg.model_dump() for msg in request.messages]
        user_query = messages_dict[-1]["content"] if messages_dict else ""

        # 1. 语义搜索相关论文
        references = []
        rag_context = ""

        if request.enable_rag:
            async with AsyncSessionLocal() as session:
                rag = RAGService(session)
                results = await rag.search_similar(user_query, top_k=3)
                if results:
                    rag_context = await rag.build_rag_context(user_query, max_papers=3)
                    references = [
                        {
                            "title": p.title,
                            "arxiv_id": p.arxiv_id,
                            "year": p.year,
                            "similarity": round(score, 4),
                        }
                        for p, score in results
                    ]

        # 2. 注入上下文到系统消息
        if rag_context:
            system_msg = {
                "role": "system",
                "content": f"你是一个科研助手。以下是相关知识库中的论文，请在回答时引用它们：{rag_context}",
            }
            full_messages = [system_msg] + messages_dict
        else:
            full_messages = messages_dict

        # 3. 调用 LLM
        content = await llm_service.chat(
            messages=full_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
        )

        return RAGChatResponse(content=content, references=references)

    except Exception as e:
        logger.error(f"RAG 对话错误: {e}")
        raise HTTPException(status_code=500, detail=f"RAG 对话失败: {str(e)}")


class FeedbackRequest(BaseModel):
    message_id: str = Field(..., description="消息 ID")
    rating: str = Field(..., pattern="^(like|dislike)$")

@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """提交消息反馈。"""
    from uuid import UUID
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as s:
        await s.execute(sa.text(
            "INSERT INTO message_feedback (id, message_id, user_id, rating) VALUES (gen_random_uuid(), :mid, :uid, :r)",
            {"mid": UUID(req.message_id), "uid": user.id, "r": req.rating}
        ))
        await s.commit()
    return {"status": "ok"}

class SummarizeRequest(BaseModel):
    title: str = Field(..., description="论文标题")
    abstract: str = Field(..., description="论文摘要")
    full_text: Optional[str] = Field(default=None, description="论文全文（可选）")


class SummarizeResponse(BaseModel):
    summary: str = Field(..., description="结构化总结（中文）")


@router.post("/paper/summarize", response_model=SummarizeResponse)
async def summarize_paper(request: SummarizeRequest):
    """论文总结接口 — 返回结构化中文总结。"""
    try:
        summary = await llm_service.summarize_paper(
            title=request.title,
            abstract=request.abstract,
            full_text=request.full_text,
        )
        return SummarizeResponse(summary=summary)
    except Exception as e:
        logger.error(f"论文总结错误: {e}")
        raise HTTPException(status_code=500, detail=f"论文总结失败: {str(e)}")
