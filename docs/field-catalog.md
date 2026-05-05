# Field Catalog For Extraction Layer

## 1. Назначение

Этот каталог определяет, какие поля extraction layer должен искать в каждом типе документа для `document validation v1`.

Каталог используется как источник для:

- настройки OCR/extraction;
- маппинга в каноническую модель;
- определения обязательности полей;
- связи между extraction и rule engine.

## 2. Колонки каталога

- `field_name` — каноническое имя поля
- `label_variants` — типовые подписи, по которым поле можно искать
- `data_type` — ожидаемый тип
- `required_v1` — обязательность для первой версии
- `used_in_rules` — коды правил, где поле используется
- `example` — пример значения
- `notes` — дополнительные указания для extraction

## 3. Общие соглашения

- `required_v1 = yes` означает, что поле должно извлекаться в `MVP Core`.
- `required_v1 = conditional` означает, что поле нужно только при определенном сценарии.
- `required_v1 = phase2` означает, что поле пока не блокирует запуск `MVP Core`, но должно быть предусмотрено в модели.
- Если у поля несколько возможных источников на странице, extraction должен сохранять кандидатов и confidence.
- Если документ табличный, extraction должен пытаться извлечь и header-level поля, и `line_items`.

## 4. Global Canonical Fields

| field_name | data_type | normalization | notes |
| --- | --- | --- | --- |
| `shipper_name` | string | company-name normalization | Сравнивается после удаления шума и унификации юр. форм |
| `buyer_name` | string | company-name normalization | Может совпадать с `consignee_name`, но не всегда |
| `seller_name` | string | company-name normalization | Полезно для будущих правил |
| `consignee_name` | string | company-name normalization | Особенно важно для BL |
| `manufacturer_name` | string | company-name normalization | Источник для COA |
| `contract_no` | string | trim, uppercase-safe | Не удалять `-` и `/` |
| `contract_date` | date | ISO date | Поддерживать разные форматы |
| `addendum_no` | string | trim | Может отсутствовать в некоторых шаблонах |
| `addendum_date` | date | ISO date | Используется в R005 |
| `invoice_no` | string | trim, uppercase-safe | Критично для R007 |
| `invoice_date` | date | ISO date | Полезно для будущих правил |
| `payment_terms` | string | lowercase normalized | Искать `prepayment`, `advance`, `100% prepaid` |
| `incoterms` | enum string | uppercase | Допустимые значения по spec |
| `currency` | enum string | uppercase | `USD`, `EUR`, `CNY`, etc. |
| `container_no` | string | uppercase, remove spaces | Не терять буквы и цифры |
| `gross_weight_kg` | decimal | kg | Если единицы не kg, конвертировать |
| `net_weight_kg` | decimal | kg | Если единицы не kg, конвертировать |
| `package_weight_kg` | decimal | kg | Используется в packing formulas |
| `empty_package_weight_kg` | decimal | kg | Phase 2 |
| `pallet_weight_kg` | decimal | kg | Phase 2 |
| `pallet_quantity` | integer | integer | Phase 2 |
| `items_quantity` | integer | integer | Для bag/item formulas |
| `packages_quantity` | integer | integer | Для packing/BL checks |
| `package_type` | string | lowercase normalized | `bags`, `barrels`, `cartons`, etc. |
| `bl_no` | string | trim, uppercase-safe | Для MBL/HBL |
| `bl_date` | date | ISO date | Используется в COA rule |
| `batch_no` | string | trim, uppercase-safe | Критично для COA |
| `manufacture_date` | date | ISO date | Критично для COA |
| `expiry_date` | date | ISO date | Критично для COA |
| `cargo_description` | string | trimmed text | Проверяется на `HS code` |
| `total_amount` | decimal | decimal | Invoice arithmetic |
| `document_presence` | boolean | n/a | Для pseudo-documents вроде payment confirmation |

## 5. Document-Specific Catalog

## 5.1 Contract

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `shipper_name` | `seller`, `exporter`, `shipper`, `supplier` | string | yes | R001 | `Qingdao Chemical Co., Ltd.` | Часто расположен в блоке стороны договора |
| `buyer_name` | `buyer`, `purchaser`, `importer` | string | yes | R002 | `OOO Customs Trade` | Не путать с consignee |
| `contract_no` | `contract no`, `contract number`, `agreement no` | string | yes | R003 | `CT-2026-041` | Часто в шапке |
| `contract_date` | `date`, `contract date`, `agreement date` | date | yes | R005 | `2026-04-10` | Если несколько дат, брать дату документа |
| `incoterms` | `incoterms`, `delivery terms`, `terms of delivery` | enum string | yes | R006 | `FOB` | Искать рядом с портом/местом |
| `currency` | `currency` | enum string | no | future | `USD` | Для будущих расчетов |

