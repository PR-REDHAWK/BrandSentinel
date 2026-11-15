"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  ShieldCheck,
  Scale,
  UserCheck,
  Award,
  Sparkles,
  ArrowDown,
  Layers,
  CheckCircle2,
} from "lucide-react";

interface NarrativeStep {
  stepNumber: string;
  tag: string;
  title: string;
  headline: string;
  description: string;
  pillIcon: React.ElementType;
  accentColor: string;
  accentBg: string;
  badgeBorder: string;
  stats: { label: string; value: string };
}

const NARRATIVE_STEPS: NarrativeStep[] = [
  {
    stepNumber: "01",
    tag: "Grounding & RAG",
    title: "No Finding Without Evidence",
    headline: "Every claim must cite a verified truth. Zero hallucinated benchmarks.",
    description:
      "BrandSentinel's RAG grounding engine checks draft assertions against your approved enterprise knowledge base. If an efficiency or uptime claim exceeds the approved truth, it cites the exact auditor page and suggests a safe correction.",
    pillIcon: ShieldCheck,
    accentColor: "text-blue-600",
    accentBg: "bg-blue-500/10",
    badgeBorder: "border-blue-200",
    stats: { label: "Citation Integrity", value: "100%" },
  },
  {
    stepNumber: "02",
    tag: "Deterministic Precision",
    title: "Deterministic Rule Accuracy",
    headline: "Zero banned slang. Exact WCAG 2.2 Level AA contrast mathematics.",
    description:
      "Bypass fuzzy LLM estimations. High-speed regex token boundary scanners catch banned colloquialisms instantly, while mathematical relative-luminance algorithms enforce the 4.5:1 text contrast standard across inline styling.",
    pillIcon: Scale,
    accentColor: "text-amber-600",
    accentBg: "bg-amber-500/10",
    badgeBorder: "border-amber-200",
    stats: { label: "Benchmark Catch Rate", value: "95.8%" },
  },
  {
    stepNumber: "03",
    tag: "Human Authority",
    title: "AI Suggests. Humans Decide.",
    headline: "Zero automatic publishing. Complete editorial sovereignty.",
    description:
      "BrandSentinel never alters content without human consent. Creators review suggestions with 1-click Accept, Custom Edit, or Reject with reasons. Reviewers enforce strict sign-off policies on high-severity findings.",
    pillIcon: UserCheck,
    accentColor: "text-emerald-600",
    accentBg: "bg-emerald-500/10",
    badgeBorder: "border-emerald-200",
    stats: { label: "Editorial Control", value: "100% Human" },
  },
  {
    stepNumber: "04",
    tag: "Digital Compliance Seal",
    title: "Version-Locked Certification",
    headline: "Immutable digital compliance certificates ready for executive export.",
    description:
      "Approved content is sealed with an official BrandSentinel Compliance Certificate (`CERT-...`), capturing signee identity, approval timestamps, resolved findings summaries, and the tamper-proof final copy.",
    pillIcon: Award,
    accentColor: "text-purple-600",
    accentBg: "bg-purple-500/10",
    badgeBorder: "border-purple-200",
    stats: { label: "Compliance Provenance", value: "Cryptographic" },
  },
];

