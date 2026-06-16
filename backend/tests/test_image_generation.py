import httpx
import pytest

from app.services import image_generation
from app.services.image_generation import (
    ImageGenerationConfigurationError,
    ImageGenerationProviderResponseError,
    ImageGenerationRequest,
    generate_image,
    openai_image_payload,
    parse_openai_image_response,
)


def test_openai_image_payload_bounds_prompt_and_generation_settings():
    payload = openai_image_payload(
        ImageGenerationRequest(
            prompt="Draw a video grounding method diagram",
            purpose="paper figure draft",
            style="flat academic diagram",
            size="1024x1536",
            quality="high",
            count=2,
        ),
        model="gpt-image-1",
    )

    assert payload["model"] == "gpt-image-1"
    assert payload["size"] == "1024x1536"
    assert payload["quality"] == "high"
    assert payload["n"] == 2
    assert "Draw a video grounding method diagram" in payload["prompt"]
    assert "paper figure draft" in payload["prompt"]


def test_parse_openai_image_response_accepts_base64_and_url_artifacts():
    artifacts = parse_openai_image_response(
        {
            "data": [
                {"b64_json": "aGVsbG8=", "revised_prompt": "revised"},
                {"url": "https://example.com/image.png"},
            ]
        },
        provider="openai-compatible",
        model="gpt-image-1",
        size="1024x1024",
    )

    assert artifacts[0].data_url == "data:image/png;base64,aGVsbG8="
    assert artifacts[0].revised_prompt == "revised"
    assert artifacts[1].data_url == "https://example.com/image.png"
    assert artifacts[1].source_url == "https://example.com/image.png"


def test_parse_openai_image_response_rejects_missing_image_data():
    with pytest.raises(ImageGenerationProviderResponseError):
        parse_openai_image_response({"data": [{}]}, provider="openai-compatible", model="gpt-image-1", size="1024x1024")


@pytest.mark.asyncio
async def test_generate_image_rejects_missing_configuration(monkeypatch):
    monkeypatch.setattr(image_generation.settings, "OPENAI_COMPATIBLE_API_KEY", "")
    monkeypatch.setattr(image_generation.settings, "OPENAI_COMPATIBLE_API_BASE", "")
    monkeypatch.setattr(image_generation.settings, "IMAGE_GENERATION_MODEL", "gpt-image-1")

    with pytest.raises(ImageGenerationConfigurationError):
        await generate_image(ImageGenerationRequest(prompt="draw a diagram"))


@pytest.mark.asyncio
async def test_generate_image_calls_openai_compatible_endpoint(monkeypatch):
    requests = []

    class FakeClient:
        async def post(self, url, headers=None, json=None):
            requests.append({"url": url, "headers": headers, "json": json})
            return httpx.Response(
                200,
                json={"data": [{"b64_json": "aGVsbG8=", "revised_prompt": "clean diagram"}]},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(image_generation.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-test")
    monkeypatch.setattr(image_generation.settings, "OPENAI_COMPATIBLE_API_BASE", "https://llm.example.com/v1")
    monkeypatch.setattr(image_generation.settings, "IMAGE_GENERATION_PROVIDER", "openai-compatible")
    monkeypatch.setattr(image_generation.settings, "IMAGE_GENERATION_MODEL", "gpt-image-1")

    result = await generate_image(
        ImageGenerationRequest(prompt="draw a diagram", count=1),
        client=FakeClient(),
    )

    assert requests[0]["url"] == "https://llm.example.com/v1/images/generations"
    assert requests[0]["headers"]["Authorization"] == "Bearer sk-test"
    assert requests[0]["json"]["model"] == "gpt-image-1"
    assert result.artifacts[0].data_url.startswith("data:image/png;base64,")
    assert result.metadata()["count"] == 1
