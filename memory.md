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
- `backend/tests/test_text_extractor.py` covers extraction for addendum, COA, and payment confirmation OCR text in addition to invoice, packing list, and bill of lading.
- After expanding `text_extractor.py`, a six-file test pack was created from the same test documents; pack id was `7b15b940-1d0f-452f-850f-c99dc78cd8cc`.
- The updated six-file test pack completed OCR and normalization, generated a validation report with summary `27 total`, `23 passed`, `0 failed`, `4 skipped`, `0 warnings`, and `0 needs_review`, and pack status became `validated`.
- `POST /api/validation-runs` now accepts files and orchestrates intake, OCR, normalization, rule-engine validation, latest-report storage, and a workflow response containing `run_id`, `pack_id`, pack `status`, summary, grouped results, full report, and normalized documents.
- `GET /api/validation-runs/{pack_id}` returns the latest in-memory validation run response for a document pack.
- `backend/src/dynno_customs_api/api/serializers.py` contains shared response serializers for normalized documents, validation reports, and grouped validation results used by the validation-run workflow.
- `backend/src/dynno_customs_api/services/validation_report_store.py` stores the latest validation report per pack in memory; `POST /api/validation/reports/{pack_id}` now also saves generated reports there.
- `backend/tests/test_validation_runs.py` covers the validation-run workflow endpoint and latest-run lookup.
- `frontend/src/App.tsx` now implements the document validation workspace: file selection, `POST /api/validation-runs` submission, API status links, run summary metrics, grouped validation results, and normalized document table.
- `frontend/src/lib/api.ts` defines typed API helpers for health, schema index, and validation-run creation.
- `frontend/src/styles.css` defines the operational validation workspace layout and responsive report UI.
- `frontend/package-lock.json` was generated after installing frontend dependencies locally.
- `backend/src/dynno_customs_api/config.py` allows CORS from both `http://localhost:5173` and `http://127.0.0.1:5173` so the Vite dev server can call the API from either local URL.

## Decisions

- Start with a narrow MVP focused on one shipment per case and three core document types: invoice, packing list, and bill of lading.
- Plan the system as two modules: document validation and landed-cost calculation.
- Prefer Python/FastAPI backend, React frontend, PostgreSQL, and an external OCR/document AI provider for the first working version.
- Default extraction should read the full document first; explicit page regions should be added only for fields that prove ambiguous or unstable across templates.
- The first validation specification separates `MVP Core` rules from `Phase 2` rules to reduce extraction complexity in the initial implementation.
- The extraction layer now has a document-by-document field catalog with explicit MVP Core priorities.
- The data contract is now formalized as JSON Schema around five artifacts: common definitions, normalized document, document pack, validation result, and validation report.
- The implementation direction is now an internal web application with a separate backend API and manually scaffolded frontend.
- The next code layer after scaffolding is `document intake` first, before OCR and rule execution.
- After intake, the next implemented layer is a schema-aligned normalization stub that classifies documents by filename and emits `partial` normalized documents for downstream validation flow.
- The rule-engine runner treats `hbl` as the preferred bill of lading document when both `hbl` and `mbl` are present; otherwise it uses `mbl`.
- Rule results use the existing validation statuses: `passed`, `failed`, `skipped`, and `needs_review`; summary `warnings` counts failed warning-severity results.
- Rule `R015` is intentionally skipped until `has_pallets` or an equivalent pallet applicability signal is added to the normalized schema.
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
- `frontend` dependencies were installed with portable Node.js `v22.12.0`; `npm run build` completed successfully and produced `frontend/dist/`.
- After frontend workflow and CORS changes, `backend\\.venv\\Scripts\\python -m pytest backend\\tests` passed with `28 passed`, and `frontend` `npm run build` completed successfully.
- The Vite dev server was started at `http://127.0.0.1:5173/` and returned HTTP 200; the backend API was restarted at `http://127.0.0.1:8000/health` and returned `status: ok`.

## Open Inputs Needed From User

- Real sample documents or anonymized equivalents.
- Exact validation rules per document and cross-document comparison rules.
- Cost-calculation formula, tariff inputs, and route/TN VED-specific exceptions. User plans to provide FOB formula later.
- Still needs clarification on product-name comparison strictness across invoice/packing list/addendum, numeric tolerances, buyer vs consignee mapping in BL, and container-number applicability.
