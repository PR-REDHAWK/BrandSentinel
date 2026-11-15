"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BookOpen,
  FileCheck2,
  BarChart3,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  if (!user) return null;

  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "Brand Knowledge Hub", href: "/knowledge", icon: BookOpen },
    { label: "Content Submissions", href: "/submissions", icon: FileCheck2 },
    { label: "Governance Insights", href: "/insights", icon: BarChart3 },
    { label: "Organization Admin", href: "/admin", icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-slate-200/80 bg-white min-h-[calc(100vh-4rem)] p-4 flex flex-col justify-between shadow-xs">
      <div className="space-y-1.5">
        <div className="px-3 py-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
          Platform Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                isActive
                  ? "bg-blue-50 text-blue-700 shadow-xs ring-1 ring-blue-200/60 translate-x-0.5"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 hover:translate-x-1"
              }`}
            >
              <Icon
                className={`w-4 h-4 transition-transform duration-200 group-hover:scale-110 ${
                  isActive ? "text-blue-700" : "text-slate-400 group-hover:text-slate-600"
                }`}
              />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="p-3.5 bg-gradient-to-br from-slate-50 to-blue-50/30 border border-slate-200/80 rounded-2xl shadow-xs">
        <div className="flex items-center space-x-2 text-xs font-bold text-slate-800 mb-1">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Governance Policy</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          AI suggests. Humans decide. 100% of factual findings link directly to genuine cited evidence.
        </p>
      </div>
    </aside>
  );
}
