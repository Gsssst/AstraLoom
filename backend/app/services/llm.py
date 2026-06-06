"""LLM 服务 — 通过 LiteLLM 统一封装 DeepSeek V4 Pro 调用。

参考 DeepSeek 官方文档:
- thinking_mode: https://api-docs.deepseek.com/zh-cn/guides/thinking_mode
- max_tokens 上限: 384K, 上下文: 1M
- reasoning_content 与 content 共享 max_tokens 预算
"""

import json
import logging
from typing import AsyncIterator, Dict, Any, Optional, Union

import litellm
from app.core.config import settings

logger = logging.getLogger(__name__)

# 配置 LiteLLM — 使用 DeepSeek 兼容 OpenAI 格式
litellm.drop_params = True  # 自动丢弃不支持的参数

# DeepSeek V4 Pro 支持最大 384K max_tokens
DEFAULT_MAX_TOKENS = 16384
LARGE_MAX_TOKENS = 32768
MAX_MAX_TOKENS = 65536


class LLMService:
    """大语言模型调用服务。"""

    def __init__(self):
        self.model = f"openai/{settings.DEEPSEEK_MODEL}"
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE

    def _get_kwargs(self) -> Dict[str, Any]:
        """获取通用调用参数。

        DeepSeek V4 Pro 默认开启思考模式，无需显式传参。
        LiteLLM openai provider 不兼容 extra_body，传了反而可能导致 400 错误。
        """
        return {
            "model": self.model,
            "api_key": self.api_key,
            "api_base": self.api_base,
        }

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
                        f"V4 Pro 思考消耗了所有 token (reasoning={len(reasoning)}chars)，"
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
                    )

                return content if content else ""
            except Exception as e:
                last_error = e
                if attempt == 0:
                    logger.warning(f"LLM 调用失败，2s 后重试: {e}")
                    import asyncio; await asyncio.sleep(2)
                else:
                    raise last_error

    async def _log_usage(self, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0):
        """异步记录 Token 用量（后台静默）。"""
        try:
            from app.services.usage_tracker import UsageTracker, get_usage_user
            usage_user = get_usage_user() or {}
            await UsageTracker.log_usage(
                user_id=usage_user.get("user_id"),
                username=usage_user.get("username") or "system",
                model=settings.DEEPSEEK_MODEL,
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
            # V4 Pro 思考模式：推理消耗了所有 token → 渐进式增大
            # 16384 → 32768 → 65536 (DeepSeek 上限 384K)
            if reasoning_seen and token_limit < MAX_MAX_TOKENS:
                token_limit = min(token_limit * 2, MAX_MAX_TOKENS)
                logger.info(f"V4 Pro 流式思考耗尽 tokens，以 {token_limit} 重试")
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
        """流式对话 — 返回结构化事件，包含思考过程和可见内容。

        每个 chunk 是 dict: {"type": "reasoning"|"content", "content": "..."}
        前端可根据 type 分别渲染思考过程（可折叠）和最终回答。

        参考 DeepSeek 官方 thinking_mode 文档：
        https://api-docs.deepseek.com/zh-cn/guides/thinking_mode
        """
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
                logger.info(f"V4 Pro 思考消耗了所有 token（{reason}），以 {token_limit} 重试")
            elif attempt == 0:
                logger.warning("LLM 流式调用未返回可展示内容，重试一次")
            else:
                raise RuntimeError("模型未返回可展示内容")

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
