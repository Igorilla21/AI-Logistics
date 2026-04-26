# JSON Schema Overview

## Назначение

Набор JSON Schema файлов в папке `schemas` задает контракт данных между:

- document intake;
- OCR/extraction layer;
- normalization layer;
- rule engine;
- UI отчета по валидации.

## Состав схем

- `schemas/common.schema.json`
  Общие определения: `documentType`, `severity`, `validationStatus`, `evidence`, `fieldCandidate`, типы полей и `lineItem`.

- `schemas/normalized-document.schema.json`
  Нормализованный документ после extraction.

- `schemas/document-pack.schema.json`
  Пакет документов по одной поставке.

- `schemas/validation-result.schema.json`
  Результат выполнения одного правила.

- `schemas/validation-report.schema.json`
  Итоговый отчет по проверке всего пакета.

## Минимальный поток данных

1. Пользователь загружает файлы.
2. Система формирует `document-pack`.
3. Каждый файл преобразуется в `normalized-document`.
4. Rule engine производит массив `validation-result`.
5. UI получает готовый `validation-report`.

## Практический смысл

Эти схемы позволяют:

- валидировать входы и выходы модулей;
- не ломать интеграции при изменении extraction;
- хранить explainability через `evidence`;
- отделить OCR-слой от business rules.
