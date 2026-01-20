from loguru import logger
import os
from typing import Tuple
from urllib.parse import urlparse
import boto3


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
