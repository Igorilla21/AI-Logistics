# Project Memory

## Repository State

- Workspace root: `C:\Users\Пользователь\Desktop\dynnoCustoms`.
- As of 2026-04-25, the workspace was empty before initialization files were added.

## Product Goal

- The product is intended to validate customs document packages and detect inconsistencies across documents.
- The product is also intended to calculate estimated landed cost in Russia from route, weight, goods price, and TN VED code.

## Current Artifacts

- `docs/product-roadmap.md` contains the initial product plan, MVP scope, architecture outline, timeline, risks, and required business inputs.
- `Rule engine v1.txt` contains the first verified set of document-validation rules for the standard document pack.
- `docs/document-validation-spec.md` contains the first structured specification for document validation, including canonical fields, normalization rules, rule catalog, MVP priorities, and open questions.
- `docs/field-catalog.md` defines the extraction field catalog by document type, label variants, data types, v1 requiredness, examples, and extraction notes.
- `schemas/common.schema.json`, `schemas/normalized-document.schema.json`, `schemas/document-pack.schema.json`, `schemas/validation-result.schema.json`, and `schemas/validation-report.schema.json` define the first machine-readable JSON contracts for extraction and validation flows.
- `docs/json-schema-overview.md` summarizes the role of the JSON schemas in the pipeline.
- `backend` now contains a FastAPI scaffold with health, schema registry, document-pack, mock validation, and rule-engine validation endpoints.
- `frontend` contains a React/Vite client for the internal web interface.
- `docs/web-application-architecture.md` records the recommended internal web deployment model and security rationale.
- `.gitignore` and root `README.md` were added for repository hygiene and local setup guidance.
- `backend` now also includes in-memory `document pack` storage, file persistence into repo-local `uploads/`, and API routes to create, list, and fetch packs.
- `backend` now includes filename-based document classification, normalized-document domain models, a stub normalization pipeline, and pack-level normalization endpoints.
- `backend/src/dynno_customs_api/services/rule_engine_runner.py` implements the validation rule runner for rules `R001` through `R027`.
- `POST /api/validation/reports/{pack_id}` runs the rule engine for a document pack, auto-runs the current normalization stub when needed, returns a validation report, and updates pack status to `validated`, `needs_review`, or `failed`.
- `backend/pyproject.toml` now includes OCR-related dependencies: `pytesseract`, `Pillow`, and `PyMuPDF`.
- `backend/src/dynno_customs_api/config.py` now defines OCR settings for Tesseract command, OCR languages, PDF render DPI, OCR temp dir, and OCR output dir.
- `backend/src/dynno_customs_api/services/tesseract_ocr.py` implements the Tesseract OCR adapter for stored PDF and image documents, returning page-level raw text and OCR confidence.
- `backend/src/dynno_customs_api/services/ocr_service.py` runs OCR for all files in a document pack and stores the latest OCR results in the in-memory document pack record.
- `POST /api/document-packs/{pack_id}/ocr` runs OCR for a document pack; `GET /api/document-packs/{pack_id}/ocr-results` returns the pack's latest OCR results.
- Completed OCR runs now persist raw text files under repo-local `storage/ocr/{pack_id}/{document_id}.txt` and expose that path as `raw_text_ref`.
- `backend/src/dynno_customs_api/services/text_extractor.py` implements the first OCR-text extractor for invoice, packing list, and bill of lading MVP fields.
- On 2026-05-05, a test document pack was created from `test-docs/invoice.pdf`, `test-docs/packing_list.pdf`, and `test-docs/bl.pdf`; uploaded files were persisted under `uploads/9314bab4-e861-4daa-abc9-84e44a654c58/`.
- The same test pack completed OCR for all three PDFs, persisted OCR text under `storage/ocr/9314bab4-e861-4daa-abc9-84e44a654c58/`, normalized all three documents with `partial` extraction status, and generated a validation report with summary `27 total`, `16 passed`, `3 failed`, `8 skipped`, `0 warnings`, and `0 needs_review`.
- On 2026-05-05, a second test document pack was created from `test-docs/invoice.pdf`, `test-docs/packing_list.pdf`, `test-docs/bl.pdf`, `test-docs/addendum.pdf`, `test-docs/coa.pdf`, and `test-docs/payment_confirmation.pdf`; pack id was `015350d1-49a0-4402-92f0-869d3b4743e3`.
- The six-file test pack completed OCR for all six PDFs and normalized all six documents with `partial` extraction status, but `addendum`, `coa`, and `payment_confirmation` normalized fields were empty because `text_extractor.py` currently implements extraction only for invoice, packing list, and bill of lading document types.
- `backend/src/dynno_customs_api/services/text_extractor.py` now extracts addendum fields (`addendum_no`, `addendum_date`, `contract_no`, `contract_date`, `seller_name`, `buyer_name`, `incoterms`, `payment_terms`), COA fields (`invoice_no`, `batch_no`, `manufacture_date`, `expiry_date`), and payment-confirmation fields (`document_presence`, party names, contract/addendum references).
- On 2026-05-29, `backend/src/dynno_customs_api/services/text_extractor.py` was expanded again to work on structured OCR text with preserved line breaks plus flat-text fallbacks; extraction coverage now includes more realistic addendum, COA, payment-confirmation, certificate-of-origin, and BL/MBL/HBL variants seen in the `тестовые доки/` baseline set.
- On 2026-05-29, `_parse_date` in `backend/src/dynno_customs_api/services/text_extractor.py` was hardened to ignore OCR-noise date matches that form invalid calendar dates instead of raising and aborting the whole normalization run.
- `backend/tests/test_text_extractor.py` covers extraction for addendum, COA, and payment confirmation OCR text in addition to invoice, packing list, and bill of lading.
- After expanding `text_extractor.py`, a six-file test pack was created from the same test documents; pack id was `7b15b940-1d0f-452f-850f-c99dc78cd8cc`.
- The updated six-file test pack completed OCR and normalization, generated a validation report with summary `27 total`, `23 passed`, `0 failed`, `4 skipped`, `0 warnings`, and `0 needs_review`, and pack status became `validated`.
- `POST /api/validation-runs` now accepts files and orchestrates intake, OCR, normalization, rule-engine validation, latest-report storage, and a workflow response containing `run_id`, `pack_id`, pack `status`, summary, grouped results, full report, and normalized documents.
- `GET /api/validation-runs/{pack_id}` returns the latest persisted validation run response for a document pack.
- `backend/src/dynno_customs_api/api/serializers.py` contains shared response serializers for normalized documents, validation reports, and grouped validation results used by the validation-run workflow.
- `backend/src/dynno_customs_api/services/validation_workflow.py` now contains the shared application workflow for intake-to-report orchestration and latest/history retrieval, so both web API routes and a future desktop shell can invoke the same backend core without duplicating HTTP-layer logic.
- `backend/src/dynno_customs_api/services/document_classifier.py` now supports broader filename normalization, common logistics-document abbreviations (`CI`, `PL`, `Add`, `BL`, `CO`, `COO`, etc.), and OCR-text fallback classification when the filename is weak.
- `backend/src/dynno_customs_api/services/tesseract_ocr.py` now preserves OCR page text as structured multi-line text based on Tesseract line metadata instead of flattening all words into one space-joined string; persisted raw OCR text now retains line breaks.
- `backend/src/dynno_customs_api/services/database.py` now initializes SQL-backed persistence tables for document packs, document files, OCR document results, normalized documents, validation reports, and validation results.
- `backend/src/dynno_customs_api/services/document_pack_store.py` now uses a SQL-backed store for persisted document packs, document files, OCR results, and normalized documents while retaining the in-memory store class for isolated unit tests.
- `backend/src/dynno_customs_api/services/validation_report_store.py` now uses a SQL-backed store for persisted validation reports and validation results while retaining the in-memory store class for isolated unit tests.
- `backend/alembic.ini`, `backend/alembic/env.py`, and `backend/alembic/versions/20260521_0001_baseline_schema.py` now define Alembic migration support and a baseline schema revision for the current SQL persistence model.
- `backend/src/dynno_customs_api/services/migrations.py` runs Alembic migrations from application startup, replacing startup-time table creation through SQLAlchemy `create_all`.
- `backend/tests/test_validation_runs.py` covers the validation-run workflow endpoint and latest-run lookup.
- `GET /api/validation-runs` now returns persisted validation-run history summaries built from saved document packs and latest validation reports.
- `backend/tests/conftest.py` now forces a repo-local SQLite test database under `.tmp/pytest/backend-tests.db` and clears persisted tables between tests.
- `backend/tests/test_validation_report_store.py` covers latest-report persistence and retrieval from the SQL-backed validation report store.
- `backend/tests/test_validation_report_store.py` now also covers roundtrip persistence of separate `validation_results` rows attached to the latest report.
- `backend/tests/test_document_pack_store.py` now covers SQL roundtrip persistence for nested pack data including files, OCR results, and normalized documents.
- `frontend/src/App.tsx` now implements the document validation workspace: file selection, `POST /api/validation-runs` submission, API status links, run summary metrics, grouped validation results, and normalized document table.
- `frontend/src/App.tsx` now also loads validation-run history, shows saved runs in the side panel, and can reopen a previous run without rerunning OCR or validation.
- `frontend/src/App.tsx` now also renders validation result details from `observed_values` and `expected_values`, highlights `needs_review` and `skipped` states separately, and selects the initial result tab by group priority instead of a simple failed-or-skipped fallback.
- `frontend/src/lib/api.ts` defines typed API helpers for health, schema index, and validation-run creation.
- `frontend/src/styles.css` defines the operational validation workspace layout, responsive report UI, and dedicated detail-card styling for `needs_review`, `skipped`, and observed/expected rule values.
- `frontend/package-lock.json` was generated after installing frontend dependencies locally.
- `backend/src/dynno_customs_api/config.py` allows CORS from both `http://localhost:5173` and `http://127.0.0.1:5173` so the Vite dev server can call the API from either local URL.
- Root `.gitignore` now excludes repo-local `.env` files, including `backend/.env`, so local database credentials stay untracked.

