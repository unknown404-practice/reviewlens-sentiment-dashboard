import React from "react";
import Link from "next/link";
import { ArrowLeft, Search } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-slate-100">
      <div className="glass-card max-w-md w-full p-8 rounded-2xl text-center border border-border">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary">
          <Search className="w-8 h-8" aria-hidden="true" />
        </div>
        <span className="text-xs font-semibold uppercase tracking-wider text-brand-primary px-2.5 py-1 rounded-full bg-brand-primary/10 border border-brand-primary/20">
          404 Not Found
        </span>
        <h1 className="text-2xl font-bold text-white mt-3">Page Not Found</h1>
        <p className="text-sm text-slate-400 mt-2">
          The requested route does not exist. Return to the ReviewLens dashboard to analyze sentiment.
        </p>
        <div className="mt-6">
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-brand-primary text-slate-950 font-semibold text-sm hover:bg-brand-hover transition-colors min-h-[44px]"
          >
            <ArrowLeft className="w-4 h-4" aria-hidden="true" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
