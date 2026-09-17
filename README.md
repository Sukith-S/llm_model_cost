# LLM Model Cost Calculator

A Python package to calculate token costs for various LLM models based on input and output tokens.
Prices come from LiteLLM's public `model_prices_and_context_window.json`, fetched on first use.

## Installation

```bash
pip install llm_model_cost
```
https://pypi.org/project/llm-model-cost/

## Usage

```python
from llm_model_cost import ModelCost

# Calculate cost for a model
costInfo = ModelCost(name="gpt-4o", input_tokens=1000, output_tokens=500)

# Get cost details
print(f"Input cost: ${costInfo.input_cost:.6f}")
print(f"Output cost: ${costInfo.output_cost:.6f}")
print(f"Total cost: ${costInfo.cost:.6f}")

# Prompt caching: input_tokens is the FULL prompt, cached_tokens the subset served from cache
#   OpenAI:    input_tokens=usage.prompt_tokens, cached_tokens=usage.prompt_tokens_details.cached_tokens
#   Anthropic: input_tokens=input_tokens + cache_read_input_tokens + cache_creation_input_tokens,
#              cached_tokens=cache_read_input_tokens, cache_creation_tokens=cache_creation_input_tokens
costInfo = ModelCost(name="gpt-4o", input_tokens=10_000, output_tokens=500, cached_tokens=8_000)
print(costInfo.uncached_input_cost, costInfo.cached_input_cost, costInfo.cache_creation_cost)

# Get model information
model_info = ModelCost.get_model_info("gpt-4o")
print(f"Max tokens: {model_info['max_tokens']}")
print(f"Provider: {model_info['litellm_provider']}")

# List all available models
models = ModelCost.list_models()
```

## How the cost is computed

- `input_cost = uncached_tokens * input_rate + cached_tokens * cache_read_rate + cache_creation_tokens * cache_creation_rate`
- `output_cost = output_tokens * output_rate` (reasoning tokens are part of `output_tokens`)
- Long-context tiers (`*_above_200k_tokens` etc.) apply to the **whole request** once `input_tokens`
  exceeds the threshold, matching provider billing.
- Models with no cache price bill cached tokens at the normal input rate (no discount known).
- `ValueError` is raised for unknown models, models not priced per token (image / audio / TTS), negative
  counts, or `cached_tokens + cache_creation_tokens > input_tokens`.

Not covered: batch / flex / priority service tiers, per-image / per-second / per-character pricing,
tool-call surcharges (web search, code interpreter).

## Features

- Calculate token costs for various LLM models, including prompt-cache reads/writes
- Get model information including max tokens, costs, and provider details
- List all available models and their capabilities
- Automatic updates from the latest pricing data

## Development

```bash
python -m unittest discover tests
```
