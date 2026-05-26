from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    redis_url: str = "redis://localhost:6379"  # reserved for future queue scaling
    db_path: str = "./app/db/jobs.db"
    api_key: str = "changeme"
    log_level: str = "INFO"
    max_concurrent_jobs: int = 5
    max_job_retries: int = 3
    worker_poll_interval: float = 5.0


settings = Settings()
