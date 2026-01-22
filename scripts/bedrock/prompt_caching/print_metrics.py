import statistics
from scripts.bedrock.prompt_caching.run import RequestMetrics
from scripts.bedrock.prompt_caching.calculate_cost import PRICING


def print_summary(metrics: list[RequestMetrics]):
    if not metrics:
        print("No metrics to summarize")
        return

    # Calculate statistics
    latencies = [m.latency_ms for m in metrics]
    costs = [m.cost_usd for m in metrics]
    cache_hits = sum(1 for m in metrics if m.used_cache)

    total_cost = sum(costs)
    avg_latency = statistics.mean(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    median_latency = statistics.median(latencies)

    total_input = sum(m.input_tokens for m in metrics)
    total_cache_read = sum(m.cache_read_tokens for m in metrics)
    total_cache_write = sum(m.cache_creation_tokens for m in metrics)
    total_output = sum(m.output_tokens for m in metrics)

    print(f"\n{'='*80}")
    print(f"📊 BENCHMARK SUMMARY")
    print(f"{'='*80}\n")

    print(f"📈 Performance Metrics:")
    print(f"   Total Requests:      {len(metrics)}")
    print(f"   Cache Hits:          {cache_hits} ({cache_hits/len(metrics)*100:.1f}%)")
    print(f"   Cache Misses:        {len(metrics) - cache_hits}")
    print()

    print(f"⚡ Latency Statistics:")
    print(f"   Average:             {avg_latency:.0f} ms")
    print(f"   Median:              {median_latency:.0f} ms")
    print(f"   Min:                 {min_latency:.0f} ms")
    print(f"   Max:                 {max_latency:.0f} ms")

    if cache_hits > 0:
        cached_latencies = [m.latency_ms for m in metrics if m.used_cache]
        uncached_latencies = [m.latency_ms for m in metrics if not m.used_cache]
        if uncached_latencies and cached_latencies:
            speedup = statistics.mean(uncached_latencies) / statistics.mean(
                cached_latencies
            )
            print(f"   Speedup (cached):    {speedup:.2f}x faster")
    print()

    print(f"🪙 Token Usage:")
    print(f"   Input Tokens:        {total_input:,}")
    print(f"   Cache Write Tokens:  {total_cache_write:,}")
    print(f"   Cache Read Tokens:   {total_cache_read:,}")
    print(f"   Output Tokens:       {total_output:,}")
    print()

    print(f"💰 Cost Analysis:")
    print(f"   Total Cost:          ${total_cost:.6f}")
    print(f"   Average per Request: ${total_cost/len(metrics):.6f}")
    print(
        f"   Cost per 1K Tokens:  ${total_cost/((total_input+total_cache_write+total_cache_read+total_output)/1000):.6f}"
    )
    print()

    # Calculate savings if cache was used
    if total_cache_read > 0:
        # Cost if cache read tokens were regular input tokens
        cost_without_cache = (total_cache_read / 1_000_000) * PRICING["input"]
        actual_cache_cost = (total_cache_read / 1_000_000) * PRICING["cache_read"]
        savings = cost_without_cache - actual_cache_cost
        savings_pct = (savings / (total_cost + savings)) * 100

        print(f"💎 Cache Savings:")
        print(f"   Money Saved:         ${savings:.6f}")
        print(f"   Savings Percentage:  {savings_pct:.1f}%")
        print(f"   Tokens Cached:       {total_cache_read:,} tokens")
        print()

    print(f"{'='*80}\n")
