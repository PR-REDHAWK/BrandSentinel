"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, Lock, Mail, AlertCircle, Sparkles, CheckCircle } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleQuickLogin = async (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError("");
    setLoading(true);

    try {
      await login({ email: demoEmail, password: demoPass });
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login({ email, password });
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to sign in. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-12">
      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-blue-700 text-white rounded-xl flex items-center justify-center mx-auto mb-3 shadow-xs">
            <Shield className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Sign in to BrandSentinel</h1>
          <p className="text-sm text-slate-500 mt-1">Access your organization's brand gate</p>
        </div>

        {error && (
          <div className="mb-5 bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 1-Click Evaluation Logins for Judges */}
        <div className="mb-6 p-4 bg-gradient-to-br from-blue-50 to-indigo-50/60 border border-blue-200/80 rounded-xl">
          <div className="flex items-center space-x-1.5 mb-1.5">
            <Sparkles className="w-4 h-4 text-blue-600 animate-pulse" />
            <span className="text-xs font-bold text-blue-900 uppercase tracking-wider">
              Judge Evaluation 1-Click Logins
            </span>
          </div>
          <p className="text-xs text-blue-800/80 mb-3">
            Pre-seeded with Acme Corp brand guidelines & findings. Click any role to enter instantly:
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin("admin@acme.com", "Password123!")}
              disabled={loading}
              className="px-2 py-2.5 bg-white hover:bg-blue-600 hover:text-white border border-blue-200 rounded-lg text-xs font-semibold text-slate-800 transition shadow-xs flex flex-col items-center text-center group"
            >
              <span className="text-sm">👑</span>
              <span className="mt-0.5 group-hover:text-white">Admin</span>
              <span className="text-[10px] text-slate-500 group-hover:text-blue-100 font-normal">Full Hub</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("reviewer@acme.com", "Password123!")}
              disabled={loading}
              className="px-2 py-2.5 bg-white hover:bg-blue-600 hover:text-white border border-blue-200 rounded-lg text-xs font-semibold text-slate-800 transition shadow-xs flex flex-col items-center text-center group"
            >
              <span className="text-sm">🔍</span>
              <span className="mt-0.5 group-hover:text-white">Reviewer</span>
              <span className="text-[10px] text-slate-500 group-hover:text-blue-100 font-normal">Sign-Off</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("creator@acme.com", "Password123!")}
              disabled={loading}
              className="px-2 py-2.5 bg-white hover:bg-blue-600 hover:text-white border border-blue-200 rounded-lg text-xs font-semibold text-slate-800 transition shadow-xs flex flex-col items-center text-center group"
            >
              <span className="text-sm">✍️</span>
              <span className="mt-0.5 group-hover:text-white">Creator</span>
              <span className="text-[10px] text-slate-500 group-hover:text-blue-100 font-normal">Drafts</span>
            </button>
          </div>
        </div>

        <div className="relative mb-5">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200"></div>
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-slate-400 font-medium">Or enter manually</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Work Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white font-medium py-2.5 rounded-lg shadow-xs transition disabled:opacity-50 mt-2"
          >
            {loading ? "Authenticating..." : "Sign In"}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          Don't have an organization tenant yet?{" "}
          <Link href="/register" className="text-blue-700 font-semibold hover:underline">
            Register your team
          </Link>
        </div>
      </div>
    </div>
  );
}
