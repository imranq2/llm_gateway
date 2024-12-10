import os

import boto3


class AwsClientFactory:
    # noinspection PyMethodMayBeStatic
    def create_client(self, *, service_name: str) -> boto3.client:
        """Create and return a Bedrock client"""
        session = boto3.Session(profile_name=os.environ.get("AWS_CREDENTIALS_PROFILE"))
        bedrock_client = session.client(
            service_name=service_name,
            region_name="us-east-1",
        )
        return bedrock_client
