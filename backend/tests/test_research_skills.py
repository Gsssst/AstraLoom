import pytest

from app.services.research_skills import (
    ResearchSkillNotFoundError,
    build_research_skill_prompt,
    get_research_skill,
    list_research_skills,
    run_research_skill,
)


def test_builtin_research_skills_are_declarative_and_cover_core_workflows():
    skills = {skill.id: skill for skill in list_research_skills()}

    assert {
        "paper-scout",
        "method-comparison",
        "experiment-planner",
        "survey-writer",
        "figure-interpreter",
        "rebuttal-helper",
    } <= set(skills)
    for skill in skills.values():
        metadata = skill.metadata()
        assert metadata["id"] == skill.id
        assert metadata["label"]
        assert metadata["description"]
        assert metadata["allowed_tool_hints"]
        assert metadata["output_format"]
        assert metadata["evaluation_criteria"]
        assert callable(getattr(skill, "instructions", None)) is False


def test_unknown_research_skill_lists_available_ids():
    with pytest.raises(ResearchSkillNotFoundError) as exc:
        get_research_skill("missing-skill")

    assert exc.value.skill_id == "missing-skill"
    assert "paper-scout" in exc.value.available_skill_ids


def test_research_skill_prompt_contains_contract_metadata():
    skill = get_research_skill("experiment-planner")
    messages = build_research_skill_prompt(
        skill,
        task="plan a video grounding experiment",
        context="dataset: Charades-STA",
        current_query="use experiment-planner",
    )

    joined = "\n".join(message["content"] for message in messages)
    assert "experiment-planner" in joined
    assert "Required output format" in joined
    assert "Evaluation criteria" in joined
    assert "Charades-STA" in joined


@pytest.mark.asyncio
async def test_run_research_skill_uses_bounded_llm_output():
    calls = []

    async def fake_llm(messages, max_tokens):
        calls.append((messages, max_tokens))
        return "实验计划输出" * 1000

    result = await run_research_skill(
        "experiment-planner",
        task="设计 video grounding 实验",
        context="context",
        current_query="query",
        max_output_chars=1200,
        llm=fake_llm,
    )

    assert result.skill.id == "experiment-planner"
    assert len(result.output) == 1200
    assert result.metadata()["output_length"] == 1200
    assert calls[0][1] <= 2000
