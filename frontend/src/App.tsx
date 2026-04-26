import { useEffect, useState } from "react";

import { fetchHealth, fetchSchemaIndex } from "./lib/api";

type HealthState = {
  status: string;
  app: string;
  version: string;
  timestamp: string;
};

export default function App() {
  const [health, setHealth] = useState<HealthState | null>(null);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [healthResponse, schemaResponse] = await Promise.all([
          fetchHealth(),
          fetchSchemaIndex(),
        ]);

        if (!active) {
          return;
        }

        setHealth(healthResponse);
        setSchemas(schemaResponse.schemas);
      } catch (err) {
        if (!active) {
          return;
        }

        setError(err instanceof Error ? err.message : "Unknown error");
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero__eyebrow">Internal Operations Platform</div>
        <h1>Dynno Customs</h1>
        <p className="hero__copy">
          Web workspace for customs document intake, extraction control, validation
          feedback, and later landed-cost calculation.
        </p>
      </section>

      <section className="grid">
        <article className="card">
          <h2>Upload Flow</h2>
          <p>Planned flow for document pack intake and background validation.</p>
          <ol>
            <li>Upload contract pack</li>
            <li>Classify documents</li>
            <li>Extract normalized fields</li>
            <li>Run rule engine</li>
            <li>Review warnings and errors</li>
          </ol>
        </article>

        <article className="card">
          <h2>API Status</h2>
          {health ? (
            <dl className="kv">
              <div>
                <dt>Status</dt>
                <dd>{health.status}</dd>
              </div>
              <div>
                <dt>App</dt>
                <dd>{health.app}</dd>
              </div>
              <div>
                <dt>Version</dt>
                <dd>{health.version}</dd>
              </div>
            </dl>
          ) : (
            <p>Backend not connected yet.</p>
          )}
        </article>

        <article className="card">
          <h2>Schema Registry</h2>
          {schemas.length > 0 ? (
            <ul className="schema-list">
              {schemas.map((schema) => (
                <li key={schema}>{schema}</li>
              ))}
            </ul>
          ) : (
            <p>No schema index loaded.</p>
          )}
        </article>

        <article className="card card--wide">
          <h2>Security Posture</h2>
          <ul>
            <li>Internal web app with centralized updates</li>
            <li>Self-hosted storage for sensitive document packs</li>
            <li>API boundary for auth, audit, and role separation</li>
            <li>Background workers isolated from UI traffic</li>
          </ul>
        </article>
      </section>

      {error ? <p className="error-banner">{error}</p> : null}
    </main>
  );
}
