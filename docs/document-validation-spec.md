# Спецификация модуля проверки документов

## 1. Назначение

Модуль проверки документов предназначен для автоматического анализа пакета документов по одной поставке и выявления:

- отсутствующих обязательных данных;
- противоречий между документами;
- арифметических ошибок;
- нарушений бизнес-правил оформления.

Результат работы модуля должен быть объяснимым: каждое замечание содержит правило, severity, затронутые документы, затронутые поля и краткое описание проблемы.

## 2. Границы первой версии

### Входит в v1

- проверка одного document pack за один запуск;
- чтение всего документа целиком с последующей нормализацией полей;
- сравнение полей между документами;
- проверки наличия, равенства, дат и формул;
- выдача `error` и `warning`.

### Не входит в v1

- автокоррекция данных;
- юридическая интерпретация спорных кейсов;
- универсальная поддержка любых шаблонов без настройки;
- детальная тарификация себестоимости.

## 3. Состав стандартного пакета документов

Исходный набор из `Rule engine v1.txt`:

1. Contract
2. Addendum to the contract
3. Commercial Invoice
4. Packing List
5. Certificate of Analysis (COA)
6. Master Bill of Lading (MBL)
7. House Bill of Lading (HBL), если применимо
8. Transport Invoice (before the border)
9. Certificate of Origin (CO)
10. Payment confirmation (`mt103` или аналог), если применимо

## 4. Каноническая модель данных

После OCR и extraction каждый документ должен быть приведен к единому JSON-представлению.

### 4.1 Общая структура документа

```json
{
  "document_id": "uuid",
  "document_type": "invoice",
  "source_file_name": "invoice_123.pdf",
  "pages": 2,
  "language": "en",
  "raw_text_ref": "storage://...",
  "fields": {},
  "line_items": [],
  "evidence": []
}
```

### 4.2 Общие поля верхнего уровня

Поля, которые могут встречаться в нескольких документах:

- `shipper_name`
- `buyer_name`
- `seller_name`
- `consignee_name`
- `manufacturer_name`
- `contract_no`
- `contract_date`
- `addendum_no`
- `addendum_date`
- `invoice_no`
- `invoice_date`
- `payment_terms`
- `incoterms`
- `currency`
- `container_no`
- `gross_weight_kg`
- `net_weight_kg`
- `package_weight_kg`
- `packages_quantity`
- `package_type`
- `bl_no`
- `bl_date`
- `batch_no`
- `manufacture_date`
- `expiry_date`
- `cargo_description`
- `total_amount`

### 4.3 Табличные позиции

Для документов с товарными позициями требуется нормализация `line_items`.

```json
{
  "line_no": 1,
  "product_name_raw": "PVC Resin SG-5",
  "product_name_normalized": "pvc resin sg5",
  "quantity": 1000,
  "quantity_unit": "kg",
  "unit_price": 1.25,
  "line_total": 1250.0,
  "batch_no": "BATCH-001"
}
```

### 4.4 Evidence model

Для каждого извлеченного поля нужно хранить подтверждение:

- `page_no`
- `text_snippet`
- `confidence`
- `bounding_box`, если OCR его возвращает

Это позволит показывать пользователю, где именно система нашла спорное значение.

## 5. Нормализация данных

Перед применением правил все извлеченные значения проходят нормализацию.

### 5.1 Нормализация строк

- привести к одному регистру;
- обрезать пробелы по краям;
- схлопнуть двойные пробелы;
- убрать служебную пунктуацию, если она не влияет на смысл;
- унифицировать `Ltd.`, `Ltd`, `LLC`, `Co., Ltd.` по таблице замен;
- сравнивать как `raw`, так и `normalized` значение.

### 5.2 Нормализация чисел и весов

- приводить разделители `,` и `.` к единому формату;
- хранить числовое значение отдельно от исходной строки;
- веса хранить в килограммах;
- использовать допустимое отклонение `tolerance`, например `0.01`, для арифметических проверок.

### 5.3 Нормализация дат

- преобразовать даты в ISO `YYYY-MM-DD`;
- поддерживать типовые форматы `DD.MM.YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD`, `Month DD, YYYY`;
- если дата не распознана однозначно, поле помечается как `unresolved`.

### 5.4 Нормализация товарных наименований

- хранить `product_name_raw`;
- хранить `product_name_normalized`;
- убирать лишние знаки и двойные пробелы;
- при необходимости применять словарь эквивалентных написаний.

