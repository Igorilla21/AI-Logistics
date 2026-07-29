from datetime import UTC, datetime
from uuid import uuid4

from dynno_customs_api.models.domain import OcrDocumentResultRecord, OcrPageResultRecord, OcrTextLineRecord
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

DENKIM_COA_TEXT = (
    "MATERIAL CERTIFICATE OF ANALYSIS "
    "DENKIM DENIZLI KIMYA SAN. VE TIC. A. S. (COA) "
    "SOYUZOPTHIM LTD. Date: 03.01.2019 "
    "Material: PAC Lot No 1752/2018 "
    "Chemical Name: Polyanionic Cellulose Production Date 29.12.2018 "
    "Chemical Character: Cellulose Ether Expiry Date 29.12.2020 "
    "Commercial Name: DENCELL PAC LV Quantity Nett 18,000"
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

TIANRUN_BL_TEXT_WITH_LEGAL_NOISE = (
    "FAST SHIPPING LINE\n"
    "ORIGINAL BL\n"
    "SHIPPER (COMPLETE NAME,ADDRESS AND PHONE) B/L No: |FASTGT1911WVRA320\n"
    "SOYUZOPTHIM LTD. INN 7806468630 indicated above stated by the shipper to comprise the cargo specified above "
    "Delivery of the Goods will only be made on payment of all Freight andcharges. "
    "LLC ESTMA LEGAL ADDRESS: 1 1 7638, Moscow, UL ODESSKAYA D.2, POM. VI, ROOM 24. "
    "INN 7721 541 425 TEL: +7 (495) 003 7862 incurred as a result of such inspections. "
    "PARTICULARS DECLARED BY SHIPPER BUT NOT ACKOWLEDGED BY THE CARRIER\n"
    "Shipping Container No. GROSS MEASURMENT (CU\n"
    "Seal No. Quantity and DESCRIPTION OF GOODS (SAID TO CONTAIN) WEIGHT(KILOS) METRES)\n"
    "720 BAGS 18144.000KGS 27.000CBM\n"
    "POLYACRYLAMIDE\n"
    "UACU3704865/523589/20GP\n"
    "FASTGT1911WVRA320\n"
    "2025-10-07\n"
    "720BAGS/18144.000KGS/27.000CBM\n"
    "TOTAL NUMBER OF CONTAINERS OR SAY TOTAL: SEVEN HUNDRED AND TWENTY BAGS ONLY.\n"
)

DENKIM_INVOICE_TEXT = (
    "COMMERCIAL INVOICE\n"
    "Shipper/Exporter\n"
    "Invoice No. Invoice Date\n"
    "DENKIM DENIZLI KIMYA SAN.VE TIC.A.S.\n"
    "DDI2019000000007 03.01.2019\n"
    "Addendum No.: CONTRACT NO,:\n"
    "DNKM-SOH 2018\n"
    "3 dated:24.12.2018 dated : 01.10.2018\n"
    "SOYUZOPTHIM LTD\n"
    "Terms of Delivery _ Payment Terms\n"
    "BATCH . :\n"
    "NO Packing Nett Weight\n"
    "18,000.00\n"
    "KGS\n"
    "Description Of The Goods\n"
    "standard 25 kg bags with pallets\n"
    "1752/2018\n"
    "Quantity (kgs)\n"
    "100% PAYMENT WITHIN 90 DAYS AFTER\n"
    "THE B/L\n"
    "CIF NOVOROSSIYSK-\n"
    "RUSSIA\n"
    "Total Pallets\n"
    "Gross\n"
    "Weight Custom Tariff Code\n"
    "18,600.00\n"
    "KGS\n"
    "20 Pallets 39.12.31.0000\n"
    "Price USD/Mt TOTAL AMOUNT\n"
    "18,000.00 KGS\n"
    "Polyanionic Cellulose LV\n"
    "22,140.00 USD\n"
    "1,230.00 USD\n"
    "TOTAL AMOUNT CIF\n"
    "NOVOROSSIYSK :\n"
    "22,140.00 USD\n"
)

DENKIM_PACKING_TEXT = (
    "PACKING LIST\n"
    "Invoice No.: DDI2019000000007\n"
    "Addendum No.:\n"
    "3 dated:24.12.2018\n"
    "CONTRACT NO.: | dated: 01.10.2018\n"
    "Name of Product Polyanionic Cellulose LV\n"
    "DENKIM DENIZLI KIMYA SAN.VE TIC.A.S.\n"
    "Manufacturer\n"
    "NETT WEIGHT\n"
    "GROSS WEIGHT\n"
    "18,000 KGS\n"
    "18,600 KGS\n"
    "PACKING standard 25 kg bags with pallets\n"
    "TOTAL PALLETS 20 Pallets\n"
    "CONTAINER EACH TOTAL TOTAL EACH EACH TOTAL TOTAL\n"
    "NO BAG BAGS PALLET PALLET PALLET PALLET PALLET\n"
    "25 350 10 875 905 8,750 9,050\n"
    "PONU 007775-4\n"
    "25 370 10 925 9,250 9,550\n"
    "18,000 18,600\n"
    "TOTAL 720 20\n"
)

HUGESTONE_ADDENDUM_TEXT = (
    "ADD 01-HS dated MAR. 20, 2025 to the Contract No. HS-SOH dated 01.03.2025 "
    "Hugestone Enterprise Co., Ltd., hereinafter referred to as the SELLER, as one party "
    "and Soyuzopthim Ltd., hereinafter referred to as the BUYER, as another party."
)

HUGESTONE_INVOICE_TEXT = (
    "COMMERCIAL INVOICE "
    "BUYER: \"SOYUZOPTHIM\" LTD "
    "INVOICE NO.: 225CW11165 "
    "DATE: MAR.28, 2025 "
    "TERMS OF PAYMENT: 60% DEPOSIT AND 40%FROM SHIPMENT DATE WITHIN 5 DAYS "
    "FOB QINGDAO,BY SEA "
    "N/M XANTHAN GUM 20000 KG| RMB16.9/KG ¥ 338,000.00"
)

HUGESTONE_PACKING_TEXT = (
    "PACKING LIST "
    "BUYER: \"SOYUZOPTHIM\" LTD "
    "INVOICE NO.: 225CW11165 "
    "XANTHAN GUM "
    "800 BAGS 20,160.00 KGS | 20,000.00 KGS "
    "PACKING: IN EIGHT HUNDRED(800) BAGS, 25KGS NET EACH ONLY."
)

HUGESTONE_COA_TEXT = (
    "CERTIFICATE OF ANALYSIS "
    "COMMODITY : Xanthan Gum "
    "QUANTITY : 20,000KG "
    "PACKING : 25KG/BAG "
    "BATCH NO. : 520250226032 "
    "MANUFACTURE DATE ss: FEB 26,2025 "
    "EXPIRY DATE : FEB 25,2027"
)

HUGESTONE_BL_TEXT = (
    "BILL OF LADING\n"
    "SHIPPER\n"
    "HUGESTONE ENTERPRISE CO., LTD.\n"
    "CONSIGNEE: SHIPPING AGENT:\n"
    "\"SOYUZOPTHIM\" LTD\n"
    "TOTAL: 800BAGS 20160KGS 27CBM\n"
    "XANTHAN GUM\n"
    "SHIPPED ON BOARD MAR.30,2025\n"
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

AIERFUKE_PACKING_TEXT_WITH_PDF_LAYER = (
    "PACKING LIST\n"
    "INVOICE NO.: 2025С1065-05 ADDENDUM NO.: ADD 05\n"
    "DATE:JUN. 01, 2025\n"
    "S/C NO.: ATIERFUKE-SOH\n"
    "THE MANUFACTURER: HENAN АТЕВЕОКЕ CHEMICALS CO., LTD.\n"
    "THE BUYER: SOYUZOPTHIM LTD.\n"
    "PACKING :25KGS/BAG POLY ALUMINIUM CHLORIDE 22088 22000 30\n"
    "880BAGS INDUSTRIAL GRADE\n"
    "\n"
    "HENAN AIERFUKE CHEMICALS CO., LTD.\n"
    "PACKING LIST\n"
    "INVOICE NO.: 2025CI065-05 ADDENDUM NO.: ADD 05\n"
    "DATE:JUN. 01, 2025\n"
    "S/C NO.: AIERFUKE-SOH\n"
    "THE MANUFACTURER: HENAN AIERFUKE CHEMICALS CO., LTD.\n"
    "THE BUYER: SOYUZOPTHIM LTD.\n"
    "PACKING :25KGS/BAG\n"
    "POLY ALUMINIUM CHLORIDE\n"
    "22088\n"
    "22000\n"
    "30\n"
    "880BAGS\n"
    "INDUSTRIAL GRADE\n"
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

AIERFUKE_BL_TEXT_WITH_PDF_LAYER = (
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
    "\n"
    "THROUGH TRANSPORT BILL OF LADING\n"
    "Shipper\n"
    "BOOKING NUMBER\n"
    "BILL OF LADING NUMBER\n"
    "HENAN AIERFUKE CHEMICALS CO.,LTD.\n"
    "THE (WEST) INDUSTRIES CLUSTER AREA OF JIAOZUO CITY, HENAN PROVINCE,CHINA\n"
    "TEL:(+86 391)3126812\n"
    "LED417527A\n"
    "LED417527A\n"
    "Consignee\n"
    "SOYUZOPTHIM LTD.\n"
    "CLHU3822754\n"
    "20GP\n"
    "COC\n"
    "STF805711\n"
    "POLY ALUMINIUM CHLORIDE\n"
    "880\n"
    "BAGS\n"
    "22088\n"
    "30\n"
    "SHIPPED ON BOARD\n"
    "10.06.2025\n"
)

AIERFUKE_CO_TEXT = (
    "1. Exporter HENAN ATERFUKE CHEMICALS CO. , LTD. "
    "2. Consignee SOYUZOPTHIM LTD. "
    "10. Number and date of invoices "
    "N/M TWO THOUSAND SIX HUNDRED AND FORTY (2640) 66264KGS G.W. | 2025C1065 "
    "BAGS OF POLY ALUMINIUM CHLORIDE JUN. 01, 2025 "
    "produced in China"
)

PAINI_INVOICE_TEXT = (
    "COMMERCIAL INVOICE\n"
    "NO. DATE\n"
    "POROHOVSKAYA STR.., 47, LIT. A, ROOM 5H, OF. 306 | PN2025051504 | 2025.05.15\n"
    "CONTRACT NO.SPNM-SOH dated15.03.2024 Add07 TERMS OF PAYMENT:\n"
    "100% TT ADVANCE\n"
    "INCOTERMS : FOB QINGDAO\n"
    "21,760.000KG\n"
    "Tallow Amine Distilled 136DRUMS CNY 14.80/KG CNY 322,048.00\n"
    "PNA-TAD 160KG/DRUM\n"
)

PAINI_ADDENDUM_TEXT = (
    "ADDENDUM № 07 dated 14.04.2025 to the Contract № SPNM-SOH dated ПРИЛОЖЕНИЕ № 07 от 14.04.2025 к Контракту No SPNM-SOH or 15.03.2024\n"
    "15.03.2024\n"
    "ADDENDUM № 07 dated 14.04.2025 ПРИЛОЖЕНИЕ № 07 от 14.04.2025\n"
    "to the Contract № SPNM-SOH dated 15.03.2024 к Контракту № SPNM-SOH от 15.03.2024\n"
    "Shandong Раш! New Material Со., Ltd, hereinafter Shandong Раш! New Material Co., Ltd, именуемый в\n"
    "referred to as the SELLER, as one party and дальнейшем ПРОДАВЕЦ, с одной стороны и OOO\n"
    "Soyuzopthim Ltd., hereinafter referred to as the «Союзоптхим», именуемый B дальнейшем\n"
    "BUYER, as another party, have agreed on the following: ПОКУПАТЕЛЬ, с другой стороны, договорились о\n"
    "нижеследующем:\n"
    "The SELLER sells and the BUYER buys on FOB, Qingdao, CHINA terms (Incoterms 2020)\n"
    "Payment for the Goods should be done Бу the BUYER Оплата за товар должна быть произведена\n"
    "on the following conditions: ПОКУПАТЕЛЕМ на следующих условиях:\n"
    "Prepayment 100% Предоплата 100%\n"
)

PAINI_PACKING_TEXT = (
    "PACKING LIST\n"
    "INVOICE NO :PN2025051504\n"
    "INVOICE DATE:MAY.15.2025\n"
    "CONTRACT NO.SPNM-SOH dated15.03.2024\n"
    "INCOTERMS : FOB QINGDAO CONTAINER NO: THKU1003241\n"
    "ANTITY\n"
    "DESCRIPTION Qu\n"
    "AND PACKAGE\n"
    "Tallow Amine 436DRUMS\n"
    "Distilled 160KG/DRUM\n"
    "PNA-TAD 34PALLETS\n"
    "DESCRIPTION\n"
    "QUANTITY\n"
    "AND PACKAGE\n"
    "G.W.\n"
    "N.W.\n"
    "MEAS.\n"
    "Tallow Amine\n"
    "Distilled\n"
    "PNA-TAD\n"
    "136DRUMS\n"
    "160KG/DRUM\n"
    "34PALLETS\n"
    "25,126.000\n"
    "KGS\n"
    "21,760.000\n"
    "KGS\n"
    "50.000\n"
    "CBM\n"
)

PAINI_COA_TEXT = (
    "CERTIFICATE OF ANALYSIS\n"
    "Production: Tallow Amine Distilled\n"
    "BatchNo: 20250312002-006\n"
    "AnalysisDate: 2025-03-12\n"
    "Quantity: 160kg*78\n"
)

PAINI_BL_TEXT = (
    "ORIGINAL BL\n"
    "GLOTAOAL006 TAOLED2507W0097D\n"
    "Shipper\n"
    "SHANDONG PAINI NEW MATERIAL CO.,LTD\n"
    "Consignee\n"
    "SOYUZOPTHIM LTD.\n"
    "Description of packages and goods as stated by shipper. Said to contain.\n"
    "ContainerNumber ContainerType Seal Number Cargo Description No. of Packag Type of Packages Gross Weight, Tare Weight, KGS Volume, m3\n"
    "TOTAL (Itogo) _ [1*4ohc 25126.000 3700.000\n"
    "TOTAL NUMBER OF CARGO PLACES RECIVED BY THE CARRIER Shipped on board 2025-05-20\n"
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


def test_extract_denkim_coa_lot_and_production_dates() -> None:
    fields, _ = extract_fields("coa", DENKIM_COA_TEXT)

    assert fields.batch_no.value == "1752/2018"
    assert fields.manufacture_date.value.isoformat() == "2018-12-29"
    assert fields.expiry_date.value.isoformat() == "2020-12-29"


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


def test_extract_tianrun_bill_of_lading_gross_weight_ignores_legal_text_numbers() -> None:
    fields, _ = extract_fields("mbl", TIANRUN_BL_TEXT_WITH_LEGAL_NOISE)

    assert fields.container_no.value == "UACU3704865"
    assert fields.packages_quantity.value == 720
    assert fields.gross_weight_kg.value == 18144.0
    assert "18144.000KGS" in fields.gross_weight_kg.text_snippet
    assert fields.bl_date.value.isoformat() == "2025-10-07"


def test_extract_denkim_invoice_commercial_layout() -> None:
    fields, line_items = extract_fields("invoice", DENKIM_INVOICE_TEXT)

    assert fields.shipper_name.value == "DENKIM DENIZLI KIMYA SAN.VE TIC.A.S"
    assert fields.manufacturer_name.value == "DENKIM DENIZLI KIMYA SAN.VE TIC.A.S"
    assert fields.invoice_no.value == "DDI2019000000007"
    assert fields.invoice_date.value.isoformat() == "2019-01-03"
    assert fields.contract_no.value == "DNKM-SOH 2018"
    assert "90 DAYS AFTER THE B/L" in fields.payment_terms.value
    assert fields.incoterms.value == "CIF"
    assert fields.currency.value == "USD"
    assert fields.total_amount.value == 22140.0
    assert len(line_items) == 1
    assert line_items[0].product_name_normalized.value == "polyanionic cellulose lv"
    assert line_items[0].quantity.value == 18.0
    assert line_items[0].unit_price.value == 1230.0
    assert line_items[0].line_total.value == 22140.0


def test_extract_denkim_packing_list_thousands_and_container_layout() -> None:
    fields, line_items = extract_fields("packing_list", DENKIM_PACKING_TEXT)

    assert fields.shipper_name.value == "DENKIM DENIZLI KIMYA SAN.VE TIC.A.S"
    assert fields.manufacturer_name.value == "DENKIM DENIZLI KIMYA SAN.VE TIC.A.S"
    assert fields.invoice_no.value == "DDI2019000000007"
    assert fields.package_type.value == "BAG"
    assert fields.packages_quantity.value == 720
    assert fields.items_quantity.value == 720
    assert fields.gross_weight_kg.value == 18600.0
    assert fields.net_weight_kg.value == 18000.0
    assert fields.package_weight_kg.value == 600.0
    assert fields.container_no.value == "PONU0077754"
    assert fields.pallet_quantity.value == 20
    assert fields.pallet_weight_kg.value == 30.0
    assert fields.empty_package_weight_kg is None
    assert len(line_items) == 1
    assert line_items[0].product_name_normalized.value == "polyanionic cellulose lv"


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


def test_extract_aierfuke_invoice_prefers_clean_payment_terms_from_pdf_text_layer() -> None:
    composite_text = (
        "COMMERCIAL INVOICE\n"
        "PAYMENT: 100% T/T IN ADVANCE sf Up wea\n"
        "TIME OF SHIPMENT: ASAP\n"
        "\n"
        "HENAN AIERFUKE CHEMICALS CO., LTD.\n"
        "COMMERCIAL INVOICE\n"
        "PAYMENT: 100% T/T IN ADVANCE\n"
        "TIME OF SHIPMENT: ASAP\n"
    )
    fields, _ = extract_fields("invoice", composite_text)

    assert fields.payment_terms.value == "100% T/T IN ADVANCE"


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


def test_extract_aierfuke_packing_list_prefers_clean_pdf_text_layer_when_present() -> None:
    fields, _ = extract_fields("packing_list", AIERFUKE_PACKING_TEXT_WITH_PDF_LAYER)

    assert fields.shipper_name.value == "HENAN AIERFUKE CHEMICALS CO., LTD"
    assert fields.manufacturer_name.value == "HENAN AIERFUKE CHEMICALS CO., LTD"
    assert fields.contract_no.value == "AIERFUKE-SOH"


def test_extract_aierfuke_bill_of_lading_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("mbl", AIERFUKE_BL_TEXT)

    assert fields.shipper_name.value == "HENAN ATEBPOKE CHEMICALS CO.,LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.bl_no.value == "LED417527A"
    assert fields.container_no.value == "CLHU3822754"
    assert fields.packages_quantity.value == 880
    assert fields.bl_date.value.isoformat() == "2025-06-10"


def test_extract_aierfuke_bill_of_lading_prefers_clean_pdf_text_layer_when_present() -> None:
    fields, _ = extract_fields("mbl", AIERFUKE_BL_TEXT_WITH_PDF_LAYER)

    assert fields.shipper_name.value == "HENAN AIERFUKE CHEMICALS CO.,LTD"
    assert fields.bl_no.value == "LED417527A"
    assert fields.container_no.value == "CLHU3822754"


def test_extract_aierfuke_certificate_of_origin_fields_from_ocr_text() -> None:
    fields, _ = extract_fields("certificate_of_origin", AIERFUKE_CO_TEXT)

    assert fields.shipper_name.value == "HENAN ATERFUKE CHEMICALS CO. , LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.invoice_no.value == "2025C1065"
    assert fields.invoice_date.value.isoformat() == "2025-06-01"
    assert fields.gross_weight_kg.value == 66264.0


def test_extract_paini_invoice_fields_from_pna_tad_text() -> None:
    fields, line_items = extract_fields("invoice", PAINI_INVOICE_TEXT)

    assert fields.invoice_no.value == "PN2025051504"
    assert fields.invoice_date.value.isoformat() == "2025-05-15"
    assert fields.contract_no.value == "SPNM-SOH"
    assert fields.addendum_no.value == "ADD 07"
    assert fields.payment_terms.value == "100% TT ADVANCE"
    assert fields.total_amount.value == 322048.0
    assert len(line_items) == 1
    assert line_items[0].product_name_raw.value == "Tallow Amine Distilled PNA-TAD"
    assert line_items[0].quantity.value == 21760.0
    assert line_items[0].unit_price.value == 14.8
    assert line_items[0].line_total.value == 322048.0


def test_extract_paini_addendum_fields_from_bilingual_ocr_text() -> None:
    fields, _ = extract_fields("addendum", PAINI_ADDENDUM_TEXT)

    assert fields.addendum_no.value == "ADD 07"
    assert fields.addendum_date.value.isoformat() == "2025-04-14"
    assert fields.contract_no.value == "SPNM-SOH"
    assert fields.contract_date.value.isoformat() == "2024-03-15"
    assert fields.seller_name.value == "Shandong Paini New Material Co., Ltd"
    assert fields.buyer_name.value == "Soyuzopthim Ltd"
    assert fields.incoterms.value == "FOB"
    assert fields.payment_terms.value == "Prepayment 100%"


def test_extract_paini_packing_list_fields_from_drums_layout() -> None:
    fields, line_items = extract_fields("packing_list", PAINI_PACKING_TEXT)

    assert fields.invoice_no.value == "PN2025051504"
    assert fields.contract_no.value == "SPNM-SOH"
    assert fields.container_no.value == "THKU1003241"
    assert fields.package_type.value == "DRUM"
    assert fields.packages_quantity.value == 136
    assert fields.items_quantity.value == 136
    assert fields.has_pallets.value is True
    assert fields.pallet_quantity.value == 34
    assert fields.gross_weight_kg.value == 25126.0
    assert fields.net_weight_kg.value == 21760.0
    assert fields.package_weight_kg.value == 3366.0
    assert fields.empty_package_weight_kg.value == 21.0
    assert fields.pallet_weight_kg.value == 15.0
    assert len(line_items) == 1
    assert line_items[0].product_name_raw.value == "Tallow Amine Distilled PNA-TAD"
    assert line_items[0].quantity.value == 21760.0


def test_extract_paini_coa_batch_and_analysis_date() -> None:
    fields, _ = extract_fields("coa", PAINI_COA_TEXT)

    assert fields.batch_no.value == "20250312002-006"
    assert fields.manufacture_date.value.isoformat() == "2025-03-12"


def test_extract_paini_bill_of_lading_gross_weight_from_total_row() -> None:
    fields, _ = extract_fields("mbl", PAINI_BL_TEXT)

    assert fields.bl_no.value == "TAOLED2507W0097D"
    assert fields.shipper_name.value == "SHANDONG PAINI NEW MATERIAL CO.,LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.gross_weight_kg.value == 25126.0
    assert fields.bl_date.value.isoformat() == "2025-05-20"


def test_extract_invoice_company_fields_from_ocr_lines_only() -> None:
    ocr_result = OcrDocumentResultRecord(
        document_id=uuid4(),
        source_file_name="invoice.pdf",
        source_file_path="uploads/test/invoice.pdf",
        provider="tesseract",
        languages="eng",
        status="completed",
        pages=[
            OcrPageResultRecord(
                page_no=1,
                text="",
                lines=[
                    OcrTextLineRecord(page_no=1, text="COMMERCIAL INVOICE"),
                    OcrTextLineRecord(page_no=1, text="THE MANUFACTURER:"),
                    OcrTextLineRecord(page_no=1, text="HENAN AIERFUKE CHEMICALS CO., LTD."),
                    OcrTextLineRecord(page_no=1, text="THE BUYER: SOYUZOPTHIM LTD."),
                ],
            )
        ],
        raw_text="",
        created_at=datetime.now(UTC),
    )

    fields, _ = extract_fields("invoice", None, ocr_result=ocr_result)

    assert fields.manufacturer_name.value == "HENAN AIERFUKE CHEMICALS CO., LTD"
    assert fields.shipper_name.value == "HENAN AIERFUKE CHEMICALS CO., LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"


def test_extract_hugestone_addendum_buyer_and_seller() -> None:
    fields, _ = extract_fields("addendum", HUGESTONE_ADDENDUM_TEXT)

    assert fields.seller_name.value == "Hugestone Enterprise Co., Ltd"
    assert fields.buyer_name.value == "Soyuzopthim Ltd"


def test_extract_hugestone_invoice_line_item_and_total() -> None:
    fields, line_items = extract_fields("invoice", HUGESTONE_INVOICE_TEXT)

    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.invoice_no.value == "225CW11165"
    assert fields.invoice_date.value.isoformat() == "2025-03-28"
    assert fields.incoterms.value == "FOB"
    assert fields.total_amount.value == 338000.0
    assert len(line_items) == 1
    assert line_items[0].product_name_raw.value == "XANTHAN GUM"
    assert line_items[0].quantity.value == 20000.0
    assert line_items[0].unit_price.value == 16.9
    assert line_items[0].line_total.value == 338000.0


def test_extract_hugestone_packing_weights_and_line_item() -> None:
    fields, line_items = extract_fields("packing_list", HUGESTONE_PACKING_TEXT)

    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.invoice_no.value == "225CW11165"
    assert fields.packages_quantity.value == 800
    assert fields.gross_weight_kg.value == 20160.0
    assert fields.net_weight_kg.value == 20000.0
    assert len(line_items) == 1
    assert line_items[0].product_name_raw.value == "XANTHAN GUM"
    assert line_items[0].quantity.value == 20000.0


def test_extract_hugestone_coa_dates_with_noisy_colons() -> None:
    fields, _ = extract_fields("coa", HUGESTONE_COA_TEXT)

    assert fields.batch_no.value == "520250226032"
    assert fields.manufacture_date.value.isoformat() == "2025-02-26"
    assert fields.expiry_date.value.isoformat() == "2027-02-25"


def test_extract_hugestone_bill_of_lading_buyer_and_cargo() -> None:
    fields, _ = extract_fields("mbl", HUGESTONE_BL_TEXT)

    assert fields.shipper_name.value == "HUGESTONE ENTERPRISE CO., LTD"
    assert fields.buyer_name.value == "SOYUZOPTHIM LTD"
    assert fields.cargo_description.value == "XANTHAN GUM"
    assert fields.gross_weight_kg.value == 20160.0
    assert fields.bl_date.value.isoformat() == "2025-03-30"
