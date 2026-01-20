import boto3
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
from typing import Tuple
from urllib.parse import urlparse


class S3Utils:
    def __init__(self, session: boto3.Session, region_name: str = "us-east-1"):
        self.s3_client = session.client("s3", region_name=region_name)

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


class BedrockBatchManager:
    def __init__(
        self, region_name: str = "us-east-1", profile_name: Optional[str] = None
    ):
        session = boto3.Session(profile_name=profile_name, region_name=region_name)
        self.bedrock = session.client("bedrock")
        self.s3_utils = S3Utils(session, region_name=region_name)
        self.region = region_name

    def prepare_jsonl(self, prompts: List[Dict], output_file: str) -> str:
        with open(file=output_file, mode="w") as f:
            for i, item in enumerate(prompts):
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
        except Exception as e:
            logger.error(f"Could not retrieve or parse manifest: {e}")
            logger.info("Tip: Verify the output S3 path structure manually.")


def main():
    REGION = "ap-southeast-1"
    MODEL_ID = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    ROLE_ARN = "arn:aws:iam::061051247257:role/AmazonBedrockServiceRole-c6alv2tvqgyh0n-3qurb3xkdy6pif"
    BUCKET = "ptp-dev-aidata-bronze"
    PREFIX = "lk_conversational_simulation/batch-inference"

    # Initialize Manager
    manager = BedrockBatchManager(region_name=REGION)

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
    # Bedrock requires the s3Uri for outputDataConfig to end with a trailing "/"
    # and point to a prefix (folder), not a specific object.
    output_uri = f"s3://{BUCKET}/{PREFIX}/{timestamp}/output/"

    # NOTE: Commented out to prevent accidental execution without valid credentials
    manager.s3_utils.upload_file(local_input, input_uri)

    print("\n--- Dry Run Configuration ---")
    print(f"Model: {MODEL_ID}")
    print(f"Input: {input_uri}")
    print(f"Output: {output_uri}")

    # --- 4. Submit & Monitor (Uncomment to run) ---
    job_name = f"batch-job-{timestamp}"
    job_arn = manager.submit_job(job_name, MODEL_ID, input_uri, output_uri, ROLE_ARN)
    job_result = manager.wait_for_job(job_arn)

    # Export job_result to a JSON file for later inspection
    os.makedirs("results", exist_ok=True)
    job_result_path = f"results/{job_name}_result.json"
    with open(job_result_path, "w") as f:
        json.dump(job_result, f, indent=2, default=str)
    logger.info(f"Saved job_result to {job_result_path}")

    manager.process_results(job_result)


if __name__ == "__main__":
    main()
