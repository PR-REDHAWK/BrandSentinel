"use client";

import React, { useState } from "react";
import {
  Sparkles,
  ShieldAlert,
  BookOpen,
  Check,
  AlertTriangle,
  HelpCircle,
  Eye,
} from "lucide-react";

interface HoverViolation {
  id: string;
  snippet: string;
  ruleId: string;
  engine: "DETERMINISTIC" | "RAG_LLM" | "VISION_OCR";
  severity: "HIGH" | "MEDIUM";
  title: string;
  explanation: string;
  citation: string;
  suggestedFix: string;
}

const SAMPLE_VIOLATIONS: Record<string, HoverViolation> = {
  slang: {
    id: "slang",
    snippet: "dirt cheap",
    ruleId: "RULE-01-BANNED-TERM",
    engine: "DETERMINISTIC",
    severity: "HIGH",
    title: "Banned Colloquial Vocabulary Detected",
    explanation:
      "The phrase 'dirt cheap' is strictly registered on the organization's banned vocabulary list as it devalues enterprise engineering credibility.",
    citation: "Acme Global Brand Manual v3.0, Section 4",
    suggestedFix: "cost-effective",
  },
  claim: {
    id: "claim",
    snippet: "guarantees 100% cloud cost reduction within 24 hours",
    ruleId: "RAG-01-CLAIM-EXAGGERATION",
    engine: "RAG_LLM",
    severity: "HIGH",
    title: "Exaggerated Performance Claim & Impossible Timeframe",
    explanation:
      "Draft claims 100% savings within 24 hours. The organization's verified benchmark states customers achieve up to 30% savings over six months.",
    citation: "Q4 2025 Financial & Tech Audit, p. 14",
    suggestedFix: "delivers up to 30% reduction in infrastructure costs within six months",
  },
  contrast: {
    id: "contrast",
    snippet: "Special Enterprise Launch Discount",
    ruleId: "RULE-03-WCAG-CONTRAST",
    engine: "DETERMINISTIC",
    severity: "HIGH",
    title: "WCAG 2.2 Contrast Failure (1.28:1 vs 4.5:1 Required)",
    explanation:
      "The contrast ratio between light gray foreground #888888 and background #959595 is 1.28:1, violating WCAG 2.2 Level AA accessibility standards.",
    citation: "W3C WCAG 2.2 Guideline 1.4.3 (Contrast Minimum)",
    suggestedFix: "Change foreground color to dark navy (#0B2046) to achieve a 10.4:1 contrast ratio",
  },
};

export function InteractiveHoverInspector() {
  const [activeHoverId, setActiveHoverId] = useState<string>("claim");

  const currentViolation = SAMPLE_VIOLATIONS[activeHoverId] || SAMPLE_VIOLATIONS.claim;

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
        <div className="flex items-center space-x-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
            <Eye className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Interactive Live Audit Playground
            </h3>
            <p className="text-xs text-slate-500">
              Hover over the highlighted snippets below to inspect real-time AI findings
            </p>
          </div>
        </div>
        <span className="hidden sm:inline-flex items-center space-x-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 border border-blue-200">
          <Sparkles className="h-3.5 w-3.5 animate-spin" />
          <span>Hover to Inspect</span>
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Draft Text with Hover Hotspots */}
        <div className="lg:col-span-7 space-y-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Submitted Draft Sample
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-5 font-mono text-xs text-slate-800 leading-relaxed space-y-3">
            <p className="font-bold text-slate-900 text-sm">
              Acme Cloud Platform — Q1 Promotional Launch
            </p>
            <p>
              Our upgraded cloud computing suite is{" "}
              <button
                onMouseEnter={() => setActiveHoverId("slang")}
                className={`cursor-pointer rounded px-1.5 py-0.5 font-bold transition-all duration-300 ${
                  activeHoverId === "slang"
                    ? "bg-red-500 text-white shadow-md scale-105"
                    : "bg-red-100 text-red-800 hover:bg-red-200"
                }`}
              >
                dirt cheap
              </button>{" "}
              and engineered for rapid scale.
            </p>
            <p>
              We{" "}
              <button
                onMouseEnter={() => setActiveHoverId("claim")}
                className={`cursor-pointer rounded px-1.5 py-0.5 font-bold transition-all duration-300 ${
                  activeHoverId === "claim"
                    ? "bg-red-500 text-white shadow-md scale-105"
                    : "bg-red-100 text-red-800 hover:bg-red-200"
                }`}
              >
                guarantee an unbelievable 100% cloud cost reduction within 24 hours
              </button>{" "}
              with zero migration downtime.
            </p>
            <div className="pt-2">
              <span className="text-[11px] text-slate-400 block mb-1">
                Embedded Promo Banner:
              </span>
              <button
                onMouseEnter={() => setActiveHoverId("contrast")}
                className={`cursor-pointer block w-full rounded p-2 text-center text-xs font-semibold transition-all duration-300 ${
                  activeHoverId === "contrast"
                    ? "ring-2 ring-red-500 shadow-md scale-[1.01]"
                    : "border border-slate-300"
                }`}
                style={{ color: "#888888", backgroundColor: "#959595" }}
              >
                Special Enterprise Launch Discount
              </button>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-[11px] text-slate-500">
            <HelpCircle className="h-3.5 w-3.5 text-slate-400" />
            <span>Hovering over each segment instantly fades the previous finding and loads the evidence.</span>
          </div>
        </div>

        {/* Right Column: Dynamic Finding Card with Fade Transition */}
        <div className="lg:col-span-5 flex flex-col justify-center">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Active Finding Card
          </div>

          <div className="relative min-h-[260px] rounded-2xl border border-slate-200 bg-white p-5 shadow-lg transition-all duration-500 hover:shadow-xl hover:border-blue-300">
            {/* Finding Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <span className="rounded bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-800 uppercase tracking-wider">
                  {currentViolation.severity}
                </span>
                <span className="font-mono text-xs font-semibold text-slate-700">
                  {currentViolation.ruleId}
                </span>
              </div>
              <span className="text-[11px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                {currentViolation.engine}
              </span>
            </div>

            {/* Finding Content with Smooth Fade Animation */}
            <div key={currentViolation.id} className="mt-3 space-y-3 animate-fadeIn">
              <div>
                <h4 className="text-xs font-bold text-slate-900">
                  {currentViolation.title}
                </h4>
                <p className="mt-1 text-xs text-slate-600 leading-relaxed">
                  {currentViolation.explanation}
                </p>
              </div>

              {/* Source Citation */}
              <div className="rounded-lg bg-blue-50/70 border border-blue-100 p-2.5 text-xs">
                <div className="flex items-center space-x-1.5 font-semibold text-blue-900 text-[11px]">
                  <BookOpen className="h-3.5 w-3.5 text-blue-700 shrink-0" />
                  <span>Ground Truth Source:</span>
                </div>
                <p className="mt-0.5 text-xs text-blue-800 italic pl-5">
                  {currentViolation.citation}
                </p>
              </div>

              {/* Suggested Correction */}
              <div className="rounded-lg bg-emerald-50/70 border border-emerald-100 p-2.5 text-xs">
                <div className="flex items-center space-x-1.5 font-semibold text-emerald-900 text-[11px]">
                  <Check className="h-3.5 w-3.5 text-emerald-700 shrink-0" />
                  <span>Suggested Correction:</span>
                </div>
                <p className="mt-0.5 text-xs text-emerald-800 font-medium pl-5">
                  "{currentViolation.suggestedFix}"
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
