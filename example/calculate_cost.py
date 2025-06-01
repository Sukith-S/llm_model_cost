from llm_model_cost import ModelCostCalculator

def main():
    # Initialize the calculator
    calculator = ModelCostCalculator()
    
    # Example 1: Calculate cost for GPT-4
    model_name = "gpt-4"
    input_tokens = 1000
    output_tokens = 500
    
    cost = calculator.calculate_cost(model_name, input_tokens, output_tokens)
    print(f"\nCost calculation for {model_name}:")
    print(f"Input tokens: {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Input cost: ${cost['input_cost']:.6f}")
    print(f"Output cost: ${cost['output_cost']:.6f}")
    print(f"Total cost: ${cost['total_cost']:.6f}")
    
    # Example 2: Get model information
    model_info = calculator.get_model_info(model_name)
    print(f"\nModel information for {model_name}:")
    print(f"Max tokens: {model_info.get('max_tokens')}")
    print(f"Max input tokens: {model_info.get('max_input_tokens')}")
    print(f"Max output tokens: {model_info.get('max_output_tokens')}")
    print(f"Provider: {model_info.get('litellm_provider')}")
    print(f"Mode: {model_info.get('mode')}")
    
    # Example 3: List all OpenAI models
    openai_models = calculator.get_models_by_provider("openai")
    print("\nOpenAI models:")
    for model in openai_models:
        print(f"- {model}")
    
    # Example 4: List all chat models
    chat_models = calculator.get_models_by_mode("chat")
    print("\nChat models:")
    for model in chat_models[:5]:  # Show first 5 models
        print(f"- {model}")

if __name__ == "__main__":
    main() 