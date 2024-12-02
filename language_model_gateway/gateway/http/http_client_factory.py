import httpx


class HttpClientFactory:
    # noinspection PyMethodMayBeStatic
    def create_http_client(self, base_url: str) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=base_url)
