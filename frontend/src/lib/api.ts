const API_BASE = "http://localhost:8000/api";

type HealthResponse = {
  status: string;
  app: string;
  version: string;
  timestamp: string;
};

type SchemaIndexResponse = {
  schemas: string[];
};

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function fetchSchemaIndex(): Promise<SchemaIndexResponse> {
  return request<SchemaIndexResponse>("/schemas");
}
