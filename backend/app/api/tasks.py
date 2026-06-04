"""任务管理 API — 提交和查询 Celery 异步任务。"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Any

from app.tasks.paper_tasks import download_paper, parse_pdf, generate_embedding
from app.core.security import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["任务"])


class TaskResponse(BaseModel):
    task_id: str = Field(..., description="Celery 任务 ID")
    status: str = Field(..., description="任务状态")


class TaskDetailResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None


class DownloadPaperRequest(BaseModel):
    arxiv_id: str = Field(..., description="arXiv 论文 ID")


class ParsePdfRequest(BaseModel):
    filepath: str = Field(..., description="PDF 文件路径")


class GenerateEmbeddingRequest(BaseModel):
    text: str = Field(..., description="需要向量化的文本")


@router.post("/download-paper", response_model=TaskResponse)
async def submit_download_paper(req: DownloadPaperRequest, user=Depends(require_admin)):
    """提交论文下载任务。"""
    task = download_paper.delay(req.arxiv_id)
    return TaskResponse(task_id=task.id, status="PENDING")


@router.post("/parse-pdf", response_model=TaskResponse)
async def submit_parse_pdf(req: ParsePdfRequest, user=Depends(require_admin)):
    """提交 PDF 解析任务。"""
    task = parse_pdf.delay(req.filepath)
    return TaskResponse(task_id=task.id, status="PENDING")


@router.post("/generate-embedding", response_model=TaskResponse)
async def submit_generate_embedding(req: GenerateEmbeddingRequest, user=Depends(require_admin)):
    """提交文本向量化任务。"""
    task = generate_embedding.delay(req.text)
    return TaskResponse(task_id=task.id, status="PENDING")


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task_status(task_id: str, user=Depends(require_admin)):
    """查询任务状态和结果。"""
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)
    response = {
        "task_id": task_id,
        "status": result.state,
        "result": None,
        "error": None,
    }

    if result.ready():
        try:
            task_result = result.get(timeout=1)
            if isinstance(task_result, dict) and task_result.get("status") == "error":
                response["error"] = task_result.get("error", "Unknown error")
            else:
                response["result"] = task_result
        except Exception as e:
            response["error"] = str(e)

    return TaskDetailResponse(**response)
