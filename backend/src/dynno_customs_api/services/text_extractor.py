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
        "у": "y",
        "х": "x",
        "к": "k",
        "м": "m",
        "н": "h",
        "в": "b",
        "і": "i",
        "І": "I",
    }
)


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

    raw_text = _repair_ocr_text(raw_text)
    multiline_text = _normalize_multiline_text(raw_text)
    text = _collapse_spaces(multiline_text)
    line_items: list[LineItemRecord] = []

    if document_type == "invoice":
        manufacturer_name = _first_company_field(
            text,
            "manufacturer_name",
            [
                r"\bTHE MANUFACTURER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED))",
                r"\bMANUFACTURER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED))",
            ],
            confidence=0.84,
        )
        fields.shipper_name = manufacturer_name or _first_company_field(
            text,
            "shipper_name",
            [
                r"\bTHE SELLER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED))",
                r"\bSELLER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED))",
            ],
            confidence=0.82,
        )
        fields.manufacturer_name = manufacturer_name
        fields.buyer_name = _first_company_field(
            text,
            "buyer_name",
            [
                r"\bTHE BUYER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:LTD\.?|LIMITED))",
                r"\bBUYER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:LTD\.?|LIMITED))",
                r"\bTO:\s*(?:0{2,3}\s*)?([A-Z][A-Z0-9&.,'\" ()/-]+(?:LTD\.?|LIMITED))\b",
            ],
            confidence=0.84,
        )
        fields.invoice_no = _first_string_field(
            text,
            "invoice_no",
            [
                r"\bINVOICE\s+NO\.?:\s*([A-Z0-9-]+)\b",
                r"\bINV\.?\s*NO\.?:\s*([A-Z0-9-]+)\b",
            ],
        )
        fields.invoice_date = _first_date_field(
            multiline_text,
            "invoice_date",
            [
                r"(?im)^\s*DATE:\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})\b",
                r"\bDATE:\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})\b",
            ],
        )
        fields.contract_no = _normalize_contract_field(
            _first_string_field(
                text,
                "contract_no",
                [
                    r"\bContract\s*(?:№|No\.?|N[eo])\s*([A-Z0-9 -]+)\s+dated\b",
                    r"\bS/C\s+NO\.?:\s*([A-Z0-9-]+)\b",
                ],
            )
        )
        fields.addendum_no = _normalize_addendum_field(
            _first_string_field(
                text,
                "addendum_no",
                [
                    r"\bINVOICE\s+NO\.?:\s*[A-Z0-9-]+\s+ADDENDUM\s+NO\.?:\s*((?:ADD\s*)?\d+)\b",
                    r"\b((?:ADD\s*)\d+)\s*//\s*Contract\b",
                ],
            )
        )
        fields.payment_terms = _first_string_field(
            multiline_text,
            "payment_terms",
            [
                r"(?im)^\s*PAYMENT:\s*([^\n]+)$",
                r"\bTERMS:\s*=?\s*(.+?)\s+FROM\s+",
            ],
            confidence=0.82,
        )
        fields.incoterms = _first_string_field(
            text,
            "incoterms",
            [
                r"\b(FOB|FOR|FCA|EXW|DAP|CPT|CIF|CFR|DDP)\s+QINGDAO\b",
                r"\b(FOB|FOR|FCA|EXW|DAP|CPT|CIF|CFR|DDP)\b",
            ],
        )
        fields.currency = _first_string_field(text, "currency", [r"\b(CNY)\b"], confidence=0.82)
        fields.total_amount = _decimal_field(text, r"\bCNY\s*([0-9][0-9\s.,]*)\s+For\b", "total_amount")
        line_item = _invoice_line_item(text)
        if line_item is not None:
            line_items.append(line_item)
            if fields.total_amount is None and line_item.line_total is not None:
                fields.total_amount = DecimalFieldRecord(
                    value=line_item.line_total.value,
                    raw_value=line_item.line_total.raw_value or str(line_item.line_total.value),
                    normalized_value=line_item.line_total.value,
                    unit="CNY",
                    confidence=0.7,
                    page_no=1,
                    text_snippet="Derived from the only extracted invoice line total.",
                    derived=True,
                )

    elif document_type == "packing_list":
        manufacturer_name = _first_company_field(
            text,
            "manufacturer_name",
            [
                r"\bTHE MANUFACTURER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED))",
                r"\bMANUFACTURER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED))",
            ],
            confidence=0.84,
        )
        fields.shipper_name = manufacturer_name or _first_company_field(
            text,
            "shipper_name",
            [
                r"\bTHE SELLER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED))",
                r"\bSELLER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED))",
            ],
            confidence=0.82,
        )
        fields.manufacturer_name = manufacturer_name
        fields.buyer_name = _first_company_field(
            text,
            "buyer_name",
            [
                r"\bTHE BUYER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:LTD\.?|LIMITED))",
                r"\bBUYER:\s*([A-Z][A-Z0-9&.,'\" ()/-]+(?:LTD\.?|LIMITED))",
            ],
            confidence=0.84,
        )
        fields.invoice_no = _first_string_field(
            text,
            "invoice_no",
            [
                r"\bINVOICE\s+NO\.?:\s*([A-Z0-9-]+)\b",
                r"\bINV\.?\s*NO\.?:\s*([A-Z0-9-]+)\b",
            ],
        )
        fields.contract_no = _normalize_contract_field(
            _first_string_field(
                text,
                "contract_no",
                [
                    r"\bContract\s+[№N][eo]?\s+([A-Z0-9 -]+)\s+dated\b",
                    r"\bS/C\s+NO\.?:\s*([A-Z0-9-]+)\b",
                ],
            )
        )
        fields.addendum_no = _normalize_addendum_field(
            _first_string_field(
                text,
                "addendum_no",
                [
                    r"\bINVOICE\s+NO\.?:\s*[A-Z0-9-]+\s+ADDENDUM\s+NO\.?:\s*((?:ADD\s*)?\d+)\b",
                    r"\b((?:ADD\s*)\d+)\s*//\s*Contract\b",
                ],
            )
        )
        fields.container_no = _first_string_field(
            text,
            "container_no",
            [
                r"\bCONTAINER\s+NO\.?:\s*([A-Z]{4}\d{7})\b",
                r"\bCONTAINER\s+NUMBER:\s*([A-Z]{4}\d{7})\b",
            ],
        )
        fields.package_type = _first_string_field(
            text,
            "package_type",
            [
                r"\bPACKING\s*:?\s*(?:IN\s+NET\s+)?\d+\s*KGS?/([A-Z]+)\b",
                r"\bPACKING\s*:?\s*(?:IN\s+NET\s+)?\d+\s*KG\s+([A-Z]+)\b",
            ],
            confidence=0.82,
        )
        fields.empty_package_weight_kg = _decimal_field(
            text, r"\bEmpty bag net weight:\s*([0-9][0-9\s.,]*)\s*kg/bag", "empty_package_weight_kg"
        )
        fields.has_pallets = _pallet_presence_field(text)
        fields.items_quantity = _first_integer_field(
            text,
            "items_quantity",
            [
                r"\b(\d+)\s*BAGS\b",
                r"\b(\d+)\s*PCS\b",
                r"\b(\d+)\s*UNITS\b",
            ],
        )
        fields.packages_quantity = _integer_field(text, r"\b(\d+)\s*BAGS\b", "packages_quantity")
        gross_weight_field, net_weight_field = _weight_pair_fields(text)
        fields.gross_weight_kg = gross_weight_field
        fields.net_weight_kg = net_weight_field
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
            if fields.empty_package_weight_kg is None and fields.packages_quantity and fields.packages_quantity.value:
                empty_package_weight = package_weight / float(fields.packages_quantity.value)
                fields.empty_package_weight_kg = DecimalFieldRecord(
                    value=round(empty_package_weight, 4),
                    raw_value=str(round(empty_package_weight, 4)),
                    normalized_value=round(empty_package_weight, 4),
                    unit="kg",
                    confidence=0.72,
                    page_no=1,
                    text_snippet="Derived as package_weight_kg / packages_quantity.",
                    derived=True,
                )
        line_item = _packing_line_item(text, fields)
        if line_item is not None:
            line_items.append(line_item)

    elif document_type in {"mbl", "hbl"}:
        fields.shipper_name = _bill_of_lading_party_field(multiline_text, "shipper")
        fields.buyer_name = _first_company_field(
            multiline_text,
            "buyer_name",
            [
                r"(?im)^\s*CONSIGNEE\s+(SOYUZOPTHIM\s+LTD\.?)(?=\s+(?:INN|CONTAINER|BILL OF LADING NUMBER|$))",
                r"(?im)^\s*Consignee\s+(SOYUZOPTHIM\s+LTD\.?)(?=\s+(?:INN|CONTAINER|BILL OF LADING NUMBER|$))",
                r"(?im)^\s*(SOYUZOPTHIM\s+LTD\.?)\s*$",
            ],
        )
        if fields.buyer_name is None:
            fields.buyer_name = _first_company_field(
                text,
                "buyer_name",
                [
                    r"\bCONSIGNEE\s+(SOYUZOPTHIM\s+LTD\.?)(?=\s+(?:INN|CONTAINER|BILL OF LADING NUMBER|$))",
                    r"\bCONSIGNEE\b.*?(SOYUZOPTHIM\s+LTD\.?)(?=\s+(?:INN|CONTAINER|$))",
                    r"\bConsignee\s+(SOYUZOPTHIM\s+LTD\.?)(?=\s+(?:INN|CONTAINER|BILL OF LADING NUMBER|$))",
                    r"\bConsignee\b.*?(SOYUZOPTHIM\s+LTD\.?)(?=\s+(?:INN|CONTAINER|$))",
                ],
            )
        fields.consignee_name = fields.buyer_name
        fields.bl_no = _bill_of_lading_number_field(multiline_text, text)
        fields.container_no = _string_field(text, r"\b([A-Z]{4}\d{7})\b", "container_no")
        fields.cargo_description = _first_string_field(
            text,
            "cargo_description",
            [
                r"\b(POLYACRYLAMIDE)\b",
                r"\b(POLY ALUMINIUM CHLORIDE)\b",
                r"\b(TALLOW AMINE DISTILLED PNA-TAD)\b",
                r"\b(POLYANIONIC CELLULOSE LV)\b",
                r"\bSaid to contain\.?\s+(?:\d+\s+(?:BAGS|PALLETS|DRUMS)\s+)?(.+?)\s+(?:Contract No|Additional agreement|QUANTITY|TOTAL|HS CODE)\b",
                r"\bCargo Description.*?(POLY [A-Z ]+|TALLOW AMINE DISTILLED PNA-TAD|POLYANIONIC CELLULOSE LV)\b",
                r"\bDescription of goods.*?(POLY [A-Z ]+|TALLOW AMINE DISTILLED PNA-TAD|POLYANIONIC CELLULOSE LV)\b",
            ],
            confidence=0.76,
        )
        fields.packages_quantity = _first_integer_field(
            text,
            "packages_quantity",
            [
                r"\b(\d+)\s*BAGS\b",
                r"\bBag\s+(\d+)\b",
                r"\b(\d+)\s*PALLETS\b",
                r"\b(\d+)\s*DRUMS\b",
            ],
            confidence=0.8,
        )
        fields.gross_weight_kg = _first_decimal_field(
            text,
            "gross_weight_kg",
            [
                r"\bGROSS WEIGHT(?:,\s*KGS| KGS)?\s*(\d[\d\s.,]*)\b",
                r"\b(\d[\d\s.,]*)\s*KGS\s+(?:TOTAL|HS CODE|FREIGHT|30\.0000 CBM|27 Container)",
                r"\b(\d[\d\s.,]*)KGS\s*G\.?W\.?",
                r"\bTOTAL:\s*\d+\s+(\d[\d\s.,]*)\s+SHIPPED ON BOARD\b",
                r"\bTOTAL:\s*\d+\s+(\d[\d\s.,]*)\s+ABOVE PARTICULARS\b",
            ],
            confidence=0.78,
        )
        fields.bl_date = _first_date_field(
            text,
            "bl_date",
            [
                r"\bSHIPPED ON BOARD\s+(\d{1,2}\.\d{1,2}\.\d{2,4})",
                r"\bShipped on board\b.*?(\d{4}-\d{2}-\d{2})",
            ],
        )

    elif document_type == "addendum":
        fields.addendum_no = _addendum_no_field(text)
        fields.addendum_date = _first_date_field(
            text,
            "addendum_date",
            [
                r"\bADDENDUM\s*(?:№|N[eo])?\s*(?:ADD\s*)?\d+\s+dated\s+(\d{1,2}\.\d{1,2}\.\d{2,4})",
                r"\bAdditional agreement\s*(?:№|No\.?)\s*\d+.*?(\d{1,2}\.\d{1,2}\.\d{2,4})",
                r"\bПРИЛОЖЕНИЕ\s*№\s*(?:Add\s*)?\d+\s*от\s*(\d{1,2}\.\d{1,2}\.\d{2,4})",
            ],
        )
        fields.contract_no = _normalize_contract_field(
            _first_string_field(
            text,
            "contract_no",
            [
                r"\bContract\s*(?:№|No\.?|N[eo])\s*([A-Z]{2,}(?:\s*-\s*|\-)[A-Z0-9]+(?:\s+\d{4})?)",
                r"\bКонтракту?\s*№\s*([A-Z]{2,}(?:\s*-\s*|\-)[A-Z0-9]+(?:\s+\d{4})?)",
            ],
            )
        )
        fields.contract_date = _first_date_field(
            text,
            "contract_date",
            [
                r"\bContract\s*(?:№|No\.?|N[eo]).+?\sdated\s+(\d{1,2}\.\d{1,2}\.\d{2,4})",
                r"\bКонтракту?\s*№.+?\s*от\s*(\d{1,2}\.\d{1,2}\.\d{2,4})",
            ],
        )
        fields.seller_name = _addendum_party_field(multiline_text, "seller")
        fields.buyer_name = _addendum_party_field(multiline_text, "buyer")
        fields.incoterms = _first_string_field(
            text,
            "incoterms",
            [
                r"\bon\s+(FOB|FOR|FCA|EXW|DAP|CPT|CIF|CFR|DDP)\s*,?\s*[A-Z][A-ZA-Z ]+",
                r"\bусловиях\s+(FOB|FOR|FCA|EXW|DAP|CPT|CIF|CFR|DDP)\b",
            ],
        )
        fields.payment_terms = _payment_terms_field(text)

    elif document_type == "coa":
        fields.manufacturer_name = _first_company_field(
            multiline_text,
            "manufacturer_name",
            [r"(?im)^\s*([^\n]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|A\.S\.|STI\.|LIMITED))\s*$"],
            confidence=0.8,
        )
        fields.invoice_no = _first_string_field(
            text,
            "invoice_no",
            [
                r"\bINVOICE\s+NO\.?:\s*([A-Z0-9-]+)",
                r"\b10\.\s*Number and date of invoices\s+([A-Z0-9-]+)",
            ],
        )
        fields.batch_no = _first_string_field(
            text,
            "batch_no",
            [
                r"\bBATCH\s*(?:NO\.?|No\.?|N0\.?)[:\s]*([A-Z0-9-]+)",
                r"\bBatchNo[:\s]*([A-Z0-9-]+)",
                r"\bLot-No\.?:\s*([A-Z0-9-]+)",
            ],
        )
        fields.manufacture_date = _first_date_field(
            text,
            "manufacture_date",
            [
                r"\bMANUFACTURE\s+DATE:\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})",
                r"\bManufacturing\s+Date:\s*\|?\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})",
                r"\bMANUFACTURE\s+DATE:\s*(\d{4}-\d{2}-\d{2})",
            ],
        )
        fields.expiry_date = _first_date_field(
            text,
            "expiry_date",
            [
                r"\bEXPIRY\s+DATE:\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})",
                r"\bEXPIRY\s+DATE:\s*(\d{4}-\d{2}-\d{2})",
                r"\bBEST\s+BEFORE:\s*([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})",
            ],
        )

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
        fields.buyer_name = _first_company_field(
            text,
            "buyer_name",
            [
                r"\bOrdering customer\b.*?(SOYUZOPTHIM[, ]+LTD\.?)",
                r"\b1/Soyuzopthim,\s*Ltd\b",
                r"\b(SOYUZOPTHIM\s+LTD)\b",
            ],
            confidence=0.8,
        )
        fields.seller_name = _first_company_field(
            text,
            "seller_name",
            [
                r"\bBeneficiary(?: Customer)?\b.*?([A-Z][A-Z0-9&.,'\" ()/-]+(?:CO\.?\s*,?\s*LTD\.?|LTD\.?|A\.S\.|STI\.|LIMITED))",
                r"\b(QINGDAO RAITTE TECHNOLOGIES CO\.?\s*,?\s*LTD\.?)\b",
                r"\b(DENKIM DENIZLI KIMYA SAN\.? VE TIC\.? A\.S\.?)\b",
            ],
            confidence=0.8,
        )
        fields.contract_no = _first_string_field(
            text,
            "contract_no",
            [
                r"\bCONTRACT\s+([A-Z]{2,}(?:-[A-Z0-9]+)+(?:\s+\d{4})?)",
                r"\bContr\s+([A-Z]{2,}(?:-[A-Z0-9]+)+(?:\s+\d{4})?)",
            ],
        )
        fields.addendum_no = _first_string_field(
            text,
            "addendum_no",
            [
                r"\b(ADD\s+\d+)\b",
                r"\bAdditional agreement\s+No:?\s*(\d+)",
            ],
        )
        if fields.addendum_no is not None and fields.addendum_no.value.isdigit():
            value = f"ADD {fields.addendum_no.value}"
            fields.addendum_no = fields.addendum_no.model_copy(
                update={
                    "value": value,
                    "normalized_value": _normalize_string(value),
                }
            )
        fields.currency = _first_string_field(
            text,
            "currency",
            [
                r"\b32:\s*(USD|EUR|CNY|RUB)\b",
                r"\b(CNY|USD|EUR|RUB)\b",
            ],
        )

    elif document_type == "certificate_of_origin":
        fields.shipper_name = _first_company_field(
            multiline_text,
            "shipper_name",
            [r"(?im)^\s*1\.\s*Exporter\s+(.+?)(?=\s+2\.\s*Consignee\b|$)"],
            confidence=0.8,
        )
        fields.buyer_name = _first_company_field(
            multiline_text,
            "buyer_name",
            [r"(?im)^\s*2\.\s*Consignee\s+(SOYUZOPTHIM\s+LTD\.?)(?=\s+10\.\s*Number and date of invoices\b|$)"],
            confidence=0.8,
        )
        if fields.buyer_name is None:
            fields.buyer_name = _first_company_field(
                text,
                "buyer_name",
                [r"\b2\.\s*Consignee\s+(SOYUZOPTHIM\s+LTD\.?)(?=\s+10\.\s*Number and date of invoices\b|$)"],
                confidence=0.8,
            )
        fields.consignee_name = fields.buyer_name
        fields.invoice_no = _first_string_field(
            text,
            "invoice_no",
            [
                r"\b10\.\s*Number and date of invoices\b.*?\|\s*([A-Z0-9-]{8,})\b",
                r"\b10\.\s*Number and date of invoices\b.*?\b([A-Z0-9-]{8,})\b",
                r"\b10\.\s*Number and date of invoices\s+([A-Z0-9-]{5,})",
            ],
        )
        fields.invoice_date = _first_date_field(
            text,
            "invoice_date",
            [
                r"\b10\.\s*Number and date of invoices\s+[A-Z0-9-]+\s+([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})",
                r"\b10\.\s*Number and date of invoices\s+[A-Z0-9-]+\s+([A-Z]{3}\.\s*\d{1,2},\s*\d{4})",
                r"\b10\.\s*Number and date of invoices\b.*?([A-Z]{3}\.?\s*\d{1,2},\s*\d{4})",
            ],
        )
        fields.gross_weight_kg = _first_decimal_field(
            text,
            "gross_weight_kg",
            [r"\b(\d{3,}(?:[ .]\d{3})*(?:[.,]\d+)?)\s*KGS\s*G\.?\s*W\.?"],
            confidence=0.8,
        )
        fields.origin_country = _first_string_field(
            text,
            "origin_country",
            [r"\bproduced in\s+(China)\b", r"\bPeople's Republic of\s+(China)\b"],
            confidence=0.78,
        )

    return fields, line_items


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_multiline_text(value: str) -> str:
    normalized_lines = [_collapse_spaces(line) for line in value.splitlines()]
    return "\n".join(line for line in normalized_lines if line)


