import {
  AdminUserView,
  AnalyticsDashboard,
  ApprovedFact,
  AuditLogEntry,
  AuthResponse,
  BrandAsset,
  ExportCertificate,
  FindingDecision,
  GlossaryTerm,
  Guideline,
  ReviewComment,
  Submission,
  User,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

function getHeaders(isFormData = false): HeadersInit {
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("brandsentinel_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}

export const api = {
  // Auth
  async register(payload: any): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    return res.json();
  },

  async login(payload: any): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    return res.json();
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch session");
    return res.json();
  },

  // Knowledge Hub
  async listGuidelines(): Promise<Guideline[]> {
    const res = await fetch(`${API_BASE}/knowledge/guidelines`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load guidelines");
    return res.json();
  },

  async uploadGuideline(formData: FormData): Promise<Guideline> {
    const res = await fetch(`${API_BASE}/knowledge/guidelines/upload`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Guideline upload failed");
    }
    return res.json();
  },

  async listFacts(): Promise<ApprovedFact[]> {
    const res = await fetch(`${API_BASE}/knowledge/facts`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load approved facts");
    return res.json();
  },

  async createFact(payload: any): Promise<ApprovedFact> {
    const res = await fetch(`${API_BASE}/knowledge/facts`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create approved fact");
    }
    return res.json();
  },

  async listGlossary(): Promise<GlossaryTerm[]> {
    const res = await fetch(`${API_BASE}/knowledge/glossary`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load glossary");
    return res.json();
  },

  async createGlossary(payload: any): Promise<GlossaryTerm> {
    const res = await fetch(`${API_BASE}/knowledge/glossary`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to add glossary rule");
    }
    return res.json();
  },

  async listAssets(): Promise<BrandAsset[]> {
    const res = await fetch(`${API_BASE}/knowledge/assets`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load brand assets");
    return res.json();
  },

  async createAsset(payload: any): Promise<BrandAsset> {
    const res = await fetch(`${API_BASE}/knowledge/assets`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create brand asset");
    }
    return res.json();
  },

  // Submissions & Auditing
  async listSubmissions(): Promise<Submission[]> {
    const res = await fetch(`${API_BASE}/audit/submissions`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load submissions");
    return res.json();
  },

  async getSubmission(submissionId: string): Promise<Submission> {
    const res = await fetch(`${API_BASE}/audit/submissions/${submissionId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load submission details");
    return res.json();
  },

  async createSubmission(payload: { title: string; target_channel: string; raw_content: string }): Promise<Submission> {
    const res = await fetch(`${API_BASE}/audit/submissions`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create draft submission");
    }
    return res.json();
  },

  async runAudit(submissionId: string, rawContent?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/audit/submissions/${submissionId}/run`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ raw_content: rawContent }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to run audit pipeline");
    }
    return res.json();
  },

  async uploadAndRunAudit(formData: FormData): Promise<any> {
    const res = await fetch(`${API_BASE}/audit/upload-and-run`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Document audit pipeline failed");
    }
    return res.json();
  },

  // Governance & Human-in-the-Loop Decisions
  async recordFindingDecision(
    findingId: string,
    payload: { decision: "ACCEPTED" | "EDITED" | "REJECTED"; custom_edit?: string; rejection_reason?: string }
  ): Promise<FindingDecision> {
    const res = await fetch(`${API_BASE}/governance/findings/${findingId}/decide`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to record decision");
    }
    return res.json();
  },

  async submitForReview(submissionId: string): Promise<Submission> {
    const res = await fetch(`${API_BASE}/governance/submissions/${submissionId}/submit-for-review`, {
      method: "POST",
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to submit for review");
    }
    return res.json();
  },

  async escalateSubmission(submissionId: string, reason: string): Promise<Submission> {
    const res = await fetch(`${API_BASE}/governance/submissions/${submissionId}/escalate`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to escalate submission");
    }
    return res.json();
  },

  async signOffSubmission(
    submissionId: string,
    payload: { approved: boolean; notes?: string }
  ): Promise<Submission> {
    const res = await fetch(`${API_BASE}/governance/submissions/${submissionId}/sign-off`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to complete sign-off");
    }
    return res.json();
  },

  async exportApprovedContent(submissionId: string): Promise<ExportCertificate> {
    const res = await fetch(`${API_BASE}/governance/submissions/${submissionId}/export`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to generate export certificate");
    }
    return res.json();
  },

  async listComments(submissionId: string): Promise<ReviewComment[]> {
    const res = await fetch(`${API_BASE}/governance/submissions/${submissionId}/comments`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load comments");
    return res.json();
  },

  async addComment(
    submissionId: string,
    payload: { comment: string; finding_id?: string }
  ): Promise<ReviewComment> {
    const res = await fetch(`${API_BASE}/governance/submissions/${submissionId}/comments`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to post comment");
    }
    return res.json();
  },

  // Analytics & Insights
  async getAnalyticsDashboard(): Promise<AnalyticsDashboard> {
    const res = await fetch(`${API_BASE}/analytics/dashboard`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load analytics dashboard");
    return res.json();
  },

  // Admin & Team Management
  async getOrganizationProfile(): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/organization`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to load organization profile");
    return res.json();
  },

  async listAdminUsers(): Promise<AdminUserView[]> {
    const res = await fetch(`${API_BASE}/admin/users`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to list organization members");
    return res.json();
  },

  async updateUserRole(userId: string, role: string): Promise<AdminUserView> {
    const res = await fetch(`${API_BASE}/admin/users/${userId}/role`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify({ role }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to update role");
    }
    return res.json();
  },

  async updateUserStatus(userId: string, isActive: boolean): Promise<AdminUserView> {
    const res = await fetch(`${API_BASE}/admin/users/${userId}/status`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify({ is_active: isActive }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to update status");
    }
    return res.json();
  },

  async listAuditLogs(limit = 50, eventType?: string): Promise<AuditLogEntry[]> {
    const url = new URL(`${API_BASE}/admin/audit-logs`);
    url.searchParams.set("limit", limit.toString());
    if (eventType) url.searchParams.set("event_type", eventType);
    const res = await fetch(url.toString(), {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch audit trail");
    return res.json();
  },
};
