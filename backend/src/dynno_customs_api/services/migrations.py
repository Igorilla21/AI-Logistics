from __future__ import annotations

from alembic import command
from alembic.config import Config

from dynno_customs_api.config import ROOT_DIR, settings
from dynno_customs_api.services.database import _ensure_database_parent_dir


def run_database_migrations() -> None:
    _ensure_database_parent_dir(settings.database_url)

    config = Config(str(ROOT_DIR / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT_DIR / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")
