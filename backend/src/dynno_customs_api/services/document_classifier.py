from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(slots=True)
class ClassificationResult:
    document_type: str
    confidence: float
    classifier: str


DOCUMENT_TYPE_RULES: list[tuple[str, tuple[str, ...], tuple[str, ...], float]] = [
    (
        "payment_confirmation",
        ("mt103", "swift", "bankslip", "bankslip", "payment", "pp", "пп"),
        ("bank slip", "swift copy", "payment confirmation"),
        0.95,
    ),
    (
        "packing_list",
        ("packing", "packinglist", "packlist", "pkl", "pl"),
        ("packing list",),
        0.95,
    ),
    (
        "transport_invoice",
        ("transportinvoice", "freightinvoice"),
        ("transport invoice", "freight invoice", "rail freight"),
        0.88,
    ),
    (
        "invoice",
        ("invoice", "commercialinvoice", "ci", "inv"),
        ("commercial invoice",),
        0.92,
    ),
    (
        "addendum",
        ("addendum", "appendix", "supplement", "add"),
        tuple(),
        0.92,
    ),
    ("contract", ("contract", "agreement"), ("sales contract",), 0.90),
    (
        "coa",
        ("coa", "certificateofanalysis"),
        ("certificate of analysis",),
        0.95,
    ),
    (
        "hbl",
        ("hbl", "housebill"),
        ("house bill", "house bill of lading"),
        0.95,
    ),
    (
        "mbl",
        ("mbl", "masterbill", "bl", "seawaybill", "swb"),
        ("master bill", "bill of lading", "sea waybill", "surrender bl"),
        0.90,
    ),
    (
        "certificate_of_origin",
        ("certificateoforigin", "coo", "co"),
        ("certificate of origin",),
        0.82,
    ),
]

TEXT_TYPE_RULES: list[tuple[str, tuple[str, ...], float]] = [
    ("payment_confirmation", ("ordering customer", "swift copy", "mt103", "payment order"), 0.96),
    ("packing_list", ("packing list",), 0.97),
    ("invoice", ("commercial invoice",), 0.97),
    ("addendum", ("addendum no", "addendum n", "addendum dated"), 0.96),
    ("contract", ("sales contract", "purchase contract", "contract no"), 0.88),
    ("coa", ("certificate of analysis", "batch no", "manufacture date", "expiry date"), 0.95),
    ("hbl", ("house bill of lading",), 0.97),
    ("mbl", ("bill of lading", "seaway bill", "sea waybill"), 0.95),
    ("transport_invoice", ("freight invoice", "transport invoice"), 0.92),
    ("certificate_of_origin", ("certificate of origin",), 0.95),
]


def classify_document(file_name: str, content_type: str | None = None, raw_text: str | None = None) -> ClassificationResult:
    normalized_name, compact_name, tokens = _normalize_filename(file_name)

    for document_type, token_keywords, phrase_keywords, confidence in DOCUMENT_TYPE_RULES:
        if _matches_filename_rule(
            compact_name=compact_name,
            normalized_name=normalized_name,
            tokens=tokens,
            token_keywords=token_keywords,
            phrase_keywords=phrase_keywords,
        ):
            return ClassificationResult(
                document_type=document_type,
                confidence=confidence,
                classifier="filename-keyword-v2",
            )

    normalized_text = _normalize_text(raw_text)
    if normalized_text:
        for document_type, phrases, confidence in TEXT_TYPE_RULES:
            if any(phrase in normalized_text for phrase in phrases):
                return ClassificationResult(
                    document_type=document_type,
                    confidence=confidence,
                    classifier="ocr-text-keyword-v1",
                )

    if content_type == "application/pdf":
        return ClassificationResult(
            document_type="invoice",
            confidence=0.20,
            classifier="filename-fallback-v1",
        )

    return ClassificationResult(
        document_type="contract",
        confidence=0.10,
        classifier="filename-fallback-v1",
    )


def _normalize_filename(file_name: str) -> tuple[str, str, set[str]]:
    file_stem = Path(file_name).stem.casefold()
    file_stem = file_stem.replace("\u00a0", " ")
    file_stem = re.sub(r"([a-zа-я])\s*[/\\]\s*([a-zа-я])", r"\1\2", file_stem, flags=re.IGNORECASE)
    normalized_name = re.sub(r"[\W_]+", " ", file_stem, flags=re.UNICODE)
    normalized_name = re.sub(r"\s+", " ", normalized_name).strip()
    compact_name = normalized_name.replace(" ", "")
    tokens = {token for token in normalized_name.split(" ") if token}
    return normalized_name, compact_name, tokens


def _normalize_text(raw_text: str | None) -> str:
    if not raw_text:
        return ""
    return re.sub(r"\s+", " ", raw_text.casefold()).strip()


def _matches_filename_rule(
    *,
    compact_name: str,
    normalized_name: str,
    tokens: set[str],
    token_keywords: tuple[str, ...],
    phrase_keywords: tuple[str, ...],
) -> bool:
    compact_keywords = {keyword for keyword in token_keywords if " " not in keyword}
    if compact_keywords and any(keyword in tokens or keyword in compact_name for keyword in compact_keywords):
        return True

    return any(phrase in normalized_name for phrase in phrase_keywords)
