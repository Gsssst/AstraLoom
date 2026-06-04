"""多智能体写作 Pipeline 引擎。

协调 Selector → Reader → Writer → Reviewer → Citation 五个 Agent 协作完成写作任务。
支持按任务类型自动选择阶段、SSE 流式进度推送、取消机制。
"""

import asyncio
import json
import logging
from enum import Enum
from typing import AsyncIterator, Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)


class Phase(str, Enum):
    """Pipeline 阶段枚举。"""
    SELECTOR = "selector"
    READER = "reader"
    WRITER = "writer"
    REVIEWER = "reviewer"
    CITATION = "citation"


class TaskType(str, Enum):
    """写作任务类型 — 决定 Pipeline 阶段配置。"""
    POLISH = "polish"
    ABSTRACT = "abstract"
    RELATED_WORK = "related_work"
    LITERATURE_REVIEW = "literature_review"
    COMPARE_PAPERS = "compare_papers"
    GRANT_WRITE = "grant_write"
    FULL_CHAPTER = "full_chapter"


# Pipeline 阶段配置：轻量/标准/重量
TASK_PHASE_CONFIG: Dict[TaskType, List[Phase]] = {
    TaskType.POLISH: [Phase.WRITER, Phase.REVIEWER],
    TaskType.ABSTRACT: [Phase.WRITER, Phase.REVIEWER],
    TaskType.RELATED_WORK: [Phase.SELECTOR, Phase.READER, Phase.WRITER, Phase.CITATION],
    TaskType.LITERATURE_REVIEW: [Phase.SELECTOR, Phase.READER, Phase.WRITER, Phase.CITATION],
    TaskType.COMPARE_PAPERS: [Phase.SELECTOR, Phase.READER, Phase.WRITER, Phase.REVIEWER],
    TaskType.GRANT_WRITE: [Phase.SELECTOR, Phase.WRITER, Phase.REVIEWER],
    TaskType.FULL_CHAPTER: [Phase.SELECTOR, Phase.READER, Phase.WRITER, Phase.REVIEWER, Phase.CITATION],
}


class PipelineEvent:
    """Pipeline 事件 — 通过 SSE 推送到前端。"""

    def __init__(self, event_type: str, phase: Optional[str] = None,
                 content: Optional[Any] = None, metadata: Optional[dict] = None):
        self.type = event_type
        self.phase = phase
        self.content = content
        self.metadata = metadata or {}

    def to_sse(self) -> str:
        payload = {"type": self.type}
        if self.phase:
            payload["phase"] = self.phase
        if self.content is not None:
            payload["content"] = self.content
        if self.metadata:
            payload["metadata"] = self.metadata
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


class WorkingMemory:
    """Agent 间共享的工作记忆 — 参考 Full_Text_RWG 的设计。"""

    def __init__(self):
        self.papers: List[dict] = []
        self.paper_relations: List[dict] = []
        self.reading_notes: List[dict] = []
        self.writer_output: Optional[str] = None
        self.citation_map: Dict[str, dict] = {}
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> dict:
        return {
            "papers": self.papers,
            "paper_relations": self.paper_relations,
            "reading_notes": self.reading_notes,
            "writer_output": self.writer_output,
            "citation_map": self.citation_map,
            "metadata": self.metadata,
        }


class WritingPipeline:
    """多智能体写作 Pipeline 引擎。

    用法:
        pipeline = WritingPipeline(llm_service, db_session_factory)
        async for event in pipeline.run(task_type="related_work", input_data={...}):
            yield event.to_sse()
    """

    def __init__(self, llm_service=None, db_session_factory=None):
        self.llm = llm_service
        self.db_factory = db_session_factory
        self._cancel_event: Optional[asyncio.Event] = None
        self._current_phase: Optional[Phase] = None
        self.memory = WorkingMemory()
        self._agents: Dict[str, Any] = {}

    async def _ensure_agents(self):
        """懒加载 Agent 实例。"""
        if not self._agents:
            from app.services.agents import (
                SelectorAgent, ReaderAgent, WriterAgent,
                ReviewerAgent, CitationAgent,
            )
            self._agents = {
                Phase.SELECTOR: SelectorAgent(self.llm, self.db_factory),
                Phase.READER: ReaderAgent(self.llm, self.db_factory),
                Phase.WRITER: WriterAgent(self.llm),
                Phase.REVIEWER: ReviewerAgent(self.llm),
                Phase.CITATION: CitationAgent(self.llm),
            }

    def cancel(self):
        """取消当前 Pipeline 执行。"""
        if self._cancel_event:
            self._cancel_event.set()
            logger.info("Pipeline 取消请求已发送")

    async def run(
        self,
        task_type: str,
        input_data: dict,
        phases: Optional[List[str]] = None,
    ) -> AsyncIterator[PipelineEvent]:
        """执行 Pipeline。

        Args:
            task_type: 任务类型 (TaskType 枚举值)
            input_data: 输入数据 (根据任务类型不同)
            phases: 手动指定阶段列表，为空则按任务类型自动选择
        """
        self._cancel_event = asyncio.Event()
        self.memory = WorkingMemory()
        self.memory.metadata["task_type"] = task_type
        self.memory.metadata["input"] = input_data

        await self._ensure_agents()

        # 确定阶段列表
        try:
            task = TaskType(task_type)
            phase_list = phases or [p.value for p in TASK_PHASE_CONFIG.get(task, [Phase.WRITER])]
        except ValueError:
            phase_list = phases or [Phase.WRITER.value]

        phase_enums = [Phase(p) for p in phase_list]

        logger.info(f"Pipeline 启动: task={task_type}, phases={[p.value for p in phase_enums]}")

        yield PipelineEvent("pipeline_start", metadata={
            "task_type": task_type,
            "phases": [p.value for p in phase_enums],
        })

        for phase in phase_enums:
            if self._cancel_event.is_set():
                yield PipelineEvent("cancelled", phase=phase.value)
                return

            self._current_phase = phase
            yield PipelineEvent("phase_start", phase=phase.value)

            try:
                agent = self._agents[phase]
                async for event in agent.execute(self.memory, self._cancel_event):
                    # 检查取消
                    if self._cancel_event.is_set():
                        yield PipelineEvent("cancelled", phase=phase.value)
                        return
                    yield event

                yield PipelineEvent("phase_complete", phase=phase.value)

            except Exception as exc:
                logger.exception(f"Phase {phase.value} 执行失败: {exc}")
                # 尝试重试一次
                if not self._cancel_event.is_set():
                    logger.info(f"Phase {phase.value} 重试中...")
                    try:
                        agent = self._agents[phase]
                        async for event in agent.execute(self.memory, self._cancel_event):
                            if self._cancel_event.is_set():
                                break
                            yield event
                        yield PipelineEvent("phase_complete", phase=phase.value)
                        continue
                    except Exception as retry_exc:
                        logger.error(f"Phase {phase.value} 重试失败: {retry_exc}")

                yield PipelineEvent("error", phase=phase.value, content={
                    "message": f"阶段 {phase.value} 执行失败: {str(exc)}",
                })
                return

        yield PipelineEvent("done", metadata={
            "phases_completed": [p.value for p in phase_enums],
            "has_output": bool(self.memory.writer_output),
        })


async def create_pipeline(
    llm_service=None,
    db_session_factory=None,
) -> WritingPipeline:
    """工厂函数：创建 Pipeline 实例并初始化 Agent。"""
    pipeline = WritingPipeline(llm_service, db_session_factory)
    await pipeline._ensure_agents()
    return pipeline
