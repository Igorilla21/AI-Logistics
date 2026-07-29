from io import BytesIO
from uuid import UUID

from fastapi.testclient import TestClient
from PIL import Image

from dynno_customs_api.main import app
from dynno_customs_api.services import tesseract_ocr
from dynno_customs_api.services.document_pack_store import document_pack_store


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (120, 60), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def _fake_image_to_data(image, lang, output_type):
    return {
        "text": ["", "Invoice", "INV-001"],
        "conf": ["-1", "95", "85"],
    }


def test_document_pack_ocr_endpoints(monkeypatch, auth_headers: dict[str, str]) -> None:
    monkeypatch.setattr(tesseract_ocr.pytesseract, "image_to_data", _fake_image_to_data)
    client = TestClient(app)

    create_response = client.post(
        "/api/document-packs",
        files=[("files", ("invoice.png", _png_bytes(), "image/png"))],
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    pack_id = create_response.json()["pack_id"]

    ocr_response = client.post(f"/api/document-packs/{pack_id}/ocr", headers=auth_headers)

    assert ocr_response.status_code == 200
    ocr_body = ocr_response.json()
    assert ocr_body["pack_id"] == pack_id
    assert ocr_body["items"][0]["status"] == "completed"
    assert ocr_body["items"][0]["raw_text"] == "Invoice INV-001"
    assert ocr_body["items"][0]["raw_text_ref"].startswith("storage")
    assert document_pack_store.get(UUID(pack_id)).status == "ocr_completed"

    get_response = client.get(f"/api/document-packs/{pack_id}/ocr-results", headers=auth_headers)

    assert get_response.status_code == 200
    assert get_response.json()["items"][0]["raw_text"] == "Invoice INV-001"


def test_document_pack_ocr_endpoint_returns_404_for_missing_pack(auth_headers: dict[str, str]) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/document-packs/00000000-0000-0000-0000-000000000000/ocr",
        headers=auth_headers,
    )

    assert response.status_code == 404
