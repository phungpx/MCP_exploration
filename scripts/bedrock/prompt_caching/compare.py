import time
import statistics
from pathlib import Path
from scripts.bedrock.prompt_caching.run import run_benchmark, export_metrics
from scripts.bedrock.prompt_caching.print_metrics import print_summary


def compare_cached_and_uncached(
    model_id: str, num_requests: int = 10, save_dir: str = "scripts/output"
):
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("🔬 RUNNING COMPARISON: CACHED vs UNCACHED")
    print("=" * 80 + "\n")

    # Run without cache
    print("Phase 1: Testing WITHOUT cache...")
    responses_uncached, metrics_uncached = run_benchmark(
        model_id,
        num_requests=num_requests,
        use_cache=False,
    )

    export_metrics(
        model_id=model_id,
        responses=responses_uncached,
        metrics=metrics_uncached,
        filename=str(save_dir / "cache_metrics_uncached.json"),
    )

    print("\n⏳ Waiting 2 seconds before next phase...\n")
    time.sleep(2)

    # Run with cache
    print("Phase 2: Testing WITH cache enabled...")
    responses_cached, metrics_cached = run_benchmark(
        model_id,
        num_requests=num_requests,
        use_cache=True,
    )

    export_metrics(
        model_id=model_id,
        responses=responses_cached,
        metrics=metrics_cached,
        filename=str(save_dir / "cache_metrics_cached.json"),
    )

    # Print individual summaries
    print("\n" + "🟢 " + "=" * 78)
    print("CACHED RESULTS:")
    print_summary(metrics_cached)

    print("\n" + "🔴 " + "=" * 78)
    print("UNCACHED RESULTS:")
    print_summary(metrics_uncached)

    # Comparative analysis
    cached_cost = sum(m.cost_usd for m in metrics_cached)
    uncached_cost = sum(m.cost_usd for m in metrics_uncached)

    cached_latency = statistics.mean([m.latency_ms for m in metrics_cached])
    uncached_latency = statistics.mean([m.latency_ms for m in metrics_uncached])

    cost_savings = uncached_cost - cached_cost
    cost_savings_pct = (cost_savings / uncached_cost) * 100
    latency_improvement = (uncached_latency - cached_latency) / uncached_latency * 100

    print("\n" + "=" * 80)
    print("🏆 FINAL COMPARISON")
    print("=" * 80 + "\n")

    print(f"💰 Cost Comparison:")
    print(f"   Cached:              ${cached_cost:.6f}")
    print(f"   Uncached:            ${uncached_cost:.6f}")
    print(
        f"   Savings:             ${cost_savings:.6f} ({cost_savings_pct:.1f}% reduction)"
    )
    print()

    print(f"⚡ Performance Comparison:")
    print(f"   Cached Latency:      {cached_latency:.0f} ms")
    print(f"   Uncached Latency:    {uncached_latency:.0f} ms")
    print(f"   Improvement:         {latency_improvement:.1f}% faster")
    print()

    print(f"🎯 Recommendation:")
    if cost_savings_pct > 50:
        print(f"   ✅ HIGHLY RECOMMENDED to use caching!")
        print(
            f"   You'll save {cost_savings_pct:.0f}% on costs and get {latency_improvement:.0f}% faster responses."
        )
    elif cost_savings_pct > 20:
        print(f"   ✅ Recommended to use caching for cost optimization.")
    else:
        print(f"   ⚠️  Caching provides moderate benefits for this workload.")

    print("\n" + "=" * 80 + "\n")

    return responses_cached, responses_uncached, metrics_cached, metrics_uncached


if __name__ == "__main__":
    model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    num_requests = 3
    save_dir = "scripts/bedrock/prompt_caching/output"

    (
        responses_cached,
        responses_uncached,
        metrics_cached,
        metrics_uncached,
    ) = compare_cached_and_uncached(
        model_id=model_id,
        num_requests=num_requests,
        save_dir=save_dir,
    )
