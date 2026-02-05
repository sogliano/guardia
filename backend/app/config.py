import os

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings

_env = os.getenv("APP_ENV", "local")


class Settings(BaseSettings):
    # Application
    app_env: str = "local"
    app_debug: bool = True
    app_secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://guardia:guardia_dev@localhost:5432/guardia"

    # Clerk Authentication
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_pem_public_key: str = ""

    @field_validator("clerk_pem_public_key")
    @classmethod
    def validate_clerk_pem_public_key(cls, v: str) -> str:
        """Convert literal \\n in PEM key to actual newlines."""
        if not v:
            return v
        # Replace literal \n with actual newlines
        return v.replace("\\n", "\n")

    # SMTP Gateway
    smtp_host: str = "0.0.0.0"
    smtp_port: int = 2525
    smtp_domain: str = "guardia.strike.sh"
    smtp_tls_cert: str = ""
    smtp_tls_key: str = ""
    smtp_require_tls: bool = False

    # Google Workspace Relay
    google_relay_host: str = "aspmx.l.google.com"
    google_relay_port: int = 25
    accepted_domains: str = "strike.sh"

    # Pipeline
    threshold_allow: float = 0.3
    threshold_warn: float = 0.6
    threshold_quarantine: float = 0.8
    pipeline_timeout_seconds: int = 30
    pipeline_ml_enabled: bool = True

    # LLM - OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"

    # Pipeline Allowlist (full bypass for trusted domains)
    allowlist_domains: str = "strike.sh"
    allowlist_require_spf: bool = True
    allowlist_require_dkim: bool = False
    allowlist_require_dmarc: bool = False

    @property
    def allowlist_domains_set(self) -> set[str]:
        return {d.strip().lower() for d in self.allowlist_domains.split(",") if d.strip()}

    # ML Model
    ml_model_path: str = "./ml_models/distilbert-guardia"
    ml_model_hf_repo: str = "guardia-project/distilbert-guardia-v2"
    ml_max_seq_length: int = 256

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"

    # Storage
    quarantine_storage_path: str = "./quarantine_store"

    model_config = {
        "env_file": (f"../.env.{_env}", f".env.{_env}", "../.env", ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str, info: ValidationInfo) -> str:
        """Validar que CORS origins no sea wildcard en producción."""
        if "*" in v:
            raise ValueError("CORS wildcard (*) no permitido")

        origins = [o.strip() for o in v.split(",") if o.strip()]
        for origin in origins:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"CORS origin inválido: {origin}")

            # En producción, solo HTTPS
            env = info.data.get("app_env", "local")
            if env == "production" and origin.startswith("http://"):
                raise ValueError(f"CORS origin en producción debe usar HTTPS: {origin}")

        return v

    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_storage_uri: str = "memory://"

    # Slack Alerts
    slack_webhook_url: str = ""
    frontend_base_url: str = "http://localhost:3000"

    # Active users filter (Google Workspace per-user gateway)
    active_users: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def accepted_domains_list(self) -> list[str]:
        return [d.strip() for d in self.accepted_domains.split(",") if d.strip()]

    @property
    def active_users_set(self) -> set[str]:
        return {u.strip().lower() for u in self.active_users.split(",") if u.strip()}


settings = Settings()
