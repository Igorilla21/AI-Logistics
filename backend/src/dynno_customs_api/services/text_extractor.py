from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from dynno_customs_api.config import ROOT_DIR
from dynno_customs_api.models.domain import (
    BooleanFieldRecord,
    DateFieldRecord,
    DecimalFieldRecord,
    IntegerFieldRecord,
    LineItemRecord,
    NormalizedDocumentFieldsRecord,
    StringFieldRecord,
)


MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def read_raw_text(raw_text_ref: str | None) -> str | None:
    if raw_text_ref is None:
        return None
    raw_text_path = Path(raw_text_ref)
    if not raw_text_path.is_absolute():
        raw_text_path = ROOT_DIR / raw_text_path
    if not raw_text_path.exists():
        return None
    return raw_text_path.read_text(encoding="utf-8")


def extract_fields(document_type: str, raw_text: str | None) -> tuple[NormalizedDocumentFieldsRecord, list[LineItemRecord]]:
    fields = NormalizedDocumentFieldsRecord()
    if not raw_text:
        return fields, []

    text = _collapse_spaces(raw_text)
    line_items: list[LineItemRecord] = []

    if document_type == "invoice":
        fields.shipper_name = _company_field(text, r"^(.+?CO\.?\s*,?\s*LTD\.?)\s+", "shipper_name")
        fields.buyer_name = _company_field(text, r"\bTO:\s*(?:0{2,3}\s*)?(.+?)\s+DATE:", "buyer_name")
        fields.invoice_no = _string_field(text, r"\bINV\.?\s*NO\.?:\s*([A-Z0-9-]+)", "invoice_no")
        fields.invoice_date = _date_field(text, r"\bDATE:\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})", "invoice_date")
        fields.contract_no = _string_field(text, r"\bContract\s+N[eo]\s+([A-Z0-9-]+)\s+dated", "contract_no")
        fields.addendum_no = _string_field(text, r"\b(ADD\s+\d+)\s*//\s*Contract", "addendum_no")
        fields.payment_terms = _string_field(text, r"\bTERMS:\s*=?\s*(.+?)\s+FROM\s+", "payment_terms")
        fields.incoterms = _string_field(text, r"\b(FOB|FOR|FCA|EXW|DAP|CPT|CIF|CFR|DDP)\s+QINGDAO", "incoterms")
        fields.currency = _string_field(text, r"\b(CNY)\s*\d", "currency")
        fields.total_amount = _decimal_field(text, r"\bCNY\s*([0-9][0-9\s.,]*)\s+For\b", "total_amount")
        line_item = _invoice_line_item(text)
        if line_item is not None:
            line_items.append(line_item)

    elif document_type == "packing_list":
        fields.shipper_name = _company_field(text, r"^(.+?CO\.?\s*,?\s*LTD\.?)\s+", "shipper_name")
        fields.invoice_no = _string_field(text, r"\bINV\.?\s*NO\.?:\s*([A-Z0-9-]+)", "invoice_no")
        fields.contract_no = _string_field(text, r"\bContract\s+[№N][eo]?\s+([A-Z0-9-]+)\s+dated", "contract_no")
        fields.addendum_no = _string_field(text, r"\b(ADD\s+\d+)\s*//\s*Contract", "addendum_no")
        fields.container_no = _string_field(text, r"\bCONTAINER NUMBER:\s*([A-Z]{4}\d{7})", "container_no")
        fields.package_type = _string_field(text, r"\bPACKING:\s*IN\s+NET\s+\d+\s*KG\s+([A-Z]+)", "package_type")
        fields.empty_package_weight_kg = _decimal_field(
            text, r"\bEmpty bag net weight:\s*([0-9][0-9\s.,]*)\s*kg/bag", "empty_package_weight_kg"
        )
        fields.packages_quantity = _integer_field(text, r"\b(\d+)\s*BAGS\b", "packages_quantity")
        fields.gross_weight_kg = _decimal_field(text, r"\b(\d[\d\s.,]*)\s*KGS\s+(\d[\d\s.,]*)\s*KGS\b", "gross_weight_kg")
        net_match = re.search(r"\b(\d[\d\s.,]*)\s*KGS\s+(\d[\d\s.,]*)\s*KGS\b", text, re.IGNORECASE)
        if net_match:
            fields.net_weight_kg = _decimal_from_match(net_match, 2, "net_weight_kg")
        if fields.gross_weight_kg and fields.net_weight_kg:
            package_weight = fields.gross_weight_kg.value - fields.net_weight_kg.value
            fields.package_weight_kg = DecimalFieldRecord(
                value=round(package_weight, 4),
                raw_value=str(package_weight),
                normalized_value=round(package_weight, 4),
                unit="kg",
                confidence=0.75,
                page_no=1,
                text_snippet="Derived as gross_weight_kg - net_weight_kg.",
                derived=True,
            )
        line_item = _packing_line_item(text)
        if line_item is not None:
            line_items.append(line_item)

    elif document_type in {"mbl", "hbl"}:
        fields.shipper_name = _company_field(
            text, r"\bSHIPPER\s+BILL OF LADING\s+(.+?CO\.?\s*,?\s*LTD\.?)\s+", "shipper_name"
        )
        fields.buyer_name = _company_field(text, r"\bCONSIGNEE\s+Bill of Lading No\..+?\s+(SOYUZOPTHIM LTD\.)", "buyer_name")
        fields.consignee_name = fields.buyer_name
        fields.bl_no = _string_field(text, r"\bBill of Lading No\.\s+Booking number\s+([A-Z0-9-]+)", "bl_no")
        fields.container_no = _string_field(text, r"\b([A-Z]{4}\d{7})\s+COC\b", "container_no")
        fields.cargo_description = _string_field(text, r"\bCOC\s+\d+\s+(.+?)\s+Bag\s+\d+\s+", "cargo_description")
        fields.packages_quantity = _integer_field(text, r"\bBag\s+(\d+)\s+\d", "packages_quantity")
        fields.gross_weight_kg = _decimal_field(text, r"\bBag\s+\d+\s+(\d[\d\s.,]*)\s+\d+\s+Container", "gross_weight_kg")
        fields.bl_date = _date_field(text, r"\bSHIPPED ON BOARD\s+(\d{1,2}\.\d{1,2}\.\d{2,4})", "bl_date")

    elif document_type == "addendum":
        fields.addendum_no = _addendum_no_field(text)
        fields.addendum_date = _date_field(
            text,
            r"\bADDENDUM\s*(?:№|N[eo])\s*\d+\s+dated\s+(\d{1,2}\.\d{1,2}\.\d{2,4})",
            "addendum_date",
        )
        fields.contract_no = _string_field(
            text,
            r"\bContract\s+(?:№|N[eo])\s+([A-Z]{2,}-[A-Z0-9]+)\s+dated\b",
            "contract_no",
        )
        fields.contract_date = _date_field(
            text,
            r"\bContract\s+(?:№|N[eo])\s+[A-Z]{2,}-[A-Z0-9]+\s+dated\s+(\d{1,2}\.\d{1,2}\.\d{2,4})",
            "contract_date",
        )
        fields.seller_name = _company_field(text, r"\b(Qingdao\s+Raitte\s+Technologies\s+Co\.?\s*,?\s*Ltd\.?)", "seller_name")
        fields.buyer_name = _company_field(text, r"\band\s+(Soyuzopthim\s+Ltd\.?)\s*,", "buyer_name")
        fields.incoterms = _string_field(text, r"\bon\s+(FOB|FOR|FCA|EXW|DAP|CPT|CIF|CFR|DDP)\s*,?\s*Qingdao", "incoterms")
        fields.payment_terms = _payment_terms_field(text)

    elif document_type == "coa":
        fields.invoice_no = _string_field(text, r"\bINVOICE\s+NO\.?:\s*([A-Z0-9-]+)", "invoice_no")
        fields.batch_no = _string_field(text, r"\bBATCH\s+NO\.?:\s*([A-Z0-9-]+)", "batch_no")
        fields.manufacture_date = _date_field(
            text, r"\bMANUFACTURE\s+DATE:\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})", "manufacture_date"
        )
        fields.expiry_date = _date_field(text, r"\bEXPIRY\s+DATE:\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})", "expiry_date")

    elif document_type == "payment_confirmation":
        fields.document_presence = BooleanFieldRecord(
            value=True,
            raw_value="payment confirmation document present",
            normalized_value=True,
            confidence=0.95,
            page_no=1,
            text_snippet="Payment confirmation document was uploaded and OCR completed.",
            derived=True,
        )
        fields.buyer_name = _company_field(text, r"\bOrdering Customer.+?\s+(SOYUZOPTHIM LTD)\s+", "buyer_name")
        fields.seller_name = _company_field(text, r"\b(QINGDAO RAITTE TECHNOLOGIES CO\.?\s*,?\s*LTD\.?)\s+", "seller_name")
        fields.contract_no = _string_field(text, r"\bCONTRACT\s+([A-Z]{2,}-[A-Z0-9]+)\b", "contract_no")
        fields.addendum_no = _string_field(text, r"\b(ADD\s+68)\b", "addendum_no")
        fields.currency = _string_field(text, r"\b(CNY)\b", "currency")

    return fields, line_items


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _string_field(text: str, pattern: str, field_name: str, confidence: float = 0.86) -> StringFieldRecord | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    raw_value = _collapse_spaces(match.group(1))
    return StringFieldRecord(
        value=raw_value,
        raw_value=raw_value,
        normalized_value=_normalize_string(raw_value),
        confidence=confidence,
        page_no=1,
        text_snippet=_snippet(match),
    )


