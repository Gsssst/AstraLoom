"""Reviewer Agent — 审阅 Writer 输出，从逻辑/语言/结构维度提出修改建议。

参考 TexGuardian 的 review pipeline 和 GPT Academic 的润色质量标准。
"""

import asyncio
import json
import logging
from typing import AsyncIterator

from app.services.agents import BaseAgent
from app.services.writing_pipeline import PipelineEvent

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    """审阅器 Agent — 对生成内容进行多维度质量评审。"""

    @property
    def name(self) -> str:
        return "Reviewer"

    async def execute(self, memory, cancel_event=None) -> AsyncIterator[PipelineEvent]:
        self._check_cancelled(cancel_event)

        content = memory.writer_output
        if not content:
            yield PipelineEvent("status", phase="reviewer",
                                content="无内容可审阅")
            return

        task_type = memory.metadata.get("task_type", "")

        yield PipelineEvent("status", phase="reviewer", content="正在审阅内容质量...")

        # 逻辑检查
        self._check_cancelled(cancel_event)
        logic_check = await self._review_dimension(content, "logic",
            "检查逻辑一致性：是否有矛盾陈述？论证链条是否完整？前提和结论是否一致？")

        # 语言检查
        self._check_cancelled(cancel_event)
        language_check = await self._review_dimension(content, "language",
            "检查语言质量：是否有语法错误？用词是否准确？句子是否流畅？是否存在口语化表达？")

        # 结构检查 (仅对较长内容)
        structure_check = ""
        if len(content) > 500 and task_type not in ("polish", "abstract"):
            self._check_cancelled(cancel_event)
            structure_check = await self._review_dimension(content, "structure",
                "检查结构组织：段落划分是否合理？是否有明确的主题句？过渡是否自然？")

        # 汇总审阅结果
        suggestions = []
        for check_name, check_result in [
            ("逻辑", logic_check), ("语言", language_check), ("结构", structure_check)
        ]:
            if check_result and check_result.strip():
                suggestions.append(f"### {check_name}方面\n{check_result}")

        if suggestions:
            review_text = "\n\n".join(suggestions)
            yield PipelineEvent("status", phase="reviewer",
                                content=f"审阅完成，发现 {len(suggestions)} 个维度的建议")
        else:
            review_text = "未发现明显问题，内容质量良好。"
            yield PipelineEvent("status", phase="reviewer", content="审阅通过")

        memory.metadata["review_result"] = review_text

    async def _review_dimension(self, content: str, dimension: str, instruction: str) -> str:
        """对单个维度进行审阅。"""
        if not self.llm:
            return ""

        # 对于长内容，分段审阅
        text = content if len(content) < 3000 else content[:1500] + "\n...(内容过长，仅审阅前1500字)\n" + content[-500:]

        prompt = f"""## 任务
作为资深审稿人，对以下学术文本进行{instruction}

## 文本
{text}

## 输出要求
- 如果发现问题，用简短的要点列出 (每条不超过 30 字)
- 每个要点前用 "- " 开头
- 如果没有问题，输出 "无"
- 不要输出其他解释文字
"""
        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1024,
            )
            result = response.strip()
            return "" if result == "无" else result
        except Exception as e:
            logger.warning(f"审阅 {dimension} 失败: {e}")
            return ""
