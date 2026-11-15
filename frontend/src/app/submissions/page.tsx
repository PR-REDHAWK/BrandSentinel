"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PlusCircle, FileCheck2, Clock, Send, FileText, Sparkles } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Submission } from "@/lib/types";

export default function SubmissionsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(false);

  // New submission form
  const [title, setTitle] = useState("");
  const [targetChannel, setTargetChannel] = useState("Web");
  const [rawContent, setRawContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadSubmissions = async () => {
    setLoading(true);
    try {
      const data = await api.listSubmissions();
      setSubmissions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) loadSubmissions();
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !rawContent) return;
    setSubmitting(true);
    try {
      const created = await api.createSubmission({
        title,
        target_channel: targetChannel,
        raw_content: rawContent,
      });
      // Automatically execute the Tri-Engine audit immediately
      try {
        await api.runAudit(created.id, rawContent);
      } catch (auditErr) {
        console.warn("Audit execution warning:", auditErr);
      }
      router.push(`/submissions/${created.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to create draft submission");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Content Submissions & Audit Queue</h1>
        <p className="text-sm text-slate-500 mt-1">
          Draft submissions awaiting brand governance auditing, reviewer sign-off, or manager approval.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Submission Form */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h2 className="text-base font-semibold text-slate-900 mb-3 flex items-center space-x-2">
            <PlusCircle className="w-4 h-4 text-blue-600" />
            <span>Create Draft Submission</span>
          </h2>

          {/* Quick-Load Test Cases for Judges */}
          <div className="mb-4 p-3 bg-gradient-to-br from-blue-50 to-indigo-50/60 border border-blue-200/80 rounded-xl space-y-2">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-blue-900 uppercase">
              <Sparkles className="w-3.5 h-3.5 text-blue-600" />
              <span>Judge Quick-Test Samples</span>
            </div>
            <p className="text-[11px] text-blue-800/80">
              Click a sample to populate test violations and run the Tri-Engine audit:
            </p>
            <div className="flex flex-col space-y-1.5">
              <button
                type="button"
                onClick={() => {
                  setTitle("Acme Cloud 2026 Announcement");
                  setTargetChannel("Press");
                  setRawContent(
                    "We guarantee an unbelievable 100% cost reduction within 24 hours. Our dirt cheap tier delivers 99.999% uptime for every enterprise customer without exception."
                  );
                }}
                className="text-left px-2.5 py-1.5 bg-white hover:bg-blue-600 hover:text-white border border-blue-200 rounded-lg text-xs font-medium text-slate-700 transition flex items-center justify-between group"
              >
                <span>🧪 Sample 1: FTC Claim & Banned Slang</span>
                <span className="text-[10px] text-slate-400 group-hover:text-blue-100 font-mono">Load →</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setTitle("Acme Enterprise Promotion");
                  setTargetChannel("Social");
                  setRawContent(
                    "Switch to Acme now to cut infrastructure costs to nothing overnight! Our miraculous technology saves up to 80% immediately with zero setup required."
                  );
                }}
                className="text-left px-2.5 py-1.5 bg-white hover:bg-blue-600 hover:text-white border border-blue-200 rounded-lg text-xs font-medium text-slate-700 transition flex items-center justify-between group"
              >
                <span>🧪 Sample 2: Tone & Outdated Metric</span>
                <span className="text-[10px] text-slate-400 group-hover:text-blue-100 font-mono">Load →</span>
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Content Title
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Q3 Cloud Launch Press Release"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Target Publication Channel
              </label>
              <select
                value={targetChannel}
                onChange={(e) => setTargetChannel(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
              >
                <option value="Web">Website / Blog</option>
                <option value="Social">Social Media (LinkedIn, X)</option>
                <option value="Press">Press Release / Media</option>
                <option value="Ad">Paid Advertising & Banners</option>
                <option value="Internal">Internal Comms / Decks</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                Draft Content / Copy
              </label>
              <textarea
                required
                rows={6}
                value={rawContent}
                onChange={(e) => setRawContent(e.target.value)}
                placeholder="Paste the draft copy or marketing announcement here..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={submitting || !title || !rawContent}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium py-2 rounded-lg shadow-xs transition disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{submitting ? "Saving Draft..." : "Create Submission Draft"}</span>
            </button>
          </form>
        </div>

        {/* Submissions List */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h2 className="text-base font-semibold text-slate-900 mb-3">Review Queue</h2>
          {submissions.length === 0 ? (
            <p className="text-sm text-slate-400 py-6 text-center">No content submitted yet.</p>
          ) : (
            <div className="space-y-3">
              {submissions.map((s) => (
                <Link
                  key={s.id}
                  href={`/submissions/${s.id}`}
                  className="p-4 border border-slate-200 rounded-lg bg-slate-50 flex items-center justify-between hover:border-blue-400 hover:bg-blue-50/30 transition block"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-sm text-slate-900">{s.title}</span>
                      <span className="text-xs bg-slate-200 px-2 py-0.5 rounded text-slate-700">
                        {s.target_channel || "General"}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>Submitted on {new Date(s.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-blue-100 text-blue-800">
                      {s.current_status}
                    </span>
                    <span className="text-xs text-blue-700 font-semibold">Inspect Audit →</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