## 6. Стратегия чтения документа

### Базовый режим v1

Система читает весь документ, а не заранее заданные области.

Порядок:

1. OCR всего документа.
2. Извлечение ключ-значение и таблиц.
3. Классификация документа.
4. Маппинг в канонические поля.
5. Проверка правил.

### Когда добавляются зоны

Явная разметка областей нужна только для проблемных полей:

- если одно поле встречается несколько раз;
- если OCR стабильно берет не тот блок;
- если значение лежит в сложной таблице;
- если разные шаблоны поставщика дают конфликтующие кандидаты.

## 7. Типы правил

В `v1` достаточно пяти типов правил:

1. `presence`
   Проверяет, что поле или документ присутствует.

2. `exact_match`
   Проверяет точное совпадение после нормализации.

3. `set_match`
   Проверяет совпадение набора значений, например product names.

4. `date_compare`
   Проверяет отношение дат: `>`, `<`, `>=`, `<=`.

5. `formula`
   Проверяет арифметику по формуле.

## 8. Каталог правил v1

Ниже формализован текущий набор правил из `Rule engine v1.txt`.

### R001. Shipper name consistency

- Severity: `warning`
- Type: `exact_match`
- Source fields:
  - `contract.shipper_name`
  - `addendum.shipper_name`
  - `invoice.shipper_name`
  - `packing_list.shipper_name`
  - `coa.manufacturer_name`
  - `mbl.shipper_name` или `hbl.shipper_name`
- Logic:
  Все найденные значения должны совпадать после нормализации.

### R002. Buyer name consistency

- Severity: `warning`
- Type: `exact_match`
- Source fields:
  - `contract.buyer_name`
  - `addendum.buyer_name`
  - `invoice.buyer_name`
  - `packing_list.buyer_name`
  - `mbl.buyer_name` или `hbl.buyer_name`
- Logic:
  Все найденные значения должны совпадать после нормализации.

### R003. Contract number consistency

- Severity: `warning`
- Type: `exact_match`
- Source fields:
  - `contract.contract_no`
  - `addendum.contract_no`
  - `invoice.contract_no`
- Logic:
  `addendum.contract_no == contract.contract_no`
  и
  `invoice.contract_no == contract.contract_no`

### R004. Product names consistency

- Severity: `warning`
- Type: `set_match`
- Source fields:
  - `addendum.line_items[].product_name_normalized`
  - `invoice.line_items[].product_name_normalized`
  - `packing_list.line_items[].product_name_normalized`
  - при наличии `coa.line_items[].product_name_normalized` или `coa.product_name_normalized`
- Logic:
  Наборы товарных наименований должны совпадать.
- Note:
  В addendum допустимо несколько позиций.
  BL `cargo_description` не участвует в этом сравнении, потому что в коносаменте описание груза может быть короче или более обобщенным, чем в invoice, packing list и addendum.

### R005. Addendum date later than contract date

- Severity: `error`
- Type: `date_compare`
- Source fields:
  - `contract.contract_date`
  - `addendum.addendum_date`
- Logic:
  `addendum.addendum_date > contract.contract_date`

### R006. Incoterms consistency

- Severity: `warning`
- Type: `exact_match`
- Source fields:
  - `contract.incoterms`
  - `addendum.incoterms`
  - `invoice.incoterms`
  - `packing_list.incoterms`, если поле есть
  - `transport_invoice.incoterms`, если поле есть
- Allowed values:
  `FOB`, `FOR`, `FCA`, `EXW`, `DAP`, `CPT`, `CIF`, `CFR`, `DDP`
- Logic:
  Все найденные значения должны совпадать и входить в allowed list.

### R007. Invoice number consistency

- Severity: `error`
- Type: `exact_match`
- Source fields:
  - `invoice.invoice_no`
  - `packing_list.invoice_no`
- Logic:
  `invoice.invoice_no == packing_list.invoice_no`

### R008. Invoice line arithmetic

- Severity: `error`
- Type: `formula`
- Source fields:
  - `invoice.line_items[].quantity`
  - `invoice.line_items[].unit_price`
  - `invoice.line_items[].line_total`
- Logic:
  Для каждой строки:
  `line_total == quantity * unit_price` с учетом `tolerance`.

### R009. Invoice total arithmetic

- Severity: `error`
- Type: `formula`
- Source fields:
  - `invoice.line_items[].line_total`
  - `invoice.total_amount`
