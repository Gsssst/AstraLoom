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
    source_type: str = "text"
    source: str = "current_paper"
    metadata: Optional[dict] = None

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
    TABLE_QUERY_TERMS = (
        "table", "benchmark", "baseline", "metric", "metrics", "reward", "ablation", "result", "results",
        "c-acc", "etf1", "tiou", "tf1", "gemini", "seed", "qwen", "gpt",
        "表格", "基准", "指标", "结果", "对比", "消融", "奖励", "贡献", "评估",
    )
    TABLE_CAPTION_PATTERN = re.compile(r"(?:^|\b)table\s*\.?\s*\d+|表\s*\d+", re.I)
    FIGURE_CAPTION_PATTERN = re.compile(r"(?:^|\b)(?:fig(?:ure)?\s*\.?\s*\d+|图\s*\d+)", re.I)

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
    def is_table_like_query(cls, query: str) -> bool:
        normalized = re.sub(r"\s+", " ", (query or "").lower())
        return any(term in normalized for term in cls.TABLE_QUERY_TERMS)

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
                    source_type="text",
                ))
        return candidates

    @classmethod
    def _document_evidence_candidates(cls, full_text: str) -> List[EvidenceChunk]:
        sections = cls.split_sections(full_text)
        if sections:
            candidates: List[EvidenceChunk] = []
            for section, section_text in sections:
                candidates.extend(
                    EvidenceChunk(text=chunk, score=0.0, section=section, source_type="text")
                    for chunk in cls.chunk_full_text(section_text)
                )
            return candidates
        return [EvidenceChunk(text=chunk, score=0.0, source_type="text") for chunk in cls.chunk_full_text(full_text)]

    @classmethod
    def _structured_evidence_candidates(cls, structured_blocks: Optional[List[dict]]) -> List[EvidenceChunk]:
        candidates: List[EvidenceChunk] = []
        for block in structured_blocks or []:
            if not isinstance(block, dict):
                continue
            text = str(block.get("text") or "").strip()
            if not text:
                continue
            page = block.get("page")
            candidates.append(EvidenceChunk(
                text=text,
                score=0.0,
                section=None,
                page_start=page if isinstance(page, int) else None,
                page_end=page if isinstance(page, int) else None,
                source_type=str(block.get("type") or "structured"),
                source=str(block.get("source") or "pdf_structured"),
                metadata=block.get("metadata") if isinstance(block.get("metadata"), dict) else {},
            ))
        return candidates

    @classmethod
    def retrieve_evidence(
        cls,
        full_text: str,
        query: str,
        top_k: int = 3,
        page_texts: Optional[List[str]] = None,
        structured_blocks: Optional[List[dict]] = None,
    ) -> Tuple[List[EvidenceChunk], str]:
        """Return structured evidence snippets, preferring explicitly requested sections."""
        candidates = cls._page_evidence_candidates(page_texts) if page_texts else cls._document_evidence_candidates(full_text)
        structured_candidates = cls._structured_evidence_candidates(structured_blocks)
        table_like_query = cls.is_table_like_query(query)
        candidates = [*structured_candidates, *candidates]
        requested_sections = set(cls.detect_requested_sections(query))
        if requested_sections:
            section_candidates = [item for item in candidates if item.section in requested_sections]
            if section_candidates:
                section_results = cls.search_evidence_chunks(
                    section_candidates,
                    query,
                    top_k=top_k,
                    requested_sections=requested_sections,
                )
                if table_like_query and structured_candidates:
                    table_results = cls._table_evidence_lane(structured_candidates, query, top_k=2)
                    return cls._merge_evidence_lanes(table_results, section_results, top_k=top_k), "section+structured"
                return section_results, "section"
        scope = "structured+document" if structured_candidates else "document"
        if table_like_query and structured_candidates:
            table_results = cls._table_evidence_lane(structured_candidates, query, top_k=2)
            document_results = cls.search_evidence_chunks(
                candidates,
                query,
                top_k=top_k,
                requested_sections=requested_sections,
            )
            return cls._merge_evidence_lanes(table_results, document_results, top_k=top_k), scope
        return cls.search_evidence_chunks(candidates, query, top_k=top_k, requested_sections=requested_sections), scope

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
        requested_sections: Optional[set[str]] = None,
    ) -> List[EvidenceChunk]:
        scored = cls.search_chunks(
            [chunk.text for chunk in chunks],
            query,
            top_k=max(top_k * 3, top_k),
            requested_sections=requested_sections,
            evidence_chunks=chunks,
        )
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
                source_type=base.source_type,
                source=base.source,
                metadata=base.metadata,
            ))
        return cls._suppress_redundant_evidence(results, top_k=top_k)

    @classmethod
    def _table_evidence_lane(cls, structured_candidates: List[EvidenceChunk], query: str, top_k: int) -> List[EvidenceChunk]:
        table_candidates = [
            item for item in structured_candidates
            if item.source_type in {"table", "caption"}
        ]
        if not table_candidates:
            return []
        reranked = [
            EvidenceChunk(
                text=item.text,
                score=cls._structured_evidence_score(item, query),
                section=item.section,
                page_start=item.page_start,
                page_end=item.page_end,
                source_type=item.source_type,
                source=item.source,
                metadata=item.metadata,
            )
            for item in table_candidates
        ]
        reranked.sort(key=lambda item: (cls._table_primary_intent_score(item, query), item.score), reverse=True)
        selected: List[EvidenceChunk] = []
        best_table = next((item for item in reranked if item.source_type == "table" and item.score >= 0.25), None)
        if best_table:
            selected.append(best_table)
        selected.extend(item for item in reranked if item is not best_table and item.score >= 0.12)
        if not selected:
            selected = reranked
        return cls._suppress_redundant_evidence(selected, top_k=top_k)

    @classmethod
    def _structured_evidence_score(cls, item: EvidenceChunk, query: str) -> float:
        text = item.text or ""
        lower_text = text.lower()
        compact_text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", lower_text)
        table_caption = cls._is_table_caption(item)
        figure_caption = cls._is_figure_caption(item)
        score = 0.25 if item.source_type == "table" else 0.18 if table_caption else 0.02
        if item.source_type == "table":
            rows = cls._markdown_table_rows(text)
            cells = [cell.strip() for row in rows for cell in row]
            non_empty_cells = sum(1 for cell in cells if cell)
            header = rows[0] if rows else []
            generic_headers = sum(1 for cell in header if re.match(r"^column\s+\d+$", cell, re.I))
            empty_ratio = (sum(1 for cell in cells if not cell) / len(cells)) if cells else 1.0
            if len(rows) >= 3 and non_empty_cells >= 6:
                score += 0.12
            if len(rows) >= 4:
                score += 0.06
            if rows and max(len(row) for row in rows) >= 3:
                score += 0.04
            if len(rows) <= 2 or non_empty_cells <= 4:
                score -= 0.22
            if generic_headers:
                score -= min(0.18, generic_headers * 0.05)
            if empty_ratio >= 0.35:
                score -= 0.16
        elif item.source_type == "caption":
            if table_caption:
                score += 0.12
                if cls.TABLE_CAPTION_PATTERN.search(text):
                    score += 0.05
            if figure_caption:
                score -= 0.25
        number_count = len(re.findall(r"(?:[+-]?\d+(?:\.\d+)?%?)", text))
        if item.source_type == "table":
            score += min(0.10, number_count * 0.012)
        elif table_caption:
            score += min(0.03, number_count * 0.006)
        if cls.is_table_like_query(query):
            query_tokens = cls._chunk_tokens(query)
            text_tokens = cls._chunk_tokens(text)
            overlap = len(query_tokens & text_tokens)
            if query_tokens:
                score += min(0.22, (overlap / len(query_tokens)) * 0.22)
            focus_matches = 0
            for term in cls._table_query_focus_terms(query):
                normalized_term = re.sub(r"\s+", " ", term.lower()).strip()
                compact_term = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", normalized_term)
                if normalized_term and normalized_term in lower_text:
                    focus_matches += 1
                elif compact_term and compact_term in compact_text:
                    focus_matches += 1
            score += min(0.30, focus_matches * 0.06)
            if re.search(r"caption\s*reward|奖励|reward", (query or "").lower(), re.I):
                if re.search(r"rcaption|caption\s*reward|reward\s*functions?|奖励", lower_text, re.I):
                    score += 0.18
            if re.search(r"caption\s*reward", (query or "").lower(), re.I) and "rcaption" in lower_text:
                score += 0.12
            if re.search(r"baseline|对比", (query or "").lower(), re.I):
                if re.search(r"baseline|gemini|gpt|qwen|seed|model", lower_text, re.I):
                    score += 0.08
        source = (item.source or "").lower()
        if source in {"docling", "command", "mineru", "marker"}:
            score += 0.03
        elif source == "pdfplumber" and item.source_type == "table":
            score -= 0.02
        return round(max(0.0, min(1.0, score)), 3)

    @staticmethod
    def _table_primary_intent_score(item: EvidenceChunk, query: str) -> float:
        lower_query = (query or "").lower()
        lower_text = (item.text or "").lower()
        compact_text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", lower_text)
        score = 0.0
        if re.search(r"caption\s*reward|奖励|reward", lower_query, re.I):
            if (
                item.source_type == "table"
                and not PaperChunkService._is_low_fidelity_table(item)
                and re.search(r"rcaption|caption\s*reward|reward\s*functions?|奖励", lower_text, re.I)
            ):
                score += 2.0
            elif item.source_type == "caption" and re.search(r"caption\s*reward|reward\s*functions?|奖励", lower_text, re.I):
                score += 0.8
        if re.search(r"baseline|对比", lower_query, re.I):
            if re.search(r"baseline|gemini|gpt|qwen|seed", lower_text, re.I):
                score += 1.0
            elif item.source_type == "table" and "model" in lower_text:
                score += 0.5
        if "omtg" in lower_query and "omtg" in compact_text:
            score += 0.2
        if item.source_type != "table":
            score -= 0.4
        return score

    @classmethod
    def _is_low_fidelity_table(cls, item: EvidenceChunk) -> bool:
        if item.source_type != "table":
            return False
        rows = cls._markdown_table_rows(item.text or "")
        cells = [cell.strip() for row in rows for cell in row]
        if not cells:
            return True
        non_empty_cells = sum(1 for cell in cells if cell)
        empty_ratio = sum(1 for cell in cells if not cell) / len(cells)
        header = rows[0] if rows else []
        generic_headers = sum(1 for cell in header if re.match(r"^column\s+\d+$", cell, re.I))
        generic_ratio = generic_headers / len(header) if header else 1.0
        return len(rows) < 2 or non_empty_cells <= 4 or empty_ratio >= 0.35 or generic_ratio >= 0.35

    @classmethod
    def _is_table_caption(cls, item: EvidenceChunk) -> bool:
        metadata = item.metadata or {}
        caption_type = str(metadata.get("caption_type") or "").lower()
        return caption_type == "table_caption" or bool(cls.TABLE_CAPTION_PATTERN.search(item.text or ""))

    @classmethod
    def _is_figure_caption(cls, item: EvidenceChunk) -> bool:
        metadata = item.metadata or {}
        caption_type = str(metadata.get("caption_type") or "").lower()
        return caption_type == "figure_caption" or bool(cls.FIGURE_CAPTION_PATTERN.search(item.text or ""))

    @staticmethod
    def _markdown_table_rows(text: str) -> List[List[str]]:
        rows: List[List[str]] = []
        for line in (text or "").splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or not stripped.endswith("|"):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and all(re.fullmatch(r"-{3,}:?", cell.replace(" ", "")) for cell in cells):
                continue
            rows.append(cells)
        return rows

    @staticmethod
    def _table_query_focus_terms(query: str) -> List[str]:
        lower = (query or "").lower()
        terms = re.findall(r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*|\d+(?:\.\d+)?", lower)
        if "caption reward" in lower or ("caption" in lower and "reward" in lower):
            terms.extend(["caption reward", "rcaption", "reward functions", "reward"])
        if "omtg" in lower:
            terms.extend(["omtg", "omtg bench", "omt gbench"])
        if "bench" in lower or "benchmark" in lower or "基准" in query:
            terms.extend(["bench", "benchmark"])
        if "baseline" in lower or "对比" in query:
            terms.extend(["baseline", "gemini", "qwen", "gpt"])
        if "seed" in lower:
            terms.append("seed")
        if "gemini" in lower:
            terms.append("gemini")
        if "etf1" in lower or "et f1" in lower:
            terms.extend(["etf1", "et f1"])
        if "c-acc" in lower or "c acc" in lower:
            terms.extend(["c-acc", "c acc"])
        if "tiou" in lower:
            terms.append("tiou")
        if "tf1" in lower:
            terms.append("tf1")
        for chinese, mapped in {
            "表格": "table",
            "指标": "metric",
            "结果": "result",
            "消融": "ablation",
            "奖励": "reward",
            "贡献": "gain",
            "评估": "evaluation",
        }.items():
            if chinese in query:
                terms.append(mapped)
        return list(dict.fromkeys(term for term in terms if term))

    @classmethod
    def _merge_evidence_lanes(
        cls,
        priority: List[EvidenceChunk],
        secondary: List[EvidenceChunk],
        *,
        top_k: int,
    ) -> List[EvidenceChunk]:
        merged: List[EvidenceChunk] = []
        seen: set[tuple[str, Optional[int], str]] = set()
        for item in [*priority, *secondary]:
            key = (item.source_type, item.page_start, item.text)
            if key in seen:
                continue
            seen.add(key)
            if any(cls._chunk_similarity(item.text, chosen.text) >= 0.72 for chosen in merged):
                continue
            merged.append(item)
            if len(merged) >= top_k:
                break
        return merged

    @staticmethod
    def search_chunks(
        chunks: List[str],
        query: str,
        top_k: int = 3,
        requested_sections: Optional[set[str]] = None,
        evidence_chunks: Optional[List[EvidenceChunk]] = None,
    ) -> List[Tuple[str, float]]:
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

            max_score = max(scores) if max(scores) > 0 else 1
            ranked = []
            for i, score in enumerate(scores):
                normalized = float(score) / max_score
                section_boost = 0.0
                if evidence_chunks and requested_sections and i < len(evidence_chunks):
                    if evidence_chunks[i].section in requested_sections:
                        section_boost = 0.15
                ranked.append((chunks[i], round(min(1.0, normalized * 0.9 + section_boost), 3)))
            ranked.sort(key=lambda x: x[1], reverse=True)
            return PaperChunkService._suppress_redundant_chunk_texts(ranked, top_k=top_k)

        except ImportError:
            # 无 BM25 → 关键词简单匹配
            return PaperChunkService._fallback_search(chunks, query, top_k)

    @staticmethod
    def _chunk_tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{1,2}", (text or "").lower()))

    @classmethod
    def _chunk_similarity(cls, left: str, right: str) -> float:
        left_tokens = cls._chunk_tokens(left)
        right_tokens = cls._chunk_tokens(right)
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)

    @classmethod
    def _suppress_redundant_chunk_texts(cls, scored: List[Tuple[str, float]], top_k: int) -> List[Tuple[str, float]]:
        selected: List[Tuple[str, float]] = []
        deferred: List[Tuple[str, float]] = []
        for text, score in scored:
            if any(cls._chunk_similarity(text, chosen) >= 0.72 for chosen, _ in selected):
                deferred.append((text, score))
                continue
            selected.append((text, score))
            if len(selected) >= top_k:
                return selected
        selected.extend(deferred[:max(0, top_k - len(selected))])
        return selected[:top_k]

    @classmethod
    def _suppress_redundant_evidence(cls, chunks: List[EvidenceChunk], top_k: int) -> List[EvidenceChunk]:
        selected: List[EvidenceChunk] = []
        deferred: List[EvidenceChunk] = []
        for chunk in chunks:
            if any(cls._chunk_similarity(chunk.text, chosen.text) >= 0.72 for chosen in selected):
                deferred.append(chunk)
                continue
            selected.append(chunk)
            if len(selected) >= top_k:
                return selected
        selected.extend(deferred[:max(0, top_k - len(selected))])
        return selected[:top_k]

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
