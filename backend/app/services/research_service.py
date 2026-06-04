"""科研 Pipeline 服务 — Idea 生成、讨论、代码生成。"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.llm import llm_service
from app.services.rag_service import RAGService
from app.db.models.paper import Paper
from app.db.models.research import ResearchProject, ResearchIdea

logger = logging.getLogger(__name__)


class ResearchPipelineService:
    """科研自动化 Pipeline 服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_ideas(
        self,
        project: ResearchProject,
        num_ideas: int = 3,
    ) -> List[ResearchIdea]:
        """基于知识库中相关论文，生成创新性研究 Idea。"""
        keywords = project.keywords or []
        keyword_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)

        # 使用新的智能论文筛选服务（参考 AI-Researcher + SciPIP）
        from app.services.paper_selection import PaperSelectionService

        selector = PaperSelectionService(self.session)
        relevant_papers = await selector.select_papers(
            topic_name=project.name,
            topic_description=project.description or "",
            keywords=keywords,
            manual_paper_ids=project.paper_ids,
            max_papers=10,
        )

        if not relevant_papers:
            logger.warning(f"未找到与项目 '{project.name}' 相关的论文，请先入库或收藏相关方向的论文")
            return []

        # 统计来源分布
        sources = {}
        for _, _, src in relevant_papers:
            src_type = src.split(":")[0] if ":" in src else src
            sources[src_type] = sources.get(src_type, 0) + 1
        logger.info(f"论文来源分布: {sources}，共 {len(relevant_papers)} 篇")

        # 确保论文有较完整的内容（类似报告生成）
        from app.services.report_service import ensure_full_text
        for p, _, _ in relevant_papers[:8]:
            try:
                await ensure_full_text(p)
            except Exception:
                pass

        # 构建结构化论文上下文（参考 SciPIP/AI-Researcher 做法）
        papers_context = "\n\n---\n\n".join([
            f"### 论文 [{i+1}]: {p.title} ({p.year or 'N/A'})\n"
            f"**作者**: {', '.join(p.authors[:5]) if isinstance(p.authors, list) else str(p.authors)[:200]}\n"
            f"**摘要**: {p.abstract or 'N/A'}\n"
            f"**全文摘要**: {p.full_text[:2000] if p.full_text else p.abstract[:600] if p.abstract else 'N/A'}\n"
            f"**标签**: {', '.join(p.tags[:5]) if p.tags else 'N/A'}\n"
            f"**选择来源**: {src} | 相关度: {score:.2f}"
            for i, (p, score, src) in enumerate(relevant_papers[:8])
        ])

        # 6. 双路径 Idea 生成（参考 SciPIP 双路径策略）
        logger.info(f"开始双路径 Idea 生成，共 {len(relevant_papers)} 篇论文")

        # 路径 A: 文献推理 — 基于论文 gap 推导可行方案
        path_a_prompt = f"""你是一位资深 AI 研究科学家。请仔细分析以下论文，找出它们未解决的问题和研究空白，然后基于这些 gap 推导出 {num_ideas} 个具体可行的研究方案。

## 研究方向
名称: {project.name}
描述: {project.description or '未提供'}
关键词: {keyword_str}

## 相关论文（含全文内容）
{papers_context}

## 要求 — 文献推理路径
对每个 Idea，详细思考以下问题后给出答案：
1. 现有工作的**共同局限**是什么？（指出 2-3 个）
2. 有哪些**被忽略的研究角度**？
3. 技术上可以**如何改进**？

请用 JSON 输出，每个 Idea 包含：
- "title": 一句话标题
- "background_gap": 指出现有工作的 gap（2-3句）
- "description": 核心思路（3-4句，具体）
- "innovation": 与现有工作的本质区别
- "approach": 技术路线（具体步骤）
- "feasibility": 可行性 1-10
- "novelty": 创新性 1-10
- "clarity": 方案清晰度 1-10
- "impact": 潜在影响力 1-10

直接输出 JSON 数组，用中文。
"""
        response_a = await llm_service.chat(
            messages=[{"role": "user", "content": path_a_prompt}],
            temperature=0.6, max_tokens=4096,
        )

        # 路径 B: 自由头脑风暴 — 不受论文限制，产生突破性想法
        path_b_prompt = f"""你是一位极具创造力的 AI 研究科学家。请为研究方向「{project.name}」自由头脑风暴 {num_ideas} 个极具创新性的研究想法。

## 研究方向
名称: {project.name}
描述: {project.description or '未提供'}
关键词: {keyword_str}

## 领域概述（仅供了解背景，不要被其限制）
        {chr(10).join([f'- {p.title}: {p.abstract[:200] if p.abstract else ""}' for p, _, _ in relevant_papers[:5]])}

## 要求 — 头脑风暴路径
- 跳出已有论文的框架，大胆想象
- 可以跨领域借鉴思想（如将 CV 方法用于 NLP）
- 可以是全新问题定义、全新评价指标、全新范式
- 甚至可以对现有假设提出挑战

请用 JSON 输出，每个 Idea 包含：
- "title": 一句话标题
- "inspiration": 灵感来源
- "description": 核心思路（3-4句）
- "innovation": 为什么这是全新的
- "approach": 技术路线（具体步骤）
- "feasibility": 可行性 1-10
- "novelty": 创新性 1-10
- "clarity": 方案清晰度 1-10
- "impact": 潜在影响力 1-10

直接输出 JSON 数组，用中文。
"""
        response_b = await llm_service.chat(
            messages=[{"role": "user", "content": path_b_prompt}],
            temperature=1.0, max_tokens=4096,
        )

        # 7. 合并双路径结果，让 LLM 做最终筛选和融合
        merge_prompt = f"""你是一位资深研究导师。以下是同一个研究方向的两组 Idea：

## 路径 A: 文献推理（可行性高）
{response_a}

## 路径 B: 头脑风暴（创新性高）
{response_b}

请从两组中选出最好的 {num_ideas} 个 Idea，可以保留、合并或改进。最终输出 JSON 数组，每个元素包含：
- "title"
- "description"
- "innovation"
- "approach"
- "feasibility": 1-10
- "novelty": 1-10
- "source": "literature" 或 "brainstorm" 或 "merged"

直接输出 JSON 数组，用中文。
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": merge_prompt}],
                temperature=0.5, max_tokens=4096,
            )

            # 4. 解析 JSON 响应
            logger.info(f"LLM 原始响应 (前200字): {response[:200]}...")
            ideas = self._parse_ideas_json(response, project.id, [
                (p, score) for p, score, _ in relevant_papers[:8]
            ])
            logger.info(f"解析得到 {len(ideas)} 个 Idea")

            # 保存到数据库
            created_ideas = []
            for idea_data in ideas:
                idea = ResearchIdea(**idea_data)
                self.session.add(idea)
                created_ideas.append(idea)

            await self.session.commit()
            logger.info(f"为项目 '{project.name}' 生成 {len(created_ideas)} 个 Idea")
            return created_ideas

        except Exception as e:
            logger.error(f"Idea 合并解析失败: {e}")
            await self.session.rollback()
            return []

    def _parse_ideas_json(
        self,
        response: str,
        project_id,
        relevant_papers: list,
    ) -> list[dict]:
        """解析 LLM 返回的 JSON Idea 列表（含 4 维评分）。"""
        import json

        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                data = [data]
        except json.JSONDecodeError:
            logger.warning("JSON 解析失败，尝试文本解析")
            return self._parse_ideas_text(response, project_id, relevant_papers)

        paper_refs = {
            str(i + 1): {"title": p.title, "arxiv_id": p.arxiv_id}
            for i, (p, _) in enumerate(relevant_papers)
        }

        ideas = []
        for item in data:
            if not isinstance(item, dict):
                continue
            # 构建详细描述（含 gap 分析和灵感来源）
            desc_parts = []
            if item.get("background_gap"):
                desc_parts.append(f"【研究空白】{item['background_gap']}")
            if item.get("inspiration"):
                desc_parts.append(f"【灵感来源】{item['inspiration']}")
            desc_parts.append(f"【核心思路】{item.get('description', '')}")
            if item.get("innovation"):
                desc_parts.append(f"【创新点】{item['innovation']}")

            ideas.append({
                "project_id": project_id,
                "title": str(item.get("title", "Untitled"))[:500],
                "description": "\n\n".join(desc_parts)[:4000],
                "approach": str(item.get("approach", "")),
                "novelty": str(item.get("innovation", "")),
                "feasibility_score": float(item.get("feasibility", 7)),
                "novelty_score": float(item.get("novelty", 8)),
                "referenced_papers": paper_refs,
                "status": "draft",
                "metadata": {
                    "source": item.get("source", "merged"),
                    "clarity": float(item.get("clarity", 7)),
                    "impact": float(item.get("impact", 7)),
                },
            })
        return ideas

    def _parse_ideas_text(
        self,
        response: str,
        project_id,
        relevant_papers: list,
    ) -> list[dict]:
        """文本解析（fallback）。"""
        ideas = []
        blocks = response.split("---")
        paper_refs = {
            str(i + 1): {"title": p.title, "arxiv_id": p.arxiv_id}
            for i, (p, _) in enumerate(relevant_papers)
        }

        for block in blocks:
            block = block.strip()
            if not block or len(block) < 50:
                continue
            title = block.split("\n")[0].strip().lstrip("0123456789.。#- ")[:100]
            ideas.append({
                "project_id": project_id,
                "title": title[:500],
                "description": block[:3000],
                "approach": "",
                "novelty": "",
                "feasibility_score": 7.0,
                "novelty_score": 8.0,
                "referenced_papers": paper_refs,
                "status": "draft",
            })
        return ideas

    async def discuss_idea(
        self,
        idea: ResearchIdea,
        user_message: str,
        discussion_history: Optional[list] = None,
    ) -> str:
        """多轮讨论细化 Idea。"""
        # 构建讨论上下文
        context = f"""## Idea: {idea.title}