- Logic:
  `invoice.total_amount == sum(invoice.line_items[].line_total)` с учетом `tolerance`.

### R010. Packing list must contain package type

- Severity: `error`
- Type: `presence`
- Source fields:
  - `packing_list.package_type`
- Logic:
  Поле обязательно.

### R011. Packing list must contain packages quantity

- Severity: `error`
- Type: `presence`
- Source fields:
  - `packing_list.packages_quantity`
- Logic:
  Поле обязательно.

### R012. Packing gross weight formula basic

- Severity: `error`
- Type: `formula`
- Source fields:
  - `packing_list.gross_weight_kg`
  - `packing_list.net_weight_kg`
  - `packing_list.package_weight_kg`
- Logic:
  `gross_weight_kg == net_weight_kg + package_weight_kg`

### R013. Packing package weight reverse formula

- Severity: `error`
- Type: `formula`
- Source fields:
  - `packing_list.gross_weight_kg`
  - `packing_list.net_weight_kg`
  - `packing_list.package_weight_kg`
- Logic:
  `package_weight_kg == gross_weight_kg - net_weight_kg`

### R014. Packing list must contain empty package weight

- Severity: `error`
- Type: `presence`
- Source fields:
  - `packing_list.empty_package_weight_kg`
- Logic:
  Поле обязательно.

### R015. Packing list pallet condition

- Severity: `warning`
- Type: `formula`
- Source fields:
  - `packing_list.has_pallets`
  - `packing_list.gross_weight_kg`
  - `packing_list.net_weight_kg`
  - `packing_list.pallet_weight_kg`
  - `packing_list.pallet_quantity`
- Logic:
  Если `has_pallets = true`, gross weight должен включать pallets.
- Note:
  Для точной автоматизации нужно подтверждение полей `has_pallets`, `pallet_weight_kg`, `pallet_quantity`.

### R016. Packing list detailed gross weight formula

- Severity: `error`
- Type: `formula`
- Source fields:
  - `packing_list.net_weight_kg`
  - `packing_list.empty_package_weight_kg`
  - `packing_list.items_quantity`
  - `packing_list.pallet_weight_kg`
  - `packing_list.pallet_quantity`
  - `packing_list.gross_weight_kg`
- Logic:
  `gross_weight_kg == net_weight_kg + (empty_package_weight_kg * items_quantity) + (pallet_weight_kg * pallet_quantity)`
- Note:
  В исходном правиле `BQ` трактуется как количество bags/items.

### R017. Packing list must contain container number

- Severity: `warning`
- Type: `presence`
- Source fields:
  - `packing_list.container_no`
- Logic:
  Поле желательно.

### R018. Prepayment requires payment confirmation

- Severity: `warning`
- Type: `presence`
- Source fields:
  - `addendum.payment_terms`
  - `payment_confirmation.document_presence`
- Logic:
  Если `payment_terms` содержит `prepayment`, в пакете должен присутствовать файл подтверждения оплаты.

### R019. COA must contain batch number

- Severity: `error`
- Type: `presence`
- Source fields:
  - `coa.batch_no`
- Logic:
  Поле обязательно.

### R020. COA must contain manufacture date

- Severity: `error`
- Type: `presence`
- Source fields:
  - `coa.manufacture_date`
- Logic:
  Поле обязательно.

### R021. COA must contain expiry date

- Severity: `error`
- Type: `presence`
- Source fields:
  - `coa.expiry_date`
- Logic:
  Поле обязательно.

### R022. COA manufacture date before BL date

- Severity: `error`
- Type: `date_compare`
- Source fields:
  - `coa.manufacture_date`
  - `mbl.bl_date` или `hbl.bl_date`
- Logic:
  `coa.manufacture_date < bl_date`

### R023. COA expiry date after manufacture date

- Severity: `error`
- Type: `date_compare`
- Source fields:
  - `coa.expiry_date`
  - `coa.manufacture_date`
- Logic:
  `coa.expiry_date > coa.manufacture_date`

### R024. BL gross weight matches packing list

- Severity: `error`
- Type: `exact_match`
- Source fields:
  - `bill_of_lading.gross_weight_kg`
  - `packing_list.gross_weight_kg`
- Logic:
  Значения должны совпадать с учетом `tolerance`.

### R025. BL packages quantity matches packing list

