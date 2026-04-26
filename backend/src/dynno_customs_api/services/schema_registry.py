import json
from pathlib import Path

from dynno_customs_api.config import settings


def _schema_path(schema_name: str) -> Path:
    schema_file = settings.schemas_dir / schema_name
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema '{schema_name}' not found.")
    return schema_file


def list_schema_names() -> list[str]:
    return sorted(path.name for path in settings.schemas_dir.glob("*.json"))


def read_schema(schema_name: str) -> dict:
    schema_file = _schema_path(schema_name)
    return json.loads(schema_file.read_text(encoding="utf-8"))
