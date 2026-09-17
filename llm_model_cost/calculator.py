import re
from typing import Dict, List, Optional

import requests


class ModelCostCalculator:
    """A class to calculate token costs for various LLM models."""

    PRICING_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    # Keys in the pricing file that describe the file format, not a model.
    _NON_MODEL_KEYS = frozenset({"sample_spec"})
    _TIER_KEY = re.compile(r"^input_cost_per_token_above_(\d+)k_tokens$")

    def __init__(self, pricing_data: Optional[Dict] = None, timeout: float = 30):
        """
        Initialize the calculator.

        Args:
            pricing_data: Pre-loaded pricing table (same shape as the LiteLLM file). When omitted the
                latest table is fetched from PRICING_URL.
            timeout: HTTP timeout in seconds for the pricing fetch.
        """
        self._pricing_data = pricing_data if pricing_data is not None else self._fetch_pricing_data(timeout)

    def _fetch_pricing_data(self, timeout: float) -> Dict:
        """Fetch the latest pricing data from the source."""
        try:
            response = requests.get(self.PRICING_URL, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch pricing data: {str(e)}")

    def _model(self, model_name: str) -> Dict:
        if model_name in self._NON_MODEL_KEYS or model_name not in self._pricing_data:
            raise ValueError(f"Model {model_name} not found in pricing data")
        return self._pricing_data[model_name]

    @classmethod
    def _tier_suffix(cls, model_info: Dict, input_tokens: int) -> str:
        """
        Long-context tier for this request, e.g. "_above_200k_tokens", or "" for base pricing.

        Providers (Anthropic, Gemini, ...) bill the *whole* request at the higher tier once the prompt
        exceeds the threshold, so the suffix is applied to every rate of the request.
        """
        best: Optional[int] = None
        for key in model_info:
            match = cls._TIER_KEY.match(key)
            if not match:
                continue
            threshold_k = int(match.group(1))
            if input_tokens > threshold_k * 1000 and (best is None or threshold_k > best):
                best = threshold_k
        return f"_above_{best}k_tokens" if best is not None else ""

    def calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        cache_creation_tokens: int = 0,
    ) -> Dict[str, float]:
        """
        Calculate the cost for a given model and token counts.

        Args:
            model_name: Name of the model
            input_tokens: Total number of input (prompt) tokens, including any cached tokens
            output_tokens: Number of output (completion) tokens, including reasoning tokens
            cached_tokens: Subset of input_tokens that were read from the prompt cache
                (OpenAI ``usage.prompt_tokens_details.cached_tokens``, Anthropic ``cache_read_input_tokens``)
            cache_creation_tokens: Subset of input_tokens that were written to the prompt cache
                (Anthropic ``cache_creation_input_tokens``)

        Returns:
            Dictionary with input_cost (all input-side cost), output_cost, total_cost, and the input
            breakdown uncached_input_cost, cached_input_cost, cache_creation_cost.

        Raises:
            ValueError: unknown model, model not priced per token (image/audio/... models), or
                inconsistent token counts.
        """
        model_info = self._model(model_name)
        if "input_cost_per_token" not in model_info or "output_cost_per_token" not in model_info:
            price_keys = sorted(k for k in model_info if "cost" in k)
            raise ValueError(
                f"Model {model_name} is not priced per token (pricing keys: {price_keys}); "
                "token cost cannot be calculated"
            )

        for label, value in (
            ("input_tokens", input_tokens),
            ("output_tokens", output_tokens),
            ("cached_tokens", cached_tokens),
            ("cache_creation_tokens", cache_creation_tokens),
        ):
            if value < 0:
                raise ValueError(f"{label} must be >= 0, got {value}")
        if cached_tokens + cache_creation_tokens > input_tokens:
            raise ValueError(
                f"cached_tokens ({cached_tokens}) + cache_creation_tokens ({cache_creation_tokens}) "
                f"exceed input_tokens ({input_tokens}); input_tokens must include cached tokens"
            )

        tier = self._tier_suffix(model_info, input_tokens)

        def rate(base_key: str, fallback: Optional[float] = None) -> Optional[float]:
            value = model_info.get(base_key + tier, model_info.get(base_key))
            return fallback if value is None else value

        input_rate = rate("input_cost_per_token")
        output_rate = rate("output_cost_per_token")
        # No cache price published => no discount: bill cached tokens as ordinary input.
        cache_read_rate = rate("cache_read_input_token_cost", fallback=input_rate)
        cache_creation_rate = rate("cache_creation_input_token_cost", fallback=input_rate)

        uncached_tokens = input_tokens - cached_tokens - cache_creation_tokens
        uncached_input_cost = uncached_tokens * input_rate
        cached_input_cost = cached_tokens * cache_read_rate
        cache_creation_cost = cache_creation_tokens * cache_creation_rate
        input_cost = uncached_input_cost + cached_input_cost + cache_creation_cost
        output_cost = output_tokens * output_rate

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "uncached_input_cost": uncached_input_cost,
            "cached_input_cost": cached_input_cost,
            "cache_creation_cost": cache_creation_cost,
        }

    def get_model_info(self, model_name: str) -> Dict:
        """
        Get detailed information about a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary containing model information
        """
        return self._model(model_name)

    def list_models(self) -> List[str]:
        """
        List all available models in the pricing data.

        Returns:
            List of model names
        """
        return [name for name in self._pricing_data if name not in self._NON_MODEL_KEYS]

    def get_models_by_provider(self, provider: str) -> List[str]:
        """
        Get all models from a specific provider.

        Args:
            provider: Name of the provider (e.g., "openai")

        Returns:
            List of model names from the specified provider
        """
        return [
            model_name for model_name, info in self._pricing_data.items()
            if model_name not in self._NON_MODEL_KEYS and info.get("litellm_provider") == provider
        ]

    def get_models_by_mode(self, mode: str) -> List[str]:
        """
        Get all models of a specific mode (e.g., "chat", "moderation").

        Args:
            mode: Mode of the models

        Returns:
            List of model names with the specified mode
        """
        return [
            model_name for model_name, info in self._pricing_data.items()
            if model_name not in self._NON_MODEL_KEYS and info.get("mode") == mode
        ]
