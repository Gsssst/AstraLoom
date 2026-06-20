"""通知与订阅 API。"""

import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.notification import (
    DigestSubscription,
    Notification,
    PaperChatShareComment,
    PaperChatShareParticipant,
    PaperChatShareStatus,
    PaperChatShareThread,
)
from app.db.models.paper import Paper, UserPaper
from app.db.models.user import User
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["通知"])
PAPER_PUSH_CATEGORIES = ("digest", "paper_chat_share")
PAPER_CHAT_SHARE_DISCUSSION_CATEGORY = "paper_chat_share_discussion"
PAPER_CHAT_SHARE_STATUSES = {"useful", "follow_up", "resolved"}


class SubscriptionUpdate(BaseModel):
    keywords: Optional[List[str]] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    frequency: Optional[str] = None
    send_hour: Optional[int] = Field(default=None, ge=0, le=23)


class SubscriptionResponse(BaseModel):
    keywords: list
    email_enabled: bool
    email_available: bool = False
    push_enabled: bool
    frequency: str
    send_hour: int = 8
    last_sent_at: Optional[str]


class DigestPaperFeedbackRequest(BaseModel):
    paper_key: str = Field(..., min_length=1, max_length=500)
    action: Literal["interested", "later", "dismissed"]


class PaperChatShareCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class PaperChatShareStatusRequest(BaseModel):
    status: Optional[Literal["useful", "follow_up", "resolved"]] = None


class PaperChatShareSaveToNoteResponse(BaseModel):
    paper_id: str
    thread_id: str
    saved_at: str
    appended_markdown: str
    note_length: int


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
        send_hour=getattr(sub, "send_hour", 8) or 8,
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
            email_available=False, frequency="daily", send_hour=8, last_sent_at=None,
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
    if req.send_hour is not None:
        sub.send_hour = req.send_hour

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


def _parse_uuid(value: str | None, field_name: str = "ID") -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


def _user_display_name(user: User | None) -> str:
    if not user:
        return "未知用户"
    return getattr(user, "display_name", None) or getattr(user, "username", None) or getattr(user, "email", None) or "未知用户"


async def _users_by_id(db: AsyncSession, user_ids: list) -> dict:
    ids = list({item for item in user_ids if item})
    if not ids:
        return {}
    result = await db.execute(select(User).where(User.id.in_(ids)))
    return {user.id: user for user in result.scalars().all()}


def _bounded_markdown_text(value, limit: int = 6000) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 1)].rstrip()}…"


def _selected_share_messages(metadata: dict) -> list[dict]:
    messages = metadata.get("selected_messages")
    if isinstance(messages, list):
        return [item for item in messages if isinstance(item, dict)][:20]
    fallback_messages: list[dict] = []
    question = _bounded_markdown_text(metadata.get("question"), 3000)
    answer = _bounded_markdown_text(metadata.get("answer") or metadata.get("answer_excerpt"), 6000)
    if question:
        fallback_messages.append({"role": "user", "content": question})
    if answer:
        fallback_messages.append({"role": "assistant", "content": answer})
    return fallback_messages


def _share_status_label(status: str | None) -> str:
    return {
        "useful": "有用",
        "follow_up": "待跟进",
        "resolved": "已处理",
    }.get(status or "", status or "未标记")


def _format_saved_at(value: datetime | None) -> str:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat()


