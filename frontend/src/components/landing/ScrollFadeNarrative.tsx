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
      "BrandSentinel's RAG grounding engine checks draft assertions against your approved enterprise knowledge base. If an efficiency or uptime claim exceeds the approved truth, it cites the exact auditor page and suggests an intent-preserving correction.",
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
  const [activeStep, setActiveStep] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [animating, setAnimating] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  // Function to switch step with smooth fade transition
  const goToStep = (nextIndex: number) => {
    if (nextIndex === activeStep || animating) return;
    setAnimating(true);
    setActiveStep(nextIndex);
    setTimeout(() => setAnimating(false), 500);
  };

  // Next / Previous step helpers
  const nextStep = () => {
    goToStep((activeStep + 1) % NARRATIVE_STEPS.length);
  };

  const prevStep = () => {
    goToStep((activeStep - 1 + NARRATIVE_STEPS.length) % NARRATIVE_STEPS.length);
  };

  // Auto-advance narrative every 5 seconds (pauses when user is hovering)
  useEffect(() => {
    if (isHovered) return;
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % NARRATIVE_STEPS.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [isHovered]);

  // Scroll / Wheel detection on card: scrolling down advances to next text, scrolling up goes to previous text
  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    // Only capture vertical delta when hovering over the card
    if (Math.abs(e.deltaY) > 35) {
      if (e.deltaY > 0) {
        nextStep();
      } else {
        prevStep();
      }
    }
  };

  const currentData = NARRATIVE_STEPS[activeStep];
  const Icon = currentData.pillIcon;

  return (
    <section className="w-full max-w-5xl mx-auto py-8">
      {/* Section Header */}
      <div className="mb-6 text-center">
        <div className="inline-flex items-center space-x-2 rounded-full border border-blue-200 bg-white px-3.5 py-1 shadow-xs">
          <Sparkles className="h-3.5 w-3.5 text-blue-600 animate-pulse" />
          <span className="text-xs font-semibold tracking-wide text-blue-700 uppercase">
            Continuous Governance Narrative
          </span>
        </div>
        <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          The Architecture of Brand Integrity
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Hover over tabs or scroll down to watch core principles fade into focus
        </p>
      </div>

      {/* Interactive Tabs with Hover Activation */}
      <div className="mb-5 flex flex-wrap items-center justify-center gap-2 sm:gap-3">
        {NARRATIVE_STEPS.map((step, idx) => {
          const isActive = activeStep === idx;
          return (
            <button
              key={step.stepNumber}
              onMouseEnter={() => goToStep(idx)}
              onClick={() => goToStep(idx)}
              className={`group flex items-center space-x-2 rounded-xl px-4 py-2 text-xs font-semibold transition-all duration-300 ${
                isActive
                  ? "bg-white text-slate-900 shadow-md ring-2 ring-blue-600 scale-105"
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
              {isActive && <CheckCircle2 className="h-3.5 w-3.5 text-blue-600 animate-fadeIn" />}
            </button>
          );
        })}
      </div>

      {/* Main Dynamic Stage Card with Fade-Out / Fade-In and Hover Lift */}
      <div
        ref={cardRef}
        onWheel={handleWheel}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`group relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-7 sm:p-10 shadow-lg transition-all duration-500 hover:shadow-2xl hover:border-blue-300 ${
          isHovered ? "-translate-y-1" : ""
        }`}
      >
        {/* Subtle Ambient Color Glow */}
        <div
          className={`pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full blur-3xl transition-all duration-700 ${
            activeStep === 0
              ? "bg-blue-400/15"
              : activeStep === 1
              ? "bg-amber-400/15"
              : activeStep === 2
              ? "bg-emerald-400/15"
              : "bg-purple-400/15"
          }`}
        />

        {/* Card Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-3">
            <div
              className={`flex h-9 w-9 items-center justify-center rounded-xl ${currentData.accentBg} ${currentData.accentColor} transition-all duration-300 group-hover:scale-110`}
            >
              <Icon className="h-4.5 w-4.5" />
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

          {/* Metric Pill & Next/Prev Controls */}
          <div className="flex items-center space-x-3">
            <div className="text-right hidden sm:block">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                {currentData.stats.label}
              </span>
              <span className={`text-sm font-extrabold ${currentData.accentColor}`}>
                {currentData.stats.value}
              </span>
            </div>

            <div className="flex items-center space-x-1 border border-slate-200 rounded-lg p-0.5 bg-slate-50">
              <button
                onClick={prevStep}
                className="p-1 rounded hover:bg-white text-slate-500 hover:text-slate-800 transition"
                title="Previous text"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={nextStep}
                className="p-1 rounded hover:bg-white text-slate-500 hover:text-slate-800 transition"
                title="Next text"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Fade Away & Fade In Content Window */}
        <div className="relative mt-6 min-h-[140px] flex flex-col justify-center">
          {NARRATIVE_STEPS.map((step, idx) => {
            const isCurrent = activeStep === idx;
            return (
              <div
                key={step.stepNumber}
                className={`transition-all duration-500 ease-out ${
                  isCurrent
                    ? "relative opacity-100 translate-y-0 pointer-events-auto"
                    : "absolute inset-0 opacity-0 -translate-y-3 pointer-events-none"
                }`}
              >
                <h4 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 leading-snug">
                  "{step.headline}"
                </h4>

                <p className="mt-3 text-xs sm:text-sm leading-relaxed text-slate-600">
                  {step.description}
                </p>
              </div>
            );
          })}
        </div>

        {/* Animated Progress Bar at bottom of card */}
        <div className="mt-6 flex items-center justify-between pt-4 border-t border-slate-100 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Layers className="h-3.5 w-3.5 text-blue-600" />
            <span className="text-[11px]">
              {isHovered ? "Paused on hover" : "Auto-advancing narrative"}
            </span>
          </div>

          {/* Dots Indicator */}
          <div className="flex items-center space-x-1.5">
            {NARRATIVE_STEPS.map((_, dotIdx) => (
              <button
                key={dotIdx}
                onClick={() => goToStep(dotIdx)}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  activeStep === dotIdx ? "w-6 bg-blue-600" : "w-1.5 bg-slate-200 hover:bg-slate-300"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
