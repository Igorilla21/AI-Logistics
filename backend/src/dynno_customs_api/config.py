from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = ROOT_DIR / "schemas"
TEMP_DIR = ROOT_DIR / ".tmp"
UPLOADS_DIR = ROOT_DIR / "uploads"


class Settings(BaseSettings):
    app_name: str = "Dynno Customs API"
    app_env: str = "development"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:5173"]
    schemas_dir: Path = SCHEMAS_DIR
    temp_dir: Path = TEMP_DIR
    uploads_dir: Path = UPLOADS_DIR

    model_config = SettingsConfigDict(
        env_prefix="DYNNO_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