def _repair_ocr_text(value: str) -> str:
    return value.translate(OCR_CONFUSABLES).replace("\u00a0", " ")


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


def _first_string_field(
    text: str, field_name: str, patterns: list[str], confidence: float = 0.86
) -> StringFieldRecord | None:
    for pattern in patterns:
        field = _string_field(text, pattern, field_name, confidence)
        if field is not None:
            return field
    return None


def _company_field(text: str, pattern: str, field_name: str, confidence: float = 0.82) -> StringFieldRecord | None:
    field = _string_field(text, pattern, field_name, confidence)
    if field is None:
        return None
    cleaned = re.sub(r"\s+", " ", _repair_ocr_text(field.value).replace("000 ", "")).strip(" .,")
    return field.model_copy(update={"value": cleaned, "raw_value": field.value, "normalized_value": _normalize_string(cleaned)})


def _first_company_field(
    text: str, field_name: str, patterns: list[str], confidence: float = 0.82
) -> StringFieldRecord | None:
    for pattern in patterns:
        field = _company_field(text, pattern, field_name, confidence)
        if field is not None:
            return field
    return None


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


def _first_date_field(text: str, field_name: str, patterns: list[str], confidence: float = 0.84) -> DateFieldRecord | None:
    for pattern in patterns:
        field = _date_field(text, pattern, field_name, confidence)
        if field is not None:
            return field
    return None


