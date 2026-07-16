from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    ENV: str = "development"
    BACKEND_PORT: int = 8000
    PROXY_PORT: int = 9000

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "ai_waf"

    TARGET_URL: str = "http://localhost:3000"

    ML_MODEL_NAME: str = "distilbert-base-uncased"
    ML_ENABLED: bool = False
    ML_RISK_THRESHOLD: float = 0.75

    BLOCKCHAIN_ENABLED: bool = False
    WEB3_PROVIDER_URL: str = "http://127.0.0.1:8545"
    CONTRACT_ADDRESS: str = ""
    DEPLOYER_PRIVATE_KEY: str = ""
    BATCH_LOG_INTERVAL_SECONDS: int = 300
    BATCH_LOG_SIZE: int = 100

    JWT_SECRET: str = "change_this_to_a_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720

    GEOIP_ENABLED: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
