import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import {
  createValidationRun,
  fetchValidationRun,
  fetchValidationRuns,
  fetchHealth,
  fetchSchemaIndex,
  HealthResponse,
  NormalizedDocument,
  ValidationEvidence,
  ValidationResult,
  ValidationRunSummary,
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

const DEFAULT_GROUP_PRIORITY: ResultGroupKey[] = [
  "failed",
  "needs_review",
  "warnings",
  "skipped",
  "passed",
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

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "string") {
    return value.trim() || "-";
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return "-";
    }
    return value.map((item) => formatValue(item)).join(", ");
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function formatFieldLabel(value: string): string {
  return value
    .replace(/\[(\d+)\]/g, " $1 ")
    .split(/[._]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatDocumentType(value: string): string {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => (part.length <= 3 ? part.toUpperCase() : part.charAt(0).toUpperCase() + part.slice(1)))
    .join(" ");
}

function getExpectedInputKeys(item: ValidationResult): string[] {
  if (item.documents.length === 1) {
    return item.fields.map((field) => `${item.documents[0]}.${field}`);
  }

  if (item.fields.length === 1) {
    return item.documents.map((document) => `${document}.${item.fields[0]}`);
  }

  if (item.documents.length === item.fields.length) {
    return item.documents.map((document, index) => `${document}.${item.fields[index]}`);
  }

  return [];
}

function getMissingInputKeys(item: ValidationResult): string[] {
  const observedKeys = new Set(Object.keys(item.observed_values ?? {}));
  return getExpectedInputKeys(item).filter((key) => !observedKeys.has(key));
}

function getSkippedReason(item: ValidationResult): string {
  const missingInputs = getMissingInputKeys(item);
  if (missingInputs.length > 0) {
    return `Rule was not evaluated because these required inputs are missing: ${missingInputs
      .map((key) => formatFieldLabel(key))
      .join(", ")}.`;
  }

  return "Rule was not evaluated because the required data or applicability signal was missing.";
}

function getInitialGroup(run: ValidationRunResponse): ResultGroupKey {
  for (const group of DEFAULT_GROUP_PRIORITY) {
    if (run.grouped_results[group].length > 0) {
      return group;
    }
  }

  return "passed";
}

function StatusPill({ status }: { status: string }) {
  return <span className={`status-pill status-pill--${status}`}>{status}</span>;
}

function ResultValues({
  label,
  values,
}: {
  label: string;
  values?: Record<string, unknown> | null;
}) {
  const entries = Object.entries(values ?? {});

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="result-values">
      <strong>{label}</strong>
      <dl className="result-values__list">
        {entries.map(([key, value]) => (
          <div key={`${label}-${key}`}>
            <dt>{formatFieldLabel(key)}</dt>
            <dd>
              <pre>{formatValue(value)}</pre>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function MissingInputs({ item }: { item: ValidationResult }) {
  const missingInputs = getMissingInputKeys(item);

  const shouldShowMissingInputs =
    (item.status === "skipped" || item.status === "needs_review") && missingInputs.length > 0;

  if (!shouldShowMissingInputs) {
    return null;
  }

  return (
    <div className="result-values result-values--missing">
      <strong>Missing required inputs</strong>
      <ul className="result-listing">
        {missingInputs.map((key) => (
          <li key={key}>{formatFieldLabel(key)}</li>
        ))}
      </ul>
    </div>
  );
}

function ResultEvidence({ evidence }: { evidence: ValidationEvidence[] }) {
  if (evidence.length === 0) {
    return null;
  }

  return (
    <div className="result-values">
      <strong>Source snippets</strong>
      <ul className="result-evidence">
        {evidence.map((item, index) => (
          <li key={`${item.document_type}-${item.page_no}-${item.field_name ?? "field"}-${index}`}>
            <div className="result-evidence__meta">
              <span>
                {formatDocumentType(item.document_type)} · page {item.page_no}
                {item.field_name ? ` · ${formatFieldLabel(item.field_name)}` : ""}
              </span>
              {item.confidence != null ? <span>{Math.round(item.confidence * 100)}%</span> : null}
            </div>
            <p>{item.text_snippet}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ResultList({ items, group }: { items: ValidationResult[]; group: ResultGroupKey }) {
  if (items.length === 0) {
    return <p className="empty-state">No rules in this group.</p>;
  }

  return (
    <div className="result-list">
      {items.map((item) => (
        <article className={`result-row result-row--${group}`} key={item.rule_code}>
          <div className="result-row__head">
            <div className="result-row__title">
              <strong>{item.rule_code}</strong>
              <StatusPill status={item.status} />
            </div>
            <span>{item.severity}</span>
          </div>
          <p>{item.message}</p>
          {group === "needs_review" ? (
            <p className="result-row__note">
              Manual review needed{item.confidence != null ? `, confidence ${Math.round(item.confidence * 100)}%` : ""}.
            </p>
          ) : null}
          {group === "skipped" ? (
            <p className="result-row__note">{getSkippedReason(item)}</p>
          ) : null}
          <div className="result-row__details">
            <ResultValues label="Found" values={item.observed_values} />
            <MissingInputs item={item} />
            <ResultValues label="Expected" values={item.expected_values} />
            <ResultEvidence evidence={item.evidence} />
          </div>
          <div className="result-row__meta">
            <span>{item.documents.map((document) => formatDocumentType(document)).join(", ")}</span>
            <span>{item.fields.map((field) => formatFieldLabel(field)).join(", ")}</span>
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

function RunHistory({
  items,
  activeRunId,
  isLoading,
  onOpenRun,
}: {
  items: ValidationRunSummary[];
  activeRunId?: string;
  isLoading: boolean;
  onOpenRun: (packId: string) => void;
}) {
  if (isLoading) {
    return <p className="empty-state">Loading history...</p>;
  }

  if (items.length === 0) {
    return <p className="empty-state">No saved validation runs yet.</p>;
  }

  return (
    <div className="history-list">
      {items.map((item) => (
        <button
          className={item.run_id === activeRunId ? "history-item history-item--active" : "history-item"}
          key={item.run_id}
          type="button"
          onClick={() => onOpenRun(item.pack_id)}
        >
          <span className="history-item__head">
            <strong>{item.status}</strong>
            <small>{formatDate(item.generated_at)}</small>
          </span>
          <span className="history-item__summary">
            {item.summary.failed} failed / {item.summary.needs_review} review / {item.summary.skipped} skipped
          </span>
          <span className="history-item__files">{item.file_names.slice(0, 2).join(", ") || `${item.document_count} documents`}</span>
        </button>
      ))}
    </div>
  );
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [run, setRun] = useState<ValidationRunResponse | null>(null);
  const [history, setHistory] = useState<ValidationRunSummary[]>([]);
  const [activeGroup, setActiveGroup] = useState<ResultGroupKey>("failed");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
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

  useEffect(() => {
    let active = true;

    async function loadHistory() {
      setIsHistoryLoading(true);
      try {
        const response = await fetchValidationRuns();
        if (active) {
          setHistory(response.items);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unable to load validation history.");
        }
      } finally {
        if (active) {
          setIsHistoryLoading(false);
        }
      }
    }

    void loadHistory();

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
      setActiveGroup(getInitialGroup(response));
      const historyResponse = await fetchValidationRuns();
      setHistory(historyResponse.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation run failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleOpenRun(packId: string) {
    setError(null);
    try {
      const response = await fetchValidationRun(packId);
      setRun(response);
      setActiveGroup(getInitialGroup(response));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to open validation run.");
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

          <section className="history-panel">
            <h2>History</h2>
            <RunHistory
              items={history}
              activeRunId={run?.run_id}
              isLoading={isHistoryLoading}
              onOpenRun={(packId) => void handleOpenRun(packId)}
            />
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
                <ResultList items={activeResults} group={activeGroup} />
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
