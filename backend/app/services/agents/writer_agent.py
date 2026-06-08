"""Writer Agent — 基于工作记忆生成写作内容。

支持流式 token 输出，按任务类型选择不同的 System Prompt 和输出格式。
"""

import asyncio
import logging
from typing import AsyncIterator

from app.services.agents import BaseAgent
from app.services.writing_pipeline import PipelineEvent

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """写作器 Agent — 根据任务类型生成写作内容。"""

    PROMPTS = {
        "polish": """你是一位资深学术编辑。对用户文本进行{style}润色：
- 保持原意和技术术语不变
- 改善语法、用词和流畅性
- 直接输出润色后的文本，不加解释""",

        "abstract": """你是一位顶会论文作者，擅长撰写高质量摘要。
按以下结构生成{language}摘要：
1. 背景与问题 (1-2句)
2. 方法概述 (2-3句)
3. 关键结果 (1-2句)
4. 意义 (1句)
总字数 180-280 字，不引用参考文献。""",

        "related_work": """你是一位担任 NeurIPS/ICLR/ACL 审稿人的资深研究员。
基于提供的论文信息撰写规范的 Related Work 章节。

要求：
1. 主题分组：按技术路线分为 2-3 组，每组 1-2 段
2. 每篇论文：简述核心方法 + 与本研究的关系/区别
3. 研究空白：每组末尾或全文末尾指出不足
4. 引用格式：使用 [1][2] 编号
5. 字数：300-600 字，学术简洁""",

        "literature_review": """你是一位资深学术研究者。
基于提供的论文撰写完整文献综述，包括：
1. 引言 (100-150字)
2. 核心方法分类 (200-300字)
3. 关键论文详述 (200-300字)
4. 对比分析表格 (Markdown)
5. 研究趋势与Gap (100-150字)
6. 结论 (50-100字)
使用 [1][2] 引用格式。""",

        "compare_papers": """你是一位学术论文评审专家。
对以下论文进行对比分析：
1. 研究问题对比
2. 核心方法对比
3. 使用的数据集
4. 主要实验结果/性能
5. 优势与局限性
6. 总结性评述：哪篇最值得跟进？为什么？
用 Markdown 表格输出对比结果。""",

        "grant_write": """你是一位经验丰富的NSFC基金申请书撰写专家。
撰写申请书的「{section}」章节。

要求：
1. 逻辑严密，层次清晰
2. 语言规范，符合NSFC写作风格
3. 关键科学问题突出
4. 技术路线明确可行
5. 字数 800-2000 字""",

        "full_chapter": """你是一位资深学术研究者和 LaTeX 论文写作助手。
撰写或改进论文章节。基于提供的论文、笔记、当前章节源码和诊断信息，写出完整、规范的学术内容。
要求：
1. 遵循学术写作规范
2. 逻辑清晰、论证充分
3. 当前章节使用 LaTeX body 源码，保留公式、命令、引用、label、表格和 figure 环境
4. 只处理用户指定的当前章节，不改写无关章节
5. 直接输出可粘贴回当前章节的 LaTeX 源码或明确的修改建议""",
    }

    @property
    def name(self) -> str:
        return "Writer"

    async def execute(self, memory, cancel_event=None) -> AsyncIterator[PipelineEvent]:
        self._check_cancelled(cancel_event)

        task_type = memory.metadata.get("task_type", "related_work")
        input_data = memory.metadata.get("input", {})

        # 构建 System Prompt
        system_prompt = self.PROMPTS.get(task_type, self.PROMPTS["related_work"])

        # 变量替换
        if task_type == "polish":
            style_map = {
                "academic": "正式学术风格",
                "concise": "简洁化",
                "fluent": "流畅性",
                "english": "翻译成学术英语",
            }
            style = style_map.get(input_data.get("style", "academic"), "正式学术风格")
            system_prompt = system_prompt.format(style=style)
        elif task_type == "abstract":
            language = "中文" if input_data.get("language", "chinese") == "chinese" else "English"
            system_prompt = system_prompt.format(language=language)
        elif task_type == "grant_write":
            section = input_data.get("section", "立项依据")
            system_prompt = system_prompt.format(section=section)

        # 构建用户消息
        user_message = self._build_user_message(task_type, input_data, memory)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # 流式生成 — 使用 chat_stream_with_thinking 以支持思考过程展示
        show_thinking = memory.metadata.get("input", {}).get("show_thinking", False)
        yield PipelineEvent("status", phase="writer", content="正在生成内容...")

        full_content = ""
        try:
            if show_thinking and hasattr(self.llm, 'chat_stream_with_thinking'):
                async for event in self.llm.chat_stream_with_thinking(
                    messages=messages,
                    temperature=0.4,
                ):
                    self._check_cancelled(cancel_event)
                    if event["type"] == "reasoning":
                        yield PipelineEvent("reasoning", phase="writer", content=event["content"])
                    elif event["type"] == "content":
                        full_content += event["content"]
                        yield PipelineEvent("content", phase="writer", content=event["content"])
            else:
                async for token in self.llm.chat_stream(
                    messages=messages,
                    temperature=0.4,
                ):
                    self._check_cancelled(cancel_event)
                    if token:
                        full_content += token
                        yield PipelineEvent("content", phase="writer", content=token)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Writer 生成失败: {e}")
            if full_content:
                yield PipelineEvent("status", phase="writer",
                                    content="生成中断，但已有部分内容")
            else:
                raise

        memory.writer_output = full_content

    def _build_user_message(self, task_type: str, input_data: dict, memory) -> str:
        """根据不同任务类型构建用户消息。"""
        if task_type == "polish":
            return f"请润色以下文本：\n\n{input_data.get('text', '')}"

        if task_type == "abstract":
            title = input_data.get("title", "")
            key_points = input_data.get("key_points", "")
            return f"论文标题: {title}\n\n关键要点:\n{key_points}"

        if task_type == "full_chapter" and input_data.get("section_title"):
            action_labels = {
                "draft": "起草当前章节",
                "improve": "改进当前章节论证",
                "insert_evidence": "补充证据与引用",
                "claim_safety": "检查并降低 Claim 风险",
                "polish": "润色当前章节 LaTeX 源码",
                "repair_latex": "解释并修复当前章节 LaTeX 编译问题",
            }
            action = input_data.get("section_action", "improve")
            parts = [
                f"项目标题: {input_data.get('project_title', '')}",
                f"当前章节: {input_data.get('section_title', '')}",
                f"动作目标: {action_labels.get(action, action)}",
                "",
                "## 当前章节 LaTeX source",
                "```latex",
                input_data.get("section_source", ""),
                "```",
            ]
            if input_data.get("project_context"):
                parts.extend(["", "## 项目上下文", str(input_data.get("project_context"))])
            if input_data.get("writing_brief"):
                parts.extend(["", "## Proposal 写作准备包摘要", str(input_data.get("writing_brief"))[:2500]])
            if input_data.get("evidence_summary"):
                parts.extend(["", "## 证据卡摘要", str(input_data.get("evidence_summary"))[:2500]])
            if input_data.get("citation_diagnostics"):
                parts.extend(["", "## 引用与 Claim 诊断", str(input_data.get("citation_diagnostics"))[:2500]])
            if input_data.get("latex_diagnostics"):
                parts.extend(["", "## LaTeX 编译诊断", str(input_data.get("latex_diagnostics"))[:2500]])
            parts.extend([
                "",
                "请围绕当前章节执行动作目标。若是起草/润色/修复，请输出可直接替换当前章节 body 的 LaTeX 源码；若是检查风险，请输出问题清单和可执行改写建议。",
            ])
            return "\n".join(parts)

        if task_type in ("related_work", "literature_review", "full_chapter"):
            topic = input_data.get("topic", "")
            parts = [f"研究主题: {topic}\n"]

            # 添加论文信息
            if memory.reading_notes:
                parts.append("\n## 已分析论文\n")
                for note in memory.reading_notes:
                    parts.append(
                        f"[{note.get('index', '?')}] **{note.get('title', '')}**\n"
                        f"- 问题: {note.get('problem', 'N/A')}\n"
                        f"- 方法: {note.get('method', 'N/A')}\n"
                        f"- 结果: {note.get('results', 'N/A')}\n"
                    )
            elif memory.papers:
                parts.append("\n## 相关论文\n")
                for i, p in enumerate(memory.papers):
                    parts.append(
                        f"[{i+1}] {p.get('title', '')} ({p.get('year', '')})\n"
                        f"摘要: {p.get('abstract', 'N/A')[:300]}\n"
                    )

            # 添加论文关系
            if memory.paper_relations:
                parts.append("\n## 论文间关系\n")
                for rel in memory.paper_relations:
                    parts.append(
                        f"[{rel.get('from', '?')}] → [{rel.get('to', '?')}]: "
                        f"{rel.get('relation', '')} - {rel.get('description', '')}\n"
                    )

            return "\n".join(parts)

        if task_type == "compare_papers":
            ids = input_data.get("paper_ids", [])
            return f"请对比分析以下 {len(ids)} 篇论文 (IDs: {', '.join(ids)})"

        if task_type == "grant_write":
            parts = [
                f"项目主题: {input_data.get('topic', '')}",
                f"项目背景: {input_data.get('background', '')}",
                f"章节: {input_data.get('section', '')}",
            ]
            if input_data.get("previous_content"):
                parts.append(f"前文内容:\n{input_data['previous_content'][:2000]}")
            return "\n\n".join(parts)

        # 默认
        return str(input_data)
