from datetime import UTC, datetime
from uuid import uuid4

import fitz
from PIL import Image

from dynno_customs_api.config import ROOT_DIR, settings
from dynno_customs_api.models.domain import DocumentFileRecord
from dynno_customs_api.services import tesseract_ocr
from dynno_customs_api.services.tesseract_ocr import TesseractOcrProvider, resolve_document_path, run_tesseract_ocr


def _test_dir():
    path = settings.temp_dir / "tests" / "ocr"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _document(stored_path: str, content_type: str = "image/png") -> DocumentFileRecord:
    return DocumentFileRecord(
        document_id=uuid4(),
        file_name="ocr-test.png",
        stored_path=stored_path,
        content_type=content_type,
        size_bytes=100,
        uploaded_at=datetime.now(UTC),
        sha256="a" * 64,
    )


def fake_image_to_data(image, lang, output_type):
    assert lang == settings.ocr_langs
    assert output_type == tesseract_ocr.pytesseract.Output.DICT
    return {
        "text": ["", "Invoice", "INV-001"],
        "conf": ["-1", "95", "85"],
        "block_num": [0, 1, 1],
        "par_num": [0, 1, 1],
        "line_num": [0, 1, 2],
    }


def test_run_tesseract_ocr_for_image(monkeypatch) -> None:
    image_path = _test_dir() / "ocr-test.png"
    Image.new("RGB", (120, 60), "white").save(image_path)

    monkeypatch.setattr(tesseract_ocr.pytesseract, "image_to_data", fake_image_to_data)

    result = run_tesseract_ocr(_document(str(image_path.relative_to(ROOT_DIR))))

    assert result.status == "completed"
    assert result.provider == "tesseract"
    assert result.raw_text == "Invoice\nINV-001"
    assert len(result.pages) == 1
    assert result.pages[0].confidence == 0.9
    assert result.pages[0].text == "Invoice\nINV-001"
    assert result.pages[0].image_width == 120
    assert result.pages[0].image_height == 60
    assert len(result.pages[0].lines) == 2
    assert result.pages[0].lines[0].text == "Invoice"
    assert result.pages[0].lines[0].line_no == 1
    assert result.pages[0].provider_metadata["word_count"] == 2
    assert result.provider_metadata["page_count"] == 1
    assert result.provider_metadata["embedded_text_appended"] is False


def test_assemble_structured_text_keeps_line_breaks() -> None:
    text = tesseract_ocr._assemble_structured_text(
        {
            "text": ["COMMERCIAL", "INVOICE", "INV-001", "DATE", "APR.13,2026"],
            "block_num": [1, 1, 1, 1, 1],
            "par_num": [1, 1, 1, 1, 1],
            "line_num": [1, 1, 2, 3, 3],
        }
    )

    assert text == "COMMERCIAL INVOICE\nINV-001\nDATE APR.13,2026"


def test_run_tesseract_ocr_fails_for_unsupported_file() -> None:
    text_path = _test_dir() / "unsupported.txt"
    text_path.write_text("not an image", encoding="utf-8")

    result = run_tesseract_ocr(_document(str(text_path.relative_to(ROOT_DIR)), "text/plain"))

    assert result.status == "failed"
    assert "Unsupported OCR content type" in result.error_message


def test_resolve_document_path_uses_repo_root_for_relative_paths() -> None:
    assert resolve_document_path("uploads/sample/invoice.pdf") == ROOT_DIR / "uploads" / "sample" / "invoice.pdf"


def test_run_tesseract_ocr_appends_embedded_pdf_text(monkeypatch) -> None:
    pdf_path = _test_dir() / "ocr-embedded.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "GROSS WEIGHT KGS 22088")
    document.save(pdf_path)
    document.close()

    monkeypatch.setattr(tesseract_ocr.pytesseract, "image_to_data", fake_image_to_data)

    result = run_tesseract_ocr(_document(str(pdf_path.relative_to(ROOT_DIR)), "application/pdf"))

    assert result.status == "completed"
    assert "Invoice\nINV-001" in result.raw_text
    assert "GROSS WEIGHT KGS 22088" in result.raw_text
    assert result.provider_metadata["embedded_text_appended"] is True


def test_tesseract_provider_calls_run_function(monkeypatch) -> None:
    image_path = _test_dir() / "provider-test.png"
    Image.new("RGB", (100, 40), "white").save(image_path)

    monkeypatch.setattr(tesseract_ocr.pytesseract, "image_to_data", fake_image_to_data)

    provider = TesseractOcrProvider()
    result = provider.process_document(_document(str(image_path.relative_to(ROOT_DIR))))

    assert provider.name == "tesseract"
    assert result.status == "completed"
