from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://agentshub:agentshub@localhost:5432/agentshub"
    embedding_provider: str = "gemini"  # gemini | ollama
    gemini_api_key: str = ""
    gemini_embedding_model: str = "text-embedding-004"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768

    environment: str = "dev"  # dev | staging | production
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    platform_wallet_address: str = ""
    platform_fee_bps: int = 200  # 2.00%
    escrow_hold_days: int = 30
    jwt_secret: str = ""
    secure_cookies: bool = False
    allow_demo_topup: bool = False
    jwt_exp_minutes: int = 60 * 24  # 1 day; refresh later
    x402_facilitator_url: str = "https://api.cdp.coinbase.com/platform/v2/x402"
    usdc_address: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    chain: str = "base"

    admin_email: str = ""
    admin_password: str = ""


settings = Settings()
