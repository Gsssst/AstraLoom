import asyncio
import sys
from types import SimpleNamespace

import pytest

from app.services import report_service


def test_pdf_text_extraction_uses_pdfplumber_without_optional_fitz(monkeypatch):
    class _FakePdf:
        pages = [
            SimpleNamespace(extract_text=lambda: "1 Introduction\nGrounded introduction."),
            SimpleNamespace(extract_text=lambda: "2 Method\nGrounded method."),
        ]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    monkeypatch.setitem(sys.modules, "pdfplumber", SimpleNamespace(open=lambda _path: _FakePdf()))
    monkeypatch.delitem(sys.modules, "fitz", raising=False)

    text = report_service._extract_pdf_text("/tmp/fake.pdf")

    assert "1 Introduction" in text
    assert "Grounded method." in text


@pytest.mark.asyncio
async def test_full_text_loading_is_shared_and_survives_foreground_cancellation(monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()
    calls = []
    paper = SimpleNamespace(id="paper-1", arxiv_id="2606.00001", abstract="摘要", full_text=None)

    async def _fake_download(current_paper):
        calls.append(current_paper.id)
        started.set()
        await release.wait()
        current_paper.full_text = "Introduction\n" + "grounded text " * 60
        return current_paper.full_text

    report_service._full_text_tasks.clear()
    monkeypatch.setattr(report_service, "_download_and_parse_full_text", _fake_download)

    first_waiter = asyncio.create_task(report_service.ensure_full_text(paper))
    await started.wait()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(first_waiter, timeout=0.001)

    second_waiter = asyncio.create_task(report_service.ensure_full_text(paper))
    release.set()
    result = await second_waiter

    assert calls == ["paper-1"]
    assert result == paper.full_text
    assert "Introduction" in result
