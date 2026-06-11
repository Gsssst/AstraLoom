"""应用配置管理 — 使用 Pydantic Settings 从环境变量加载配置。"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用全局配置，所有值从环境变量或 .env 文件加载。"""

    # --- 应用 ---
    APP_NAME: str = "AstraLoom"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change_me_to_random_secret_key"

    # --- 服务器 ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- 数据库 ---
    POSTGRES_USER: str = "auto_research"
    POSTGRES_PASSWORD: str = "change_me"
    POSTGRES_DB: str = "auto_research_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Alembic 使用的同步数据库 URL。"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- LLM ---
    LLM_PROVIDER: str = "deepseek"  # deepseek, openai-compatible
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    OPENAI_COMPATIBLE_API_KEY: str = ""
    OPENAI_COMPATIBLE_API_BASE: str = ""
    OPENAI_COMPATIBLE_MODEL: str = "gpt-5.5"
    LLM_RUNTIME_CONFIG_PATH: str = "./uploads/llm-runtime-config.json"
    USAGE_DEEPSEEK_INPUT_CNY_PER_1M: float = 3.0
    USAGE_DEEPSEEK_OUTPUT_CNY_PER_1M: float = 6.0
    USAGE_OPENAI_COMPATIBLE_INPUT_CNY_PER_1M: float = 0.0
    USAGE_OPENAI_COMPATIBLE_OUTPUT_CNY_PER_1M: float = 0.0
    USAGE_FALLBACK_INPUT_CNY_PER_1M: float = 3.0
    USAGE_FALLBACK_OUTPUT_CNY_PER_1M: float = 6.0

    # --- 联网搜索（可选；未配置时回退到 Bing + DuckDuckGo HTML） ---
    SEARXNG_API_URL: str = ""
    TAVILY_API_KEY: str = ""
    EXA_API_KEY: str = ""
    BRAVE_SEARCH_API_KEY: str = ""

    # --- 学术检索（可选） ---
    ARXIV_API_BASE: str = "https://arxiv.org/api/query"
    ARXIV_API_FALLBACK_BASE: str = "https://export.arxiv.org/api/query"
    ARXIV_SEARCH_TIMEOUT_SECONDS: float = 6.0
    ARXIV_REQUEST_DELAY_SECONDS: float = 3.0
    ARXIV_CACHE_TTL_SECONDS: float = 300.0
    ARXIV_PDF_MIRROR_BASE_URLS: str = ""
    ARXIV_PDF_OFFICIAL_BASE_URL: str = "https://arxiv.org/pdf"
    ARXIV_PDF_CACHE_DIR: str = "./uploads/arxiv-pdfs"
    ARXIV_PDF_TIMEOUT_SECONDS: float = 30.0
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    OPENALEX_MAILTO: str = ""
    SERPAPI_API_KEY: str = ""

    # --- 本地向量模型 ---
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    HF_ENDPOINT: str = "https://hf-mirror.com"
    HF_HOME: str = "./model-cache/huggingface"
    TRANSFORMERS_CACHE: str = "./model-cache/transformers"
    SENTENCE_TRANSFORMERS_HOME: str = "./model-cache/sentence-transformers"

    # --- 飞书 ---
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def arxiv_pdf_base_urls(self) -> List[str]:
        """Configured mirrors first, official arXiv PDF origin last."""

        candidates = [
            *self.ARXIV_PDF_MIRROR_BASE_URLS.split(","),
            self.ARXIV_PDF_OFFICIAL_BASE_URL,
        ]
        return list(dict.fromkeys(url.strip().rstrip("/") for url in candidates if url.strip()))

    # --- 文件上传 ---
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # --- 日志 ---
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
