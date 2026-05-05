from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = ROOT_DIR / "schemas"
TEMP_DIR = ROOT_DIR / ".tmp"
UPLOADS_DIR = ROOT_DIR / "uploads"
OCR_TEMP_DIR = TEMP_DIR / "ocr"
OCR_OUTPUT_DIR = ROOT_DIR / "storage" / "ocr"
DEFAULT_TESSERACT_CMD = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if not DEFAULT_TESSERACT_CMD.exists():
    DEFAULT_TESSERACT_CMD = Path("tesseract")


class Settings(BaseSettings):
    app_name: str = "Dynno Customs API"
    app_env: str = "development"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    schemas_dir: Path = SCHEMAS_DIR
    temp_dir: Path = TEMP_DIR
    uploads_dir: Path = UPLOADS_DIR
    ocr_temp_dir: Path = OCR_TEMP_DIR
    ocr_output_dir: Path = OCR_OUTPUT_DIR
    tesseract_cmd: Path | str = DEFAULT_TESSERACT_CMD
    ocr_langs: str = "eng+rus"
    ocr_pdf_dpi: int = 300

    model_config = SettingsConfigDict(
        env_prefix="DYNNO_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