- Severity: `error`
- Type: `exact_match`
- Source fields:
  - `bill_of_lading.packages_quantity`
  - `packing_list.packages_quantity`
- Logic:
  Значения должны совпадать.

### R026. BL container number matches packing list

- Severity: `error`
- Type: `exact_match`
- Source fields:
  - `bill_of_lading.container_no`
  - `packing_list.container_no`
- Logic:
  Значения должны совпадать после нормализации.

### R027. BL cargo description must not contain HS code

- Severity: `warning`
- Type: `presence`
- Source fields:
  - `bill_of_lading.cargo_description`
- Logic:
  В `cargo_description` не должно быть подстрок вроде `HS code`, `HS CODE`, `H.S. code`.

## 9. Приоритет правил для MVP

Чтобы первая версия была реализуемой, правила делятся на две очереди.

### MVP Core

Реализовать в первую очередь:

- R001 Shipper name consistency
- R002 Buyer name consistency
- R003 Contract number consistency
- R005 Addendum date later than contract date
- R006 Incoterms consistency
- R007 Invoice number consistency
- R008 Invoice line arithmetic
- R009 Invoice total arithmetic
- R010 Packing list must contain package type
- R011 Packing list must contain packages quantity
- R012 Packing gross weight formula basic
- R017 Packing list must contain container number
- R018 Prepayment requires payment confirmation
- R019-R023 COA presence and date rules
- R024-R027 BL consistency and cargo description rules

### Phase 2 After MVP Core

Перенести на второй шаг:

- R004 Product names consistency
- R013 Packing package weight reverse formula
- R014 Packing list must contain empty package weight
- R015 Packing list pallet condition
- R016 Packing list detailed gross weight formula

Причина:

- эти правила сильнее зависят от качества табличного extraction;
- для них выше риск неоднозначности полей на разных шаблонах.

## 10. Требования к результату проверки

Каждый validation result должен возвращаться в такой структуре:

```json
{
  "rule_code": "R024",
  "severity": "error",
  "status": "failed",
  "message": "Gross weight in Bill of Lading does not match Packing List.",
  "documents": ["mbl", "packing_list"],
  "fields": ["gross_weight_kg"],
  "observed_values": {
    "mbl.gross_weight_kg": 21540.0,
    "packing_list.gross_weight_kg": 21480.0
  },
  "evidence": [
    {
      "document_type": "mbl",
      "page_no": 1,
      "text_snippet": "Gross Weight: 21,540 KGS"
    }
  ]
}
```

### Статусы

- `passed`
- `failed`
- `skipped`
- `needs_review`

`needs_review` нужен, когда OCR дал недостаточную уверенность или найдено несколько кандидатов для одного поля.

Policy:

- `skipped` допустим только когда отсутствующая информация не критична для решения по пакету.
- если финальный документ присутствует, но в нем отсутствует критичное поле, правило должно возвращать видимый `failed`, а не информационный `skipped`.
- подробная политика классификации результатов описана в `docs/validation-policy.md`.

## 11. Требования к missing data и uncertain data

Если поле не найдено:

- правило `presence` возвращает `failed`;
- зависимые правила возвращают `skipped` или `needs_review`, а не ложный `failed`.

Если найдено несколько кандидатов:

- выбирается кандидат с наибольшим confidence;
- при близких confidence правило помечается как `needs_review`.

## 12. Открытые вопросы для уточнения

Ниже вопросы, которые стоит закрыть до реализации rule engine v1 в коде:

1. Нужно ли считать `HBL` приоритетнее `MBL`, если присутствуют оба?
2. Как именно сравнивать `product names` между invoice, packing list и addendum: строгое равенство, словарь синонимов или fuzzy match?
3. Какие допустимы отклонения по весу и суммам: `0`, `0.01`, `0.1`, `1 кг`?
4. Всегда ли `buyer_name` в BL соответствует buyer, а не consignee/notified party?
5. Обязателен ли `container_no` для всех видов поставок или только для контейнерных?
6. Нужно ли проверять `Certificate of Origin` и `Transport Invoice` отдельными правилами уже в v1, или пока только хранить и классифицировать их?

## 13. Рекомендуемый следующий артефакт

После этой спецификации следующий рабочий документ должен быть:

- `field-catalog.md` с детальной таблицей:
  - `document_type`
  - `field_name`
  - `label variants`
  - `data type`
  - `required`
  - `example`

Именно он станет прямым входом для extraction layer.
