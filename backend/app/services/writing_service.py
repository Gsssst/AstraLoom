"""论文写作辅助服务。"""

import logging
import re
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm import llm_service
from app.services.rag_service import RAGService
from app.db.models.paper import Paper

logger = logging.getLogger(__name__)


class WritingAssistantService:
    """论文写作辅助服务。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    _ROLE_LABELS = {
        "supporting_evidence": "支持证据",
        "counterexample": "反例/局限",
        "baseline_method": "基线方法",
        "background": "背景资料",
    }

    _ROLE_REASONS = {
        "supporting_evidence": "该论文与当前表述的核心术语和研究问题相近，适合作为正向依据。",
        "counterexample": "当前表述包含局限、失败或反向比较语义，该论文适合作为反例或问题来源。",
        "baseline_method": "当前表述涉及 baseline、benchmark、SOTA 或对比实验，该论文适合作为基线方法引用。",
        "background": "当前表述偏领域背景或问题定义，该论文适合作为背景资料引用。",
    }

    _STOPWORDS = {
        "the", "and", "for", "with", "that", "this", "from", "into", "about",
        "are", "was", "were", "have", "has", "had", "can", "will", "shall",
        "large", "model", "models", "paper", "method", "methods", "research",
        "论文", "方法", "模型", "研究", "工作", "本文", "可以", "需要", "介绍",
    }

    def _tokenize(self, text: str) -> set[str]:
        tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_\-]{1,}|[\u4e00-\u9fff]{2,}", (text or "").lower())
        return {t for t in tokens if t not in self._STOPWORDS and len(t) > 1}

    def classify_citation_role(self, text: str, paper: Paper | None = None) -> dict:
        """判断一条推荐引用在写作中更适合扮演什么角色。"""
        normalized = (text or "").lower()
        if re.search(r"baseline|benchmark|sota|state-of-the-art|compare|comparison|对比|基线|实验比较|性能", normalized):
            role = "baseline_method"
        elif re.search(r"limitation|fail|failure|negative|contradict|weakness|不足|局限|失败|反例|无法|缺陷", normalized):
            role = "counterexample"
        elif re.search(r"background|survey|overview|motivation|problem|背景|综述|领域|问题定义|动机", normalized):
            role = "background"
        else:
            role = "supporting_evidence"

        return {
            "role": role,
            "role_label": self._ROLE_LABELS[role],
            "role_reason": self._ROLE_REASONS[role],
        }

    def score_sentence_paper_match(self, sentence: str, paper: Paper) -> dict:
        """用轻量词项重叠估计句子和论文是否匹配。"""
        sentence_tokens = self._tokenize(sentence)
        evidence_text = " ".join([
            paper.title or "",
            paper.abstract or "",
            " ".join(paper.tags or []),
        ])
        paper_tokens = self._tokenize(evidence_text)

        if not sentence_tokens or not paper_tokens:
            score = 0.0
            overlap = []
        else:
            overlap = sorted(sentence_tokens & paper_tokens)
            precision = len(overlap) / max(len(sentence_tokens), 1)
            recall = len(overlap) / max(min(len(paper_tokens), len(sentence_tokens) + 8), 1)
            score = round((precision * 0.7) + (recall * 0.3), 4)

        if score >= 0.35:
            status = "strong"
            label = "强匹配"
            explanation = "句子和论文标题/摘要存在较充分的术语重合，可作为较可信引用候选。"
        elif score >= 0.16:
            status = "partial"
            label = "部分匹配"
            explanation = "句子和论文有部分术语重合，建议人工确认具体结论是否被论文支持。"
        else:
            status = "weak"
            label = "弱匹配"
            explanation = "句子和论文证据重合较少，不建议直接作为该句引用。"

        return {
            "match_score": score,
            "match_status": status,
            "match_label": label,
            "match_terms": overlap[:8],
            "match_explanation": explanation,
        }

    def build_citation_decision(self, role_info: dict, match_info: dict) -> dict:
        """把引用角色和匹配质量转成写作动作建议。"""
        role = role_info.get("role") or "supporting_evidence"
        match_status = match_info.get("match_status") or "weak"

        role_action = {
            "supporting_evidence": "可用于支撑当前论断",
            "counterexample": "适合放在局限、反例或问题动机中",
            "baseline_method": "适合放在实验对比或基线方法说明中",
            "background": "适合放在背景、问题定义或相关工作铺垫中",
        }.get(role, "可作为候选引用")

        if match_status == "strong":
            confidence = "high"
            warning = "匹配较强，仍建议在正式投稿前核对原文页码和具体结论。"
            action = role_action
        elif match_status == "partial":
            confidence = "medium"
            warning = "只有部分术语匹配，建议补充原文片段或换成更直接支持该句的证据。"
            action = f"{role_action}，但需要人工确认"
        else:
            confidence = "low"
            warning = "匹配较弱，不建议直接引用来支撑该句。请替换引用、补全文检索或改写句子。"
            action = "谨慎使用：先补证据或替换引用"

        return {
            "decision_label": f"{role_info.get('role_label', '候选引用')} · {match_info.get('match_label', '待确认')}",
            "decision_action": action,
            "decision_warning": warning,
            "decision_confidence": confidence,
        }

    async def retrieve_topic_papers(self, topic: str, max_papers: int = 8) -> list[tuple[Paper, float]]:
        """检索写作主题相关论文。"""
        rag = RAGService(self.session)
        return await rag.search_similar(topic, top_k=max_papers)

    async def recommend_citations(
        self,
        text: str,
        top_k: int = 5,
    ) -> list[dict]:
        """根据写作内容推荐引用论文。"""
        results = await self.retrieve_topic_papers(text, max_papers=top_k)

        recommendations = []
        for p, score in results:
            role_info = self.classify_citation_role(text, p)
            match_info = self.score_sentence_paper_match(text, p)
            decision_info = self.build_citation_decision(role_info, match_info)
            recommendations.append({
                "paper_id": str(p.id),
                "title": p.title,
                "authors": ", ".join(p.authors[:5]) if isinstance(p.authors, list) else str(p.authors),
                "year": p.year,
                "arxiv_id": p.arxiv_id,
                "doi": p.doi,
                "abstract_snippet": p.abstract[:200] if p.abstract else "",
                "similarity": round(score, 4),
                "bibtex": self._generate_bibtex(p),
                **role_info,
                **match_info,
                **decision_info,
            })
        return recommendations

    async def generate_related_work_table(
        self,
        topic: str,
        max_papers: int = 8,
    ) -> dict:
        """生成 Related Work 对比表。"""
        results = await self.retrieve_topic_papers(topic, max_papers=max_papers)
        rows = []
        for index, (paper, score) in enumerate(results, start=1):
            role_info = self.classify_citation_role(topic, paper)
            abstract = (paper.abstract or "").strip()
            contribution = abstract[:160] + ("..." if len(abstract) > 160 else "")
            compare_point = self._infer_comparison_point(abstract)
            rows.append({
                "index": index,
                "paper_id": str(paper.id),
                "title": paper.title,
                "year": paper.year,
                "authors": ", ".join(paper.authors[:3]) if isinstance(paper.authors, list) else str(paper.authors or ""),
                "contribution": contribution or "摘要不足，建议补全文或补摘要后再生成精细对比。",
                "role": role_info["role"],
                "role_label": role_info["role_label"],
                "comparison_point": compare_point,
                "similarity": round(score, 4),
            })

        header = "| # | 论文 | 年份 | 方法/贡献 | 证据角色 | 可对比点 |\n|---|---|---:|---|---|---|"
        body = "\n".join(
            f"| {r['index']} | [{r['title']}](#/papers/{r['paper_id']}) | {r['year'] or 'N/A'} | {self._escape_table_cell(r['contribution'])} | {r['role_label']} | {self._escape_table_cell(r['comparison_point'])} |"
            for r in rows
        )
        markdown = header if not rows else f"{header}\n{body}"
        return {
            "topic": topic,
            "total_papers": len(rows),
            "rows": rows,
            "markdown": markdown,
            "coverage_note": "已基于本地知识库生成；若论文较少或摘要不足，建议先补全文/补向量后再生成最终稿。",
        }

    def _infer_comparison_point(self, abstract: str) -> str:
        text = (abstract or "").lower()
        if not text:
            return "缺少摘要，无法判断对比点。"
        if re.search(r"dataset|benchmark|evaluation|experiment|数据集|基准|实验", text):
            return "适合在实验设置、数据集或评测指标上对比。"
        if re.search(r"efficient|latency|cost|token|速度|效率|开销", text):
            return "适合在效率、计算开销或 token 使用上对比。"
        if re.search(r"framework|architecture|network|model|框架|架构|网络", text):
            return "适合在模型结构或方法路线中对比。"
        return "适合围绕研究问题、方法假设和适用场景对比。"

    def _escape_table_cell(self, value: str) -> str:
        return (value or "").replace("\n", " ").replace("|", "\\|")

    def _generate_bibtex(self, paper: Paper) -> str:
        """为论文生成 BibTeX 条目。"""
        arxiv_id = paper.arxiv_id or ""
        # 使用 arXiv ID 的最后部分作为 citation key
        key = arxiv_id.replace("/", "").replace(".", "_") if arxiv_id else f"ref_{str(paper.id)[:8]}"

        authors = paper.authors
        if isinstance(authors, list) and authors:
            first_author = authors[0].split()[-1] if authors else "Unknown"
        else:
            first_author = str(authors).split()[-1] if authors else "Unknown"

        year = paper.year or 2024
        key = f"{first_author.lower()}{year}_{arxiv_id.split('.')[0] if arxiv_id else key}"

        primary_class = "cs.AI"
        if paper.categories:
            first_category = paper.categories[0]
            primary_class = getattr(first_category, "name", str(first_category)) or primary_class

        bibtex = f"""@article{{{key},
  title = {{{{{paper.title}}}}},
  author = {{{{{', '.join(authors) if isinstance(authors, list) else authors or 'Unknown'}}}}},
  year = {{{{{paper.year or 'N/A'}}}}},
  journal = {{arXiv preprint}},
  archivePrefix = {{arXiv}},
  eprint = {{{{{arxiv_id}}}}},
  primaryClass = {{{{{primary_class}}}}}
}}"""
        return bibtex

    async def generate_related_work(
        self,
        research_topic: str,
        max_papers: int = 5,
        language: str = "chinese",
    ) -> str:
        """基于知识库生成 Related Work 段落（参考 ScholarCopilot + STORM 策略）。"""
        rag = RAGService(self.session)
        results = await rag.search_similar(research_topic, top_k=max_papers)

        if not results:
            return "知识库中暂无相关论文，请先入库该方向的论文。"

        # 确保有全文
        from app.services.report_service import ensure_full_text
        for p, _ in results:
            try:
                await ensure_full_text(p)
            except Exception:
                pass

        # 控制每篇论文信息长度，避免 prompt 过长导致 token 不足
        papers_info = "\n\n".join([
            f"### [{i+1}] {p.title} ({p.year})\n"
            f"**作者**: {', '.join(p.authors[:3]) if isinstance(p.authors, list) else str(p.authors)[:200]}\n"
            f"**摘要**: {p.abstract[:300] if p.abstract else 'N/A'}\n"
            f"**全文参考**: {p.full_text[:800] if p.full_text else ''}"
            for i, (p, _) in enumerate(results)
        ])

        lang = "中文" if language == "chinese" else "English"
        prompt = f"""## 角色
