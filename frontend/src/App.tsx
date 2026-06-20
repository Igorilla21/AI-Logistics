import {
  ChangeEvent,
  SVGProps,
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  ApiError,
  AuthBootstrapStatusResponse,
  AuthUser,
  createValidationRun,
  fetchAuthBootstrapStatus,
  fetchCurrentUser,
  fetchValidationRun,
  fetchValidationRuns,
  fetchHealth,
  fetchSchemaIndex,
  HealthResponse,
  loginAuth,
  NormalizedDocument,
  NormalizedField,
  NormalizedFieldValue,
  NormalizedLineItem,
  logoutAuth,
  registerAuth,
  ValidationResult,
  ValidationRunResponse,
  ValidationRunSummary,
} from "./lib/api";

type StageStatus = "ok" | "check" | "warning" | "missing" | "problem";
type AuthMode = "login" | "register";
type IconName =
  | "shield"
  | "home"
  | "shipment"
  | "document"
  | "rules"
  | "alerts"
  | "reports"
  | "reference"
  | "settings"
  | "search"
  | "bell"
  | "help"
  | "share"
  | "export"
  | "upload"
  | "chevronRight"
  | "chevronDown"
  | "invoice"
  | "packing"
  | "coa"
  | "bill"
  | "addendum"
  | "payment"
  | "checkCircle"
  | "warningCircle"
  | "minusCircle"
  | "problemCircle"
  | "refresh";

type ShipmentStage = {
  id: string;
  label: string;
  document: NormalizedDocument | null;
  documentTypes: string[];
  footerLabel: string;
  hint: string;
  icon: IconName;
  informationalResults: ValidationResult[];
  issueCount: number;
  message: string;
  results: ValidationResult[];
  searchText: string;
  status: StageStatus;
  step: number;
  totalRules: number;
  triggeredCount: number;
  visibleResults: ValidationResult[];
};

type ShipmentMeta = {
  exporter: string;
  importer: string;
  incoterms: string;
  mode: string;
  route: string;
};

type ActivityItem = {
  actor: string;
  message: string;
  timestamp: string | null;
  tone: StageStatus | "neutral";
};

type WorkspaceStateTone = "neutral" | "info" | "warning" | "problem";

type ExtractionFieldView = {
  confidence: number | null;
  derived: boolean;
  key: string;
  label: string;
  normalizedValue: string | null;
  pageNo: number | null;
  primaryValue: string;
  rawValue: string | null;
  snippet: string | null;
  structured: boolean;
};

const EXTRACTION_FIELD_PRIORITY: Record<string, number> = {
  seller_name: 100,
  buyer_name: 99,
  manufacturer_name: 98,
  shipper_name: 97,
  contract_no: 96,
  contract_date: 95,
  addendum_no: 94,
  addendum_date: 93,
  invoice_no: 92,
  invoice_date: 91,
  incoterms: 90,
  payment_terms: 89,
  total_amount: 88,
  container_no: 87,
  gross_weight_kg: 86,
  net_weight_kg: 85,
  packages_quantity: 84,
};

type ExtractionLineItemView = {
  fields: ExtractionFieldView[];
  label: string;
};

type ShipmentNotice = {
  id: string;
  body: string;
  title: string;
};

const NAV_ITEMS: Array<{ icon: IconName; label: string; badge?: string; active?: boolean }> = [
  { icon: "home", label: "Dashboard" },
  { icon: "shipment", label: "Shipments", active: true },
  { icon: "document", label: "Documents" },
  { icon: "rules", label: "Rules" },
  { icon: "alerts", label: "Alerts", badge: "3" },
  { icon: "reports", label: "Reports" },
  { icon: "reference", label: "Reference Data" },
  { icon: "settings", label: "Settings" },
];

const STAGE_DEFINITIONS: Array<{ documentTypes: string[]; icon: IconName; id: string; label: string }> = [
  { id: "addendum", label: "Addendum", icon: "addendum", documentTypes: ["addendum"] },
  { id: "invoice", label: "Invoice", icon: "invoice", documentTypes: ["invoice", "commercial_invoice"] },
  { id: "packing-list", label: "Packing List", icon: "packing", documentTypes: ["packing_list"] },
  { id: "certificate-of-analysis", label: "Certificate of Analysis", icon: "coa", documentTypes: ["coa", "certificate_of_analysis"] },
  { id: "bill-of-lading", label: "Bill of Lading", icon: "bill", documentTypes: ["bl", "bill_of_lading", "hbl", "mbl"] },
  { id: "payment-confirmation", label: "Payment Confirmation", icon: "payment", documentTypes: ["payment_confirmation"] },
];

const CONTRACT_OPTIONAL_SKIP_RULES = new Set(["R003", "R005"]);
const INCOTERMS_INFORMATIONAL_SKIP_RULES = new Set(["R006"]);
const REDUNDANT_COA_SKIP_RULES = new Set(["R023"]);
const BL_PACKING_INFORMATIONAL_SKIP_RULES = new Set(["R025"]);
const PAYMENT_OPTIONAL_WARNING_RULES = new Set(["R018"]);
const AUTH_TOKEN_STORAGE_KEY = "dynno_customs_auth_token";

