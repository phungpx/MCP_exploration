SYSTEM_PROMPT = """You are an expert Python developer with deep knowledge of AWS services, 
cloud architecture, and software engineering best practices. You specialize in:

1. Building scalable serverless applications using AWS Lambda, API Gateway, and DynamoDB
2. Implementing robust error handling and retry mechanisms
3. Optimizing performance and cost efficiency in cloud environments
4. Following security best practices including least privilege and encryption
5. Writing clean, maintainable, and well-documented code
6. Implementing comprehensive testing strategies
7. Using infrastructure as code with AWS CDK and CloudFormation
8. Designing event-driven architectures with EventBridge and SQS
9. Monitoring and observability with CloudWatch and X-Ray
10. CI/CD pipelines with CodePipeline and GitHub Actions

Your responses should be practical, actionable, and include code examples when relevant.
Always consider cost optimization, security, and scalability in your recommendations.
"""

DOCUMENT_GENERATION_PROMPT = """
# AWS Lambda Best Practices Documentation

## Error Handling Patterns

### 1. Exponential Backoff
When dealing with transient failures, implement exponential backoff:

```python
import time
import random

def exponential_backoff(attempt, base_delay=1, max_delay=60):
    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
    time.sleep(delay)
    return delay

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = exponential_backoff(attempt)
            print(f"Retry {attempt + 1} after {delay:.2f}s due to: {e}")
```

### 2. Circuit Breaker Pattern
Prevent cascading failures by implementing circuit breakers:

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func):
        if self.state == 'open':
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func()
            if self.state == 'half-open':
                self.state = 'closed'
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()
            if self.failures >= self.failure_threshold:
                self.state = 'open'
            raise
```

## Async Operations

### 1. Using asyncio for Concurrent Operations

```python
import asyncio
import aiohttp

async def fetch_data(session, url):
    async with session.get(url) as response:
        return await response.json()

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Usage
urls = ['https://api.example.com/1', 'https://api.example.com/2']
results = asyncio.run(fetch_all(urls))
```

### 2. AWS Lambda Async Invocations

```python
import boto3
import json

lambda_client = boto3.client('lambda')

def invoke_async(function_name, payload):
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='Event',  # Async invocation
        Payload=json.dumps(payload)
    )
    return response['StatusCode'] == 202
```

## DynamoDB Optimization

### Batch Operations

```python
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('MyTable')

def batch_write_items(items):
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

def batch_get_items(keys):
    response = dynamodb.batch_get_item(
        RequestItems={
            'MyTable': {
                'Keys': keys,
                'ConsistentRead': True
            }
        }
    )
    return response['Responses']['MyTable']
```

## Cost Optimization Strategies

1. Use provisioned concurrency only when needed
2. Implement proper memory sizing based on actual usage
3. Leverage Lambda layers for shared dependencies
4. Use S3 lifecycle policies for data archival
5. Implement caching with ElastiCache or DAX
6. Use spot instances for non-critical workloads
7. Enable cost allocation tags
8. Monitor with Cost Explorer and set budgets

## Security Best Practices

1. Never hardcode credentials - use IAM roles
2. Enable encryption at rest and in transit
3. Implement least privilege access
4. Use VPC endpoints for private connectivity
5. Enable CloudTrail for audit logging
6. Implement input validation and sanitization
7. Use AWS Secrets Manager for sensitive data
8. Enable MFA for privileged operations

## Monitoring and Observability

```python
import logging
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Patch libraries for X-Ray tracing
patch_all()

@xray_recorder.capture('process_event')
def lambda_handler(event, context):
    logger.info(f"Processing event: {event}")
    
    # Add metadata to X-Ray trace
    xray_recorder.put_metadata('user_id', event.get('user_id'))
    xray_recorder.put_annotation('event_type', event.get('type'))
    
    try:
        result = process_business_logic(event)
        logger.info(f"Successfully processed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)
        raise
```

This documentation covers the essential patterns and practices for building
production-ready serverless applications on AWS.
"""
