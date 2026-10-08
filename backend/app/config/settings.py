from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================================================
    # GENERAL
    # =========================================================

    ENV: str = "development"

    BACKEND_PORT: int = 8000
    PROXY_PORT: int = 9000


    # =========================================================
    # DATABASE
    # =========================================================

    MONGO_URI: str = "mongodb://localhost:27017"

    MONGO_DB_NAME: str = "ai_waf"


    # =========================================================
    # REVERSE PROXY / TARGET
    # =========================================================

    TARGET_URL: str = "http://localhost:3000"


    # =========================================================
    # MACHINE LEARNING
    # =========================================================

    ML_MODEL_NAME: str = "distilbert-base-uncased"

    # Enable DEFENZA AI
    ML_ENABLED: bool = True

    ML_RISK_THRESHOLD: float = 0.75


    # =========================================================
    # CONTEXT-AWARE RISK SCORING
    # =========================================================

    SENSITIVE_ENDPOINT_BONUS: float = 0.15

    POST_REQUEST_BONUS: float = 0.10

    HIGH_RISK_METHOD_BONUS: float = 0.15


    # =========================================================
    # SENSITIVE ENDPOINTS
    # =========================================================

    SENSITIVE_ENDPOINTS: list[str] = [
        "/admin",
        "/login",
        "/signin",
        "/auth",
        "/dashboard",
        "/config",
        "/api/auth",
        "/phpmyadmin",
        "/wp-admin",
    ]


    # =========================================================
    # BLOCKCHAIN
    # =========================================================

    BLOCKCHAIN_ENABLED: bool = False

    WEB3_PROVIDER_URL: str = (
        "http://127.0.0.1:8545"
    )

    CONTRACT_ADDRESS: str = ""

    DEPLOYER_PRIVATE_KEY: str = ""

    BATCH_LOG_INTERVAL_SECONDS: int = 300

    BATCH_LOG_SIZE: int = 100


    # =========================================================
    # AUTHENTICATION
    # =========================================================

    JWT_SECRET: str = (
        "change_this_to_a_long_random_string"
    )

    JWT_ALGORITHM: str = "HS256"

    JWT_EXPIRE_MINUTES: int = 720


    # =========================================================
    # INTERNAL PROXY COMMUNICATION
    # =========================================================

    # Shared secret used by the reverse proxy when
    # communicating with the backend AI analysis endpoint.

    INTERNAL_API_KEY: str = (
        "defenza-internal-change-this-key"
    )


    # =========================================================
    # GEOIP
    # =========================================================

    GEOIP_ENABLED: bool = False


    # =========================================================
    # PYDANTIC SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# =============================================================
# SETTINGS INSTANCE
# =============================================================

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()