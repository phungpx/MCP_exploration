import time
import boto3
import statistics
import json
from dataclasses import dataclass, asdict
from datetime import datetime

from scripts.bedrock.prompt_caching.prompt import (
    SYSTEM_PROMPT,
    DOCUMENT_GENERATION_PROMPT,
)
from scripts.bedrock.prompt_caching.calculate_cost import calculate_cost


@dataclass
class RequestMetrics:
    timestamp: datetime
    latency_ms: float
    input_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    used_cache: bool
    user_message: str


client = boto3.client("bedrock-runtime", region_name="us-west-2")


# Helper functions
def add_user_message(messages, content):
    if isinstance(content, str):
        user_message = {"role": "user", "content": [{"text": content}]}
    else:
        user_message = {"role": "user", "content": content}
    messages.append(user_message)


def add_assistant_message(messages, content):
    if isinstance(content, str):
        assistant_message = {
            "role": "assistant",
            "content": [{"text": content}],
        }
    else:
        assistant_message = {"role": "assistant", "content": content}

    messages.append(assistant_message)


def chat(
    model_id: str,
    messages,
    system=None,
    temperature=0.0,
    stop_sequences=[],
    tools=None,
    tool_choice="auto",
    text_editor=None,
    thinking=False,
    thinking_budget=1024,
    use_cache=False,
) -> tuple[str, RequestMetrics]:
    params = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {
            "temperature": temperature,
            "stopSequences": stop_sequences,
        },
    }

    if system:
        if use_cache:
            params["system"] = [{"text": system}, {"cachePoint": {"type": "default"}}]
        else:
            params["system"] = [{"text": system}]

    tool_choices = {"auto": {"auto": {}}, "any": {"any": {}}}
    if tools or text_editor:
        choice = tool_choices.get(tool_choice, {"tool": {"name": tool_choice}})
        tools_with_cache = (
            tools + [{"cachePoint": {"type": "default"}}] if use_cache else tools
        )
        params["toolConfig"] = {"tools": tools_with_cache, "toolChoice": choice}

    additional_model_fields = {}
    if text_editor:
        additional_model_fields["tools"] = [
            {
                "type": text_editor,
                "name": "str_replace_editor",
            }
        ]

    if thinking:
        additional_model_fields["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        }

    params["additionalModelRequestFields"] = additional_model_fields

    t1 = time.time()
    response = client.converse(**params)
    latency_ms = (time.time() - t1) * 1000

    parts = response["output"]["message"]["content"]
    response_text = "\n".join([p["text"] for p in parts if "text" in p])

    usage = response["usage"]
    metric = RequestMetrics(
        timestamp=datetime.now(),
        latency_ms=latency_ms,
        input_tokens=usage["inputTokens"],
        output_tokens=usage["outputTokens"],
        cache_creation_tokens=usage["cacheWriteInputTokens"],
        cache_read_tokens=usage["cacheReadInputTokens"],
        total_tokens=usage["totalTokens"],
        cost_usd=calculate_cost(usage),
        used_cache=use_cache,
        user_message=messages[0]["content"][0]["text"],
    )

    return response_text, metric


def run_benchmark(
    model_id: str,
    num_requests: int = 10,
    use_cache: bool = False,
):
    questions = [
        "How do I implement proper error handling in Lambda functions?",
        "What are the best practices for async operations in Python?",
        "How can I optimize DynamoDB batch operations?",
        "What security measures should I implement for AWS Lambda?",
        "How do I set up proper monitoring and observability?",
        "What are the cost optimization strategies for serverless?",
        "How do I implement circuit breaker pattern?",
        "What's the best way to handle retries with exponential backoff?",
        "How can I use AWS X-Ray for tracing?",
        "What are the DynamoDB best practices for high-traffic applications?",
    ]

    # ~1.6k tokens
    system_prompt = (f"{SYSTEM_PROMPT}/n{DOCUMENT_GENERATION_PROMPT}").strip()

    metrics: list[RequestMetrics] = []
    responses: list[str] = []
    for i in range(num_requests):
        question = questions[i % len(questions)]
        print(f"📤 Request {i+1}/{num_requests}: {question[:60]}...")
        response, metric = chat(
            model_id=model_id,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"text": question}]}],
            use_cache=use_cache,
        )
        metrics.append(metric)
        responses.append(response)
        if i < num_requests - 1:
            time.sleep(0.5)

    return responses, metrics


def export_metrics(
    model_id: str,
    responses: list[str],
    metrics: list[RequestMetrics],
    filename: str = "cache_metrics.json",
):
    """Export metrics to JSON file"""
    data = {
        "model_id": model_id,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_requests": len(metrics),
            "total_cost": sum(m.cost_usd for m in metrics),
            "avg_latency_ms": statistics.mean([m.latency_ms for m in metrics]),
            "cache_hit_rate": sum(1 for m in metrics if m.used_cache) / len(metrics),
        },
        "responses": [
            {"metric": asdict(m), "response": r} for m, r in zip(metrics, responses)
        ],
    }

    with open(filename, mode="w") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    print(f"📁 Metrics exported to {filename}")


if __name__ == "__main__":
    use_cache = True
    num_requests = 3
    model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    filename = f"cache_metrics_{model_id}_{'cached' if use_cache else 'uncached'}.json"

    responses, metrics = run_benchmark(
        model_id=model_id,
        num_requests=num_requests,
        use_cache=use_cache,
    )
    export_metrics(
        model_id=model_id,
        responses=responses,
        metrics=metrics,
        filename=filename,
    )
