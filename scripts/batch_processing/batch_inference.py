import boto3
import json
import time
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

# Configure Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Configuration & Constants ---


@dataclass
class ModelPricing:
    """Pricing per 1M tokens (USD)"""

    input_ondemand: float
    output_ondemand: float
    # Batch is typically 50% of on-demand price
    input_batch: float
    output_batch: float


# Pricing Reference (Example: Claude 3 Haiku)
PRICING_REGISTRY = {
    "anthropic.claude-3-haiku-20240307-v1:0": ModelPricing(0.25, 1.25, 0.125, 0.625),
    "anthropic.claude-3-sonnet-20240229-v1:0": ModelPricing(3.00, 15.00, 1.50, 7.50),
    "anthropic.claude-3-5-sonnet-20240620-v1:0": ModelPricing(3.00, 15.00, 1.50, 7.50),
    # Default fallback (placeholder)
    "default": ModelPricing(1.0, 1.0, 0.5, 0.5),
}

# --- Utilities ---


class S3Utils:
    """Helper for S3 operations"""

    def __init__(self, session: boto3.Session):
        self.s3_client = session.client("s3")

    @staticmethod
    def parse_s3_uri(s3_uri: str) -> Tuple[str, str]:
        """Parses s3://bucket/key into (bucket, key)"""
        parsed = urlparse(s3_uri)
        return parsed.netloc, parsed.path.lstrip("/")

    def upload_file(self, local_path: str, s3_uri: str) -> str:
        bucket, key = self.parse_s3_uri(s3_uri)
        try:
            self.s3_client.upload_file(local_path, bucket, key)
            logger.info(f"Uploaded {local_path} to {s3_uri}")
            return s3_uri
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise

    def download_file(self, s3_uri: str, local_path: str) -> str:
        bucket, key = self.parse_s3_uri(s3_uri)
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(bucket, key, local_path)
            logger.info(f"Downloaded {s3_uri} to {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            raise


class CostAnalyzer:
    """Handles cost estimation and comparison"""

    @staticmethod
    def calculate_savings(
        model_id: str, input_tokens: int, output_tokens: int
    ) -> Dict[str, float]:
        pricing = PRICING_REGISTRY.get(model_id, PRICING_REGISTRY["default"])

        # Calculate Costs
        ondemand_cost = (input_tokens / 1_000_000 * pricing.input_ondemand) + (
            output_tokens / 1_000_000 * pricing.output_ondemand
        )

        batch_cost = (input_tokens / 1_000_000 * pricing.input_batch) + (
            output_tokens / 1_000_000 * pricing.output_batch
        )

        savings = ondemand_cost - batch_cost
        savings_pct = (savings / ondemand_cost * 100) if ondemand_cost > 0 else 0

        return {
            "batch_cost": round(batch_cost, 4),
            "ondemand_cost": round(ondemand_cost, 4),
            "savings": round(savings, 4),
            "savings_pct": round(savings_pct, 2),
        }


class BedrockBatchManager:
    """Core logic for managing Bedrock Batch Inference"""

    def __init__(
        self, region_name: str = "us-east-1", profile_name: Optional[str] = None
    ):
        session = boto3.Session(profile_name=profile_name, region_name=region_name)
        self.bedrock = session.client("bedrock")
        self.s3_utils = S3Utils(session)
        self.region = region_name

    def prepare_jsonl(self, prompts: List[Dict], output_file: str) -> str:
        """Creates the JSONL input file formatted for Anthropic models"""
        with open(output_file, "w") as f:
            for i, item in enumerate(prompts):
                # Construct Payload for Claude 3
                record = {
                    "recordId": item.get("id", f"record_{i:06d}"),
                    "modelInput": {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": item.get("max_tokens", 1024),
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"type": "text", "text": item["prompt"]}],
                            }
                        ],
                    },
                }
                f.write(json.dumps(record) + "\n")

        logger.info(f"Generated input file: {output_file} ({len(prompts)} records)")
        return output_file

    def submit_job(
        self,
        job_name: str,
        model_id: str,
        input_s3_uri: str,
        output_s3_uri: str,
        role_arn: str,
    ) -> str:
        """Submits a batch inference job"""
        try:
            response = self.bedrock.create_model_invocation_job(
                roleArn=role_arn,
                modelId=model_id,
                jobName=job_name,
                inputDataConfig={"s3InputDataConfig": {"s3Uri": input_s3_uri}},
                outputDataConfig={"s3OutputDataConfig": {"s3Uri": output_s3_uri}},
            )
            job_arn = response["jobArn"]
            logger.info(f"Job submitted successfully. ARN: {job_arn}")
            return job_arn
        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            raise

    def wait_for_job(self, job_arn: str, poll_interval: int = 60) -> Dict:
        """Blocks and monitors job until terminal state"""
        logger.info(f"Monitoring job: {job_arn}")
        start_time = time.time()

        while True:
            response = self.bedrock.get_model_invocation_job(jobIdentifier=job_arn)
            status = response["status"]

            if status in ["Completed", "Failed", "Stopped"]:
                duration = (time.time() - start_time) / 60
                logger.info(
                    f"Job ended with status: {status} (Duration: {duration:.1f}m)"
                )
                return response

            logger.info(f"Status: {status}...")
            time.sleep(poll_interval)

    def process_results(self, job_response: Dict) -> None:
        """Downloads manifest and prints analysis"""
        if job_response["status"] != "Completed":
            logger.warning("Job did not complete successfully. Skipping analysis.")
            return

        # 1. Locate Output Manifest
        # The output path in the response points to the folder, we need the manifest file
        # Format usually: s3://bucket/prefix/job-id/manifest.json.out
        # Note: Bedrock creates a subfolder with the Job ID.

        output_config = job_response.get("outputDataConfig", {}).get(
            "s3OutputDataConfig", {}
        )
        s3_output_uri = output_config.get("s3Uri")

        # Bedrock appends a directory with the Job ID + manifest.json.out seems to be inside or defined in documentation
        # Actually, let's look for where the manifest really is.
        # It's safest to construct the manifest path if we know the job structure,
        # but often it's easier to list the bucket or assume standard structure:
        # <output_uri>/<job_id>/manifest.json.out

        job_id = job_response["jobArn"].split("/")[-1]
        manifest_s3_uri = f"{s3_output_uri.rstrip('/')}/{job_id}/manifest.json.out"

        local_manifest_path = f"results/{job_id}_manifest.json"

        try:
            logger.info(f"Attempting to download manifest from: {manifest_s3_uri}")
            self.s3_utils.download_file(manifest_s3_uri, local_manifest_path)

            with open(local_manifest_path, "r") as f:
                manifest_data = json.load(f)

            self._print_report(manifest_data, job_response.get("modelId"))

        except Exception as e:
            logger.error(f"Could not retrieve or parse manifest: {e}")
            logger.info("Tip: Verify the output S3 path structure manually.")

    def _print_report(self, manifest: Dict, model_id: str):
        stats = {
            "total": manifest.get("inputRecordsCount", 0),
            "success": manifest.get("successfulRecordsCount", 0),
            "failed": manifest.get("failedRecordsCount", 0),
            "in_tok": manifest.get("totalInputTokenCount", 0),
            "out_tok": manifest.get("totalOutputTokenCount", 0),
        }

        financials = CostAnalyzer.calculate_savings(
            model_id, stats["in_tok"], stats["out_tok"]
        )

        print("\n" + "=" * 50)
        print(f"📊 BATCH INFERENCE REPORT: {model_id}")
        print("=" * 50)
        print(
            f"Records: {stats['success']}/{stats['total']} (Failed: {stats['failed']})"
        )
        print(f"Tokens:  In: {stats['in_tok']:,} | Out: {stats['out_tok']:,}")
        print("-" * 50)
        print(f"💰 Cost (Batch):      ${financials['batch_cost']:.4f}")
        print(f"💰 Cost (On-Demand):  ${financials['ondemand_cost']:.4f}")
        print(
            f"💵 SAVINGS:           ${financials['savings']:.4f} ({financials['savings_pct']}%)"
        )
        print("=" * 50 + "\n")


