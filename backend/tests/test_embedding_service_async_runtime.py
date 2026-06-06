"""Regression tests for local embedding runtime behavior."""

import asyncio
import time

import pytest

from app.services import embedding_service


class _FakeEmbedding:
    def __init__(self, values: list[float]):
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


@pytest.mark.asyncio
async def test_generate_embedding_keeps_event_loop_responsive(monkeypatch):
    class SlowModel:
        def __init__(self, _name: str):
            time.sleep(0.08)

        def get_sentence_embedding_dimension(self) -> int:
            return 2

        def encode(self, _text: str, normalize_embeddings: bool = True) -> _FakeEmbedding:
            time.sleep(0.08)
            return _FakeEmbedding([0.1, 0.2])

    monkeypatch.setattr(embedding_service, "_model", None)
    monkeypatch.setattr(embedding_service, "SentenceTransformer", SlowModel)

    started = time.perf_counter()
    task = asyncio.create_task(embedding_service.generate_embedding("query"))

    await asyncio.sleep(0.01)

    assert time.perf_counter() - started < 0.05
    assert not task.done()
    assert await task == [0.1, 0.2]


@pytest.mark.asyncio
async def test_concurrent_embedding_calls_share_one_model_initialization(monkeypatch):
    init_count = 0

    class SlowModel:
        def __init__(self, _name: str):
            nonlocal init_count
            time.sleep(0.03)
            init_count += 1

        def get_sentence_embedding_dimension(self) -> int:
            return 1

        def encode(self, text: str, normalize_embeddings: bool = True) -> _FakeEmbedding:
            return _FakeEmbedding([float(len(text))])

    monkeypatch.setattr(embedding_service, "_model", None)
    monkeypatch.setattr(embedding_service, "SentenceTransformer", SlowModel)

    results = await asyncio.gather(
        *(embedding_service.generate_embedding(f"query-{index}") for index in range(5))
    )

    assert init_count == 1
    assert results == [[7.0], [7.0], [7.0], [7.0], [7.0]]