你是一位担任 NeurIPS/ICLR/ACL 审稿人的资深研究员，擅长撰写高质量 Related Work 章节。

## 任务
为以下研究方向撰写规范的 Related Work 章节，用{lang}撰写。

## 研究主题
{research_topic}

## 可引用论文（含全文信息）
{papers_info}

## 写作规范（参考顶会论文风格）
1. **主题分组**：按技术路线将论文分为 2-3 个主题组，每组 1-2 段
2. **每篇论文的写法**：简述其核心方法 + 与本研究的关系/区别，不是简单罗列标题
3. **Research Gap**：在每组末尾或全文末尾，明确指出已有工作的不足，自然过渡到本研究的创新点
4. **引用格式**：严格使用 `[1]` `[2]` 等编号，每篇论文至少引用一次
5. **字数**：300-600 字，学术简洁，避免冗余
6. **语言风格**：客观、准确，避免"非常"、"十分"等主观词

## 输出格式示例
```
### 方法A及其变体

早期工作 [1] 提出了 XXX 方法... 然而该方法存在 YYY 局限... 后续 [2] 改进了...

### 方法B及相关方向

另一类工作 [3] 从不同角度... 但 [3] 未考虑 ZZZ 问题...

综上所述，现有工作主要存在以下不足：（1）... （2）... 本文针对这些问题提出...
```

