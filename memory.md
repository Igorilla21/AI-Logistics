# Project Memory

## Repository State

- Workspace root: `C:\Users\Пользователь\Desktop\dynnoCustoms`.
- As of 2026-04-25, the workspace was empty before initialization files were added.
- `git` is not available in PATH in the current shell environment.

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
- `backend` now contains a FastAPI scaffold with health, schema registry, document-pack, and mock validation endpoints.
- `frontend` now contains a manually scaffolded React/Vite client shell for the internal web interface.
- `docs/web-application-architecture.md` records the recommended internal web deployment model and security rationale.
- `.gitignore` and root `README.md` were added for repository hygiene and local setup guidance.

## Decisions

- Start with a narrow MVP focused on one shipment per case and three core document types: invoice, packing list, and bill of lading.
- Plan the system as two modules: document validation and landed-cost calculation.
- Prefer Python/FastAPI backend, React frontend, PostgreSQL, and an external OCR/document AI provider for the first working version.
- Default extraction should read the full document first; explicit page regions should be added only for fields that prove ambiguous or unstable across templates.
- The first validation specification separates `MVP Core` rules from `Phase 2` rules to reduce extraction complexity in the initial implementation.
- The extraction layer now has a document-by-document field catalog with explicit MVP Core priorities.
- The data contract is now formalized as JSON Schema around five artifacts: common definitions, normalized document, document pack, validation result, and validation report.
- The implementation direction is now an internal web application with a separate backend API and manually scaffolded frontend.

## Validation Scope Known So Far

- Standard document pack currently includes: contract, addendum, commercial invoice, packing list, COA, master/house bill of lading, transport invoice, certificate of origin, and payment confirmation.
- Verified rule themes in `Rule engine v1.txt`: party-name matching, contract/invoice references, product-name matching, addendum-vs-contract dates, Incoterms consistency, invoice number matching, invoice arithmetic, packing-list weight/package logic, prepayment-to-payment-confirmation dependency, COA batch/manufacture/expiry checks, and BL-to-packing-list consistency checks.
- The structured rule catalog currently defines rules `R001` through `R027`.
- The field catalog covers canonical fields, line-item schema, label variants, and extraction priorities for all currently known document types.

## Environment Notes

- `git` is available (`git version 2.54.0.windows.1`).
- `py` launcher is available with `Python 3.13.13`.
- `node` and `npm` were not usable in the current environment during scaffold creation, so the frontend was created manually and not executed.

## Open Inputs Needed From User

- Real sample documents or anonymized equivalents.
- Exact validation rules per document and cross-document comparison rules.
- Cost-calculation formula, tariff inputs, and route/TN VED-specific exceptions. User plans to provide FOB formula later.
- Still needs clarification on HBL vs MBL priority, product-name comparison strictness, numeric tolerances, buyer vs consignee mapping in BL, and container-number applicability.