# --- Main Execution ---


def main():
    # --- 1. User Settings ---
    REGION = "us-east-1"
    MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
    ROLE_ARN = "arn:aws:iam::YOUR_ACCOUNT_ID:role/BedrockBatchInferenceRole"
    BUCKET = "your-s3-bucket-name"
    PREFIX = "batch-tests"

    # Initialize Manager
    manager = BedrockBatchManager(region_name=REGION)

    # --- 2. Create Dummy Data ---
    prompts = [
        {
            "id": f"req_{i}",
            "prompt": "Explain quantum computing briefly.",
            "max_tokens": 100,
        }
        for i in range(10)
    ]

    local_input = manager.prepare_jsonl(prompts, "input_batch.jsonl")

    # --- 3. Upload to S3 ---
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    input_s3_key = f"{PREFIX}/{timestamp}/input.jsonl"
    input_uri = f"s3://{BUCKET}/{input_s3_key}"
    output_uri = f"s3://{BUCKET}/{PREFIX}/{timestamp}/output"

    # NOTE: Commented out to prevent accidental execution without valid credentials
    # manager.s3_utils.upload_file(local_input, input_uri)

    print("\n--- Dry Run Configuration ---")
    print(f"Model: {MODEL_ID}")
    print(f"Input: {input_uri}")
    print(f"Output: {output_uri}")

    # --- 4. Submit & Monitor (Uncomment to run) ---
    # job_name = f"batch-job-{timestamp}"
    # job_arn = manager.submit_job(job_name, MODEL_ID, input_uri, output_uri, ROLE_ARN)
    # job_result = manager.wait_for_job(job_arn)
    # manager.process_results(job_result)


if __name__ == "__main__":
    main()
