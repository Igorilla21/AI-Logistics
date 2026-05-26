const API_BASE = "http://localhost:8000/api";

export type HealthResponse = {
  status: string;
  app: string;
  version: string;
  timestamp: string;
};

export type SchemaIndexResponse = {
  schemas: string[];
};

export type ValidationSummary = {
  total_rules: number;
  passed: number;
  failed: number;
  warnings: number;
  needs_review: number;
  skipped: number;
};

export type ValidationResult = {
  rule_code: string;
  severity: "error" | "warning" | "info" | string;
  status: "passed" | "failed" | "skipped" | "needs_review" | string;
  message: string;
  documents: string[];
  fields: string[];
  observed_values: Record<string, unknown>;
  expected_values?: Record<string, unknown> | null;
  confidence?: number | null;
};

export type ValidationResultGroups = {
  failed: ValidationResult[];
  needs_review: ValidationResult[];
  warnings: ValidationResult[];
  skipped: ValidationResult[];
  passed: ValidationResult[];
};

export type NormalizedDocument = {
  document_id: string;
  document_type: string;
  source_file_name: string;
  pages: number;
  extraction_status: string;
  fields: Record<string, unknown>;
  line_items: Record<string, unknown>[];
};

export type ValidationRunResponse = {
  run_id: string;
  pack_id: string;
  status: string;
  created_at: string;
  updated_at?: string | null;
  summary: ValidationSummary;
  grouped_results: ValidationResultGroups;
  report: {
    report_id: string;
    pack_id: string;
    generated_at: string;
    summary: ValidationSummary;
    results: ValidationResult[];
  };
  documents: NormalizedDocument[];
};

export type ValidationRunSummary = {
  run_id: string;
  pack_id: string;
  status: string;
  created_at: string;
  updated_at?: string | null;
  generated_at: string;
  summary: ValidationSummary;
  document_count: number;
  file_names: string[];
};

export type ValidationRunListResponse = {
  items: ValidationRunSummary[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function fetchSchemaIndex(): Promise<SchemaIndexResponse> {
  return request<SchemaIndexResponse>("/schemas");
}

export function createValidationRun(files: File[]): Promise<ValidationRunResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  return request<ValidationRunResponse>("/validation-runs", {
    method: "POST",
    body: formData,
  });
}

export function fetchValidationRuns(): Promise<ValidationRunListResponse> {
  return request<ValidationRunListResponse>("/validation-runs");
}

export function fetchValidationRun(packId: string): Promise<ValidationRunResponse> {
  return request<ValidationRunResponse>(`/validation-runs/${packId}`);
}
