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

ADDENDUM_TEXT = (
    "ADDENDUM №68 dated 25.03.2026 to the Contract Ne QRT-SOH dated 01.09.2025 "
    "Qingdao Raitte Technologies Co., Ltd., hereinafter referred to as the SELLER, as one party "
    "and Soyuzopthim Ltd., hereinafter referred to as the BUYER, as another party, have agreed "
    "The SELLER sells and the BUYER buys on FOB, Qingdao, CHINA terms (Incoterms 2020) "
    "2. PAYMENT CONDITIONS Payment for the Goods should be done by the BUYER on the following conditions: "
    "Prepayment 50%, Payment from shipment date 50% within 60 days "
    "The date of shipment means the date of corresponding Bill of Lading"
)

COA_TEXT = (
    "ANHUI TIANRUN CHEMICALS CO., LTD. CERTIFICATE OF ANALYSIS DATE: APR.13,2026 "
    "INVOICE NO.: 26RTO0004 PRODUCT NAME: STABVISCO FNL1 BATCH NO.: 95320172 "
    "MANUFACTURE DATE: MAR.08,2026 EXPIRY DATE: MAR.07,2028"
)

PAYMENT_CONFIRMATION_TEXT = (
    "Ordering Customer (Name, address, city, country) SOYUZOPTHIM LTD BOLSHAYA POROHOVSKAYA "
    "Beneficiary Customer QINGDAO RAITTE TECHNOLOGIES CO., LTD. Details of payment "
    "HSCODE 390690 FOR FLOCCULANT PAYMENT TO THE CONTRACT QRT-SOH DD 01.09.2025, ADD 68,69 DD 25.03.26 "
    "CNY 188400,00"
)

ADDENDUM_TEXT_REAL = (
    "Additional agreement №3 to the Contract № DNKM-SOH 2018 dated 01.10.2018 "
    "Saint Petersburg 24.12.2018 "
    "Form of payment 100% payment within 90 days after the B/L has been issued"
)

COA_TEXT_REAL = (
    "CERTIFICATE OF ANALYSIS INDUSTRY GRADE "
    "Lot-No.: 20250528 Manufacturing Date: MAY. 28, 2025 "
    "Date of Issue: MAY. 28, 2025"
)

PAYMENT_CONFIRMATION_TEXT_REAL = (
    "Payment order Ordering customer Soyuzopthim, Ltd "
    "Beneficiary Denkim Denizli Kimya San. ve Tic. A.S. "
    "Payment to the CONTRACT for PAC-LV. Contr DNKM-SOH 2018 dd 01.10.2018"
)

CO_TEXT_REAL = (
    "1. Exporter SHANDONG PAINI NEW MATERIAL CO., LTD "
    "2. Consignee SOYUZOPTHIM LTD. "
    "10. Number and date of invoices PN2025051504 MAY 15, 2025 "
    "25126KGS G.W. produced in China"
)

BL_TEXT_REAL = (
    "THROUGH TRANSPORT BILL OF LADING "
    "Shipper HENAN AIERFUKE CHEMICALS CO.,LTD. "
    "BILL OF LADING NUMBER LED417527A "
    "Consignee SOYUZOPTHIM LTD. "
    "CONTAINER NUMBER CLHU3822754 20GP COC STF805711 "
    "POLY ALUMINIUM CHLORIDE 880 BAGS "
    "SHIPPED ON BOARD 10.06.2025"
)

BL_TEXT_TABLE_REAL = (
    "SHIPPER\n"
    "BILL OF LADING\n"
    "QINGDAO RAITTE TECHNOLOGIES CO.,LTD\n"
    "CONSIGNEE\n"
    "Bill of Lading No. Booking number\n"
    "LED432374 LED432374\n"
    "SOYUZOPTHIM LTD.\n"
    "Description of packages and goods as stated by shipper. Said to contain.\n"
    "CONTAINER NUMBER NUMBER CARGO DESCRIPTION PACKAGES KGS VOLUME M3\n"
    "JZPU2136329 COC 001280 POLYACRYLAMIDE Bag 720 18 144 27\n"
    "Container(s) 20 DC*1\n"
    "TOTAL: 720 18 144\n"
    "ABOVE PARTICULARS DECLARED BY SHIPPER.\n"
    "SHIPPED ON BOARD 17.04.26\n"
)

