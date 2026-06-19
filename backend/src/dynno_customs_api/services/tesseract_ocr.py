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
from dynno_customs_api.models.domain import (
    BoundingBoxRecord,
    DocumentFileRecord,
    OcrDocumentResultRecord,
    OcrPageResultRecord,
    OcrTextLineRecord,
)


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
OCR_ORIENTATION_RETRY_DEGREES = (180, 90, 270)
OCR_SIGNAL_WORDS = (
    "addendum",
    "analysis",
    "batch",
    "bill",
    "certificate",
    "commercial",
    "container",
    "date",
    "expiry",
    "invoice",
    "lot",
    "manufacture",
    "manufacturing",
    "packing",
    "production",
)


class TesseractOcrProvider:
    name = "tesseract"

    def process_document(self, document: DocumentFileRecord) -> OcrDocumentResultRecord:
        return run_tesseract_ocr(document)


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
        embedded_text = _extract_embedded_pdf_text(source_path, document.content_type)
        if embedded_text and embedded_text not in raw_text:
            raw_text = "\n\n".join(part for part in [raw_text, embedded_text] if part)
        return OcrDocumentResultRecord(
            document_id=document.document_id,
            source_file_name=document.file_name,
            source_file_path=str(source_path),
            provider="tesseract",
            languages=settings.ocr_langs,
            status="completed",
            pages=pages,
            raw_text=raw_text,
            provider_metadata={
                "content_type": document.content_type,
                "embedded_text_appended": bool(embedded_text),
                "page_count": len(pages),
            },
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
            provider_metadata={
                "content_type": document.content_type,
            },
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


def _extract_embedded_pdf_text(source_path: Path, content_type: str) -> str:
    normalized_content_type = content_type.lower()
    if normalized_content_type not in PDF_CONTENT_TYPES and source_path.suffix.lower() != ".pdf":
        return ""

    lines: list[str] = []
    with fitz.open(source_path) as pdf_document:
        for page in pdf_document:
            text = page.get_text()
            if not text:
                continue
            normalized = _normalize_pdf_text(text)
            if normalized:
                lines.append(normalized)
    return "\n\n".join(lines)


def _ocr_image(*, page_no: int, image: Image.Image) -> OcrPageResultRecord:
    original = _ocr_image_once(page_no=page_no, image=image, rotation_degrees=0)
    if not _needs_orientation_retry(original):
        return original

    candidates = [original]
    for rotation_degrees in OCR_ORIENTATION_RETRY_DEGREES:
        rotated_image = image.rotate(rotation_degrees, expand=True)
        candidates.append(_ocr_image_once(page_no=page_no, image=rotated_image, rotation_degrees=rotation_degrees))
    return max(candidates, key=_ocr_quality_key)


def _ocr_image_once(*, page_no: int, image: Image.Image, rotation_degrees: int) -> OcrPageResultRecord:
    data = pytesseract.image_to_data(
        image,
        lang=settings.ocr_langs,
        output_type=pytesseract.Output.DICT,
    )
    lines = _extract_line_records(page_no=page_no, data=data)
    text = "\n".join(line.text for line in lines)
    word_count = sum(1 for raw_word in data.get("text", []) if str(raw_word).strip())
    signal_count = _ocr_signal_count(text)
    return OcrPageResultRecord(
        page_no=page_no,
        text=text,
        confidence=_average_confidence(data),
        image_width=image.width,
        image_height=image.height,
        lines=lines,
        provider_metadata={
            "word_count": word_count,
            "rotation_degrees": rotation_degrees,
            "signal_word_count": signal_count,
        },
    )


def _needs_orientation_retry(page: OcrPageResultRecord) -> bool:
    word_count = int(page.provider_metadata.get("word_count", 0))
    signal_count = int(page.provider_metadata.get("signal_word_count", 0))
    confidence = page.confidence or 0.0
    if word_count < 8:
        return True
    if confidence < 0.72:
        return True
    return word_count >= 40 and signal_count == 0 and confidence < 0.82


def _ocr_quality_key(page: OcrPageResultRecord) -> tuple[int, float, int]:
    word_count = int(page.provider_metadata.get("word_count", 0))
    signal_count = int(page.provider_metadata.get("signal_word_count", 0))
    confidence = page.confidence or 0.0
    return signal_count, confidence, word_count


def _ocr_signal_count(text: str) -> int:
    normalized = text.lower()
    return sum(1 for word in OCR_SIGNAL_WORDS if word in normalized)


def _assemble_structured_text(data: dict[str, list[Any]]) -> str:
    return "\n".join(line.text for line in _extract_line_records(page_no=1, data=data))


def _extract_line_records(*, page_no: int, data: dict[str, list[Any]]) -> list[OcrTextLineRecord]:
    words = data.get("text", [])
    if not words:
        return []

    block_nums = data.get("block_num", [])
    par_nums = data.get("par_num", [])
    line_nums = data.get("line_num", [])
    lefts = data.get("left", [])
    tops = data.get("top", [])
    widths = data.get("width", [])
    heights = data.get("height", [])
    confidences = data.get("conf", [])

    if not block_nums or not par_nums or not line_nums:
        flat_text = " ".join(str(word).strip() for word in words if str(word).strip())
        return [OcrTextLineRecord(page_no=page_no, text=flat_text, word_count=len(flat_text.split()))] if flat_text else []

    line_rows: list[dict[str, Any]] = []
    current_words: list[str] = []
    current_confidences: list[float] = []
    current_key: tuple[int, int, int] | None = None
    current_lefts: list[int] = []
    current_tops: list[int] = []
    current_rights: list[int] = []
    current_bottoms: list[int] = []

    def flush_current() -> None:
        nonlocal current_words, current_confidences, current_key, current_lefts, current_tops, current_rights, current_bottoms
        if not current_words or current_key is None:
            return

        bounding_box = None
        if (
            current_lefts
            and current_tops
            and current_rights
            and current_bottoms
            and max(current_rights) > min(current_lefts)
            and max(current_bottoms) > min(current_tops)
        ):
            bounding_box = BoundingBoxRecord(
                x=float(min(current_lefts)),
                y=float(min(current_tops)),
                width=float(max(current_rights) - min(current_lefts)),
                height=float(max(current_bottoms) - min(current_tops)),
            )

        line_rows.append(
            {
                "block_no": current_key[0],
                "paragraph_no": current_key[1],
                "line_no": current_key[2],
                "text": " ".join(current_words),
                "confidence": round(sum(current_confidences) / len(current_confidences), 4) if current_confidences else None,
                "word_count": len(current_words),
                "bounding_box": bounding_box,
            }
        )
        current_words = []
        current_confidences = []
        current_key = None
        current_lefts = []
        current_tops = []
        current_rights = []
        current_bottoms = []

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
            flush_current()
            current_key = key

        current_words.append(word)
        confidence = _safe_confidence(confidences, index)
        if confidence is not None:
            current_confidences.append(confidence)

        if index < len(lefts) and index < len(tops) and index < len(widths) and index < len(heights):
            left = _safe_ocr_index(lefts, index)
            top = _safe_ocr_index(tops, index)
            width = _safe_ocr_index(widths, index)
            height = _safe_ocr_index(heights, index)
            current_lefts.append(left)
            current_tops.append(top)
            current_rights.append(left + width)
            current_bottoms.append(top + height)

    flush_current()

    return [
        OcrTextLineRecord(
            page_no=page_no,
            text=item["text"],
            confidence=item["confidence"],
            block_no=item["block_no"],
            paragraph_no=item["paragraph_no"],
            line_no=item["line_no"],
            word_count=item["word_count"],
            bounding_box=item["bounding_box"],
        )
        for item in line_rows
    ]


def _normalize_pdf_text(text: str) -> str:
    normalized_lines = [" ".join(str(line).split()) for line in text.splitlines()]
    return "\n".join(line for line in normalized_lines if line)


def _safe_ocr_index(values: list[Any], index: int) -> int:
    try:
        return int(values[index])
    except (IndexError, TypeError, ValueError):
        return 0


def _average_confidence(data: dict[str, list[Any]]) -> float | None:
    values: list[float] = []
    for raw_confidence in data.get("conf", []):
        confidence = _normalize_confidence(raw_confidence)
        if confidence is not None:
            values.append(confidence)

    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _safe_confidence(values: list[Any], index: int) -> float | None:
    try:
        return _normalize_confidence(values[index])
    except IndexError:
        return None


def _normalize_confidence(raw_confidence: Any) -> float | None:
    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError):
        return None
    if confidence < 0:
        return None
    return confidence / 100 if confidence > 1 else confidence
