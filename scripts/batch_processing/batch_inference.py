import boto3
import json
import time
import os
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse
from loguru import logger


class BedrockBatchProcessing:
    def __init__(self, region_name: str):
        self.bedrock = boto3.client("bedrock", region_name=region_name)
        self.s3 = boto3.client("s3", region_name=region_name)

    def prepare_jsonl(
        self,
        prompts: List[Dict],
        output_file: str,
        default_max_tokens: int = 1024,
    ) -> str:
        with open(output_file, "w") as f:
            for i, item in enumerate(prompts):
                record = {
                    "recordId": item.get("id", f"record_{i:06d}"),
                    "modelInput": {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": item.get("max_tokens", default_max_tokens),
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": item["prompt"]},
                                ],
                            }
                        ],
                    },
                }
                if "system" in item:
                    record["modelInput"]["system"] = item["system"]
                f.write(json.dumps(record) + "\n")

        logger.info(f"Created {output_file} with {len(prompts)} records")
        return output_file

    def upload_to_s3(self, local_path: str, s3_uri: str) -> str:
        """Upload file to S3."""
        parsed = urlparse(s3_uri)
        bucket, key = parsed.netloc, parsed.path.lstrip("/")
        self.s3.upload_file(local_path, bucket, key)
        logger.info(f"Uploaded to {s3_uri}")
        return s3_uri

    def download_from_s3(self, s3_uri: str, local_path: str) -> str:
        """Download file from S3."""
        parsed = urlparse(s3_uri)
        bucket, key = parsed.netloc, parsed.path.lstrip("/")
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        self.s3.download_file(bucket, key, local_path)
        logger.info(f"Downloaded to {local_path}")
        return local_path

    def submit_job(
        self,
        job_name: str,
        model_id: str,
        input_s3_uri: str,
        output_s3_uri: str,
        role_arn: str,
    ) -> str:
        """Submit batch job and return job ARN."""
        response = self.bedrock.create_model_invocation_job(
            roleArn=role_arn,
            modelId=model_id,
            jobName=job_name,
            inputDataConfig={"s3InputDataConfig": {"s3Uri": input_s3_uri}},
            outputDataConfig={"s3OutputDataConfig": {"s3Uri": output_s3_uri}},
        )
        job_arn = response["jobArn"]
        logger.info(f"Submitted job: {job_arn}")
        return job_arn

    def wait_for_job(self, job_arn: str, poll_interval: int = 60) -> Dict:
        terminal_states = {"Completed", "Failed", "Stopped"}
        start = time.time()

        while True:
            response = self.bedrock.get_model_invocation_job(jobIdentifier=job_arn)
            status = response["status"]
            elapsed = (time.time() - start) / 60

            if status in terminal_states:
                logger.info(f"Job {status} after {elapsed:.1f} minutes")
                return response

            logger.info(f"Status: {status} ({elapsed:.1f}m elapsed)")
            time.sleep(poll_interval)

    def get_results(
        self, job_response: Dict, output_dir: str = "results"
    ) -> List[Dict]:
        if job_response["status"] != "Completed":
            logger.error(f"Job not completed: {job_response['status']}")
            return []

        job_id = job_response["jobArn"].split("/")[-1]
        output_base = job_response["outputDataConfig"]["s3OutputDataConfig"]["s3Uri"]
        output_uri = f"{output_base.rstrip('/')}/{job_id}/"

        # List and download output files
        parsed = urlparse(output_uri)
        bucket, prefix = parsed.netloc, parsed.path.lstrip("/")

        os.makedirs(output_dir, exist_ok=True)
        results = []

        response = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".jsonl.out"):
                local_file = os.path.join(output_dir, os.path.basename(key))
                self.s3.download_file(bucket, key, local_file)

                with open(local_file) as f:
                    for line in f:
                        results.append(json.loads(line))

        logger.info(f"Retrieved {len(results)} results")
        return results


def main():
    # === CONFIGURATION ===
    CONFIG = {
        "region": "ap-southeast-1",
        "model_id": "apac.anthropic.claude-sonnet-4-20250514-v1:0",
        "role_arn": "arn:aws:iam::061051247257:role/ptp-dev-aidata-ds-sagemaker-bedrock-execution-role",
        "bucket": "ptp-dev-aidata-bronze",
        "prefix": "lk_conversational_simulation/batch-inference",
    }

    # === SETUP ===
    manager = BedrockBatchProcessing(region_name=CONFIG["region"])
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_name = f"test-batch-{timestamp}"

    # === TEST PROMPTS ===
    prompts = [
        {
            "id": f"req_{i}",
            "prompt": "Explain quantum computing in one sentence.",
            "max_tokens": 100,
        }
        for i in range(101)
    ]

    # === RUN BATCH JOB ===
    # 1. Prepare input
    local_input = manager.prepare_jsonl(prompts, "input_batch.jsonl")

    # 2. Upload to S3
    input_uri = f"s3://{CONFIG['bucket']}/{CONFIG['prefix']}/{job_name}/input.jsonl"
    output_uri = f"s3://{CONFIG['bucket']}/{CONFIG['prefix']}/{job_name}/output/"
    manager.upload_to_s3(local_input, input_uri)

    # 3. Submit job
    job_arn = manager.submit_job(
        job_name=job_name,
        model_id=CONFIG["model_id"],
        input_s3_uri=input_uri,
        output_s3_uri=output_uri,
        role_arn=CONFIG["role_arn"],
    )

    # 4. Wait for completion
    job_response = manager.wait_for_job(job_arn)

    # 5. Get results
    results = manager.get_results(job_response)

    # === DISPLAY RESULTS ===
    for r in results:
        record_id = r.get("recordId", "?")
        if "error" in r:
            print(f"[{record_id}] ERROR: {r['error']}")
        else:
            text = r.get("modelOutput", {}).get("content", [{}])[0].get("text", "")
            print(f"[{record_id}] {text[:100]}")


if __name__ == "__main__":
    main()