## 5.2 Addendum

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `shipper_name` | `seller`, `supplier`, `shipper` | string | yes | R001 | `Qingdao Chemical Co., Ltd.` | |
| `buyer_name` | `buyer`, `purchaser` | string | yes | R002 | `OOO Customs Trade` | |
| `contract_no` | `contract no`, `to contract`, `agreement no` | string | yes | R003 | `CT-2026-041` | Может быть ссылкой на основной contract |
| `addendum_no` | `addendum no`, `appendix no`, `supplement no` | string | no | future | `ADD-03` | |
| `addendum_date` | `date`, `addendum date` | date | yes | R005 | `2026-04-20` | |
| `incoterms` | `incoterms`, `delivery terms` | enum string | yes | R006 | `FOB` | |
| `payment_terms` | `payment terms`, `terms of payment`, `payment condition` | string | yes | R018 | `100% prepayment` | Нужно искать `prepayment` |
| `line_items[].product_name_raw` | `product name`, `goods`, `commodity`, `description` | string | phase2 | R004 | `PVC Resin SG-5` | Табличное извлечение |
| `line_items[].product_name_normalized` | derived | string | phase2 | R004 | `pvc resin sg5` | Строится post-processing |
| `line_items[].quantity` | `qty`, `quantity` | decimal | phase2 | future | `1000` | |
| `line_items[].quantity_unit` | `unit`, `uom` | string | phase2 | future | `kg` | |

## 5.3 Commercial Invoice

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `shipper_name` | `seller`, `exporter`, `shipper`, `supplier` | string | yes | R001 | `Qingdao Chemical Co., Ltd.` | |
| `buyer_name` | `buyer`, `consignee`, `importer` | string | yes | R002 | `OOO Customs Trade` | В некоторых шаблонах buyer и consignee разделены |
| `contract_no` | `contract no`, `contract number` | string | yes | R003 | `CT-2026-041` | |
| `invoice_no` | `invoice no`, `invoice number`, `no.` | string | yes | R007 | `INV-24051` | |
| `invoice_date` | `invoice date`, `date` | date | no | future | `2026-04-21` | |
| `incoterms` | `incoterms`, `delivery terms` | enum string | yes | R006 | `FOB` | |
| `currency` | `currency` | enum string | yes | future | `USD` | |
| `total_amount` | `total amount`, `invoice total`, `amount` | decimal | yes | R009 | `12500.00` | Предпочитать grand total |
| `line_items[].product_name_raw` | `description`, `goods description`, `commodity` | string | yes | R004 | `PVC Resin SG-5` | Core для extraction, Phase 2 для rule |
| `line_items[].product_name_normalized` | derived | string | yes | R004 | `pvc resin sg5` | |
| `line_items[].quantity` | `qty`, `quantity` | decimal | yes | R008 | `1000` | |
| `line_items[].quantity_unit` | `unit`, `uom` | string | yes | R008 | `kg` | |
| `line_items[].unit_price` | `unit price`, `price`, `rate` | decimal | yes | R008 | `1.25` | |
| `line_items[].line_total` | `amount`, `total`, `line total` | decimal | yes | R008, R009 | `1250.00` | |

## 5.4 Packing List

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `shipper_name` | `seller`, `shipper`, `supplier` | string | yes | R001 | `Qingdao Chemical Co., Ltd.` | |
| `buyer_name` | `buyer`, `consignee`, `importer` | string | yes | R002 | `OOO Customs Trade` | |
| `invoice_no` | `invoice no`, `ref invoice`, `invoice reference` | string | yes | R007 | `INV-24051` | |
| `incoterms` | `incoterms`, `delivery terms` | enum string | conditional | R006 | `FOB` | Если поле реально есть в шаблоне |
| `container_no` | `container no`, `container number`, `cntr no` | string | yes | R017, R026 | `MSCU1234567` | Может встречаться в шапке или в таблице |
| `package_type` | `package type`, `packing`, `kind of packages` | string | yes | R010 | `bags` | |
| `packages_quantity` | `packages`, `number of packages`, `qty of packages` | integer | yes | R011, R025 | `1000` | |
| `gross_weight_kg` | `gross weight`, `g.w.`, `gw` | decimal | yes | R012, R024 | `21540` | Приводить к kg |
| `net_weight_kg` | `net weight`, `n.w.`, `nw` | decimal | yes | R012 | `21000` | |
| `package_weight_kg` | `package weight`, `packing weight` | decimal | yes | R012, R013 | `540` | Иногда вычисляется, а не читается напрямую |
| `empty_package_weight_kg` | `empty bag weight`, `bag weight`, `empty barrel weight` | decimal | phase2 | R014, R016 | `0.025` | |
| `items_quantity` | `bags qty`, `items qty`, `pcs`, `units` | integer | phase2 | R016 | `1000` | Нужно отличать от `packages_quantity` |
| `pallet_weight_kg` | `pallet weight` | decimal | phase2 | R015, R016 | `20` | |
| `pallet_quantity` | `pallet qty`, `number of pallets` | integer | phase2 | R015, R016 | `10` | |
| `has_pallets` | derived | boolean | phase2 | R015 | `true` | Может выводиться из pallet fields или текста |
| `line_items[].product_name_raw` | `description`, `commodity`, `goods` | string | yes | R004 | `PVC Resin SG-5` | |
| `line_items[].product_name_normalized` | derived | string | yes | R004 | `pvc resin sg5` | |
| `line_items[].quantity` | `qty`, `quantity` | decimal | conditional | future | `1000` | Если список построчный |