def _decimal_field(text: str, pattern: str, field_name: str, confidence: float = 0.86) -> DecimalFieldRecord | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return _decimal_from_match(match, 1, field_name, confidence)


def _first_decimal_field(
    text: str, field_name: str, patterns: list[str], confidence: float = 0.86
) -> DecimalFieldRecord | None:
    for pattern in patterns:
        field = _decimal_field(text, pattern, field_name, confidence)
        if field is not None:
            return field
    return None


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


def _first_integer_field(
    text: str, field_name: str, patterns: list[str], confidence: float = 0.86
) -> IntegerFieldRecord | None:
    for pattern in patterns:
        field = _integer_field(text, pattern, field_name, confidence)
        if field is not None:
            return field
    return None


def _addendum_no_field(text: str) -> StringFieldRecord | None:
    match = re.search(
        r"\b(?:ADDENDUM|Additional agreement|ПРИЛОЖЕНИЕ)\s*(?:№|N[eo]\.?)?\s*(?:Add\s*)?(\d+)\b",
        text,
        re.IGNORECASE,
    )
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
    patterns = [
        r"\bPayment\s+for\s+the\s+Goods\s+should\s+be\s+done.+?:\s*(.+?)\s+The\s+date\s+of\s+shipment\b",
        r"\bОплата\s+за\s+товар.+?:\s*(.+?)\s+Под\s+датой\s+отгрузки\b",
        r"\bForm\s+of\s+payment\s+(.+?)(?:\s+4\s+|\s+Дополнительное\s+соглашение\b|$)",
    ]
    return _first_string_field(text, "payment_terms", patterns, confidence=0.82)


