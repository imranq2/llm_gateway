import httpx

from language_model_gateway.gateway.http.http_client_factory import HttpClientFactory


class MockHttpClientFactory(HttpClientFactory):
    def __init__(self, *, http_client: httpx.AsyncClient) -> None:
        self.http_client: httpx.AsyncClient = http_client
        assert self.http_client is not None
        assert isinstance(self.http_client, httpx.AsyncClient)

    def create_http_client(self, base_url: str) -> httpx.AsyncClient:
        return self.http_client
