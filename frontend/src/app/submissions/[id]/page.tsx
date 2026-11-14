"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  FileCheck2,
  BookOpen,
  ArrowLeft,
  Check,
  Edit3,
  X,
  Play,
  Clock,
  Sparkles,
  Send,
  MessageSquare,
  FileDown,
  AlertCircle,
  Award,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { ContentVersion, ExportCertificate, Finding, ReviewComment, Submission } from "@/lib/types";

export default function SubmissionAuditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();

  const [submission, setSubmission] = useState<Submission | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<ContentVersion | null>(null);
  const [comments, setComments] = useState<ReviewComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [auditing, setAuditing] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Modals & form state
  const [activeEditFinding, setActiveEditFinding] = useState<Finding | null>(null);
  const [customEditText, setCustomEditText] = useState("");
  const [activeRejectFinding, setActiveRejectFinding] = useState<Finding | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [escalateModalOpen, setEscalateModalOpen] = useState(false);
  const [escalateReason, setEscalateReason] = useState("");
  const [signOffModalOpen, setSignOffModalOpen] = useState<"approve" | "reject" | null>(null);
  const [signOffNotes, setSignOffNotes] = useState("");
  const [exportCert, setExportCert] = useState<ExportCertificate | null>(null);
  const [newCommentText, setNewCommentText] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [subData, commentsData] = await Promise.all([
        api.getSubmission(id),
        api.listComments(id).catch(() => []),
      ]);
      setSubmission(subData);
      setComments(commentsData);
      if (subData.versions && subData.versions.length > 0) {
        const latest = [...subData.versions].sort((a, b) => b.version_number - a.version_number)[0];
        setSelectedVersion(latest);
      }
    } catch (e: any) {
      console.error(e);
      setErrorMessage(e.message || "Failed to load submission");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && id) {
      loadData();
    }
  }, [user, id]);

  const handleRunAudit = async () => {
    setAuditing(true);
    setErrorMessage(null);
    try {
      await api.runAudit(id, selectedVersion?.raw_content);
      setSuccessMessage("Tri-engine audit completed successfully.");
      await loadData();
    } catch (err: any) {
      setErrorMessage(err.message || "Audit failed");
    } finally {
      setAuditing(false);
    }
  };

  const handleAcceptFinding = async (finding: Finding) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.recordFindingDecision(finding.id, {
        decision: "ACCEPTED",
      });
      setSuccessMessage(`Accepted correction for ${finding.rule_id}`);
      await loadData();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to record decision");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveCustomEdit = async () => {
    if (!activeEditFinding) return;
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.recordFindingDecision(activeEditFinding.id, {
        decision: "EDITED",
        custom_edit: customEditText,
      });
      setActiveEditFinding(null);
      setCustomEditText("");
      setSuccessMessage(`Saved custom edit for ${activeEditFinding.rule_id}`);
      await loadData();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to save edit");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveRejection = async () => {
    if (!activeRejectFinding) return;
    if (!rejectionReason.trim()) {
      alert("Please provide a reason for rejecting this finding (required for audit telemetry).");
      return;
    }
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.recordFindingDecision(activeRejectFinding.id, {
        decision: "REJECTED",
        rejection_reason: rejectionReason,
      });
      setActiveRejectFinding(null);
      setRejectionReason("");
      setSuccessMessage(`Recorded rejection exception for ${activeRejectFinding.rule_id}`);
      await loadData();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to reject finding");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitForReview = async () => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.submitForReview(id);
      setSuccessMessage("Content submitted to review queue.");
      await loadData();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to submit for review");
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalate = async () => {
    if (!escalateReason.trim()) {
      alert("Please provide an escalation reason.");
      return;
    }
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.escalateSubmission(id, escalateReason);
      setEscalateModalOpen(false);
      setEscalateReason("");
      setSuccessMessage("Submission escalated to Brand Compliance / Legal.");
      await loadData();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to escalate");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSignOff = async (approved: boolean) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await api.signOffSubmission(id, {
        approved,
        notes: signOffNotes,
      });
      setSignOffModalOpen(null);
      setSignOffNotes("");
      setSuccessMessage(approved ? "Submission approved and version-locked!" : "Submission rejected.");
      await loadData();
    } catch (err: any) {
      setErrorMessage(err.message || "Sign-off blocked");
    } finally {
      setActionLoading(false);
    }
  };

  const handleExportCertificate = async () => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      const cert = await api.exportApprovedContent(id);
      setExportCert(cert);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to export certificate");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCommentText.trim()) return;
    try {
      await api.addComment(id, { comment: newCommentText.trim() });
      setNewCommentText("");
      const updatedComments = await api.listComments(id);
      setComments(updatedComments);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to post comment");
    }
  };

  if (loading && !submission) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-slate-500 font-medium animate-pulse">Loading submission audit data...</div>
      </div>
    );
  }

  if (!submission) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-bold text-slate-800">Submission not found</h2>
        <Link href="/submissions" className="text-blue-700 underline text-sm mt-2 inline-block">
          Return to review queue
        </Link>
      </div>
    );
  }

  const findings: Finding[] = selectedVersion?.findings || [];
  const score = selectedVersion?.audit_score ?? 100.0;
  const isApproved = submission.current_status === "APPROVED";
  const canReview = user?.role === "REVIEWER" || user?.role === "BRAND_MANAGER" || user?.role === "ADMIN";

  const unresolvedHigh = findings.filter(
    (f) =>
      f.severity === "HIGH" &&
      (!f.decision || (f.decision.decision === "REJECTED" && !f.decision.rejection_reason))
  );

  const scoreBadgeColor =
    score >= 85
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : score >= 70
      ? "bg-amber-50 text-amber-700 border-amber-200"
      : "bg-red-50 text-red-700 border-red-200";

  return (
    <div className="space-y-6">
      {/* Toast Messages */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-800 rounded-xl flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-red-500 hover:text-red-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <Check className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-500 hover:text-emerald-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            href="/submissions"
            className="p-2 border border-slate-200 bg-white hover:bg-slate-50 rounded-lg text-slate-600 transition shadow-xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold text-slate-900">{submission.title}</h1>
              <span className="text-xs bg-slate-200 px-2 py-0.5 rounded text-slate-700 font-medium">
                {submission.target_channel || "General"}
              </span>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                  isApproved
                    ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                    : submission.current_status === "ESCALATED"
                    ? "bg-purple-100 text-purple-800 border border-purple-300"
                    : submission.current_status === "IN_REVIEW"
                    ? "bg-amber-100 text-amber-800 border border-amber-300"
                    : "bg-slate-100 text-slate-800 border border-slate-300"
                }`}
              >
                {submission.current_status}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Version v{selectedVersion?.version_number || 1} • Created by{" "}
              <span className="font-mono text-slate-700">{submission.creator_id.slice(0, 8)}</span>
            </p>
          </div>
        </div>

        {/* Workflow Action Buttons */}
        <div className="flex items-center space-x-2">
          {!isApproved && (
            <button
              onClick={handleRunAudit}
              disabled={auditing || actionLoading}
              className="flex items-center space-x-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold px-3 py-2 rounded-lg shadow-xs transition disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${auditing ? "animate-spin" : ""}`} />
              <span>{auditing ? "Auditing..." : "Re-Audit"}</span>
            </button>
          )}

          {!isApproved && submission.current_status === "DRAFT" && (
            <button
              onClick={handleSubmitForReview}
              disabled={actionLoading}
              className="flex items-center space-x-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-3 py-2 rounded-lg shadow-xs transition"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit for Review</span>
            </button>
          )}

          {!isApproved && canReview && (
            <>
              <button
                onClick={() => setEscalateModalOpen(true)}
                disabled={actionLoading}
                className="flex items-center space-x-1 text-xs font-semibold px-3 py-2 border border-purple-300 bg-purple-50 text-purple-800 hover:bg-purple-100 rounded-lg transition"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-purple-700" />
                <span>Escalate</span>
              </button>
              <button
                onClick={() => setSignOffModalOpen("approve")}
                disabled={actionLoading}
                className="flex items-center space-x-1 text-xs font-semibold px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg shadow-xs transition"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Sign Off & Approve</span>
              </button>
              <button
                onClick={() => setSignOffModalOpen("reject")}
                disabled={actionLoading}
                className="flex items-center space-x-1 text-xs font-semibold px-3 py-2 border border-red-300 bg-red-50 text-red-700 hover:bg-red-100 rounded-lg transition"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reject</span>
              </button>
            </>
          )}

          {isApproved && (
            <button
              onClick={handleExportCertificate}
              disabled={actionLoading}
              className="flex items-center space-x-1.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-xs transition"
            >
              <Award className="w-4 h-4" />
              <span>Export Certified Copy</span>
            </button>
          )}
        </div>
      </div>

      {/* Brand Compliance Score Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex items-center justify-between">
        <div className="space-y-1">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Brand Compliance Index
          </div>
          <div className="flex items-baseline space-x-3">
            <span className="text-4xl font-extrabold text-slate-900">{score}</span>
            <span className="text-sm text-slate-500 font-medium">/ 100</span>
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${scoreBadgeColor}`}>
              {score >= 85 ? "Compliant" : score >= 70 ? "Needs Review" : "Major Violations"}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            {findings.length === 0
              ? "Zero violations detected. Content is verified against brand guidelines."
              : `${findings.length} brand compliance findings detected across deterministic, RAG, and visual checks.`}
          </p>
        </div>

        {/* Severity Count Pills */}
        <div className="flex space-x-3">
          <div className="text-center px-4 py-2 bg-red-50 border border-red-200 rounded-lg">
            <div className="text-lg font-bold text-red-700">
              {findings.filter((f) => f.severity === "HIGH").length}
            </div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-red-600">High</div>
          </div>
          <div className="text-center px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="text-lg font-bold text-amber-700">
              {findings.filter((f) => f.severity === "MEDIUM").length}
            </div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-amber-600">Med</div>
          </div>
          <div className="text-center px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-lg font-bold text-blue-700">
              {findings.filter((f) => f.severity === "LOW").length}
            </div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-blue-600">Low</div>
          </div>
        </div>
      </div>

      {/* Main Two-Column Audit Studio */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Draft Content + Review Comments */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
                <FileCheck2 className="w-4 h-4 text-slate-500" />
                <span>Submitted Copy</span>
              </h2>
              <span className="text-xs text-slate-400">
                {isApproved ? "Version-Locked Copy" : "Working Draft"}
              </span>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg font-mono text-xs text-slate-800 whitespace-pre-wrap leading-relaxed max-h-[450px] overflow-y-auto">
              {selectedVersion?.raw_content || "No raw content provided."}
            </div>
          </div>

          {/* Comments Panel */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-semibold text-xs text-slate-900 flex items-center space-x-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-blue-600" />
                <span>Review Collaboration ({comments.length})</span>
              </h3>
            </div>

            <div className="space-y-2.5 max-h-[300px] overflow-y-auto">
              {comments.length === 0 ? (
                <div className="text-center py-4 text-slate-400 text-xs">No comments recorded yet.</div>
              ) : (
                comments.map((c) => (
                  <div key={c.id} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span className="font-mono">{c.user_id.slice(0, 8)}</span>
                      <span>{new Date(c.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-slate-800">{c.comment}</p>
                  </div>
                ))
              )}
            </div>

            <form onSubmit={handleAddComment} className="flex space-x-2 pt-2 border-t border-slate-100">
              <input
                type="text"
                placeholder="Add reviewer feedback..."
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-600"
              />
              <button
                type="submit"
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-xs"
              >
                Post
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Unified Findings Stream */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Evidence-Backed Findings ({findings.length})</span>
            </h2>
            <span className="text-xs text-slate-400">Severity-Ranked (AI Suggests. Humans Decide.)</span>
          </div>

          {findings.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400">
              <ShieldCheck className="w-10 h-10 text-emerald-600 mx-auto mb-2 opacity-80" />
              <p className="text-sm font-medium text-slate-700">No brand violations detected.</p>
              <p className="text-xs text-slate-500 mt-1">
                Content complies fully with active brand guidelines and verified facts.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {findings.map((f) => {
                const sevColor =
                  f.severity === "HIGH"
                    ? "bg-red-50 text-red-700 border-red-200"
                    : f.severity === "MEDIUM"
                    ? "bg-amber-50 text-amber-700 border-amber-200"
                    : "bg-blue-50 text-blue-700 border-blue-200";

                const engineLabel =
                  f.engine === "DETERMINISTIC"
                    ? "Deterministic Rule"
                    : f.engine === "RAG_LLM"
                    ? "RAG + LLM Grounding"
                    : "Vision & OCR";

                const decision = f.decision;

                return (
                  <div
                    key={f.id}
                    className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3"
                  >
                    {/* Finding Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${sevColor}`}>
                          {f.severity}
                        </span>
                        <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono">
                          {f.rule_id}
                        </span>
                        <span className="text-xs text-slate-400">• {engineLabel}</span>
                      </div>

                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono text-slate-500">
                          {Math.round(f.confidence_score * 100)}% Conf.
                        </span>
                        {f.requires_human_review && (
                          <span className="text-[10px] font-semibold bg-purple-50 text-purple-700 px-2 py-0.5 rounded border border-purple-200">
                            Review Required
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Title & Detected Snippet */}
                    <div>
                      <h3 className="font-semibold text-sm text-slate-900">{f.title}</h3>
                      <div className="mt-1 p-2 bg-red-50/50 border border-red-100 rounded text-xs text-red-900 font-mono">
                        "{f.detected_content}"
                      </div>
                    </div>

                    {/* Explanation */}
                    <p className="text-xs text-slate-600 leading-relaxed">{f.explanation}</p>

                    {/* Source Citation & Grounded Evidence */}
                    {f.source_citation && (
                      <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-lg space-y-1">
                        <div className="flex items-center space-x-1.5 text-xs font-semibold text-blue-900">
                          <BookOpen className="w-3.5 h-3.5 text-blue-700 shrink-0" />
                          <span>Cited Source: {f.source_citation}</span>
                        </div>
                        {f.supporting_passage && (
                          <p className="text-xs text-blue-800 italic pl-5">
                            "{f.supporting_passage}"
                          </p>
                        )}
                      </div>
                    )}

                    {/* Suggested Correction */}
                    {f.suggested_correction && (
                      <div className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-lg space-y-1">
                        <div className="text-xs font-semibold text-emerald-900">
                          Suggested Intent-Safe Correction:
                        </div>
                        <p className="text-xs text-emerald-800 font-medium">
                          {f.suggested_correction}
                        </p>
                      </div>
                    )}

                    {/* Recorded Decision Banner if already decided */}
                    {decision && (
                      <div
                        className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
                          decision.decision === "ACCEPTED"
                            ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                            : decision.decision === "EDITED"
                            ? "bg-blue-50 border-blue-200 text-blue-800"
                            : "bg-amber-50 border-amber-200 text-amber-800"
                        }`}
                      >
                        <div>
                          <strong className="uppercase">{decision.decision}</strong>
                          {decision.custom_edit && <span>: "{decision.custom_edit}"</span>}
                          {decision.rejection_reason && <span> (Reason: {decision.rejection_reason})</span>}
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {new Date(decision.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                    )}

                    {/* Human Decision Action Buttons (Only allowed if not approved) */}
                    {!isApproved && (
                      <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                        <button
                          onClick={() => handleAcceptFinding(f)}
                          disabled={actionLoading}
                          className="inline-flex items-center space-x-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-xs disabled:opacity-50"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Accept Fix</span>
                        </button>
                        <button
                          onClick={() => {
                            setActiveEditFinding(f);
                            setCustomEditText(f.suggested_correction || f.detected_content);
                          }}
                          disabled={actionLoading}
                          className="inline-flex items-center space-x-1 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 transition"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          <span>Edit</span>
                        </button>
                        <button
                          onClick={() => {
                            setActiveRejectFinding(f);
                            setRejectionReason("");
                          }}
                          disabled={actionLoading}
                          className="inline-flex items-center space-x-1 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-red-50 hover:text-red-700 text-slate-600 transition"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Custom Edit Modal */}
      {activeEditFinding && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-slate-900">Custom Edit Suggestion</h3>
              <button onClick={() => setActiveEditFinding(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Provide manual correction text for rule <strong>{activeEditFinding.rule_id}</strong>.
            </p>
            <textarea
              rows={4}
              value={customEditText}
              onChange={(e) => setCustomEditText(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 font-mono focus:outline-none focus:border-blue-600"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setActiveEditFinding(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCustomEdit}
                disabled={actionLoading}
                className="px-4 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-lg shadow-xs"
              >
                Save Custom Edit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject with Reason Modal */}
      {activeRejectFinding && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-slate-900">Reject Finding Exception</h3>
              <button onClick={() => setActiveRejectFinding(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Mandatory reason required for rejecting rule <strong>{activeRejectFinding.rule_id}</strong>. This feeds guideline ambiguity telemetry.
            </p>
            <textarea
              rows={3}
              placeholder="e.g. Campaign exception approved by Brand Director for satire promotion."
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 focus:outline-none focus:border-blue-600"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setActiveRejectFinding(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveRejection}
                disabled={actionLoading}
                className="px-4 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg shadow-xs"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Escalate Modal */}
      {escalateModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-purple-900 flex items-center space-x-1.5">
                <AlertTriangle className="w-4 h-4 text-purple-700" />
                <span>Escalate for Senior Review</span>
              </h3>
              <button onClick={() => setEscalateModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Transfer this submission to the Brand Lead or Legal Counsel queue.
            </p>
            <textarea
              rows={3}
              placeholder="Reason for escalation (e.g. Unverified claim in Section 2 requires legal counsel clearance)..."
              value={escalateReason}
              onChange={(e) => setEscalateReason(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 focus:outline-none focus:border-purple-600"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setEscalateModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleEscalate}
                disabled={actionLoading}
                className="px-4 py-1.5 bg-purple-700 hover:bg-purple-800 text-white text-xs font-semibold rounded-lg shadow-xs"
              >
                Escalate Submission
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sign-Off Modal */}
      {signOffModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-slate-900">
                {signOffModalOpen === "approve" ? "Sign Off & Approve Content" : "Reject Submission"}
              </h3>
              <button onClick={() => setSignOffModalOpen(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {signOffModalOpen === "approve" && unresolvedHigh.length > 0 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 space-y-1">
                <strong>Policy Guardrail Block:</strong>
                <p>
                  Cannot approve: {unresolvedHigh.length} High-severity finding(s) have not been resolved by the creator.
                </p>
              </div>
            )}

            <p className="text-xs text-slate-500">
              Optional sign-off notes or compliance certification commentary:
            </p>
            <textarea
              rows={3}
              placeholder="e.g. Verified against Q1 Brand Guidelines. Approved for press release syndication."
              value={signOffNotes}
              onChange={(e) => setSignOffNotes(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-800 focus:outline-none focus:border-blue-600"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setSignOffModalOpen(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => handleSignOff(signOffModalOpen === "approve")}
                disabled={actionLoading || (signOffModalOpen === "approve" && unresolvedHigh.length > 0)}
                className={`px-4 py-1.5 text-white text-xs font-semibold rounded-lg shadow-xs disabled:opacity-50 ${
                  signOffModalOpen === "approve" ? "bg-emerald-600 hover:bg-emerald-700" : "bg-red-600 hover:bg-red-700"
                }`}
              >
                {signOffModalOpen === "approve" ? "Approve & Lock Version" : "Reject Submission"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Certificate Modal */}
      {exportCert && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2 text-emerald-700">
                <Award className="w-5 h-5" />
                <h3 className="font-bold text-base text-slate-900">BrandSentinel Compliance Seal</h3>
              </div>
              <button onClick={() => setExportCert(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Certificate Header Banner */}
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono font-bold text-emerald-900">{exportCert.certificate_id}</span>
                <span className="px-2 py-0.5 rounded bg-emerald-600 text-white font-bold text-[10px] tracking-wider uppercase">
                  {exportCert.approval_status}
                </span>
              </div>
              <h4 className="text-base font-bold text-emerald-950">{exportCert.title}</h4>
              <p className="text-xs text-emerald-800">
                Organization: {exportCert.organization} • Channel: {exportCert.target_channel}
              </p>
              <div className="pt-2 text-[11px] text-emerald-900 flex items-center justify-between border-t border-emerald-200">
                <span>Signed by: <strong>{exportCert.signed_by}</strong> ({exportCert.signee_role})</span>
                <span>Timestamp: {new Date(exportCert.approval_timestamp).toLocaleString()}</span>
              </div>
            </div>

            {/* Compliance Scores & Findings */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="text-slate-500 font-medium">Compliance Index</div>
                <div className="text-xl font-black text-slate-900">{exportCert.brand_compliance_score} / 100</div>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="text-slate-500 font-medium">Resolved Findings</div>
                <div className="text-xl font-black text-slate-900">{exportCert.resolved_findings_count} Audit Items</div>
              </div>
            </div>

            {/* Approved Immutable Content */}
            <div className="space-y-1.5">
              <div className="text-xs font-semibold text-slate-700">Certified Content Copy:</div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-xs text-slate-800 whitespace-pre-wrap max-h-48 overflow-y-auto">
                {exportCert.final_approved_content}
              </div>
            </div>

            <p className="text-[11px] text-slate-400 italic text-center">
              "{exportCert.governance_notice}"
            </p>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(exportCert, null, 2)], {
                    type: "application/json",
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `${exportCert.certificate_id}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold rounded-lg shadow-xs"
              >
                <FileDown className="w-3.5 h-3.5" />
                <span>Download Digital Seal (.JSON)</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