def _normalize_contract_field(field: StringFieldRecord | None) -> StringFieldRecord | None:
    if field is None:
        return None
    value = re.sub(r"\s*-\s*", "-", _repair_ocr_text(field.value))
    value = re.sub(r"\s+", " ", value).strip(" .,")
    return field.model_copy(update={"value": value, "normalized_value": _normalize_string(value)})


def _normalize_addendum_field(field: StringFieldRecord | None) -> StringFieldRecord | None:
    if field is None:
        return None
    match = re.search(r"(\d+)", field.value)
    if not match:
        return field
    value = f"ADD {match.group(1)}"
    return field.model_copy(update={"value": value, "normalized_value": _normalize_string(value)})


def _pallet_presence_field(text: str) -> BooleanFieldRecord:
    has_pallets = re.search(r"\bpallets?\b", text, re.IGNORECASE) is not None
    snippet = "Pallet term found in packing list text." if has_pallets else "No pallet terms found in packing list text."
    return BooleanFieldRecord(
        value=has_pallets,
        raw_value=snippet,
        normalized_value=has_pallets,
        confidence=0.72 if has_pallets else 0.68,
        page_no=1,
        text_snippet=snippet,
        derived=True,
    )


def _weight_pair_fields(text: str) -> tuple[DecimalFieldRecord | None, DecimalFieldRecord | None]:
    patterns = [
        r"\b(\d[\d\s.,]*)\s*KGS\s+(\d[\d\s.,]*)\s*KGS\b",
        r"\bPACKING\s*:.*?\b(\d{4,}(?:[.,]\d+)?)\s+(\d{4,}(?:[.,]\d+)?)\s+\d+\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match is None:
            continue
        return (
            _decimal_from_match(match, 1, "gross_weight_kg"),
            _decimal_from_match(match, 2, "net_weight_kg"),
        )
    return None, None


def _bill_of_lading_party_field(multiline_text: str, party: str) -> StringFieldRecord | None:
    inline_patterns = {
        "shipper": [
            r"\bShipper\s+(.+?)(?=\s+BILL OF LADING NUMBER|\s+Consignee\b|$)",
            r"\bSHIPPER\s+(.+?)(?=\s+BILL OF LADING NUMBER|\s+CONSIGNEE\b|$)",
        ],
        "consignee": [
            r"\bConsignee\s+(.+?)(?=\s+Notify address|\s+CONTAINER|\s+BILL OF LADING NUMBER|$)",
            r"\bCONSIGNEE\s+(.+?)(?=\s+Notify address|\s+CONTAINER|\s+BILL OF LADING NUMBER|$)",
        ],
    }
    inline_field = _first_company_field(multiline_text, party, inline_patterns.get(party, []), confidence=0.8)
    if inline_field is not None and "BOOKING NUMBER" not in inline_field.value.upper():
        return inline_field

    lines = [line for line in multiline_text.splitlines() if line]
    labels = {"shipper": {"shipper"}, "consignee": {"consignee", "notify address"}}
    party_labels = labels.get(party, set())
    if not party_labels:
        return None

    for index, line in enumerate(lines):
        if line.casefold().strip(" :") not in party_labels:
            continue
        candidates = lines[index + 1 : index + 4]
        for candidate in candidates:
            upper = candidate.upper()
            if not candidate or "BILL OF LADING NUMBER" in upper or "BOOKING NUMBER" in upper:
                continue
            if re.search(r"(CO\.?\s*,?\s*LTD\.?|LTD\.?|LIMITED|SOYUZOPTHIM)", upper):
                return StringFieldRecord(
                    value=candidate.strip(" .,"),
                    raw_value=candidate,
                    normalized_value=_normalize_string(candidate),
                    confidence=0.8,
                    page_no=1,
                    text_snippet=f"{line} {candidate}",
                )
    return None


def _addendum_party_field(multiline_text: str, party: str) -> StringFieldRecord | None:
    regex_patterns = {
        "seller": [
            r"\b(Henan\s+[A-Za-z ]+?Chemicals\s+Co\.?,?\s*Ltd\.?)\s*,?\s+hereinafter\s+referred\s+to\s+as\s+the\s+SELLER\b",
            r"\b(Henan\s+[A-Za-z ]+?Chemicals\s+Co\.?,?\s*Ltd\.?)\s*,?\s+именуемый\b",
        ],
        "buyer": [
            r"\b(Soyuzopthim\s+Ltd\.?)\s*,?\s+hereinafter\s+referred\s+to\s+as\s+the\s+BUYER\b",
            r"\b(OOO\s+[«\"]?Союзоптхим[»\"]?)\s*,?\s+именуемый\b",
        ],
    }
    regex_field = _first_company_field(multiline_text, party, regex_patterns.get(party, []), confidence=0.8)
    if regex_field is not None:
        return regex_field

    lines = [line for line in multiline_text.splitlines() if line]
    english_marker = "SELLER" if party == "seller" else "BUYER"
    russian_marker = "ПРОДАВЕЦ" if party == "seller" else "ПОКУПАТЕЛЬ"

    for index, line in enumerate(lines):
        window = " ".join(lines[index : index + 3])
        if english_marker in window and "hereinafter" in window.casefold():
            candidate = lines[index].strip(" .,")
            return StringFieldRecord(
                value=candidate,
                raw_value=candidate,
                normalized_value=_normalize_string(candidate),
                confidence=0.8,
                page_no=1,
                text_snippet=window,
            )
        if russian_marker in window and "именуем" in window.casefold():
            candidate = lines[index].strip(" .,")
            return StringFieldRecord(
                value=candidate,
                raw_value=candidate,
                normalized_value=_normalize_string(candidate),
                confidence=0.78,
                page_no=1,
                text_snippet=window,
            )
    return None


def _bill_of_lading_number_field(multiline_text: str, text: str) -> StringFieldRecord | None:
    lines = [line for line in multiline_text.splitlines() if line]
    for index, line in enumerate(lines):
        if "BILL OF LADING NUMBER" not in line.upper():
            continue
        window = " ".join(lines[index : index + 4])
        repeated = re.search(r"\b([A-Z]{3,}\d[A-Z0-9-]*)\b(?:\s+\1\b)", window)
        if repeated is not None:
            return StringFieldRecord(
                value=repeated.group(1),
                raw_value=repeated.group(1),
                normalized_value=_normalize_string(repeated.group(1)),
                confidence=0.82,
                page_no=1,
                text_snippet=window,
            )
        token_match = re.search(r"\bBILL OF LADING NUMBER\s+([A-Z]{2,}\d[A-Z0-9-]*)\b", window)
        if token_match is not None:
            return StringFieldRecord(
                value=token_match.group(1),
                raw_value=token_match.group(1),
                normalized_value=_normalize_string(token_match.group(1)),
                confidence=0.82,
                page_no=1,
                text_snippet=window,
            )

    patterns = [
        r"(?ims)BILL OF LADING NUMBER.*?\n(?:[^\n]*\n){0,3}?([A-Z]{3,}\d{5,}[A-Z0-9-]*)\b(?:\s+\1\b)?",
        r"\bBILL OF LADING NUMBER\s+([A-Z]{2,}\d[A-Z0-9-]*)\b",
        r"\bB/L\s+No:?\s*([A-Z0-9-]+)",
        r"\bBill of Lading No\.?\s*(?:Booking number\s+)?([A-Z0-9-]+)",
        r"\bSEJJ\s+вл\.\s*№\s*([A-Z0-9-]+)",
    ]
    field = _first_string_field(multiline_text, "bl_no", patterns)
    if field is None:
        field = _first_string_field(text, "bl_no", patterns)
    return field


def _invoice_line_item(text: str) -> LineItemRecord | None:
    match = re.search(
        r"\b(POLYACRYLAMIDE\s+StabVisco\s+FNL1)\s+([0-9][0-9\s.,]*)\s*KG\s+CNY\s*([0-9][0-9\s.,]*)/MT\s+CNY\s*([0-9][0-9\s.,]*)",
        text,
        re.IGNORECASE,
    )
    if match:
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
            product_name_normalized=_line_string(
                _normalize_string(product_name), match, "line_items[1].product_name_normalized"
            ),
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

    aluminium_match = re.search(
        r"\b(POLY ALUMINIUM CHLORIDE)\s+INDUSTRIAL GRADE\s+([0-9][0-9\s.,]*)\s+([0-9][0-9\s.,]*)\b",
        text,
        re.IGNORECASE,
    )
    if aluminium_match is None:
        return None

    quantity_metric_tons = _parse_decimal(aluminium_match.group(2))
    line_total = _parse_decimal(aluminium_match.group(3))
    if quantity_metric_tons is None or line_total is None or quantity_metric_tons == 0:
        return None

    unit_price = round(line_total / quantity_metric_tons, 4)
    product_name = f"{_collapse_spaces(aluminium_match.group(1))} INDUSTRIAL GRADE"
    return LineItemRecord(
        line_no=1,
        product_name_raw=_line_string(product_name, aluminium_match, "line_items[1].product_name_raw"),
        product_name_normalized=_line_string(
            _normalize_string(product_name), aluminium_match, "line_items[1].product_name_normalized"
        ),
        quantity=DecimalFieldRecord(
            value=quantity_metric_tons,
            raw_value=aluminium_match.group(2),
            normalized_value=quantity_metric_tons,
            unit="MT",
            confidence=0.78,
            page_no=1,
            text_snippet=_snippet(aluminium_match),
        ),
        quantity_unit=_line_string("MT", aluminium_match, "line_items[1].quantity_unit"),
        unit_price=DecimalFieldRecord(
            value=unit_price,
            raw_value=str(unit_price),
            normalized_value=unit_price,
            unit="CNY/MT",
            confidence=0.68,
            page_no=1,
            text_snippet="Derived as line_total / quantity for the only detected invoice line item.",
            derived=True,
        ),
        line_total=DecimalFieldRecord(
            value=line_total,
            raw_value=aluminium_match.group(3),
            normalized_value=line_total,
            unit="CNY",
            confidence=0.78,
            page_no=1,
            text_snippet=_snippet(aluminium_match),
        ),
    )


def _packing_line_item(text: str, fields: NormalizedDocumentFieldsRecord | None = None) -> LineItemRecord | None:
    match = re.search(r"\b(POLYACRYLAMIDE\s+StabVisco\s+FNL1)\s+([0-9][0-9\s.,]*)\s*KG\s+(\d+)\s*BAGS", text, re.IGNORECASE)
    if not match:
        if fields is None or fields.net_weight_kg is None:
            return None
        aluminium_match = re.search(r"\b(POLY ALUMINIUM CHLORIDE)\b", text, re.IGNORECASE)
        if aluminium_match is None:
            return None
        product_name = _collapse_spaces(aluminium_match.group(1))
        if re.search(r"\bINDUSTRIAL GRADE\b", text, re.IGNORECASE):
            product_name = f"{product_name} INDUSTRIAL GRADE"
        return LineItemRecord(
            line_no=1,
            product_name_raw=_line_string(product_name, aluminium_match, "line_items[1].product_name_raw"),
            product_name_normalized=_line_string(
                _normalize_string(product_name), aluminium_match, "line_items[1].product_name_normalized"
            ),
            quantity=DecimalFieldRecord(
                value=fields.net_weight_kg.value,
                raw_value=fields.net_weight_kg.raw_value or str(fields.net_weight_kg.value),
                normalized_value=fields.net_weight_kg.value,
                unit="kg",
                confidence=0.76,
                page_no=1,
                text_snippet="Derived from packing-list net weight for the only detected product row.",
                derived=True,
            ),
            quantity_unit=_line_string("kg", aluminium_match, "line_items[1].quantity_unit"),
        )
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
        try:
            return date(int(month_match.group(3)), month, int(month_match.group(2)))
        except ValueError:
            return None

    numeric_match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", raw_value)
    if numeric_match:
        year = int(numeric_match.group(3))
        if year < 100:
            year += 2000
        try:
            return date(year, int(numeric_match.group(2)), int(numeric_match.group(1)))
        except ValueError:
            return None

    iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw_value)
    if iso_match:
        try:
            return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None
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
    text = _repair_ocr_text(value).casefold().strip()
    text = re.sub(r"[|]+", " ", text)
    text = re.sub(r"[.,;:]+", " ", text)
    text = re.sub(r"\b(co)\s*,?\s*(ltd)\b", r"\1 \2", text)
    text = re.sub(r"\b(company|limited liability company)\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _snippet(match: re.Match[str]) -> str:
    return _collapse_spaces(match.group(0))
