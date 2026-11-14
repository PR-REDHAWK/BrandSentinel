"use client";

import React, { useEffect, useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  Palette,
  Upload,
  Plus,
  FileText,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { ApprovedFact, BrandAsset, GlossaryTerm, Guideline } from "@/lib/types";

export default function KnowledgePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"guidelines" | "facts" | "glossary" | "assets">("guidelines");

  const [guidelines, setGuidelines] = useState<Guideline[]>([]);
  const [facts, setFacts] = useState<ApprovedFact[]>([]);
  const [glossary, setGlossary] = useState<GlossaryTerm[]>([]);
  const [assets, setAssets] = useState<BrandAsset[]>([]);
  const [loading, setLoading] = useState(false);

  // Upload guideline state
  const [uploadTitle, setUploadTitle] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // New fact state
  const [newFact, setNewFact] = useState({
    category: "Performance",
    claim_pattern: "",
    approved_truth: "",
    mandatory_caveat: "",
    source_citation: "",
  });

  // New glossary state
  const [newGlossary, setNewGlossary] = useState({
    term: "",
    is_banned: true,
    preferred_term: "",
    definition_or_rule: "",
  });

  // New asset state
  const [newAsset, setNewAsset] = useState({
    asset_type: "PALETTE" as "PALETTE" | "LOGO",
    name: "",
    hex_colors: "#0B2046, #FF6B35, #FFFFFF",
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [g, f, gl, a] = await Promise.all([
        api.listGuidelines(),
        api.listFacts(),
        api.listGlossary(),
        api.listAssets(),
      ]);
      setGuidelines(g);
      setFacts(f);
      setGlossary(gl);
      setAssets(a);
    } catch (err) {
      console.error("Error loading knowledge data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user]);

  const handleGuidelineUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !uploadTitle) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("title", uploadTitle);
      formData.append("file", selectedFile);
      await api.uploadGuideline(formData);
      setUploadTitle("");
      setSelectedFile(null);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Guideline upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleCreateFact = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createFact(newFact);
      setNewFact({
        category: "Performance",
        claim_pattern: "",
        approved_truth: "",
        mandatory_caveat: "",
        source_citation: "",
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to create fact");
    }
  };

  const handleCreateGlossary = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createGlossary(newGlossary);
      setNewGlossary({
        term: "",
        is_banned: true,
        preferred_term: "",
        definition_or_rule: "",
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to add term");
    }
  };

  const handleCreateAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const colors = newAsset.hex_colors.split(",").map((c) => c.trim()).filter(Boolean);
      await api.createAsset({
        asset_type: newAsset.asset_type,
        name: newAsset.name,
        hex_colors: colors,
      });
      setNewAsset({ asset_type: "PALETTE", name: "", hex_colors: "#0B2046, #FF6B35, #FFFFFF" });
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to add asset");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Brand Knowledge Hub</h1>
          <p className="text-sm text-slate-500 mt-1">
            Single source of truth for guidelines, factual claims, glossary terms, and visual brand assets.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center space-x-1.5 text-xs text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded-lg hover:bg-slate-50 shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab("guidelines")}
          className={`flex items-center space-x-2 pb-3 px-3 text-sm font-medium border-b-2 transition ${
            activeTab === "guidelines"
              ? "border-blue-700 text-blue-700 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Guidelines ({guidelines.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("facts")}
          className={`flex items-center space-x-2 pb-3 px-3 text-sm font-medium border-b-2 transition ${
            activeTab === "facts"
              ? "border-blue-700 text-blue-700 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>Approved Facts ({facts.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("glossary")}
          className={`flex items-center space-x-2 pb-3 px-3 text-sm font-medium border-b-2 transition ${
            activeTab === "glossary"
              ? "border-blue-700 text-blue-700 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Glossary & Terms ({glossary.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("assets")}
          className={`flex items-center space-x-2 pb-3 px-3 text-sm font-medium border-b-2 transition ${
            activeTab === "assets"
              ? "border-blue-700 text-blue-700 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          <Palette className="w-4 h-4" />
          <span>Brand Assets ({assets.length})</span>
        </button>
      </div>

      {/* Tab 1: Guidelines */}
      {activeTab === "guidelines" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-3 flex items-center space-x-2">
              <Upload className="w-4 h-4 text-blue-600" />
              <span>Upload Guideline</span>
            </h2>
            <form onSubmit={handleGuidelineUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Document Title
                </label>
                <input
                  type="text"
                  required
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="e.g. Acme Brand Guide 2026"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  File (PDF or DOCX)
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>

              <button
                type="submit"
                disabled={uploading || !selectedFile}
                className="w-full bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium py-2 rounded-lg shadow-xs transition disabled:opacity-50"
              >
                {uploading ? "Ingesting & Chunking..." : "Ingest Document"}
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-3">Ingested Guidelines</h2>
            {guidelines.length === 0 ? (
              <p className="text-sm text-slate-400 py-6 text-center">No guidelines uploaded yet.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {guidelines.map((g) => (
                  <div key={g.id} className="py-3.5 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-blue-700" />
                      <div>
                        <div className="font-medium text-sm text-slate-800">{g.title}</div>
                        <div className="text-xs text-slate-500 font-mono">
                          Format: {g.file_type} • Chunks: {g.chunk_count || 0} indexed
                        </div>
                      </div>
                    </div>
                    <span className="text-xs font-medium bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      Active Index
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Approved Facts */}
      {activeTab === "facts" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-3 flex items-center space-x-2">
              <Plus className="w-4 h-4 text-emerald-600" />
              <span>Add Approved Fact</span>
            </h2>
            <form onSubmit={handleCreateFact} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Category
                </label>
                <input
                  type="text"
                  required
                  value={newFact.category}
                  onChange={(e) => setNewFact({ ...newFact, category: e.target.value })}
                  placeholder="Performance, Pricing, Metrics"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Governed Claim / Pattern
                </label>
                <input
                  type="text"
                  required
                  value={newFact.claim_pattern}
                  onChange={(e) => setNewFact({ ...newFact, claim_pattern: e.target.value })}
                  placeholder="e.g. Infrastructure cost savings"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Approved Truth (Exact Wording)
                </label>
                <textarea
                  required
                  rows={3}
                  value={newFact.approved_truth}
                  onChange={(e) => setNewFact({ ...newFact, approved_truth: e.target.value })}
                  placeholder="e.g. Customers achieve up to 30% reduction in infrastructure costs within six months."
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Mandatory Caveat / Condition
                </label>
                <input
                  type="text"
                  value={newFact.mandatory_caveat}
                  onChange={(e) => setNewFact({ ...newFact, mandatory_caveat: e.target.value })}
                  placeholder="e.g. Over deployments of 500+ seats"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Source Citation (Mandatory)
                </label>
                <input
                  type="text"
                  required
                  value={newFact.source_citation}
                  onChange={(e) => setNewFact({ ...newFact, source_citation: e.target.value })}
                  placeholder="e.g. Q4 2025 Auditor Report, p. 12"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-medium py-2 rounded-lg shadow-xs transition"
              >
                Save Approved Fact
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-3">Verified Organization Truths</h2>
            {facts.length === 0 ? (
              <p className="text-sm text-slate-400 py-6 text-center">No approved facts registered yet.</p>
            ) : (
              <div className="space-y-3">
                {facts.map((f) => (
                  <div key={f.id} className="p-3.5 border border-slate-200 rounded-lg bg-slate-50 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                        {f.category}
                      </span>
                      <span className="text-xs font-mono text-slate-500">{f.source_citation}</span>
                    </div>
                    <div className="font-semibold text-slate-900 text-sm">{f.approved_truth}</div>
                    {f.mandatory_caveat && (
                      <div className="text-xs text-amber-800 bg-amber-50 p-1.5 rounded border border-amber-200">
                        Caveat: {f.mandatory_caveat}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Glossary */}
      {activeTab === "glossary" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-3 flex items-center space-x-2">
              <Plus className="w-4 h-4 text-blue-600" />
              <span>Add Term Rule</span>
            </h2>
            <form onSubmit={handleCreateGlossary} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Term / Phrase
                </label>
                <input
                  type="text"
                  required
                  value={newGlossary.term}
                  onChange={(e) => setNewGlossary({ ...newGlossary, term: e.target.value })}
                  placeholder="e.g. dirt cheap"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="flex items-center space-x-2 text-sm text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newGlossary.is_banned}
                    onChange={(e) => setNewGlossary({ ...newGlossary, is_banned: e.target.checked })}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="font-medium">Strictly Banned Term</span>
                </label>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Preferred Alternative
                </label>
                <input
                  type="text"
                  value={newGlossary.preferred_term}
                  onChange={(e) => setNewGlossary({ ...newGlossary, preferred_term: e.target.value })}
                  placeholder="e.g. cost-effective"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Rule Definition / Explanation
                </label>
                <textarea
                  required
                  rows={3}
                  value={newGlossary.definition_or_rule}
                  onChange={(e) => setNewGlossary({ ...newGlossary, definition_or_rule: e.target.value })}
                  placeholder="Why this term is governed..."
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium py-2 rounded-lg shadow-xs transition"
              >
                Save Term Rule
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-3">Terminology Rules</h2>
            {glossary.length === 0 ? (
              <p className="text-sm text-slate-400 py-6 text-center">No terminology rules defined yet.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {glossary.map((t) => (
                  <div key={t.id} className="py-3 flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-sm text-slate-900 font-mono">"{t.term}"</span>
                        {t.is_banned ? (
                          <span className="text-xs bg-red-50 text-red-700 font-semibold px-2 py-0.5 rounded border border-red-200">
                            BANNED
                          </span>
                        ) : (
                          <span className="text-xs bg-blue-50 text-blue-700 font-semibold px-2 py-0.5 rounded">
                            APPROVED
                          </span>
                        )}
                      </div>
                      {t.preferred_term && (
                        <div className="text-xs text-emerald-700 mt-1 font-medium">
                          Use instead: "{t.preferred_term}"
                        </div>
                      )}
                      <p className="text-xs text-slate-500 mt-1">{t.definition_or_rule}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Assets */}
      {activeTab === "assets" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-3 flex items-center space-x-2">
              <Plus className="w-4 h-4 text-blue-600" />
              <span>Add Brand Asset</span>
            </h2>
            <form onSubmit={handleCreateAsset} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Asset Type
                </label>
                <select
                  value={newAsset.asset_type}
                  onChange={(e) => setNewAsset({ ...newAsset, asset_type: e.target.value as any })}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                >
                  <option value="PALETTE">Color Palette</option>
                  <option value="LOGO">Logo Parameters</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Asset Name
                </label>
                <input
                  type="text"
                  required
                  value={newAsset.name}
                  onChange={(e) => setNewAsset({ ...newAsset, name: e.target.value })}
                  placeholder="Primary Brand Colors"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Hex Colors (Comma Separated)
                </label>
                <input
                  type="text"
                  value={newAsset.hex_colors}
                  onChange={(e) => setNewAsset({ ...newAsset, hex_colors: e.target.value })}
                  placeholder="#0B2046, #FF6B35, #FFFFFF"
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium py-2 rounded-lg shadow-xs transition"
              >
                Register Brand Asset
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-3">Approved Brand Assets</h2>
            {assets.length === 0 ? (
              <p className="text-sm text-slate-400 py-6 text-center">No brand assets registered yet.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {assets.map((a) => (
                  <div key={a.id} className="p-4 border border-slate-200 rounded-lg bg-slate-50 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm text-slate-900">{a.name}</span>
                      <span className="text-xs bg-slate-200 px-2 py-0.5 rounded text-slate-700 font-mono">
                        {a.asset_type}
                      </span>
                    </div>
                    {a.hex_colors && a.hex_colors.length > 0 && (
                      <div className="flex space-x-2 pt-1">
                        {a.hex_colors.map((hex, i) => (
                          <div key={i} className="flex items-center space-x-1">
                            <div
                              className="w-6 h-6 rounded border border-slate-300 shadow-xs"
                              style={{ backgroundColor: hex }}
                            />
                            <span className="text-xs font-mono text-slate-600">{hex}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
