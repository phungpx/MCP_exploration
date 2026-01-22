# https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_Converse_AnthropicClaude_section.html

import boto3
import json
from loguru import logger
from botocore.exceptions import ClientError

model_id = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
client = boto3.client("bedrock-runtime", region_name="ap-southeast-1")


def add_user_message(messages: list[dict], user_input: str):
    messages.append({"role": "user", "content": [{"text": user_input}]})


def add_assistant_message(messages: list[dict], text: str):
    messages.append({"role": "assistant", "content": [{"text": text}]})


def chat(messages: list[dict]) -> str:
    try:
        response = client.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={
                "maxTokens": 512,
                "temperature": 0.5,
                "topP": 0.9,
            },
        )
        logger.info(json.dumps(response, indent=4, ensure_ascii=False))
        return response["output"]["message"]["content"][0]["text"]

    except (ClientError, Exception) as e:
        logger.error(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)


messages = []

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break

    add_user_message(messages, user_input)
    text = chat(messages)
    add_assistant_message(messages, text)
    print(f"Assistant: {text}")
