from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import writing as writing_api
from app.services import report_service
from app.services.report_service import ReportService


class _ScalarResult:
    def __init__(self, paper):
        self.paper = paper

    def scalar_one_or_none(self):
        return self.paper


class _Session:
    def __init__(self, papers):
        self.papers = list(papers)
        self.index = 0
        self.committed = False

    async def execute(self, _query):
        paper = self.papers[self.index] if self.index < len(self.papers) else None
        self.index += 1
        return _ScalarResult(paper)

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_custom_group_report_uses_user_prompt_for_global_report(monkeypatch):
    captured = {}
    paper = SimpleNamespace(
        id=uuid4(),
        title="Video Grounding",
        authors=["Alice", "Bob"],
        year=2026,
        arxiv_id="2606.00001",
        abstract="Ground long videos.",
        full_text="Full text about datasets and methods.",
    )

    async def fake_ensure_full_text(_paper):
        return _paper.full_text

    async def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        captured["kwargs"] = kwargs
        return "## 横向比较\n- 按方法脉络汇报"

    monkeypatch.setattr(report_service, "ensure_full_text", fake_ensure_full_text)
    monkeypatch.setattr(report_service.llm_service, "chat", fake_chat)

    result = await ReportService(_Session([paper])).generate_report(
        [str(paper.id)],
        "自定义组会",
        custom_prompt="不要逐篇汇报，请按方法脉络横向比较。",
    )

    prompt = captured["messages"][0]["content"]
    assert "不要逐篇汇报，请按方法脉络横向比较。" in prompt
    assert "Video Grounding" in prompt
    assert result["custom_report"].startswith("## 横向比较")
    assert result["custom_prompt"] == "不要逐篇汇报，请按方法脉络横向比较。"


@pytest.mark.asyncio
async def test_group_report_preset_combines_with_custom_prompt(monkeypatch):
    captured = {}
    paper = SimpleNamespace(
        id=uuid4(),
        title="Retrieval Augmented Research",
        authors=["Alice"],
        year=2026,
        arxiv_id=None,
        abstract="Study retrieval augmented research workflows.",
        full_text="Full text about retrieval and experiments.",
    )

    async def fake_ensure_full_text(_paper):
        return _paper.full_text

    async def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        return "## 复现报告\n- 数据集与指标"

    monkeypatch.setattr(report_service, "ensure_full_text", fake_ensure_full_text)
    monkeypatch.setattr(report_service.llm_service, "chat", fake_chat)

    result = await ReportService(_Session([paper])).generate_report(
        [str(paper.id)],
        "复现导向组会",
        custom_prompt="请最后给出复现优先级。",
        report_preset="reproduction",
    )

    prompt = captured["messages"][0]["content"]
    assert "实验复现角度" in prompt
    assert "数据集、指标、baseline" in prompt
    assert "请最后给出复现优先级。" in prompt
    assert result["report_preset"] == "reproduction"
    assert "请最后给出复现优先级。" in result["custom_prompt"]


def test_group_report_docx_font_helper_sets_latin_and_east_asia_fonts():
    from docx import Document

    doc = Document()
    writing_api._configure_report_doc_fonts(doc)
    paragraph = writing_api._add_report_paragraph(doc, "中文 Chinese")

    xml = paragraph.runs[0]._element.xml
    style_xml = doc.styles["Normal"]._element.xml

    assert 'w:eastAsia="宋体"' in xml
    assert 'w:ascii="Times New Roman"' in xml
    assert 'w:hAnsi="Times New Roman"' in xml
    assert 'w:eastAsia="宋体"' in style_xml
