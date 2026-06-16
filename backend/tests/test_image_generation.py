import httpx
import pytest

from app.services import image_generation
from app.services.image_generation import (
    DAYA_VERTEX_PROVIDER,
    ImageGenerationConfigurationError,
    ImageGenerationProviderResponseError,
    ImageGenerationRequest,
    daya_vertex_image_payload,
    generate_image,
    openai_image_payload,
    parse_daya_vertex_image_response,
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


def test_daya_vertex_image_payload_uses_response_modalities():
    payload = daya_vertex_image_payload(
        ImageGenerationRequest(
            prompt="Draw a video grounding method diagram",
            purpose="paper figure draft",
            style="flat academic diagram",
            count=2,
        )
    )

    assert payload["contents"][0]["role"] == "user"
    assert "Draw a video grounding method diagram" in payload["contents"][0]["parts"][0]["text"]
    assert payload["generationConfig"]["responseModalities"] == ["TEXT", "IMAGE"]
    assert payload["generationConfig"]["candidateCount"] == 2


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


def test_parse_daya_vertex_image_response_accepts_inline_data_and_file_uri():
    artifacts = parse_daya_vertex_image_response(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Here is a diagram."},
                            {"inlineData": {"mimeType": "image/png", "data": "aGVsbG8="}},
                            {"fileData": {"mimeType": "image/jpeg", "fileUri": "https://example.com/image.jpg"}},
                        ]
                    }
                }
            ]
        },
        provider=DAYA_VERTEX_PROVIDER,
        model="google/gemini-3-pro-image-preview",
        size="1024x1024",
    )

    assert artifacts[0].data_url == "data:image/png;base64,aGVsbG8="
    assert artifacts[0].provider == DAYA_VERTEX_PROVIDER
    assert artifacts[1].data_url == "https://example.com/image.jpg"
    assert artifacts[1].source_url == "https://example.com/image.jpg"


def test_parse_daya_vertex_image_response_rejects_text_only_response():
    with pytest.raises(ImageGenerationProviderResponseError):
        parse_daya_vertex_image_response(
            {"candidates": [{"content": {"parts": [{"text": "I cannot draw that."}]}}]},
            provider=DAYA_VERTEX_PROVIDER,
            model="google/gemini-3-pro-image-preview",
            size="1024x1024",
        )


@pytest.mark.asyncio
async def test_generate_image_rejects_missing_configuration(monkeypatch):
    monkeypatch.setattr(image_generation.settings, "OPENAI_COMPATIBLE_API_KEY", "")
    monkeypatch.setattr(image_generation.settings, "IMAGE_GENERATION_API_BASE", "")
    monkeypatch.setattr(image_generation.settings, "IMAGE_GENERATION_MODEL", "google/gemini-3-pro-image-preview")

    with pytest.raises(ImageGenerationConfigurationError):
        await generate_image(ImageGenerationRequest(prompt="draw a diagram"))


@pytest.mark.asyncio
async def test_generate_image_calls_daya_vertex_endpoint(monkeypatch):
    requests = []

    class FakeClient:
        async def post(self, url, headers=None, json=None):
            requests.append({"url": url, "headers": headers, "json": json})
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"inlineData": {"mimeType": "image/png", "data": "aGVsbG8="}},
                                ]
                            }
                        }
                    ]
                },
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(image_generation.settings, "OPENAI_COMPATIBLE_API_KEY", "sk-test")
    monkeypatch.setattr(image_generation.settings, "IMAGE_GENERATION_API_BASE", "https://api.dayaai.com")
    monkeypatch.setattr(image_generation.settings, "IMAGE_GENERATION_PROVIDER", DAYA_VERTEX_PROVIDER)
    monkeypatch.setattr(image_generation.settings, "IMAGE_GENERATION_MODEL", "google/gemini-3-pro-image-preview")

    result = await generate_image(
        ImageGenerationRequest(prompt="draw a diagram", count=1),
        client=FakeClient(),
    )

    assert requests[0]["url"] == "https://api.dayaai.com/v1beta/models/google%2Fgemini-3-pro-image-preview:generateContent"
    assert requests[0]["headers"]["Authorization"] == "Bearer sk-test"
    assert requests[0]["headers"]["x-goog-api-key"] == "sk-test"
    assert requests[0]["json"]["generationConfig"]["responseModalities"] == ["TEXT", "IMAGE"]
    assert result.artifacts[0].data_url.startswith("data:image/png;base64,")
    assert result.metadata()["count"] == 1
