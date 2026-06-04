"""论文相关异步任务 — 论文下载、PDF 解析、向量化等耗时操作。"""

import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="download_paper")
def download_paper(self, arxiv_id: str, download_dir: str | None = None):
    """异步缓存 arXiv 论文 PDF。"""
    from app.services.arxiv_pdf_cache import ensure_cached_arxiv_pdf_sync

    try:
        cached_pdf = ensure_cached_arxiv_pdf_sync(arxiv_id, cache_dir=download_dir)
        logger.info("论文缓存完成: %s", arxiv_id)
        return {
            "status": "success",
            "arxiv_id": cached_pdf.arxiv_id,
            "filepath": cached_pdf.path,
            "cache_hit": cached_pdf.cache_hit,
            "source_url": cached_pdf.source_url,
        }
    except Exception as e:
        logger.error(f"论文下载失败 {arxiv_id}: {e}")
        return {"status": "error", "arxiv_id": arxiv_id, "error": str(e)}


@celery_app.task(bind=True, name="parse_pdf")
def parse_pdf(self, filepath: str):
    """异步解析论文 PDF，提取文本内容。"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        logger.info(f"PDF 解析完成: {filepath} ({len(text)} 字符)")
        return {"status": "success", "filepath": filepath, "text": text[:100000]}
    except Exception as e:
        logger.error(f"PDF 解析失败 {filepath}: {e}")
        return {"status": "error", "filepath": filepath, "error": str(e)}


@celery_app.task(bind=True, name="generate_embedding")
def generate_embedding(self, text: str, model: str = "text-embedding-3-small"):
    """异步生成文本向量嵌入。"""
    import litellm
    from app.core.config import settings

    try:
        response = litellm.embedding(
            model=f"openai/{model}",
            input=[text[:8000]],  # 限制输入长度
            api_key=settings.DEEPSEEK_API_KEY,
            api_base=settings.DEEPSEEK_API_BASE,
        )
        embedding = response.data[0]["embedding"]
        logger.info(f"向量生成完成: 维度={len(embedding)}")
        return {"status": "success", "embedding": embedding}
    except Exception as e:
        logger.error(f"向量生成失败: {e}")
        return {"status": "error", "error": str(e)}
