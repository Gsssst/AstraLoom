"""多智能体模块 — 参考 OpenDraft + Full_Text_RWG 的 Agent 架构设计。

每个 Agent 封装专用 System Prompt + 工具调用，共享同一个 LLM 实例。
Agent 通过 WorkingMemory 进行协作，不需要额外的通信协议。
"""

import abc
import logging
import asyncio
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)


class BaseAgent(abc.ABC):
    """Agent 基类 — 所有写作 Agent 的抽象基类。"""

    def __init__(self, llm_service=None, db_session_factory=None):
        self.llm = llm_service
        self.db_factory = db_session_factory

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Agent 名称，用于日志和调试。"""
        ...

    @abc.abstractmethod
    async def execute(
        self,
        memory,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncIterator:
        """执行 Agent 的核心逻辑。

        Args:
            memory: WorkingMemory 实例，Agent 间共享状态
            cancel_event: 取消信号

        Yields:
            PipelineEvent 实例
        """
        ...

    def _check_cancelled(self, cancel_event: Optional[asyncio.Event]):
        """检查是否被取消。"""
        if cancel_event and cancel_event.is_set():
            raise asyncio.CancelledError(f"Agent {self.name} 被取消")


from app.services.agents.selector_agent import SelectorAgent
from app.services.agents.reader_agent import ReaderAgent
from app.services.agents.writer_agent import WriterAgent
from app.services.agents.reviewer_agent import ReviewerAgent
from app.services.agents.citation_agent import CitationAgent

__all__ = [
    "BaseAgent",
    "SelectorAgent",
    "ReaderAgent",
    "WriterAgent",
    "ReviewerAgent",
    "CitationAgent",
]
