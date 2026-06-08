"""Tests for paper-detail AI insight helpers."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import papers as papers_api


def test_parse_insight_sections_maps_required_markdown_headings():
    parsed = papers_api._parse_insight_sections(
        """## 核心贡献
- 提出新的检索增强流程
## 可借鉴方法
- 分阶段评估
## 可复现实验
- 提供数据集和指标
## 局限
- 规模有限
## 研究缺口
- 缺少长期验证
## 研究方向关联
- 可用于论文库智能筛选
"""
    )

    assert parsed["contribution"] == "提出新的检索增强流程"
    assert parsed["reusable_methods"] == "分阶段评估"
    assert parsed["reproducible_experiments"] == "提供数据集和指标"
    assert parsed["limitations"] == "规模有限"
    assert parsed["research_gaps"] == "缺少长期验证"
    assert parsed["research_fit"] == "可用于论文库智能筛选"


@pytest.mark.asyncio
async def test_paper_ai_insights_returns_metadata_cache_without_llm(monkeypatch):
    paper_id = uuid4()
    cached = {
        "paper_id": str(paper_id),
        "generated_at": "2026-06-08T00:00:00+00:00",
        "evidence_coverage": "full_text",
        "contribution": "cached contribution",
        "reusable_methods": "cached method",
        "reproducible_experiments": "cached experiment",
        "limitations": "cached limitation",
        "research_gaps": "cached gap",
        "research_fit": "cached fit",
        "raw": "cached raw",
    }
    paper = SimpleNamespace(
        id=paper_id,
        title="Cached Paper",
        metadata_json={"ai_insights": cached},
    )

    class _Result:
        def scalar_one_or_none(self):
            return paper

    class _Db:
        committed = False

        async def execute(self, _query):
            return _Result()

        async def commit(self):
            self.committed = True

    async def fail_chat(*_args, **_kwargs):
        raise AssertionError("cached insights should not call LLM")

    monkeypatch.setattr(papers_api.llm_service, "chat", fail_chat)
    db = _Db()

    response = await papers_api.get_paper_ai_insights(
        str(paper_id),
        refresh=False,
        db=db,
        user=SimpleNamespace(id=uuid4()),
    )

    assert response.paper_id == str(paper_id)
    assert response.contribution == "cached contribution"
    assert db.committed is False