请严格按照以上规范撰写。
"""
        try:
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=8192,  # 推理模型需要更多 token，V4 Pro 的思考过程消耗 token
            )
            if not response or not response.strip():
                return "⚠️ 模型未能生成有效内容。可能原因：论文全文过长导致上下文溢出。请尝试减少论文数量或入库更多相关论文后重试。"
            return response
        except Exception as e:
            logger.error(f"Related Work 生成失败: {e}")
            raise

    async def polish_text(
        self,
        text: str,
        style: str = "academic",
    ) -> str:
        """润色学术文本（参考 gpt_academic 润色模板）。"""
        style_configs = {
            "academic": {
                "role": "你是 Nature Communications 的资深语言编辑，专门润色非英语母语研究者的学术论文。",
                "instruction": "将以下文本润色为正式学术风格。保持原意和技术术语不变。",
                "rules": [
                    "将口语化表达改为学术书面语",
                    "修正语法错误和不自然的表达",
                    "确保主谓一致和时态正确",
                    "技术术语和专有名词保持原样",
                    "不要改变引用格式 \\cite{{}} 和数学公式",
                ],
            },
            "concise": {
                "role": "你是一位擅长精简文字的科学编辑。",
                "instruction": "精简以下文本，删除冗余表达，使每个句子都传达有价值的信息。",
                "rules": [
                    "删除重复表述和废话",
                    "将长句拆分为简洁短句",
                    "保持核心信息和技术细节不变",
                    "字数减少 20-30%",
                ],
            },
            "fluent": {
                "role": "你是一位帮助研究者改善论文可读性的写作教练。",
                "instruction": "改善以下文本的流畅性和可读性。",
                "rules": [
                    "改善句子间的逻辑衔接",
                    "使用过渡词增强连贯性",
                    "避免连续多个长句",
                    "保持学术语气不变",
                ],
            },
            "english": {
                "role": "你是一位专业的学术论文中译英翻译专家。",
                "instruction": "将以下中文文本翻译为学术英语。",
                "rules": [
                    "使用地道的学术英语表达",
                    "保持专业术语准确",
                    "避免中式英语（Chinglish）",
                    "确保语法正确、表达自然",
                ],
            },
        }

        config = style_configs.get(style, style_configs["academic"])
        rules_text = "\n".join(f"- {r}" for r in config["rules"])

        prompt = f"""## 角色
{config['role']}

