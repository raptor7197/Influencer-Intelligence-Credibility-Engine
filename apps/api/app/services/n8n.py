from app.core.settings import Settings
from app.integrations.n8n.client import N8nClient
from app.integrations.n8n.status import N8nStatusClient


def build_n8n_client() -> N8nClient:
    settings = Settings()
    if not settings.n8n_webhook_url:
        raise ValueError("N8N_WEBHOOK_URL is required")
    return N8nClient(webhook_url=settings.n8n_webhook_url, api_key=settings.n8n_api_key)


def build_n8n_status_client() -> N8nStatusClient | None:
    settings = Settings()
    if not settings.n8n_base_url:
        return None
    return N8nStatusClient(base_url=settings.n8n_base_url, api_key=settings.n8n_api_key)