BL_TEXT_PDF_LAYER_REAL = (
    "THROUGH TRANSPORT BILL OF LADING\n"
    "Shipper\n"
    "BOOKING NUMBER\n"
    "BILL OF LADING NUMBER\n"
    "HENAN AIERFUKE CHEMICALS CO.,LTD.\n"
    "LED417527A\n"
    "LED417527A\n"
    "Consignee\n"
    "SOYUZOPTHIM LTD.\n"
    "CONTAINER NUMBER\n"
    "CONTAINER TYPE\n"
    "SOC/COC\n"
    "SEAL NUMBER\n"
    "CARGO DESCRIPTION\n"
    "NO. OF\n"
    "PACKAGES\n"
    "TYPE OF\n"
    "PACKAGES\n"
    "NET WEIGHT KGS GROSS WEIGHT KGS\n"
    "VOLUME M3\n"
    "CLHU3822754\n"
    "20GP\n"
    "COC\n"
    "STF805711\n"
    "POLY ALUMINIUM CHLORIDE\n"
    "880\n"
    "BAGS\n"
    "22088\n"
    "30\n"
    "TOTAL\n"
    "880\n"
    "22088\n"
    "30\n"
    "SHIPPED ON BOARD\n"
    "10.06.2025\n"
)

AIERFUKE_ADDENDUM_TEXT = (
    "ADDENDUM № Add 05 dated 22.05.2025 to the Contract Ne AIERFUKE-SOH dated 17.01.2025 "
    "Henan Aierfuke Chemicals Co., Ltd., hereinafter referred to as the SELLER, as one party and "
    "Soyuzopthim Ltd., hereinafter referred to as the BUYER, as another party, have agreed on the following: "
    "The SELLER sells and the BUYER buys on FOB, Qingdao, CHINA terms (Incoterms 2020). "
    "Payment for the Goods should be done by the BUYER on the following conditions: Prepayment 100% "
    "The date of shipment means the date of corresponding Bill of Lading."
)

AIERFUKE_INVOICE_TEXT = (
    "TAY PS Be ON A уче ЕН BR ZS] HENAN ATERFUKE CHEMICALS CO., LTD. "
    "COMMERCIAL INVOICE "
    "INVOICE NO.: 2025С1065-05 ADDENDUM NO.: ADD 05 "
    "DATE:JUN. 01, 2025 "
    "S/C NO.: AIERFUKE-SOH "
    "THE SELLER: HENAN CONJOIN-WIN INTERNATIONAL TRADING CO.,LTD "
    "THE MANUFACTURER: HENAN AIERFUKE CHEMICALS СО., LTD. "
    "THE BUYER: SOYUZOPTHIM LTD. "
    "FROM: QINGDAO, CHINA TO:VRANGEL, RUSSIA "
    "POLY ALUMINIUM CHLORIDE INDUSTRIAL GRADE 22 42900 "
    "FOB QINGDAO "
    "PAYMENT: 100% T/T IN ADVANCE"
)

AIERFUKE_PACKING_TEXT = (
    "PACKING LIST "
    "INVOICE NO.: 2025С1065-05 ADDENDUM NO.: ADD 05 "
    "DATE:JUN. 01, 2025 "
    "S/C NO.: ATIERFUKE-SOH "
    "THE SELLER: HENAN CONJOIN-WIN INTERNATIONAL TRADING CO.,LTD "
    "THE MANUFACTURER: HENAN АТЕВЕОКЕ CHEMICALS CO., LTD. "
    "THE BUYER: SOYUZOPTHIM LTD. "
    "PAYMENT: 100% T/T IN ADVANCE. "
    "CONTAINER NO.: CLHU3822754 "
    "PACKING :25KGS/BAG POLY ALUMINIUM CHLORIDE 22088 22000 30 "
    "880BAGS INDUSTRIAL GRADE MADE IN CHINA"
)

