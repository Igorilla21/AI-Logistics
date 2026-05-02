from pathlib import Path

from dynno_customs_api.config import ROOT_DIR, settings


def test_ocr_settings_are_repo_local_by_default() -> None:
    assert settings.ocr_temp_dir == ROOT_DIR / ".tmp" / "ocr"
    assert settings.ocr_output_dir == ROOT_DIR / "storage" / "ocr"
    assert settings.ocr_temp_dir.is_relative_to(ROOT_DIR)
    assert settings.ocr_output_dir.is_relative_to(ROOT_DIR)


def test_tesseract_settings_have_safe_defaults() -> None:
    assert settings.ocr_langs == "eng+rus"
    assert settings.ocr_pdf_dpi == 300
    assert Path(settings.tesseract_cmd).name in {"tesseract", "tesseract.exe"}
