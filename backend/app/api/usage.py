"""Token 用量统计 API。"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.services.usage_tracker import UsageTracker
from app.db.models.user import User
from app.core.security import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/usage", tags=["用量"])


class UserStatsResponse(BaseModel):
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_calls: int
    estimated_cost: float
    today_tokens: int
    month_tokens: int


class AllUsersStatsResponse(BaseModel):
    users: list[dict]
    grand_total_tokens: int
    grand_total_cost: float


@router.get("/my-stats", response_model=UserStatsResponse)
async def get_my_stats(user: User = Depends(get_current_user)):
    """获取当前用户的 Token 用量统计。"""
    return await UsageTracker.get_user_stats(str(user.id))


@router.get("/all-stats")
async def get_all_stats(user: User = Depends(require_admin)):
    """获取所有用户的用量统计。"""
    users = await UsageTracker.get_all_users_stats()
    grand_total = sum(u["total_tokens"] for u in users)
    grand_cost = sum(u["estimated_cost"] for u in users)

    return AllUsersStatsResponse(
        users=users,
        grand_total_tokens=grand_total,
        grand_total_cost=round(grand_cost, 4),
    )


@router.get("/history")
async def get_history(
    user_id: Optional[str] = Query(default=None, description="筛选用户，不传则返回全部"),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
):
    """获取 Token 使用历史记录。"""
    scoped_user_id = user_id if user.role == "admin" else str(user.id)
    return await UsageTracker.get_recent_history(user_id=scoped_user_id, limit=limit)