AIERFUKE_BL_TEXT = (
    "THROUGH TRANSPORT BILL OF LADING\n"
    "Shipper\n"
    "BOOKING NUMBER BILL OF LADING NUMBER\n"
    "HENAN АТЕВРОКЕ CHEMICALS CO.,LTD.\n"
    "THE (WEST) INDUSTRIES CLUSTER AREA OF JIAOZUO CITY, HENAN PROVINCE,CHINA\n"
    "TEL:(+86 391)3126812 LED417527A LED417527A\n"
    "Consignee\n"
    "SOYUZOPTHIM LTD.\n"
    "CLHU3822754 20GP COC STF805711 POLY ALUMINIUM CHLORIDE 880 BAGS\n"
    "TOTAL NUMBER OF CARGO PLACES RECEIVED BY THE CARRIER SHIPPED ON BOARD 10.06.2025\n"
)

AIERFUKE_CO_TEXT = (
    "1. Exporter HENAN ATERFUKE CHEMICALS CO. , LTD. "
    "2. Consignee SOYUZOPTHIM LTD. "
    "10. Number and date of invoices "
    "N/M TWO THOUSAND SIX HUNDRED AND FORTY (2640) 66264KGS G.W. | 2025C1065 "
    "BAGS OF POLY ALUMINIUM CHLORIDE JUN. 01, 2025 "
    "produced in China"
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
    assert fields.has_pallets.value is False
    assert fields.items_quantity.value == 720
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


def test_extract_addendum_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("addendum", ADDENDUM_TEXT)

    assert fields.addendum_no.value == "ADD 68"
    assert fields.addendum_date.value.isoformat() == "2026-03-25"
    assert fields.contract_no.value == "QRT-SOH"
    assert fields.contract_date.value.isoformat() == "2025-09-01"
    assert fields.incoterms.value == "FOB"
    assert fields.payment_terms.value == "Prepayment 50%, Payment from shipment date 50% within 60 days"


def test_extract_coa_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("coa", COA_TEXT)

    assert fields.invoice_no.value == "26RTO0004"
    assert fields.batch_no.value == "95320172"
    assert fields.manufacture_date.value.isoformat() == "2026-03-08"
    assert fields.expiry_date.value.isoformat() == "2028-03-07"


def test_extract_payment_confirmation_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("payment_confirmation", PAYMENT_CONFIRMATION_TEXT)

    assert fields.document_presence.value is True
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.seller_name.value == "QINGDAO RAITTE TECHNOLOGIES CO., LTD"
    assert fields.contract_no.value == "QRT-SOH"
    assert fields.addendum_no.value == "ADD 68"


def test_extract_addendum_fields_from_realistic_text_variants() -> None:
    fields, _ = extract_fields("addendum", ADDENDUM_TEXT_REAL)

    assert fields.addendum_no.value == "ADD 3"
    assert fields.contract_no.value == "DNKM-SOH 2018"
    assert fields.contract_date.value.isoformat() == "2018-10-01"
    assert fields.payment_terms.value == "100% payment within 90 days after the B/L has been issued"


def test_extract_coa_fields_from_realistic_text_variants() -> None:
    fields, _ = extract_fields("coa", COA_TEXT_REAL)

    assert fields.batch_no.value == "20250528"
    assert fields.manufacture_date.value.isoformat() == "2025-05-28"


def test_extract_payment_confirmation_fields_from_realistic_text_variants() -> None:
    fields, _ = extract_fields("payment_confirmation", PAYMENT_CONFIRMATION_TEXT_REAL)

    assert fields.buyer_name.value == "Soyuzopthim, Ltd"
    assert fields.seller_name.value == "Denkim Denizli Kimya San. ve Tic. A.S"
    assert fields.contract_no.value == "DNKM-SOH 2018"


def test_extract_certificate_of_origin_fields_from_realistic_text_variants() -> None:
    fields, _ = extract_fields("certificate_of_origin", CO_TEXT_REAL)

    assert fields.shipper_name.value == "SHANDONG PAINI NEW MATERIAL CO., LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.invoice_no.value == "PN2025051504"
    assert fields.invoice_date.value.isoformat() == "2025-05-15"
    assert fields.gross_weight_kg.value == 25126.0
    assert fields.origin_country.value == "China"


def test_extract_bill_of_lading_fields_from_realistic_text_variants() -> None:
    fields, _ = extract_fields("mbl", BL_TEXT_REAL)

    assert fields.shipper_name.value == "HENAN AIERFUKE CHEMICALS CO.,LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.bl_no.value == "LED417527A"
    assert fields.container_no.value == "CLHU3822754"
    assert fields.packages_quantity.value == 880
    assert fields.bl_date.value.isoformat() == "2025-06-10"


def test_extract_bill_of_lading_gross_weight_from_multiline_table_text() -> None:
    fields, _ = extract_fields("mbl", BL_TEXT_TABLE_REAL)

    assert fields.gross_weight_kg.value == 18144.0


def test_extract_bill_of_lading_gross_weight_from_pdf_text_layer_table() -> None:
    fields, _ = extract_fields("mbl", BL_TEXT_PDF_LAYER_REAL)

    assert fields.bl_no.value == "LED417527A"
    assert fields.container_no.value == "CLHU3822754"
    assert fields.packages_quantity.value == 880
    assert fields.gross_weight_kg.value == 22088.0


def test_extract_aierfuke_addendum_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("addendum", AIERFUKE_ADDENDUM_TEXT)

    assert fields.addendum_no.value == "ADD 05"
    assert fields.contract_no.value == "AIERFUKE-SOH"
    assert fields.seller_name.value == "Henan Aierfuke Chemicals Co., Ltd"
    assert fields.buyer_name.value == "Soyuzopthim Ltd"
    assert fields.payment_terms.value == "Prepayment 100%"


def test_extract_aierfuke_invoice_fields_from_ocr_text() -> None:
    fields, line_items = extract_fields("invoice", AIERFUKE_INVOICE_TEXT)

    assert fields.shipper_name.value == "HENAN AIERFUKE CHEMICALS CO., LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.invoice_no.value == "2025C1065-05"
    assert fields.contract_no.value == "AIERFUKE-SOH"
    assert fields.addendum_no.value == "ADD 05"
    assert fields.total_amount.value == 42900.0
    assert len(line_items) == 1
    assert line_items[0].product_name_raw.value == "POLY ALUMINIUM CHLORIDE INDUSTRIAL GRADE"
    assert line_items[0].quantity.value == 22.0
    assert line_items[0].unit_price.value == 1950.0
    assert line_items[0].line_total.value == 42900.0


def test_extract_aierfuke_packing_list_fields_from_ocr_text() -> None:
    fields, line_items = extract_fields("packing_list", AIERFUKE_PACKING_TEXT)

    assert fields.shipper_name.value == "HENAN ATEBEOKE CHEMICALS CO., LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.invoice_no.value == "2025C1065-05"
    assert fields.contract_no.value == "ATIERFUKE-SOH"
    assert fields.addendum_no.value == "ADD 05"
    assert fields.container_no.value == "CLHU3822754"
    assert fields.package_type.value == "BAG"
    assert fields.packages_quantity.value == 880
    assert fields.gross_weight_kg.value == 22088.0
    assert fields.net_weight_kg.value == 22000.0
    assert fields.package_weight_kg.value == 88.0
    assert round(fields.empty_package_weight_kg.value, 2) == 0.10
    assert len(line_items) == 1
    assert line_items[0].quantity.value == 22000.0


def test_extract_aierfuke_bill_of_lading_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("mbl", AIERFUKE_BL_TEXT)

    assert fields.shipper_name.value == "HENAN ATEBPOKE CHEMICALS CO.,LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.bl_no.value == "LED417527A"
    assert fields.container_no.value == "CLHU3822754"
    assert fields.packages_quantity.value == 880
    assert fields.bl_date.value.isoformat() == "2025-06-10"


def test_extract_aierfuke_certificate_of_origin_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("certificate_of_origin", AIERFUKE_CO_TEXT)

    assert fields.shipper_name.value == "HENAN ATERFUKE CHEMICALS CO. , LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.invoice_no.value == "2025C1065"
    assert fields.invoice_date.value.isoformat() == "2025-06-01"
    assert fields.gross_weight_kg.value == 66264.0
