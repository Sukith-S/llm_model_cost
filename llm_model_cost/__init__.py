from typing import Optional

from .calculator import ModelCostCalculator


class CostResult:
    """Class to hold cost calculation results with attributes."""

    def __init__(
        self,
        input_cost: float,
        output_cost: float,
        total_cost: float,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        currency: str,
        cached_tokens: int = 0,
        cache_creation_tokens: int = 0,
        uncached_input_cost: Optional[float] = None,
        cached_input_cost: float = 0.0,
        cache_creation_cost: float = 0.0,
    ):
        self.input_cost = input_cost
        self.output_cost = output_cost
        self.total_cost = total_cost
        self.cost = total_cost  # Alias for total_cost for convenience
        self.model_name = model_name
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cached_tokens = cached_tokens
        self.cache_creation_tokens = cache_creation_tokens
        self.uncached_input_cost = input_cost if uncached_input_cost is None else uncached_input_cost
        self.cached_input_cost = cached_input_cost
        self.cache_creation_cost = cache_creation_cost
        self.currency = currency

    def __str__(self):
        return (
            f"CostResult(input_cost=${self.input_cost:.6f}, output_cost=${self.output_cost:.6f}, "
            f"total_cost=${self.total_cost:.6f})"
        )

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost,
            "uncached_input_cost": self.uncached_input_cost,
            "cached_input_cost": self.cached_input_cost,
            "cache_creation_cost": self.cache_creation_cost,
            "model_name": self.model_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "currency": self.currency,
        }


class ModelCost:
    _calculator: Optional[ModelCostCalculator] = None

    @classmethod
    def _get_calculator(cls) -> ModelCostCalculator:
        """Build the shared calculator on first use so importing the package needs no network."""
        if cls._calculator is None:
            cls._calculator = ModelCostCalculator()
        return cls._calculator

    def __new__(
        cls,
        name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        cache_creation_tokens: int = 0,
    ):
        """
        Calculate the cost for a given model and token counts.

        Args:
            name: Name of the model
            input_tokens: Total input (prompt) tokens, including cached tokens
            output_tokens: Number of output tokens
            cached_tokens: Subset of input_tokens read from the prompt cache
            cache_creation_tokens: Subset of input_tokens written to the prompt cache

        Returns:
            CostResult object containing input_cost, output_cost, total_cost and the cache breakdown
        """
        cost_dict = cls._get_calculator().calculate_cost(
            name,
            input_tokens,
            output_tokens,
            cached_tokens=cached_tokens,
            cache_creation_tokens=cache_creation_tokens,
        )
        return CostResult(
            input_cost=cost_dict["input_cost"],
            output_cost=cost_dict["output_cost"],
            total_cost=cost_dict["total_cost"],
            model_name=name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            currency="USD",
            cached_tokens=cached_tokens,
            cache_creation_tokens=cache_creation_tokens,
            uncached_input_cost=cost_dict["uncached_input_cost"],
            cached_input_cost=cost_dict["cached_input_cost"],
            cache_creation_cost=cost_dict["cache_creation_cost"],
        )

    @classmethod
    def get_model_info(cls, name: str):
        """Get detailed information about a specific model."""
        return cls._get_calculator().get_model_info(name)

    @classmethod
    def list_models(cls):
        """List all available models."""
        return cls._get_calculator().list_models()

    @classmethod
    def get_models_by_provider(cls, provider: str):
        """Get all models from a specific provider."""
        return cls._get_calculator().get_models_by_provider(provider)

    @classmethod
    def get_models_by_mode(cls, mode: str):
        """Get all models of a specific mode."""
        return cls._get_calculator().get_models_by_mode(mode)


__version__ = "1.1.0"
