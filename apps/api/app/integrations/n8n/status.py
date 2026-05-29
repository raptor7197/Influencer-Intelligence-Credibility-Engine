from dataclasses import dataclass

import httpx


@dataclass
class N8nStatusClient:
    base_url: str
    api_key: str | None = None
    _client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30)
        return self._client

    async def get_run_status(self, run_id: str) -> dict:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        client = await self._get_client()
        response = await client.get(f"{self.base_url}/executions/{run_id}", headers=headers)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
