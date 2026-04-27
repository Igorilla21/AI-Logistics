from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ClassificationResult:
    document_type: str
    confidence: float
    classifier: str


DOCUMENT_TYPE_RULES: list[tuple[str, tuple[str, ...], float]] = [
    ("payment_confirmation", ("mt103", "payment", "swift"), 0.95),
    ("packing_list", ("packing", "packing_list", "pkl"), 0.95),
    ("invoice", ("invoice", "commercial_invoice", "inv"), 0.92),
    ("addendum", ("addendum", "appendix", "supplement"), 0.92),
    ("contract", ("contract", "agreement"), 0.90),
    ("coa", ("coa", "certificate_of_analysis"), 0.95),
    ("hbl", ("house_bill", "hbl"), 0.95),
    ("mbl", ("master_bill", "mbl", "bill_of_lading", "bl"), 0.90),
    ("transport_invoice", ("transport_invoice", "freight_invoice", "transport"), 0.88),
    ("certificate_of_origin", ("certificate_of_origin", "origin", "co"), 0.82),
]


def classify_document(file_name: str, content_type: str | None = None) -> ClassificationResult:
    file_stem = Path(file_name).stem.lower()
    normalized_name = file_stem.replace("-", "_").replace(" ", "_")

    for document_type, keywords, confidence in DOCUMENT_TYPE_RULES:
        if any(keyword in normalized_name for keyword in keywords):
            return ClassificationResult(
                document_type=document_type,
                confidence=confidence,
                classifier="filename-keyword-v1",
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
