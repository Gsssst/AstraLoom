"""Bounded image generation provider adapter for chat tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.core.config import settings
from app.services.llm import OPENAI_COMPATIBLE_PROVIDER


SUPPORTED_IMAGE_SIZES = {"1024x1024", "1024x1536", "1536x1024"}
SUPPORTED_IMAGE_QUALITIES = {"auto", "low", "medium", "high"}
MAX_IMAGE_COUNT = 2


class ImageGenerationError(ValueError):
    """Raised when image generation cannot complete."""


class ImageGenerationConfigurationError(ImageGenerationError):
    """Raised when no supported provider is configured."""


class ImageGenerationProviderResponseError(ImageGenerationError):
    """Raised when the provider returns an unusable payload."""


@dataclass(frozen=True)
class ImageGenerationRequest:
    prompt: str
    purpose: str = "research_visual_draft"
    style: str = "clean academic diagram"
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["auto", "low", "medium", "high"] = "auto"
    count: int = 1


@dataclass(frozen=True)
class GeneratedImageArtifact:
    data_url: str
    provider: str
    model: str
    size: str
    revised_prompt: str | None = None
    source_url: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return {
            "type": "generated_image",
            "data_url": self.data_url,
            "provider": self.provider,
            "model": self.model,
            "size": self.size,
            "revised_prompt": self.revised_prompt,
            "source_url": self.source_url,
        }


@dataclass(frozen=True)
class ImageGenerationResult:
    prompt: str
    purpose: str
    style: str
    provider: str
    model: str
    size: str
    quality: str
    artifacts: list[GeneratedImageArtifact]

    def metadata(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "purpose": self.purpose,
            "style": self.style,
            "provider": self.provider,
            "model": self.model,
            "size": self.size,
            "quality": self.quality,
            "count": len(self.artifacts),
        }


def _normalized_provider() -> str:
    return (settings.IMAGE_GENERATION_PROVIDER or OPENAI_COMPATIBLE_PROVIDER).strip().lower()


def configured_image_provider() -> dict[str, Any]:
    provider = _normalized_provider()
    model = (settings.IMAGE_GENERATION_MODEL or "").strip()
    if provider != OPENAI_COMPATIBLE_PROVIDER:
        return {
            "provider": provider,
            "model": model,
            "configured": False,
            "reason": "仅支持 openai-compatible 图片生成 provider。",
        }
    configured = bool(settings.OPENAI_COMPATIBLE_API_KEY and settings.OPENAI_COMPATIBLE_API_BASE and model)
    return {
        "provider": provider,
        "model": model,
        "configured": configured,
        "api_base": settings.OPENAI_COMPATIBLE_API_BASE,
        "reason": "" if configured else "请配置 OPENAI_COMPATIBLE_API_BASE、OPENAI_COMPATIBLE_API_KEY 和 IMAGE_GENERATION_MODEL。",
    }


def _validate_request(request: ImageGenerationRequest) -> ImageGenerationRequest:
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise ImageGenerationError("图片生成 prompt 不能为空。")
    size = request.size if request.size in SUPPORTED_IMAGE_SIZES else "1024x1024"
    quality = request.quality if request.quality in SUPPORTED_IMAGE_QUALITIES else "auto"
    count = max(1, min(int(request.count or 1), MAX_IMAGE_COUNT))
    return ImageGenerationRequest(
        prompt=prompt[:4000],
        purpose=(request.purpose or "research_visual_draft").strip()[:120],
        style=(request.style or "clean academic diagram").strip()[:300],
        size=size,  # type: ignore[arg-type]
        quality=quality,  # type: ignore[arg-type]
        count=count,
    )


def openai_image_payload(request: ImageGenerationRequest, *, model: str) -> dict[str, Any]:
    req = _validate_request(request)
    composed_prompt = "\n".join([
        req.prompt,
        f"Purpose: {req.purpose}.",
        f"Style: {req.style}.",
        "Make it a draft visual aid for research communication. Avoid claiming measured results unless explicitly provided.",
    ])
    return {
        "model": model,
        "prompt": composed_prompt,
        "size": req.size,
        "quality": req.quality,
        "n": req.count,
    }


def _image_artifact_from_item(item: dict[str, Any], *, provider: str, model: str, size: str) -> GeneratedImageArtifact | None:
    b64 = item.get("b64_json")
    if isinstance(b64, str) and b64.strip():
        return GeneratedImageArtifact(
            data_url=f"data:image/png;base64,{b64.strip()}",
            provider=provider,
            model=model,
            size=size,
            revised_prompt=item.get("revised_prompt") if isinstance(item.get("revised_prompt"), str) else None,
        )
    url = item.get("url")
    if isinstance(url, str) and url.strip():
        return GeneratedImageArtifact(
            data_url=url.strip(),
            provider=provider,
            model=model,
            size=size,
            revised_prompt=item.get("revised_prompt") if isinstance(item.get("revised_prompt"), str) else None,
            source_url=url.strip(),
        )
    return None


def parse_openai_image_response(payload: dict[str, Any], *, provider: str, model: str, size: str) -> list[GeneratedImageArtifact]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise ImageGenerationProviderResponseError("图片生成 provider 响应缺少 data 数组。")
    artifacts = [
        artifact
        for item in data
        if isinstance(item, dict)
        for artifact in [_image_artifact_from_item(item, provider=provider, model=model, size=size)]
        if artifact is not None
    ]
    if not artifacts:
        raise ImageGenerationProviderResponseError("图片生成 provider 未返回可用图片数据。")
    return artifacts


async def generate_image(
    request: ImageGenerationRequest,
    *,
    client: httpx.AsyncClient | None = None,
) -> ImageGenerationResult:
    req = _validate_request(request)
    config = configured_image_provider()
    if not config["configured"]:
        raise ImageGenerationConfigurationError(str(config.get("reason") or "图片生成 provider 未配置。"))

    provider = config["provider"]
    model = config["model"]
    api_base = str(config["api_base"]).rstrip("/")
    payload = openai_image_payload(req, model=model)
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_COMPATIBLE_API_KEY}",
        "Content-Type": "application/json",
    }

    owns_client = client is None
    active_client = client or httpx.AsyncClient(timeout=60)
    try:
        response = await active_client.post(
            f"{api_base}/images/generations",
            headers=headers,
            json=payload,
        )
        if response.status_code >= 400:
            detail = response.text[:500]
            raise ImageGenerationError(f"图片生成 provider 请求失败 ({response.status_code}): {detail}")
        artifacts = parse_openai_image_response(response.json(), provider=provider, model=model, size=req.size)
    finally:
        if owns_client:
            await active_client.aclose()

    return ImageGenerationResult(
        prompt=req.prompt,
        purpose=req.purpose,
        style=req.style,
        provider=provider,
        model=model,
        size=req.size,
        quality=req.quality,
        artifacts=artifacts[: req.count],
    )
