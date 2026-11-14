"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart3,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  Layers,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { AnalyticsDashboard } from "@/lib/types";

export default function InsightsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAnalyticsDashboard();
      setData(res);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load governance insights");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-slate-500 font-medium animate-pulse">
          Aggregating governance intelligence from database...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-center">
        <AlertCircle className="w-8 h-8 text-red-600 mx-auto mb-2" />
        <h3 className="font-semibold text-red-900">Unable to load insights</h3>
        <p className="text-sm text-red-700 mt-1">{error}</p>
        <button
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg shadow-xs"
        >
          Retry
        </button>
      </div>
    );
  }

  const { overview, violations_by_category, violations_by_severity, top_violated_rules, creator_actions, guideline_ambiguity_ranking, recent_activity } = data;

  const totalViolations = Object.values(violations_by_category).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-blue-700">
          <Sparkles className="w-4 h-4" />
          <span>Continuous Governance Telemetry</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mt-1">Governance Insights & Ambiguity Radar</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Real-time metrics, recurring brand drift, creator adoption rates, and guideline clarity intelligence.
        </p>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Compliance Score</div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-900">{overview.average_compliance_score}</span>
            <span className="text-xs text-slate-500 font-medium">/ 100</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Calculated across all audited versions</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Approved Content</div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-emerald-600">{overview.approved_submissions}</span>
            <span className="text-xs text-slate-500 font-medium">of {overview.total_submissions} total</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Locked and certified for publication</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Review Queue</div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-amber-600">{overview.in_review_queue}</span>
            <span className="text-xs text-slate-500 font-medium">pending sign-off</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">In review or escalated for legal check</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Creator Acceptance</div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-blue-700">{creator_actions.acceptance_rate_pct}%</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">{creator_actions.accepted} accepted, {creator_actions.edited} edited</p>
        </div>
      </div>

      {/* Two-Column Middle Section: Violations by Category & Creator Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Violations by Category */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-blue-600" />
              <span>Violations by Category ({totalViolations} Total Detected)</span>
            </h2>
            <span className="text-xs text-slate-400">Deterministic + RAG + Vision</span>
          </div>

          {Object.keys(violations_by_category).length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">No violation data available yet.</div>
          ) : (
            <div className="space-y-3">
              {Object.entries(violations_by_category).map(([cat, count]) => {
                const pct = totalViolations > 0 ? Math.round((count / totalViolations) * 100) : 0;
                return (
                  <div key={cat} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-700">{cat}</span>
                      <span className="text-slate-500">{count} ({pct}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Severity Breakdown Badges */}
          <div className="pt-3 border-t border-slate-100 flex items-center space-x-4 text-xs">
            <span className="text-slate-500 font-medium">By Severity:</span>
            <span className="px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200 font-semibold">
              HIGH: {violations_by_severity["HIGH"] || 0}
            </span>
            <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-semibold">
              MEDIUM: {violations_by_severity["MEDIUM"] || 0}
            </span>
            <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
              LOW: {violations_by_severity["LOW"] || 0}
            </span>
          </div>
        </div>

        {/* Creator Actions & Decision Telemetry */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <span>Human Decision Telemetry</span>
            </h2>
            <span className="text-xs text-slate-400">AI Suggests. Humans Decide.</span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center pt-2">
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
              <div className="text-2xl font-bold text-emerald-700">{creator_actions.accepted}</div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-emerald-800 mt-1">Accepted</div>
            </div>
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">{creator_actions.edited}</div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-blue-800 mt-1">Custom Edited</div>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="text-2xl font-bold text-amber-700">{creator_actions.rejected}</div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-amber-800 mt-1">Rejected</div>
            </div>
          </div>

          <p className="text-xs text-slate-500 leading-relaxed pt-2">
            BrandSentinel never automatically overwrites content. Suggestions accepted directly or custom-edited indicate high AI suggestion relevance. Rejections are fed back into guideline ambiguity detection.
          </p>
        </div>
      </div>

      {/* Guideline Ambiguity Radar & Top Violated Rules */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Ambiguity Radar */}
        <div className="lg:col-span-6 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
              <HelpCircle className="w-4 h-4 text-purple-600" />
              <span>Guideline Ambiguity Ranking</span>
            </h2>
            <span className="text-xs text-purple-700 font-medium">Repeated Creator Rejections</span>
          </div>

          {guideline_ambiguity_ranking.length === 0 ? (
            <div className="p-6 text-center text-slate-400 text-xs">
              <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto mb-1" />
              No ambiguous guidelines flagged. High creator consensus across active rules.
            </div>
          ) : (
            <div className="space-y-3">
              {guideline_ambiguity_ranking.map((item, idx) => (
                <div key={idx} className="p-3 bg-purple-50/50 border border-purple-200 rounded-lg space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-semibold text-purple-900">{item.rule_id}</span>
                    <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-bold">
                      {item.rejections} Rejections
                    </span>
                  </div>
                  <div className="text-xs text-slate-600 font-medium">Source: {item.source_citation}</div>
                  <p className="text-xs text-purple-900 italic mt-1">{item.insight}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Violated Rules */}
        <div className="lg:col-span-6 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Top Violated Brand Rules</span>
            </h2>
            <span className="text-xs text-slate-400">Training Opportunity Areas</span>
          </div>

          {top_violated_rules.length === 0 ? (
            <div className="p-6 text-center text-slate-400 text-xs">No recurring violations recorded yet.</div>
          ) : (
            <div className="divide-y divide-slate-100">
              {top_violated_rules.map((rule, idx) => (
                <div key={idx} className="py-2.5 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-semibold text-slate-800">{rule.title}</div>
                    <div className="text-[11px] font-mono text-slate-400">{rule.rule_id}</div>
                  </div>
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {rule.frequency} hits
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Live Governance Audit Log Feed */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
            <Clock className="w-4 h-4 text-slate-500" />
            <span>Recent Governance Activity Stream</span>
          </h2>
          <span className="text-xs text-slate-400">Immutable Audit Trail</span>
        </div>

        {recent_activity.length === 0 ? (
          <div className="p-4 text-center text-slate-400 text-xs">No audit activity recorded yet.</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recent_activity.map((log) => (
              <div key={log.id} className="py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3">
                  <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-slate-700 font-semibold text-[11px]">
                    {log.event_type}
                  </span>
                  <span className="text-slate-600">
                    {log.entity_type} {log.details?.action ? `• ${log.details.action}` : ""} {log.details?.rule_id ? `(${log.details.rule_id})` : ""}
                  </span>
                </div>
                <span className="text-slate-400 font-mono text-[11px]">
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
