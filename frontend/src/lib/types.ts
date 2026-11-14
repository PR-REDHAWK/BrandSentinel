export type UserRole = "CREATOR" | "BRAND_MANAGER" | "REVIEWER" | "ADMIN";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  organization?: Organization;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Guideline {
  id: string;
  organization_id: string;
  title: string;
  file_type: string;
  file_path: string;
  version: number;
  status: string;
  created_at: string;
  chunk_count?: number;
}

export interface ApprovedFact {
  id: string;
  organization_id: string;
  category: string;
  claim_pattern: string;
  approved_truth: string;
  mandatory_caveat?: string;
  source_citation: string;
  effective_from?: string;
  expires_at?: string;
  created_at: string;
}

export interface GlossaryTerm {
  id: string;
  organization_id: string;
  term: string;
  is_banned: boolean;
  preferred_term?: string;
  definition_or_rule: string;
  case_sensitive: boolean;
  created_at: string;
}

export interface BrandAsset {
  id: string;
  organization_id: string;
  asset_type: "LOGO" | "PALETTE" | "TYPOGRAPHY";
  name: string;
  hex_colors?: string[];
  aspect_ratio?: number;
  rules?: Record<string, any>;
  created_at: string;
}

export interface FindingDecision {
  id: string;
  finding_id: string;
  user_id: string;
  decision: "ACCEPTED" | "EDITED" | "REJECTED";
  custom_edit?: string;
  rejection_reason?: string;
  created_at: string;
}

export interface Finding {
  id: string;
  content_version_id: string;
  rule_id: string;
  engine: "DETERMINISTIC" | "RAG_LLM" | "VISION_OCR";
  category: string;
  severity: "HIGH" | "MEDIUM" | "LOW" | "INFO";
  title: string;
  detected_content: string;
  explanation: string;
  source_citation?: string;
  supporting_passage?: string;
  suggested_correction?: string;
  confidence_score: number;
  requires_human_review: boolean;
  created_at: string;
  decision?: FindingDecision;
}

export interface ReviewComment {
  id: string;
  user_id: string;
  finding_id?: string;
  comment: string;
  created_at: string;
}

export interface ContentVersion {
  id: string;
  submission_id: string;
  version_number: number;
  raw_content?: string;
  document_path?: string;
  has_images: boolean;
  image_metadata: any[];
  audit_score?: number;
  created_at: string;
  findings: Finding[];
}

export interface Submission {
  id: string;
  organization_id: string;
  creator_id: string;
  title: string;
  target_channel?: string;
  current_status: "DRAFT" | "AUDITED" | "IN_REVIEW" | "ESCALATED" | "APPROVED" | "REJECTED";
  created_at: string;
  updated_at: string;
  versions?: ContentVersion[];
}

export interface ExportCertificate {
  certificate_id: string;
  platform: string;
  organization: string;
  title: string;
  target_channel: string;
  version_number: number;
  approval_status: string;
  approval_timestamp: string;
  signed_by: string;
  signee_role: string;
  signee_notes: string;
  brand_compliance_score: number;
  resolved_findings_count: number;
  audit_summary: Array<{
    rule_id: string;
    severity: string;
    title: string;
    evidence_citation?: string;
    decision: string;
  }>;
  final_approved_content: string;
  governance_notice: string;
}

export interface AnalyticsDashboard {
  overview: {
    total_submissions: number;
    approved_submissions: number;
    in_review_queue: number;
    average_compliance_score: number;
  };
  violations_by_category: Record<string, number>;
  violations_by_severity: Record<string, number>;
  top_violated_rules: Array<{
    rule_id: string;
    title: string;
    frequency: number;
  }>;
  creator_actions: {
    accepted: number;
    edited: number;
    rejected: number;
    acceptance_rate_pct: number;
  };
  guideline_ambiguity_ranking: Array<{
    rule_id: string;
    source_citation: string;
    rejections: number;
    insight: string;
  }>;
  recent_activity: Array<{
    id: string;
    event_type: string;
    entity_type: string;
    details: any;
    timestamp: string;
  }>;
}

export interface AdminUserView {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  user_id?: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  details: any;
  ip_address?: string;
  created_at: string;
}
