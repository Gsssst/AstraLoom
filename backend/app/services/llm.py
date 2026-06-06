"""LLM 服务 — 通过 LiteLLM 统一封装可选 Chat Completions 兼容模型。
"""

import json
import logging
import os
from typing import AsyncIterator, Dict, Any, Optional, Union

import httpx
import litellm
from app.core.config import settings

logger = logging.getLogger(__name__)

# 配置 LiteLLM — 使用 DeepSeek 兼容 OpenAI 格式
litellm.drop_params = True  # 自动丢弃不支持的参数

# DeepSeek V4 Pro 支持最大 384K max_tokens
DEFAULT_MAX_TOKENS = 16384
LARGE_MAX_TOKENS = 32768
MAX_MAX_TOKENS = 65536

DEFAULT_PROVIDER = "deepseek"
OPENAI_COMPATIBLE_PROVIDER = "openai-compatible"


def _normalize_provider(value: Optional[str]) -> str:
    provider = (value or DEFAULT_PROVIDER).strip().lower()
    aliases = {
        "deepseek": DEFAULT_PROVIDER,
        "openai": OPENAI_COMPATIBLE_PROVIDER,
        "openai_compatible": OPENAI_COMPATIBLE_PROVIDER,
        "openai-compatible": OPENAI_COMPATIBLE_PROVIDER,
        "gpt": OPENAI_COMPATIBLE_PROVIDER,
        "gpt-5.5": OPENAI_COMPATIBLE_PROVIDER,
    }
    return aliases.get(provider, provider)


def _litellm_model(model: str) -> str:
    return model if model.startswith("openai/") else f"openai/{model}"


def _responses_model(model: str) -> str:
    return model.removeprefix("openai/")


