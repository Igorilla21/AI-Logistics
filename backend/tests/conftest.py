from __future__ import annotations

import os
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
TEST_DB_DIR = ROOT_DIR / ".tmp" / "pytest"
TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DYNNO_DATABASE_URL"] = f"sqlite+pysqlite:///{(TEST_DB_DIR / 'backend-tests.db').as_posix()}"

from dynno_customs_api.services.database import init_database
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.validation_report_store import validation_report_store


@pytest.fixture(autouse=True)
def reset_persistent_stores() -> None:
    init_database()
    document_pack_store.clear()
    validation_report_store.clear()
    yield

