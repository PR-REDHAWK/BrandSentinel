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
  ShieldCheck,
  Scale,
  Sparkles,
  Cpu,
  Eye,
  Award,
  Layers,
  BarChart3,
  Lock,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { ApprovedFact, Guideline, Submission } from "@/lib/types";
import { ScrollFadeNarrative } from "@/components/landing/ScrollFadeNarrative";
import { InteractiveHoverInspector } from "@/components/landing/InteractiveHoverInspector";
import { ScrollReveal } from "@/components/ui/ScrollReveal";

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
        <div className="text-slate-500 font-medium animate-pulse flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-blue-600 animate-spin" />
          <span>Loading BrandSentinel...</span>
        </div>
      </div>
    );
  }

  // ==================== PUBLIC LANDING PAGE (UNAUTHENTICATED) ====================
  if (!user) {
    return (
      <div className="space-y-16 py-4">
        {/* Hero Section */}
        <ScrollReveal direction="up">
          <div className="max-w-4xl mx-auto text-center space-y-6 pt-4">
            <div className="inline-flex items-center space-x-2 bg-blue-50/80 border border-blue-200 text-blue-700 px-3.5 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider shadow-xs hover:scale-105 transition-transform duration-300">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
              <span>Pre-Publication Brand Governance Gate</span>
            </div>

            <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight sm:text-6xl leading-[1.15]">
              Brand Integrity Backed by{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-700 via-indigo-600 to-emerald-600">
                Audited Evidence.
              </span>
            </h1>

            <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
              Eliminate unverified marketing claims, banned slang, off-brand tone, and WCAG contrast failures before content reaches customers.
            </p>

            {/* Action Buttons with Hover Effects */}
            <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
              <Link
                href="/register"
                className="group relative inline-flex items-center space-x-2 overflow-hidden rounded-xl bg-blue-700 px-6 py-3.5 text-sm font-semibold text-white shadow-md transition-all duration-300 hover:bg-blue-800 hover:shadow-lg hover:-translate-y-0.5"
              >
                <span>Create Organization Account</span>
                <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
              </Link>

              <Link
                href="/login"
                className="inline-flex items-center space-x-2 rounded-xl border border-slate-300 bg-white px-6 py-3.5 text-sm font-semibold text-slate-700 shadow-xs transition-all duration-300 hover:bg-slate-50 hover:border-slate-400 hover:-translate-y-0.5"
              >
                <span>Sign In to Existing Tenant</span>
              </Link>
            </div>

            {/* Demo Credentials Pill */}
            <div className="pt-2">
              <span className="inline-block rounded-lg bg-slate-100 border border-slate-200 px-3 py-1.5 text-xs text-slate-600 font-mono">
                Demo Access: <strong className="text-slate-800">admin@acme.com</strong> • Password: <strong className="text-slate-800">Password123!</strong>
              </span>
            </div>
          </div>
        </ScrollReveal>

        {/* Feature 1: The Scroll-Fade Narrative Section */}
        {/* Text fades away when scrolling down and the next text fades into the page */}
        <ScrollFadeNarrative />

        {/* Feature 2: Interactive Live Audit Playground with Hover Text Animations */}
        <ScrollReveal direction="up" delay={50}>
          <div className="max-w-5xl mx-auto">
            <InteractiveHoverInspector />
          </div>
        </ScrollReveal>

        {/* Feature 3: Tri-Engine Architecture Cards with Hover-Lift */}
        <ScrollReveal direction="up" delay={100}>
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-center space-y-2">
              <div className="inline-flex items-center space-x-1.5 text-xs font-semibold text-blue-700 uppercase tracking-wider">
                <Cpu className="w-3.5 h-3.5" />
                <span>Three Coordinated Engines</span>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 sm:text-3xl">
                Unified Tri-Engine Auditing Pipeline
              </h2>
              <p className="text-sm text-slate-500 max-w-xl mx-auto">
                Every piece of submitted content is evaluated in parallel across deterministic syntax, grounded RAG semantics, and visual assets.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Engine A */}
              <div className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover-card-lift transition-all duration-300 hover:border-blue-300">
                <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold mb-4 group-hover:scale-110 transition-transform duration-300">
                  <Scale className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded uppercase tracking-wider">
                  Engine A
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-2">
                  Deterministic Rule Engine
                </h3>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Word-boundary banned slang scanning, glossary preferred terms, WCAG 2.2 relative luminance contrast calculation, and missing image alt-text.
                </p>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Latency: &lt; 5ms</span>
                  <span className="text-emerald-600 font-semibold">100% Deterministic</span>
                </div>
              </div>

              {/* Engine B */}
              <div className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover-card-lift transition-all duration-300 hover:border-blue-300">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold mb-4 group-hover:scale-110 transition-transform duration-300">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded uppercase tracking-wider">
                  Engine B
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-2">
                  RAG + LLM Grounding
                </h3>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Semantic retrieval across uploaded brand guidelines and approved facts. Bounds-checked percentage metrics, timeframe promises, and hyperbolic tone analysis.
                </p>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Hard Citation Gate</span>
                  <span className="text-emerald-600 font-semibold">Zero Hallucinations</span>
                </div>
              </div>

              {/* Engine C */}
              <div className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover-card-lift transition-all duration-300 hover:border-blue-300">
                <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold mb-4 group-hover:scale-110 transition-transform duration-300">
                  <Eye className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded uppercase tracking-wider">
                  Engine C
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-2">
                  Vision & OCR Engine
                </h3>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Dominant color extraction vs. approved hex palettes, logo aspect ratio distortion check, visual low-contrast text overlays, and dual-path Tesseract / Multimodal OCR.
                </p>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Logo & Color Integrity</span>
                  <span className="text-purple-600 font-semibold">Multimodal</span>
                </div>
              </div>
            </div>
          </div>
        </ScrollReveal>

        {/* Bottom Call-To-Action Banner */}
        <ScrollReveal direction="up" delay={150}>
          <div className="max-w-4xl mx-auto rounded-3xl bg-slate-900 p-8 sm:p-12 text-center text-white shadow-xl space-y-6">
            <div className="inline-flex items-center space-x-2 rounded-full bg-slate-800 border border-slate-700 px-3 py-1 text-xs text-blue-400">
              <Lock className="w-3.5 h-3.5" />
              <span>Strict Tenant Isolation & Data Governance</span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Ready to Protect Your Brand Reputation?
            </h2>

            <p className="text-sm text-slate-300 max-w-xl mx-auto leading-relaxed">
              Register your enterprise organization, upload your brand guidelines, and run your first tri-engine compliance audit in minutes.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
              <Link
                href="/register"
                className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 text-sm shadow-md transition-all duration-300 hover:scale-105"
              >
                <span>Get Started Now</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center space-x-2 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-200 font-semibold px-6 py-3 text-sm transition-all duration-300"
              >
                <span>Sign In to Demo Account</span>
              </Link>
            </div>
          </div>
        </ScrollReveal>
      </div>
    );
  }

  // ==================== AUTHENTICATED DASHBOARD ====================
  return (
    <div className="space-y-8">
      {/* Welcome Banner with Hover Highlights */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex items-center justify-between hover-card-lift">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-slate-900">
              Welcome back, {user.full_name}
            </h1>
            <span className="text-xs bg-emerald-50 text-emerald-700 font-semibold px-2 py-0.5 rounded-full border border-emerald-200">
              Active Session
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Enterprise Tenant: <span className="font-semibold text-slate-800">{user.organization?.name}</span> • Role: <span className="font-mono text-blue-700 font-semibold">{user.role}</span>
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/knowledge"
            className="inline-flex items-center space-x-2 border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-medium px-4 py-2 rounded-xl transition duration-200 shadow-xs hover:border-slate-400"
          >
            <BookOpen className="w-4 h-4 text-slate-500" />
            <span>Manage Brand Hub</span>
          </Link>
          <Link
            href="/submissions"
            className="inline-flex items-center space-x-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium px-4 py-2 rounded-xl shadow-xs transition duration-200 hover:scale-105"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Submission</span>
          </Link>
        </div>
      </div>

      {/* Metrics Row with Interactive Hover Effects */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <Link
          href="/knowledge"
          className="group bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover-card-lift block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider group-hover:text-blue-700 transition-colors">
              Brand Guidelines
            </span>
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 mt-3">{guidelines.length}</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center justify-between">
            <span>Uploaded & indexed</span>
            <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-blue-600" />
          </div>
        </Link>

        <Link
          href="/knowledge"
          className="group bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover-card-lift block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider group-hover:text-emerald-700 transition-colors">
              Approved Facts
            </span>
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center group-hover:scale-110 group-hover:bg-emerald-600 group-hover:text-white transition-all duration-300">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 mt-3">{facts.length}</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center justify-between">
            <span>Audited source truths</span>
            <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-emerald-600" />
          </div>
        </Link>

        <Link
          href="/submissions"
          className="group bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover-card-lift block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider group-hover:text-purple-700 transition-colors">
              Submissions
            </span>
            <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center group-hover:scale-110 group-hover:bg-purple-600 group-hover:text-white transition-all duration-300">
              <FileCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 mt-3">{submissions.length}</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center justify-between">
            <span>In review queue</span>
            <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-purple-600" />
          </div>
        </Link>

        <Link
          href="/insights"
          className="group bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover-card-lift block"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider group-hover:text-amber-700 transition-colors">
              Governance Gate
            </span>
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center group-hover:scale-110 group-hover:bg-amber-600 group-hover:text-white transition-all duration-300">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 mt-3">100%</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center justify-between">
            <span>Evidence-backed policy</span>
            <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-amber-600" />
          </div>
        </Link>
      </div>

      {/* Quick View Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Guidelines List */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4 hover-card-lift">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-semibold text-slate-900 flex items-center space-x-2">
              <BookOpen className="w-4 h-4 text-blue-600" />
              <span>Active Brand Guidelines</span>
            </h2>
            <Link href="/knowledge" className="text-xs text-blue-700 hover:underline font-semibold">
              View All &rarr;
            </Link>
          </div>

          {guidelines.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              No guidelines uploaded yet. Upload your PDF/DOCX policy documents in the Knowledge Hub.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {guidelines.slice(0, 4).map((g) => (
                <div
                  key={g.id}
                  className="py-3 flex items-center justify-between hover:bg-slate-50/70 px-2 rounded-lg transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <FileText className="w-4 h-4 text-slate-400" />
                    <div>
                      <div className="font-medium text-sm text-slate-800">{g.title}</div>
                      <div className="text-xs text-slate-500 font-mono">
                        {g.file_type} • {g.chunk_count || 0} semantic chunks
                      </div>
                    </div>
                  </div>
                  <span className="text-xs bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded-full font-semibold border border-emerald-200">
                    ACTIVE
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Submissions */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4 hover-card-lift">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-semibold text-slate-900 flex items-center space-x-2">
              <FileCheck2 className="w-4 h-4 text-purple-600" />
              <span>Content Submissions</span>
            </h2>
            <Link href="/submissions" className="text-xs text-blue-700 hover:underline font-semibold">
              Review Queue &rarr;
            </Link>
          </div>

          {submissions.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              No content submitted for auditing yet. Create your first draft submission to run checks.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {submissions.slice(0, 4).map((s) => (
                <Link
                  key={s.id}
                  href={`/submissions/${s.id}`}
                  className="py-3 flex items-center justify-between hover:bg-slate-50/70 px-2 rounded-lg transition-colors group block"
                >
                  <div>
                    <div className="font-medium text-sm text-slate-800 group-hover:text-blue-700 transition-colors">
                      {s.title}
                    </div>
                    <div className="text-xs text-slate-500">
                      Channel: {s.target_channel || "General"}
                    </div>
                  </div>
                  <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                    {s.current_status}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
