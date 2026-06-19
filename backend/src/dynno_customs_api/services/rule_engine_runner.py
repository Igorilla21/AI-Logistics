from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from typing import Any
from uuid import uuid4

from dynno_customs_api.models.domain import (
    DocumentPackRecord,
    EvidenceRecord,
    NormalizedDocumentRecord,
    ValidationReportRecord,
    ValidationResultRecord,
    ValidationSeverity,
    ValidationStatus,
    ValidationSummaryRecord,
)


NUMERIC_TOLERANCE = 0.01
UNCERTAIN_CONFIDENCE_THRESHOLD = 0.5
INCOTERMS_ALLOWED = {"FOB", "FOR", "FCA", "EXW", "DAP", "CPT", "CIF", "CFR", "DDP"}
HS_CODE_PATTERN = re.compile(r"\bh\s*\.?\s*s\s*\.?\s*code\b", re.IGNORECASE)
NON_PALLET_PACKAGE_TYPES = {
    "bag",
    "bags",
    "box",
    "boxes",
    "carton",
    "cartons",
    "package",
    "packages",
    "pkg",
}
NON_PALLET_GROSS_NET_WARNING_THRESHOLD_KG = 300.0
COMPANY_CORE_STOP_WORDS = {
    "a",
    "co",
    "company",
    "limited",
    "llc",
    "ltd",
    "ooo",
    "s",
    "san",
    "sanayi",
    "the",
    "tic",
    "ticaret",
    "ve",
}
OCR_CONFUSABLES = str.maketrans(
    {
        "А": "A",
        "В": "B",
        "С": "C",
        "Е": "E",
        "Н": "H",
        "К": "K",
        "М": "M",
        "О": "O",
        "Р": "P",
        "Т": "T",
        "У": "Y",
        "Х": "X",
        "а": "a",
        "е": "e",
        "о": "o",
        "р": "p",
        "с": "c",
        "т": "t",
        "у": "y",
        "х": "x",
        "к": "k",
        "м": "m",
        "н": "n",
        "в": "b",
        "і": "i",
        "І": "I",
    }
)


@dataclass(frozen=True, slots=True)
class RuleContext:
    pack: DocumentPackRecord
    generated_at: datetime
    tolerance: float = NUMERIC_TOLERANCE

    @property
    def documents_by_type(self) -> dict[str, list[NormalizedDocumentRecord]]:
        grouped: dict[str, list[NormalizedDocumentRecord]] = {}
        for document in self.pack.normalized_documents:
            grouped.setdefault(document.document_type, []).append(document)
        return grouped

    def doc(self, document_type: str) -> NormalizedDocumentRecord | None:
        documents = self.documents_by_type.get(document_type, [])
        return documents[0] if documents else None

    def bill_of_lading(self) -> NormalizedDocumentRecord | None:
        return self.doc("hbl") or self.doc("mbl")


@dataclass(frozen=True, slots=True)
class FieldValue:
    key: str
    value: Any
    comparable: Any
    evidence: EvidenceRecord | None
    confidence: float | None
    uncertain: bool


Rule = Callable[[RuleContext], ValidationResultRecord]
SourceSpec = tuple[str, str]


def run_rule_engine(pack: DocumentPackRecord) -> ValidationReportRecord:
    generated_at = datetime.now(UTC)
    context = RuleContext(pack=pack, generated_at=generated_at)
    results = [rule(context) for rule in RULES]
    return ValidationReportRecord(
        report_id=uuid4(),
        pack_id=pack.pack_id,
        generated_at=generated_at,
        summary=_summarize(results),
        results=results,
    )


def derive_pack_status(report: ValidationReportRecord) -> str:
    if any(result.status == "failed" and result.severity == "error" for result in report.results):
        return "failed"
    if any(result.status in {"failed", "needs_review"} for result in report.results):
        return "needs_review"
    return "validated"


def _summarize(results: Sequence[ValidationResultRecord]) -> ValidationSummaryRecord:
    passed = 0
    failed = 0
    warnings = 0
    needs_review = 0
    skipped = 0

    for result in results:
        if result.status == "passed":
            passed += 1
        elif result.status == "skipped":
            skipped += 1
        elif result.status == "needs_review":
            needs_review += 1
        elif result.severity == "warning":
            warnings += 1
        else:
            failed += 1

    return ValidationSummaryRecord(
        total_rules=len(results),
        passed=passed,
        failed=failed,
        warnings=warnings,
        needs_review=needs_review,
        skipped=skipped,
    )


def _result(
    context: RuleContext,
    *,
    rule_code: str,
    severity: ValidationSeverity,
    status: ValidationStatus,
    message: str,
    documents: Sequence[str],
    fields: Sequence[str],
    observed_values: dict[str, Any] | None = None,
    expected_values: dict[str, Any] | None = None,
    evidence: Sequence[EvidenceRecord | None] | None = None,
    confidence: float | None = None,
) -> ValidationResultRecord:
    return ValidationResultRecord(
        rule_code=rule_code,
        severity=severity,
        status=status,
        message=message,
        documents=_unique(documents),
        fields=_unique(fields),
        observed_values=observed_values or {},
        expected_values=expected_values,
        evidence=[item for item in evidence or [] if item is not None],
        confidence=confidence,
        created_at=context.generated_at,
    )


