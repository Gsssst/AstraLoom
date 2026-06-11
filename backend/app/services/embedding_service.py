"""向量嵌入服务 — 使用 sentence-transformers 本地模型生成文本向量。"""

import asyncio
import logging
import os
import threading
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# 加载轻量模型（首次运行自动下载，约 80MB）
SentenceTransformer: Any | None = None
_model: Any | None = None
_model_lock = threading.Lock()
_runtime_env_configured = False


def _configure_runtime_environment() -> None:
    """Apply model download/cache environment before sentence-transformers loads."""

    global _runtime_env_configured
    if _runtime_env_configured:
        return

    env_values = {
        "HF_HOME": settings.HF_HOME,
        "TRANSFORMERS_CACHE": settings.TRANSFORMERS_CACHE,
        "SENTENCE_TRANSFORMERS_HOME": settings.SENTENCE_TRANSFORMERS_HOME,
    }
    if settings.HF_ENDPOINT.strip():
        env_values["HF_ENDPOINT"] = settings.HF_ENDPOINT.strip()

    for key, value in env_values.items():
        if value:
            os.environ[key] = value

    _runtime_env_configured = True


def _get_sentence_transformer_class() -> Any:
    global SentenceTransformer
    if SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer as _SentenceTransformer

        SentenceTransformer = _SentenceTransformer
    return SentenceTransformer


def _get_model() -> Any:
    """懒加载 sentence-transformers 模型。"""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _configure_runtime_environment()
                model_name = settings.EMBEDDING_MODEL_NAME
                model_cls = _get_sentence_transformer_class()
                logger.info("正在加载 sentence-transformers 模型 (%s)...", model_name)
                _model = model_cls(model_name)
                logger.info(f"模型加载完成，向量维度: {_model.get_sentence_embedding_dimension()}")
    return _model


def _encode_text(text: str) -> list[float]:
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


async def generate_embedding(text: str) -> list[float]:
    """为文本生成向量嵌入（384 维）。"""
    # 截断过长文本（模型最大支持约 256 token）
    truncated = text[:2000]
    return await asyncio.to_thread(_encode_text, truncated)


async def generate_paper_embedding(title: str, abstract: str) -> list[float]:
    """为论文生成向量嵌入（标题 + 摘要）。"""
    text = f"Title: {title}. Abstract: {abstract}" if abstract else title
    return await generate_embedding(text)
