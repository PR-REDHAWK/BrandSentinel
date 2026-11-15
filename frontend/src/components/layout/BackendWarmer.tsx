"use client";

import { useEffect } from "react";

export function BackendWarmer() {
  useEffect(() => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const healthUrl = apiBase.replace(/\/api\/v1\/?$/, "") + "/health";
      fetch(healthUrl, { method: "GET", mode: "cors" }).catch(() => {});
    } catch {
      // Non-critical background warm-up
    }
  }, []);

  return null;
}
