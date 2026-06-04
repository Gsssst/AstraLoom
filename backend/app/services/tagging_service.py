"""论文标签服务 — 参考 TopicGPT + LLM-TAKE 的多层次标签系统。"""

import logging
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services.llm import llm_service
from app.db.models.paper import Paper

logger = logging.getLogger(__name__)

# 计算机科学领域标准分类体系
CS_TAXONOMY = {
    "NLP": ["language model", "machine translation", "text generation", "sentiment analysis",
            "question answering", "summarization", "NER", "parsing", "dialogue", "information extraction"],
    "CV": ["image classification", "object detection", "segmentation", "video understanding",
           "image generation", "3D vision", "face recognition", "pose estimation"],
    "ML": ["deep learning", "reinforcement learning", "federated learning", "meta learning",
           "transfer learning", "self-supervised", "few-shot learning", "continual learning"],
    "RL": ["policy gradient", "Q-learning", "actor-critic", "model-based RL", "multi-agent RL",
           "imitation learning", "offline RL", "RLHF"],
    "Systems": ["distributed training", "model compression", "quantization", "pruning",
                "inference optimization", "GPU programming"],
    "IR": ["search", "recommendation", "ranking", "knowledge graph", "question answering"],
    "Speech": ["ASR", "TTS", "speaker recognition", "audio processing"],
    "Multimodal": ["vision-language", "audio-visual", "text-image", "video-text", "VLN"],
    "Security": ["adversarial attack", "privacy", "fairness", "robustness", "backdoor"],
    "Applications": ["healthcare", "education", "science", "code", "robotics", "autonomous driving"],
}


class TaggingService:
    """多层次论文标签服务（参考 TopicGPT + LLM-TAKE）。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_tags(self, paper: Paper) -> dict:
        """生成多层次标签：领域 > 子方向 > 方法 > 任务 > 自由关键词。

        参考 LLM-TAKE 的 5 阶段流程：生成→去幻觉→排序→去重。
        """
        if paper.tags and isinstance(paper.tags, dict) and paper.tags.get("domain"):
            return paper.tags  # 已有层次标签

        # 阶段 1: 生成候选标签
        raw_tags = await self._generate_raw_tags(paper)

        # 阶段 2: 验证和去幻觉（与分类体系对齐）
        validated = await self._validate_tags(raw_tags)

        # 阶段 3: 排序和精简
        final_tags = self._rank_and_trim(validated)

        # 保存到数据库
        paper.tags = final_tags
        await self.session.commit()

        logger.info(f"标签生成完成: {paper.title[:40]}... → domain={final_tags.get('domain', '')}")
        return final_tags

    async def _generate_raw_tags(self, paper: Paper) -> dict:
        """阶段 1: LLM 生成候选标签（参考 TopicGPT 分层生成）。"""
        prompt = f"""## 角色
你是一位熟悉计算机科学全领域的学术文献分类专家。

## 任务
为以下论文生成多层次标签，严格按 JSON 格式输出。

## 论文信息
标题: {paper.title}
摘要: {paper.abstract[:800] if paper.abstract else '无'}
全文片段: {paper.full_text[:1500] if paper.full_text else '无'}

## 可用分类体系（参考）
{json.dumps(CS_TAXONOMY, ensure_ascii=False, indent=2)}

## 输出格式
{{
  "domain": "主要领域（如 NLP/CV/ML/RL/Systems/Multimodal 之一）",
  "subfields": ["子方向1", "子方向2"],
  "methods": ["具体方法名（如 Transformer, RLHF, Diffusion Model 等）"],
  "tasks": ["研究任务（如 machine translation, object detection 等）"],
  "keywords": ["自由关键词5-8个，应具体、可检索"],
  "venue_quality": "估算质量: high(顶会/高引)/medium/low"
}}

规则:
- 每个列表 2-5 项
- 方法/任务名使用英文标准术语
- 不要编造不存在的术语
- 如果论文内容不足以判断，对应字段留空数组 []
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2, max_tokens=1024,
            )
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            tags = json.loads(text)
            if isinstance(tags, dict):
                return tags
        except Exception as e:
            logger.warning(f"标签 JSON 解析失败: {e}")

        # 回退
        return {"domain": "", "subfields": [], "methods": [], "tasks": [], "keywords": [], "venue_quality": "medium"}

    async def _validate_tags(self, tags: dict) -> dict:
        """阶段 2: LLM 验证标签质量（参考 World Bank LLM-as-judge）。"""
        if not tags.get("domain"):
            return tags

        prompt = f"""## 角色
你是一位严格的学术文献分类审核专家。

## 任务
审核以下论文标签是否准确，纠正错误的、补充遗漏的。

## 当前标签
{json.dumps(tags, ensure_ascii=False)}

## 已知分类体系
{json.dumps(CS_TAXONOMY, ensure_ascii=False, indent=2)}

## 审核规则
1. domain 必须在已知分类体系中
2. keywords 不能包含无意义的通用词（如 "method", "result", "experiment"）
3. methods 中的方法名必须是真实存在的
4. 如果某个字段明显错误，纠正它
5. 如果论文质量明显很高（如多篇顶会引用），venue_quality 应为 "high"

## 输出
输出修正后的完整 JSON，格式与输入相同。
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=1024,
            )
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            validated = json.loads(text)
            if isinstance(validated, dict):
                return validated
        except Exception as e:
            logger.warning(f"标签验证失败: {e}")

        return tags

    def _rank_and_trim(self, tags: dict) -> dict:
        """阶段 3: 精简标签，确保每个列表不超过 5 项。"""
        for key in ["subfields", "methods", "tasks", "keywords"]:
            if key in tags and isinstance(tags[key], list):
                # 去重 + 去空 + 限制数量
                seen = set()
                cleaned = []
                for item in tags[key]:
                    item = str(item).strip().lower()
                    if item and item not in seen and len(item) > 1 and item not in ["method", "result", "experiment", "paper", "model"]:
                        cleaned.append(item)
                        seen.add(item)
                tags[key] = cleaned[:5]
        return tags

    async def tag_all_papers(self) -> dict:
        """为所有论文生成层次标签。"""
        result = await self.session.execute(
            select(Paper).where(
                (Paper.tags == None) |
                (Paper.tags == []) |
                (func.jsonb_typeof(Paper.tags) != 'object')
            ).limit(20)
        )
        papers = result.scalars().all()

        tagged = 0
        for paper in papers:
            try:
                await self.generate_tags(paper)
                tagged += 1
            except Exception as e:
                logger.error(f"标签失败 {paper.id}: {e}")

        return {"total": len(papers), "tagged": tagged, "failed": len(papers) - tagged}