## 5.5 Certificate of Analysis (COA)

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `manufacturer_name` | `manufacturer`, `made by`, `producer` | string | yes | R001 | `Qingdao Chemical Co., Ltd.` | В rules v1 используется как shipper-equivalent |
| `batch_no` | `batch no`, `lot no`, `batch number`, `lot number` | string | yes | R019 | `BATCH-001` | |
| `manufacture_date` | `manufacture date`, `mfg date`, `date of production` | date | yes | R020, R022 | `2026-03-15` | |
| `expiry_date` | `expiry date`, `exp date`, `best before`, `valid until` | date | yes | R021, R023 | `2028-03-14` | |
| `product_name_raw` | `product name`, `material`, `commodity` | string | phase2 | R004 | `PVC Resin SG-5` | |
| `product_name_normalized` | derived | string | phase2 | R004 | `pvc resin sg5` | |
| `line_items[].product_name_raw` | table row text | string | phase2 | R004 | `PVC Resin SG-5` | Если COA многопозиционный |

## 5.6 Master Bill of Lading (MBL)

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `bl_no` | `bill of lading no`, `b/l no`, `bl no` | string | yes | future | `COSU63542109` | |
| `bl_date` | `date of issue`, `on board date`, `issue date` | date | yes | R022 | `2026-04-25` | |
| `shipper_name` | `shipper`, `consignor` | string | yes | R001 | `Qingdao Chemical Co., Ltd.` | |
| `buyer_name` | `consignee`, `buyer`, `notify party` | string | yes | R002 | `OOO Customs Trade` | Требует уточнения по mapping |
| `consignee_name` | `consignee` | string | no | future | `OOO Customs Trade` | Хранить отдельно даже если buyer mapping спорный |
| `container_no` | `container no`, `container number`, `marks & nos` | string | yes | R026 | `MSCU1234567` | Может быть несколько контейнеров |
| `gross_weight_kg` | `gross weight`, `gross mass` | decimal | yes | R024 | `21540` | |
| `packages_quantity` | `no. of packages`, `packages` | integer | yes | R025 | `1000` | |
| `package_type` | `kind of packages`, `packages` | string | no | future | `bags` | |
| `cargo_description` | `description of goods`, `cargo description` | string | yes | R027 | `PVC RESIN SG-5` | Проверять отсутствие `HS code`; не использовать для R004 product-name matching |

## 5.7 House Bill of Lading (HBL)

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `bl_no` | `house bl no`, `bill of lading no`, `b/l no` | string | yes | future | `HBL-77811` | |
| `bl_date` | `date of issue`, `issue date` | date | yes | R022 | `2026-04-25` | |
| `shipper_name` | `shipper`, `consignor` | string | yes | R001 | `Qingdao Chemical Co., Ltd.` | |
| `buyer_name` | `consignee`, `buyer`, `notify party` | string | yes | R002 | `OOO Customs Trade` | Те же ограничения, что и у MBL |
| `consignee_name` | `consignee` | string | no | future | `OOO Customs Trade` | |
| `container_no` | `container no`, `container number` | string | yes | R026 | `MSCU1234567` | |
| `gross_weight_kg` | `gross weight`, `gross mass` | decimal | yes | R024 | `21540` | |
| `packages_quantity` | `no. of packages`, `packages` | integer | yes | R025 | `1000` | |
| `cargo_description` | `description of goods`, `cargo description` | string | yes | R027 | `PVC RESIN SG-5` | Не использовать для R004 product-name matching |

## 5.8 Transport Invoice

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `shipper_name` | `carrier`, `supplier`, `shipper` | string | no | future | `Shanghai Freight Service Co.` | |
| `buyer_name` | `customer`, `consignee`, `buyer` | string | no | future | `OOO Customs Trade` | |
| `incoterms` | `incoterms`, `terms` | enum string | conditional | R006 | `FOB` | Пока только если поле есть |
| `invoice_no` | `invoice no`, `reference no` | string | no | future | `TI-77881` | |
| `invoice_date` | `date` | date | no | future | `2026-04-24` | |
| `total_amount` | `amount`, `total freight` | decimal | no | future | `1500.00` | |

