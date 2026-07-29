from io import BytesIO
from uuid import UUID

from fastapi.testclient import TestClient
from PIL import Image

from dynno_customs_api.main import app
from dynno_customs_api.services import tesseract_ocr
from dynno_customs_api.services.document_pack_store import document_pack_store
from dynno_customs_api.services.validation_report_store import validation_report_store


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (120, 60), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def _fake_invoice_ocr_data(image, lang, output_type):
    text = (
        "QINGDAO RAITTE TECHNOLOGIES CO.,LTD. COMMERCIAL INVOICE "
        "TO:000 SOYUZOPTHIM LTD DATE: APR.13,2026 INV.NO.: 26RT0004 "
        "ADD 68 // Contract Ne QRT-SOH dated 01.09.2025 "
        "POLYACRYLAMIDE StabVisco FNL1 18000.00KG CNY9.1000/MT CNY 163800.00 "
        "PACKING: IN NET 25KG BAG CNY 163800.00 For"
    )
    words = text.split()
    return {
        "text": words,
        "conf": ["95"] * len(words),
    }


def test_validation_run_endpoint_orchestrates_full_pipeline(monkeypatch, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(tesseract_ocr.pytesseract, "image_to_data", _fake_invoice_ocr_data)
    client = TestClient(app)

    response = client.post(
        "/api/validation-runs",
        files=[("files", ("invoice.png", _png_bytes(), "image/png"))],
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == body["report"]["report_id"]
    assert body["pack_id"] == body["report"]["pack_id"]
    assert body["summary"]["total_rules"] == 27
    assert body["documents"][0]["document_type"] == "invoice"
    assert body["documents"][0]["fields"]["invoice_no"]["value"] == "26RT0004"
    assert body["grouped_results"]["failed"]
    assert document_pack_store.get(UUID(body["pack_id"])).status == body["status"]

    latest_response = client.get(f"/api/validation-runs/{body['pack_id']}", headers=auth_headers)

    assert latest_response.status_code == 200
    assert latest_response.json()["run_id"] == body["run_id"]

    history_response = client.get("/api/validation-runs", headers=auth_headers)

    assert history_response.status_code == 200
    history_body = history_response.json()
    assert history_body["items"][0]["run_id"] == body["run_id"]
    assert history_body["items"][0]["pack_id"] == body["pack_id"]
    assert history_body["items"][0]["file_names"] == ["invoice.png"]


def test_validation_run_latest_endpoint_returns_404_for_missing_pack(auth_headers: dict[str, str]) -> None:
    client = TestClient(app)

    response = client.get("/api/validation-runs/00000000-0000-0000-0000-000000000000", headers=auth_headers)

    assert response.status_code == 404


def test_validation_report_endpoint_uses_shared_workflow(monkeypatch, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(tesseract_ocr.pytesseract, "image_to_data", _fake_invoice_ocr_data)
    client = TestClient(app)

    pack_response = client.post(
        "/api/document-packs",
        files=[("files", ("invoice.png", _png_bytes(), "image/png"))],
        headers=auth_headers,
    )

    assert pack_response.status_code == 200
    pack_id = pack_response.json()["pack_id"]

    response = client.post(f"/api/validation/reports/{pack_id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["pack_id"] == pack_id
    assert body["summary"]["total_rules"] == 27
    assert validation_report_store.get_latest(UUID(pack_id)) is not None
    assert document_pack_store.get(UUID(pack_id)).status in {"failed", "validated", "needs_review"}


def test_validation_run_routes_require_auth() -> None:
    client = TestClient(app)

    response = client.get("/api/validation-runs")

    assert response.status_code == 401
