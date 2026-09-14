"use client";

import React, { useEffect } from "react";
import { AlertCircle, RefreshCw, Home } from "lucide-react";

export default function GlobalError({ error, reset }) {
  useEffect(() => {
    // Log minimal error status without sensitive details
    console.error("Application error boundary triggered:", error?.message || "Unknown error");
  }, [error]);

  return (
    <div
      className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-slate-100"
      role="alert"
      aria-live="assertive"
    >
      <div className="glass-card max-w-md w-full p-8 rounded-2xl border border-red-500/30 text-center shadow-2xl">
        <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
          <AlertCircle className="w-7 h-7" aria-hidden="true" />
        </div>
        <h1 className="text-xl font-bold text-white tracking-tight">Application Encountered an Error</h1>
        <p className="text-sm text-slate-400 mt-2">
          {error?.message || "An unexpected client error occurred while rendering the dashboard."}
        </p>

        <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => reset()}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-brand-primary text-slate-950 font-semibold text-sm hover:bg-brand-hover transition-colors min-h-[44px]"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
            Try Again
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-surface-secondary text-slate-200 hover:text-white hover:bg-surface-tertiary transition-colors text-sm font-medium border border-border min-h-[44px]"
          >
            <Home className="w-4 h-4" aria-hidden="true" />
            Reload Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
