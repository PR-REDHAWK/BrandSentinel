"use client";

import React from "react";
import Link from "next/link";
import { Shield, Building2, UserCircle, LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 border-b border-slate-200/80 bg-white/90 backdrop-blur-md sticky top-0 z-50 px-6 flex items-center justify-between shadow-xs transition-colors">
      <div className="flex items-center space-x-3">
        <Link href="/" className="group flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-xl bg-blue-700 text-white flex items-center justify-center shadow-sm group-hover:scale-105 group-hover:bg-blue-800 transition-all duration-300">
            <Shield className="w-5 h-5 text-blue-100" />
          </div>
          <span className="font-extrabold text-xl tracking-tight text-slate-900 group-hover:text-blue-900 transition-colors">
            Brand<span className="text-blue-700">Sentinel</span>
          </span>
        </Link>
        <span className="text-[11px] bg-blue-50/80 text-blue-700 font-semibold px-2.5 py-0.5 rounded-full border border-blue-200">
          v1.0 MVP
        </span>
      </div>

      <div className="flex items-center space-x-4">
        {user ? (
          <>
            <div className="flex items-center space-x-2 text-xs bg-slate-50 border border-slate-200/80 px-3 py-1.5 rounded-lg hover:border-slate-300 transition-colors">
              <Building2 className="w-3.5 h-3.5 text-slate-500" />
              <span className="font-semibold text-slate-700">
                {user.organization?.name || "Organization"}
              </span>
            </div>

            <div className="flex items-center space-x-2 text-xs">
              <UserCircle className="w-5 h-5 text-slate-600" />
              <div className="text-left">
                <div className="font-semibold text-slate-900 leading-tight">{user.full_name}</div>
                <div className="text-[10px] text-blue-700 font-mono font-semibold">{user.role}</div>
              </div>
            </div>

            <button
              onClick={logout}
              className="text-slate-400 hover:text-red-600 p-2 rounded-lg hover:bg-red-50 hover:border-red-100 border border-transparent transition-all duration-200"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </>
        ) : (
          <div className="flex items-center space-x-3">
            <Link
              href="/login"
              className="text-xs font-semibold text-slate-600 hover:text-blue-700 px-3 py-1.5 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="text-xs font-semibold bg-blue-700 text-white px-4 py-2 rounded-xl shadow-xs hover:bg-blue-800 hover:shadow-sm hover:-translate-y-0.5 transition-all duration-200"
            >
              Get Started
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
