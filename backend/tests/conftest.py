from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[2]
TEST_DB_DIR = ROOT_DIR / ".tmp" / "pytest"
TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DYNNO_DATABASE_URL"] = f"sqlite+pysqlite:///{(TEST_DB_DIR / 'backend-tests.db').as_posix()}"

from dynno_customs_api.services.database import init_database
from dynno_customs_api.services.auth_store import auth_store
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.validation_report_store import validation_report_store
from dynno_customs_api.main import app


@pytest.fixture(autouse=True)
def reset_persistent_stores() -> None:
    init_database()
    auth_store.clear()
    document_pack_store.clear()
    validation_report_store.clear()
    yield


@pytest.fixture
def auth_headers() -> dict[str, str]:
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={
            "email": "admin@example.com",
            "password": "StrongPass123",
            "full_name": "Admin User",
        },
    )

    assert response.status_code == 201
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}
