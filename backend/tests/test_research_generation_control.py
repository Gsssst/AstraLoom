"""Regression tests for controllable Research Idea Workbench generation."""

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import research


RESEARCH_API_SOURCE = Path(__file__).resolve().parents[1] / "app" / "api" / "research.py"


class _CancelSession:
    def __init__(self):
        self.commits = 0
        self.refreshes = 0

    async def commit(self):
        self.commits += 1

    async def refresh(self, _item):
        self.refreshes += 1


def _run(status="running", **overrides):
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "status": status,
        "stage": "generating",
        "progress": 56,
        "message": "正在通过多条路径生成候选假设",
        "config_json": {},
        "evidence_map": {"seed": [{"paper_id": "p1"}]},
        "gap_map": {"gaps": []},
        "candidate_pool": [{"title": "candidate"}],
        "review_summary": None,
        "error": "previous transient error",
        "ideas": [],
        "created_at": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_gap_continuation_stream_endpoint_is_registered():
    source = RESEARCH_API_SOURCE.read_text()

    assert 'continue-from-gaps/stream' in source
    assert 'continue_idea_run_from_gaps_stream' in source
    assert '_stream_idea_run_execution' in source
    assert 'service.continue_from_gap_review' in source


@pytest.mark.asyncio
async def test_cancel_idea_run_marks_running_run_cancelled_and_preserves_progress():
    session = _CancelSession()
    run = _run(status="running")

    cancelled = await research._cancel_idea_run(session, run)

    assert cancelled.status == "cancelled"
    assert cancelled.stage == "generating"
    assert cancelled.progress == 56
    assert cancelled.candidate_pool == [{"title": "candidate"}]
    assert cancelled.message == "已停止生成候选 Proposal"
    assert cancelled.error is None
    assert session.commits == 1
    assert session.refreshes == 1


@pytest.mark.asyncio
async def test_cancel_idea_run_is_idempotent_for_terminal_statuses():
    for status in ("complete", "failed", "cancelled"):
        session = _CancelSession()
        run = _run(status=status, message="terminal", error="terminal error")

        response = await research._cancel_idea_run(session, run)

        assert response.status == status
        assert response.message == "terminal"
        assert response.error == "terminal error"
        assert session.commits == 0
        assert session.refreshes == 0


@pytest.mark.asyncio
async def test_cancel_idea_run_endpoint_requires_matching_project(monkeypatch):
    project_id = uuid4()
    run = _run(status="running", project_id=uuid4())

    async def fake_project(*_args, **_kwargs):
        return SimpleNamespace(id=project_id)

    async def fake_run(*_args, **_kwargs):
        return run

    monkeypatch.setattr(research, "_get_workspace_accessible_project", fake_project)
    monkeypatch.setattr(research, "_get_owned_run", fake_run)

    with pytest.raises(HTTPException) as exc:
        await research.cancel_idea_run(
            project_id=str(project_id),
            run_id=str(run.id),
            db=_CancelSession(),
            current_user=SimpleNamespace(id=uuid4()),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_cancel_idea_run_endpoint_returns_cancelled_run(monkeypatch):
    project_id = uuid4()
    run = _run(status="running", project_id=project_id)
    session = _CancelSession()

    async def fake_project(*_args, **_kwargs):
        return SimpleNamespace(id=project_id)

    async def fake_run(*_args, **_kwargs):
        return run

    monkeypatch.setattr(research, "_get_workspace_accessible_project", fake_project)
    monkeypatch.setattr(research, "_get_owned_run", fake_run)

    response = await research.cancel_idea_run(
        project_id=str(project_id),
        run_id=str(run.id),
        db=session,
        current_user=SimpleNamespace(id=uuid4()),
    )

    assert response.status == "cancelled"
    assert response.stage == "generating"
    assert response.progress == 56
    assert session.commits == 1


@pytest.mark.asyncio
async def test_stream_idea_run_emits_heartbeat_when_business_events_pause(monkeypatch):
    run = _run(status="running")
    session = _CancelSession()
    wait_for_calls = []

    async def is_disconnected():
        return False

    request = SimpleNamespace(is_disconnected=is_disconnected)

    async def fake_wait_for(awaitable, timeout):
        wait_for_calls.append(timeout)
        if hasattr(awaitable, "close"):
            awaitable.close()
        raise research.asyncio.TimeoutError

    async def slow_execute(_push):
        await research.asyncio.sleep(60)
        return []

    monkeypatch.setattr(research.asyncio, "wait_for", fake_wait_for)

    response = research._stream_idea_run_execution(
        db=session,
        request=request,
        run=run,
        execute_factory=slow_execute,
    )
    stream = response.body_iterator

    first = await anext(stream)
    second = await anext(stream)
    await stream.aclose()

    assert '"type": "run"' in first
    assert second == ": ping\n\n"
    assert wait_for_calls == [15]
