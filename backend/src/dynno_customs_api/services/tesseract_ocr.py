from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import fitz
import pytesseract
from PIL import Image, UnidentifiedImageError

from dynno_customs_api.config import ROOT_DIR, settings
from dynno_customs_api.models.domain import DocumentFileRecord, OcrDocumentResultRecord, OcrPageResultRecord


IMAGE_CONTENT_TYPES = {
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/tiff",
    "image/webp",
}
PDF_CONTENT_TYPES = {"application/pdf"}
IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def run_tesseract_ocr(document: DocumentFileRecord) -> OcrDocumentResultRecord:
    created_at = datetime.now(UTC)
    source_path = resolve_document_path(document.stored_path)
    pytesseract.pytesseract.tesseract_cmd = str(settings.tesseract_cmd)

    try:
        settings.ocr_temp_dir.mkdir(parents=True, exist_ok=True)
        settings.ocr_output_dir.mkdir(parents=True, exist_ok=True)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        pages = [
            _ocr_image(page_no=page_no, image=image)
            for page_no, image in _iter_page_images(source_path=source_path, content_type=document.content_type)
        ]
        raw_text = "\n\n".join(page.text for page in pages if page.text)
        return OcrDocumentResultRecord(
            document_id=document.document_id,
            source_file_name=document.file_name,
            source_file_path=str(source_path),
            provider="tesseract",
            languages=settings.ocr_langs,
            status="completed",
            pages=pages,
            raw_text=raw_text,
            created_at=created_at,
        )
    except Exception as exc:
        return OcrDocumentResultRecord(
            document_id=document.document_id,
            source_file_name=document.file_name,
            source_file_path=str(source_path),
            provider="tesseract",
            languages=settings.ocr_langs,
            status="failed",
            error_message=str(exc),
            created_at=created_at,
        )


def resolve_document_path(stored_path: str) -> Path:
    source_path = Path(stored_path)
    if source_path.is_absolute():
        return source_path
    return ROOT_DIR / source_path


def _iter_page_images(*, source_path: Path, content_type: str) -> Iterator[tuple[int, Image.Image]]:
    normalized_content_type = content_type.lower()
    suffix = source_path.suffix.lower()

    if normalized_content_type in PDF_CONTENT_TYPES or suffix == ".pdf":
        yield from _iter_pdf_page_images(source_path)
        return

    if normalized_content_type in IMAGE_CONTENT_TYPES or suffix in IMAGE_SUFFIXES:
        try:
            with Image.open(source_path) as image:
                yield 1, image.convert("RGB").copy()
        except UnidentifiedImageError as exc:
            raise ValueError(f"Unsupported or corrupt image file: {source_path}") from exc
        return

    raise ValueError(f"Unsupported OCR content type: {content_type}")


def _iter_pdf_page_images(source_path: Path) -> Iterator[tuple[int, Image.Image]]:
    zoom = settings.ocr_pdf_dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(source_path) as pdf_document:
        for page_index, page in enumerate(pdf_document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png"))).convert("RGB")
            yield page_index, image


def _ocr_image(*, page_no: int, image: Image.Image) -> OcrPageResultRecord:
    data = pytesseract.image_to_data(
        image,
        lang=settings.ocr_langs,
        output_type=pytesseract.Output.DICT,
    )
    text = _assemble_structured_text(data)
    return OcrPageResultRecord(
        page_no=page_no,
        text=text,
        confidence=_average_confidence(data),
        image_width=image.width,
        image_height=image.height,
    )


def _assemble_structured_text(data: dict[str, list[Any]]) -> str:
    words = data.get("text", [])
    if not words:
        return ""

    block_nums = data.get("block_num", [])
    par_nums = data.get("par_num", [])
    line_nums = data.get("line_num", [])

    if not block_nums or not par_nums or not line_nums:
        return " ".join(str(word).strip() for word in words if str(word).strip())

    lines: list[str] = []
    current_words: list[str] = []
    current_key: tuple[int, int, int] | None = None

    for index, raw_word in enumerate(words):
        word = str(raw_word).strip()
        if not word:
            continue

        key = (
            _safe_ocr_index(block_nums, index),
            _safe_ocr_index(par_nums, index),
            _safe_ocr_index(line_nums, index),
        )

        if current_key is None:
            current_key = key
        elif key != current_key:
            if current_words:
                lines.append(" ".join(current_words))
            current_words = []
            current_key = key

        current_words.append(word)

    if current_words:
        lines.append(" ".join(current_words))

    return "\n".join(lines)


def _safe_ocr_index(values: list[Any], index: int) -> int:
    try:
        return int(values[index])
    except (IndexError, TypeError, ValueError):
        return 0


def _average_confidence(data: dict[str, list[Any]]) -> float | None:
    values: list[float] = []
    for raw_confidence in data.get("conf", []):
        try:
            confidence = float(raw_confidence)
        except (TypeError, ValueError):
            continue
        if confidence < 0:
            continue
        values.append(confidence / 100 if confidence > 1 else confidence)

    if not values:
        return None
    return round(sum(values) / len(values), 4)