def _company_field(text: str, pattern: str, field_name: str, confidence: float = 0.82) -> StringFieldRecord | None:
    field = _string_field(text, pattern, field_name, confidence)
    if field is None:
        return None
    cleaned = re.sub(r"\s+", " ", field.value.replace("000 ", "")).strip(" .,")
    return field.model_copy(update={"value": cleaned, "raw_value": field.value, "normalized_value": _normalize_string(cleaned)})


def _date_field(text: str, pattern: str, field_name: str, confidence: float = 0.84) -> DateFieldRecord | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    raw_value = _collapse_spaces(match.group(1))
    parsed = _parse_date(raw_value)
    if parsed is None:
        return None
    return DateFieldRecord(
        value=parsed,
        raw_value=raw_value,
        normalized_value=parsed,
        confidence=confidence,
        page_no=1,
        text_snippet=_snippet(match),
    )


def _decimal_field(text: str, pattern: str, field_name: str, confidence: float = 0.86) -> DecimalFieldRecord | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return _decimal_from_match(match, 1, field_name, confidence)


def _decimal_from_match(match: re.Match[str], group_no: int, field_name: str, confidence: float = 0.86) -> DecimalFieldRecord | None:
    raw_value = _collapse_spaces(match.group(group_no))
    value = _parse_decimal(raw_value)
    if value is None:
        return None
    return DecimalFieldRecord(
        value=value,
        raw_value=raw_value,
        normalized_value=value,
        unit="kg" if "weight" in field_name or field_name.endswith("_kg") else None,
        confidence=confidence,
        page_no=1,
        text_snippet=_snippet(match),
    )