{idea.description}

可行性: {idea.feasibility_score}/10 | 创新性: {idea.novelty_score}/10
"""

        messages = [
            {"role": "system", "content": f"你是一位资深研究导师。请围绕以下研究 Idea 与学生讨论，帮助其细化方案、识别潜在问题、提出改进建议。\n\n{context}"},
        ]

        if discussion_history:
            messages.extend(discussion_history)

        messages.append({"role": "user", "content": user_message})

        response = await llm_service.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )

        # 更新讨论记录
        current_log = idea.discussion_log or []
        current_log.append({"role": "user", "content": user_message})
        current_log.append({"role": "assistant", "content": response})
        idea.discussion_log = current_log
        idea.status = "discussing"
        await self.session.commit()

        return response

    async def generate_code(
        self,
        idea: ResearchIdea,
        framework: str = "pytorch",
    ) -> str:
        """为 Idea 生成实验代码框架。"""
        prompt = f"""请为以下研究 Idea 生成 {framework} 实验代码框架。

## Idea: {idea.title}

{idea.description or ''}

## 要求
- 使用 {framework} 框架
- 包含完整的训练循环、数据加载、模型定义
- 添加详细的中文注释
- 代码应可直接运行（使用模拟数据如需要）
- 包含必要的 import 语句

请直接输出代码，不要其他解释。
"""

        try:
            code = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4096,
            )

            # 提取代码块
            if "```" in code:
                code_blocks = code.split("```")
                # 取第一个代码块
                for i, block in enumerate(code_blocks):
                    if block.startswith("python") or (i % 2 == 1 and not block.startswith("python")):
                        code = block.replace("python\n", "").strip()
                        break

            # 保存到数据库
            idea.generated_code = code
            idea.status = "implemented"
            await self.session.commit()

            return code
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            await self.session.rollback()
            raise