function getStoredAuthToken(): string | null {
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

function setStoredAuthToken(token: string) {
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

function clearStoredAuthToken() {
  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
}

function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

function getUserInitials(user: AuthUser | null): string {
  if (!user) {
    return "SA";
  }

  const parts = user.full_name
    .split(/\s+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length === 0) {
    return "SA";
  }

  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function formatUserRole(role: string): string {
  return role === "admin" ? "Workspace admin" : role === "operator" ? "Customs operator" : formatFieldLabel(role);
}

function getDefaultAuthMode(bootstrap: AuthBootstrapStatusResponse | null): AuthMode {
  if (!bootstrap) {
    return "login";
  }
  return bootstrap.has_users ? "login" : "register";
}

function AppIcon({ name, ...props }: SVGProps<SVGSVGElement> & { name: IconName }) {
  const common = {
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.8,
  };

  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" {...props}>
      {name === "shield" ? (
        <>
          <path {...common} d="M12 3 5 6v6c0 5 3.2 8 7 9 3.8-1 7-4 7-9V6z" />
          <path {...common} d="m9.5 12 1.7 1.8 3.3-3.6" />
        </>
      ) : null}
      {name === "home" ? (
        <>
          <path {...common} d="M4 11.5 12 5l8 6.5" />
          <path {...common} d="M6.5 10.5V19h11v-8.5" />
        </>
      ) : null}
      {name === "shipment" ? (
        <>
          <path {...common} d="M4 8.5h16v10H4z" />
          <path {...common} d="M8 8.5V6h8v2.5" />
          <path {...common} d="M4 12h16" />
        </>
      ) : null}
      {name === "document" || name === "invoice" ? (
        <>
          <path {...common} d="M7 3.5h7l4 4V20H7z" />
          <path {...common} d="M14 3.5V8h4" />
          <path {...common} d="M10 12h5M10 15.5h5" />
        </>
      ) : null}
      {name === "rules" ? (
        <>
          <path {...common} d="M6 6h12M6 12h12M6 18h12" />
          <circle {...common} cx="9" cy="6" r="1.5" />
          <circle {...common} cx="15" cy="12" r="1.5" />
          <circle {...common} cx="11" cy="18" r="1.5" />
        </>
      ) : null}
      {name === "alerts" ? (
        <>
          <path {...common} d="M12 4a4 4 0 0 0-4 4v2.6L6.3 14v1h11.4v-1L16 10.6V8a4 4 0 0 0-4-4Z" />
          <path {...common} d="M10 18a2 2 0 0 0 4 0" />
        </>
      ) : null}
      {name === "reports" ? (
        <>
          <circle {...common} cx="12" cy="12" r="8" />
          <path {...common} d="M12 7v5l3.5 2" />
        </>
      ) : null}
      {name === "reference" ? (
        <>
          <ellipse {...common} cx="12" cy="6" rx="6.5" ry="2.5" />
          <path {...common} d="M5.5 6v6c0 1.4 2.9 2.5 6.5 2.5s6.5-1.1 6.5-2.5V6" />
          <path {...common} d="M5.5 12v6c0 1.4 2.9 2.5 6.5 2.5s6.5-1.1 6.5-2.5v-6" />
        </>
      ) : null}
      {name === "settings" ? (
        <>
          <circle {...common} cx="12" cy="12" r="3.25" />
          <path {...common} d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.5-2.3.7a7.2 7.2 0 0 0-1.7-1L14.5 3h-5l-.5 2.7a7.2 7.2 0 0 0-1.7 1L5 6 3 9.5 5 11a7 7 0 0 0 0 2l-2 1.5L5 18l2.3-.7a7.2 7.2 0 0 0 1.7 1l.5 2.7h5l.5-2.7a7.2 7.2 0 0 0 1.7-1l2.3.7 2-3.5-2-1.5c.1-.3.1-.7.1-1Z" />
        </>
      ) : null}
      {name === "search" ? (
        <>
          <circle {...common} cx="11" cy="11" r="6" />
          <path {...common} d="m20 20-4.2-4.2" />
        </>
      ) : null}
      {name === "bell" ? (
        <>
          <path {...common} d="M7.5 10.5A4.5 4.5 0 0 1 12 6a4.5 4.5 0 0 1 4.5 4.5v2L18 15v1H6v-1l1.5-2.5z" />
          <path {...common} d="M10.5 18a1.5 1.5 0 0 0 3 0" />
        </>
      ) : null}
      {name === "help" ? (
        <>
          <circle {...common} cx="12" cy="12" r="9" />
          <path {...common} d="M9.8 9.5a2.4 2.4 0 1 1 4.4 1.4c-.7.8-1.7 1.3-1.7 2.6" />
          <path {...common} d="M12 17h.01" />
        </>
      ) : null}
      {name === "share" ? (
        <>
          <circle {...common} cx="18" cy="5.5" r="2" />
          <circle {...common} cx="6" cy="12" r="2" />
          <circle {...common} cx="18" cy="18.5" r="2" />
          <path {...common} d="m7.8 11 8.1-4.2M7.8 13l8.1 4.2" />
        </>
      ) : null}
      {name === "export" ? (
        <>
          <path {...common} d="M12 4v10" />
          <path {...common} d="m8.5 10.5 3.5 3.5 3.5-3.5" />
          <path {...common} d="M5 18.5h14" />
        </>
      ) : null}
      {name === "upload" ? (
        <>
          <path {...common} d="M12 19V8" />
          <path {...common} d="m8.5 11.5 3.5-3.5 3.5 3.5" />
          <path {...common} d="M5 20h14" />
        </>
      ) : null}
      {name === "chevronRight" ? <path {...common} d="m9 6 6 6-6 6" /> : null}
      {name === "chevronDown" ? <path {...common} d="m6 9 6 6 6-6" /> : null}
      {name === "packing" ? (
        <>
          <path {...common} d="m12 3 7 4-7 4-7-4z" />
          <path {...common} d="M5 7v8l7 4 7-4V7" />
          <path {...common} d="M12 11v8" />
        </>
      ) : null}
      {name === "coa" ? (
        <>
          <path {...common} d="M10 4h4" />
          <path {...common} d="M10.8 4v6l-4.6 7.4A1 1 0 0 0 7.1 19h9.8a1 1 0 0 0 .9-1.6L13.2 10V4" />
          <path {...common} d="M9 14h6" />
        </>
      ) : null}
      {name === "bill" ? (
        <>
          <path {...common} d="M4 15.5h14l2-2.5H7z" />
          <path {...common} d="M7 13V9.5l3-2h4l3 2v3.5" />
          <path {...common} d="M4 18.5h16" />
          <path {...common} d="M8 18.5a1.5 1.5 0 0 0 3 0m2 0a1.5 1.5 0 0 0 3 0" />
        </>
      ) : null}
      {name === "addendum" ? (
        <>
          <path {...common} d="M8.5 11.5 13 7a3 3 0 1 1 4.2 4.2l-5.1 5.1a4 4 0 0 1-5.6-5.6l5.6-5.6" />
        </>
      ) : null}
      {name === "payment" ? (
        <>
          <path {...common} d="M12 3v18" />
          <path {...common} d="M15.5 6.5a3.5 3.5 0 0 0-3.5-2 3.2 3.2 0 0 0-3.5 3c0 1.7 1.3 2.7 3.5 3.1 2.1.4 3.5 1.2 3.5 3.1a3.2 3.2 0 0 1-3.5 3 3.7 3.7 0 0 1-4-2.2" />
        </>
      ) : null}
      {name === "checkCircle" ? (
        <>
          <circle {...common} cx="12" cy="12" r="8" />
          <path {...common} d="m8.8 12.2 2.1 2.2 4.3-4.5" />
        </>
      ) : null}
      {name === "warningCircle" ? (
        <>
          <circle {...common} cx="12" cy="12" r="8" />
          <path {...common} d="M12 8v5" />
          <path {...common} d="M12 16h.01" />
        </>
      ) : null}
      {name === "minusCircle" ? (
        <>
          <circle {...common} cx="12" cy="12" r="8" />
          <path {...common} d="M8.5 12h7" />
        </>
      ) : null}
      {name === "problemCircle" ? (
        <>
          <circle {...common} cx="12" cy="12" r="8" />
          <path {...common} d="m9 9 6 6M15 9l-6 6" />
        </>
      ) : null}
      {name === "refresh" ? (
        <>
          <path {...common} d="M19 8a7 7 0 0 0-12.6-2L4 8.5" />
          <path {...common} d="M5 5v3.5h3.5" />
          <path {...common} d="M5 16a7 7 0 0 0 12.6 2L20 15.5" />
          <path {...common} d="M19 19v-3.5h-3.5" />
        </>
      ) : null}
    </svg>
  );
}

function normalizeDocType(value: string): string {
  return value.toLowerCase().replace(/[\s-]+/g, "_");
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

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatTime(value: string | null | undefined): string {
  if (!value) {
    return "--:--";
  }

  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatFieldLabel(value: string): string {
  return value
    .replace(/\[(\d+)\]/g, " $1 ")
    .split(/[._]/)
    .filter(Boolean)
    .map((part) => {
      if (part.length <= 3) {
        return part.toUpperCase();
      }

      return part.charAt(0).toUpperCase() + part.slice(1);
    })
    .join(" ");
}

function formatDocumentType(value: string): string {
  return normalizeDocType(value)
    .split("_")
    .filter(Boolean)
    .map((part) => (part.length <= 3 ? part.toUpperCase() : part.charAt(0).toUpperCase() + part.slice(1)))
    .join(" ");
}

function formatShipmentCode(packId: string): string {
  return `SHP-${packId.slice(0, 8).toUpperCase()}`;
}

function hasMeaningfulValue(value: unknown): boolean {
  if (value === null || value === undefined) {
    return false;
  }
  if (typeof value === "string") {
    return value.trim().length > 0;
  }
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  if (typeof value === "object") {
    return Object.keys(value as Record<string, unknown>).length > 0;
  }
  return true;
}

function formatValue(value: unknown): string {
  if (!hasMeaningfulValue(value)) {
    return "—";
  }

  if (typeof value === "string") {
    return value.trim();
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map((item) => formatValue(item)).join(", ");
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStructuredField(value: unknown): value is NormalizedField {
  if (!isRecord(value)) {
    return false;
  }

  return [
    "value",
    "raw_value",
    "normalized_value",
    "confidence",
    "text_snippet",
    "derived",
    "page_no",
    "unit",
  ].some((key) => key in value);
}

function formatMeasuredValue(value: unknown, unit?: string | null): string {
  const formatted = formatValue(value);
  if (formatted === "—" || !unit) {
    return formatted;
  }

  if (formatted.toLowerCase().includes(String(unit).toLowerCase())) {
    return formatted;
  }

  return `${formatted} ${unit}`;
}

function getFieldDisplayValue(value: NormalizedFieldValue | undefined): string | null {
  if (!hasMeaningfulValue(value)) {
    return null;
  }

  if (isStructuredField(value)) {
    return formatMeasuredValue(
      value.value ?? value.normalized_value ?? value.raw_value,
      typeof value.unit === "string" ? value.unit : null,
    );
  }

  return formatValue(value);
}

function getFieldStringValue(value: NormalizedFieldValue | undefined): string | null {
  const displayValue = getFieldDisplayValue(value);
  if (!displayValue || displayValue === "—") {
    return null;
  }

  return displayValue;
}

function buildExtractionFieldView(key: string, value: NormalizedFieldValue): ExtractionFieldView {
  if (isStructuredField(value)) {
    return {
      confidence: typeof value.confidence === "number" ? value.confidence : null,
      derived: value.derived === true,
      key,
      label: formatFieldLabel(key),
      normalizedValue: hasMeaningfulValue(value.normalized_value)
        ? formatMeasuredValue(value.normalized_value, typeof value.unit === "string" ? value.unit : null)
        : null,
      pageNo: typeof value.page_no === "number" ? value.page_no : null,
      primaryValue: formatMeasuredValue(
        value.value ?? value.normalized_value ?? value.raw_value,
        typeof value.unit === "string" ? value.unit : null,
      ),
      rawValue: hasMeaningfulValue(value.raw_value) ? formatValue(value.raw_value) : null,
      snippet: typeof value.text_snippet === "string" && value.text_snippet.trim().length > 0 ? value.text_snippet.trim() : null,
      structured: true,
    };
  }

  return {
    confidence: null,
    derived: false,
    key,
    label: formatFieldLabel(key),
    normalizedValue: null,
    pageNo: null,
    primaryValue: formatValue(value),
    rawValue: null,
    snippet: null,
    structured: false,
  };
}

function getExtractionFieldPriority(key: string): number {
  return EXTRACTION_FIELD_PRIORITY[key] ?? 0;
}

function buildLineItemLabel(item: NormalizedLineItem, index: number): string {
  const lineNoValue = isRecord(item) ? item.line_no : null;
  const resolvedLineNo =
    typeof lineNoValue === "number" || typeof lineNoValue === "string" ? formatValue(lineNoValue) : String(index + 1);

  return `Line item ${resolvedLineNo}`;
}

function getConfidenceTone(confidence: number | null): "high" | "medium" | "low" | "unknown" {
  if (confidence === null) {
    return "unknown";
  }
  if (confidence >= 0.85) {
    return "high";
  }
  if (confidence >= 0.65) {
    return "medium";
  }
  return "low";
}

function getDocumentField(document: NormalizedDocument | null | undefined, keys: string[]): string | null {
  if (!document) {
    return null;
  }

  for (const key of keys) {
    const value = getFieldStringValue(document.fields[key]);
    if (value) {
      return value;
    }
  }

  return null;
}

function buildShipmentMeta(run: ValidationRunResponse | null): ShipmentMeta {
  const documents = run?.documents ?? [];
  const findDocument = (documentTypes: string[]) =>
    documents.find((item) => documentTypes.includes(normalizeDocType(item.document_type))) ?? null;

  const invoice = findDocument(["invoice", "commercial_invoice"]);
  const addendum = findDocument(["addendum"]);
  const bill = findDocument(["bl", "bill_of_lading", "hbl", "mbl"]);

  const exporter =
    getDocumentField(invoice, ["seller_name", "exporter_name", "shipper_name"]) ??
    getDocumentField(addendum, ["seller_name"]) ??
    "Not captured yet";
  const importer =
    getDocumentField(invoice, ["buyer_name", "importer_name", "consignee_name"]) ??
    getDocumentField(addendum, ["buyer_name"]) ??
    "Not captured yet";
  const incoterms =
    getDocumentField(invoice, ["incoterms"]) ??
    getDocumentField(addendum, ["incoterms"]) ??
    "Not captured yet";
  const originPort = getDocumentField(bill, ["port_of_loading", "place_of_receipt"]);
  const destinationPort = getDocumentField(bill, ["port_of_discharge", "place_of_delivery"]);
  const route =
    originPort && destinationPort
      ? `${originPort} → ${destinationPort}`
      : originPort ?? destinationPort ?? "Route not captured yet";
  const mode = bill ? "Ocean Freight" : "Validation Workflow";

  return {
    exporter,
    importer,
    incoterms,
    mode,
    route,
  };
}

function matchesStageDocument(stageDocumentTypes: string[], value: string): boolean {
  const normalizedValue = normalizeDocType(value);
  return stageDocumentTypes.includes(normalizedValue);
}

function hasDocumentType(run: ValidationRunResponse, documentType: string): boolean {
  return run.documents.some((item) => normalizeDocType(item.document_type) === documentType);
}

function isContractInformationalSkip(run: ValidationRunResponse, result: ValidationResult): boolean {
  return result.status === "skipped" && !hasDocumentType(run, "contract") && CONTRACT_OPTIONAL_SKIP_RULES.has(result.rule_code);
}

function isPaymentInformationalWarning(run: ValidationRunResponse, result: ValidationResult): boolean {
  return (
    result.status === "failed" &&
    result.severity === "warning" &&
    !hasDocumentType(run, "payment_confirmation") &&
    PAYMENT_OPTIONAL_WARNING_RULES.has(result.rule_code)
  );
}

function isIncotermsInformationalSkip(result: ValidationResult): boolean {
  return result.status === "skipped" && INCOTERMS_INFORMATIONAL_SKIP_RULES.has(result.rule_code);
}

function isRedundantCoaInformationalSkip(result: ValidationResult): boolean {
  return result.status === "skipped" && REDUNDANT_COA_SKIP_RULES.has(result.rule_code);
}

function isBlPackingInformationalSkip(result: ValidationResult): boolean {
  return result.status === "skipped" && BL_PACKING_INFORMATIONAL_SKIP_RULES.has(result.rule_code);
}

function isInformationalShipmentResult(run: ValidationRunResponse, result: ValidationResult): boolean {
  return (
    isContractInformationalSkip(run, result) ||
    isPaymentInformationalWarning(run, result) ||
    isIncotermsInformationalSkip(result) ||
    isRedundantCoaInformationalSkip(result) ||
    isBlPackingInformationalSkip(result)
  );
}

function isInformationalOnlyStage(stage: ShipmentStage): boolean {
  return stage.visibleResults.length === 0 && stage.informationalResults.length > 0;
}

function isOptionalPaymentConfirmationStage(stage: ShipmentStage): boolean {
  return stage.id === "payment-confirmation" && !stage.document && isInformationalOnlyStage(stage);
}

function isContractInformationalStage(stage: ShipmentStage): boolean {
  return stage.informationalResults.some((item) => CONTRACT_OPTIONAL_SKIP_RULES.has(item.rule_code));
}

function isIncotermsInformationalStage(stage: ShipmentStage): boolean {
  return stage.informationalResults.some((item) => INCOTERMS_INFORMATIONAL_SKIP_RULES.has(item.rule_code));
}

function isBlPackingInformationalStage(stage: ShipmentStage): boolean {
  return stage.informationalResults.some((item) => BL_PACKING_INFORMATIONAL_SKIP_RULES.has(item.rule_code));
}

function buildStage(run: ValidationRunResponse, stageDefinition: (typeof STAGE_DEFINITIONS)[number], step: number): ShipmentStage {
  const document =
    run.documents.find((item) => matchesStageDocument(stageDefinition.documentTypes, item.document_type)) ?? null;

  const results = run.report.results.filter((item) =>
    item.documents.some((documentType) => matchesStageDocument(stageDefinition.documentTypes, documentType)),
  );
  const nonPassedResults = results.filter((item) => item.status !== "passed");
  const informationalResults = nonPassedResults.filter((item) => isInformationalShipmentResult(run, item));
  const visibleResults = nonPassedResults.filter((item) => !isInformationalShipmentResult(run, item));
  const actionableResults = visibleResults.filter((item) => item.status !== "skipped");
  const skippedCount = visibleResults.length - actionableResults.length;
  const warningFailures = actionableResults.filter((item) => item.status === "failed" && item.severity === "warning");
  const hasErrorFailure = actionableResults.some((item) => item.status === "failed" && item.severity === "error");
  const hasNeedsReview = actionableResults.some((item) => item.status === "needs_review");
  const informationalOnly = visibleResults.length === 0 && informationalResults.length > 0;

  let status: StageStatus;
  if (!document) {
    status = "missing";
  } else if (hasErrorFailure) {
    status = "problem";
  } else if (warningFailures.length > 1 || (warningFailures.length === 1 && skippedCount === 0 && actionableResults.length === 1)) {
    status = "warning";
  } else if (actionableResults.length > 0 || hasNeedsReview || skippedCount > 0) {
    status = "check";
  } else {
    status = "ok";
  }

  const issueCount = actionableResults.length;
  const messageByStatus: Record<StageStatus, string> = {
    check:
      issueCount > 0
        ? issueCount === 1
          ? "1 issue to review"
          : `${issueCount} issues to review`
        : skippedCount === 1
          ? "1 check skipped"
          : `${skippedCount} checks skipped`,
    missing: "Document not uploaded",
    ok: "All key checks passed",
    problem: issueCount === 1 ? "1 blocking issue found" : `${issueCount} blocking issues found`,
    warning: issueCount === 1 ? "1 issue found" : `${issueCount} issues found`,
  };

  const message =
    status === "missing" && informationalOnly && stageDefinition.id === "payment-confirmation"
      ? "Optional upload"
      : messageByStatus[status];
  const hint = document
    ? `${document.source_file_name} · ${Object.keys(document.fields ?? {}).length} extracted fields`
    : status === "missing" && informationalOnly && stageDefinition.id === "payment-confirmation"
      ? "Upload if available to complete prepayment evidence for this shipment"
      : "Validation chain cannot continue without this document";

  return {
    id: stageDefinition.id,
    label: stageDefinition.label,
    document,
    documentTypes: stageDefinition.documentTypes,
    footerLabel: results.length === 1 ? "1 rule evaluated" : `${results.length} rules evaluated`,
    hint,
    icon: stageDefinition.icon,
    informationalResults,
    issueCount,
    message,
    results,
    searchText: [
      stageDefinition.label,
      document?.source_file_name ?? "",
      hint,
      ...results.map((item) => `${item.rule_code} ${item.message}`),
    ]
      .join(" ")
      .toLowerCase(),
    status,
    step,
    totalRules: results.length,
    triggeredCount: results.length,
    visibleResults,
  };
}

function getDefaultStageId(stages: ShipmentStage[]): string | null {
  const primaryStages = stages.filter((stage) => !isOptionalPaymentConfirmationStage(stage));
  const orderedStages = primaryStages.length > 0 ? primaryStages : stages;

  return (
    orderedStages.find((stage) => stage.status === "problem")?.id ??
    orderedStages.find((stage) => stage.status === "warning")?.id ??
    orderedStages.find((stage) => stage.status === "check")?.id ??
    orderedStages.find((stage) => stage.status === "missing")?.id ??
    orderedStages[0]?.id ??
    null
  );
}

function getStageToneLabel(status: StageStatus): string {
  switch (status) {
    case "ok":
      return "OK";
    case "check":
      return "CHECK";
    case "warning":
      return "WARNING";
    case "missing":
      return "MISSING";
    case "problem":
      return "PROBLEM";
  }
}

function getStageStatusIcon(status: StageStatus): IconName {
  switch (status) {
    case "ok":
      return "checkCircle";
    case "check":
    case "warning":
      return "warningCircle";
    case "missing":
      return "minusCircle";
    case "problem":
      return "problemCircle";
  }
}

function getRunStatusLabel(status: string): string {
  if (status === "validated") {
    return "Validated";
  }
  if (status === "needs_review") {
    return "In Progress";
  }
  if (status === "failed") {
    return "Blocked";
  }
  return formatFieldLabel(status);
}

function getStageRecommendedAction(stage: ShipmentStage): string {
  if (isOptionalPaymentConfirmationStage(stage)) {
    return "Upload the payment confirmation if it is available. The shipment can still be reviewed without this proof-of-payment file.";
  }

  if (stage.status === "missing") {
    return `Upload the ${stage.label.toLowerCase()} to continue the validation chain.`;
  }

  const topIssue = stage.visibleResults[0];
  if (!topIssue) {
    if (isContractInformationalStage(stage)) {
      return "No document-level action is needed here. Contract-dependent checks were skipped because the master contract file is not included in this pack.";
    }
    if (isIncotermsInformationalStage(stage)) {
      return "No document-level action is needed here. Incoterms comparison was skipped because the required addendum/invoice pair was not fully extracted.";
    }
    return "Continue to the next document or export the current report.";
  }

  if (topIssue.status === "skipped") {
    return `Provide the missing inputs for ${topIssue.rule_code} and rerun validation.`;
  }

  if (topIssue.severity === "error") {
    return `Correct the source document values for ${topIssue.rule_code} before export.`;
  }

  return `Review ${topIssue.rule_code} with the source snippet and confirm the final document values.`;
}

function buildShipmentNotices(run: ValidationRunResponse | null): ShipmentNotice[] {
  if (!run) {
    return [];
  }

  const notices: ShipmentNotice[] = [];
  const contractSkips = run.report.results.filter((item) => isContractInformationalSkip(run, item));
  if (contractSkips.length > 0) {
    const ruleCodes = contractSkips.map((item) => item.rule_code).join(", ");
    notices.push({
      id: "contract-missing",
      title: "Contract file is not included in this pack",
      body: `Contract-dependent checks were skipped (${ruleCodes}). Addendum and invoice values were extracted successfully, but they were not compared against a separate master contract.`,
    });
  }

  const paymentWarnings = run.report.results.filter((item) => isPaymentInformationalWarning(run, item));
  if (paymentWarnings.length > 0) {
    notices.push({
      id: "payment-confirmation-missing",
      title: "Payment confirmation is not uploaded",
      body: "The shipment can still be reviewed without this file. Upload the payment confirmation later if you want to attach proof of prepayment for the broker or audit trail.",
    });
  }

  const incotermsSkips = run.report.results.filter((item) => isIncotermsInformationalSkip(item));
  if (incotermsSkips.length > 0) {
    notices.push({
      id: "incoterms-partial",
      title: "Incoterms comparison was skipped",
      body: "Incoterms are required in addendum and invoice. Optional documents stay green when this field is absent, and cross-document comparison resumes once both required values are extracted.",
    });
  }

  const blPackingSkips = run.report.results.filter((item) => isBlPackingInformationalSkip(item));
  if (blPackingSkips.length > 0) {
    const ruleCodes = blPackingSkips.map((item) => item.rule_code).join(", ");
    notices.push({
      id: "bl-packing-partial",
      title: "BL and packing-list comparison is partial",
      body: `Some BL vs packing-list checks were skipped (${ruleCodes}) because package quantity was not extracted from both documents. Container-number gaps remain visible document issues.`,
    });
  }

  return notices;
}

function buildActivityTimeline(stages: ShipmentStage[], run: ValidationRunResponse | null): ActivityItem[] {
  const timestamp = run?.updated_at ?? run?.created_at ?? null;

  return stages
    .filter((stage) => stage.document || stage.status === "missing")
    .map<ActivityItem>((stage) => {
      if (isOptionalPaymentConfirmationStage(stage)) {
        return {
          actor: "System",
          message: `${stage.label} not uploaded yet (optional)`,
          timestamp,
          tone: "neutral",
        };
      }

      if (stage.status === "missing") {
        return {
          actor: "System",
          message: `${stage.label} is missing`,
          timestamp,
          tone: "missing",
        };
      }

      if (stage.status === "ok") {
        return {
          actor: "System",
          message: `${stage.label} validated`,
          timestamp,
          tone: "ok",
        };
      }

      return {
        actor: "System",
        message: `${stage.label} needs attention`,
        timestamp,
        tone: stage.status,
      };
    })
    .slice(0, 4);
}

function StageCard({
  active,
  onSelect,
  stage,
}: {
  active: boolean;
  onSelect: () => void;
  stage: ShipmentStage;
}) {
  return (
    <button
      className={active ? "stage-card stage-card--active" : `stage-card stage-card--${stage.status}`}
      type="button"
      onClick={onSelect}
    >
      <span className="stage-card__step">{stage.step}</span>
      <span className={`stage-card__icon stage-card__icon--${stage.status}`}>
        <AppIcon name={stage.icon} className="app-icon" />
      </span>
      <strong className="stage-card__title">{stage.label}</strong>
      <span className={`stage-tag stage-tag--${stage.status}`}>{getStageToneLabel(stage.status)}</span>
      <span className="stage-card__message">{stage.message}</span>
      <span className="stage-card__hint">{stage.hint}</span>
      <span className="stage-card__footer">
        <span>{stage.footerLabel}</span>
        <AppIcon
          name={active && stage.issueCount > 0 ? "chevronDown" : "chevronRight"}
          className="app-icon app-icon--muted"
        />
      </span>
    </button>
  );
}

function HistoryList({
  activeRunId,
  isLoading,
  items,
  onOpenRun,
}: {
  activeRunId?: string;
  isLoading: boolean;
  items: ValidationRunSummary[];
  onOpenRun: (packId: string) => void;
}) {
  if (isLoading) {
    return <p className="sidebar-note">Loading shipments…</p>;
  }

  if (items.length === 0) {
    return <p className="sidebar-note">No validated shipments yet.</p>;
  }

  return (
    <div className="history-stack">
      {items.slice(0, 5).map((item) => (
        <button
          key={item.run_id}
          className={item.run_id === activeRunId ? "history-card history-card--active" : "history-card"}
          type="button"
          onClick={() => onOpenRun(item.pack_id)}
        >
          <span className="history-card__head">
            <strong>{formatShipmentCode(item.pack_id)}</strong>
            <span className={`mini-status mini-status--${item.status}`}>{getRunStatusLabel(item.status)}</span>
          </span>
          <span className="history-card__meta">{item.document_count} docs · {item.summary.total_rules} rules</span>
          <span className="history-card__time">{formatDateTime(item.generated_at)}</span>
        </button>
      ))}
    </div>
  );
}

function WorkspaceStatePanel({
  actionLabel,
  icon,
  message,
  onAction,
  title,
  tone,
}: {
  actionLabel?: string;
  icon: IconName;
  message: string;
  onAction?: () => void;
  title: string;
  tone: WorkspaceStateTone;
}) {
  return (
    <section className={`workspace-state workspace-state--${tone}`}>
      <div className={`workspace-state__icon workspace-state__icon--${tone}`}>
        <AppIcon name={icon} className="app-icon" />
      </div>
      <div className="workspace-state__copy">
        <strong>{title}</strong>
        <p>{message}</p>
      </div>
      {actionLabel && onAction ? (
        <button className="ghost-button workspace-state__action" type="button" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </section>
  );
}

export default function App() {
  const [authBootstrap, setAuthBootstrap] = useState<AuthBootstrapStatusResponse | null>(null);
  const [authEmail, setAuthEmail] = useState("");
  const [authFullName, setAuthFullName] = useState("");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authPassword, setAuthPassword] = useState("");
  const [authToken, setAuthToken] = useState<string | null>(() => getStoredAuthToken());
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [history, setHistory] = useState<ValidationRunSummary[]>([]);
  const [isAuthSubmitting, setIsAuthSubmitting] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isOpeningRun, setIsOpeningRun] = useState(false);
  const [isSessionRestoring, setIsSessionRestoring] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [run, setRun] = useState<ValidationRunResponse | null>(null);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeStageId, setActiveStageId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const deferredSearchQuery = useDeferredValue(searchQuery.trim().toLowerCase());

  useEffect(() => {
    let active = true;

    async function bootstrapWorkspace() {
      setIsInitialLoading(true);
      setIsSessionRestoring(true);
      try {
        const [healthResponse, schemaResponse, bootstrapResponse] = await Promise.all([
          fetchHealth(),
          fetchSchemaIndex(),
          fetchAuthBootstrapStatus(),
        ]);
        if (!active) {
          return;
        }
        setHealth(healthResponse);
        setSchemas(schemaResponse.schemas);
        setAuthBootstrap(bootstrapResponse);
        setAuthMode(getDefaultAuthMode(bootstrapResponse));

        if (!authToken) {
          setAuthUser(null);
          return;
        }

        const currentUser = await fetchCurrentUser(authToken);
        if (!active) {
          return;
        }
        setAuthUser(currentUser);
      } catch (err) {
        if (active && isApiError(err) && err.status === 401) {
          clearStoredAuthToken();
          setAuthToken(null);
          setAuthUser(null);
          setError("Session expired. Sign in again.");
          return;
        }
        if (active) {
          setError(err instanceof Error ? err.message : "Unable to connect to API.");
        }
      } finally {
        if (active) {
          setIsInitialLoading(false);
          setIsSessionRestoring(false);
        }
      }
    }

    void bootstrapWorkspace();

    return () => {
      active = false;
    };
  }, [authToken]);

  useEffect(() => {
    let active = true;

    async function loadHistory() {
      if (!authToken || !authUser) {
        setHistory([]);
        setRun(null);
        setIsHistoryLoading(false);
        return;
      }

      setIsHistoryLoading(true);
      try {
        const response = await fetchValidationRuns(authToken);
        if (!active) {
          return;
        }
        setHistory(response.items);
      } catch (err) {
        if (active && isApiError(err) && err.status === 401) {
          clearStoredAuthToken();
          setAuthToken(null);
          setAuthUser(null);
          setHistory([]);
          setRun(null);
          setError("Session expired. Sign in again.");
          return;
        }
        if (active) {
          setError(err instanceof Error ? err.message : "Unable to load shipment history.");
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
  }, [authToken, authUser]);

  useEffect(() => {
    if (!run && history.length > 0) {
      void handleOpenRun(history[0].pack_id);
    }
  }, [history, run]);

  const allStages = useMemo(
    () => (run ? STAGE_DEFINITIONS.map((stageDefinition, index) => buildStage(run, stageDefinition, index + 1)) : []),
    [run],
  );

  const visibleStages = useMemo(() => {
    if (!deferredSearchQuery) {
      return allStages;
    }

    return allStages.filter((stage) => stage.searchText.includes(deferredSearchQuery));
  }, [allStages, deferredSearchQuery]);

  useEffect(() => {
    if (visibleStages.length === 0) {
      setActiveStageId(null);
      return;
    }

    if (!activeStageId || !visibleStages.some((stage) => stage.id === activeStageId)) {
      setActiveStageId(getDefaultStageId(visibleStages));
    }
  }, [activeStageId, visibleStages]);

  const activeStage = useMemo(
    () => visibleStages.find((stage) => stage.id === activeStageId) ?? allStages.find((stage) => stage.id === activeStageId) ?? null,
    [activeStageId, allStages, visibleStages],
  );

  const shipmentMeta = useMemo(() => buildShipmentMeta(run), [run]);

  const stageSummary = useMemo(() => {
    const summaryStages = allStages.filter((stage) => !isOptionalPaymentConfirmationStage(stage));
    const okCount = summaryStages.filter((stage) => stage.status === "ok").length;
    const reviewCount = summaryStages.filter((stage) => stage.status === "check" || stage.status === "warning").length;
    const missingCount = summaryStages.filter((stage) => stage.status === "missing").length;
    const problemCount = summaryStages.filter((stage) => stage.status === "problem").length;
    const documentCount = allStages.filter((stage) => stage.document).length;
    const progressPercent =
      summaryStages.length > 0 ? Math.round(((okCount + reviewCount * 0.5) / summaryStages.length) * 100) : 0;

    return {
      documentCount,
      missingCount,
      okCount,
      problemCount,
      progressPercent,
      reviewCount,
    };
  }, [allStages]);

  const visibleAlerts = useMemo(() => {
    const alerts = run?.report.results.filter((item) => item.status !== "passed" && !isInformationalShipmentResult(run, item)) ?? [];
    if (!deferredSearchQuery) {
      return alerts.slice(0, 4);
    }

    return alerts
      .filter((item) => `${item.rule_code} ${item.message} ${item.documents.join(" ")}`.toLowerCase().includes(deferredSearchQuery))
      .slice(0, 4);
  }, [deferredSearchQuery, run]);

  const activityTimeline = useMemo(() => buildActivityTimeline(allStages, run), [allStages, run]);
  const shipmentNotices = useMemo(() => buildShipmentNotices(run), [run]);

  const actionableStages = allStages.filter((stage) => !isOptionalPaymentConfirmationStage(stage));
  const nextActionStage =
    actionableStages.find((stage) => stage.status === "problem") ??
    actionableStages.find((stage) => stage.status === "warning") ??
    actionableStages.find((stage) => stage.status === "check") ??
    actionableStages.find((stage) => stage.status === "missing") ??
    actionableStages[0] ??
    allStages[0] ??
    null;

  const selectedBytes = useMemo(() => files.reduce((total, file) => total + file.size, 0), [files]);
  const isAuthenticated = Boolean(authToken && authUser);
  const isWorkspaceBooting = isInitialLoading || isSessionRestoring || (isAuthenticated && (isHistoryLoading || isOpeningRun));
  const showAuthGate = !isWorkspaceBooting && !isAuthenticated;
  const showEmptyStartState = isAuthenticated && !run && !isWorkspaceBooting && !isSubmitting;
  const isBootstrapSetup = Boolean(authBootstrap && !authBootstrap.has_users);
  const isOpenSelfRegistration = Boolean(authBootstrap?.registration_open && authBootstrap.has_users);
  const authStatusLabel = isAuthenticated
    ? `${schemas.length} schemas loaded`
    : isBootstrapSetup
      ? "Bootstrap access open"
      : authBootstrap?.registration_open
        ? "Self-registration available"
        : "Sign in required";
  const authProfileLabel = authUser
    ? formatUserRole(authUser.role)
    : isBootstrapSetup
      ? "Bootstrap admin setup"
      : authBootstrap?.registration_open
        ? "Sign in or self-register"
        : "Sign in required";
  const authAccessLabel = isBootstrapSetup
    ? "Bootstrap admin setup"
    : authBootstrap?.registration_open
      ? "Sign in or self-register"
      : "Authenticated operators only";
  const authAsideTitle = isBootstrapSetup
    ? "Create the first admin account"
    : authBootstrap?.registration_open
      ? "Sign in or create an account"
      : "Sign in to continue";
  const authAsideCopy = isBootstrapSetup
    ? "The first account becomes the workspace admin and opens the internal validation pipeline on the project SQL database."
    : authBootstrap?.registration_open
      ? "Validation runs, document packs, OCR, and history are protected. Existing users can sign in, and new users can create an operator account for this internal workspace."
      : "Validation runs, document packs, OCR, and history are now available only after authentication.";
  const authRegistrationNote = isBootstrapSetup
    ? "Bootstrap window is open"
    : authBootstrap?.registration_open
      ? "Open self-registration is enabled"
      : "Open self-registration is disabled";
  const authFormEyebrow = authMode === "register" ? (isBootstrapSetup ? "Bootstrap admin" : "Create operator account") : "Secure sign in";
  const authFormTitle = authMode === "register" ? (isBootstrapSetup ? "Set up internal access" : "Create workspace access") : "Authenticate operator session";
  const authFormCopy = authMode === "register"
    ? isBootstrapSetup
      ? "Create the first internal admin for this workspace. After that, sign-in remains available and open self-registration can stay enabled or be closed by configuration."
      : "Create a new account for this internal workspace. Additional self-registered users are created as operators."
    : "Use the email and password stored in the local SQL-backed auth layer.";
  const authSubmitLabel = isAuthSubmitting
    ? "Authenticating..."
    : authMode === "register"
      ? isBootstrapSetup
        ? "Create admin account"
        : "Create operator account"
      : "Sign in";

  function handleClearSearch() {
    setSearchQuery("");
  }

  function resetAuthForm(nextMode: AuthMode) {
    setAuthMode(nextMode);
    setAuthEmail("");
    setAuthPassword("");
    setAuthFullName("");
  }

  function handleSessionExpired(message = "Session expired. Sign in again.") {
    clearStoredAuthToken();
    setAuthToken(null);
    setAuthUser(null);
    setHistory([]);
    setRun(null);
    setFiles([]);
    setActiveStageId(null);
    setError(message);
    resetAuthForm(getDefaultAuthMode(authBootstrap));
  }

  function handleRetryBootstrap() {
    window.location.reload();
  }

  async function handleAuthSubmit() {
    setIsAuthSubmitting(true);
    setError(null);

    try {
      const response =
        authMode === "register"
          ? await registerAuth({
              email: authEmail,
              password: authPassword,
              full_name: authFullName,
            })
          : await loginAuth({
              email: authEmail,
              password: authPassword,
            });

      let nextBootstrap = authBootstrap;
      try {
        nextBootstrap = await fetchAuthBootstrapStatus();
      } catch {
        // Keep the signed-in session even if the post-auth status refresh fails.
      }

      setStoredAuthToken(response.access_token);
      setAuthToken(response.access_token);
      setAuthUser(response.user);
      if (nextBootstrap) {
        setAuthBootstrap(nextBootstrap);
      }
      resetAuthForm(getDefaultAuthMode(nextBootstrap));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to complete authentication.");
    } finally {
      setIsAuthSubmitting(false);
    }
  }

  const activeFieldEntries = useMemo(
    () =>
      Object.entries(activeStage?.document?.fields ?? {})
        .filter(([, value]) => hasMeaningfulValue(value))
        .map(([key, value]) => buildExtractionFieldView(key, value))
        .sort((left, right) => {
          const structuredDelta = Number(right.structured) - Number(left.structured);
          if (structuredDelta !== 0) {
            return structuredDelta;
          }
          const priorityDelta = getExtractionFieldPriority(right.key) - getExtractionFieldPriority(left.key);
          if (priorityDelta !== 0) {
            return priorityDelta;
          }
          return left.label.localeCompare(right.label);
        }),
    [activeStage],
  );
  const activeLineItemEntries = useMemo(
    () =>
      (activeStage?.document?.line_items ?? []).map((item, index) => ({
        fields: Object.entries(item)
          .filter(([key, value]) => key !== "line_no" && hasMeaningfulValue(value))
          .map(([key, value]) => buildExtractionFieldView(key, value))
          .sort((left, right) => {
            const structuredDelta = Number(right.structured) - Number(left.structured);
            if (structuredDelta !== 0) {
              return structuredDelta;
            }
            const priorityDelta = getExtractionFieldPriority(right.key) - getExtractionFieldPriority(left.key);
            if (priorityDelta !== 0) {
              return priorityDelta;
            }
            return left.label.localeCompare(right.label);
          }),
        label: buildLineItemLabel(item, index),
      }))
      .filter((item) => item.fields.length > 0),
    [activeStage],
  );

  function handleFilesChange(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files ?? []));
    setError(null);
    event.target.value = "";
  }

  async function handleOpenRun(packId: string) {
    if (!authToken) {
      handleSessionExpired();
      return;
    }

    setError(null);
    setIsOpeningRun(true);
    try {
      const response = await fetchValidationRun(packId, authToken);
      setRun(response);
      const stages = STAGE_DEFINITIONS.map((stageDefinition, index) => buildStage(response, stageDefinition, index + 1));
      setActiveStageId(getDefaultStageId(stages));
    } catch (err) {
      if (isApiError(err) && err.status === 401) {
        handleSessionExpired();
        return;
      }
      setError(err instanceof Error ? err.message : "Unable to open shipment.");
    } finally {
      setIsOpeningRun(false);
    }
  }

  async function handleRunValidation() {
    if (!authToken) {
      handleSessionExpired();
      return;
    }

    if (files.length === 0) {
      setError("Select shipment documents before starting validation.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await createValidationRun(files, authToken);
      setRun(response);
      setFiles([]);
      const stages = STAGE_DEFINITIONS.map((stageDefinition, index) => buildStage(response, stageDefinition, index + 1));
      setActiveStageId(getDefaultStageId(stages));
      const historyResponse = await fetchValidationRuns(authToken);
      setHistory(historyResponse.items);
    } catch (err) {
      if (isApiError(err) && err.status === 401) {
        handleSessionExpired();
        return;
      }
      setError(err instanceof Error ? err.message : "Validation run failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLogout() {
    const token = authToken;
    setError(null);

    try {
      if (token) {
        await logoutAuth(token);
      }
    } catch {
      // Even if the session is already invalid, we still clear the client state.
    } finally {
      handleSessionExpired("Signed out.");
    }
  }

  async function handleShare() {
    if (!run) {
      return;
    }

    try {
      await navigator.clipboard.writeText(`${formatShipmentCode(run.pack_id)} · ${run.pack_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to copy shipment reference.");
    }
  }

  function handleExport() {
    if (!run) {
      return;
    }

    const blob = new Blob([JSON.stringify(run, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${formatShipmentCode(run.pack_id).toLowerCase()}-validation-report.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const pageTitle = showAuthGate ? "Secure access" : run ? formatShipmentCode(run.pack_id) : "Shipment workspace";

  return (
    <div className="layout-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand__mark">
            <AppIcon name="shield" className="app-icon" />
          </span>
          <div>
            <strong>Customs Validation</strong>
          </div>
        </div>

        <nav className="nav-list" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.label}
              className={item.active ? "nav-item nav-item--active" : "nav-item"}
              type="button"
            >
              <AppIcon name={item.icon} className="app-icon" />
              <span>{item.label}</span>
              {item.badge ? <span className="nav-item__badge">{item.badge}</span> : null}
            </button>
          ))}
        </nav>

        <section className="sidebar-section">
          <div className="sidebar-section__head">
            <strong>Recent shipments</strong>
          </div>
          <HistoryList
            items={history}
            activeRunId={run?.run_id}
            isLoading={isHistoryLoading}
            onOpenRun={(packId) => void handleOpenRun(packId)}
          />
        </section>

        <div className="sidebar-footer">
          <div className="sidebar-footer__status">
            <span className={health ? "status-dot status-dot--online" : "status-dot"} />
            <span>{health ? `${health.status} · v${health.version}` : "API offline"}</span>
          </div>
          <span>{authStatusLabel}</span>
        </div>
      </aside>

      <main className="main-shell">
        <header className="masthead">
          <div className="breadcrumb-row">
            <span className="breadcrumb">Shipments</span>
            <AppIcon name="chevronRight" className="app-icon app-icon--tiny app-icon--muted" />
            <strong>{pageTitle}</strong>
          </div>

          <div className="masthead__actions">
            <label className="searchbar">
              <AppIcon name="search" className="app-icon app-icon--muted" />
              <input
                type="search"
                disabled={!isAuthenticated}
                value={searchQuery}
                onChange={(event) =>
                  startTransition(() => {
                    setSearchQuery(event.target.value);
                  })
                }
                placeholder={isAuthenticated ? "Search shipments, documents, rules..." : "Sign in to search workspace data"}
              />
              <span className="searchbar__hint">⌘K</span>
            </label>

            <button className="icon-button" type="button" aria-label="Notifications">
              <AppIcon name="bell" className="app-icon" />
              <span className="icon-button__badge">3</span>
            </button>
            <button className="icon-button" type="button" aria-label="Help">
              <AppIcon name="help" className="app-icon" />
            </button>

            <div className="profile-chip">
              <span className="profile-chip__avatar">{getUserInitials(authUser)}</span>
              <span>
                <strong>{authUser?.full_name ?? "Secure access"}</strong>
                <small>{authProfileLabel}</small>
              </span>
            </div>
            {isAuthenticated ? (
              <button className="ghost-button ghost-button--compact" type="button" onClick={() => void handleLogout()}>
                <span>Log out</span>
              </button>
            ) : null}
          </div>
        </header>

        <section className="page-header">
          <div className="page-header__copy">
            <div className="page-header__title-row">
              <h1>{showAuthGate ? "Internal access" : run ? `Shipment ${formatShipmentCode(run.pack_id)}` : "Validation workspace"}</h1>
              <span className={`run-pill run-pill--${showAuthGate ? "needs_review" : run?.status ?? "draft"}`}>
                {showAuthGate ? "Secure" : run ? getRunStatusLabel(run.status) : "Draft"}
              </span>
            </div>

            <div className="meta-strip">
              {showAuthGate ? (
                <>
                  <span>
                    <strong>Mode:</strong> Internal workspace
                  </span>
                  <span>
                    <strong>Access:</strong> {authAccessLabel}
                  </span>
                  <span>
                    <strong>API:</strong> {health ? "Online" : "Offline"}
                  </span>
                  <span className="meta-pill">{isBootstrapSetup ? "Bootstrap" : authBootstrap?.registration_open ? "Open registration" : "Protected"}</span>
                </>
              ) : (
                <>
                  <span>
                    <strong>Exporter:</strong> {shipmentMeta.exporter}
                  </span>
                  <span>
                    <strong>Importer:</strong> {shipmentMeta.importer}
                  </span>
                  <span>
                    <strong>Route:</strong> {shipmentMeta.route}
                  </span>
                  <span>
                    <strong>Incoterms:</strong> {shipmentMeta.incoterms}
                  </span>
                  <span className="meta-pill">{shipmentMeta.mode}</span>
                </>
              )}
            </div>
          </div>

          <div className="page-header__actions">
            {showAuthGate ? (
              <div className="button-row">
                {!health ? (
                  <button className="ghost-button" type="button" onClick={handleRetryBootstrap}>
                    <AppIcon name="refresh" className="app-icon" />
                    <span>Retry connection</span>
                  </button>
                ) : null}
              </div>
            ) : (
              <div className="button-row">
                <button className="ghost-button" type="button" onClick={handleShare} disabled={!run}>
                  <AppIcon name="share" className="app-icon" />
                  <span>Share</span>
                </button>
                <button className="ghost-button" type="button" onClick={handleExport} disabled={!run}>
                  <AppIcon name="export" className="app-icon" />
                  <span>Export</span>
                </button>
                <button className="primary-button primary-button--inline" type="button" onClick={() => fileInputRef.current?.click()}>
                  <AppIcon name="upload" className="app-icon" />
                  <span>Select Docs</span>
                </button>
                <button
                  className="primary-button primary-button--dark primary-button--inline"
                  type="button"
                  onClick={() => void handleRunValidation()}
                  disabled={isSubmitting || files.length === 0}
                >
                  <AppIcon name="refresh" className="app-icon" />
                  <span>{isSubmitting ? "Running..." : "Run Validation"}</span>
                </button>
              </div>
            )}

            <div className="page-header__timestamp">
              <span>
                Last updated: {showAuthGate ? (authUser?.last_login_at ? formatTime(authUser.last_login_at) : "Awaiting sign-in") : run ? formatTime(run.updated_at) : "Not yet run"}
              </span>
            </div>
          </div>
        </section>

        <input
          ref={fileInputRef}
          className="visually-hidden"
          type="file"
          multiple
          accept=".pdf,image/png,image/jpeg,image/tiff,image/webp"
          onChange={handleFilesChange}
        />

        {isAuthenticated && files.length > 0 ? (
          <section className="upload-tray">
            <div>
              <strong>{files.length} files staged</strong>
              <p>
                {formatBytes(selectedBytes)} selected for the next validation run.
              </p>
            </div>
            <div className="upload-tray__chips">
              {files.slice(0, 6).map((file) => (
                <span key={`${file.name}-${file.size}`} className="file-chip">
                  {file.name}
                </span>
              ))}
              {files.length > 6 ? <span className="file-chip file-chip--more">+{files.length - 6} more</span> : null}
            </div>
          </section>
        ) : null}

        {error ? <div className="error-banner">{error}</div> : null}

        {showAuthGate ? (
          <section className="auth-panel">
            <div className="auth-panel__grid">
              <article className="auth-panel__aside">
                <span className="section-eyebrow">Protected internal workspace</span>
                <h2>{authAsideTitle}</h2>
                <p>{authAsideCopy}</p>
                <div className="auth-panel__notes">
                  <span>{health ? `API online · v${health.version}` : "API offline"}</span>
                  <span>{schemas.length} schemas available</span>
                  <span>{authRegistrationNote}</span>
                </div>
              </article>

              <form
                className="auth-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  void handleAuthSubmit();
                }}
              >
                <span className="section-eyebrow">{authFormEyebrow}</span>
                <h2>{authFormTitle}</h2>
                <p>{authFormCopy}</p>

                {isOpenSelfRegistration ? (
                  <div className="auth-form__mode-switch" role="tablist" aria-label="Authentication mode">
                    <button
                      className={`auth-form__mode-button ${authMode === "login" ? "auth-form__mode-button--active" : ""}`}
                      type="button"
                      onClick={() => resetAuthForm("login")}
                    >
                      Sign in
                    </button>
                    <button
                      className={`auth-form__mode-button ${authMode === "register" ? "auth-form__mode-button--active" : ""}`}
                      type="button"
                      onClick={() => resetAuthForm("register")}
                    >
                      Create account
                    </button>
                  </div>
                ) : null}

                {authMode === "register" ? (
                  <label className="auth-form__field">
                    <span>Full name</span>
                    <input
                      type="text"
                      value={authFullName}
                      onChange={(event) => setAuthFullName(event.target.value)}
                      placeholder="Admin User"
                      autoComplete="name"
                    />
                  </label>
                ) : null}

                <label className="auth-form__field">
                  <span>Email</span>
                  <input
                    type="email"
                    value={authEmail}
                    onChange={(event) => setAuthEmail(event.target.value)}
                    placeholder="admin@example.com"
                    autoComplete="email"
                  />
                </label>

                <label className="auth-form__field">
                  <span>Password</span>
                  <input
                    type="password"
                    value={authPassword}
                    onChange={(event) => setAuthPassword(event.target.value)}
                    placeholder="Enter password"
                    autoComplete={authMode === "register" ? "new-password" : "current-password"}
                  />
                </label>

                <div className="button-row">
                  <button
                    className="primary-button primary-button--dark"
                    type="submit"
                    disabled={
                      isAuthSubmitting ||
                      !authEmail.trim() ||
                      !authPassword.trim() ||
                      (authMode === "register" && !authFullName.trim())
                    }
                  >
                    <span>{authSubmitLabel}</span>
                  </button>
                </div>
              </form>
            </div>
          </section>
        ) : (
          <>
        {isSubmitting ? (
          <WorkspaceStatePanel
            icon="refresh"
            tone="info"
            title="Validation in progress"
            message={`OCR, extraction, and rule checks are running for ${files.length} staged ${files.length === 1 ? "document" : "documents"}.`}
          />
        ) : null}
          </>
        )}

        {isWorkspaceBooting && !run && !isSubmitting ? (
          <WorkspaceStatePanel
            icon="refresh"
            tone="neutral"
            title="Loading workspace"
            message="Connecting to the API, loading shipment history, and restoring the latest validation run."
          />
        ) : null}

        {run ? (
          <>
            <section className="summary-band">
              <article className="summary-progress">
                <div className="progress-ring" style={{ ["--progress" as string]: String(stageSummary.progressPercent) }}>
                  <span>{stageSummary.progressPercent}%</span>
                </div>
                <div className="summary-progress__copy">
                  <span className="summary-label">Overall Status</span>
                  <strong>{run.status === "validated" ? "Ready" : "Check"}</strong>
                  <small>
                    {nextActionStage
                      ? `${nextActionStage.issueCount > 0 ? "Action needed" : "Review"} in ${nextActionStage.label}`
                      : "Waiting for documents"}
                  </small>
                </div>
              </article>

              <article className="summary-metric">
                <span className="summary-metric__icon summary-metric__icon--blue">
                  <AppIcon name="document" className="app-icon" />
                </span>
                <div>
                  <span className="summary-label">Documents</span>
                  <strong>
                    {stageSummary.documentCount} of {allStages.length}
                  </strong>
                </div>
              </article>

              <article className="summary-metric">
                <span className="summary-metric__icon summary-metric__icon--green">
                  <AppIcon name="checkCircle" className="app-icon" />
                </span>
                <div>
                  <span className="summary-label">OK</span>
                  <strong>{stageSummary.okCount}</strong>
                </div>
              </article>

              <article className="summary-metric">
                <span className="summary-metric__icon summary-metric__icon--amber">
                  <AppIcon name="warningCircle" className="app-icon" />
                </span>
                <div>
                  <span className="summary-label">Check</span>
                  <strong>{stageSummary.reviewCount}</strong>
                </div>
              </article>

              <article className="summary-metric">
                <span className="summary-metric__icon summary-metric__icon--slate">
                  <AppIcon name="minusCircle" className="app-icon" />
                </span>
                <div>
                  <span className="summary-label">Missing</span>
                  <strong>{stageSummary.missingCount}</strong>
                </div>
              </article>

              <article className="summary-metric">
                <span className="summary-metric__icon summary-metric__icon--red">
                  <AppIcon name="problemCircle" className="app-icon" />
                </span>
                <div>
                  <span className="summary-label">Problems</span>
                  <strong>{stageSummary.problemCount}</strong>
                </div>
              </article>

              <article className="summary-metric">
                <span className="summary-metric__icon summary-metric__icon--violet">
                  <AppIcon name="rules" className="app-icon" />
                </span>
                <div>
                  <span className="summary-label">Rules Evaluated</span>
                  <strong>{run.summary.total_rules}</strong>
                </div>
              </article>
            </section>

            <section className="stage-flow">
              {visibleStages.length > 0 ? (
                visibleStages.map((stage, index) => (
                  <div className="stage-flow__item" key={stage.id}>
                    <StageCard stage={stage} active={stage.id === activeStage?.id} onSelect={() => setActiveStageId(stage.id)} />
                    {index < visibleStages.length - 1 ? (
                      <div className="stage-flow__arrow" aria-hidden="true">
                        <AppIcon name="chevronRight" className="app-icon app-icon--muted" />
                      </div>
                    ) : null}
                  </div>
                ))
              ) : (
                <div className="empty-panel">
                  <strong>No stages match “{searchQuery}”.</strong>
                  <span>Try another document name, rule code, or issue text.</span>
                  <button className="ghost-button" type="button" onClick={handleClearSearch}>
                    Clear search
                  </button>
                </div>
              )}
            </section>

            {activeStage ? (
              <section className="detail-grid">
                <article className="detail-card detail-card--issues">
                  <div className="detail-card__head">
                    <div>
                      <span className="section-eyebrow">Current step</span>
                      <h2>{activeStage.label}</h2>
                    </div>
                    <span className={`stage-tag stage-tag--${activeStage.status}`}>{getStageToneLabel(activeStage.status)}</span>
                  </div>

                  {activeStage.visibleResults.length > 0 ? (
                    <div className="issue-stack">
                      {activeStage.visibleResults.map((item) => (
                          <div key={`${activeStage.id}-${item.rule_code}`} className="issue-row">
                            <div className={`issue-row__icon issue-row__icon--${item.status === "failed" ? item.severity : item.status}`}>
                              <AppIcon
                                name={
                                  item.status === "skipped"
                                    ? "minusCircle"
                                    : item.severity === "error"
                                      ? "problemCircle"
                                      : "warningCircle"
                                }
                                className="app-icon"
                              />
                            </div>
                            <div className="issue-row__body">
                              <strong>{item.message}</strong>
                              <span>
                                Rule {item.rule_code} · {item.documents.map((documentType) => formatDocumentType(documentType)).join(", ")}
                              </span>
                              {item.evidence[0]?.text_snippet ? (
                                <p>{item.evidence[0].text_snippet}</p>
                              ) : (
                                <p>No source snippet attached for this result.</p>
                              )}
                            </div>
                            <AppIcon name="chevronRight" className="app-icon app-icon--muted" />
                          </div>
                        ))}
                    </div>
                  ) : (
                    <div className="detail-empty">
                      <strong>No active issues</strong>
                      <span>
                        {isContractInformationalStage(activeStage)
                          ? "All document-level checks passed. Contract-dependent checks were skipped at the shipment level."
                          : isIncotermsInformationalStage(activeStage)
                            ? "All document-level checks passed. Incoterms comparison was skipped because the required addendum/invoice pair is incomplete."
                          : isBlPackingInformationalStage(activeStage)
                            ? "All document-level checks passed. BL and packing-list package comparison will resume when package quantity is available in both documents."
                          : isOptionalPaymentConfirmationStage(activeStage)
                            ? "Core document checks passed. Payment confirmation can be uploaded later as optional proof of prepayment."
                          : "All key checks passed for this document."}
                      </span>
                    </div>
                  )}

                  <div className="recommendation-box">
                    <span className="section-eyebrow">Recommended action</span>
                    <p>{getStageRecommendedAction(activeStage)}</p>
                  </div>
                </article>

                <article className="detail-card">
                  <div className="detail-card__head">
                    <div>
                      <span className="section-eyebrow">Extracted data</span>
                      <h2>{activeStage.document ? activeStage.document.source_file_name : activeStage.label}</h2>
                    </div>
                    {activeStage.document ? (
                      <span className="document-pill">
                        {formatDocumentType(activeStage.document.document_type)} · {activeStage.document.pages} pages
                      </span>
                    ) : null}
                  </div>

                  {activeStage.document ? (
                    <>
                      <div className="document-stats">
                        <div>
                          <span className="summary-label">Extraction status</span>
                          <strong>{formatFieldLabel(activeStage.document.extraction_status)}</strong>
                        </div>
                        <div>
                          <span className="summary-label">Fields</span>
                          <strong>{Object.keys(activeStage.document.fields ?? {}).length}</strong>
                        </div>
                        <div>
                          <span className="summary-label">Line items</span>
                          <strong>{activeStage.document.line_items.length}</strong>
                        </div>
                      </div>

                      {activeFieldEntries.length > 0 || activeLineItemEntries.length > 0 ? (
                        <section className="extraction-review">
                          {activeFieldEntries.length > 0 ? (
                            <>
                              <div className="extraction-review__head">
                                <span className="section-eyebrow">Field review</span>
                                <span className="document-pill">{activeFieldEntries.length} extracted fields</span>
                              </div>

                              <dl className="field-grid">
                                {activeFieldEntries.map((field) => (
                                  <div key={`${activeStage.id}-${field.key}`} className="field-grid__item">
                                    <dt>{field.label}</dt>
                                    <dd className="field-grid__value">{field.primaryValue}</dd>

                                    <div className="field-grid__meta">
                                      {field.derived ? <span className="field-badge field-badge--derived">Derived</span> : null}
                                      {field.confidence !== null ? (
                                        <span className={`field-badge field-badge--${getConfidenceTone(field.confidence)}`}>
                                          {Math.round(field.confidence * 100)}% confidence
                                        </span>
                                      ) : null}
                                      {field.pageNo !== null ? (
                                        <span className="field-badge field-badge--page">Page {field.pageNo}</span>
                                      ) : null}
                                    </div>

                                    {field.rawValue && field.rawValue !== field.primaryValue ? (
                                      <div className="field-grid__detail">
                                        <span>Raw</span>
                                        <strong>{field.rawValue}</strong>
                                      </div>
                                    ) : null}

                                    {field.normalizedValue && field.normalizedValue !== field.primaryValue ? (
                                      <div className="field-grid__detail">
                                        <span>Normalized</span>
                                        <strong>{field.normalizedValue}</strong>
                                      </div>
                                    ) : null}

                                    {field.snippet ? (
                                      <div className="field-grid__snippet">
                                        <span>Source snippet</span>
                                        <p>{field.snippet}</p>
                                      </div>
                                    ) : null}
                                  </div>
                                ))}
                              </dl>
                            </>
                          ) : null}

                          {activeLineItemEntries.length > 0 ? (
                            <div className="line-items-review">
                              <div className="extraction-review__head">
                                <span className="section-eyebrow">Line items</span>
                                <span className="document-pill">{activeLineItemEntries.length} rows</span>
                              </div>

                              <div className="line-items-review__stack">
                                {activeLineItemEntries.map((item) => (
                                  <section key={`${activeStage.id}-${item.label}`} className="line-item-card">
                                    <div className="line-item-card__head">
                                      <strong>{item.label}</strong>
                                      <span>{item.fields.length} extracted fields</span>
                                    </div>

                                    <dl className="field-grid field-grid--line-item">
                                      {item.fields.map((field) => (
                                        <div key={`${item.label}-${field.key}`} className="field-grid__item field-grid__item--compact">
                                          <dt>{field.label}</dt>
                                          <dd className="field-grid__value">{field.primaryValue}</dd>
                                          <div className="field-grid__meta">
                                            {field.derived ? (
                                              <span className="field-badge field-badge--derived">Derived</span>
                                            ) : null}
                                            {field.confidence !== null ? (
                                              <span className={`field-badge field-badge--${getConfidenceTone(field.confidence)}`}>
                                                {Math.round(field.confidence * 100)}%
                                              </span>
                                            ) : null}
                                          </div>
                                          {field.snippet ? (
                                            <div className="field-grid__snippet">
                                              <span>Source snippet</span>
                                              <p>{field.snippet}</p>
                                            </div>
                                          ) : null}
                                        </div>
                                      ))}
                                    </dl>
                                  </section>
                                ))}
                              </div>
                            </div>
                          ) : null}
                        </section>
                      ) : (
                        <div className="detail-empty">
                          <strong>No extracted values yet</strong>
                          <span>The document is present, but no user-facing fields were extracted.</span>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="detail-empty">
                      <strong>{isOptionalPaymentConfirmationStage(activeStage) ? "Optional document not uploaded" : "Document missing"}</strong>
                      <span>
                        {isOptionalPaymentConfirmationStage(activeStage)
                          ? "Upload this file later if you want to attach proof of payment. The rest of the shipment review can proceed without it."
                          : "Upload this file to unlock extraction and rule evaluation for the current step."}
                      </span>
                    </div>
                  )}
                </article>
              </section>
            ) : null}

            {shipmentNotices.length > 0
              ? shipmentNotices.map((notice) => (
                  <section key={notice.id} className="shipment-notice">
                    <span className="section-eyebrow">Pack note</span>
                    <strong>{notice.title}</strong>
                    <p>{notice.body}</p>
                  </section>
                ))
              : null}

            <section className="footer-grid">
              <article className="footer-card">
                <div className="footer-card__head">
                  <span className="footer-card__icon footer-card__icon--blue">
                    <AppIcon name="chevronRight" className="app-icon" />
                  </span>
                  <div>
                    <span className="section-eyebrow">Next action</span>
                    <h2>{nextActionStage ? `Review ${nextActionStage.label}` : "Prepare shipment"}</h2>
                  </div>
                </div>
                <p>
                  {nextActionStage
                    ? `${nextActionStage.message}. Then proceed to the next document in the validation chain.`
                    : "Select shipment documents and start the first validation run."}
                </p>
                {nextActionStage ? (
                  <button className="primary-button primary-button--light" type="button" onClick={() => setActiveStageId(nextActionStage.id)}>
                    <span>{nextActionStage.status === "missing" ? "Inspect missing step" : `Go to ${nextActionStage.label}`}</span>
                    <AppIcon name="chevronRight" className="app-icon" />
                  </button>
                ) : null}
              </article>

              <article className="footer-card">
                <div className="footer-card__head">
                  <span className="section-eyebrow">Recent alerts</span>
                  {visibleAlerts.length > 0 ? <span className="footer-card__badge">{visibleAlerts.length}</span> : null}
                </div>
                {visibleAlerts.length > 0 ? (
                  <ul className="timeline-list">
                    {visibleAlerts.map((item) => (
                      <li key={`${item.rule_code}-${item.documents.join("-")}`}>
                        <span
                          className={
                            item.status === "skipped"
                              ? "timeline-list__tone timeline-list__tone--missing"
                              : item.severity === "error"
                                ? "timeline-list__tone timeline-list__tone--problem"
                                : "timeline-list__tone timeline-list__tone--warning"
                          }
                        />
                        <div>
                          <strong>{item.message}</strong>
                          <small>{item.rule_code} · {formatTime(run.updated_at)}</small>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="detail-empty">
                    <strong>No open alerts</strong>
                    <span>Triggered issues will appear here after the next validation run.</span>
                  </div>
                )}
              </article>

              <article className="footer-card">
                <div className="footer-card__head footer-card__head--spread">
                  <div>
                    <span className="section-eyebrow">Activity timeline</span>
                  </div>
                  <button className="link-button" type="button">
                    View full timeline
                  </button>
                </div>
                <ul className="timeline-list">
                  {activityTimeline.map((item, index) => (
                    <li key={`${item.message}-${index}`}>
                      <span className={`timeline-list__tone timeline-list__tone--${item.tone}`} />
                      <div>
                        <strong>{item.message}</strong>
                        <small>{item.actor}</small>
                      </div>
                      <time>{formatTime(item.timestamp)}</time>
                    </li>
                  ))}
                </ul>
              </article>
            </section>
          </>
        ) : showEmptyStartState ? (
          <section className="empty-state-panel">
            <span className="section-eyebrow">Validation-only internal pipeline</span>
            <h2>{history.length > 0 ? "Restore a shipment or start a fresh validation run" : "Stage the first document pack"}</h2>
            <p>
              {health
                ? "Select shipment documents, run OCR and validation, and inspect the workflow as a readable shipment screen instead of a raw report dump."
                : "The API is not responding yet. Reconnect the backend first, then stage a shipment for OCR, extraction, and rule validation."}
            </p>
            <div className="button-row">
              {health ? (
                <button className="primary-button primary-button--inline" type="button" onClick={() => fileInputRef.current?.click()}>
                  <AppIcon name="upload" className="app-icon" />
                  <span>Select Documents</span>
                </button>
              ) : (
                <button className="ghost-button" type="button" onClick={handleRetryBootstrap}>
                  <AppIcon name="refresh" className="app-icon" />
                  <span>Retry connection</span>
                </button>
              )}
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}
