const API_BASE = (import.meta.env.VITE_DYNNO_API_BASE ?? "http://localhost:8000/api").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type HealthResponse = {
  status: string;
  app: string;
  version: string;
  timestamp: string;
};

export type SchemaIndexResponse = {
  schemas: string[];
};

export type AuthUser = {
  user_id: string;
  email: string;
  full_name: string;
  role: "admin" | "operator" | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
};

export type AuthBootstrapStatusResponse = {
  has_users: boolean;
  registration_open: boolean;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: AuthUser;
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
  evidence: ValidationEvidence[];
  confidence?: number | null;
};

export type ValidationEvidence = {
  document_type: string;
  page_no: number;
  field_name?: string | null;
  text_snippet: string;
  confidence?: number | null;
};

export type ValidationResultGroups = {
  failed: ValidationResult[];
  needs_review: ValidationResult[];
  warnings: ValidationResult[];
  skipped: ValidationResult[];
  passed: ValidationResult[];
};

export type NormalizedField = {
  value?: unknown;
  raw_value?: unknown;
  normalized_value?: unknown;
  confidence?: number | null;
  page_no?: number | null;
  text_snippet?: string | null;
  derived?: boolean | null;
  unit?: string | null;
  [key: string]: unknown;
};

export type NormalizedFieldValue =
  | NormalizedField
  | string
  | number
  | boolean
  | null
  | undefined
  | unknown[]
  | Record<string, unknown>;

export type NormalizedLineItem = Record<string, NormalizedFieldValue>;

export type NormalizedDocument = {
  document_id: string;
  document_type: string;
  source_file_name: string;
  pages: number;
  extraction_status: string;
  fields: Record<string, NormalizedFieldValue>;
  line_items: NormalizedLineItem[];
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

function buildHeaders(init?: HeadersInit, authToken?: string): Headers {
  const headers = new Headers(init);
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  return headers;
}

async function request<T>(path: string, init?: RequestInit, authToken?: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: buildHeaders(init?.headers, authToken),
  });

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    const contentType = response.headers.get("content-type") ?? "";

    if (contentType.includes("application/json")) {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string" && body.detail.trim()) {
        detail = body.detail;
      } else {
        detail = JSON.stringify(body);
      }
    } else {
      const bodyText = await response.text();
      if (bodyText.trim()) {
        detail = bodyText;
      }
    }

    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function fetchSchemaIndex(): Promise<SchemaIndexResponse> {
  return request<SchemaIndexResponse>("/schemas");
}

export function fetchAuthBootstrapStatus(): Promise<AuthBootstrapStatusResponse> {
  return request<AuthBootstrapStatusResponse>("/auth/bootstrap-status");
}

export function registerAuth(payload: {
  email: string;
  password: string;
  full_name: string;
}): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function loginAuth(payload: {
  email: string;
  password: string;
}): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchCurrentUser(authToken: string): Promise<AuthUser> {
  return request<AuthUser>("/auth/me", undefined, authToken);
}

export function logoutAuth(authToken: string): Promise<{ status: string }> {
  return request<{ status: string }>(
    "/auth/logout",
    {
      method: "POST",
    },
    authToken,
  );
}

export function createValidationRun(files: File[], authToken: string): Promise<ValidationRunResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  return request<ValidationRunResponse>(
    "/validation-runs",
    {
      method: "POST",
      body: formData,
    },
    authToken,
  );
}

export function fetchValidationRuns(authToken: string): Promise<ValidationRunListResponse> {
  return request<ValidationRunListResponse>("/validation-runs", undefined, authToken);
}

export function fetchValidationRun(packId: string, authToken: string): Promise<ValidationRunResponse> {
  return request<ValidationRunResponse>(`/validation-runs/${packId}`, undefined, authToken);
}
