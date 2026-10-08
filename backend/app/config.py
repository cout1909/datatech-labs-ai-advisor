from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = "openai/gpt-oss-20b"
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = ""
    database_url: str = f"sqlite:///{(BASE_DIR / 'storage/advisor.db').as_posix()}"
    rate_limit_per_minute: int = Field(default=10, ge=1, le=1000)
    max_concurrent_requests: int = Field(default=2, ge=1, le=10)
    model_config = SettingsConfigDict(env_file=(BASE_DIR.parent / ".env", BASE_DIR / ".env"), extra="ignore")

    @property
    def allowed_origins(self):
        return [origin.strip().rstrip('/') for origin in (self.cors_origins or self.frontend_url).split(',') if origin.strip()]

settings = Settings()
