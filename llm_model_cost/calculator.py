import requests
from typing import Dict, List, Optional, Union
import json

class ModelCostCalculator:
    """A class to calculate token costs for various LLM models."""
    
    PRICING_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    
    def __init__(self):
        """Initialize the calculator and fetch the latest pricing data."""
        self._pricing_data = self._fetch_pricing_data()
    
    def _fetch_pricing_data(self) -> Dict:
        """Fetch the latest pricing data from the source."""
        try:
            response = requests.get(self.PRICING_URL)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch pricing data: {str(e)}")
    
    def calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """
        Calculate the cost for a given model and token counts.
        
        Args:
            model_name: Name of the model
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary containing input cost, output cost, and total cost
        """
        if model_name not in self._pricing_data:
            raise ValueError(f"Model {model_name} not found in pricing data")
        
        model_info = self._pricing_data[model_name]
        
        input_cost = input_tokens * model_info.get("input_cost_per_token", 0)
        output_cost = output_tokens * model_info.get("output_cost_per_token", 0)
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost
        }
    
    def get_model_info(self, model_name: str) -> Dict:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary containing model information
        """
        if model_name not in self._pricing_data:
            raise ValueError(f"Model {model_name} not found in pricing data")
        
        return self._pricing_data[model_name]
    
    def list_models(self) -> List[str]:
        """
        List all available models in the pricing data.
        
        Returns:
            List of model names
        """
        return list(self._pricing_data.keys())
    
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
            if info.get("litellm_provider") == provider
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
            if info.get("mode") == mode
        ] 
    