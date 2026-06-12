"""三层记忆服务 — 参考 mem0/MemoryLLM/lethes 的混合上下文管理。"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.llm import llm_service
from app.db.models.chat import ChatSession, ChatMessage

logger = logging.getLogger(__name__)
PAPER_FULL_TEXT_LOAD_TIMEOUT_SECONDS = 20.0

# 配置
SHORT_TERM_COUNT = 10       # 最近 N 条消息始终保留
SUMMARY_TRIGGER = 15        # 超过此数量触发增量摘要
MAX_CONTEXT_TOKENS = 6000   # 上下文 token 上限
SUMMARY_MODEL_TEMP = 0.2    # 摘要用低温（确定性输出）


class MemoryService:
    """三层记忆管理：滑动窗口 + 增量摘要 + 语义检索（参考 mem0/MemoryLLM/lethes）。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def build_context(
        self,
        session: ChatSession,
        current_query: str,
        extra_context: str = "",
    ) -> List[dict]:
        """构建优化后的对话上下文，智能管理 token 预算。"""

        # 1. 获取所有消息
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at)
        )
        all_msgs = list(result.scalars().all())

        if not all_msgs:
            context = []
            if extra_context:
                context.append({"role": "system", "content": extra_context})
            context.append({"role": "user", "content": current_query})
            return context

        total_count = len(all_msgs)

        # 2. 估算 token 数
        total_chars = sum(len(m.content) for m in all_msgs)
        estimated_tokens = total_chars // 2.5 + total_count * 4

        # 3. 情况1：对话较短，全部保留
        if total_count <= SHORT_TERM_COUNT or estimated_tokens < MAX_CONTEXT_TOKENS:
            context = [{"role": m.role, "content": m.content} for m in all_msgs]
            return self._finalize_context(context, extra_context, session)

        # 4. 情况2：需要压缩 — 三层记忆架构
        context = await self._build_hybrid_context(all_msgs, extra_context, session)

        return context

    async def _build_hybrid_context(
        self,
        all_msgs: list,
        extra_context: str,
        session: ChatSession,
    ) -> List[dict]:
        """构建混合上下文：摘要 + 滑动窗口。"""

        total = len(all_msgs)
        recent = all_msgs[-SHORT_TERM_COUNT:]     # Layer 1: 最近 N 条
        older = all_msgs[:-SHORT_TERM_COUNT]       # 需要压缩的部分

        # Layer 2: 增量摘要（参考 lethes 的多层级摘要）
        summary = await self._generate_summary(older, session)

        # 构建最终上下文
        context = []
        if extra_context:
            context.append({"role": "system", "content": extra_context})

        # 注入摘要（作为系统消息）
        context.append({
            "role": "system",
            "content": f"[对话历史摘要 — 共 {total} 轮，以下是前 {total - SHORT_TERM_COUNT} 轮的要点]\n{summary}\n\n---\n以下是最近的对话："
        })

        # 添加最近消息
        for m in recent:
            context.append({"role": m.role, "content": m.content})

        logger.info(f"混合上下文: {total} 条消息 → 摘要 + {len(recent)} 条 (估算节省 {len(older) * 200} tokens)")
        return context

    async def _generate_summary(self, messages: list, session: ChatSession) -> str:
        """生成对话摘要（参考 MemoryLLM 增量摘要策略）。

        使用低温 + 结构化输出，确保关键信息不丢失。
        """
        # 只取每条消息的前 200 字做摘要素材
        history_text = "\n".join([
            f"[{m.role}]: {m.content[:200]}" for m in messages[::2]  # 跳帧采样，减少 token
        ][:30])  # 最多 30 条素材

        prompt = f"""## 任务
将以下对话历史压缩为一段简洁摘要（100-200字），保留以下关键信息：
1. 用户的研究方向和关注点
2. 讨论过的主要技术问题和结论
3. 任何明确的需求或决策

## 对话历史
{history_text}

## 输出
直接输出摘要文本，不要任务描述或其他前缀。
"""
        try:
            summary = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=SUMMARY_MODEL_TEMP,
                max_tokens=400,
            )
            # 存储摘要到 session metadata
            meta = session.metadata_json or {}
            meta["last_summary"] = summary
            meta["summary_generated_at"] = str(len(messages))
            session.metadata_json = meta
            await self.session.commit()
            return summary.strip()
        except Exception as e:
            logger.warning(f"摘要生成失败: {e}")
            return f"以下为 {len(messages)} 轮对话的简要回顾"

    def _finalize_context(
        self,
        context: List[dict],
        extra_context: str,
        session: ChatSession,
    ) -> List[dict]:
        """最终上下文的收尾处理。"""
        if extra_context:
            context.insert(0, {"role": "system", "content": extra_context})
        return context


async def build_paper_context(
    paper,
    question: str,
    history: List[dict] = None,
    max_tokens: int = 6000,
) -> List[dict]:
    context, _evidence = await build_paper_context_with_evidence(
        paper,
        question,
        history=history,
        max_tokens=max_tokens,
    )
    return context


