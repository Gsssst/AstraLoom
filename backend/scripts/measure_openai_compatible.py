"""Measure an OpenAI Chat Completions compatible endpoint.

Reads:
- OPENAI_COMPATIBLE_API_BASE
- OPENAI_COMPATIBLE_API_KEY
- OPENAI_COMPATIBLE_MODEL

The script never prints the API key.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from typing import Any

import httpx


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _chat_url(api_base: str) -> str:
    return f"{api_base.rstrip('/')}/chat/completions"


def _payload(model: str, prompt: str, *, stream: bool, max_tokens: int) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": stream,
    }


def _extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return message.get("content") or ""


def _extract_stream_delta(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    return delta.get("content") or ""


async def measure_non_streaming(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    model: str,
    prompt: str,
    max_tokens: int,
) -> None:
    started = time.perf_counter()
    response = await client.post(
        url,
        headers=headers,
        json=_payload(model, prompt, stream=False, max_tokens=max_tokens),
    )
    elapsed = time.perf_counter() - started
    print(f"non_stream.status={response.status_code}")
    print(f"non_stream.total_seconds={elapsed:.3f}")
    if response.status_code >= 400:
        print(f"non_stream.error={response.text[:1000]}")
        return

    data = response.json()
    content = _extract_content(data)
    print(f"non_stream.content_chars={len(content)}")
    print(f"non_stream.content_preview={content[:300]!r}")
    usage = data.get("usage")
    if usage:
        print(f"non_stream.usage={json.dumps(usage, ensure_ascii=False)}")


async def measure_streaming(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    model: str,
    prompt: str,
    max_tokens: int,
) -> None:
    started = time.perf_counter()
    first_token_at: float | None = None
    chunks = 0
    content_parts: list[str] = []

    async with client.stream(
        "POST",
        url,
        headers=headers,
        json=_payload(model, prompt, stream=True, max_tokens=max_tokens),
    ) as response:
        print(f"stream.status={response.status_code}")
        if response.status_code >= 400:
            body = await response.aread()
            print(f"stream.error={body.decode(errors='replace')[:1000]}")
            return

        async for line in response.aiter_lines():
            if not line.startswith("data:"):
                continue
            payload = line.removeprefix("data:").strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            chunks += 1
            delta = _extract_stream_delta(data)
            if delta:
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                content_parts.append(delta)

    total = time.perf_counter() - started
    first = None if first_token_at is None else first_token_at - started
    content = "".join(content_parts)
    print(f"stream.first_token_seconds={first if first is not None else 'none'}")
    print(f"stream.total_seconds={total:.3f}")
    print(f"stream.chunks={chunks}")
    print(f"stream.content_chars={len(content)}")
    print(f"stream.content_preview={content[:300]!r}")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="Reply with exactly: OK")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    api_base = _env("OPENAI_COMPATIBLE_API_BASE")
    api_key = _env("OPENAI_COMPATIBLE_API_KEY")
    model = _env("OPENAI_COMPATIBLE_MODEL", "gpt-5.5")
    if not api_base or not api_key or not model:
        print("Missing OPENAI_COMPATIBLE_API_BASE, OPENAI_COMPATIBLE_API_KEY, or OPENAI_COMPATIBLE_MODEL")
        return 2

    url = _chat_url(api_base)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    print(f"api_base={api_base}")
    print(f"model={model}")
    print(f"prompt={args.prompt!r}")
    print(f"max_tokens={args.max_tokens}")

    timeout = httpx.Timeout(args.timeout, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        await measure_non_streaming(client, url, headers, model, args.prompt, args.max_tokens)
        await measure_streaming(client, url, headers, model, args.prompt, args.max_tokens)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
