from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_version: str = "1.2.0"
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/researchflow"
    llm_provider: str = "gemini"
    openai_api_key: str = ""
    openai_compatible_api_key: str = ""
    openai_compatible_base_url: str = ""
    openai_compatible_model: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    tavily_api_key: str = ""
    model_name: str = "gpt-4.1-mini"
    search_provider: str = "tavily"
    search_max_results: int = 3
    tavily_search_depth: str = "advanced"
    provider_timeout_seconds: float = 45.0
    worker_poll_interval: float = 2.0
    cors_allowed_origins: str = "*"

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_allowed_origins.split(",")]
        return [origin for origin in origins if origin] or ["*"]


settings = Settings()
