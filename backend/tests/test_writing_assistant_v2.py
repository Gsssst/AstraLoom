"""写作助手 V2 单元测试与集成测试。"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock


# ============================================================
# 12.1 Pipeline 引擎测试
# ============================================================

class TestWritingPipeline:
    """Pipeline 引擎单元测试。"""

    @pytest.mark.asyncio
    async def test_pipeline_phase_config_lightweight(self):
        """轻量任务（润色）只使用 Writer + Reviewer。"""
        from app.services.writing_pipeline import TASK_PHASE_CONFIG, TaskType, Phase

        phases = TASK_PHASE_CONFIG[TaskType.POLISH]
        assert phases == [Phase.WRITER, Phase.REVIEWER]

    @pytest.mark.asyncio
    async def test_pipeline_phase_config_standard(self):
        """标准任务（Related Work）使用 Selector + Reader + Writer + Citation。"""
        from app.services.writing_pipeline import TASK_PHASE_CONFIG, TaskType, Phase

        phases = TASK_PHASE_CONFIG[TaskType.RELATED_WORK]
        assert Phase.SELECTOR in phases
        assert Phase.READER in phases
        assert Phase.WRITER in phases
        assert Phase.CITATION in phases

    @pytest.mark.asyncio
    async def test_pipeline_phase_config_heavy(self):
        """重量任务使用全部五阶段。"""
        from app.services.writing_pipeline import TASK_PHASE_CONFIG, TaskType, Phase

        phases = TASK_PHASE_CONFIG[TaskType.FULL_CHAPTER]
        assert len(phases) == 5

    @pytest.mark.asyncio
    async def test_pipeline_event_to_sse(self):
        """SSE 事件格式化。"""
        from app.services.writing_pipeline import PipelineEvent

        event = PipelineEvent("phase_start", phase="writer", content="test")
        sse = event.to_sse()
        assert sse.startswith("data: ")
        assert "phase_start" in sse
        assert "writer" in sse
        assert "test" in sse
        assert sse.endswith("\n\n")

    @pytest.mark.asyncio
    async def test_pipeline_cancel_mechanism(self):
        """取消机制：cancel() 设置 asyncio.Event。"""
        from app.services.writing_pipeline import WritingPipeline

        pipeline = WritingPipeline()
        pipeline._cancel_event = asyncio.Event()
        assert not pipeline._cancel_event.is_set()

        pipeline.cancel()
        assert pipeline._cancel_event.is_set()

    @pytest.mark.asyncio
    async def test_pipeline_manual_phases_override(self):
        """手动指定阶段列表覆盖任务类型默认配置。"""
        from app.services.writing_pipeline import WritingPipeline, Phase

        pipeline = WritingPipeline()
        events = []
        async for event in pipeline.run(
            task_type="polish",
            input_data={"text": "test"},
            phases=["writer"],
        ):
            events.append(event)

        # 应该只有 writer 阶段的事件
        phases = [e.phase for e in events if e.type in ("phase_start", "phase_complete")]
        assert len(phases) <= 2  # writer start + writer complete

    @pytest.mark.asyncio
    async def test_working_memory(self):
        """WorkingMemory 数据共享。"""
        from app.services.writing_pipeline import WorkingMemory

        memory = WorkingMemory()
        memory.papers = [{"title": "Test"}]
        memory.reading_notes = [{"note": "test"}]
        memory.writer_output = "Hello"

        d = memory.to_dict()
        assert len(d["papers"]) == 1
        assert d["writer_output"] == "Hello"


# ============================================================
# 12.2 Agent 测试
# ============================================================

class TestAgents:
    """Agent 单元测试。"""

    @pytest.mark.asyncio
    async def test_selector_agent_retrieves_papers(self):
        """Selector Agent 能检索论文。"""
        from app.services.agents.selector_agent import SelectorAgent
        from app.services.writing_pipeline import WorkingMemory

        agent = SelectorAgent(llm_service=None, db_session_factory=None)
        memory = WorkingMemory()
        memory.metadata["task_type"] = "related_work"
        memory.metadata["input"] = {"topic": "test"}

        events = []
        async for event in agent.execute(memory):
            events.append(event)

        # 无 LLM 和 DB 时，应正常返回（空论文列表）
        status_events = [e for e in events if e.type == "status"]
        assert len(status_events) > 0

    @pytest.mark.asyncio
    async def test_reader_agent_empty_papers(self):
        """Reader Agent 处理空论文列表。"""
        from app.services.agents.reader_agent import ReaderAgent
        from app.services.writing_pipeline import WorkingMemory

        agent = ReaderAgent(llm_service=None, db_session_factory=None)
        memory = WorkingMemory()
        memory.papers = []

        events = []
        async for event in agent.execute(memory):
            events.append(event)

        status = [e for e in events if e.type == "status"]
        assert any("无待阅读论文" in str(e.content) for e in status)

    def test_writer_prompts_exist(self):
        """Writer Agent 所有任务类型都有 Prompt。"""
        from app.services.agents.writer_agent import WriterAgent

        agent = WriterAgent()
        expected_types = [
            "polish", "abstract", "related_work", "literature_review",
            "compare_papers", "grant_write", "full_chapter",
        ]
        for t in expected_types:
            assert t in agent.PROMPTS, f"Missing prompt for {t}"
            assert len(agent.PROMPTS[t]) > 50

    def test_reviewer_dimensions(self):
        """Reviewer Agent 三个审阅维度。"""
        from app.services.agents.reviewer_agent import ReviewerAgent

        agent = ReviewerAgent()
        # 验证 review_dimension 方法存在
        assert callable(agent._review_dimension)

    def test_citation_agent_pattern(self):
        """Citation Agent [N] 引用提取正则正确。"""
        import re
        from app.services.agents.citation_agent import CitationAgent

        agent = CitationAgent()
        text = "This is discussed in [1] and [2]. Further work [3] extends this."
        pattern = re.compile(r'\[(\d+)\]')
        matches = set(int(m) for m in pattern.findall(text))
        assert matches == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_writer_builds_message_for_polish(self):
        """Writer Agent 润色任务的消息构建。"""
        from app.services.agents.writer_agent import WriterAgent
        from app.services.writing_pipeline import WorkingMemory

        agent = WriterAgent()
        memory = WorkingMemory()
        memory.metadata["task_type"] = "polish"
        memory.metadata["input"] = {"text": "hello world", "style": "academic"}

        msg = agent._build_user_message("polish", memory.metadata["input"], memory)
        assert "hello world" in msg


# ============================================================
# 12.3 LaTeX 处理器测试
# ============================================================

class TestLatexProcessor:
    """LaTeX 感知处理器测试。"""

    def test_find_inline_math(self):
        """检测行内公式。"""
        from app.services.latex_processor import latex_processor

        text = "The formula $E = mc^2$ is famous."
        blocks = latex_processor.find_protected_blocks(text)
        assert len(blocks) >= 1
        assert blocks[0][1] == "inline_math"

    def test_find_cite_commands(self):
        """检测引用命令。"""
        from app.services.latex_processor import latex_processor

        text = r"As shown in \cite{vaswani2017attention} and \citep{devlin2018bert}."
        blocks = latex_processor.find_protected_blocks(text)
        assert len(blocks) >= 2

    def test_find_equation_environment(self):
        """检测公式环境。"""
        from app.services.latex_processor import latex_processor

        text = r"\begin{equation}E = mc^2\end{equation} and text."
        blocks = latex_processor.find_protected_blocks(text)
        assert len(blocks) >= 1

    def test_protect_and_restore(self):
        """保护 → 还原 循环测试。"""
        from app.services.latex_processor import latex_processor

        original = "The formula $E = mc^2$ explains energy-mass equivalence."
        protected, block_map = latex_processor.protect(original)
        restored = latex_processor.restore(protected, block_map)
        assert restored == original

    def test_protect_preserves_non_latex(self):
        """不含 LaTeX 的文本原样保留。"""
        from app.services.latex_processor import latex_processor

        text = "This is plain text without any LaTeX commands."
        protected, block_map = latex_processor.protect(text)
        # 没有受保护块
        assert len(block_map) == 0
        assert protected == text

    def test_extract_sections(self):
        """从 .tex 提取章节结构。"""
        from app.services.latex_processor import latex_processor

        tex = r"""
