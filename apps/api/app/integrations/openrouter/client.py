import asyncio
from dataclasses import dataclass, field
from time import monotonic

import httpx


class TokenBucket:
    def __init__(self, rate: int) -> None:
        self.rate = rate
        self.tokens = float(rate)
        self.last_refill = monotonic()

    async def acquire(self) -> None:
        now = monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.rate), self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens < 1:
            sleep_for = (1 - self.tokens) / self.rate
            await asyncio.sleep(sleep_for)
            self.tokens = 0.0
        else:
            self.tokens -= 1.0


@dataclass
class OpenRouterClient:
    api_key: str
    fallback_model: str = "google/gemini-2.5-flash-preview"
    rate_per_second: int = 5
    base_url: str = "https://openrouter.ai/api/v1"
    _bucket: TokenBucket = field(init=False)
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._bucket = TokenBucket(self.rate_per_second)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60)
        return self._client

    async def _post(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int | None,
    ) -> dict:
        await self._bucket.acquire()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        _is_retry: bool = False,
    ) -> dict:
        try:
            return await self._post(model, messages, temperature, max_tokens)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500 and self.fallback_model and not _is_retry:
                return await self.chat(
                    self.fallback_model, messages, temperature, max_tokens, _is_retry=True
                )
            raise
        except httpx.RequestError:
            if self.fallback_model and not _is_retry:
                return await self.chat(
                    self.fallback_model, messages, temperature, max_tokens, _is_retry=True
                )
            raise

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
