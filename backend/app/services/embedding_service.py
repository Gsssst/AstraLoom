"""向量嵌入服务 — 使用 sentence-transformers 本地模型生成文本向量。"""

import asyncio
import logging
import threading
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# 加载轻量模型（首次运行自动下载，约 80MB）
_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """懒加载 sentence-transformers 模型。"""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info("正在加载 sentence-transformers 模型 (all-MiniLM-L6-v2)...")
                _model = SentenceTransformer("all-MiniLM-L6-v2")
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