async def _format_paper_chat_share_note_block(
    db: AsyncSession,
    *,
    notification: Notification,
    thread: PaperChatShareThread,
    current_user: User,
    saved_at: datetime | None = None,
) -> tuple[str, str]:
    metadata = dict(notification.metadata_json or {})
    thread_metadata = dict(thread.metadata_json or {})
    title = _bounded_markdown_text(
        metadata.get("paper_title") or thread.title or thread_metadata.get("paper_title") or notification.title or "论文精读分享",
        300,
    )
    sender_name = _bounded_markdown_text(metadata.get("sender_name") or thread_metadata.get("sender_name"), 80)
    sender_note = _bounded_markdown_text(metadata.get("note") or thread_metadata.get("note"), 1200)
    saved_at_text = _format_saved_at(saved_at)
    messages = _selected_share_messages(metadata)
    comments = (await db.execute(
        select(PaperChatShareComment)
        .where(PaperChatShareComment.thread_id == thread.id)
        .order_by(PaperChatShareComment.created_at.asc())
    )).scalars().all()
    statuses = (await db.execute(
        select(PaperChatShareStatus).where(PaperChatShareStatus.thread_id == thread.id)
    )).scalars().all()
    participants = (await db.execute(
        select(PaperChatShareParticipant).where(PaperChatShareParticipant.thread_id == thread.id)
    )).scalars().all()
    users = await _users_by_id(
        db,
        [comment.author_id for comment in comments if comment.author_id]
        + [status.user_id for status in statuses]
        + [participant.user_id for participant in participants],
    )
    status_lines = []
    for status in statuses:
        name = _user_display_name(users.get(status.user_id))
        status_lines.append(f"- {name}: {_share_status_label(status.status)}")
    message_blocks = []
    for index, item in enumerate(messages, start=1):
        role = "问题" if item.get("role") == "user" else "回答" if item.get("role") == "assistant" else "消息"
        content = _bounded_markdown_text(item.get("content") or item.get("display_content") or item.get("excerpt"), 6000)
        if not content:
            content = "（无正文）"
        message_blocks.append(f"#### {index}. {role}\n\n{content}")
    comment_lines = []
    for comment in comments:
        author = _user_display_name(users.get(comment.author_id)) if comment.author_id else "未知用户"
        created_at = comment.created_at.isoformat() if comment.created_at else ""
        suffix = f"（{created_at}）" if created_at else ""
        comment_lines.append(f"- **{author}**{suffix}: {_bounded_markdown_text(comment.content, 1600)}")
    source_path = metadata.get("path") or thread_metadata.get("path") or ""
    lines = [
        "",
        "---",
        "",
        f"## 精读分享沉淀：{title}",
        "",
        f"- 保存时间：{saved_at_text}",
        f"- 来源线程：{thread.id}",
    ]
    if sender_name:
        lines.append(f"- 分享者：{sender_name}")
    if source_path:
        lines.append(f"- 来源页面：{source_path}")
    if sender_note:
        lines.extend(["", "### 分享备注", "", sender_note])
    lines.extend(["", "### 共享对话", ""])
    lines.append("\n\n".join(message_blocks) if message_blocks else "（这条分享没有附带对话片段）")
    lines.extend(["", "### 讨论评论", ""])
    lines.append("\n".join(comment_lines) if comment_lines else "（暂无讨论评论）")
    lines.extend(["", "### 处理状态", ""])
    lines.append("\n".join(status_lines) if status_lines else "（暂无参与者标记）")
    return "\n".join(lines).strip() + "\n", saved_at_text


async def _get_or_create_user_paper_note(db: AsyncSession, user_id, paper_id) -> UserPaper:
    user_paper = (await db.execute(
        select(UserPaper).where(
            UserPaper.user_id == user_id,
            UserPaper.paper_id == paper_id,
        )
    )).scalar_one_or_none()
    if user_paper:
        return user_paper
    user_paper = UserPaper(user_id=user_id, paper_id=paper_id, saved=True)
    db.add(user_paper)
    await db.flush()
    return user_paper


async def _ensure_share_participant(
    db: AsyncSession,
    thread_id,
    user_id,
    role: str,
    notification_id=None,
) -> PaperChatShareParticipant:
    result = await db.execute(
        select(PaperChatShareParticipant).where(
            PaperChatShareParticipant.thread_id == thread_id,
            PaperChatShareParticipant.user_id == user_id,
        )
    )
    participant = result.scalar_one_or_none()
    if participant:
        if notification_id and not participant.notification_id:
            participant.notification_id = notification_id
        if role == "sender" and participant.role != "sender":
            participant.role = "sender"
        return participant
    participant = PaperChatShareParticipant(
        thread_id=thread_id,
        user_id=user_id,
        role=role,
        notification_id=notification_id,
    )
    db.add(participant)
    await db.flush()
    return participant