def _responses_content(content: Any) -> Any:
    """Convert Chat Completions style content parts to Responses API content."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)

    parts: list[dict[str, Any]] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        part_type = part.get("type")
        if part_type == "text":
            parts.append({"type": "input_text", "text": part.get("text", "")})
        elif part_type == "image_url":
            image_url = part.get("image_url") or {}
            if isinstance(image_url, dict) and image_url.get("url"):
                parts.append({"type": "input_image", "image_url": image_url["url"]})
    return parts or ""


def _responses_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role") or "user"
        if role not in {"user", "assistant", "system", "developer"}:
            role = "user"
        inputs.append({"role": role, "content": _responses_content(message.get("content", ""))})
    return inputs


class LLMService:
    """大语言模型调用服务。"""

    def __init__(self):
        self.runtime_config_path = settings.LLM_RUNTIME_CONFIG_PATH

    def available_options(self) -> list[dict[str, Any]]:
        """Return model options without exposing API keys."""
        return [
            {
                "provider": DEFAULT_PROVIDER,
                "label": "DeepSeek V4 Pro",
                "model": settings.DEEPSEEK_MODEL,
                "api_base": settings.DEEPSEEK_API_BASE,
                "has_api_key": bool(settings.DEEPSEEK_API_KEY),
                "configured": bool(settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_BASE and settings.DEEPSEEK_MODEL),
                "supports_thinking": True,
                "api_key_env": "DEEPSEEK_API_KEY",
                "api_base_env": "DEEPSEEK_API_BASE",
                "model_env": "DEEPSEEK_MODEL",
            },
            {
                "provider": OPENAI_COMPATIBLE_PROVIDER,
                "label": "GPT-5.5（OpenAI 兼容）",
                "model": settings.OPENAI_COMPATIBLE_MODEL,
                "api_base": settings.OPENAI_COMPATIBLE_API_BASE,
                "has_api_key": bool(settings.OPENAI_COMPATIBLE_API_KEY),
                "configured": bool(
                    settings.OPENAI_COMPATIBLE_API_KEY
                    and settings.OPENAI_COMPATIBLE_API_BASE
                    and settings.OPENAI_COMPATIBLE_MODEL
                ),
                "supports_thinking": True,
                "api_key_env": "OPENAI_COMPATIBLE_API_KEY",
                "api_base_env": "OPENAI_COMPATIBLE_API_BASE",
                "model_env": "OPENAI_COMPATIBLE_MODEL",
            },
        ]

    def get_active_option(self) -> dict[str, Any]:
        provider, model_override = self._read_runtime_selection()
        option = next((item for item in self.available_options() if item["provider"] == provider), None)
        if not option:
            provider = DEFAULT_PROVIDER
            option = self.available_options()[0]
        if model_override:
            option = {**option, "model": model_override}
        return option

    @property
    def active_provider(self) -> str:
        return self._read_runtime_selection()[0]

    @property
    def model(self) -> str:
        return self.get_active_option()["model"]

    @property
    def api_base(self) -> str:
        return self.get_active_option()["api_base"]

    @property
    def api_key(self) -> str:
        provider = self.active_provider
        if provider == OPENAI_COMPATIBLE_PROVIDER:
            return settings.OPENAI_COMPATIBLE_API_KEY
        return settings.DEEPSEEK_API_KEY

    def _read_runtime_selection(self) -> tuple[str, Optional[str]]:
        provider = _normalize_provider(settings.LLM_PROVIDER)
        model_override: Optional[str] = None
        if not self.runtime_config_path:
            return provider, model_override
        try:
            with open(self.runtime_config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            provider = _normalize_provider(data.get("provider") or provider)
            raw_model = data.get("model")
            if isinstance(raw_model, str) and raw_model.strip():
                model_override = raw_model.strip()
        except FileNotFoundError:
            pass
        except Exception as exc:
            logger.warning("读取 LLM 运行时配置失败，回退到环境变量: %s", exc)
        return provider, model_override

    def _write_runtime_selection(self, provider: str, model: str) -> None:
        if not self.runtime_config_path:
            return
        directory = os.path.dirname(self.runtime_config_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        payload = {"provider": provider, "model": model}
        tmp_path = f"{self.runtime_config_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.runtime_config_path)

    def select_model(self, provider: str, model: Optional[str] = None) -> dict[str, Any]:
        provider = _normalize_provider(provider)
        option = next((item for item in self.available_options() if item["provider"] == provider), None)
        if not option:
            raise ValueError("不支持的 LLM 提供商")
        selected_model = (model or option["model"]).strip()
        if not selected_model:
            raise ValueError("模型名称不能为空")
        if not option["api_base"] or not option["has_api_key"]:
            raise ValueError("该模型的 API Base 或 API Key 尚未在服务器环境变量中配置")
        self._write_runtime_selection(provider, selected_model)
        return self.get_active_option()

    def _get_kwargs(self) -> Dict[str, Any]:
        """获取通用调用参数。

        DeepSeek V4 Pro 默认开启思考模式，无需显式传参。
        LiteLLM openai provider 不兼容 extra_body，传了反而可能导致 400 错误。
        """
        return {
            "model": _litellm_model(self.model),
            "api_key": self.api_key,
            "api_base": self.api_base,
        }

    def _responses_api_url(self) -> str:
        return f"{self.api_base.rstrip('/')}/responses"

    async def chat(
        self,
        messages,
        temperature: float = 0.7,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        stream: bool = False,
    ) -> str:
        """非流式对话。

        DeepSeek V4 Pro 的 reasoning_content 与 content 共享 max_tokens 预算。
        默认 max_tokens=16384，确保有足够空间用于思考+输出。
        """
        last_error = None
        for attempt in range(3):
            try:
                response = await litellm.acompletion(
                    messages=messages, temperature=temperature,
                    max_tokens=max_tokens, stream=False, **self._get_kwargs(),
                )
                message = response.choices[0].message
                content = message.content or ""
                reasoning = getattr(message, "reasoning_content", None) or ""
                if attempt > 0:
                    logger.info(f"LLM 重试成功 (attempt {attempt+1})")

                # V4 Pro 思考模式: content 为空但 reasoning_content 有内容 → token 不足
                # 渐进式升级: 16384 → 32768 → 65536
                if not content and reasoning and max_tokens < MAX_MAX_TOKENS:
                    next_limit = min(max_tokens * 2, MAX_MAX_TOKENS)
                    logger.info(
                        f"模型思考消耗了所有 token (reasoning={len(reasoning)}chars)，"
                        f"以 {next_limit} max_tokens 重试"
                    )
                    return await self.chat(messages, temperature, max_tokens=next_limit)

                # 记录用量（含 reasoning tokens）
                usage = response.usage
                if usage:
                    await self._log_usage(
                        prompt_tokens=getattr(usage, "prompt_tokens", 0),
                        completion_tokens=getattr(usage, "completion_tokens", 0),
                        total_tokens=getattr(usage, "total_tokens", 0),
                        model=self.model,
                    )

                return content if content else ""
            except Exception as e:
                last_error = e
                if attempt == 0:
                    logger.warning(f"LLM 调用失败，2s 后重试: {e}")
                    import asyncio; await asyncio.sleep(2)
                else:
                    raise last_error

    async def _log_usage(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        model: Optional[str] = None,
    ):
        """异步记录 Token 用量（后台静默）。"""
        try:
            from app.services.usage_tracker import UsageTracker, get_usage_user
            usage_user = get_usage_user() or {}
            await UsageTracker.log_usage(
                user_id=usage_user.get("user_id"),
                username=usage_user.get("username") or "system",
                model=model or self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
        except Exception:
            pass

    async def chat_stream(
        self,
        messages,
        temperature: float = 0.7,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> AsyncIterator[str]:
        """流式对话 — 逐个返回 content token（向后兼容）。

        如需获取思考过程，请使用 chat_stream_with_thinking()。
        """
        token_limit = max_tokens
        for attempt in range(3):
            emitted_content = False
            reasoning_seen = False
            try:
                response = await litellm.acompletion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=token_limit,
                    stream=True,
                    **self._get_kwargs(),
                )
                async for chunk in response:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    reasoning_seen = reasoning_seen or bool(getattr(delta, "reasoning_content", None))
                    content = getattr(delta, "content", None)
                    if content:
                        emitted_content = True
                        yield content
            except Exception as e:
                if emitted_content or attempt == 1:
                    logger.error(f"LLM 流式调用失败: {e}")
                    raise
                logger.warning(f"LLM 流式调用失败，2s 后重试: {e}")
                import asyncio
                await asyncio.sleep(2)
                continue

            if emitted_content:
                return
            # 思考模式：推理消耗了所有 token → 渐进式增大
            # 16384 → 32768 → 65536 (DeepSeek 上限 384K)
            if reasoning_seen and token_limit < MAX_MAX_TOKENS:
                token_limit = min(token_limit * 2, MAX_MAX_TOKENS)
                logger.info(f"模型流式思考耗尽 tokens，以 {token_limit} 重试")
            elif not reasoning_seen and token_limit < MAX_MAX_TOKENS:
                token_limit = min(token_limit * 2, MAX_MAX_TOKENS)
                logger.info(f"V4 Pro 流式未返回内容，以 {token_limit} max_tokens 重试")
            elif attempt == 0:
                logger.warning("LLM 流式调用未返回可展示内容，重试一次")
            else:
                raise RuntimeError("模型未返回可展示内容")

    async def chat_stream_with_thinking(
        self,
        messages,
        temperature: float = 0.7,
        max_tokens: int = LARGE_MAX_TOKENS,
    ) -> AsyncIterator[Dict[str, str]]:
        """流式对话 — 返回结构化事件，包含思考摘要/过程和可见内容。

        每个 chunk 是 dict: {"type": "reasoning"|"content", "content": "..."}
        前端可根据 type 分别渲染思考过程（可折叠）和最终回答。

        DeepSeek 等模型可能返回 reasoning_content；OpenAI-compatible
        provider 在支持 Responses API 时返回 reasoning summary。
        """
        if self.active_provider == OPENAI_COMPATIBLE_PROVIDER:
            async for event in self.chat_stream_responses_with_reasoning_summary(
                messages=messages,
                max_tokens=max_tokens,
            ):
                yield event
            return

        token_limit = max_tokens
        reasoning_total = ""
        content_total = ""

        for attempt in range(3):
            emitted_reasoning = False
            emitted_content = False
            try:
                response = await litellm.acompletion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=token_limit,
                    stream=True,
                    **self._get_kwargs(),
                )
                async for chunk in response:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    reasoning = getattr(delta, "reasoning_content", None)
                    content = getattr(delta, "content", None)

                    if reasoning:
                        emitted_reasoning = True
                        reasoning_total += reasoning
                        yield {"type": "reasoning", "content": reasoning}

                    if content:
                        emitted_content = True
                        content_total += content
                        yield {"type": "content", "content": content}

            except Exception as e:
                if emitted_content or attempt == 1:
                    logger.error(f"LLM 流式调用失败: {e}")
                    raise
                logger.warning(f"LLM 流式调用失败，2s 后重试: {e}")
                import asyncio
                await asyncio.sleep(2)
                continue

            if emitted_content:
                return
            # 有思考但无内容 → 渐进式增大 token，多级重试
            if token_limit < MAX_MAX_TOKENS:
                token_limit = min(token_limit * 2, MAX_MAX_TOKENS)
                reason = f"reasoning={len(reasoning_total)}chars" if emitted_reasoning else "无推理输出"
                logger.info(f"模型思考消耗了所有 token（{reason}），以 {token_limit} 重试")
            elif attempt == 0:
                logger.warning("LLM 流式调用未返回可展示内容，重试一次")
            else:
                raise RuntimeError("模型未返回可展示内容")

    async def chat_stream_responses_with_reasoning_summary(
        self,
        messages,
        max_tokens: int = LARGE_MAX_TOKENS,
        reasoning_effort: str = "medium",
        reasoning_summary: str = "auto",
    ) -> AsyncIterator[Dict[str, str]]:
        """Stream OpenAI Responses API output text and reasoning summary deltas."""
        payload = {
            "model": _responses_model(self.model),
            "input": _responses_input(messages),
            "reasoning": {"effort": reasoning_effort, "summary": reasoning_summary},
            "max_output_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        emitted_content = False
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                self._responses_api_url(),
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise RuntimeError(f"Responses API 调用失败 ({response.status_code}): {detail.decode('utf-8', errors='ignore')[:500]}")

                data_lines: list[str] = []
                async for raw_line in response.aiter_lines():
                    line = raw_line.strip()
                    if not line:
                        event = self._parse_responses_sse_data(data_lines)
                        data_lines = []
                        if not event:
                            continue
                        event_type = event.get("type")
                        delta = event.get("delta")
                        if event_type == "response.reasoning_summary_text.delta" and isinstance(delta, str):
                            yield {"type": "reasoning", "content": delta}
                        elif event_type == "response.output_text.delta" and isinstance(delta, str):
                            emitted_content = True
                            yield {"type": "content", "content": delta}
                        elif event_type == "response.error":
                            error = event.get("error") or event
                            raise RuntimeError(f"Responses API 返回错误: {error}")
                        elif event_type in {"response.completed", "response.output_text.done"}:
                            continue
                        continue
                    if line.startswith("data:"):
                        data_lines.append(line[5:].strip())

                event = self._parse_responses_sse_data(data_lines)
                if event and event.get("type") == "response.output_text.delta" and isinstance(event.get("delta"), str):
                    emitted_content = True
                    yield {"type": "content", "content": event["delta"]}

        if not emitted_content:
            raise RuntimeError("Responses API 未返回可展示内容")

    @staticmethod
    def _parse_responses_sse_data(data_lines: list[str]) -> dict[str, Any] | None:
        if not data_lines:
            return None
        data = "\n".join(data_lines)
        if data == "[DONE]":
            return None
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            logger.debug("忽略无法解析的 Responses SSE 数据: %s", data[:200])
            return None
        return parsed if isinstance(parsed, dict) else None

    async def summarize_paper(
        self,
        title: str,
        abstract: str,
        full_text: Optional[str] = None,
    ) -> str:
        """论文总结 — 使用结构化提示词提取关键信息。

        返回包含以下内容的结构化总结（中文）：
        - 研究问题
        - 方法与创新点
        - 主要贡献
        - 局限性
        - 与相关工作的关系
        """
        prompt = f"""请对以下论文进行结构化总结，使用中文输出：

**论文标题**: {title}
**摘要**: {abstract}
"""
        if full_text:
            prompt += f"\n**全文概要**: {full_text[:8000]}\n"

        prompt += """
请按以下格式输出：
1. **研究问题**：论文要解决的核心问题
2. **方法与创新点**：提出的方法及其新颖之处
3. **主要贡献**：论文的关键贡献
4. **局限性**：方法存在的限制或不足
5. **未来方向**：可能的改进或后续研究方向
"""
        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
        )


# 全局单例
llm_service = LLMService()
