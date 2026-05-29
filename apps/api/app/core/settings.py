from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "iice-api"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str
    n8n_webhook_url: str
    n8n_base_url: str | None = None
    n8n_api_key: str | None = None
    serper_api_key: str = ""
    openrouter_api_key: str | None = None
    llm_mode: str = "stub"
    openrouter_model_evidence: str = "xai/grok-2-latest"
    openrouter_model_scoring: str = "xai/grok-2-latest"
    openrouter_fallback_model: str = "google/gemini-2.5-flash"
    openrouter_max_tokens_evidence: int = 600
    openrouter_max_tokens_scoring: int = 600
    openrouter_rate_per_second: int = 5
