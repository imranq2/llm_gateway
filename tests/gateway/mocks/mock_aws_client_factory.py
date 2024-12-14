from typing import override

import boto3

from language_model_gateway.gateway.aws.aws_client_factory import AwsClientFactory


class MockAwsClientFactory(AwsClientFactory):
    def __init__(self, *, aws_client: boto3.client) -> None:
        self.aws_client = aws_client
        assert self.aws_client is not None

    @override
    def create_client(self, *, service_name: str) -> boto3.client:
        return self.aws_client
