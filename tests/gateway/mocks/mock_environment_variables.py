from typing import override

from language_model_gateway.gateway.utilities.environment_variables import (
    EnvironmentVariables,
)


class MockEnvironmentVariables(EnvironmentVariables):
    @override
    @property
    def github_org(self) -> str:
        return "github_org"

    @override
    @property
    def github_token(self) -> str:
        return "github_token"