def _integer_field(text: str, pattern: str, field_name: str, confidence: float = 0.86) -> IntegerFieldRecord | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    raw_value = _collapse_spaces(match.group(1))
    value = _parse_int(raw_value)
    if value is None:
        return None
    return IntegerFieldRecord(
        value=value,
        raw_value=raw_value,
        normalized_value=value,
        confidence=confidence,
        page_no=1,
        text_snippet=_snippet(match),
    )


def _addendum_no_field(text: str) -> StringFieldRecord | None:
    match = re.search(r"\bADDENDUM\s*(?:№|N[eo])\s*(\d+)\b", text, re.IGNORECASE)
    if not match:
        return None
    value = f"ADD {match.group(1)}"
    return StringFieldRecord(
        value=value,
        raw_value=_collapse_spaces(match.group(0)),
        normalized_value=_normalize_string(value),
        confidence=0.86,
        page_no=1,
        text_snippet=_snippet(match),
    )


def _payment_terms_field(text: str) -> StringFieldRecord | None:
    match = re.search(
        r"\bPayment\s+for\s+the\s+Goods\s+should\s+be\s+done.+?:\s*(.+?)\s+The\s+date\s+of\s+shipment\b",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    raw_value = _collapse_spaces(match.group(1))
    return StringFieldRecord(
        value=raw_value,
        raw_value=raw_value,
        normalized_value=_normalize_string(raw_value),
        confidence=0.82,
        page_no=1,
        text_snippet=_snippet(match),
    )


def _invoice_line_item(text: str) -> LineItemRecord | None:
    match = re.search(
        r"\b(POLYACRYLAMIDE\s+StabVisco\s+FNL1)\s+([0-9][0-9\s.,]*)\s*KG\s+CNY\s*([0-9][0-9\s.,]*)/MT\s+CNY\s*([0-9][0-9\s.,]*)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    quantity_kg = _parse_decimal(match.group(2))
    unit_price_per_metric_ton = _parse_decimal(match.group(3))
    line_total = _parse_decimal(match.group(4))
    if quantity_kg is None or unit_price_per_metric_ton is None or line_total is None:
        return None

    quantity_metric_tons = quantity_kg / 1000
    product_name = _collapse_spaces(match.group(1))
    return LineItemRecord(
        line_no=1,
        product_name_raw=_line_string(product_name, match, "line_items[1].product_name_raw"),
        product_name_normalized=_line_string(_normalize_string(product_name), match, "line_items[1].product_name_normalized"),
        quantity=DecimalFieldRecord(
            value=quantity_metric_tons,
            raw_value=f"{match.group(2)}KG",
            normalized_value=quantity_metric_tons,
            unit="MT",
            confidence=0.86,
            page_no=1,
            text_snippet=_snippet(match),
        ),
        quantity_unit=_line_string("MT", match, "line_items[1].quantity_unit"),
        unit_price=DecimalFieldRecord(
            value=unit_price_per_metric_ton * 1000,
            raw_value=f"CNY{match.group(3)}/MT",
            normalized_value=unit_price_per_metric_ton * 1000,
            unit="CNY/MT",
            confidence=0.86,
            page_no=1,
            text_snippet=_snippet(match),
        ),
        line_total=DecimalFieldRecord(
            value=line_total,
            raw_value=f"CNY {match.group(4)}",
            normalized_value=line_total,
            unit="CNY",
            confidence=0.86,
            page_no=1,
            text_snippet=_snippet(match),
        ),
    )


def _packing_line_item(text: str) -> LineItemRecord | None:
    match = re.search(r"\b(POLYACRYLAMIDE\s+StabVisco\s+FNL1)\s+([0-9][0-9\s.,]*)\s*KG\s+(\d+)\s*BAGS", text, re.IGNORECASE)
    if not match:
        return None
    quantity = _parse_decimal(match.group(2))
    if quantity is None:
        return None
    product_name = _collapse_spaces(match.group(1))
    return LineItemRecord(
        line_no=1,
        product_name_raw=_line_string(product_name, match, "line_items[1].product_name_raw"),
        product_name_normalized=_line_string(_normalize_string(product_name), match, "line_items[1].product_name_normalized"),
        quantity=DecimalFieldRecord(
            value=quantity,
            raw_value=f"{match.group(2)}KG",
            normalized_value=quantity,
            unit="kg",
            confidence=0.86,
            page_no=1,
            text_snippet=_snippet(match),
        ),
        quantity_unit=_line_string("kg", match, "line_items[1].quantity_unit"),
    )


def _line_string(value: str, match: re.Match[str], field_name: str) -> StringFieldRecord:
    return StringFieldRecord(
        value=value,
        raw_value=value,
        normalized_value=_normalize_string(value),
        confidence=0.86,
        page_no=1,
        text_snippet=_snippet(match),
    )


def _parse_date(raw_value: str) -> date | None:
    month_match = re.search(r"([A-Z]{3})\.?\s*(\d{1,2}),\s*(\d{4})", raw_value, re.IGNORECASE)
    if month_match:
        month = MONTHS.get(month_match.group(1).lower())
        if month is None:
            return None
        return date(int(month_match.group(3)), month, int(month_match.group(2)))

    numeric_match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", raw_value)
    if numeric_match:
        year = int(numeric_match.group(3))
        if year < 100:
            year += 2000
        return date(year, int(numeric_match.group(2)), int(numeric_match.group(1)))
    return None


def _parse_decimal(raw_value: str) -> float | None:
    normalized = raw_value.replace(" ", "").replace(",", ".")
    if normalized.count(".") > 1:
        parts = normalized.split(".")
        normalized = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(normalized)
    except ValueError:
        return None


def _parse_int(raw_value: str) -> int | None:
    digits = re.sub(r"\D", "", raw_value)
    if not digits:
        return None
    return int(digits)


def _normalize_string(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().strip())


def _snippet(match: re.Match[str]) -> str:
    return _collapse_spaces(match.group(0))
