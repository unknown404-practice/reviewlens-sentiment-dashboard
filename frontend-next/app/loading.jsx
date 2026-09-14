import React from "react";

export default function Loading() {
  return (
    <div
      className="min-h-screen bg-background flex flex-col items-center justify-center p-4 text-slate-200"
      role="status"
      aria-live="polite"
    >
      <div className="relative w-16 h-16 mb-4">
        <div className="absolute inset-0 rounded-full border-2 border-brand-primary/20 animate-ping"></div>
        <div className="absolute inset-0 rounded-full border-2 border-t-brand-primary border-r-transparent border-b-transparent border-l-transparent animate-spin"></div>
        <div className="absolute inset-2 rounded-full bg-surface flex items-center justify-center text-xl">
          🔍
        </div>
      </div>
      <h2 className="text-lg font-semibold text-slate-100 tracking-wide">Loading ReviewLens Dashboard...</h2>
      <p className="text-sm text-slate-400 mt-1">Connecting to FastAPI Sentiment Intelligence Engine</p>
      <span className="sr-only">Loading application resources...</span>
    </div>
  );
}
