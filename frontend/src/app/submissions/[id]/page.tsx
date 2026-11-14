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
  RefreshCw,
  Check,
  Edit3,
  X,
  Play,
  Clock,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { ContentVersion, Finding, Submission } from "@/lib/types";

export default function SubmissionAuditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();

  const [submission, setSubmission] = useState<Submission | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<ContentVersion | null>(null);
  const [loading, setLoading] = useState(true);
  const [auditing, setAuditing] = useState(false);

  const loadSubmission = async () => {
    setLoading(true);
    try {
      const data = await api.getSubmission(id);
      setSubmission(data);
      if (data.versions && data.versions.length > 0) {
        // Select latest version
        const latest = [...data.versions].sort((a, b) => b.version_number - a.version_number)[0];
        setSelectedVersion(latest);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && id) {
      loadSubmission();
    }
  }, [user, id]);

  const handleRunAudit = async () => {
    setAuditing(true);
    try {
      await api.runAudit(id, selectedVersion?.raw_content);
      await loadSubmission();
    } catch (err: any) {
      alert(err.message || "Audit failed");
    } finally {
      setAuditing(false);
    }
  };

  if (loading) {
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

  const scoreBadgeColor =
    score >= 85
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : score >= 70
      ? "bg-amber-50 text-amber-700 border-amber-200"
      : "bg-red-50 text-red-700 border-red-200";

  return (
    <div className="space-y-6">
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
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Version v{selectedVersion?.version_number || 1} • Status:{" "}
              <span className="font-semibold text-slate-800">{submission.current_status}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleRunAudit}
            disabled={auditing}
            className="flex items-center space-x-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-xs transition disabled:opacity-50"
          >
            <Play className={`w-4 h-4 ${auditing ? "animate-spin" : ""}`} />
            <span>{auditing ? "Auditing Content..." : "Run Tri-Engine Audit"}</span>
          </button>
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
        {/* Left Column: Draft Content */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
              <FileCheck2 className="w-4 h-4 text-slate-500" />
              <span>Submitted Copy</span>
            </h2>
            <span className="text-xs text-slate-400">Read-only draft view</span>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg font-mono text-xs text-slate-800 whitespace-pre-wrap leading-relaxed max-h-[600px] overflow-y-auto">
            {selectedVersion?.raw_content || "No raw content provided."}
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
                Click "Run Tri-Engine Audit" to re-evaluate after updating guidelines.
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

                    {/* Human Decision Buttons */}
                    <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                      <button
                        onClick={() => alert(`Accepted correction: "${f.suggested_correction}"`)}
                        className="inline-flex items-center space-x-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-xs"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Accept Fix</span>
                      </button>
                      <button
                        onClick={() => alert("Custom edit mode (Phase 3 Workflow)")}
                        className="inline-flex items-center space-x-1 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 transition"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Edit</span>
                      </button>
                      <button
                        onClick={() => alert("Rejection dialog (Phase 3 Workflow)")}
                        className="inline-flex items-center space-x-1 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-red-50 hover:text-red-700 text-slate-600 transition"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
