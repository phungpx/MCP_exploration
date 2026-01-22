# Pricing constants (as of Jan 2025 - per million tokens)
PRICING = {
    "input": 3.00,  # Regular input tokens
    "cache_write": 3.75,  # Cache creation tokens (25% premium)
    "cache_read": 0.30,  # Cache read tokens (90% discount)
    "output": 15.00,  # Output tokens
}


def calculate_cost(usage: dict[str, int]) -> float:
    cost = 0.0

    # Regular input tokens
    input_tokens = usage.get("inputTokens", 0)
    cost += (input_tokens / 1_000_000) * PRICING["input"]

    # Cache creation tokens (25% premium)
    cache_creation = usage.get("cacheWriteInputTokens", 0)
    cost += (cache_creation / 1_000_000) * PRICING["cache_write"]

    # Cache read tokens (90% discount)
    cache_read = usage.get("cacheReadInputTokens", 0)
    cost += (cache_read / 1_000_000) * PRICING["cache_read"]

    # Output tokens
    output_tokens = usage.get("outputTokens", 0)
    cost += (output_tokens / 1_000_000) * PRICING["output"]

    return cost
