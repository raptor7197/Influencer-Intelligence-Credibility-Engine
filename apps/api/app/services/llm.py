from app.core.settings import Settings
from app.integrations.openrouter.client import OpenRouterClient


def build_openrouter_client() -> OpenRouterClient:
    settings = Settings()
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is required")
    return OpenRouterClient(
        api_key=settings.openrouter_api_key,
        fallback_model=settings.openrouter_fallback_model,
        rate_per_second=settings.openrouter_rate_per_second,
    )