export function ScrollFadeNarrative() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;

      // Calculate how far through this section the user has scrolled
      const totalDist = rect.height - windowHeight;
      if (totalDist <= 0) return;

      const currentScroll = -rect.top;
      const progress = Math.min(Math.max(currentScroll / totalDist, 0), 1);
      setScrollProgress(progress);

      // Determine active narrative index (0 to 3)
      const index = Math.min(
        Math.floor(progress * NARRATIVE_STEPS.length),
        NARRATIVE_STEPS.length - 1
      );
      setActiveStep(index);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const currentData = NARRATIVE_STEPS[activeStep];
  const Icon = currentData.pillIcon;

  return (
    <section
      ref={containerRef}
      className="relative min-h-[260vh] bg-gradient-to-b from-slate-50 via-slate-100/70 to-slate-50 py-12"
    >
      {/* Sticky Viewport Stage */}
      <div className="sticky top-20 flex min-h-[75vh] items-center justify-center px-4 sm:px-6">
        <div className="w-full max-w-5xl">
          {/* Section Header */}
          <div className="mb-6 text-center">
            <div className="inline-flex items-center space-x-2 rounded-full border border-blue-200 bg-white px-3 py-1 shadow-xs">
              <Sparkles className="h-3.5 w-3.5 text-blue-600 animate-pulse" />
              <span className="text-xs font-semibold tracking-wide text-blue-700 uppercase">
                Continuous Governance Narrative
              </span>
            </div>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              The Architecture of Brand Integrity
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Scroll down to explore how BrandSentinel protects your enterprise reputation
            </p>
          </div>

          {/* Interactive Navigation Steps & Progress Bar */}
          <div className="mb-6 flex items-center justify-center space-x-2 sm:space-x-4">
            {NARRATIVE_STEPS.map((step, idx) => {
              const isActive = activeStep === idx;
              const isPast = activeStep > idx;

              return (
                <button
                  key={step.stepNumber}
                  onClick={() => {
                    setActiveStep(idx);
                    if (containerRef.current) {
                      const rect = containerRef.current.getBoundingClientRect();
                      const scrollTop = window.scrollY || document.documentElement.scrollTop;
                      const target =
                        scrollTop +
                        rect.top +
                        (idx / NARRATIVE_STEPS.length) * (rect.height - window.innerHeight);
                      window.scrollTo({ top: target, behavior: "smooth" });
                    }
                  }}
                  className={`group relative flex items-center space-x-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all duration-300 ${
                    isActive
                      ? "bg-white text-slate-900 shadow-md ring-2 ring-blue-600 scale-105"
                      : isPast
                      ? "bg-slate-200/80 text-slate-700 hover:bg-slate-300/80"
                      : "bg-white/60 text-slate-400 hover:bg-white hover:text-slate-600"
                  }`}
                >
                  <span
                    className={`font-mono text-[11px] ${
                      isActive ? "text-blue-600 font-bold" : "text-slate-400"
                    }`}
                  >
                    {step.stepNumber}
                  </span>
                  <span className="hidden sm:inline">{step.tag}</span>
                  {isPast && <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />}
                </button>
              );
            })}
          </div>

          {/* Progress Indicator Line */}
          <div className="mx-auto mb-8 h-1 max-w-xs overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full bg-blue-600 transition-all duration-200 ease-out"
              style={{ width: `${Math.round(scrollProgress * 100)}%` }}
            />
          </div>

          {/* Dynamic Scroll-Fade Text Stage with Hover Interaction */}
          <div
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={`group relative overflow-hidden rounded-3xl border border-slate-200/90 bg-white/95 p-8 sm:p-12 shadow-xl backdrop-blur-md transition-all duration-500 ${
              isHovered ? "shadow-2xl ring-2 ring-blue-500/20 -translate-y-1" : ""
            }`}
          >
            {/* Subtle Gradient Glow Backdrop */}
            <div
              className={`pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full blur-3xl transition-opacity duration-700 ${
                activeStep === 0
                  ? "bg-blue-400/15"
                  : activeStep === 1
                  ? "bg-amber-400/15"
                  : activeStep === 2
                  ? "bg-emerald-400/15"
                  : "bg-purple-400/15"
              }`}
            />

            {/* Stage Tag and Stats */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-2">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-lg ${currentData.accentBg} ${currentData.accentColor} transition-transform duration-300 group-hover:scale-110`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div>
                  <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-slate-400">
                    Stage {currentData.stepNumber} • {currentData.tag}
                  </span>
                  <h3 className="text-sm font-semibold text-slate-800">
                    {currentData.title}
                  </h3>
                </div>
              </div>

              {/* Dynamic Metric Pill */}
              <div className="text-right">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                  {currentData.stats.label}
                </span>
                <span className={`text-base font-extrabold ${currentData.accentColor}`}>
                  {currentData.stats.value}
                </span>
              </div>
            </div>

            {/* Fading Headline & Narrative Text */}
            <div className="relative mt-6 min-h-[160px]">
              {NARRATIVE_STEPS.map((step, idx) => {
                const isCurrent = activeStep === idx;
                return (
                  <div
                    key={step.stepNumber}
                    className={`transition-all duration-700 ease-out ${
                      isCurrent
                        ? "relative opacity-100 translate-y-0 pointer-events-auto"
                        : "absolute inset-0 opacity-0 -translate-y-4 pointer-events-none"
                    }`}
                  >
                    <h4 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl leading-snug">
                      "{step.headline}"
                    </h4>

                    <p className="mt-4 text-sm leading-relaxed text-slate-600 sm:text-base">
                      {step.description}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Interactive Scroll Prompt Footer */}
            <div className="mt-8 flex items-center justify-between pt-4 border-t border-slate-100 text-xs text-slate-400">
              <div className="flex items-center space-x-1.5">
                <Layers className="h-3.5 w-3.5 text-blue-600" />
                <span>Scroll down to advance next pillar</span>
              </div>
              <div className="flex items-center space-x-1 text-slate-500 font-mono text-[11px]">
                <ArrowDown className="h-3.5 w-3.5 animate-bounce text-blue-600" />
                <span>{(scrollProgress * 100).toFixed(0)}% Scrolled</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
