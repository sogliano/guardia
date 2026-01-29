from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://guardia:guardia_dev@localhost:5432/guardia"

    # Clerk Authentication
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_pem_public_key: str = ""

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

    # LLM - Claude (Primary)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-5-20251101"

    # LLM - OpenAI (Fallback)
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"

    # ML Model
    ml_model_path: str = "./ml_models/distilbert-guardia"
    ml_max_seq_length: int = 256

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"

    # Storage
    quarantine_storage_path: str = "./quarantine_store"

    model_config = {
        "env_file": ("../.env", ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    # Active users filter (Google Workspace per-user gateway)
    active_users: str = ""

    @property
    def accepted_domains_list(self) -> list[str]:
        return [d.strip() for d in self.accepted_domains.split(",") if d.strip()]

    @property
    def active_users_set(self) -> set[str]:
        return {u.strip().lower() for u in self.active_users.split(",") if u.strip()}


settings = Settings()