## 指令
{config['instruction']}

## 规则
{rules_text}

## 原文
{text}

## 输出
直接输出润色后的文本，不要任何解释性文字，不要加前缀或后缀说明。
"""
        response = await llm_service.chat(
            messages=[{"role": "system", "content": config["role"]},
                      {"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=8192,
        )
        return response

    async def generate_abstract(
        self,
        title: str,
        key_points: str,
        language: str = "chinese",
    ) -> str:
        """生成论文摘要（参考顶会摘要结构）。"""
        lang = "中文" if language == "chinese" else "English"
        prompt = f"""## 角色
你是一位经验丰富的学术论文作者，擅长撰写符合 NeurIPS/ICML/ACL 标准的论文摘要。

## 任务
为以下论文撰写规范的{lang}摘要。

## 论文标题
{title}

## 关键要点
{key_points}

## 摘要结构（严格遵循）
1. **背景与问题**（1-2 句）：简述研究领域和核心挑战
2. **方法概述**（2-3 句）：简要说明提出的方法/模型/框架
3. **关键结果**（1-2 句）：在什么数据集上、相比 baseline 提升了多少
4. **意义**（1 句）：对领域的贡献或潜在影响

## 要求
- 总字数 180-280 字，简洁有力
- 不引用参考文献（摘要中不出现 \\cite{{}}）
- 不出现「本文」「我们」等视角切换（统一用「本文」或第三人称）
- 数字和百分比用阿拉伯数字

## {lang}摘要参考范例
{{
    "chinese": "大语言模型在...方面取得了显著进展。然而，现有方法在...方面仍存在不足。本文提出了一种...方法，通过...机制来解决...问题。在XX基准测试上，本文方法相比SOTA提升了XX%，证明了...的有效性。",
    "english": "Large language models have shown remarkable capabilities in... However, existing approaches still struggle with... We propose a novel method that... Extensive experiments on XX benchmark demonstrate that our approach outperforms SOTA by XX%..."
}}["{language}"]

