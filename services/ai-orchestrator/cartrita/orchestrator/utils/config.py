# Cartrita AI OS - Configuration Settings
# Advanced Pydantic Settings with Environment Variable Support

"""
Configuration management for Cartrita AI OS.
Uses Pydantic v2 with advanced validation and environment variable support.
"""

import secrets
from pathlib import Path

from pydantic import (
    Field,
    HttpUrl,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic.networks import IPvAnyAddress
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5433, ge=1, le=65535, description="Database port")
    user: str = Field(default="robert-non-root", description="Database user")
    password: SecretStr = Field(
        default="punky1", description="Database password"
    )
    database: str = Field(default="cartrita_db", description="Database name")
    pool_size: int = Field(default=20, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(
        default=30, ge=0, le=100, description="Max overflow connections"
    )
    pool_timeout: int = Field(default=30, ge=1, description="Pool timeout in seconds")
    pool_recycle: int = Field(
        default=3600, ge=60, description="Pool recycle time in seconds"
    )

    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.database}"

    class Config:
        env_prefix = "POSTGRES_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    password: SecretStr | None = Field(default=None, description="Redis password")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    max_connections: int = Field(
        default=20, ge=1, le=100, description="Max Redis connections"
    )
    socket_timeout: int = Field(
        default=5, ge=1, description="Socket timeout in seconds"
    )
    socket_connect_timeout: int = Field(
        default=5, ge=1, description="Socket connect timeout"
    )
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")

    @property
    def url(self) -> str:
        """Generate Redis URL."""
        auth = f":{self.password.get_secret_value()}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    class Config:
        env_prefix = "REDIS_"


class AISettings(BaseSettings):
    """AI and ML configuration settings."""

    # OpenAI GPT-4.1 for Orchestrator
    openai_api_key: SecretStr = Field(
        ..., description="OpenAI API key for GPT-4.1 orchestrator"
    )
    openai_embeddings_api_key: SecretStr | None = Field(
        default=None, description="OpenAI embeddings API key"
    )
    openai_organization: str | None = Field(
        default=None, description="OpenAI organization ID"
    )
    openai_project: str | None = Field(default=None, description="OpenAI project ID")

    # Model configurations
    orchestrator_model: str = Field(
        default="gpt-4.1-turbo", description="GPT-4.1 model for orchestrator"
    )
    agent_model: str = Field(
        default="claude-3.5-sonnet-20241022",
        description="GPT-5 variant for agents",
    )
    embedding_model: str = Field(
        default="text-embedding-3-large", description="Embedding model"
    )

    # Model parameters
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Model temperature"
    )
    max_tokens: int = Field(
        default=4096, ge=1, le=32768, description="Maximum tokens per request"
    )
    top_p: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Top-p sampling parameter"
    )
    frequency_penalty: float = Field(
        default=0.0, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    presence_penalty: float = Field(
        default=0.0, ge=-2.0, le=2.0, description="Presence penalty"
    )

    # Agent limits
    max_concurrent_agents: int = Field(
        default=10, ge=1, le=50, description="Max concurrent agents"
    )
    agent_timeout: int = Field(
        default=300, ge=30, le=1800, description="Agent execution timeout"
    )
    max_agent_memory: str = Field(default="2GB", description="Max memory per agent")

    class Config:
        env_prefix = "AI_"


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32)),
        description="Secret key for JWT and encryption",
    )
    jwt_secret: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32)),
        description="JWT secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration: int = Field(
        default=3600, ge=300, le=86400, description="JWT expiration in seconds"
    )

    # API Key settings
    api_key_length: int = Field(default=32, ge=16, le=64, description="API key length")
    api_key_prefix: str = Field(default="ck_", description="API key prefix")

    # Encryption
    encryption_key: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_hex(32)),
        description="Encryption key for sensitive data",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow CORS credentials"
    )
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods",
    )
    cors_allow_headers: list[str] = Field(
        default=["*"], description="Allowed CORS headers"
    )

    # Rate limiting
    rate_limit_requests: int = Field(
        default=100, ge=1, description="Rate limit requests per window"
    )
    rate_limit_window: int = Field(
        default=60, ge=1, description="Rate limit window in seconds"
    )

    class Config:
        env_prefix = "SECURITY_"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""

    # OpenTelemetry
    otel_service_name: str = Field(
        default="cartrita-ai-orchestrator", description="OTel service name"
    )
    otel_service_version: str = Field(
        default="2.0.0", description="OTel service version"
    )
    otel_traces_exporter: str = Field(default="otlp", description="Traces exporter")
    otel_metrics_exporter: str = Field(default="otlp", description="Metrics exporter")
    otel_logs_exporter: str = Field(default="otlp", description="Logs exporter")

    # Jaeger
    jaeger_endpoint: HttpUrl | None = Field(default=None, description="Jaeger endpoint")
    jaeger_user: str | None = Field(default=None, description="Jaeger username")
    jaeger_password: SecretStr | None = Field(
        default=None, description="Jaeger password"
    )
    jaeger_host: str = Field(default="localhost", description="Jaeger host")
    jaeger_port: int = Field(default=6831, ge=1, le=65535, description="Jaeger port")

    # Prometheus
    prometheus_enabled: bool = Field(
        default=True, description="Enable Prometheus metrics"
    )
    prometheus_port: int = Field(
        default=8001, ge=1024, le=65535, description="Prometheus port"
    )
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=False, description="Enable tracing")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")
    log_file: Path | None = Field(default=None, description="Log file path")

    # Sentry
    sentry_dsn: SecretStr | None = Field(default=None, description="Sentry DSN")
    sentry_environment: str = Field(
        default="production", description="Sentry environment"
    )
    sentry_traces_sample_rate: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Sentry traces sample rate"
    )

    class Config:
        env_prefix = "MONITORING_"


