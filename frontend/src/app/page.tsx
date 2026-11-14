"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  FileCheck2,
  ShieldAlert,
  ArrowRight,
  PlusCircle,
  FileText,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { ApprovedFact, Guideline, Submission } from "@/lib/types";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const [guidelines, setGuidelines] = useState<Guideline[]>([]);
  const [facts, setFacts] = useState<ApprovedFact[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (user) {
      setFetching(true);
      Promise.all([api.listGuidelines(), api.listFacts(), api.listSubmissions()])
        .then(([gData, fData, sData]) => {
          setGuidelines(gData);
          setFacts(fData);
          setSubmissions(sData);
        })
        .catch((e) => console.error("Error fetching dashboard data:", e))
        .finally(() => setFetching(false));
    }
  }, [user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-slate-500 font-medium animate-pulse">Loading BrandSentinel...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center">
        <div className="inline-flex items-center space-x-2 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-6">
          Pre-Publication Governance Gate
        </div>
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight sm:text-5xl mb-4">
          Brand Integrity Backed by Real Evidence.
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
          BrandSentinel checks content before publication. Deterministic term scanning, RAG factual verification with cited sources, and multimodal visual analysis.
        </p>
        <div className="flex items-center justify-center space-x-4">
          <Link
            href="/register"
            className="bg-blue-700 hover:bg-blue-800 text-white font-medium px-6 py-3 rounded-lg shadow-sm transition inline-flex items-center space-x-2"
          >
            <span>Create Organization Account</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/login"
            className="border border-slate-300 hover:bg-slate-100 text-slate-700 font-medium px-6 py-3 rounded-lg transition"
          >
            Sign In to Existing Tenant
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Welcome back, {user.full_name}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Enterprise Tenant: <span className="font-semibold text-slate-800">{user.organization?.name}</span> • Role: <span className="font-mono text-blue-700 font-semibold">{user.role}</span>
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/knowledge"
            className="inline-flex items-center space-x-2 border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-medium px-4 py-2 rounded-lg transition"
          >
            <BookOpen className="w-4 h-4 text-slate-500" />
            <span>Manage Brand Hub</span>
          </Link>
          <Link
            href="/submissions"
            className="inline-flex items-center space-x-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium px-4 py-2 rounded-lg shadow-xs transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Submission</span>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Brand Guidelines
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-3">{guidelines.length}</div>
          <div className="text-xs text-slate-500 mt-1">Uploaded & indexed</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Approved Facts
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-3">{facts.length}</div>
          <div className="text-xs text-slate-500 mt-1">Audited source truths</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Submissions
            </span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center">
              <FileCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-3">{submissions.length}</div>
          <div className="text-xs text-slate-500 mt-1">In review queue</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Governance Gate
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold text-slate-900 mt-3">100%</div>
          <div className="text-xs text-slate-500 mt-1">Evidence-backed policy</div>
        </div>
      </div>

      {/* Quick View Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Guidelines List */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-semibold text-slate-900 flex items-center space-x-2">
              <BookOpen className="w-4 h-4 text-blue-600" />
              <span>Active Brand Guidelines</span>
            </h2>
            <Link href="/knowledge" className="text-xs text-blue-700 hover:underline">
              View All
            </Link>
          </div>

          {guidelines.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              No guidelines uploaded yet. Upload your PDF/DOCX policy documents in the Knowledge Hub.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {guidelines.slice(0, 4).map((g) => (
                <div key={g.id} className="py-3 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-4 h-4 text-slate-400" />
                    <div>
                      <div className="font-medium text-sm text-slate-800">{g.title}</div>
                      <div className="text-xs text-slate-500 font-mono">
                        {g.file_type} • {g.chunk_count || 0} semantic chunks
                      </div>
                    </div>
                  </div>
                  <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded font-medium">
                    ACTIVE
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Submissions */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-semibold text-slate-900 flex items-center space-x-2">
              <FileCheck2 className="w-4 h-4 text-purple-600" />
              <span>Content Submissions</span>
            </h2>
            <Link href="/submissions" className="text-xs text-blue-700 hover:underline">
              View All
            </Link>
          </div>

          {submissions.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              No content submitted for auditing yet. Create your first draft submission to run checks.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {submissions.slice(0, 4).map((s) => (
                <div key={s.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="font-medium text-sm text-slate-800">{s.title}</div>
                    <div className="text-xs text-slate-500">
                      Channel: {s.target_channel || "General"}
                    </div>
                  </div>
                  <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                    {s.current_status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