## 输出
直接输出摘要文本，不要任何解释。
"""
        response = await llm_service.chat(
            messages=[{"role": "system", "content": "你是一位顶会论文作者，擅长撰写高质量摘要。"},
                      {"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4096,
        )
        return response

    async def generate_literature_review(
        self,
        topic: str,
        language: str = "chinese",
        max_papers: int = 10,
    ) -> dict:
        """生成完整文献综述，含结构化章节、对比表格、研究 gap。"""
        rag = RAGService(self.session)
        results = await rag.search_similar(topic, top_k=max_papers)

        if not results:
            return {"error": "知识库中暂无相关论文"}

        # 收集论文信息
        papers_info = []
        for i, (p, score) in enumerate(results):
            papers_info.append({
                "id": str(p.id),
                "index": i + 1,
                "title": p.title,
                "authors": ", ".join(p.authors[:5]) if isinstance(p.authors, list) else str(p.authors),
                "year": p.year,
                "abstract": p.abstract[:400] if p.abstract else "",
                "tags": p.tags or [],
                "similarity": round(score, 4),
            })

        papers_text = "\n\n".join([
            f"[{pi['index']}] {pi['title']} ({pi['year']})\n"
            f"作者: {pi['authors']}\n"
            f"摘要: {pi['abstract']}\n"
            f"标签: {', '.join(pi['tags'][:5])}"
            for pi in papers_info
        ])

        lang_instr = "中文" if language == "chinese" else "English"
        prompt = f"""你是一位资深学术研究者。请基于以下论文，撰写一篇关于「{topic}」的完整文献综述。

## 可用论文
{papers_text}

## 要求（用{lang_instr}撰写）
1. **引言** (100-150字)：该领域的背景和重要性
2. **核心方法分类** (200-300字)：按技术路线分类介绍各论文的方法，如分为不同流派
3. **关键论文详述** (200-300字)：选2-3篇最重要的论文详细介绍
4. **对比分析表格**：用 Markdown 表格对比各论文的方法、数据集、性能指标
5. **研究趋势与Gap** (100-150字)：总结当前趋势和未解决的问题
6. **结论** (50-100字)

请使用学术规范引用格式 [1][2] 等标注。
"""
        response = await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4096,
        )
        return {
            "content": response,
            "papers": papers_info,
            "total_papers": len(papers_info),
        }

    async def compare_papers(
        self,
        paper_ids: list[str],
    ) -> str:
        """对比分析多篇论文。"""
        from uuid import UUID
        from sqlalchemy import select

        papers = []
        for pid in paper_ids:
            try:
                result = await self.session.execute(select(Paper).where(Paper.id == UUID(pid)))
                p = result.scalar_one_or_none()
                if p:
                    papers.append(p)
            except Exception:
                continue

        if len(papers) < 2:
            return "至少需要 2 篇论文进行对比"

        papers_text = "\n\n".join([
            f"[{i+1}] {p.title} ({p.year})\n"
            f"摘要: {p.abstract[:300] if p.abstract else 'N/A'}"
            for i, p in enumerate(papers)
        ])

        prompt = f"""请对比分析以下 {len(papers)} 篇论文，用 Markdown 表格输出对比结果：

{papers_text}

请生成以下内容的对比表格：
1. 研究问题
2. 核心方法
3. 使用的数据集
4. 主要实验结果/性能
5. 优势
6. 局限性

最后给出总结性评述（100字内）：哪篇工作最值得跟进？为什么？
"""
        return await llm_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=8192,
        )

    async def export_bibtex(self, paper_ids: list[str]) -> str:
        """导出多篇论文的 BibTeX。"""
        from uuid import UUID
        from sqlalchemy import select

        bibtex_entries = []
        for pid in paper_ids:
            try:
                result = await self.session.execute(
                    select(Paper).where(Paper.id == UUID(pid))
                )
                paper = result.scalar_one_or_none()
                if paper:
                    bibtex_entries.append(self._generate_bibtex(paper))
            except (ValueError, Exception) as e:
                logger.warning(f"BibTeX 导出跳过 {pid}: {e}")

        return "\n\n".join(bibtex_entries)
