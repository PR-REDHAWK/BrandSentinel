"use client";

import React from "react";
import Link from "next/link";
import { Shield, Building2, UserCircle, LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-50 px-6 flex items-center justify-between shadow-xs">
      <div className="flex items-center space-x-3">
        <Link href="/" className="flex items-center space-x-2">
          <div className="w-9 h-9 rounded-lg bg-blue-700 text-white flex items-center justify-center shadow-sm">
            <Shield className="w-5 h-5 text-blue-100" />
          </div>
          <span className="font-bold text-xl tracking-tight text-slate-900">
            Brand<span className="text-blue-700">Sentinel</span>
          </span>
        </Link>
        <span className="text-xs bg-blue-50 text-blue-700 font-semibold px-2 py-0.5 rounded-full border border-blue-200">
          v1.0 MVP
        </span>
      </div>

      <div className="flex items-center space-x-4">
        {user ? (
          <>
            <div className="flex items-center space-x-2 text-sm bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-md">
              <Building2 className="w-4 h-4 text-slate-500" />
              <span className="font-medium text-slate-700">
                {user.organization?.name || "Organization"}
              </span>
            </div>

            <div className="flex items-center space-x-2 text-sm">
              <UserCircle className="w-5 h-5 text-slate-600" />
              <div className="text-left">
                <div className="font-medium text-slate-900 leading-tight">{user.full_name}</div>
                <div className="text-xs text-slate-500 font-mono">{user.role}</div>
              </div>
            </div>

            <button
              onClick={logout}
              className="text-slate-500 hover:text-red-600 p-1.5 rounded-md hover:bg-slate-100 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </>
        ) : (
          <div className="flex items-center space-x-3">
            <Link
              href="/login"
              className="text-sm font-medium text-slate-700 hover:text-blue-700 px-3 py-1.5"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="text-sm font-medium bg-blue-700 text-white px-3.5 py-1.5 rounded-md shadow-xs hover:bg-blue-800 transition"
            >
              Get Started
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
