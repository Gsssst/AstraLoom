"""系统设置 API。"""

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.user import User
from app.core.security import get_current_user, hash_password, verify_password
from app.core.config import settings as app_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["设置"])


class ProfileResponse(BaseModel):
    username: str
    email: str
    role: str
    is_active: bool
    avatar: Optional[str] = None
    display_name: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class ApiConfigResponse(BaseModel):
    provider: str = "deepseek"
    model: str
    api_base: str
    has_api_key: bool
    web_search_providers: list[str] = Field(default_factory=list)


class UpdateApiConfigRequest(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None


class SystemInfoResponse(BaseModel):
    app_name: str
    version: str
    debug: bool


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: User = Depends(get_current_user)):
    """获取当前用户资料。"""
    return ProfileResponse(
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        avatar=user.avatar,
        display_name=user.display_name,
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(req: UpdateProfileRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """更新用户资料。"""
    if req.email:
        user.email = req.email
    if req.display_name is not None:
        user.display_name = req.display_name
    await db.commit()
    await db.refresh(user)
    return ProfileResponse(username=user.username, email=user.email, role=user.role, is_active=user.is_active, avatar=user.avatar, display_name=user.display_name)


@router.post("/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """上传头像（base64 存储）。"""
    import base64
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="头像不能超过 2MB")
    b64 = base64.b64encode(content).decode("utf-8")
    mime = file.content_type or "image/png"
    user.avatar = f"data:{mime};base64,{b64}"
    await db.commit()
    return {"avatar": user.avatar}


@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """修改密码。"""
    if not verify_password(req.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.hashed_password = hash_password(req.new_password)
    await db.commit()
    return {"success": True, "message": "密码已修改"}


@router.get("/api-config", response_model=ApiConfigResponse)
async def get_api_config(user: User = Depends(get_current_user)):
    """获取 API 配置信息（隐藏 API Key）。"""
    from app.services.web_search import available_web_provider_names

    return ApiConfigResponse(
        provider="deepseek",
        model=app_settings.DEEPSEEK_MODEL,
        api_base=app_settings.DEEPSEEK_API_BASE,
        has_api_key=bool(app_settings.DEEPSEEK_API_KEY),
        web_search_providers=available_web_provider_names(),
    )


@router.get("/system-info", response_model=SystemInfoResponse)
async def get_system_info():
    """获取系统信息。"""
    return SystemInfoResponse(
        app_name=app_settings.APP_NAME,
        version="0.2.0",
        debug=app_settings.DEBUG,
    )