class ExternalAPISettings(BaseSettings):
    """External API configuration settings."""

    # Search APIs
    tavily_api_key: SecretStr | None = Field(
        default=None, description="Tavily search API key"
    )
    serpapi_api_key: SecretStr | None = Field(default=None, description="SerpAPI key")

    # Knowledge APIs
    wolfram_alpha_api_key: SecretStr | None = Field(
        default=None, description="Wolfram Alpha API key"
    )
    wikipedia_user_agent: str = Field(
        default="Cartrita-AI-OS/2.0.0 (https://cartrita.ai)",
        description="Wikipedia user agent",
    )

    # Speech APIs
    deepgram_api_key: SecretStr | None = Field(
        default=None, description="Deepgram API key"
    )

    # LangSmith
    langchain_tracing_v2: bool = Field(
        default=True, description="Enable LangChain tracing v2"
    )
    langchain_api_key: SecretStr | None = Field(
        default=None, description="LangChain API key"
    )
    langchain_project: str = Field(
        default="cartrita-v2", description="LangChain project name"
    )
    langchain_endpoint: HttpUrl = Field(
        default="https://api.smith.langchain.com",
        description="LangChain endpoint",
    )

    # HuggingFace
    huggingface_token: SecretStr | None = Field(
        default=None, description="HuggingFace token"
    )
    huggingface_hub_token: SecretStr | None = Field(
        default=None, description="HuggingFace Hub token"
    )

    class Config:
        env_prefix = "EXTERNAL_"


class Settings(BaseSettings):
    """Main application settings combining all configuration sections."""

    # Application metadata
    app_name: str = Field(default="Cartrita AI OS", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    environment: str = Field(default="production", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")

    # Server settings
    host: IPvAnyAddress = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1024, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, le=16, description="Number of workers")

    # Paths
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent.parent
    )
    logs_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent.parent / "logs"
    )
    uploads_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent.parent / "uploads"
    )
    temp_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent.parent / "temp"
    )

    # Feature flags
    computer_use_enabled: bool = Field(
        default=True, description="Enable computer use functionality"
    )
    computer_use_safety_mode: str = Field(
        default="strict",
        pattern="^(strict|moderate|permissive)$",
        description="Computer use safety mode",
    )

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ai: AISettings = Field(default_factory=AISettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    external: ExternalAPISettings = Field(default_factory=ExternalAPISettings)

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: dict) -> dict:
        """Validate environment-specific settings."""
        environment = values.get("environment", "production")

        if environment == "development":
            # Relax some constraints for development
            values.setdefault("debug", True)
            values.setdefault("monitoring_log_level", "DEBUG")

        return values

    @field_validator("logs_dir", "uploads_dir", "temp_dir")
    @classmethod
    def create_directories(cls, path: str) -> str:
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_file = "/home/robbie/cartrita-ai-os/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"

        # Environment variable prefixes
        env_prefix = ""

        # Nested settings
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()
