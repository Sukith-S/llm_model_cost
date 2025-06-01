from .calculator import ModelCostCalculator

class CostResult:
    """Class to hold cost calculation results with attributes."""
    def __init__(self, input_cost: float, output_cost: float, total_cost: float, model_name: str, input_tokens: int, output_tokens: int, currency: str):
        self.input_cost = input_cost
        self.output_cost = output_cost
        self.total_cost = total_cost
        self.cost = total_cost  # Alias for total_cost for convenience
        self.model_name = model_name
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.currency = currency
    
    def __str__(self):
        return f"CostResult(input_cost=${self.input_cost:.6f}, output_cost=${self.output_cost:.6f}, total_cost=${self.total_cost:.6f})"
    
    def __repr__(self):
        return self.__str__()
    
    def to_dict(self):
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost,
            "model_name": self.model_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "currency": self.currency
        }

class ModelCost:
    _calculator = ModelCostCalculator()
    
    def __new__(cls, name: str, input_tokens: int = 0, output_tokens: int = 0):
        """
        Calculate the cost for a given model and token counts.
        
        Args:
            name: Name of the model
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            CostResult object containing input_cost, output_cost, and total_cost attributes
        """
        cost_dict = cls._calculator.calculate_cost(name, input_tokens, output_tokens)
        return CostResult(
            input_cost=cost_dict['input_cost'],
            output_cost=cost_dict['output_cost'],
            total_cost=cost_dict['total_cost'],
            model_name=name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            currency="USD",

        )
    
    @classmethod
    def get_model_info(cls, name: str):
        """Get detailed information about a specific model."""
        return cls._calculator.get_model_info(name)
    
    @classmethod
    def list_models(cls):
        """List all available models."""
        return cls._calculator.list_models()
    
    @classmethod
    def get_models_by_provider(cls, provider: str):
        """Get all models from a specific provider."""
        return cls._calculator.get_models_by_provider(provider)
    
    @classmethod
    def get_models_by_mode(cls, mode: str):
        """Get all models of a specific mode."""
        return cls._calculator.get_models_by_mode(mode)

__version__ = "1.0.0" 