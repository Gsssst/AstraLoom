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
    monkeypatch.setattr(embedding_service, "_runtime_env_configured", False)
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
    monkeypatch.setattr(embedding_service, "_runtime_env_configured", False)
    monkeypatch.setattr(embedding_service, "SentenceTransformer", SlowModel)

    results = await asyncio.gather(
        *(embedding_service.generate_embedding(f"query-{index}") for index in range(5))
    )

    assert init_count == 1
    assert results == [[7.0], [7.0], [7.0], [7.0], [7.0]]


@pytest.mark.asyncio
async def test_generate_embedding_uses_configured_model_name(monkeypatch):
    loaded_names: list[str] = []

    class Model:
        def __init__(self, name: str):
            loaded_names.append(name)

        def get_sentence_embedding_dimension(self) -> int:
            return 1

        def encode(self, _text: str, normalize_embeddings: bool = True) -> _FakeEmbedding:
            return _FakeEmbedding([0.5])

    monkeypatch.setattr(embedding_service, "_model", None)
    monkeypatch.setattr(embedding_service, "_runtime_env_configured", False)
    monkeypatch.setattr(embedding_service, "SentenceTransformer", Model)
    monkeypatch.setattr(embedding_service.settings, "EMBEDDING_MODEL_NAME", "/app/model-cache/local-minilm")

    assert await embedding_service.generate_embedding("query") == [0.5]
    assert loaded_names == ["/app/model-cache/local-minilm"]


@pytest.mark.asyncio
async def test_generate_embedding_applies_huggingface_runtime_env(monkeypatch):
    seen_env: dict[str, str | None] = {}

    class Model:
        def __init__(self, _name: str):
            seen_env["HF_ENDPOINT"] = embedding_service.os.environ.get("HF_ENDPOINT")
            seen_env["HF_HOME"] = embedding_service.os.environ.get("HF_HOME")
            seen_env["TRANSFORMERS_CACHE"] = embedding_service.os.environ.get("TRANSFORMERS_CACHE")
            seen_env["SENTENCE_TRANSFORMERS_HOME"] = embedding_service.os.environ.get("SENTENCE_TRANSFORMERS_HOME")

        def get_sentence_embedding_dimension(self) -> int:
            return 1

        def encode(self, _text: str, normalize_embeddings: bool = True) -> _FakeEmbedding:
            return _FakeEmbedding([0.7])

    for key in ("HF_ENDPOINT", "HF_HOME", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME"):
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setattr(embedding_service, "_model", None)
    monkeypatch.setattr(embedding_service, "_runtime_env_configured", False)
    monkeypatch.setattr(embedding_service, "SentenceTransformer", Model)
    monkeypatch.setattr(embedding_service.settings, "HF_ENDPOINT", "https://hf-mirror.com")
    monkeypatch.setattr(embedding_service.settings, "HF_HOME", "/cache/hf")
    monkeypatch.setattr(embedding_service.settings, "TRANSFORMERS_CACHE", "/cache/transformers")
    monkeypatch.setattr(embedding_service.settings, "SENTENCE_TRANSFORMERS_HOME", "/cache/st")

    assert await embedding_service.generate_embedding("query") == [0.7]
    assert seen_env == {
        "HF_ENDPOINT": "https://hf-mirror.com",
        "HF_HOME": "/cache/hf",
        "TRANSFORMERS_CACHE": "/cache/transformers",
        "SENTENCE_TRANSFORMERS_HOME": "/cache/st",
    }


def test_huggingface_endpoint_defaults_to_mirror():
    assert embedding_service.settings.HF_ENDPOINT == "https://hf-mirror.com"


def test_runtime_env_overrides_existing_huggingface_endpoint(monkeypatch):
    monkeypatch.setenv("HF_ENDPOINT", "https://huggingface.co")
    monkeypatch.setattr(embedding_service, "_runtime_env_configured", False)
    monkeypatch.setattr(embedding_service.settings, "HF_ENDPOINT", "https://hf-mirror.com")

    embedding_service._configure_runtime_environment()

    assert embedding_service.os.environ["HF_ENDPOINT"] == "https://hf-mirror.com"
