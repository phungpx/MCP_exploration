import json

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class BedrockInference:
    def __init__(self, model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"):
        self.model_id = model_id
        config = Config(
            retries={
                "max_attempts": 10,
                "mode": "adaptive",
            }
        )
        self.client = boto3.client(
            "bedrock-runtime",
            region_name="ap-southeast-1",
            config=config,
        )

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry_error_callback=lambda r: r.outcome.failed,
    )
    def predict(self, prompt: str) -> str | None:
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 1500,
                        "temperature": 0.1,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ),
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"].strip()
        except ClientError as e:
            if e.response["Error"]["Code"] == "ThrottlingException":
                logger.warning("ThrottlingException from Bedrock caught, retrying...")
                raise  # Reraise to trigger tenacity retry
            logger.error(f"An unexpected Bedrock client error occurred: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    bedrock_inference = BedrockInference(
        model_id="apac.anthropic.claude-sonnet-4-20250514-v1:0"
    )
    print(bedrock_inference.predict("Hello, how are you?"))
