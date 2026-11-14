"use client";

import React, { useEffect, useState } from "react";
import {
  Users,
  ShieldAlert,
  ShieldCheck,
  Building,
  Key,
  Clock,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  UserX,
  RefreshCw,
  Search,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { AdminUserView, AuditLogEntry, UserRole } from "@/lib/types";

export default function AdminPage() {
  const { user } = useAuth();

  const [org, setOrg] = useState<any>(null);
  const [users, setUsers] = useState<AdminUserView[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEventType, setSelectedEventType] = useState<string>("");
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const loadData = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const [orgData, usersData, logsData] = await Promise.all([
        api.getOrganizationProfile().catch(() => null),
        api.listAdminUsers().catch(() => []),
        api.listAuditLogs(50, selectedEventType || undefined).catch(() => []),
      ]);
      setOrg(orgData);
      setUsers(usersData);
      setAuditLogs(logsData);
    } catch (err: any) {
      console.error(err);
      setMessage({ text: err.message || "Failed to load admin console", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user, selectedEventType]);

  const handleRoleChange = async (userId: string, newRole: UserRole) => {
    setUpdatingUserId(userId);
    setMessage(null);
    try {
      await api.updateUserRole(userId, newRole);
      setMessage({ text: `Updated user role to ${newRole}`, type: "success" });
      await loadData();
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to change role", type: "error" });
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleStatusToggle = async (userId: string, currentStatus: boolean) => {
    setUpdatingUserId(userId);
    setMessage(null);
    try {
      await api.updateUserStatus(userId, !currentStatus);
      setMessage({
        text: `User account ${!currentStatus ? "activated" : "deactivated"}`,
        type: "success",
      });
      await loadData();
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to update status", type: "error" });
    } finally {
      setUpdatingUserId(null);
    }
  };

  if (loading && !org) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-slate-500 font-medium animate-pulse">
          Loading organization administration console...
        </div>
      </div>
    );
  }

  const isAdminOrManager = user?.role === "ADMIN" || user?.role === "BRAND_MANAGER";

  if (!isAdminOrManager) {
    return (
      <div className="p-8 bg-amber-50 border border-amber-200 rounded-xl text-center">
        <ShieldAlert className="w-10 h-10 text-amber-600 mx-auto mb-2" />
        <h2 className="text-lg font-bold text-amber-900">Access Restricted</h2>
        <p className="text-sm text-amber-700 mt-1">
          Only Organization Administrators and Brand Managers can access team governance controls and audit logs.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-blue-700">
            <Key className="w-4 h-4" />
            <span>Enterprise Access & Governance</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Organization Administration</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Role-based access control, active members, security permissions, and audit log inspection.
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 rounded-lg shadow-xs transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Notification Banner */}
      {message && (
        <div
          className={`p-4 rounded-xl border flex items-center space-x-2 text-sm ${
            message.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          {message.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Organization Card */}
      {org && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
              <Building className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">{org.name}</h2>
              <div className="flex items-center space-x-3 text-xs text-slate-500 mt-0.5">
                <span>Tenant Slug: <span className="font-mono text-slate-700">{org.slug}</span></span>
                <span>•</span>
                <span>Data Isolation: <strong className="text-emerald-700">Strict Tenant Partitioning</strong></span>
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-2xl font-black text-slate-900">{org.total_members}</div>
            <div className="text-xs text-slate-400 font-medium">Active Team Members</div>
          </div>
        </div>
      )}

      {/* User Management Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
            <Users className="w-4 h-4 text-blue-600" />
            <span>Organization Members & Role Permissions ({users.length})</span>
          </h2>
          <span className="text-xs text-slate-400">
            Roles: Creator • Reviewer • Brand Manager • Admin
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-y border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Member Name</th>
                <th className="py-2.5 px-4">Email</th>
                <th className="py-2.5 px-4">Assigned Role</th>
                <th className="py-2.5 px-4">Account Status</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => {
                const isSelf = u.id === user?.id;
                const isRowUpdating = updatingUserId === u.id;

                return (
                  <tr key={u.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {u.full_name} {isSelf && <span className="text-[10px] text-blue-600 font-normal">(You)</span>}
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-mono">{u.email}</td>
                    <td className="py-3 px-4">
                      {user?.role === "ADMIN" ? (
                        <select
                          value={u.role}
                          disabled={isRowUpdating}
                          onChange={(e) => handleRoleChange(u.id, e.target.value as UserRole)}
                          className="bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-800 font-semibold focus:outline-none focus:border-blue-600"
                        >
                          <option value="CREATOR">CREATOR</option>
                          <option value="REVIEWER">REVIEWER</option>
                          <option value="BRAND_MANAGER">BRAND_MANAGER</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-slate-100 font-semibold text-slate-700">
                          {u.role}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold ${
                          u.is_active
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-red-50 text-red-700 border border-red-200"
                        }`}
                      >
                        {u.is_active ? <UserCheck className="w-3 h-3" /> : <UserX className="w-3 h-3" />}
                        <span>{u.is_active ? "Active" : "Disabled"}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {user?.role === "ADMIN" && !isSelf && (
                        <button
                          onClick={() => handleStatusToggle(u.id, u.is_active)}
                          disabled={isRowUpdating}
                          className="text-xs text-slate-500 hover:text-slate-800 underline transition"
                        >
                          {u.is_active ? "Deactivate" : "Activate"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Trail Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="font-semibold text-sm text-slate-900 flex items-center space-x-2">
            <Clock className="w-4 h-4 text-slate-500" />
            <span>Organization Audit Trail Log</span>
          </h2>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500">Filter Event:</span>
            <select
              value={selectedEventType}
              onChange={(e) => setSelectedEventType(e.target.value)}
              className="bg-white border border-slate-200 rounded px-2.5 py-1 text-xs text-slate-700 focus:outline-none"
            >
              <option value="">All Events</option>
              <option value="LOGIN">LOGIN</option>
              <option value="FINDING_DECISION">FINDING_DECISION</option>
              <option value="SUBMITTED_FOR_REVIEW">SUBMITTED_FOR_REVIEW</option>
              <option value="SUBMISSION_ESCALATED">SUBMISSION_ESCALATED</option>
              <option value="SUBMISSION_APPROVED">SUBMISSION_APPROVED</option>
              <option value="SUBMISSION_REJECTED">SUBMISSION_REJECTED</option>
              <option value="USER_ROLE_CHANGED">USER_ROLE_CHANGED</option>
              <option value="USER_STATUS_CHANGED">USER_STATUS_CHANGED</option>
            </select>
          </div>
        </div>

        {auditLogs.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            No audit logs found for the selected filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-y border-slate-200">
                <tr>
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Event Type</th>
                  <th className="py-2 px-3">Target Entity</th>
                  <th className="py-2 px-3">Details Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50">
                    <td className="py-2 px-3 text-slate-400 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-2 px-3">
                      <span className="px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-100">
                        {log.event_type}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-600">{log.entity_type}</td>
                    <td className="py-2 px-3 text-slate-700 max-w-md truncate font-sans">
                      {log.details ? JSON.stringify(log.details) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