async def build_paper_context_with_evidence(
    paper,
    question: str,
    history: List[dict] = None,
    max_tokens: int = 6000,
) -> tuple[List[dict], list[dict]]:
    """为论文专属问答构建优化上下文。

    与之前的"全文注入"不同，现在使用分块检索（RAG over paper）：
    1. 始终包含论文 metadata（标题/作者/摘要）
    2. 将全文按段落切片，BM25 检索与问题最相关的 3 个片段
    3. 大幅减少输入 token（~8000 chars → ~2800 chars）
    """
    # 确保有全文（如果已缓存则直接使用，否则尝试获取）
    from app.services.report_service import ensure_full_text
    if not paper.full_text or len(paper.full_text) < 500:
        try:
            import asyncio
            await asyncio.wait_for(
                ensure_full_text(paper),
                timeout=PAPER_FULL_TEXT_LOAD_TIMEOUT_SECONDS,
            )
        except (asyncio.TimeoutError, Exception):
            logger.warning(f"PDF 全文加载超时，使用摘要: {paper.title[:50]}")

    # 构建始终存在的 metadata
    authors_str = ', '.join(paper.authors[:5]) if isinstance(paper.authors, list) else paper.authors or '未知'
    metadata = f"""## 论文信息
标题: {paper.title}
作者: {authors_str}
年份: {paper.year or 'N/A'}
摘要: {paper.abstract or '无'}"""

    # 分块检索相关片段（RAG over paper）
    if paper.full_text and len(paper.full_text) >= 500:
        from app.services.paper_chunk_service import paper_chunk_service
        page_texts = []
        structured_blocks = []
        try:
            from app.services.report_service import (
                ensure_structured_pdf_content,
                extract_pdf_page_texts,
                resolve_paper_pdf_path,
                structured_pdf_evidence_blocks_from_paper,
            )
            import asyncio

            pdf_path = await resolve_paper_pdf_path(paper)
            if pdf_path:
                page_texts = await asyncio.to_thread(extract_pdf_page_texts, pdf_path)
                structured_blocks = structured_pdf_evidence_blocks_from_paper(paper)
                if not structured_blocks:
                    structured_extraction = await ensure_structured_pdf_content(paper)
                    structured_blocks = structured_extraction.to_evidence_blocks() if structured_extraction else []
        except Exception as exc:
            logger.warning(f"PDF 按页/结构化解析失败，使用全文证据: {exc}")
        evidence_top_k = paper_chunk_service.recommended_evidence_top_k(question)
        evidence_chunks, retrieval_scope = paper_chunk_service.retrieve_evidence(
            paper.full_text,
            question,
            top_k=evidence_top_k,
            page_texts=page_texts or None,
            structured_blocks=structured_blocks or None,
        )

        if evidence_chunks:
            scope_label = "用户指定章节优先检索" if retrieval_scope == "section" else "根据问题检索"
            chunk_lines = [f"## 相关片段（{scope_label}）"]
            evidence_refs = []
            for i, evidence in enumerate(evidence_chunks):
                label = "★ 高度相关" if evidence.score > 0.8 else ("◎ 相关" if evidence.score > 0.5 else "○ 部分相关")
                page_label = f"，PDF 第 {evidence.page_start} 页" if evidence.page_start else ""
                section_label = f"，章节: {evidence.section}" if evidence.section else ""
                type_label = {
                    "experiment_dossier": "，类型: 实验证据档案",
                    "table_catalog": "，类型: 表格目录",
                    "table_pack": "，类型: 表格证据包",
                    "table": "，类型: 表格",
                    "caption": "，类型: 图/表标题",
                    "ocr": "，类型: OCR 文本",
                    "formula": "，类型: 公式",
                }.get(evidence.source_type, "")
                evidence_id = f"E{i + 1}"
                chunk_lines.append(
                    f"\n### [{evidence_id}] {label} (相关度: {evidence.score:.0%}{section_label}{page_label}{type_label})\n{evidence.text}"
                )
                evidence_refs.append({
                    "id": evidence_id,
                    "title": paper.title,
                    "source": "current_paper",
                    "type": "paper_evidence",
                    "evidence_type": evidence.source_type,
                    "parser_source": evidence.source,
                    "section": evidence.section,
                    "page": evidence.page_start,
                    "page_start": evidence.page_start,
                    "page_end": evidence.page_end,
                    "score": evidence.score,
                    "snippet": evidence.snippet(),
                    "metadata": evidence.metadata or {},
                })

            relevant_context = "\n".join(chunk_lines)
        else:
            # 全文太短，直接用全文
            relevant_context = f"## 全文\n{paper.full_text[:2000]}"
            evidence_refs = []
    else:
        # 无全文，使用摘要
        relevant_context = f"## 摘要\n{paper.abstract or '无'}"
        evidence_refs = []

    paper_context = f"{metadata}\n\n{relevant_context}"
    evidence_coverage = min(1.0, len(evidence_refs) / 3) if paper.full_text and len(paper.full_text) >= 500 else 0.0
    if not evidence_refs:
        evidence_warning = "当前没有检索到可定位的正文证据。若用户要求 Introduction、Method、Experiments 等章节，请明确说明“当前论文内容不足”，不要仅根据摘要推测。"
    else:
        evidence_warning = f"当前检索到 {len(evidence_refs)} 条正文/结构化证据，引用覆盖率约 {evidence_coverage:.0%}。回答中的关键结论应尽量标注 [E1]、[E2] 这样的证据编号。"

    context = []
    context.append({
        "role": "system",
        "content": (
            "你是这篇论文的专家助手。请严格基于以下论文内容回答用户问题。"
            "回答中的关键结论必须绑定证据编号（例如 [E1]）。"
            "证据类型可能包含正文、表格、图/表标题、OCR 文本或公式；"
            "如果证据不足以支持用户要求的章节、实验数据或方法细节，请明确说明“当前论文内容不足”，"
            "不要根据摘要或常识补全不存在的内容。"
            f"{evidence_warning}\n\n"
            f"{paper_context}"
        )
    })

    # 添加历史对话（压缩版）
    if history:
        trimmed = []
        for h in history[-8:]:
            content = h.get("content", "")
            if len(content) > 500:
                content = content[:500] + "..."
            trimmed.append({"role": h.get("role", "user"), "content": content})
        context.extend(trimmed)

    context.append({"role": "user", "content": question})
    return context, evidence_refs
