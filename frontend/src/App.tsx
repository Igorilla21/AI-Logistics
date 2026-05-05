import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import {
  createValidationRun,
  fetchHealth,
  fetchSchemaIndex,
  HealthResponse,
  NormalizedDocument,
  ValidationResult,
  ValidationRunResponse,
} from "./lib/api";

type ResultGroupKey = "failed" | "needs_review" | "warnings" | "skipped" | "passed";

const GROUPS: Array<{ key: ResultGroupKey; label: string }> = [
  { key: "failed", label: "Failed" },
  { key: "needs_review", label: "Needs review" },
  { key: "warnings", label: "Warnings" },
  { key: "skipped", label: "Skipped" },
  { key: "passed", label: "Passed" },
];

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function countFields(document: NormalizedDocument): number {
  return Object.keys(document.fields ?? {}).length;
}

function StatusPill({ status }: { status: string }) {
  return <span className={`status-pill status-pill--${status}`}>{status}</span>;
}

function ResultList({ items }: { items: ValidationResult[] }) {
  if (items.length === 0) {
    return <p className="empty-state">No rules in this group.</p>;
  }

  return (
    <div className="result-list">
      {items.map((item) => (
        <article className="result-row" key={item.rule_code}>
          <div className="result-row__head">
            <strong>{item.rule_code}</strong>
            <span>{item.severity}</span>
          </div>
          <p>{item.message}</p>
          <div className="result-row__meta">
            <span>{item.documents.join(", ")}</span>
            <span>{item.fields.join(", ")}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function DocumentTable({ documents }: { documents: NormalizedDocument[] }) {
  if (documents.length === 0) {
    return <p className="empty-state">No normalized documents yet.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>File</th>
            <th>Type</th>
            <th>Status</th>
            <th>Pages</th>
            <th>Fields</th>
            <th>Lines</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => (
            <tr key={document.document_id}>
              <td>{document.source_file_name}</td>
              <td>{document.document_type}</td>
              <td>{document.extraction_status}</td>
              <td>{document.pages}</td>
              <td>{countFields(document)}</td>
              <td>{document.line_items.length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [run, setRun] = useState<ValidationRunResponse | null>(null);
  const [activeGroup, setActiveGroup] = useState<ResultGroupKey>("failed");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [healthResponse, schemaResponse] = await Promise.all([fetchHealth(), fetchSchemaIndex()]);
        if (!active) {
          return;
        }
        setHealth(healthResponse);
        setSchemas(schemaResponse.schemas);
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Unable to connect to API.");
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, []);

  const selectedBytes = useMemo(() => files.reduce((total, file) => total + file.size, 0), [files]);
  const activeResults = run?.grouped_results[activeGroup] ?? [];

  function handleFilesChange(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files ?? []));
    setError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (files.length === 0) {
      setError("Select at least one document.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await createValidationRun(files);
      setRun(response);
      setActiveGroup(response.grouped_results.failed.length > 0 ? "failed" : "skipped");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation run failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Dynno Customs</p>
          <h1>Document Validation</h1>
        </div>
        <nav className="api-links" aria-label="API links">
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            Swagger
          </a>
          <a href="http://127.0.0.1:8000/redoc" target="_blank" rel="noreferrer">
            ReDoc
          </a>
        </nav>
      </header>

      <section className="workspace">
        <aside className="side-panel">
          <form className="upload-panel" onSubmit={handleSubmit}>
            <label className="file-picker">
              <span>Select documents</span>
              <input
                type="file"
                multiple
                accept=".pdf,image/png,image/jpeg,image/tiff,image/webp"
                onChange={handleFilesChange}
              />
            </label>

            <div className="file-summary">
              <strong>{files.length} files</strong>
              <span>{formatBytes(selectedBytes)}</span>
            </div>

            {files.length > 0 ? (
              <ul className="file-list">
                {files.map((file) => (
                  <li key={`${file.name}-${file.size}`}>
                    <span>{file.name}</span>
                    <small>{formatBytes(file.size)}</small>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="hint">Use invoice, packing list, bill of lading, addendum, COA, and payment confirmation.</p>
            )}

            <button className="primary-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Processing..." : "Run validation"}
            </button>
          </form>

          <section className="system-panel">
            <h2>System</h2>
            <dl className="kv">
              <div>
                <dt>API</dt>
                <dd>{health ? health.status : "offline"}</dd>
              </div>
              <div>
                <dt>Version</dt>
                <dd>{health?.version ?? "-"}</dd>
              </div>
              <div>
                <dt>Schemas</dt>
                <dd>{schemas.length}</dd>
              </div>
            </dl>
          </section>
        </aside>

        <section className="main-panel">
          {error ? <div className="error-banner">{error}</div> : null}

          {run ? (
            <>
              <section className="summary-band">
                <div>
                  <span>Pack</span>
                  <strong>{run.pack_id}</strong>
                </div>
                <div>
                  <span>Status</span>
                  <StatusPill status={run.status} />
                </div>
                <div>
                  <span>Updated</span>
                  <strong>{formatDate(run.updated_at)}</strong>
                </div>
              </section>

              <section className="metric-grid">
                <div className="metric">
                  <span>Total</span>
                  <strong>{run.summary.total_rules}</strong>
                </div>
                <div className="metric metric--passed">
                  <span>Passed</span>
                  <strong>{run.summary.passed}</strong>
                </div>
                <div className="metric metric--failed">
                  <span>Failed</span>
                  <strong>{run.summary.failed}</strong>
                </div>
                <div className="metric">
                  <span>Needs review</span>
                  <strong>{run.summary.needs_review}</strong>
                </div>
                <div className="metric">
                  <span>Skipped</span>
                  <strong>{run.summary.skipped}</strong>
                </div>
              </section>

              <section className="report-panel">
                <div className="tabs" role="tablist" aria-label="Validation result groups">
                  {GROUPS.map((group) => (
                    <button
                      className={group.key === activeGroup ? "tab tab--active" : "tab"}
                      type="button"
                      key={group.key}
                      onClick={() => setActiveGroup(group.key)}
                    >
                      <span>{group.label}</span>
                      <strong>{run.grouped_results[group.key].length}</strong>
                    </button>
                  ))}
                </div>
                <ResultList items={activeResults} />
              </section>

              <section className="documents-panel">
                <h2>Normalized Documents</h2>
                <DocumentTable documents={run.documents} />
              </section>
            </>
          ) : (
            <section className="empty-workspace">
              <h2>Ready for a document pack</h2>
              <p>Select the shipment documents and run validation. The API will intake files, run OCR, normalize fields, and return grouped rule results.</p>
            </section>
          )}
        </section>
      </section>
    </main>
  );
}
