"""论文全文分块与检索服务。

将论文 full_text 按段落切分为 chunks，使用 BM25 关键词检索
与用户问题最相关的片段。避免将整篇论文塞入 LLM 上下文。
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EvidenceChunk:
    """A retrieved paper snippet that can be shown as answer evidence."""

    text: str
    score: float
    section: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None

    def snippet(self, limit: int = 320) -> str:
        cleaned = re.sub(r"\s+", " ", self.text).strip()
        return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


class PaperChunkService:
    """论文分块检索服务。"""

    # 分块参数
    CHUNK_MIN_CHARS = 400
    CHUNK_MAX_CHARS = 1000
    CHUNK_OVERLAP = 100  # 重叠字符数，保持上下文连贯
    SECTION_ALIASES = {
        "abstract": ("abstract", "摘要"),
        "introduction": ("introduction", "intro", "引言", "导言"),
        "related_work": ("related work", "related works", "literature review", "相关工作", "文献综述"),
        "method": ("method", "methods", "methodology", "approach", "方法", "模型方法"),
        "experiments": ("experiment", "experiments", "evaluation", "results", "实验", "评估", "结果"),
        "conclusion": ("conclusion", "conclusions", "discussion", "结论", "总结", "讨论"),
    }

    @staticmethod
    def chunk_full_text(full_text: str) -> List[str]:
        """将论文全文按段落切分为 chunks。

        策略：
        1. 按双换行（段落）切分
        2. 短段落（< MIN）合并
        3. 长段落（> MAX）按句子再切分
        """
        if not full_text or len(full_text) < 200:
            return [full_text] if full_text else []

        # Step 1: 按段落切分
        paragraphs = re.split(r'\n\s*\n', full_text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Step 2: 合并短段落，切分长段落
        chunks = []
        buffer = ""

        for para in paragraphs:
            if len(buffer) + len(para) < PaperChunkService.CHUNK_MIN_CHARS:
                # 与 buffer 合并
                buffer = f"{buffer}\n\n{para}" if buffer else para
            else:
                # buffer 已足够大，保存
                if buffer:
                    chunks.append(buffer.strip())
                buffer = para

            # 当前 buffer 太长，按句子切分
            while len(buffer) > PaperChunkService.CHUNK_MAX_CHARS:
                # 找最佳切割点（句子边界）
                split_pos = PaperChunkService._find_split_point(buffer)
                chunks.append(buffer[:split_pos].strip())
                # 保留重叠部分
                overlap_start = max(0, split_pos - PaperChunkService.CHUNK_OVERLAP)
                buffer = buffer[overlap_start:]

        # 处理残留
        if buffer.strip():
            chunks.append(buffer.strip())

        logger.info(f"论文分块: {len(full_text)} 字符 → {len(chunks)} chunks")
        return chunks

    @staticmethod
    def _find_split_point(text: str) -> int:
        """在 CHUNK_MAX_CHARS 附近找最佳切割点（句子边界）。"""
        target = PaperChunkService.CHUNK_MAX_CHARS
        # 在 target 前后 200 字符范围内找句子结束符
        search_start = max(0, target - 200)
        search_end = min(len(text), target + 200)

        # 优先级：句号 > 换行 > 逗号 > 空格
        for punct in ['. ', '.\n', '。', '.\n\n', ', ', '，', ' ']:
            pos = text.rfind(punct, search_start, search_end)
            if pos > 0:
                return pos + len(punct.rstrip())

        return target

    @classmethod
    def detect_requested_sections(cls, query: str) -> List[str]:
        """识别用户明确点名的论文章节。"""
        normalized_query = re.sub(r'[_-]+', ' ', query.lower())
        return [
            section
            for section, aliases in cls.SECTION_ALIASES.items()
            if any(alias in normalized_query for alias in aliases)
        ]

    @classmethod
    def _match_section_heading(cls, line: str) -> Optional[str]:
        """将标题行映射到规范章节名，忽略编号和简单副标题。"""
        if not line.strip() or len(line.strip()) > 100:
            return None

        normalized = line.strip().lower()
        normalized = re.sub(r'^\s*(?:section|chapter)\s+', '', normalized)
        normalized = re.sub(r'^\s*(?:\d+(?:\.\d+)*|[ivxlcdm]+)[\s.)、:：-]+', '', normalized)
        normalized = re.sub(r'[\s:：.]+$', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)

        for section, aliases in cls.SECTION_ALIASES.items():
            for alias in aliases:
                if normalized == alias:
                    return section
                if normalized.startswith(f"{alias} ") and len(normalized.split()) <= 8:
                    return section
        return None

    @classmethod
    def split_sections(cls, full_text: str) -> List[Tuple[str, str]]:
        """按常见论文标题拆分正文，保留标题本身作为检索线索。"""
        sections: List[Tuple[str, str]] = []
        current_section: Optional[str] = None
        current_lines: List[str] = []

        for line in full_text.splitlines():
            matched_section = cls._match_section_heading(line)
            if matched_section:
                if current_section and current_lines:
                    sections.append((current_section, "\n".join(current_lines).strip()))
                current_section = matched_section
                current_lines = [line.strip()]
            elif current_section:
                current_lines.append(line)

        if current_section and current_lines:
            sections.append((current_section, "\n".join(current_lines).strip()))
        return sections

    @classmethod
    def _section_for_text(cls, text: str) -> Optional[str]:
        for line in text.splitlines()[:8]:
            matched = cls._match_section_heading(line)
            if matched:
                return matched
        return None

    @classmethod
    def _page_evidence_candidates(cls, page_texts: List[str]) -> List[EvidenceChunk]:
        candidates: List[EvidenceChunk] = []
        current_section: Optional[str] = None
        for page_index, page_text in enumerate(page_texts, 1):
            if not page_text or not page_text.strip():
                continue
            detected = cls._section_for_text(page_text)
            if detected:
                current_section = detected
            for chunk in cls.chunk_full_text(page_text):
                candidates.append(EvidenceChunk(
                    text=chunk,
                    score=0.0,
                    section=cls._section_for_text(chunk) or current_section,
                    page_start=page_index,
                    page_end=page_index,
                ))
        return candidates

    @classmethod
    def _document_evidence_candidates(cls, full_text: str) -> List[EvidenceChunk]:
        sections = cls.split_sections(full_text)
        if sections:
            candidates: List[EvidenceChunk] = []
            for section, section_text in sections:
                candidates.extend(
                    EvidenceChunk(text=chunk, score=0.0, section=section)
                    for chunk in cls.chunk_full_text(section_text)
                )
            return candidates
        return [EvidenceChunk(text=chunk, score=0.0) for chunk in cls.chunk_full_text(full_text)]

    @classmethod
    def retrieve_evidence(
        cls,
        full_text: str,
        query: str,
        top_k: int = 3,
        page_texts: Optional[List[str]] = None,
    ) -> Tuple[List[EvidenceChunk], str]:
        """Return structured evidence snippets, preferring explicitly requested sections."""
        candidates = cls._page_evidence_candidates(page_texts) if page_texts else cls._document_evidence_candidates(full_text)
        requested_sections = set(cls.detect_requested_sections(query))
        if requested_sections:
            section_candidates = [item for item in candidates if item.section in requested_sections]
            if section_candidates:
                return cls.search_evidence_chunks(section_candidates, query, top_k=top_k), "section"
        return cls.search_evidence_chunks(candidates, query, top_k=top_k), "document"

    @classmethod
    def retrieve_chunks(cls, full_text: str, query: str, top_k: int = 3) -> Tuple[List[Tuple[str, float]], str]:
        """优先检索用户指定章节；未命中时回退到全文 BM25。"""
        evidence, scope = cls.retrieve_evidence(full_text, query, top_k=top_k)
        return [(item.text, item.score) for item in evidence], scope

    @classmethod
    def search_evidence_chunks(
        cls,
        chunks: List[EvidenceChunk],
        query: str,
        top_k: int = 3,
    ) -> List[EvidenceChunk]:
        scored = cls.search_chunks([chunk.text for chunk in chunks], query, top_k=top_k)
        by_text: dict[str, List[EvidenceChunk]] = {}
        for chunk in chunks:
            by_text.setdefault(chunk.text, []).append(chunk)
        results: List[EvidenceChunk] = []
        for text, score in scored:
            match_list = by_text.get(text) or []
            base = match_list.pop(0) if match_list else EvidenceChunk(text=text, score=0.0)
            results.append(EvidenceChunk(
                text=base.text,
                score=score,
                section=base.section,
                page_start=base.page_start,
                page_end=base.page_end,
            ))
        return results

    @staticmethod
    def search_chunks(chunks: List[str], query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """使用 BM25 检索与 query 最相关的 chunks。

        Args:
            chunks: 论文分块列表
            query: 用户问题
            top_k: 返回的最相关片段数

        Returns:
            [(chunk_text, relevance_score), ...] 按相关度降序
        """
        if not chunks:
            return []

        if len(chunks) <= top_k:
            return [(c, 1.0) for c in chunks]

        try:
            from rank_bm25 import BM25Okapi

            # Tokenize: 中英文混合分词
            def tokenize(text: str) -> List[str]:
                # 中文按字符+词，英文按空格
                tokens = []
                # 英文单词
                english_words = re.findall(r'[a-zA-Z]+', text.lower())
                tokens.extend(english_words)
                # 中文双字组合 (bigram)
                chinese_chars = re.findall(r'[一-鿿]', text)
                for i in range(len(chinese_chars) - 1):
                    tokens.append(chinese_chars[i] + chinese_chars[i + 1])
                # 添加单个中文字符
                tokens.extend(chinese_chars)
                return tokens

            tokenized_chunks = [tokenize(c) for c in chunks]
            tokenized_query = tokenize(query)

            bm25 = BM25Okapi(tokenized_chunks)
            scores = bm25.get_scores(tokenized_query)

            # 按分数排序取 top_k
            ranked = sorted(
                enumerate(scores),
                key=lambda x: x[1],
                reverse=True,
            )[:top_k]

            # 归一化分数
            max_score = max(scores) if max(scores) > 0 else 1
            return [(chunks[i], round(s / max_score, 3)) for i, s in ranked]

        except ImportError:
            # 无 BM25 → 关键词简单匹配
            return PaperChunkService._fallback_search(chunks, query, top_k)

    @staticmethod
    def _fallback_search(chunks: List[str], query: str, top_k: int) -> List[Tuple[str, float]]:
        """BM25 不可用时的关键词匹配降级方案。"""
        query_lower = query.lower()
        query_words = set(re.findall(r'[a-zA-Z一-鿿]+', query_lower))

        scored = []
        for i, chunk in enumerate(chunks):
            chunk_lower = chunk.lower()
            # 计算匹配词数占比
            matches = sum(1 for w in query_words if w in chunk_lower)
            score = matches / max(len(query_words), 1)
            if score > 0:
                scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        result = scored[:top_k]

        # 不够 top_k 时补充前面的 chunks
        if len(result) < top_k:
            for i, chunk in enumerate(chunks):
                if (chunk, 0.0) not in result:
                    result.append((chunk, 0.0))
                if len(result) >= top_k:
                    break

        return result


# 全局单例
paper_chunk_service = PaperChunkService()
