"""Controlled Research Scout agent loop and tool registry."""

from __future__ import annotations

import inspect
import json
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)

TraceStatus = Literal["planned", "running", "completed", "failed", "skipped", "rejected", "available"]


class ResearchScoutConstraints(BaseModel):
    original_query: str
    search_depth: Literal["quick", "standard", "deep"] = "standard"
    requested_count: int | None = None
    final_limit: int = 8
    year_from: int | None = None
    year_to: int | None = None
    venues: list[str] = Field(default_factory=list)
    institutions: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    constraint_mode: Literal["hard", "soft"] = "soft"


class ResearchScoutToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    thought_summary: str = ""


class ResearchScoutToolObservation(BaseModel):
    tool: str
    status: TraceStatus = "completed"
    summary: str = ""
    result_count: int = 0
    excluded_count: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


class ResearchScoutTraceEvent(BaseModel):
    id: str
    tool: str
    label: str
    status: TraceStatus
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)


class ResearchScoutAgentState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    constraints: ResearchScoutConstraints
    intent: dict[str, Any] = Field(default_factory=dict)
    planned_queries: list[str] = Field(default_factory=list)
    expanded_queries: list[str] = Field(default_factory=list)
    papers: list[Any] = Field(default_factory=list)
    filtered_papers: list[Any] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    references: list[dict[str, Any]] = Field(default_factory=list)
    system_context: list[dict[str, str]] = Field(default_factory=list)
    retrieval: dict[str, Any] = Field(default_factory=dict)
    observations: list[ResearchScoutToolObservation] = Field(default_factory=list)
    trace_events: list[ResearchScoutTraceEvent] = Field(default_factory=list)
    stop_reason: str = ""


class EmptyToolArgs(BaseModel):
    pass


ToolExecutor = Callable[[BaseModel, ResearchScoutAgentState], Awaitable[ResearchScoutToolObservation] | ResearchScoutToolObservation]


@dataclass(frozen=True)
class ResearchScoutToolDefinition:
    name: str
    label: str
    args_model: type[BaseModel]
    executor: ToolExecutor
    side_effect: bool = False

    def schema_summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "side_effect": self.side_effect,
            "parameters": self.args_model.model_json_schema(),
        }


class ResearchScoutToolRegistry:
    def __init__(self):
        self._tools: dict[str, ResearchScoutToolDefinition] = {}

    def register(self, definition: ResearchScoutToolDefinition) -> None:
        self._tools[definition.name] = definition

    def get(self, name: str) -> ResearchScoutToolDefinition | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema_summary() for tool in self._tools.values()]

    async def execute(
        self,
        call: ResearchScoutToolCall,
        state: ResearchScoutAgentState,
        *,
        allow_side_effects: bool = False,
    ) -> ResearchScoutToolObservation:
        definition = self.get(call.tool)
        if not definition:
            return ResearchScoutToolObservation(
                tool=call.tool,
                status="rejected",
                summary=f"Unknown Research Scout tool: {call.tool}",
                details={"allowed_tools": list(self._tools)},
            )
        if definition.side_effect and not allow_side_effects:
            return ResearchScoutToolObservation(
                tool=call.tool,
                status="rejected",
                summary="Side-effect tools require explicit user confirmation.",
                details={"side_effect": True},
            )
        try:
            args = definition.args_model.model_validate(call.arguments or {})
        except ValidationError as exc:
            return ResearchScoutToolObservation(
                tool=call.tool,
                status="rejected",
                summary="Tool arguments failed validation.",
                details={"errors": exc.errors()},
            )
        try:
            result = definition.executor(args, state)
            if inspect.isawaitable(result):
                result = await result
            return result
        except Exception as exc:
            logger.exception("Research Scout tool failed: %s", call.tool)
            return ResearchScoutToolObservation(
                tool=call.tool,
                status="failed",
                summary=f"{definition.label} failed: {exc}",
                details={"error": str(exc)},
            )


class ResearchScoutAgent:
    def __init__(self, registry: ResearchScoutToolRegistry, *, max_steps: int = 10):
        self.registry = registry
        self.max_steps = max(1, max_steps)

    async def run(
        self,
        state: ResearchScoutAgentState,
        actions: list[ResearchScoutToolCall],
    ) -> ResearchScoutAgentState:
        for index, call in enumerate(actions[:self.max_steps], start=1):
            definition = self.registry.get(call.tool)
            label = definition.label if definition else call.tool
            running = ResearchScoutTraceEvent(
                id=f"agent-{index}-{call.tool}",
                tool=call.tool,
                label=label,
                status="running",
                summary=call.thought_summary or f"Running {call.tool}",
                details={"arguments": call.arguments},
            )
            state.trace_events.append(running)
            observation = await self.registry.execute(call, state)
            state.observations.append(observation)
            state.trace_events.append(ResearchScoutTraceEvent(
                id=f"agent-{index}-{call.tool}-done",
                tool=call.tool,
                label=label,
                status=observation.status,
                summary=observation.summary,
                details={
                    **observation.details,
                    "result_count": observation.result_count,
                    "excluded_count": observation.excluded_count,
                },
            ))
            if observation.status in {"failed", "rejected"}:
                state.stop_reason = f"{call.tool}:{observation.status}"
                continue
        if len(actions) > self.max_steps:
            state.stop_reason = "max_steps"
        elif not state.stop_reason:
            state.stop_reason = "completed"
        return state


def parse_research_scout_action_json(value: str) -> list[ResearchScoutToolCall]:
    """Parse strict JSON action output from a model into validated tool calls."""

    cleaned = (value or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()
    parsed = json.loads(cleaned)
    raw_actions = parsed.get("actions") if isinstance(parsed, dict) else parsed
    if not isinstance(raw_actions, list):
        raise ValueError("Research Scout action JSON must contain an actions array")
    return [ResearchScoutToolCall.model_validate(item) for item in raw_actions if isinstance(item, dict)]
