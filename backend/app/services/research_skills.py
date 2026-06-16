"""Built-in declarative research skills for chat tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.services.llm import llm_service


SKILL_CONTEXT_MAX_CHARS = 7000
SKILL_OUTPUT_MAX_CHARS = 8000


class ResearchSkillNotFoundError(ValueError):
    def __init__(self, skill_id: str, available_skill_ids: list[str]):
        super().__init__(f"Unknown research skill: {skill_id}")
        self.skill_id = skill_id
        self.available_skill_ids = available_skill_ids


@dataclass(frozen=True)
class ResearchSkill:
    id: str
    label: str
    description: str
    allowed_tool_hints: tuple[str, ...]
    output_format: str
    evaluation_criteria: tuple[str, ...]
    instructions: str

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "allowed_tool_hints": list(self.allowed_tool_hints),
            "output_format": self.output_format,
            "evaluation_criteria": list(self.evaluation_criteria),
        }


@dataclass(frozen=True)
class ResearchSkillRunResult:
    skill: ResearchSkill
    task: str
    output: str
    context_used_chars: int

    def metadata(self) -> dict[str, Any]:
        return {
            **self.skill.metadata(),
            "task": self.task,
            "context_used_chars": self.context_used_chars,
            "output_length": len(self.output),
        }


BUILT_IN_RESEARCH_SKILLS: tuple[ResearchSkill, ...] = (
    ResearchSkill(
        id="paper-scout",
        label="论文侦察",
        description="Turn a research topic into a shortlist strategy, ranking criteria, and reading order.",
        allowed_tool_hints=("search_papers", "search_library", "import_paper"),
        output_format="候选主题拆解、筛选标准、推荐优先级、风险提示、下一步检索式",
        evaluation_criteria=("相关性", "新颖性", "可复现性", "证据覆盖", "风险透明度"),
        instructions=(
            "Analyze the topic as a paper-scouting task. Clarify the search facets, propose ranking criteria, "
            "identify likely evidence gaps, and produce an actionable reading shortlist plan."
        ),
    ),
    ResearchSkill(
        id="method-comparison",
        label="方法对比",
        description="Compare methods by assumptions, inputs, architecture, supervision, compute, and failure modes.",
        allowed_tool_hints=("search_library", "read_pdf"),
        output_format="对比维度表、关键差异、适用场景、实验验证建议",
        evaluation_criteria=("公平对比", "机制解释", "实验可验证性", "局限识别"),
        instructions=(
            "Compare methods structurally. Separate mechanism, assumptions, required data, evaluation setup, "
            "strengths, weaknesses, and experiments that could distinguish them."
        ),
    ),
    ResearchSkill(
        id="experiment-planner",
        label="实验设计",
        description="Convert a research idea into hypotheses, baselines, ablations, datasets, metrics, and risks.",
        allowed_tool_hints=("search_library", "read_pdf"),
        output_format="假设、实验矩阵、baseline、消融、指标、资源和风险",
        evaluation_criteria=("可执行性", "对照充分性", "指标合理性", "资源约束", "失败预案"),
        instructions=(
            "Design experiments for a research idea. Include hypotheses, baselines, ablations, datasets, metrics, "
            "minimum viable experiment, expected outcomes, and failure checks."
        ),
    ),
    ResearchSkill(
        id="survey-writer",
        label="综述草稿",
        description="Organize a topic into a survey outline with taxonomy, representative papers, and open problems.",
        allowed_tool_hints=("search_papers", "search_library", "read_pdf"),
        output_format="综述大纲、分类体系、代表工作、争议点、开放问题",
        evaluation_criteria=("结构完整性", "分类清晰度", "代表性", "证据引用计划", "研究空白"),
        instructions=(
            "Draft a survey structure. Build a taxonomy, map representative work to categories, identify trends, "
            "contradictions, and open problems."
        ),
    ),
    ResearchSkill(
        id="figure-interpreter",
        label="图表解读",
        description="Interpret figures or tables by extracting claims, evidence, caveats, and follow-up questions.",
        allowed_tool_hints=("read_pdf", "extract_docx", "extract_pptx"),
        output_format="图表主张、证据链、注意事项、可复核问题",
        evaluation_criteria=("证据忠实度", "不臆测", "量化细节", "可复核性"),
        instructions=(
            "Interpret supplied figure or table context conservatively. State what is directly supported, what is "
            "uncertain, and what follow-up evidence is needed."
        ),
    ),
    ResearchSkill(
        id="rebuttal-helper",
        label="审稿回复",
        description="Turn review concerns into response strategy, evidence needs, experiments, and concise rebuttal text.",
        allowed_tool_hints=("search_library", "read_pdf", "extract_docx"),
        output_format="问题归类、回复策略、补实验建议、逐点回复草稿",
        evaluation_criteria=("礼貌具体", "证据驱动", "承认局限", "可执行补救", "不夸大"),
        instructions=(
            "Help respond to reviewer concerns. Classify objections, identify evidence needed, propose realistic "
            "additional analysis, and draft concise respectful responses."
        ),
    ),
)

_SKILLS_BY_ID = {skill.id: skill for skill in BUILT_IN_RESEARCH_SKILLS}


def list_research_skills() -> list[ResearchSkill]:
    return list(BUILT_IN_RESEARCH_SKILLS)


def research_skill_ids() -> list[str]:
    return [skill.id for skill in BUILT_IN_RESEARCH_SKILLS]


def get_research_skill(skill_id: str) -> ResearchSkill:
    normalized = (skill_id or "").strip().lower()
    skill = _SKILLS_BY_ID.get(normalized)
    if not skill:
        raise ResearchSkillNotFoundError(skill_id, research_skill_ids())
    return skill


def build_research_skill_prompt(
    skill: ResearchSkill,
    *,
    task: str,
    context: str = "",
    current_query: str = "",
) -> list[dict[str, str]]:
    bounded_context = (context or "")[:SKILL_CONTEXT_MAX_CHARS]
    system_prompt = (
        "You are executing one built-in research skill inside a larger research assistant. "
        "Stay within the selected skill. Do not claim that files, papers, folders, projects, or external tools were modified. "
        "If evidence is missing, say what evidence is needed instead of inventing it.\n\n"
        f"Skill id: {skill.id}\n"
        f"Skill label: {skill.label}\n"
        f"Skill description: {skill.description}\n"
        f"Skill instructions: {skill.instructions}\n"
        f"Required output format: {skill.output_format}\n"
        f"Evaluation criteria: {', '.join(skill.evaluation_criteria)}"
    )
    user_prompt = (
        f"Current user query:\n{current_query or task}\n\n"
        f"Skill task:\n{task}\n\n"
        f"Available context:\n{bounded_context or 'No additional context supplied.'}"
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


SkillLLM = Callable[[list[dict[str, str]], int], Awaitable[str]]


async def _default_skill_llm(messages: list[dict[str, str]], max_tokens: int) -> str:
    return await llm_service.chat(messages=messages, temperature=0.2, max_tokens=max_tokens)


async def run_research_skill(
    skill_id: str,
    *,
    task: str,
    context: str = "",
    current_query: str = "",
    max_output_chars: int = SKILL_OUTPUT_MAX_CHARS,
    llm: SkillLLM | None = None,
) -> ResearchSkillRunResult:
    skill = get_research_skill(skill_id)
    bounded_task = (task or current_query or "").strip()
    if not bounded_task:
        raise ValueError("Skill task cannot be empty.")
    bounded_context = (context or "")[:SKILL_CONTEXT_MAX_CHARS]
    max_chars = max(500, min(int(max_output_chars or SKILL_OUTPUT_MAX_CHARS), SKILL_OUTPUT_MAX_CHARS))
    max_tokens = max(300, min(2000, max_chars // 2))
    runner = llm or _default_skill_llm
    output = await runner(
        build_research_skill_prompt(
            skill,
            task=bounded_task,
            context=bounded_context,
            current_query=current_query,
        ),
        max_tokens,
    )
    bounded_output = (output or "").strip()[:max_chars]
    if not bounded_output:
        bounded_output = "该技能本轮未生成可用输出，请补充更多上下文后重试。"
    return ResearchSkillRunResult(
        skill=skill,
        task=bounded_task,
        output=bounded_output,
        context_used_chars=len(bounded_context),
    )
