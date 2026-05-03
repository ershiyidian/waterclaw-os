from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    input_cny_per_token: float
    output_cny_per_token: float


MODEL_PRICING_CNY: dict[str, ModelPricing] = {
    "openai/gpt-4o-mini": ModelPricing(input_cny_per_token=0.00000105, output_cny_per_token=0.0000042),
    "openai/gpt-4o": ModelPricing(input_cny_per_token=0.000018, output_cny_per_token=0.000072),
    "anthropic/claude-3-5-sonnet-20241022": ModelPricing(input_cny_per_token=0.000021, output_cny_per_token=0.000105),
    "anthropic/claude-3.5-sonnet": ModelPricing(input_cny_per_token=0.000021, output_cny_per_token=0.000105),
}

DEFAULT_PRICING = ModelPricing(input_cny_per_token=0.000001, output_cny_per_token=0.000004)


def calculate_cost_cny(model: str, input_tokens: float, output_tokens: float) -> float:
    pricing = MODEL_PRICING_CNY.get(model, DEFAULT_PRICING)
    return round(input_tokens * pricing.input_cny_per_token + output_tokens * pricing.output_cny_per_token, 4)
