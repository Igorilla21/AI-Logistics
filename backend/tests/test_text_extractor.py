from dynno_customs_api.services.text_extractor import extract_fields


INVOICE_TEXT = (
    "QINGDAO RAITTE TECHNOLOGIES CO.,LTD. ROOM 302 COMMERCIAL INVOICE "
    "TO:000 SOYUZOPTHIM LTD DATE: APR.13,2026 INV.NO.: 26RT0004 "
    "S/C NO.: RT260004 ADD 68 // Contract Ne QRT-SOH dated 01.09.2025 "
    "TERMS: = 50% T/T INADVANCE 50% AFTER 60DAYS AGAINST B/L DATE FROM QINGDAO PORT, CHINA "
    "DESCRIPTION OF GOODS & QUANTITY UNIT PRICE TOTAL AMOUNT FOB QINGDAO PORT, CHINA "
    "POLYACRYLAMIDE StabVisco FNL1 18000.00KG CNY9.1000/MT CNY 163800.00 "
    "PACKING: IN NET 25KG BAG CNY 163800.00 For and on behalf"
)

PACKING_TEXT = (
    "QINGDAO RAITTE TECHNOLOGIES CO.,LTD ROOM 302 PACKING LIST DATE: APR. 13, 2026 "
    "INV. NO.:26RT0004 S/C NO.: RT260004// ADD 68 // Contract № QRT-SOH dated 01.09.2025 "
    "POLYACRYLAMIDE StabVisco FNL1 18000.00KG 720BAGS 18144.00 KGS 18000.00 KGS "
    "Empty bag net weight: 0.2kg/bag PACKING: IN NET 25KG BAG "
    "CONTAINER NUMBER: JZPU2136329 (95320172)"
)

BL_TEXT = (
    "SHIPPER BILL OF LADING QINGDAO RAITTE TECHNOLOGIES CO.,LTD ROOM302 CONSIGNEE "
    "Bill of Lading No. Booking number LED432374 LED432374 "
    "SOYUZOPTHIM LTD. INN 7806468630 "
    "JZPU2136329 COC 001280 POLYACRYLAMIDE Bag 720 18 144 27 Container(s) "
    "TOTAL: 720 18 144 SHIPPED ON BOARD 17.04.26"
)


def test_extract_invoice_fields_from_ocr_text() -> None:
    fields, line_items = extract_fields("invoice", INVOICE_TEXT)

    assert fields.invoice_no.value == "26RT0004"
    assert fields.contract_no.value == "QRT-SOH"
    assert fields.addendum_no.value == "ADD 68"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.invoice_date.value.isoformat() == "2026-04-13"
    assert fields.total_amount.value == 163800.0
    assert len(line_items) == 1
    assert line_items[0].quantity.value == 18.0
    assert line_items[0].quantity.unit == "MT"
    assert line_items[0].unit_price.value == 9100.0
    assert line_items[0].line_total.value == 163800.0


def test_extract_packing_list_fields_from_ocr_text() -> None:
    fields, line_items = extract_fields("packing_list", PACKING_TEXT)

    assert fields.invoice_no.value == "26RT0004"
    assert fields.contract_no.value == "QRT-SOH"
    assert fields.addendum_no.value == "ADD 68"
    assert fields.container_no.value == "JZPU2136329"
    assert fields.packages_quantity.value == 720
    assert fields.gross_weight_kg.value == 18144.0
    assert fields.net_weight_kg.value == 18000.0
    assert fields.package_weight_kg.value == 144.0
    assert fields.empty_package_weight_kg.value == 0.2
    assert len(line_items) == 1
    assert line_items[0].quantity.value == 18000.0


def test_extract_bill_of_lading_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("mbl", BL_TEXT)

    assert fields.bl_no.value == "LED432374"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.container_no.value == "JZPU2136329"
    assert fields.cargo_description.value == "POLYACRYLAMIDE"
    assert fields.packages_quantity.value == 720
    assert fields.gross_weight_kg.value == 18144.0
    assert fields.bl_date.value.isoformat() == "2026-04-17"
