"""引用验证服务 — 参考 OpenScholar 引用真实性检查。"""
import re, logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.paper import Paper

logger = logging.getLogger(__name__)

async def validate_citations(db: AsyncSession, answer: str, references: list) -> dict:
    """验证 AI 回复中的引用是否真实。返回验证结果。"""
    if not references:
        return {"status": "no_citations", "verified": 0, "issues": []}

    issues = []
    for i, ref in enumerate(references):
        title = ref.get("title", "")
        arxiv_id = ref.get("arxiv_id")
        if arxiv_id:
            paper = (await db.execute(select(Paper).where(Paper.arxiv_id == arxiv_id))).scalar_one_or_none()
            if not paper:
                issues.append({"index": i + 1, "title": title, "issue": "arXiv ID 在知识库中未找到"})
        elif title:
            paper = (await db.execute(select(Paper).where(Paper.title.ilike(f"%{title[:50]}%")))).scalar_one_or_none()
            if not paper:
                issues.append({"index": i + 1, "title": title, "issue": "标题在知识库中未找到，可能是编造的"})

    return {
        "status": "verified" if not issues else "has_issues",
        "verified": len(references) - len(issues),
        "total": len(references),
        "issues": issues,
    }
