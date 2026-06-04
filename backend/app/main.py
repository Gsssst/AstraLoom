"""FastAPI 应用入口。"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)

# --- 日志配置 ---
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    logger.info(f"🚀 {settings.APP_NAME} 启动中... (env={settings.APP_ENV})")

    # 启动时：初始化数据库
    from app.db.init_db import init_db
    await init_db()
    logger.info("✅ 数据库初始化完成")

    yield

    # 关闭时：清理资源
    logger.info(f"👋 {settings.APP_NAME} 正在关闭...")


app = FastAPI(
    title=settings.APP_NAME,
    description="自动化科研工作流系统 API",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# --- CORS 中间件 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 异常处理注册 ---
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# --- 健康检查 ---
@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查端点。"""
    return JSONResponse(
        content={
            "status": "ok",
            "app": settings.APP_NAME,
            "env": settings.APP_ENV,
            "version": "0.1.0",
        }
    )


# --- 注册路由 ---
from app.api import chat, tasks, papers, auth, research, writing  # noqa: E402
from app.api.writing_v2 import router as writing_v2_router  # noqa: E402
from app.api.settings import router as settings_router  # noqa: E402
from app.api.usage import router as usage_router  # noqa: E402
from app.api.notifications import router as notif_router  # noqa: E402
from app.api.chat_sessions import router as chat_sessions_router  # noqa: E402
from app.api.folders import router as folders_router  # noqa: E402
from app.api.dashboard import router as dashboard_router  # noqa: E402
from app.api.workspaces import router as workspaces_router  # noqa: E402
from app.api.admin import router as admin_router  # noqa: E402

app.include_router(chat.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(writing.router, prefix="/api")
app.include_router(writing_v2_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(usage_router, prefix="/api")
app.include_router(notif_router, prefix="/api")
app.include_router(chat_sessions_router, prefix="/api")
app.include_router(folders_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(workspaces_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
