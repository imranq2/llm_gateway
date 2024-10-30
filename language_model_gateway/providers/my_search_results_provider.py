from typing import Any, Dict, List, Optional

from language_model_gateway.providers.results_provider import ResultsProvider


class MyResultsProvider(ResultsProvider):
    async def get_results_async(
        self,
        *,
        query_id: str,
        query: str,
        client: Optional[str] = None,
        test: bool = False,
    ) -> Dict[str, Any]:
        return {
            "total_count": 1,
            "results": [
                {
                    "result_id": 123
                }
            ]
        }