def _metadata_uuid(metadata: dict, key: str):
    value = metadata.get(key)
    if not value:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


async def _ensure_share_thread_for_notification(
    db: AsyncSession,
    notification: Notification,
) -> PaperChatShareThread:
    metadata = dict(notification.metadata_json or {})
    thread_id = _metadata_uuid(metadata, "share_thread_id")
    if thread_id:
        thread = (await db.execute(
            select(PaperChatShareThread).where(PaperChatShareThread.id == thread_id)
        )).scalar_one_or_none()
        if thread:
            role = "sender" if str(metadata.get("sender_id") or "") == str(notification.user_id) else "recipient"
            await _ensure_share_participant(db, thread.id, notification.user_id, role, notification.id)
            return thread

    sender_id = _metadata_uuid(metadata, "sender_id")
    thread = PaperChatShareThread(
        paper_id=_metadata_uuid(metadata, "paper_id"),
        sender_id=sender_id,
        title=(metadata.get("paper_title") or notification.title or "")[:500],
        metadata_json={
            "legacy_notification_id": str(notification.id),
            "paper_title": metadata.get("paper_title"),
            "sender_name": metadata.get("sender_name"),
            "note": metadata.get("note"),
            "path": metadata.get("path"),
            "message_count": metadata.get("message_count"),
        },
    )
    db.add(thread)
    await db.flush()
    role = "sender" if sender_id and sender_id == notification.user_id else "recipient"
    await _ensure_share_participant(db, thread.id, notification.user_id, role, notification.id)
    if sender_id and sender_id != notification.user_id:
        sender_notification = Notification(
            user_id=sender_id,
            title="你分享了论文 AI 精读",
            content=notification.content,
            category="paper_chat_share",
            is_read=True,
            metadata_json={
                **metadata,
                "share_thread_id": str(thread.id),
                "recipient_mode": "sent_legacy",
            },
        )
        db.add(sender_notification)
        await db.flush()
        await _ensure_share_participant(db, thread.id, sender_id, "sender", sender_notification.id)
    metadata["share_thread_id"] = str(thread.id)
    notification.metadata_json = metadata
    await db.flush()
    return thread


