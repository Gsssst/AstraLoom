"""全局异常定义和异常处理中间件。"""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """应用基础异常，所有自定义异常由此派生。"""

    def __init__(self, message: str, status_code: int = 500, detail: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源未找到异常。"""

    def __init__(self, message: str = "资源未找到"):
        super().__init__(message, status_code=404)


class UnauthorizedException(AppException):
    """未认证异常。"""

    def __init__(self, message: str = "未认证"):
        super().__init__(message, status_code=401)


class ForbiddenException(AppException):
    """无权限异常。"""

    def __init__(self, message: str = "无权限"):
        super().__init__(message, status_code=403)


class BadRequestException(AppException):
    """错误的请求参数异常。"""

    def __init__(self, message: str = "请求参数错误"):
        super().__init__(message, status_code=400)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """处理 AppException 及其子类。"""
    logger.warning(f"应用异常: {exc.message} (status={exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "detail": exc.detail,
            },
            "status": exc.status_code,
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理 Starlette/FastAPI 内置 HTTP 异常。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": str(exc.detail),
            },
            "status": exc.status_code,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求参数校验异常。"""
    logger.warning(f"参数校验失败: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "请求参数校验失败",
                "detail": exc.errors(),
            },
            "status": 422,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常。"""
    logger.exception(f"未处理异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "服务器内部错误" if not request.app.debug else str(exc),
            },
            "status": 500,
        },
    )
