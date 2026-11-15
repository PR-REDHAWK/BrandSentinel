"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  ShieldCheck,
  Scale,
  UserCheck,
  Award,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Layers,
  ArrowDown,
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
  accentBorder: string;
  stats: { label: string; value: string };
}

const NARRATIVE_STEPS: NarrativeStep[] = [
  {
    stepNumber: "01",
    tag: "Grounding & RAG",
    title: "No Finding Without Evidence",
    headline: "Every claim must cite a verified truth. Zero hallucinated benchmarks.",
    description:
      "BrandSentinel's RAG grounding engine checks draft assertions against your approved enterprise knowledge base. If an efficiency or uptime claim exceeds the approved truth, it cites the exact auditor page and suggests an intent-preserving correction.",
    pillIcon: ShieldCheck,
    accentColor: "text-blue-600",
    accentBg: "bg-blue-500/10",
    accentBorder: "border-blue-200",
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
    accentBorder: "border-amber-200",
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
    accentBorder: "border-emerald-200",
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
    accentBorder: "border-purple-200",
    stats: { label: "Compliance Provenance", value: "Cryptographic" },
  },
];

export function ScrollFadeNarrative() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  // Scroll listener that updates progress and active narrative step as user scrolls down the page
  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const stickyOffset = 88; // 5.5rem / top-20 to top-24

      // The scrollable distance through this section
      const totalScrollable = rect.height - windowHeight;
      if (totalScrollable <= 0) return;

      const currentScroll = stickyOffset - rect.top;
      const progress = Math.min(Math.max(currentScroll / totalScrollable, 0), 1);
      setScrollProgress(progress);

      // Determine active narrative index (0 to 3) based on scroll progress
      const stepIndex = Math.min(
        Math.floor(progress * NARRATIVE_STEPS.length),
        NARRATIVE_STEPS.length - 1
      );
      setActiveStep(stepIndex);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleScroll, { passive: true });
    handleScroll();

    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleScroll);
    };
  }, []);

  // Smooth scroll to a specific step when user clicks tabs or arrows
  const scrollToStep = (idx: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const stickyOffset = 88;
    const totalScrollable = rect.height - windowHeight;
    const targetProgress = (idx + 0.15) / NARRATIVE_STEPS.length;
    const targetScrollY = window.scrollY + rect.top - stickyOffset + targetProgress * totalScrollable;
    window.scrollTo({ top: targetScrollY, behavior: "smooth" });
    setActiveStep(idx);
  };

  const nextStep = () => {
    const nextIdx = (activeStep + 1) % NARRATIVE_STEPS.length;
    scrollToStep(nextIdx);
  };

  const prevStep = () => {
    const prevIdx = (activeStep - 1 + NARRATIVE_STEPS.length) % NARRATIVE_STEPS.length;
    scrollToStep(prevIdx);
  };

  const currentData = NARRATIVE_STEPS[activeStep];
  const Icon = currentData.pillIcon;

  return (
    <section className="w-full">
      {/* Section Header (placed outside the sticky container so it flows naturally) */}
      <div className="mb-8 text-center max-w-4xl mx-auto">
        <div className="inline-flex items-center space-x-2 rounded-full border border-blue-200 bg-white px-3.5 py-1 shadow-xs hover:scale-105 transition-transform duration-300">
          <Sparkles className="h-3.5 w-3.5 text-blue-600 animate-pulse" />
          <span className="text-xs font-semibold tracking-wide text-blue-700 uppercase">
            Continuous Governance Narrative
          </span>
        </div>
        <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
          The Architecture of Brand Integrity
        </h2>
        <p className="mt-2 text-sm text-slate-500 max-w-xl mx-auto">
          Scroll down to watch core principles fade away and the next principle fade into focus.
        </p>
      </div>

      {/* Scroll-Driven Sticky Track */}
      <div
        ref={containerRef}
        className="relative min-h-[170vh] sm:min-h-[185vh]"
      >
        {/* Sticky Viewport Stage: Locks at top-20 / top-24 and smoothly crossfades text */}
        <div className="sticky top-20 sm:top-24 z-10 w-full max-w-5xl mx-auto px-2">
          {/* Interactive Navigation Pills with Hover Lift & Direct Click */}
          <div className="mb-4 flex flex-wrap items-center justify-center gap-2 sm:gap-3">
            {NARRATIVE_STEPS.map((step, idx) => {
              const isActive = activeStep === idx;
              const isPast = activeStep > idx;
              return (
                <button
                  key={step.stepNumber}
                  onClick={() => scrollToStep(idx)}
                  className={`group flex items-center space-x-2 rounded-xl px-3.5 py-1.5 sm:px-4 sm:py-2 text-xs font-semibold transition-all duration-300 ${
                    isActive
                      ? "bg-white text-slate-900 shadow-md ring-2 ring-blue-600 scale-105 -translate-y-0.5"
                      : "bg-white/70 text-slate-500 hover:bg-white hover:text-slate-800 hover:shadow-xs hover:-translate-y-0.5"
                  }`}
                >
                  <span
                    className={`font-mono text-[11px] ${
                      isActive ? "text-blue-600 font-bold" : "text-slate-400 group-hover:text-blue-600"
                    }`}
                  >
                    {step.stepNumber}
                  </span>
                  <span>{step.tag}</span>
                  {isPast ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  ) : isActive ? (
                    <span className="h-2 w-2 rounded-full bg-blue-600 animate-ping" />
                  ) : null}
                </button>
              );
            })}
          </div>

          {/* Continuous Scroll Progress Bar */}
          <div className="mx-auto mb-6 h-1.5 max-w-md overflow-hidden rounded-full bg-slate-200/80 shadow-inner">
            <div
              className="h-full bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 transition-all duration-150 ease-out"
              style={{ width: `${Math.round(scrollProgress * 100)}%` }}
            />
          </div>

          {/* Dynamic Scroll-Fade Stage Card with Hover Lift & Ambient Glow */}
          <div
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={`group relative overflow-hidden rounded-3xl border border-slate-200/90 bg-white p-7 sm:p-10 shadow-xl transition-all duration-500 hover:shadow-2xl hover:border-blue-300 ${
              isHovered ? "-translate-y-1 ring-2 ring-blue-500/15" : ""
            }`}
          >
            {/* Dynamic Ambient Blur Glow changing color per active stage */}
            <div
              className={`pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full blur-3xl transition-all duration-700 ${
                activeStep === 0
                  ? "bg-blue-400/20"
                  : activeStep === 1
                  ? "bg-amber-400/20"
                  : activeStep === 2
                  ? "bg-emerald-400/20"
                  : "bg-purple-400/20"
              }`}
            />

            {/* Stage Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl ${currentData.accentBg} ${currentData.accentColor} transition-transform duration-300 group-hover:scale-110 shadow-xs`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-slate-400 block">
                    Pillar {currentData.stepNumber} • {currentData.tag}
                  </span>
                  <h3 className="text-sm font-bold text-slate-800">
                    {currentData.title}
                  </h3>
                </div>
              </div>

              {/* Metric Badge & Step Navigation Buttons */}
              <div className="flex items-center space-x-3">
                <div className="text-right hidden sm:block">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                    {currentData.stats.label}
                  </span>
                  <span className={`text-base font-extrabold ${currentData.accentColor}`}>
                    {currentData.stats.value}
                  </span>
                </div>

                <div className="flex items-center space-x-1 border border-slate-200 rounded-lg p-0.5 bg-slate-50">
                  <button
                    onClick={prevStep}
                    className="p-1 rounded hover:bg-white text-slate-500 hover:text-slate-800 transition shadow-xs"
                    title="Previous text (or scroll up)"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={nextStep}
                    className="p-1 rounded hover:bg-white text-slate-500 hover:text-slate-800 transition shadow-xs"
                    title="Next text (or scroll down)"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Dynamic Scroll-Fading Text Window:
                - Active text is fully visible (opacity 1, translateY 0)
                - Past text fades away upward (opacity 0, translateY -24px)
                - Future text is ready below (opacity 0, translateY 24px)
            */}
            <div className="relative mt-7 min-h-[150px] sm:min-h-[140px] flex flex-col justify-center overflow-hidden">
              {NARRATIVE_STEPS.map((step, idx) => {
                const isActive = activeStep === idx;
                const isPast = activeStep > idx;

                let stateClasses = "opacity-0 translate-y-6 pointer-events-none absolute inset-0";
                if (isActive) {
                  stateClasses = "opacity-100 translate-y-0 pointer-events-auto relative";
                } else if (isPast) {
                  stateClasses = "opacity-0 -translate-y-6 pointer-events-none absolute inset-0";
                }

                return (
                  <div
                    key={step.stepNumber}
                    className={`transition-all duration-500 cubic-bezier(0.16, 1, 0.3, 1) ${stateClasses}`}
                  >
                    <h4 className="text-xl sm:text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900 leading-snug">
                      "{step.headline}"
                    </h4>

                    <p className="mt-3.5 text-xs sm:text-sm md:text-base leading-relaxed text-slate-600">
                      {step.description}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Interactive Footer Toolbar */}
            <div className="mt-6 flex items-center justify-between pt-4 border-t border-slate-100 text-xs text-slate-400">
              <div className="flex items-center space-x-2 text-slate-500">
                <Layers className="h-3.5 w-3.5 text-blue-600" />
                <span className="text-[11px] font-medium hidden sm:inline">
                  Scroll down the page to crossfade narrative pillars
                </span>
                <span className="text-[11px] font-medium sm:hidden">
                  Scroll down to advance
                </span>
              </div>

              {/* Progress and Dots */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-1 font-mono text-[11px] text-blue-700 font-semibold bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
                  <ArrowDown className="h-3 w-3 animate-bounce" />
                  <span>{Math.round(scrollProgress * 100)}% Scrolled</span>
                </div>

                <div className="flex items-center space-x-1.5">
                  {NARRATIVE_STEPS.map((_, dotIdx) => (
                    <button
                      key={dotIdx}
                      onClick={() => scrollToStep(dotIdx)}
                      className={`h-2 rounded-full transition-all duration-300 ${
                        activeStep === dotIdx
                          ? "w-6 bg-blue-600"
                          : "w-2 bg-slate-200 hover:bg-slate-300"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