async def _owned_paper_chat_share_notification(
    notification_id: str,
    user: User,
    db: AsyncSession,
) -> Notification:
    nid = _parse_uuid(notification_id, "notification_id")
    result = await db.execute(
        select(Notification).where(
            Notification.id == nid,
            Notification.user_id == user.id,
            Notification.category == "paper_chat_share",
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Paper chat share not found")
    return notification


async def _assert_thread_participant(db: AsyncSession, thread_id, user_id) -> PaperChatShareParticipant:
    participant = (await db.execute(
        select(PaperChatShareParticipant).where(
            PaperChatShareParticipant.thread_id == thread_id,
            PaperChatShareParticipant.user_id == user_id,
        )
    )).scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Paper chat share not found")
    return participant


async def _paper_chat_share_thread_response(
    db: AsyncSession,
    thread: PaperChatShareThread,
    current_user: User,
) -> dict:
    participants = (await db.execute(
        select(PaperChatShareParticipant)
        .where(PaperChatShareParticipant.thread_id == thread.id)
        .order_by(PaperChatShareParticipant.created_at.asc())
    )).scalars().all()
    comments = (await db.execute(
        select(PaperChatShareComment)
        .where(PaperChatShareComment.thread_id == thread.id)
        .order_by(PaperChatShareComment.created_at.asc())
    )).scalars().all()
    statuses = (await db.execute(
        select(PaperChatShareStatus).where(PaperChatShareStatus.thread_id == thread.id)
    )).scalars().all()
    users = await _users_by_id(
        db,
        [participant.user_id for participant in participants]
        + [comment.author_id for comment in comments if comment.author_id]
        + [status.user_id for status in statuses],
    )
    status_counts: dict[str, int] = {}
    current_status = None
    for item in statuses:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
        if item.user_id == current_user.id:
            current_status = item.status
    return {
        "id": str(thread.id),
        "paper_id": str(thread.paper_id) if thread.paper_id else None,
        "sender_id": str(thread.sender_id) if thread.sender_id else None,
        "title": thread.title,
        "metadata": thread.metadata_json or {},
        "participants": [
            {
                "id": str(participant.id),
                "user_id": str(participant.user_id),
                "name": _user_display_name(users.get(participant.user_id)),
                "role": participant.role,
                "notification_id": str(participant.notification_id) if participant.notification_id else None,
            }
            for participant in participants
        ],
        "comments": [
            {
                "id": str(comment.id),
                "author_id": str(comment.author_id) if comment.author_id else None,
                "author_name": _user_display_name(users.get(comment.author_id)) if comment.author_id else "未知用户",
                "content": comment.content,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            }
            for comment in comments
        ],
        "current_user_status": current_status,
        "status_counts": status_counts,
        "created_at": thread.created_at.isoformat() if thread.created_at else None,
        "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
    }


async def _notify_paper_chat_share_comment(
    db: AsyncSession,
    thread: PaperChatShareThread,
    comment: PaperChatShareComment,
    actor: User,
) -> None:
    participant_rows = (await db.execute(
        select(PaperChatShareParticipant).where(PaperChatShareParticipant.thread_id == thread.id)
    )).scalars().all()
    participant_by_user = {item.user_id: item for item in participant_rows}
    target_ids = {item.user_id for item in participant_rows if item.user_id != actor.id}
    if not target_ids:
        return
    title = (thread.title or (thread.metadata_json or {}).get("paper_title") or "论文精读分享")[:120]
    actor_name = _user_display_name(actor)
    for target_id in target_ids:
        participant = participant_by_user.get(target_id)
        db.add(Notification(
            user_id=target_id,
            title=f"{actor_name} 回复了论文精读分享",
            content=f"《{title}》的精读分享有新评论。",
            category=PAPER_CHAT_SHARE_DISCUSSION_CATEGORY,
            metadata_json={
                "action": "paper_chat_share_commented",
                "share_thread_id": str(thread.id),
                "comment_id": str(comment.id),
                "paper_id": str(thread.paper_id) if thread.paper_id else None,
                "paper_title": title,
                "path": "/papers/digests",
                "target_notification_id": str(participant.notification_id) if participant and participant.notification_id else None,
            },
        ))


@router.get("/list")
async def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    unread_only: bool = False,
    category: Optional[str] = Query(default=None, min_length=1, max_length=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取通知列表。"""
    query = select(Notification).where(Notification.user_id == user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)
    if category:
        query = query.where(Notification.category == category)

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
            Notification.category.in_(PAPER_PUSH_CATEGORIES),
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
            Notification.category.in_(PAPER_PUSH_CATEGORIES),
            Notification.is_read == False,
        )
    )
    return {"unread_count": result.scalar() or 0}


@router.get("/paper-chat-shares/{notification_id}/thread")
async def get_paper_chat_share_thread(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取论文精读分享讨论串。"""
    notification = await _owned_paper_chat_share_notification(notification_id, user, db)
    thread = await _ensure_share_thread_for_notification(db, notification)
    await _assert_thread_participant(db, thread.id, user.id)
    await db.commit()
    return await _paper_chat_share_thread_response(db, thread, user)


@router.post("/paper-chat-shares/{notification_id}/comments")
async def add_paper_chat_share_comment(
    notification_id: str,
    req: PaperChatShareCommentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """在论文精读分享讨论串中发表评论。"""
    content = " ".join(req.content.split())
    if not content:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    notification = await _owned_paper_chat_share_notification(notification_id, user, db)
    thread = await _ensure_share_thread_for_notification(db, notification)
    await _assert_thread_participant(db, thread.id, user.id)
    comment = PaperChatShareComment(
        thread_id=thread.id,
        author_id=user.id,
        content=content[:4000],
    )
    db.add(comment)
    await db.flush()
    await _notify_paper_chat_share_comment(db, thread, comment, user)
    await db.commit()
    return await _paper_chat_share_thread_response(db, thread, user)


@router.put("/paper-chat-shares/{notification_id}/status")
async def update_paper_chat_share_status(
    notification_id: str,
    req: PaperChatShareStatusRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户对论文精读分享的处理状态。"""
    notification = await _owned_paper_chat_share_notification(notification_id, user, db)
    thread = await _ensure_share_thread_for_notification(db, notification)
    await _assert_thread_participant(db, thread.id, user.id)
    existing = (await db.execute(
        select(PaperChatShareStatus).where(
            PaperChatShareStatus.thread_id == thread.id,
            PaperChatShareStatus.user_id == user.id,
        )
    )).scalar_one_or_none()
    if req.status is None:
        if existing:
            await db.delete(existing)
    elif req.status not in PAPER_CHAT_SHARE_STATUSES:
        raise HTTPException(status_code=400, detail="不支持的状态")
    elif existing:
        existing.status = req.status
    else:
        db.add(PaperChatShareStatus(
            thread_id=thread.id,
            user_id=user.id,
            status=req.status,
        ))
    await db.commit()
    return await _paper_chat_share_thread_response(db, thread, user)


@router.post("/paper-chat-shares/{notification_id}/save-to-note", response_model=PaperChatShareSaveToNoteResponse)
async def save_paper_chat_share_discussion_to_note(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将论文精读分享和讨论沉淀到当前用户的论文笔记。"""
    notification = await _owned_paper_chat_share_notification(notification_id, user, db)
    thread = await _ensure_share_thread_for_notification(db, notification)
    await _assert_thread_participant(db, thread.id, user.id)
    if not thread.paper_id:
        raise HTTPException(status_code=400, detail="这条精读分享没有绑定本地论文，无法沉淀到论文笔记")
    paper = (await db.execute(select(Paper).where(Paper.id == thread.paper_id))).scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在，无法沉淀到论文笔记")
    saved_at = datetime.now(timezone.utc)
    block, saved_at_text = await _format_paper_chat_share_note_block(
        db,
        notification=notification,
        thread=thread,
        current_user=user,
        saved_at=saved_at,
    )
    user_paper = await _get_or_create_user_paper_note(db, user.id, thread.paper_id)
    existing_note = (user_paper.personal_notes or "").rstrip()
    user_paper.personal_notes = f"{existing_note}\n\n{block}".strip() if existing_note else block.strip()
    user_paper.saved = True
    await db.commit()
    return PaperChatShareSaveToNoteResponse(
        paper_id=str(thread.paper_id),
        thread_id=str(thread.id),
        saved_at=saved_at_text,
        appended_markdown=block,
        note_length=len(user_paper.personal_notes or ""),
    )


@router.post("/digests/read-all")
async def mark_all_digests_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """仅将论文推送标记为已读，保留其他通知的未读状态。"""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.category.in_(PAPER_PUSH_CATEGORIES),
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
async def mark_all_read(
    category: Optional[str] = Query(default=None, min_length=1, max_length=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """全部标记已读。"""
    query = select(Notification).where(
        Notification.user_id == user.id,
        Notification.is_read == False,
    )
    if category:
        query = query.where(Notification.category == category)
    result = await db.execute(query)
    notifications = result.scalars().all()
    for notification in notifications:
        notification.is_read = True
    await db.commit()
    return {"read_all": True, "updated": len(notifications)}
