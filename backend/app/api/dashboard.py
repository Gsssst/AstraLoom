"""系统仪表盘 API。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models.paper import Paper
from app.db.models.user import User
from app.db.models.usage import TokenUsage
from app.db.models.chat import ChatSession
from app.core.security import require_admin

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    """系统统计概览。"""
    paper_count = (await db.execute(select(func.count(Paper.id)))).scalar() or 0
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    chat_count = (await db.execute(select(func.count(ChatSession.id)))).scalar() or 0
    total_tokens = (await db.execute(select(func.sum(TokenUsage.total_tokens)))).scalar() or 0
    total_cost = (await db.execute(select(func.sum(TokenUsage.cost_estimate)))).scalar() or 0

    # 最近活动
    recent_papers = (await db.execute(select(Paper).order_by(Paper.created_at.desc()).limit(5))).scalars().all()
    recent_chats = (await db.execute(select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(3))).scalars().all()

    return {
        "stats": {
            "papers": int(paper_count), "users": int(user_count),
            "chats": int(chat_count), "total_tokens": int(total_tokens),
            "total_cost": round(float(total_cost), 4),
        },
        "recent": {
            "papers": [{"title": p.title, "date": p.created_at.isoformat() if p.created_at else ""} for p in recent_papers],
            "chats": [{"title": c.title, "date": c.updated_at.isoformat() if c.updated_at else ""} for c in recent_chats],
        },
    }
