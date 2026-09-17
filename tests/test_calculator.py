import unittest

from llm_model_cost import CostResult, ModelCost
from llm_model_cost.calculator import ModelCostCalculator

# Offline fixture shaped like LiteLLM's model_prices_and_context_window.json.
PRICING = {
    "sample_spec": {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0, "mode": "chat"},
    "gpt-4o": {
        "input_cost_per_token": 2.5e-06,
        "output_cost_per_token": 1e-05,
        "cache_read_input_token_cost": 1.25e-06,
        "litellm_provider": "openai",
        "mode": "chat",
    },
    "claude-sonnet-4": {
        "input_cost_per_token": 3e-06,
        "output_cost_per_token": 1.5e-05,
        "cache_read_input_token_cost": 3e-07,
        "cache_creation_input_token_cost": 3.75e-06,
        "cache_creation_input_token_cost_above_1hr": 6e-06,
        "input_cost_per_token_above_200k_tokens": 6e-06,
        "output_cost_per_token_above_200k_tokens": 2.25e-05,
        "cache_read_input_token_cost_above_200k_tokens": 6e-07,
        "cache_creation_input_token_cost_above_200k_tokens": 7.5e-06,
        "litellm_provider": "anthropic",
        "mode": "chat",
    },
    "no-cache-model": {"input_cost_per_token": 1e-06, "output_cost_per_token": 2e-06, "mode": "chat"},
    "dall-e-3": {"output_cost_per_image": 0.04, "litellm_provider": "openai", "mode": "image_generation"},
}


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.calc = ModelCostCalculator(pricing_data=PRICING)

    def test_plain_per_token_pricing(self):
        cost = self.calc.calculate_cost("gpt-4o", 1000, 500)
        self.assertAlmostEqual(cost["input_cost"], 0.0025)
        self.assertAlmostEqual(cost["output_cost"], 0.005)
        self.assertAlmostEqual(cost["total_cost"], 0.0075)

    def test_cached_tokens_use_cache_read_rate(self):
        # OpenAI semantics: input_tokens is the full prompt, cached_tokens is the subset served from cache.
        cost = self.calc.calculate_cost("gpt-4o", 10_000, 500, cached_tokens=8_000)
        self.assertAlmostEqual(cost["uncached_input_cost"], 2_000 * 2.5e-06)
        self.assertAlmostEqual(cost["cached_input_cost"], 8_000 * 1.25e-06)
        self.assertAlmostEqual(cost["input_cost"], 0.005 + 0.01)
        self.assertAlmostEqual(cost["total_cost"], 0.015 + 0.005)

    def test_cache_creation_tokens_use_cache_creation_rate(self):
        cost = self.calc.calculate_cost("claude-sonnet-4", 10_000, 100, cached_tokens=2_000, cache_creation_tokens=3_000)
        self.assertAlmostEqual(cost["uncached_input_cost"], 5_000 * 3e-06)
        self.assertAlmostEqual(cost["cached_input_cost"], 2_000 * 3e-07)
        self.assertAlmostEqual(cost["cache_creation_cost"], 3_000 * 3.75e-06)
        self.assertAlmostEqual(cost["input_cost"], 0.015 + 0.0006 + 0.01125)

    def test_cached_tokens_without_cache_rate_bill_at_input_rate(self):
        cost = self.calc.calculate_cost("no-cache-model", 1_000, 0, cached_tokens=400)
        self.assertAlmostEqual(cost["input_cost"], 1_000 * 1e-06)

    def test_long_context_tier_applies_to_whole_request(self):
        cost = self.calc.calculate_cost("claude-sonnet-4", 250_000, 1_000, cached_tokens=50_000)
        self.assertAlmostEqual(cost["uncached_input_cost"], 200_000 * 6e-06)
        self.assertAlmostEqual(cost["cached_input_cost"], 50_000 * 6e-07)
        self.assertAlmostEqual(cost["output_cost"], 1_000 * 2.25e-05)

    def test_at_threshold_stays_on_base_tier(self):
        cost = self.calc.calculate_cost("claude-sonnet-4", 200_000, 10)
        self.assertAlmostEqual(cost["input_cost"], 200_000 * 3e-06)
        self.assertAlmostEqual(cost["output_cost"], 10 * 1.5e-05)

    def test_cached_exceeding_input_raises(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_cost("gpt-4o", 100, 10, cached_tokens=101)
        with self.assertRaises(ValueError):
            self.calc.calculate_cost("claude-sonnet-4", 100, 10, cached_tokens=60, cache_creation_tokens=50)

    def test_negative_tokens_raise(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_cost("gpt-4o", -1, 10)

    def test_non_token_priced_model_raises_instead_of_zero(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_cost("dall-e-3", 1000, 100)

    def test_unknown_model_raises(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_cost("does-not-exist", 1, 1)

    def test_sample_spec_is_not_a_model(self):
        self.assertNotIn("sample_spec", self.calc.list_models())
        with self.assertRaises(ValueError):
            self.calc.get_model_info("sample_spec")


class ModelCostWrapperTests(unittest.TestCase):
    def setUp(self):
        ModelCost._calculator = ModelCostCalculator(pricing_data=PRICING)

    def test_wrapper_exposes_breakdown(self):
        result = ModelCost(name="gpt-4o", input_tokens=10_000, output_tokens=500, cached_tokens=8_000)
        self.assertIsInstance(result, CostResult)
        self.assertEqual(result.cached_tokens, 8_000)
        self.assertAlmostEqual(result.cached_input_cost, 0.01)
        self.assertAlmostEqual(result.uncached_input_cost, 0.005)
        self.assertAlmostEqual(result.input_cost, 0.015)
        self.assertAlmostEqual(result.cost, 0.02)
        self.assertEqual(result.to_dict()["cached_tokens"], 8_000)

    def test_wrapper_defaults_unchanged(self):
        result = ModelCost(name="gpt-4o", input_tokens=1000, output_tokens=500)
        self.assertAlmostEqual(result.cost, 0.0075)


if __name__ == "__main__":
    unittest.main()