def _unique(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


def _field_values(document: NormalizedDocumentRecord, field_name: str) -> list[FieldValue]:
    raw_field = getattr(document.fields, field_name)
    if raw_field is None:
        return []

    field_records = raw_field if isinstance(raw_field, list) else [raw_field]
    values: list[FieldValue] = []
    for index, field_record in enumerate(field_records, start=1):
        value = getattr(field_record, "normalized_value", None)
        if value is None:
            value = getattr(field_record, "value", None)
        if value is None or value == "":
            continue

        indexed_field_name = field_name if len(field_records) == 1 else f"{field_name}[{index}]"
        key = f"{document.document_type}.{indexed_field_name}"
        confidence = getattr(field_record, "confidence", None)
        values.append(
            FieldValue(
                key=key,
                value=value,
                comparable=_normalize_value(value),
                evidence=_field_evidence(document, field_record, indexed_field_name),
                confidence=confidence,
                uncertain=_field_uncertain(field_record),
            )
        )
    return values


def _field_evidence(document: NormalizedDocumentRecord, field_record: Any, field_name: str) -> EvidenceRecord:
    text_snippet = getattr(field_record, "text_snippet", None) or f"{document.document_type}.{field_name}: {field_record.value}"
    return EvidenceRecord(
        document_type=document.document_type,
        page_no=getattr(field_record, "page_no", None) or 1,
        field_name=field_name,
        text_snippet=text_snippet,
        confidence=getattr(field_record, "confidence", None),
        bounding_box=getattr(field_record, "bounding_box", None),
    )


def _field_uncertain(field_record: Any) -> bool:
    confidence = getattr(field_record, "confidence", None)
    if confidence is not None and confidence < UNCERTAIN_CONFIDENCE_THRESHOLD:
        return True

    candidates = getattr(field_record, "candidates", None) or []
    if len(candidates) < 2:
        return False

    sorted_candidates = sorted(candidates, key=lambda item: item.confidence, reverse=True)
    return abs(sorted_candidates[0].confidence - sorted_candidates[1].confidence) <= 0.05


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _normalize_string(value)
    return value


def _normalize_string(value: str) -> str:
    text = value.translate(OCR_CONFUSABLES).casefold().strip()
    text = re.sub(r"[.,;:]+", " ", text)
    text = re.sub(r"[|]+", " ", text)
    text = re.sub(r"\b(co)\s*,?\s*(ltd)\b", r"\1 \2", text)
    text = re.sub(r"\b(company|limited liability company|the)\b", " ", text)
    text = re.sub(r"\b(ooo|llc)\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _string_values_match(left: str, right: str, similarity_threshold: float | None = None) -> bool:
    if left == right:
        return True
    if similarity_threshold is None:
        return False
    if _company_core_tokens_match(left, right):
        return True
    return SequenceMatcher(None, left, right).ratio() >= similarity_threshold


def _company_core_tokens_match(left: str, right: str) -> bool:
    left_tokens = _company_core_tokens(left)
    right_tokens = _company_core_tokens(right)
    if len(left_tokens) < 2 or len(right_tokens) < 2:
        return False
    smaller, larger = (left_tokens, right_tokens) if len(left_tokens) <= len(right_tokens) else (right_tokens, left_tokens)
    return smaller.issubset(larger)


def _company_core_tokens(value: str) -> set[str]:
    return {token for token in value.split() if len(token) > 1 and token not in COMPANY_CORE_STOP_WORDS}


def _observed(values: Sequence[FieldValue]) -> dict[str, Any]:
    return {value.key: value.value for value in values}


def _evidence(values: Sequence[FieldValue]) -> list[EvidenceRecord | None]:
    return [value.evidence for value in values]


def _confidence(values: Sequence[FieldValue]) -> float | None:
    confidences = [value.confidence for value in values if value.confidence is not None]
    return min(confidences) if confidences else None


def _documents_from_sources(sources: Sequence[SourceSpec]) -> list[str]:
    return _unique([document_type for document_type, _ in sources])


def _collect_sources(context: RuleContext, sources: Sequence[SourceSpec]) -> list[FieldValue]:
    values: list[FieldValue] = []
    for document_type, field_name in sources:
        document = context.doc(document_type)
        if document is not None:
            values.extend(_field_values(document, field_name))
    return values


def _source_fields(sources: Sequence[SourceSpec]) -> list[str]:
    return _unique([field_name for _, field_name in sources])


def _exact_match_rule(
    context: RuleContext,
    *,
    rule_code: str,
    severity: ValidationSeverity,
    sources: Sequence[SourceSpec],
    pass_message: str,
    fail_message: str,
    skip_message: str,
    similarity_threshold: float | None = None,
) -> ValidationResultRecord:
    values = _collect_sources(context, sources)
    if len(values) < 2:
        return _result(
            context,
            rule_code=rule_code,
            severity=severity,
            status="skipped",
            message=skip_message,
            documents=_documents_from_sources(sources),
            fields=_source_fields(sources),
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    if any(value.uncertain for value in values):
        return _result(
            context,
            rule_code=rule_code,
            severity=severity,
            status="needs_review",
            message="One or more compared values have low confidence or ambiguous candidates.",
            documents=_documents_from_sources(sources),
            fields=_source_fields(sources),
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    expected = values[0].comparable
    if isinstance(expected, str):
        matched = all(isinstance(value.comparable, str) and _string_values_match(expected, value.comparable, similarity_threshold) for value in values[1:])
    else:
        matched = all(value.comparable == expected for value in values[1:])
    status: ValidationStatus = "passed" if matched else "failed"
    return _result(
        context,
        rule_code=rule_code,
        severity=severity,
        status=status,
        message=pass_message if status == "passed" else fail_message,
        documents=_documents_from_sources(sources),
        fields=_source_fields(sources),
        observed_values=_observed(values),
        expected_values={"normalized_value": expected},
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _reference_match_rule(
    context: RuleContext,
    *,
    rule_code: str,
    severity: ValidationSeverity,
    reference: SourceSpec,
    targets: Sequence[SourceSpec],
    pass_message: str,
    fail_message: str,
    skip_message: str,
) -> ValidationResultRecord:
    sources = [reference, *targets]
    reference_document = context.doc(reference[0])
    reference_values = _field_values(reference_document, reference[1]) if reference_document else []
    target_values = _collect_sources(context, targets)
    values = [*reference_values, *target_values]

    if not reference_values or len(target_values) != len(targets):
        return _result(
            context,
            rule_code=rule_code,
            severity=severity,
            status="skipped",
            message=skip_message,
            documents=_documents_from_sources(sources),
            fields=_source_fields(sources),
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    if any(value.uncertain for value in values):
        return _result(
            context,
            rule_code=rule_code,
            severity=severity,
            status="needs_review",
            message="One or more compared values have low confidence or ambiguous candidates.",
            documents=_documents_from_sources(sources),
            fields=_source_fields(sources),
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    expected = reference_values[0].comparable
    status: ValidationStatus = "passed" if all(value.comparable == expected for value in target_values) else "failed"
    return _result(
        context,
        rule_code=rule_code,
        severity=severity,
        status=status,
        message=pass_message if status == "passed" else fail_message,
        documents=_documents_from_sources(sources),
        fields=_source_fields(sources),
        observed_values=_observed(values),
        expected_values={reference_values[0].key: reference_values[0].value},
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _presence_rule(
    context: RuleContext,
    *,
    rule_code: str,
    severity: ValidationSeverity,
    document_type: str,
    field_name: str,
    pass_message: str,
    fail_message: str,
) -> ValidationResultRecord:
    document = context.doc(document_type)
    values = _field_values(document, field_name) if document else []
    status: ValidationStatus = "passed" if values else "failed"
    observed_values = _observed(values) if values else {f"{document_type}.{field_name}": None}
    return _result(
        context,
        rule_code=rule_code,
        severity=severity,
        status=status,
        message=pass_message if status == "passed" else fail_message,
        documents=[document_type],
        fields=[field_name],
        observed_values=observed_values,
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _date_compare_rule(
    context: RuleContext,
    *,
    rule_code: str,
    severity: ValidationSeverity,
    left: SourceSpec,
    right: SourceSpec,
    operator: str,
    pass_message: str,
    fail_message: str,
    skip_message: str,
) -> ValidationResultRecord:
    left_document = context.doc(left[0])
    right_document = context.doc(right[0])
    left_values = _field_values(left_document, left[1]) if left_document else []
    right_values = _field_values(right_document, right[1]) if right_document else []
    values = [*left_values, *right_values]

    if not left_values or not right_values:
        return _result(
            context,
            rule_code=rule_code,
            severity=severity,
            status="skipped",
            message=skip_message,
            documents=[left[0], right[0]],
            fields=[left[1], right[1]],
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    left_value = left_values[0].value
    right_value = right_values[0].value
    checks = {
        ">": left_value > right_value,
        "<": left_value < right_value,
        ">=": left_value >= right_value,
        "<=": left_value <= right_value,
    }
    status: ValidationStatus = "passed" if checks[operator] else "failed"
    return _result(
        context,
        rule_code=rule_code,
        severity=severity,
        status=status,
        message=pass_message if status == "passed" else fail_message,
        documents=[left[0], right[0]],
        fields=[left[1], right[1]],
        observed_values=_observed(values),
        expected_values={"operator": operator},
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _numeric_field(document: NormalizedDocumentRecord | None, field_name: str) -> FieldValue | None:
    if document is None:
        return None
    values = _field_values(document, field_name)
    return values[0] if values else None


def _numeric_formula_rule(
    context: RuleContext,
    *,
    rule_code: str,
    severity: ValidationSeverity,
    document_type: str,
    fields: Sequence[str],
    compute_expected: Callable[[dict[str, float]], float],
    target_field: str,
    pass_message: str,
    fail_message: str,
    skip_message: str,
) -> ValidationResultRecord:
    document = context.doc(document_type)
    values_by_field = {field_name: _numeric_field(document, field_name) for field_name in fields}
    values = [value for value in values_by_field.values() if value is not None]

    if any(value is None for value in values_by_field.values()):
        return _result(
            context,
            rule_code=rule_code,
            severity=severity,
            status="skipped",
            message=skip_message,
            documents=[document_type],
            fields=fields,
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    numeric_values = {field_name: float(value.value) for field_name, value in values_by_field.items() if value is not None}
    expected = compute_expected(numeric_values)
    actual = numeric_values[target_field]
    status: ValidationStatus = "passed" if abs(actual - expected) <= context.tolerance else "failed"
    return _result(
        context,
        rule_code=rule_code,
        severity=severity,
        status=status,
        message=pass_message if status == "passed" else fail_message,
        documents=[document_type],
        fields=fields,
        observed_values=_observed(values),
        expected_values={f"{document_type}.{target_field}": expected, "tolerance": context.tolerance},
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _numeric_pair_rule(
    context: RuleContext,
    *,
    rule_code: str,
    severity: ValidationSeverity,
    left: SourceSpec,
    right: SourceSpec,
    pass_message: str,
    fail_message: str,
    skip_message: str,
) -> ValidationResultRecord:
    left_document = context.doc(left[0])
    right_document = context.doc(right[0])
    left_value = _numeric_field(left_document, left[1])
    right_value = _numeric_field(right_document, right[1])
    values = [value for value in (left_value, right_value) if value is not None]

    if left_value is None or right_value is None:
        return _result(
            context,
            rule_code=rule_code,
            severity=severity,
            status="skipped",
            message=skip_message,
            documents=[left[0], right[0]],
            fields=[left[1], right[1]],
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    status: ValidationStatus = (
        "passed" if abs(float(left_value.value) - float(right_value.value)) <= context.tolerance else "failed"
    )
    return _result(
        context,
        rule_code=rule_code,
        severity=severity,
        status=status,
        message=pass_message if status == "passed" else fail_message,
        documents=[left[0], right[0]],
        fields=[left[1], right[1]],
        observed_values=_observed(values),
        expected_values={"tolerance": context.tolerance},
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _field_sources_with_bl(field_name: str, coa_field: str | None = None, context: RuleContext | None = None) -> list[SourceSpec]:
    sources: list[SourceSpec] = [
        ("contract", field_name),
        ("addendum", field_name),
        ("invoice", field_name),
        ("packing_list", field_name),
    ]
    if coa_field is not None:
        sources.append(("coa", coa_field))

    bl_type = context.bill_of_lading().document_type if context and context.bill_of_lading() else None
    sources.append((bl_type or "hbl", field_name))
    if bl_type is None:
        sources.append(("mbl", field_name))
    return sources


def _rule_r001(context: RuleContext) -> ValidationResultRecord:
    return _exact_match_rule(
        context,
        rule_code="R001",
        severity="warning",
        sources=_field_sources_with_bl("shipper_name", "manufacturer_name", context),
        pass_message="Shipper/manufacturer names match across available documents.",
        fail_message="Shipper/manufacturer names do not match across documents.",
        skip_message="Not enough shipper/manufacturer values were extracted to compare documents.",
        similarity_threshold=0.84,
    )


def _rule_r002(context: RuleContext) -> ValidationResultRecord:
    return _exact_match_rule(
        context,
        rule_code="R002",
        severity="warning",
        sources=_field_sources_with_bl("buyer_name", None, context),
        pass_message="Buyer names match across available documents.",
        fail_message="Buyer names do not match across documents.",
        skip_message="Not enough buyer values were extracted to compare documents.",
        similarity_threshold=0.92,
    )


def _rule_r003(context: RuleContext) -> ValidationResultRecord:
    return _reference_match_rule(
        context,
        rule_code="R003",
        severity="warning",
        reference=("contract", "contract_no"),
        targets=(("addendum", "contract_no"), ("invoice", "contract_no")),
        pass_message="Contract numbers in addendum and invoice match the contract.",
        fail_message="Contract numbers in addendum or invoice do not match the contract.",
        skip_message="Separate contract document is missing or unreadable, so addendum and invoice contract numbers cannot be matched to it.",
    )


def _product_names(document: NormalizedDocumentRecord) -> list[FieldValue]:
    values: list[FieldValue] = []
    for item_index, line_item in enumerate(document.line_items, start=1):
        field_record = line_item.product_name_normalized or line_item.product_name_raw
        if field_record is None:
            continue
        value = field_record.normalized_value or field_record.value
        key = f"{document.document_type}.line_items[{item_index}].product_name_normalized"
        values.append(
            FieldValue(
                key=key,
                value=value,
                comparable=_normalize_string(value),
                evidence=_field_evidence(document, field_record, f"line_items[{item_index}].product_name_normalized"),
                confidence=field_record.confidence,
                uncertain=_field_uncertain(field_record),
            )
        )
    return values


def _rule_r004(context: RuleContext) -> ValidationResultRecord:
    # BL cargo_description is deliberately excluded: BL may contain a shorter cargo family description.
    source_types = ("addendum", "invoice", "packing_list", "coa")
    values_by_doc: dict[str, list[FieldValue]] = {}
    for document_type in source_types:
        document = context.doc(document_type)
        if document is not None:
            values_by_doc[document_type] = _product_names(document)

    values = [value for doc_values in values_by_doc.values() for value in doc_values]
    comparable_sets = {
        document_type: {value.comparable for value in doc_values}
        for document_type, doc_values in values_by_doc.items()
        if doc_values
    }
    if len(comparable_sets) < 2:
        return _result(
            context,
            rule_code="R004",
            severity="warning",
            status="skipped",
            message="Not enough product names were extracted to compare product sets.",
            documents=list(source_types),
            fields=["line_items.product_name_normalized"],
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    expected = next(iter(comparable_sets.values()))
    status: ValidationStatus = "passed" if all(value_set == expected for value_set in comparable_sets.values()) else "failed"
    return _result(
        context,
        rule_code="R004",
        severity="warning",
        status=status,
        message="Product name sets match across available documents."
        if status == "passed"
        else "Product name sets do not match across documents.",
        documents=list(comparable_sets.keys()),
        fields=["line_items.product_name_normalized"],
        observed_values={key: sorted(value_set) for key, value_set in comparable_sets.items()},
        expected_values={"normalized_product_set": sorted(expected)},
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _rule_r005(context: RuleContext) -> ValidationResultRecord:
    return _date_compare_rule(
        context,
        rule_code="R005",
        severity="error",
        left=("addendum", "addendum_date"),
        right=("contract", "contract_date"),
        operator=">",
        pass_message="Addendum date is later than contract date.",
        fail_message="Addendum date is not later than contract date.",
        skip_message="Separate contract document date is missing, so the extracted addendum date cannot be compared to a contract date.",
    )


def _rule_r006(context: RuleContext) -> ValidationResultRecord:
    required_sources: list[SourceSpec] = [
        ("addendum", "incoterms"),
        ("invoice", "incoterms"),
    ]
    optional_sources: list[SourceSpec] = [
        ("contract", "incoterms"),
        ("packing_list", "incoterms"),
        ("transport_invoice", "incoterms"),
    ]
    sources = [*required_sources, *optional_sources]
    values = _collect_sources(context, sources)
    required_values = _collect_sources(context, required_sources)
    invalid_values = [value for value in values if str(value.value).upper() not in INCOTERMS_ALLOWED]
    comparable_values = [str(value.value).upper() for value in values]

    if not required_values:
        return _result(
            context,
            rule_code="R006",
            severity="warning",
            status="skipped",
            message="Incoterms were not extracted from the required addendum/invoice pair, so cross-document comparison was skipped.",
            documents=_documents_from_sources(sources),
            fields=["incoterms"],
            observed_values=_observed(values),
        )

    if invalid_values:
        return _result(
            context,
            rule_code="R006",
            severity="warning",
            status="failed",
            message="One or more Incoterms values are outside the allowed list.",
            documents=_documents_from_sources(sources),
            fields=["incoterms"],
            observed_values=_observed(values),
            expected_values={"allowed_values": sorted(INCOTERMS_ALLOWED)},
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    if len(required_values) < 2:
        return _result(
            context,
            rule_code="R006",
            severity="warning",
            status="skipped",
            message="Incoterms were extracted from only one required document (addendum or invoice); optional documents stay green and cross-document comparison was skipped.",
            documents=_documents_from_sources(sources),
            fields=["incoterms"],
            observed_values=_observed(values),
            expected_values={
                "allowed_values": sorted(INCOTERMS_ALLOWED),
                "required_documents": ["addendum", "invoice"],
            },
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    expected = comparable_values[0]
    status: ValidationStatus = "passed" if all(value == expected for value in comparable_values[1:]) else "failed"
    return _result(
        context,
        rule_code="R006",
        severity="warning",
        status=status,
        message="Incoterms match across available documents." if status == "passed" else "Incoterms do not match.",
        documents=_documents_from_sources(sources),
        fields=["incoterms"],
        observed_values=_observed(values),
        expected_values={"allowed_values": sorted(INCOTERMS_ALLOWED), "normalized_value": expected},
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _rule_r007(context: RuleContext) -> ValidationResultRecord:
    return _exact_match_rule(
        context,
        rule_code="R007",
        severity="error",
        sources=(("invoice", "invoice_no"), ("packing_list", "invoice_no")),
        pass_message="Invoice number matches between invoice and packing list.",
        fail_message="Invoice number does not match between invoice and packing list.",
        skip_message="Invoice number is missing from invoice or packing list.",
    )


def _rule_r008(context: RuleContext) -> ValidationResultRecord:
    invoice = context.doc("invoice")
    if invoice is None or not invoice.line_items:
        return _result(
            context,
            rule_code="R008",
            severity="error",
            status="skipped",
            message="Invoice line items are missing.",
            documents=["invoice"],
            fields=["line_items.quantity", "line_items.unit_price", "line_items.line_total"],
        )

    observed_values: dict[str, Any] = {}
    expected_values: dict[str, Any] = {"tolerance": context.tolerance}
    evidence: list[EvidenceRecord | None] = []
    missing = False
    failed_lines: list[int] = []

    for index, item in enumerate(invoice.line_items, start=1):
        quantity = item.quantity
        unit_price = item.unit_price
        line_total = item.line_total
        if quantity is None or unit_price is None or line_total is None:
            missing = True
            continue

        expected = float(quantity.value) * float(unit_price.value)
        actual = float(line_total.value)
        observed_values[f"invoice.line_items[{index}].quantity"] = quantity.value
        observed_values[f"invoice.line_items[{index}].unit_price"] = unit_price.value
        observed_values[f"invoice.line_items[{index}].line_total"] = line_total.value
        expected_values[f"invoice.line_items[{index}].line_total"] = expected
        evidence.extend(
            [
                _field_evidence(invoice, quantity, f"line_items[{index}].quantity"),
                _field_evidence(invoice, unit_price, f"line_items[{index}].unit_price"),
                _field_evidence(invoice, line_total, f"line_items[{index}].line_total"),
            ]
        )
        if abs(actual - expected) > context.tolerance:
            failed_lines.append(index)

    if missing:
        return _result(
            context,
            rule_code="R008",
            severity="error",
            status="skipped",
            message="One or more invoice line items are missing quantity, unit price, or line total.",
            documents=["invoice"],
            fields=["line_items.quantity", "line_items.unit_price", "line_items.line_total"],
            observed_values=observed_values,
            expected_values=expected_values,
            evidence=evidence,
        )

    status: ValidationStatus = "passed" if not failed_lines else "failed"
    return _result(
        context,
        rule_code="R008",
        severity="error",
        status=status,
        message="Invoice line arithmetic is valid." if status == "passed" else "Invoice line arithmetic is invalid.",
        documents=["invoice"],
        fields=["line_items.quantity", "line_items.unit_price", "line_items.line_total"],
        observed_values=observed_values,
        expected_values=expected_values,
        evidence=evidence,
    )


def _rule_r009(context: RuleContext) -> ValidationResultRecord:
    invoice = context.doc("invoice")
    total_amount = _numeric_field(invoice, "total_amount")
    if invoice is None or not invoice.line_items or total_amount is None:
        return _result(
            context,
            rule_code="R009",
            severity="error",
            status="skipped",
            message="Invoice total amount or line totals are missing.",
            documents=["invoice"],
            fields=["line_items.line_total", "total_amount"],
            observed_values=_observed([total_amount] if total_amount else []),
            evidence=_evidence([total_amount] if total_amount else []),
            confidence=total_amount.confidence if total_amount else None,
        )

    line_totals = [item.line_total for item in invoice.line_items if item.line_total is not None]
    if len(line_totals) != len(invoice.line_items):
        return _result(
            context,
            rule_code="R009",
            severity="error",
            status="skipped",
            message="One or more invoice line totals are missing.",
            documents=["invoice"],
            fields=["line_items.line_total", "total_amount"],
            observed_values={total_amount.key: total_amount.value},
            evidence=[total_amount.evidence],
            confidence=total_amount.confidence,
        )

    expected = sum(float(line_total.value) for line_total in line_totals)
    actual = float(total_amount.value)
    observed_values = {total_amount.key: total_amount.value}
    evidence: list[EvidenceRecord | None] = [total_amount.evidence]
    for index, line_total in enumerate(line_totals, start=1):
        key = f"invoice.line_items[{index}].line_total"
        observed_values[key] = line_total.value
        evidence.append(_field_evidence(invoice, line_total, f"line_items[{index}].line_total"))

    status: ValidationStatus = "passed" if abs(actual - expected) <= context.tolerance else "failed"
    return _result(
        context,
        rule_code="R009",
        severity="error",
        status=status,
        message="Invoice total amount matches line total sum."
        if status == "passed"
        else "Invoice total amount does not match line total sum.",
        documents=["invoice"],
        fields=["line_items.line_total", "total_amount"],
        observed_values=observed_values,
        expected_values={"invoice.total_amount": expected, "tolerance": context.tolerance},
        evidence=evidence,
        confidence=total_amount.confidence,
    )


def _rule_r010(context: RuleContext) -> ValidationResultRecord:
    return _presence_rule(
        context,
        rule_code="R010",
        severity="error",
        document_type="packing_list",
        field_name="package_type",
        pass_message="Packing list contains package type.",
        fail_message="Packing list package type is missing.",
    )


def _rule_r011(context: RuleContext) -> ValidationResultRecord:
    return _presence_rule(
        context,
        rule_code="R011",
        severity="error",
        document_type="packing_list",
        field_name="packages_quantity",
        pass_message="Packing list contains packages quantity.",
        fail_message="Packing list packages quantity is missing.",
    )


def _rule_r012(context: RuleContext) -> ValidationResultRecord:
    return _numeric_formula_rule(
        context,
        rule_code="R012",
        severity="error",
        document_type="packing_list",
        fields=("gross_weight_kg", "net_weight_kg", "package_weight_kg"),
        compute_expected=lambda values: values["net_weight_kg"] + values["package_weight_kg"],
        target_field="gross_weight_kg",
        pass_message="Packing gross weight equals net weight plus package weight.",
        fail_message="Packing gross weight does not equal net weight plus package weight.",
        skip_message="Packing gross, net, or package weight is missing.",
    )


def _rule_r013(context: RuleContext) -> ValidationResultRecord:
    return _numeric_formula_rule(
        context,
        rule_code="R013",
        severity="error",
        document_type="packing_list",
        fields=("package_weight_kg", "gross_weight_kg", "net_weight_kg"),
        compute_expected=lambda values: values["gross_weight_kg"] - values["net_weight_kg"],
        target_field="package_weight_kg",
        pass_message="Packing package weight equals gross weight minus net weight.",
        fail_message="Packing package weight does not equal gross weight minus net weight.",
        skip_message="Packing gross, net, or package weight is missing.",
    )


def _rule_r014(context: RuleContext) -> ValidationResultRecord:
    packing_list = context.doc("packing_list")
    if packing_list is None:
        return _result(
            context,
            rule_code="R014",
            severity="error",
            status="skipped",
            message="Packing list is missing.",
            documents=["packing_list"],
            fields=["empty_package_weight_kg"],
        )

    empty_package_values = _field_values(packing_list, "empty_package_weight_kg")
    if empty_package_values:
        return _result(
            context,
            rule_code="R014",
            severity="error",
            status="passed",
            message="Packing list contains empty package weight.",
            documents=["packing_list"],
            fields=["empty_package_weight_kg"],
            observed_values=_observed(empty_package_values),
            evidence=_evidence(empty_package_values),
            confidence=_confidence(empty_package_values),
        )

    supporting_values = [
        value
        for value in [
            _numeric_field(packing_list, "gross_weight_kg"),
            _numeric_field(packing_list, "net_weight_kg"),
            _numeric_field(packing_list, "pallet_weight_kg"),
            _numeric_field(packing_list, "pallet_quantity"),
            _numeric_field(packing_list, "has_pallets"),
        ]
        if value is not None
    ]
    has_pallets = next((value for value in supporting_values if value.key == "packing_list.has_pallets"), None)
    if has_pallets is not None and bool(has_pallets.value) and len(supporting_values) == 5:
        return _result(
            context,
            rule_code="R014",
            severity="error",
            status="skipped",
            message="Packing list does not state empty package tare separately; palletized gross/net reconciliation uses pallet weight instead.",
            documents=["packing_list"],
            fields=["empty_package_weight_kg", "has_pallets", "pallet_weight_kg", "pallet_quantity"],
            observed_values={**_observed(supporting_values), "packing_list.empty_package_weight_kg": None},
            evidence=_evidence(supporting_values),
            confidence=_confidence(supporting_values),
        )

    return _result(
        context,
        rule_code="R014",
        severity="error",
        status="failed",
        message="Packing list empty package weight is missing.",
        documents=["packing_list"],
        fields=["empty_package_weight_kg"],
        observed_values={"packing_list.empty_package_weight_kg": None},
    )


def _rule_r015(context: RuleContext) -> ValidationResultRecord:
    packing_list = context.doc("packing_list")
    if packing_list is None:
        return _result(
            context,
            rule_code="R015",
            severity="warning",
            status="skipped",
            message="Packing list is missing, so pallet applicability could not be evaluated.",
            documents=["packing_list"],
            fields=["has_pallets", "pallet_weight_kg", "pallet_quantity"],
        )

    has_pallets_values = _field_values(packing_list, "has_pallets")
    if not has_pallets_values:
        return _result(
            context,
            rule_code="R015",
            severity="warning",
            status="skipped",
            message="Pallet applicability is missing from the packing list extraction.",
            documents=["packing_list"],
            fields=["has_pallets", "pallet_weight_kg", "pallet_quantity"],
        )

    has_pallets = bool(has_pallets_values[0].value)
    if not has_pallets:
        return _result(
            context,
            rule_code="R015",
            severity="warning",
            status="passed",
            message="Packing list indicates pallets are not applicable.",
            documents=["packing_list"],
            fields=["has_pallets", "pallet_weight_kg", "pallet_quantity"],
            observed_values={has_pallets_values[0].key: has_pallets},
            evidence=[has_pallets_values[0].evidence],
            confidence=has_pallets_values[0].confidence,
        )

    pallet_weight_values = _field_values(packing_list, "pallet_weight_kg")
    pallet_quantity_values = _field_values(packing_list, "pallet_quantity")
    observed_values = {has_pallets_values[0].key: has_pallets}
    if pallet_weight_values:
        observed_values[pallet_weight_values[0].key] = pallet_weight_values[0].value
    if pallet_quantity_values:
        observed_values[pallet_quantity_values[0].key] = pallet_quantity_values[0].value

    missing_fields = []
    if not pallet_weight_values:
        missing_fields.append("pallet_weight_kg")
    if not pallet_quantity_values:
        missing_fields.append("pallet_quantity")

    if missing_fields:
        return _result(
            context,
            rule_code="R015",
            severity="warning",
            status="failed",
            message="Packing list indicates pallets are present, but pallet weight or quantity is missing.",
            documents=["packing_list"],
            fields=["has_pallets", "pallet_weight_kg", "pallet_quantity"],
            observed_values=observed_values,
            expected_values={field_name: "required when has_pallets is true" for field_name in missing_fields},
            evidence=[has_pallets_values[0].evidence],
            confidence=has_pallets_values[0].confidence,
        )

    return _result(
        context,
        rule_code="R015",
        severity="warning",
        status="passed",
        message="Packing list contains pallet weight and pallet quantity for a palletized shipment.",
        documents=["packing_list"],
        fields=["has_pallets", "pallet_weight_kg", "pallet_quantity"],
        observed_values=observed_values,
        evidence=[
            has_pallets_values[0].evidence,
            pallet_weight_values[0].evidence,
            pallet_quantity_values[0].evidence,
        ],
    )


def _rule_r016(context: RuleContext) -> ValidationResultRecord:
    packing_list = context.doc("packing_list")
    if packing_list is None:
        return _result(
            context,
            rule_code="R016",
            severity="error",
            status="skipped",
            message="Packing list is missing.",
            documents=["packing_list"],
            fields=[
                "gross_weight_kg",
                "net_weight_kg",
                "empty_package_weight_kg",
                "items_quantity",
                "has_pallets",
                "pallet_weight_kg",
                "pallet_quantity",
            ],
        )

    has_pallets_value = _numeric_field(packing_list, "has_pallets")
    package_type_value = _field_values(packing_list, "package_type")
    base_fields = {
        "gross_weight_kg": _numeric_field(packing_list, "gross_weight_kg"),
        "net_weight_kg": _numeric_field(packing_list, "net_weight_kg"),
        "empty_package_weight_kg": _numeric_field(packing_list, "empty_package_weight_kg"),
        "items_quantity": _numeric_field(packing_list, "items_quantity"),
    }
    optional_pallet_fields = {
        "pallet_weight_kg": _numeric_field(packing_list, "pallet_weight_kg"),
        "pallet_quantity": _numeric_field(packing_list, "pallet_quantity"),
    }

    observed_values = _observed(
        [
            value
            for value in [
                *base_fields.values(),
                has_pallets_value,
                *package_type_value,
                *optional_pallet_fields.values(),
            ]
            if value is not None
        ]
    )
    evidence = _evidence(
        [
            value
            for value in [
                *base_fields.values(),
                has_pallets_value,
                *package_type_value,
                *optional_pallet_fields.values(),
            ]
            if value is not None
        ]
    )
    confidence = _confidence(
        [
            value
            for value in [
                *base_fields.values(),
                has_pallets_value,
                *package_type_value,
                *optional_pallet_fields.values(),
            ]
            if value is not None
        ]
    )

    if any(value is None for value in base_fields.values()):
        if (
            base_fields["empty_package_weight_kg"] is None
            and base_fields["gross_weight_kg"] is not None
            and base_fields["net_weight_kg"] is not None
            and has_pallets_value is not None
            and bool(has_pallets_value.value)
            and all(value is not None for value in optional_pallet_fields.values())
        ):
            expected = float(base_fields["net_weight_kg"].value) + (
                float(optional_pallet_fields["pallet_weight_kg"].value)
                * float(optional_pallet_fields["pallet_quantity"].value)
            )
            actual = float(base_fields["gross_weight_kg"].value)
            status: ValidationStatus = "passed" if abs(actual - expected) <= context.tolerance else "failed"
            return _result(
                context,
                rule_code="R016",
                severity="error",
                status=status,
                message="Packing palletized gross weight formula is valid without separately stated empty package tare."
                if status == "passed"
                else "Packing palletized gross weight formula is invalid.",
                documents=["packing_list"],
                fields=[
                    "gross_weight_kg",
                    "net_weight_kg",
                    "has_pallets",
                    "pallet_weight_kg",
                    "pallet_quantity",
                ],
                observed_values=observed_values,
                expected_values={"packing_list.gross_weight_kg": expected, "tolerance": context.tolerance},
                evidence=evidence,
                confidence=confidence,
            )
        return _result(
            context,
            rule_code="R016",
            severity="error",
            status="skipped",
            message="One or more base fields for the detailed packing gross weight formula are missing.",
            documents=["packing_list"],
            fields=["gross_weight_kg", "net_weight_kg", "empty_package_weight_kg", "items_quantity"],
            observed_values=observed_values,
            evidence=evidence,
            confidence=confidence,
        )

    numeric_values = {field_name: float(value.value) for field_name, value in base_fields.items() if value is not None}
    expected = numeric_values["net_weight_kg"] + (
        numeric_values["empty_package_weight_kg"] * numeric_values["items_quantity"]
    )

    has_pallets = bool(has_pallets_value.value) if has_pallets_value is not None else None
    gross_net_delta = numeric_values["gross_weight_kg"] - numeric_values["net_weight_kg"]
    package_type = package_type_value[0].comparable if package_type_value else None

    if has_pallets:
        if any(value is None for value in optional_pallet_fields.values()):
            return _result(
                context,
                rule_code="R016",
                severity="error",
                status="skipped",
                message="Pallet details required for the detailed packing gross weight formula are missing.",
                documents=["packing_list"],
                fields=["pallet_weight_kg", "pallet_quantity"],
                observed_values=observed_values,
                evidence=evidence,
                confidence=confidence,
            )
        expected += float(optional_pallet_fields["pallet_weight_kg"].value) * float(
            optional_pallet_fields["pallet_quantity"].value
        )
    elif package_type in NON_PALLET_PACKAGE_TYPES and gross_net_delta > NON_PALLET_GROSS_NET_WARNING_THRESHOLD_KG:
        return _result(
            context,
            rule_code="R016",
            severity="warning",
            status="failed",
            message="Packing list indicates no pallets, but gross-minus-net weight is unusually high for bag/carton/box/package packaging. Check whether pallets are actually present.",
            documents=["packing_list"],
            fields=[
                "gross_weight_kg",
                "net_weight_kg",
                "package_type",
                "has_pallets",
                "pallet_weight_kg",
                "pallet_quantity",
            ],
            observed_values={
                **observed_values,
                "packing_list.gross_minus_net_weight_kg": round(gross_net_delta, 4),
            },
            expected_values={
                "max_non_pallet_gross_minus_net_weight_kg": NON_PALLET_GROSS_NET_WARNING_THRESHOLD_KG,
                "package_types_to_check_for_pallets": sorted(NON_PALLET_PACKAGE_TYPES),
            },
            evidence=evidence,
            confidence=confidence,
        )

    actual = numeric_values["gross_weight_kg"]
    status: ValidationStatus = "passed" if abs(actual - expected) <= context.tolerance else "failed"
    return _result(
        context,
        rule_code="R016",
        severity="error",
        status=status,
        message="Packing detailed gross weight formula is valid."
        if status == "passed"
        else "Packing detailed gross weight formula is invalid.",
        documents=["packing_list"],
        fields=[
            "gross_weight_kg",
            "net_weight_kg",
            "empty_package_weight_kg",
            "items_quantity",
            "has_pallets",
            "pallet_weight_kg",
            "pallet_quantity",
        ],
        observed_values=observed_values,
        expected_values={"packing_list.gross_weight_kg": expected, "tolerance": context.tolerance},
        evidence=evidence,
        confidence=confidence,
    )


def _rule_r017(context: RuleContext) -> ValidationResultRecord:
    return _presence_rule(
        context,
        rule_code="R017",
        severity="warning",
        document_type="packing_list",
        field_name="container_no",
        pass_message="Packing list contains container number.",
        fail_message="Packing list container number is missing.",
    )


def _rule_r018(context: RuleContext) -> ValidationResultRecord:
    addendum = context.doc("addendum")
    payment_terms = _field_values(addendum, "payment_terms") if addendum else []
    if not payment_terms:
        return _result(
            context,
            rule_code="R018",
            severity="warning",
            status="skipped",
            message="Addendum payment terms are missing.",
            documents=["addendum", "payment_confirmation"],
            fields=["payment_terms", "document_presence"],
        )

    requires_prepayment = any("prepayment" in str(value.comparable) for value in payment_terms)
    payment_confirmation = context.doc("payment_confirmation")
    status: ValidationStatus = "passed" if not requires_prepayment or payment_confirmation is not None else "failed"
    observed_values = _observed(payment_terms)
    observed_values["payment_confirmation.document"] = payment_confirmation.source_file_name if payment_confirmation else None
    return _result(
        context,
        rule_code="R018",
        severity="warning",
        status=status,
        message="Prepayment terms have payment confirmation or do not require it."
        if status == "passed"
        else "Prepayment terms require payment confirmation, but no payment confirmation document was found.",
        documents=["addendum", "payment_confirmation"],
        fields=["payment_terms", "document_presence"],
        observed_values=observed_values,
        evidence=_evidence(payment_terms),
        confidence=_confidence(payment_terms),
    )


def _rule_r019(context: RuleContext) -> ValidationResultRecord:
    return _presence_rule(
        context,
        rule_code="R019",
        severity="error",
        document_type="coa",
        field_name="batch_no",
        pass_message="COA contains batch number.",
        fail_message="COA batch number is missing.",
    )


def _rule_r020(context: RuleContext) -> ValidationResultRecord:
    return _presence_rule(
        context,
        rule_code="R020",
        severity="error",
        document_type="coa",
        field_name="manufacture_date",
        pass_message="COA contains manufacture date.",
        fail_message="COA manufacture date is missing.",
    )


def _rule_r021(context: RuleContext) -> ValidationResultRecord:
    coa = context.doc("coa")
    if coa is None:
        return _result(
            context,
            rule_code="R021",
            severity="warning",
            status="skipped",
            message="COA is missing.",
            documents=["coa"],
            fields=["expiry_date", "manufacture_date"],
        )

    expiry_date = _field_values(coa, "expiry_date")
    if expiry_date:
        return _result(
            context,
            rule_code="R021",
            severity="warning",
            status="passed",
            message="COA contains expiry date.",
            documents=["coa"],
            fields=["expiry_date"],
            observed_values=_observed(expiry_date),
            evidence=_evidence(expiry_date),
            confidence=_confidence(expiry_date),
        )

    manufacture_date = _field_values(coa, "manufacture_date")
    if manufacture_date:
        return _result(
            context,
            rule_code="R021",
            severity="warning",
            status="failed",
            message="COA expiry date is missing, but manufacture date is present.",
            documents=["coa"],
            fields=["expiry_date", "manufacture_date"],
            observed_values=_observed(manufacture_date),
            expected_values={"coa.expiry_date": "recommended when manufacture_date is present"},
            evidence=_evidence(manufacture_date),
            confidence=_confidence(manufacture_date),
        )

    return _result(
        context,
        rule_code="R021",
        severity="warning",
        status="skipped",
        message="COA expiry date and manufacture date are missing.",
        documents=["coa"],
        fields=["expiry_date", "manufacture_date"],
    )


def _rule_r022(context: RuleContext) -> ValidationResultRecord:
    bl = context.bill_of_lading()
    if bl is None:
        return _result(
            context,
            rule_code="R022",
            severity="error",
            status="skipped",
            message="Bill of Lading is missing.",
            documents=["coa", "hbl", "mbl"],
            fields=["manufacture_date", "bl_date"],
        )
    return _date_compare_rule(
        context,
        rule_code="R022",
        severity="error",
        left=("coa", "manufacture_date"),
        right=(bl.document_type, "bl_date"),
        operator="<",
        pass_message="COA manufacture date is before BL date.",
        fail_message="COA manufacture date is not before BL date.",
        skip_message="COA manufacture date or BL date is missing.",
    )


def _rule_r023(context: RuleContext) -> ValidationResultRecord:
    coa = context.doc("coa")
    if coa is None:
        return _result(
            context,
            rule_code="R023",
            severity="error",
            status="skipped",
            message="COA is missing, so expiry-after-manufacture comparison was skipped.",
            documents=["coa"],
            fields=["expiry_date", "manufacture_date"],
        )

    expiry_date = _field_values(coa, "expiry_date")
    manufacture_date = _field_values(coa, "manufacture_date")
    if not expiry_date or not manufacture_date:
        return _result(
            context,
            rule_code="R023",
            severity="error",
            status="skipped",
            message="COA expiry-after-manufacture comparison was skipped because one of the dates is missing.",
            documents=["coa"],
            fields=["expiry_date", "manufacture_date"],
            observed_values=_observed([*expiry_date, *manufacture_date]),
            evidence=_evidence([*expiry_date, *manufacture_date]),
            confidence=_confidence([*expiry_date, *manufacture_date]),
        )

    return _date_compare_rule(
        context,
        rule_code="R023",
        severity="error",
        left=("coa", "expiry_date"),
        right=("coa", "manufacture_date"),
        operator=">",
        pass_message="COA expiry date is after manufacture date.",
        fail_message="COA expiry date is not after manufacture date.",
        skip_message="COA expiry-after-manufacture comparison was skipped because one of the dates is missing.",
    )


def _rule_r024(context: RuleContext) -> ValidationResultRecord:
    bl = context.bill_of_lading()
    if bl is None:
        return _result(
            context,
            rule_code="R024",
            severity="error",
            status="skipped",
            message="Bill of Lading is missing.",
            documents=["hbl", "mbl", "packing_list"],
            fields=["gross_weight_kg"],
        )
    return _numeric_pair_rule(
        context,
        rule_code="R024",
        severity="error",
        left=(bl.document_type, "gross_weight_kg"),
        right=("packing_list", "gross_weight_kg"),
        pass_message="BL gross weight matches packing list gross weight.",
        fail_message="BL gross weight does not match packing list gross weight.",
        skip_message="BL or packing list gross weight is missing.",
    )


def _rule_r025(context: RuleContext) -> ValidationResultRecord:
    bl = context.bill_of_lading()
    if bl is None:
        return _result(
            context,
            rule_code="R025",
            severity="error",
            status="skipped",
            message="Bill of Lading is missing.",
            documents=["hbl", "mbl", "packing_list"],
            fields=["packages_quantity"],
        )

    packing_list = context.doc("packing_list")
    bl_values = _field_values(bl, "packages_quantity")
    packing_values = _field_values(packing_list, "packages_quantity") if packing_list else []
    pallet_values = _field_values(packing_list, "pallet_quantity") if packing_list else []
    values = [*bl_values, *packing_values, *pallet_values]

    if not bl_values or (not packing_values and not pallet_values):
        return _result(
            context,
            rule_code="R025",
            severity="error",
            status="skipped",
            message="BL vs packing-list package quantity comparison was skipped because the value was not extracted from both documents.",
            documents=[bl.document_type, "packing_list"],
            fields=["packages_quantity", "pallet_quantity"],
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    if any(value.uncertain for value in values):
        return _result(
            context,
            rule_code="R025",
            severity="error",
            status="needs_review",
            message="One or more compared values have low confidence or ambiguous candidates.",
            documents=[bl.document_type, "packing_list"],
            fields=["packages_quantity", "pallet_quantity"],
            observed_values=_observed(values),
            evidence=_evidence(values),
            confidence=_confidence(values),
        )

    bl_value = bl_values[0].comparable
    matched = any(value.comparable == bl_value for value in packing_values)
    matched_pallet_quantity = False
    if not matched and pallet_values:
        matched_pallet_quantity = any(value.comparable == bl_value for value in pallet_values)
        matched = matched_pallet_quantity

    status: ValidationStatus = "passed" if matched else "failed"
    return _result(
        context,
        rule_code="R025",
        severity="error",
        status=status,
        message=(
            "BL packages quantity matches packing list pallet quantity."
            if matched_pallet_quantity
            else "BL packages quantity matches packing list."
        )
        if status == "passed"
        else "BL packages quantity does not match packing list.",
        documents=[bl.document_type, "packing_list"],
        fields=["packages_quantity", "pallet_quantity"],
        observed_values=_observed(values),
        expected_values={"accepted_values": [value.value for value in [*packing_values, *pallet_values]]},
        evidence=_evidence(values),
        confidence=_confidence(values),
    )


def _rule_r026(context: RuleContext) -> ValidationResultRecord:
    bl = context.bill_of_lading()
    if bl is None:
        return _result(
            context,
            rule_code="R026",
            severity="error",
            status="skipped",
            message="Bill of Lading is missing.",
            documents=["hbl", "mbl", "packing_list"],
            fields=["container_no"],
        )
    return _exact_match_rule(
        context,
        rule_code="R026",
        severity="error",
        sources=((bl.document_type, "container_no"), ("packing_list", "container_no")),
        pass_message="BL container number matches packing list.",
        fail_message="BL container number does not match packing list.",
        skip_message="BL vs packing-list container number comparison was skipped because the value was not extracted from both documents.",
    )


def _rule_r027(context: RuleContext) -> ValidationResultRecord:
    bl = context.bill_of_lading()
    cargo_description = _field_values(bl, "cargo_description") if bl else []
    if bl is None or not cargo_description:
        return _result(
            context,
            rule_code="R027",
            severity="warning",
            status="skipped",
            message="BL cargo description is missing.",
            documents=[bl.document_type if bl else "hbl", "mbl"],
            fields=["cargo_description"],
            observed_values=_observed(cargo_description),
            evidence=_evidence(cargo_description),
            confidence=_confidence(cargo_description),
        )

    has_hs_code = any(HS_CODE_PATTERN.search(str(value.value)) for value in cargo_description)
    status: ValidationStatus = "failed" if has_hs_code else "passed"
    return _result(
        context,
        rule_code="R027",
        severity="warning",
        status=status,
        message="BL cargo description does not contain HS code."
        if status == "passed"
        else "BL cargo description contains HS code.",
        documents=[bl.document_type],
        fields=["cargo_description"],
        observed_values=_observed(cargo_description),
        evidence=_evidence(cargo_description),
        confidence=_confidence(cargo_description),
    )


RULES: tuple[Rule, ...] = (
    _rule_r001,
    _rule_r002,
    _rule_r003,
    _rule_r004,
    _rule_r005,
    _rule_r006,
    _rule_r007,
    _rule_r008,
    _rule_r009,
    _rule_r010,
    _rule_r011,
    _rule_r012,
    _rule_r013,
    _rule_r014,
    _rule_r015,
    _rule_r016,
    _rule_r017,
    _rule_r018,
    _rule_r019,
    _rule_r020,
    _rule_r021,
    _rule_r022,
    _rule_r023,
    _rule_r024,
    _rule_r025,
    _rule_r026,
    _rule_r027,
)