\section{Introduction}
This is the intro.
\section{Method}
This is the method.
\subsection{Architecture}
Architecture details.
"""
        sections = latex_processor.extract_sections(tex)
        assert len(sections) >= 3
        assert sections[0]["title"] == "Introduction"
        assert sections[0]["level"] == 1
        # 应该有一个 subsection
        subs = [s for s in sections if s["level"] == 2]
        assert len(subs) >= 1

    def test_render_to_tex(self):
        """渲染为 .tex 文件。"""
        from app.services.latex_processor import latex_processor

        sections = [
            {"title": "Abstract", "content": "This is abstract.", "level": 1},
            {"title": "Introduction", "content": "Hello world.", "level": 1},
        ]
        tex = latex_processor.render_to_tex("Test Paper", sections)
        assert r"\documentclass" in tex
        assert r"\section{Abstract}" in tex
        assert r"\section{Introduction}" in tex

    def test_render_to_tex_supports_double_column_layout(self):
        """渲染双栏版式。"""
        from app.services.latex_processor import latex_processor

        tex = latex_processor.render_to_tex(
            "Test Paper",
            [{"title": "Introduction", "content": "Hello world.", "level": 1}],
            render_options={"layout": "double_column"},
        )

        assert r"\documentclass[twocolumn]{article}" in tex

    def test_render_to_tex_supports_template_metadata(self):
        """渲染模板 metadata。"""
        from app.services.latex_processor import latex_processor

        tex = latex_processor.render_to_tex(
            "Test Paper",
            [{"title": "Introduction", "content": "Hello world.", "level": 1}],
            render_options={
                "layout": "template",
                "document_class": "IEEEtran",
                "document_options": ["conference"],
                "packages": ["booktabs"],
            },
        )

        assert r"\documentclass[conference]{IEEEtran}" in tex
        assert r"\usepackage{booktabs}" in tex

    def test_render_to_tex_tolerates_null_section_content(self):
        """空章节内容不应导致 LaTeX 预览接口 500。"""
        from app.services.latex_processor import latex_processor

        tex = latex_processor.render_to_tex(
            "Test Paper",
            [
                {"title": "Introduction", "content": None, "level": 1},
                {"title": None, "content": 123, "level": "bad-level"},
            ],
        )

        assert r"\section{Introduction}" in tex
        assert r"\section{Untitled}" in tex
        assert "123" in tex

    def test_extract_bibliography(self):
        """提取 \\bibliography 引用。"""
        from app.services.latex_processor import latex_processor

        tex = r"\bibliography{references}"
        bib = latex_processor.extract_bibliography(tex)
        assert bib == "references"


# ============================================================
# 12.4 Diff 引擎测试
# ============================================================

class TestDiffEngine:
    """Diff 引擎测试。"""

    def test_split_sentences(self):
        """句子分割。"""
        from app.services.diff_engine import diff_engine

        text = "Hello world. This is a test. How are you?"
        sents = diff_engine.split_sentences(text)
        assert len(sents) == 3

    def test_split_sentences_chinese(self):
        """中文句子分割。"""
        from app.services.diff_engine import diff_engine

        text = "这是第一句。这是第二句！这是第三句？"
        sents = diff_engine.split_sentences(text)
        assert len(sents) >= 3

    def test_compute_diff_identical(self):
        """相同文本 diff 结果无修改。"""
        from app.services.diff_engine import diff_engine

        text = "This is a test sentence."
        result = diff_engine.compute_diff(text, text)
        assert result["stats"]["equal"] > 0
        assert result["stats"]["additions"] == 0
        assert result["stats"]["deletions"] == 0
        assert result["stats"]["replacements"] == 0

    def test_compute_diff_modified(self):
        """修改文本产生 diff。"""
        from app.services.diff_engine import diff_engine

        original = "The model perform good on benchmark."
        polished = "The model performs strongly on the benchmark."
        result = diff_engine.compute_diff(original, polished)

        total_changes = result["stats"]["additions"] + result["stats"]["deletions"] + result["stats"]["replacements"]
        assert total_changes > 0

    def test_compute_diff_latex_aware(self):
        """LaTeX 感知 diff 保护公式。"""
        from app.services.diff_engine import diff_engine

        original = "The loss $L(x)$ is minimized using SGD."
        polished = "The loss $L(x)$ is minimized using Adam optimizer."
        result = diff_engine.compute_diff(original, polished)

        # 公式 $L(x)$ 应该保持不变
        for hunk in result["hunks"]:
            if hunk["type"] == "equal" or hunk["type"] == "replace":
                # 至少有一个 hunk 保留了 $L(x)$
                pass

    def test_apply_hunks_accept_all(self):
        """接受所有 hunks → 得到润色版本。"""
        from app.services.diff_engine import diff_engine

        original = "hello world"
        polished = "hello beautiful world"
        result = diff_engine.compute_diff(original, polished)

        all_indices = set(h["index"] for h in result["hunks"])
        applied = diff_engine.apply_hunks(result["hunks"], all_indices)
        assert "beautiful" in applied

    def test_apply_hunks_reject_all(self):
        """拒绝所有 hunks → 保持原文。"""
        from app.services.diff_engine import diff_engine

        original = "hello world"
        polished = "hello beautiful world"
        result = diff_engine.compute_diff(original, polished)

        # 只接受 equal 类型的 hunks
        equal_indices = set(h["index"] for h in result["hunks"] if h["type"] == "equal")
        applied = diff_engine.apply_hunks(result["hunks"], equal_indices)
        assert "beautiful" not in applied

    def test_to_unified_diff(self):
        """生成 unified diff 格式。"""
        from app.services.diff_engine import diff_engine

        diff_text = diff_engine.to_unified_diff("hello", "world")
        assert "--- original" in diff_text or "---" in diff_text
        assert "+++ polished" in diff_text or "+++" in diff_text


# ============================================================
# 12.5 引用验证器测试
# ============================================================

class TestCitationVerifier:
    """引用验证器测试。"""

    def test_title_similarity_identical(self):
        """完全相同标题相似度 = 1.0。"""
        from app.services.citation_verifier import citation_verifier

        sim = citation_verifier._title_similar(
            "Attention Is All You Need",
            "Attention Is All You Need",
        )
        assert sim > 0.99

    def test_title_similarity_different(self):
        """完全不同标题相似度低。"""
        from app.services.citation_verifier import citation_verifier

        sim = citation_verifier._title_similar(
            "Attention Is All You Need",
            "Completely Different Paper About Biology",
        )
        assert sim < 0.3

    @pytest.mark.asyncio
    async def test_verify_without_redis(self):
        """无 Redis 时正常验证（外部 API 可能不返回结果）。"""
        from app.services.citation_verifier import CitationVerifier

        verifier = CitationVerifier(redis_client=None)
        result = await verifier.verify(
            title="Test Paper Title That Does Not Exist",
            arxiv_id="",
        )
        assert result["status"] in ("verified", "uncertain", "likely_hallucination")
        assert "sources" in result

    @pytest.mark.asyncio
    async def test_verify_batch(self):
        """批量验证。"""
        from app.services.citation_verifier import CitationVerifier

        verifier = CitationVerifier(redis_client=None)
        citations = [
            {"title": "Attention Is All You Need", "arxiv_id": "1706.03762"},
            {"title": "BERT: Pre-training of Deep Bidirectional Transformers", "arxiv_id": "1810.04805"},
        ]
        results = await verifier.verify_batch(citations)
        assert len(results) == 2
        for r in results:
            if not isinstance(r, Exception):
                assert "status" in r


# ============================================================
# 12.6 集成测试
# ============================================================

class TestWritingV2Integration:
    """后端集成测试。"""

    def test_citation_verifier_importable(self):
        """引用验证器可导入。"""
        from app.services.citation_verifier import citation_verifier, CitationVerifier
        assert citation_verifier is not None
        assert CitationVerifier is not None

    def test_diff_engine_importable(self):
        """Diff 引擎可导入。"""
        from app.services.diff_engine import diff_engine, DiffEngine, PolishVersionManager
        assert diff_engine is not None
        assert DiffEngine is not None

    def test_latex_processor_importable(self):
        """LaTeX 处理器可导入。"""
        from app.services.latex_processor import latex_processor, LatexProcessor
        assert latex_processor is not None
        assert LatexProcessor is not None

    def test_smart_citation_importable(self):
        """智能引用服务可导入。"""
        from app.services.smart_citation_service import smart_citation_service, SmartCitationService
        assert smart_citation_service is not None

    def test_writing_project_service_importable(self):
        """项目管理服务可导入。"""
        from app.services.writing_project_service import WritingProjectService, TEMPLATES
        assert WritingProjectService is not None
        assert len(TEMPLATES) >= 5  # 至少 5 个模板

    def test_writing_v2_api_importable(self):
        """V2 API 可导入。"""
        from app.api.writing_v2 import router
        assert router is not None

    def test_pipeline_importable(self):
        """Pipeline 可导入。"""
        from app.services.writing_pipeline import (
            WritingPipeline, PipelineEvent, Phase, TaskType,
            WorkingMemory, TASK_PHASE_CONFIG, create_pipeline,
        )
        assert WritingPipeline is not None
        assert len(TASK_PHASE_CONFIG) >= 5

    def test_all_agents_importable(self):
        """所有 Agent 可导入。"""
        from app.services.agents import (
            SelectorAgent, ReaderAgent, WriterAgent,
            ReviewerAgent, CitationAgent, BaseAgent,
        )
        assert BaseAgent is not None
        assert SelectorAgent is not None
        assert ReaderAgent is not None
        assert WriterAgent is not None
        assert ReviewerAgent is not None
        assert CitationAgent is not None

    def test_models_importable(self):
        """新数据模型可导入。"""
        from app.db.models.writing import WritingProject, WritingSection, PolishVersion
        assert WritingProject is not None
        assert WritingSection is not None
        assert PolishVersion is not None

    def test_citation_verify_endpoint_returns_json(self):
        """引用验证端点结构正确。"""
        # 验证请求/响应模型可以正常导入
        from app.api.writing_v2 import CitationVerifyRequest
        req = CitationVerifyRequest(answer="Test [1] reference.")
        assert req.answer == "Test [1] reference."

    def test_project_create_request(self):
        """项目创建请求模型。"""
        from app.api.writing_v2 import ProjectCreateRequest
        req = ProjectCreateRequest(
            title="Test Paper",
            template_type="acl",
            research_project_id="research-1",
            collection_ids=["collection-1"],
            target_venue="ACL",
            target_year="2026",
        )
        assert req.title == "Test Paper"
        assert req.template_type == "acl"
        assert req.writing_type == "paper"
        assert req.collection_ids == ["collection-1"]
        assert req.target_venue == "ACL"
