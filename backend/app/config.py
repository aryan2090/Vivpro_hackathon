from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    es_url: str = "http://localhost:9200"
    es_index: str = "clinical_trials"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    model_config = {
        "env_file": ("../.env", ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