## Decisions

- Start with a narrow MVP focused on one shipment per case and three core document types: invoice, packing list, and bill of lading.
- Plan the system as two modules: document validation and landed-cost calculation.
- The current product implementation is deterministic application software, not an LLM-based agent runtime; OCR, extraction, validation, and reporting currently run without any language model dependency.
- Prefer Python/FastAPI backend, React frontend, PostgreSQL, and an external OCR/document AI provider for the first working version.
- For the first persistence step, keep report structures serialized as JSON payloads in SQL tables.
- For the second persistence step, store `document files`, `OCR results`, and `normalized documents` in separate SQL tables while still keeping per-row JSON payloads to avoid premature ORM decomposition of every nested field.
- After extending the second persistence step, store `validation results` in a separate SQL table keyed by `(report_id, rule_code)` while keeping the report header and summary payload in `validation_reports`.
- Default extraction should read the full document first; explicit page regions should be added only for fields that prove ambiguous or unstable across templates.
- The first validation specification separates `MVP Core` rules from `Phase 2` rules to reduce extraction complexity in the initial implementation.
- The extraction layer now has a document-by-document field catalog with explicit MVP Core priorities.
- The data contract is now formalized as JSON Schema around five artifacts: common definitions, normalized document, document pack, validation result, and validation report.
- The implementation direction is now an internal web application with a separate backend API and manually scaffolded frontend.
- The next code layer after scaffolding is `document intake` first, before OCR and rule execution.
- After intake, the next implemented layer is a schema-aligned normalization stub that classifies documents by filename and emits `partial` normalized documents for downstream validation flow.
- The rule-engine runner treats `hbl` as the preferred bill of lading document when both `hbl` and `mbl` are present; otherwise it uses `mbl`.
- Rule results use the existing validation statuses: `passed`, `failed`, `skipped`, and `needs_review`; summary `warnings` counts failed warning-severity results.
- Rule `R015` now uses the normalized `has_pallets` applicability signal: it passes when pallets are not applicable, warns when pallets are present but pallet weight or quantity is missing, and passes when pallet details are present.
- Rule `R004` product-name matching compares invoice, packing list, addendum, and COA product line items when available; BL `cargo_description` is excluded because BL descriptions may be shorter or more general.
- OCR endpoint execution currently runs synchronously and stores OCR result metadata in memory; raw OCR text is persisted to repo-local files.
- Document pack status now includes `ocr_completed` and `ocr_failed` in the JSON Schema.
- For the observed sample commercial invoice, `QRT-SOH` is the customs-relevant contract number, `ADD 68` is the addendum number, and `RT260004` is a Sales Contract number that is not needed for customs validation.
- Invoice unit price values like `CNY9.1000/MT` mean `9100 CNY` per metric ton.
- Extractor v1 intentionally ignores Sales Contract number `RT260004` and maps invoice unit price `CNY9.1000/MT` to `9100.0 CNY/MT` while converting `18000.00KG` to `18.0 MT` for invoice arithmetic.