## 5.9 Certificate of Origin (CO)

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `shipper_name` | `exporter`, `consignor`, `producer` | string | no | future | `Qingdao Chemical Co., Ltd.` | Пока отдельные rules не заданы |
| `buyer_name` | `consignee`, `importer` | string | no | future | `OOO Customs Trade` | |
| `product_name_raw` | `marks and numbers`, `description of goods` | string | no | future | `PVC Resin SG-5` | |
| `origin_country` | `country of origin`, `origin criterion` | string | no | future | `China` | Заранее добавить в модель полезно |
| `document_no` | `certificate no`, `no.` | string | no | future | `CO-2026-0045` | |
| `issue_date` | `date`, `date of issue` | date | no | future | `2026-04-22` | |

## 5.10 Payment Confirmation

| field_name | label_variants | data_type | required_v1 | used_in_rules | example | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `document_presence` | n/a | boolean | conditional | R018 | `true` | Определяется самим фактом наличия файла |
| `payment_reference` | `mt103`, `reference`, `transaction reference` | string | no | future | `MT103-99081` | |
| `payment_date` | `value date`, `date` | date | no | future | `2026-04-18` | |
| `payment_amount` | `amount`, `remitted amount` | decimal | no | future | `12500.00` | |
| `currency` | `currency` | enum string | no | future | `USD` | |
| `payer_name` | `ordering customer`, `payer` | string | no | future | `OOO Customs Trade` | |
| `beneficiary_name` | `beneficiary`, `receiver` | string | no | future | `Qingdao Chemical Co., Ltd.` | |

## 6. Line Item Schema

Следующие поля должны поддерживаться единообразно для `invoice`, `packing_list`, `addendum` и при необходимости `coa`.

| field_name | data_type | required_v1 | notes |
| --- | --- | --- | --- |
| `line_no` | integer | yes | Если номера строки нет, генерировать по порядку |
| `product_name_raw` | string | yes | Для v1 extraction обязателен в invoice и packing list |
| `product_name_normalized` | string | yes | Генерируется post-processing |
| `quantity` | decimal | yes | Особенно важно для invoice |
| `quantity_unit` | string | yes | Нужен для корректного понимания веса и количества |
| `unit_price` | decimal | yes for invoice | |
| `line_total` | decimal | yes for invoice | |
| `batch_no` | string | no | Важен для будущих cross-check rules |

## 7. Extraction Priorities

## 7.1 MVP Core Fields

Эти поля должны иметь наивысший приоритет в extraction pipeline:

- `contract.contract_no`
- `contract.contract_date`
- `contract.shipper_name`
- `contract.buyer_name`
- `contract.incoterms`
- `addendum.contract_no`
- `addendum.addendum_date`
- `addendum.payment_terms`
- `invoice.invoice_no`
- `invoice.total_amount`
- `invoice.line_items[].quantity`
- `invoice.line_items[].unit_price`
- `invoice.line_items[].line_total`
- `packing_list.invoice_no`
- `packing_list.container_no`
- `packing_list.package_type`
- `packing_list.packages_quantity`
- `packing_list.gross_weight_kg`
- `packing_list.net_weight_kg`
- `packing_list.package_weight_kg`
- `coa.batch_no`
- `coa.manufacture_date`
- `coa.expiry_date`
- `mbl/hbl.bl_date`
- `mbl/hbl.gross_weight_kg`
- `mbl/hbl.packages_quantity`
- `mbl/hbl.container_no`
- `mbl/hbl.cargo_description`

## 7.2 Phase 2 Fields

- `product_name_*` cross-document harmonization
- `empty_package_weight_kg`
- `items_quantity`
- `pallet_weight_kg`
- `pallet_quantity`
- `has_pallets`

## 8. Implementation Notes

- Для `buyer_name` и `shipper_name` желательно хранить не только выбранное значение, но и `role_source`, например `buyer`, `consignee`, `notify_party`.
- Для `container_no` желательно поддержать список значений, даже если v1 UI показывает только первое.
- Для `gross_weight_kg` и `net_weight_kg` хранить исходную строку и единицы измерения отдельно от нормализованного значения.
- Для invoice total extraction предпочтительнее `grand total`, а не промежуточный subtotal.
- Для packing list допускается derived extraction: если `package_weight_kg` не найден явно, он может быть вычислен позже, но должен быть помечен как `derived`.

## 9. Open Questions Tied To Extraction

1. Нужно ли маппить `consignee` в `buyer_name` для всех BL, или хранить отдельно и сравнивать позже?
2. Если в packing list несколько контейнеров, сравнение делать по первому, по полному набору или по каждой строке?
3. Если `package_weight_kg` не указан явно, считать ли это ошибкой extraction или допустимым derived field?
4. Для COA с несколькими batch numbers сравнение должно работать по набору значений или по одному batch?
