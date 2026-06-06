"""Regression tests for model-specific token cost estimates."""

from app.services import usage_tracker


def test_deepseek_usage_cost_uses_deepseek_rates(monkeypatch):
    monkeypatch.setattr(usage_tracker.settings, "USAGE_DEEPSEEK_INPUT_CNY_PER_1M", 3.0)
    monkeypatch.setattr(usage_tracker.settings, "USAGE_DEEPSEEK_OUTPUT_CNY_PER_1M", 6.0)

    cost = usage_tracker.estimate_usage_cost(
        model="deepseek-v4-pro",
        prompt_tokens=1_000_000,
        completion_tokens=500_000,
    )

    assert cost == 6.0


def test_openai_compatible_usage_cost_uses_configured_gpt_rates(monkeypatch):
    monkeypatch.setattr(usage_tracker.settings, "USAGE_OPENAI_COMPATIBLE_INPUT_CNY_PER_1M", 10.0)
    monkeypatch.setattr(usage_tracker.settings, "USAGE_OPENAI_COMPATIBLE_OUTPUT_CNY_PER_1M", 30.0)

    cost = usage_tracker.estimate_usage_cost(
        model="openai/gpt-5.5",
        prompt_tokens=250_000,
        completion_tokens=100_000,
    )

    assert cost == 5.5


def test_unknown_model_usage_cost_uses_fallback_rates(monkeypatch):
    monkeypatch.setattr(usage_tracker.settings, "USAGE_FALLBACK_INPUT_CNY_PER_1M", 2.0)
    monkeypatch.setattr(usage_tracker.settings, "USAGE_FALLBACK_OUTPUT_CNY_PER_1M", 8.0)

    cost = usage_tracker.estimate_usage_cost(
        model="local-test-model",
        prompt_tokens=500_000,
        completion_tokens=125_000,
    )

    assert cost == 2.0