## Validation Scope Known So Far

- Standard document pack currently includes: contract, addendum, commercial invoice, packing list, COA, master/house bill of lading, transport invoice, certificate of origin, and payment confirmation.
- Verified rule themes in `Rule engine v1.txt`: party-name matching, contract/invoice references, product-name matching, addendum-vs-contract dates, Incoterms consistency, invoice number matching, invoice arithmetic, packing-list weight/package logic, prepayment-to-payment-confirmation dependency, COA batch/manufacture/expiry checks, and BL-to-packing-list consistency checks.
- The structured rule catalog currently defines rules `R001` through `R027`.
- The field catalog covers canonical fields, line-item schema, label variants, and extraction priorities for all currently known document types.

## Environment Notes

- `git` is available (`git version 2.54.0.windows.1`).
- `py` launcher is available with `Python 3.13.13`.
- System `node` and `npm` remain unavailable through PATH, but portable Node.js `v22.12.0` was downloaded to repo-local `.cache/node/` and used for frontend installation/build commands with npm cache in `.cache/npm/`.
- A project-local backend virtual environment was created at `backend/.venv`.
- `backend\\.venv\\Scripts\\python -m pip install -e backend[dev]` completed successfully.
- `backend\\.venv\\Scripts\\python -m pytest backend/tests` passed with `2 passed`.
- After rule-engine runner changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `8 passed`.
- Tesseract OCR is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- Tesseract version check returned `5.5.0.20241111`; available languages include `eng`, `rus`, `chi_sim`, `chi_tra`, `osd`, and `equ`.
- After installing OCR dependencies into `backend/.venv`, imports for `pytesseract`, `Pillow`, and `PyMuPDF` succeeded and `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `8 passed`.
- OCR config defaults resolved `settings.tesseract_cmd` to `C:\Program Files\Tesseract-OCR\tesseract.exe`, `settings.ocr_langs` to `eng+rus`, `settings.ocr_temp_dir` to repo-local `.tmp\ocr`, `settings.ocr_output_dir` to repo-local `storage\ocr`, and `settings.ocr_pdf_dpi` to `300`.
- After OCR config changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `10 passed`.
- After Tesseract OCR adapter changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `13 passed`.
- After OCR endpoint changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `17 passed`.
- After OCR raw-text persistence changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `18 passed`.
- After extractor v1 changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `22 passed`.
- On 2026-05-05, the backend was started with `backend\\.venv\\Scripts\\python -m uvicorn dynno_customs_api.main:app --host 127.0.0.1 --port 8000` from `backend`; `GET /api/health` returned `status: ok`.
- The 2026-05-05 validation report for the three-file test pack set pack status to `failed` because COA rules `R019`, `R020`, and `R021` failed due missing COA batch, manufacture date, and expiry date fields.
- The 2026-05-05 validation report for the six-file test pack also returned `27 total`, `16 passed`, `3 failed`, `8 skipped`, `0 warnings`, and `0 needs_review`; failures remained `R019`, `R020`, and `R021` because COA fields were not extracted despite OCR text containing `BATCH NO.: 95320172`, `MANUFACTURE DATE: MAR.08,2026`, and `EXPIRY DATE: MAR.07,2028`.
- After addendum/COA/payment extractor changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `26 passed`.
- After restarting uvicorn and rerunning the six-file validation pack, COA rules `R019` through `R023` and prepayment rule `R018` passed; remaining skipped rules were `R003`, `R005`, `R015`, and `R016`.
- After adding validation-run endpoints and shared serializers, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `28 passed`.
- After restarting uvicorn, `POST /api/validation-runs` on the six-file test set produced run id `9383b505-4499-4ece-b0dc-2e8dead12ea3`, pack id `dd91cc2f-caea-4e2d-900c-13839975593a`, status `validated`, summary `27 total`, `23 passed`, `0 failed`, `4 skipped`, `0 warnings`, and `0 needs_review`; `GET /api/validation-runs/{pack_id}` returned the same run.
- On 2026-05-14, backend dependencies were updated to include `sqlalchemy` and `psycopg[binary]`; `backend\\.venv\\Scripts\\python -m pytest backend\\tests` then passed with `31 passed`.
- Backend settings now include `DYNNO_DATABASE_URL`; the default runtime database path is repo-local `storage/dynno_customs.db`, while pytest uses repo-local `.tmp/pytest/backend-tests.db`.
- On 2026-05-15, PostgreSQL 17 was installed locally on Windows via `winget`; service `postgresql-x64-17` was started, database `dynno_customs` was created, and backend runtime was switched to PostgreSQL through local `backend/.env`.
- After the PostgreSQL switch on 2026-05-15, `GET /api/health` returned `status: ok`, and the `dynno_customs` database contained SQL-created tables `document_packs` and `validation_reports`.
- On 2026-05-21, the second persistence step was applied and verified: `dynno_customs` now also contains tables `document_files`, `ocr_document_results`, and `normalized_documents`.
- After the second persistence step on 2026-05-21, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `31 passed`.
- On 2026-05-21, persistence was extended further so `dynno_customs` now also contains table `validation_results`; the live PostgreSQL schema now includes `document_packs`, `document_files`, `ocr_document_results`, `normalized_documents`, `validation_reports`, and `validation_results`.
- On 2026-05-21, Alembic `1.18.4` was installed into `backend/.venv`, a baseline revision `20260521_0001` was added, `alembic upgrade head` successfully created the full schema in a fresh PostgreSQL database `dynno_customs_alembic_test`, and the existing local database `dynno_customs` was aligned to that baseline with `alembic stamp head`.
- After introducing Alembic on 2026-05-21, `backend\\.venv\\Scripts\\alembic.exe -c alembic.ini current` returned `20260521_0001 (head)` for the local PostgreSQL runtime, and `backend\\.venv\\Scripts\\python -m pytest tests` still passed with `31 passed`.
- On 2026-05-22, application startup was changed to run Alembic migrations; a FastAPI lifespan check against a repo-local SQLite database returned `200 ok` after applying baseline migration, and the temporary startup-check database was removed.
- On 2026-05-22, validation-run history was added end-to-end: backend history API, frontend history list, and reopening saved runs by `pack_id`.
- On 2026-05-22, `has_pallets` was added to normalized fields and schema, packing-list extraction now derives it from pallet terms, and rule `R015` now evaluates instead of always skipping when the applicability signal exists.
- On 2026-05-26, validation orchestration was refactored out of FastAPI routes into `services/validation_workflow.py`; both `/api/validation-runs` and `/api/validation/reports/{pack_id}` now use the same workflow service and shared run serializers.
- After the 2026-05-26 validation workflow refactor, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `33 passed`.
- On 2026-05-29, a baseline OCR run across `10` real document sets (`62` PDFs) under `тестовые доки/` showed `0` OCR execution failures but high filename-classification noise: `30` filename fallbacks, `34` low-classifier-confidence documents, `19` documents with no extracted fields, and `5` low-OCR-confidence documents.
- On 2026-05-29, after improving document classification, a repeat baseline run on the same `10` sets reduced filename fallbacks from `30` to `5` and low-classifier-confidence documents from `34` to `9`; the remaining dominant gap became extraction coverage (`25` documents with no extracted fields), especially for COA, bill of lading, certificate of origin, and some addendum/payment files.
- After the 2026-05-29 classifier changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `36 passed`.
- On 2026-05-29, OCR text assembly was upgraded to preserve line breaks from Tesseract page output; after this OCR-structure change, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `37 passed`.
- After the 2026-05-29 extractor expansion on top of structured OCR text, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `42 passed`.
- On 2026-05-29, a repeat baseline run across the same `10` real document sets (`62` PDFs) after extractor improvements produced `.tmp/ocr_baseline_20260529_after_extractor.json`; compared with the post-classifier baseline, `no_extracted_fields` dropped from `25` to `5`, documents with `5+` extracted fields increased from `8` to `20`, and average extracted field count rose from `1.97` to `3.63`.
- The full repeat baseline run across all `10` sets on 2026-05-29 took about `440.7` seconds end-to-end in the local test workflow, roughly `44.1` seconds per order or `7.1` seconds per PDF on average.
- After the 2026-05-22 history and `R015` changes, `backend\\.venv\\Scripts\\python -m pytest tests` passed with `32 passed`, and the frontend TypeScript/Vite production build completed successfully via repo-local Node.js.
- On 2026-05-22, local backend and frontend servers were available at `http://127.0.0.1:8000/` and `http://127.0.0.1:5173/`; HTTP checks returned `200` for `/api/health` and the Vite UI root.
- `frontend` dependencies were installed with portable Node.js `v22.12.0`; `npm run build` completed successfully and produced `frontend/dist/`.
- After frontend workflow and CORS changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `28 passed`, and `frontend` `npm run build` completed successfully.
- After the review-flow UI changes on 2026-05-06, `frontend` TypeScript build and Vite production build both succeeded when invoked directly through repo-local `node.exe`; the `npm.cmd run build` wrapper returned `Access is denied` in this shell environment, but direct `node` execution completed successfully.
- The Vite dev server was started at `http://127.0.0.1:5173/` and returned HTTP 200; the backend API was restarted at `http://127.0.0.1:8000/health` and returned `status: ok`.

## Open Inputs Needed From User

- Real sample documents or anonymized equivalents.
- Exact validation rules per document and cross-document comparison rules.
- Cost-calculation formula, tariff inputs, and route/TN VED-specific exceptions. User plans to provide FOB formula later.
- Still needs clarification on product-name comparison strictness across invoice/packing list/addendum, numeric tolerances, buyer vs consignee mapping in BL, and container-number applicability.
