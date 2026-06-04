"""通知与订阅 API。"""

import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.notification import DigestSubscription, Notification
from app.db.models.user import User
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["通知"])


class SubscriptionUpdate(BaseModel):
    keywords: Optional[List[str]] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    frequency: Optional[str] = None


class SubscriptionResponse(BaseModel):
    keywords: list
    email_enabled: bool
    email_available: bool = False
    push_enabled: bool
    frequency: str
    last_sent_at: Optional[str]


class DigestPaperFeedbackRequest(BaseModel):
    paper_key: str = Field(..., min_length=1, max_length=500)
    action: Literal["interested", "later", "dismissed"]


# --- 订阅管理 ---

def _normalize_keywords(keywords: Optional[List[str]]) -> list[str]:
    """Normalize user-entered keywords while keeping their original order."""
    normalized = []
    for keyword in keywords or []:
        cleaned = " ".join(keyword.strip().split())
        if cleaned and cleaned.lower() not in {item.lower() for item in normalized}:
            normalized.append(cleaned[:100])
    return normalized[:20]


def _subscription_response(sub: DigestSubscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        keywords=sub.keywords or [],
        email_enabled=False,
        email_available=False,
        push_enabled=sub.push_enabled,
        frequency=sub.frequency,
        last_sent_at=sub.last_sent_at.isoformat() if sub.last_sent_at else None,
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户的推送订阅。"""
    result = await db.execute(
        select(DigestSubscription).where(DigestSubscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        return SubscriptionResponse(
            keywords=[], email_enabled=False, push_enabled=False,
            email_available=False, frequency="daily", last_sent_at=None,
        )

    return _subscription_response(sub)


@router.put("/subscription", response_model=SubscriptionResponse)
async def update_subscription(
    req: SubscriptionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新推送订阅。"""
    result = await db.execute(
        select(DigestSubscription).where(DigestSubscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        sub = DigestSubscription(user_id=user.id)
        db.add(sub)

    if req.keywords is not None:
        sub.keywords = _normalize_keywords(req.keywords)
    if req.email_enabled is not None:
        if req.email_enabled:
            raise HTTPException(status_code=400, detail="邮箱推送暂未配置，请先使用站内推送")
        sub.email_enabled = False
    if req.push_enabled is not None:
        sub.push_enabled = req.push_enabled
    if req.frequency is not None:
        if req.frequency != "daily":
            raise HTTPException(status_code=400, detail="当前仅支持每日推送")
        sub.frequency = req.frequency

    if sub.push_enabled and not sub.keywords:
        raise HTTPException(status_code=400, detail="请至少填写一个关注关键词后再开启站内推送")

    await db.commit()
    await db.refresh(sub)
    return _subscription_response(sub)


@router.post("/subscription/test")
async def test_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """立即生成一条站内测试摘要，便于用户验证订阅链路。"""
    result = await db.execute(
        select(DigestSubscription).where(DigestSubscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()
    keywords = _normalize_keywords(sub.keywords if sub else [])
    if not keywords:
        raise HTTPException(status_code=400, detail="请先保存至少一个关注关键词")

    from app.services.digest_service import DigestService

    delivery = await DigestService(db).dispatch_in_app_digest(
        user_id=user.id,
        keywords=keywords,
        is_test=True,
        notify_on_empty=True,
    )
    if sub:
        sub.last_sent_at = datetime.now(timezone.utc)
    await db.commit()
    return delivery


# --- 通知 ---

def _notification_response(notification: Notification) -> dict:
    return {
        "id": str(notification.id),
        "title": notification.title,
        "content": notification.content,
        "category": notification.category,
        "is_read": notification.is_read,
        "metadata": notification.metadata_json,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }


@router.get("/list")
async def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取通知列表。"""
    query = select(Notification).where(Notification.user_id == user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()

    return [_notification_response(notification) for notification in notifications]


@router.get("/digests")
async def list_digests(
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取论文推送历史，供论文库推送中心阅读。"""
    result = await db.execute(
        select(Notification)
        .where(
            Notification.user_id == user.id,
            Notification.category == "digest",
        )
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return [_notification_response(notification) for notification in result.scalars().all()]


@router.get("/digests/unread-count")
async def digest_unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取未读论文推送数量。"""
    result = await db.execute(
        select(func.count(Notification.id))
        .where(
            Notification.user_id == user.id,
            Notification.category == "digest",
            Notification.is_read == False,
        )
    )
    return {"unread_count": result.scalar() or 0}


@router.post("/digests/read-all")
async def mark_all_digests_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """仅将论文推送标记为已读，保留其他通知的未读状态。"""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.category == "digest",
            Notification.is_read == False,
        )
    )
    notifications = result.scalars().all()
    for notification in notifications:
        notification.is_read = True
    await db.commit()
    return {"read_all": True, "updated": len(notifications)}


@router.post("/digests/{notification_id}/feedback")
async def update_digest_feedback(
    notification_id: str,
    req: DigestPaperFeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """记录用户对单篇推送论文的反馈，供后续推荐排序使用。"""
    from uuid import UUID
    try:
        digest_id = UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(Notification).where(
            Notification.id == digest_id,
            Notification.user_id == user.id,
            Notification.category == "digest",
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Digest not found")

    metadata = dict(notification.metadata_json or {})
    feedback = dict(metadata.get("feedback", {}) or {})
    feedback[req.paper_key] = {
        "action": req.action,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    metadata["feedback"] = feedback
    notification.metadata_json = metadata
    await db.commit()
    return {"paper_key": req.paper_key, "action": req.action}


@router.get("/unread-count")
async def unread_count(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取未读通知数量。"""
    result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == user.id)
        .where(Notification.is_read == False)
    )
    count = result.scalar() or 0
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """标记通知为已读。"""
    from uuid import UUID
    try:
        nid = UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await db.execute(
        select(Notification).where(
            Notification.id == nid,
            Notification.user_id == user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Not found")

    notif.is_read = True
    await db.commit()
    return {"read": True}


@router.post("/read-all")
async def mark_all_read(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """全部标记已读。"""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.is_read == False,
        )
    )
    for n in result.scalars().all():
        n.is_read = True
    await db.commit()
    return {"read_all": True}
