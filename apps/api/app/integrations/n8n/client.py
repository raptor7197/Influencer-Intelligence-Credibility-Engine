from dataclasses import dataclass, field

import httpx


@dataclass
class N8nClient:
    webhook_url: str
    api_key: str | None = None
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=300)
        return self._client

    async def trigger_discovery(self, payload: dict) -> dict:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        client = await self._get_client()
        response = await client.post(self.webhook_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
