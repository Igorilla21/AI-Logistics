# Web Application Architecture

## Recommendation

For this product, the right default is an **internal web application with a separate backend**, not a desktop-first application.

## Why Web Is Better Here

### 1. Centralized updates

- backend rules can be updated without reinstalling software on every workstation;
- UI changes, rule changes, and OCR pipeline changes can be rolled out centrally;
- security fixes can be applied faster.

### 2. Better scaling path

- file upload traffic, OCR jobs, and validation jobs can be scaled separately;
- heavy document processing can run in worker queues;
- storage, API, and UI can evolve independently.

### 3. Better security controls

- documents stay in a controlled server-side environment;
- access control can be managed centrally;
- audit logs and retention rules are easier to enforce;
- integrations with SSO, VPN-only access, and private storage are simpler.

## Recommended Deployment Model

For customs and commercial documents, start with a **self-hosted internal web platform**:

- `frontend` served inside the corporate perimeter;
- `backend API` behind reverse proxy and authentication;
- `PostgreSQL` for metadata and validation history;
- `object storage` for source files and OCR outputs;
- `background workers` for OCR, normalization, and validation;
- optional `private OCR provider` or tightly controlled external OCR integration.

## Security Notes

### Data at rest

- encrypt object storage and database volumes;
- separate raw documents from normalized extracted data;
- store file hashes for integrity checks.

### Data in transit

- TLS everywhere;
- signed upload/download URLs if object storage is exposed indirectly;
- internal service-to-service authentication.

### Access control

- role-based access for operators, reviewers, and admins;
- tenant or customer isolation if multiple legal entities will use the system;
- audit trail for upload, view, validation, and override actions.

### Sensitive integrations

- if using external OCR, do not send every document by default without contractual and legal review;
- plan a switchable OCR adapter so you can replace providers later.

## When Desktop Would Be Better

Desktop is justified only if at least one of these is mandatory:

- strict offline work with no internal server;
- legal or policy restrictions against server-side document storage;
- workstation-local OCR and validation as a hard requirement.

Even then, a hybrid model is often better: desktop capture client plus central backend.

## Recommended Technical Split

### Frontend

- React + Vite
- upload workflow
- validation report UI
- manual review and override screens

### Backend

- FastAPI
- REST API for upload, pack management, schema registry, validation jobs, and reports
- adapters for OCR and storage

### Workers

- queue-driven tasks for OCR, extraction, normalization, and validation
- isolated from public request cycle

## Update Strategy

- use semantic versioning for API and schema contracts;
- keep JSON Schema versioned separately from UI and backend releases;
- add migration strategy for stored normalized documents and validation reports.
