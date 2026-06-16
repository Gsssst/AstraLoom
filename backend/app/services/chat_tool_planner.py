"""LLM-driven planner for registered chat tools.

The planner owns model prompting and action/observation loop control. Actual
tool execution remains inside ``ChatAgentToolRuntime`` so validation and
side-effect gates stay centralized.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Awaitable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.services.chat_agent_tools import (
    ChatAgentRuntimeState,
    ChatAgentToolRuntime,
    ChatToolCall,
    ChatToolObservation,
    ChatToolRegistry,
    ChatToolTraceEvent,
    chat_tool_context_block,
    default_chat_tool_registry,
    deterministic_chat_tool_plan,
)
from app.services.llm import llm_service

logger = logging.getLogger(__name__)

PlannerStopReason = Literal[
    "completed",
    "max_rounds",
    "planner_invalid",
    "no_actions",
    "waiting_confirmation",
    "fallback_used",
    "failed",
]

PLANNER_CONTEXT_MAX_CHARS = 9000
PLANNER_OBSERVATION_MAX_CHARS = 3500
PLANNER_MAX_ACTIONS_PER_ROUND = 3
PLANNER_DEFAULT_MAX_ROUNDS = 2
PLANNER_DEFAULT_MAX_TOOL_STEPS = 4


class ChatToolPlannerDecision(BaseModel):
    actions: list[ChatToolCall] = Field(default_factory=list)
    final: bool = False
    final_context_summary: str = Field(default="", max_length=2000)


class ChatToolPlannerParseError(BaseModel):
    message: str
    raw_excerpt: str = ""


class ChatToolPlannerRound(BaseModel):
    round_index: int
    raw_response: str = ""
    decision: ChatToolPlannerDecision | None = None
    parse_error: ChatToolPlannerParseError | None = None
    used_fallback: bool = False


class ChatToolPlannerResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    state: ChatAgentRuntimeState
    rounds: list[ChatToolPlannerRound] = Field(default_factory=list)
    fallback_used: bool = False
    stop_reason: PlannerStopReason = "completed"
    final_context_summary: str = ""
    planner_failed: bool = False


PlannerLLM = Callable[[list[dict[str, str]]], Awaitable[str]]


def _json_from_possible_fence(value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError("planner returned empty output")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    raise ValueError("planner output did not contain a JSON object")


def parse_planner_decision(value: str) -> ChatToolPlannerDecision:
    raw_json = _json_from_possible_fence(value)
    parsed = json.loads(raw_json)
    if not isinstance(parsed, dict):
        raise ValueError("planner JSON must be an object")
    try:
        decision = ChatToolPlannerDecision.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"planner JSON failed schema validation: {exc}") from exc
    if len(decision.actions) > PLANNER_MAX_ACTIONS_PER_ROUND:
        decision.actions = decision.actions[:PLANNER_MAX_ACTIONS_PER_ROUND]
    return decision


def _tool_schema_prompt(registry: ChatToolRegistry) -> str:
    return json.dumps(registry.schemas(), ensure_ascii=False, indent=2)


def _compact_messages(messages: list[dict[str, Any]], *, max_chars: int = 3500) -> str:
    parts: list[str] = []
    for message in messages[-10:]:
        role = str(message.get("role") or "unknown")
        content = message.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)[:1200]
        parts.append(f"{role}: {content[:1200]}")
    return "\n\n".join(parts)[-max_chars:]


def _observation_prompt(observations: list[ChatToolObservation]) -> str:
    if not observations:
        return "No observations yet."
    blocks: list[str] = []
    for index, observation in enumerate(observations[-8:], start=1):
        details = {
            "tool": observation.tool,
            "status": observation.status,
            "summary": observation.summary,
            "result_count": observation.result_count,
            "reference_count": len(observation.references),
        }
        context = "\n".join(observation.context_blocks)[:1200]
        blocks.append(f"[OBS-{index}] {json.dumps(details, ensure_ascii=False)}\n{context}")
    return "\n\n".join(blocks)[-PLANNER_OBSERVATION_MAX_CHARS:]


def build_planner_messages(
    *,
    user_query: str,
    registry: ChatToolRegistry,
    conversation_context: list[dict[str, Any]] | None = None,
    observations: list[ChatToolObservation] | None = None,
    round_index: int = 1,
    max_rounds: int = PLANNER_DEFAULT_MAX_ROUNDS,
) -> list[dict[str, str]]:
    system_prompt = (
        "You are a tool-planning controller for a research chat assistant. "
        "Choose only from the registered tools. Return exactly one JSON object, no markdown. "
        "Never claim a side-effect tool completed unless the observation says completed. "
        "If a side-effect tool waits for confirmation, stop planning. "
        "Use tools only when they materially improve the answer; otherwise return final=true with no actions.\n\n"
        "Output schema:\n"
        "{\"actions\":[{\"tool\":\"search_library\",\"arguments\":{\"query\":\"...\",\"limit\":5},"
        "\"thought_summary\":\"why this tool is useful\"}],\"final\":false,\"final_context_summary\":\"\"}\n"
        "When enough evidence is collected, return {\"actions\":[],\"final\":true,\"final_context_summary\":\"brief evidence summary\"}."
    )
    user_prompt = (
        f"Round: {round_index}/{max_rounds}\n"
        f"User query:\n{user_query}\n\n"
        f"Registered tools:\n{_tool_schema_prompt(registry)}\n\n"
        f"Recent conversation context:\n{_compact_messages(conversation_context or [])}\n\n"
        f"Prior tool observations:\n{_observation_prompt(observations or [])}"
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


async def _default_planner_llm(messages: list[dict[str, str]]) -> str:
    return await llm_service.chat(messages=messages, temperature=0.1, max_tokens=1200)


def _planner_trace_event(
    *,
    round_index: int,
    status: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> ChatToolTraceEvent:
    return ChatToolTraceEvent(
        id=f"planner-round-{round_index}-{status}",
        tool="llm_tool_planner",
        label="规划工具",
        status=status,  # type: ignore[arg-type]
        summary=summary,
        details=details or {},
    )


def _should_use_fallback(rounds: list[ChatToolPlannerRound], state: ChatAgentRuntimeState) -> bool:
    if state.observations:
        return all(item.status == "rejected" for item in state.observations)
    if any(item.parse_error for item in rounds):
        return True
    if not rounds:
        return False
    latest = rounds[-1].decision
    return bool(latest and not latest.final and not latest.actions)


async def _run_deterministic_fallback(
    *,
    state: ChatAgentRuntimeState,
    registry: ChatToolRegistry,
    user_query: str,
    max_tool_steps: int,
) -> bool:
    actions = deterministic_chat_tool_plan(user_query)
    if not actions:
        return False
    state.trace_events.append(_planner_trace_event(
        round_index=0,
        status="planned",
        summary="LLM 工具规划不可用，已回退到确定性工具规划。",
        details={"action_count": len(actions), "fallback_used": True},
    ))
    runtime = ChatAgentToolRuntime(registry, max_steps=max_tool_steps)
    await runtime.run(state, actions[:max_tool_steps], allow_side_effects=False)
    state.stop_reason = "fallback_used" if state.stop_reason == "completed" else state.stop_reason
    return True


async def run_llm_tool_planner(
    *,
    user_query: str,
    state: ChatAgentRuntimeState,
    registry: ChatToolRegistry | None = None,
    conversation_context: list[dict[str, Any]] | None = None,
    planner_llm: PlannerLLM | None = None,
    max_rounds: int = PLANNER_DEFAULT_MAX_ROUNDS,
    max_tool_steps: int = PLANNER_DEFAULT_MAX_TOOL_STEPS,
    enable_fallback: bool = True,
) -> ChatToolPlannerResult:
    registry = registry or default_chat_tool_registry()
    planner_llm = planner_llm or _default_planner_llm
    max_rounds = max(1, max_rounds)
    max_tool_steps = max(1, max_tool_steps)
    result = ChatToolPlannerResult(state=state)
    executed_steps = 0

    for round_index in range(1, max_rounds + 1):
        state.trace_events.append(_planner_trace_event(
            round_index=round_index,
            status="running",
            summary="正在让模型规划下一步工具调用。",
            details={"round": round_index, "max_rounds": max_rounds},
        ))
        messages = build_planner_messages(
            user_query=user_query,
            registry=registry,
            conversation_context=conversation_context,
            observations=state.observations,
            round_index=round_index,
            max_rounds=max_rounds,
        )
        try:
            raw = await planner_llm(messages)
            decision = parse_planner_decision(raw)
            planner_round = ChatToolPlannerRound(round_index=round_index, raw_response=raw, decision=decision)
        except Exception as exc:
            logger.warning("LLM tool planner failed on round %s: %s", round_index, exc)
            planner_round = ChatToolPlannerRound(
                round_index=round_index,
                raw_response=locals().get("raw", ""),
                parse_error=ChatToolPlannerParseError(message=str(exc), raw_excerpt=str(locals().get("raw", ""))[:500]),
            )
            result.rounds.append(planner_round)
            state.trace_events.append(_planner_trace_event(
                round_index=round_index,
                status="rejected",
                summary="模型工具规划输出无效。",
                details={"error": planner_round.parse_error.model_dump()},
            ))
            result.stop_reason = "planner_invalid"
            result.planner_failed = True
            break

        result.rounds.append(planner_round)
        action_count = len(decision.actions)
        state.trace_events.append(_planner_trace_event(
            round_index=round_index,
            status="planned",
            summary="模型已规划工具动作。" if action_count else "模型认为无需继续调用工具。",
            details={
                "round": round_index,
                "action_count": action_count,
                "final": decision.final,
                "final_context_summary": decision.final_context_summary,
            },
        ))

        if decision.final and not decision.actions:
            result.stop_reason = "completed"
            result.final_context_summary = decision.final_context_summary
            state.stop_reason = "completed"
            break
        if not decision.actions:
            result.stop_reason = "no_actions"
            state.stop_reason = "no_actions"
            break

        remaining_steps = max_tool_steps - executed_steps
        if remaining_steps <= 0:
            result.stop_reason = "max_rounds"
            state.stop_reason = "max_rounds"
            break
        actions = decision.actions[:remaining_steps]
        runtime = ChatAgentToolRuntime(registry, max_steps=remaining_steps)
        before_count = len(state.observations)
        await runtime.run(state, actions, allow_side_effects=False)
        executed_steps += len(state.observations) - before_count

        if any(item.status == "waiting_confirmation" for item in state.observations[before_count:]):
            result.stop_reason = "waiting_confirmation"
            state.stop_reason = "waiting_confirmation"
            break
        if executed_steps >= max_tool_steps:
            result.stop_reason = "max_rounds"
            state.stop_reason = "max_rounds"
            break
    else:
        result.stop_reason = "max_rounds"
        state.stop_reason = "max_rounds"

    if enable_fallback and _should_use_fallback(result.rounds, state):
        fallback_used = await _run_deterministic_fallback(
            state=state,
            registry=registry,
            user_query=user_query,
            max_tool_steps=max_tool_steps,
        )
        result.fallback_used = fallback_used
        if fallback_used:
            result.stop_reason = "fallback_used"
            state.stop_reason = "fallback_used"

    if result.final_context_summary:
        state.context_blocks.append(f"[PLANNER-SUMMARY] {result.final_context_summary}")
    return result


def planner_tool_context_block(result: ChatToolPlannerResult) -> str:
    return chat_tool_context_block(result.state)[:PLANNER_CONTEXT_MAX_CHARS]


def planner_tool_trace_payload(result: ChatToolPlannerResult, registry: ChatToolRegistry | None = None) -> dict[str, Any]:
    registry = registry or default_chat_tool_registry()
    return {
        "enabled": bool(result.state.trace_events),
        "workflow": "llm_tool_planner",
        "stop_reason": result.stop_reason,
        "fallback_used": result.fallback_used,
        "planner_rounds": [item.model_dump() for item in result.rounds],
        "tools": registry.schemas(),
        "steps": [event.model_dump() for event in result.state.trace_events],
    }
