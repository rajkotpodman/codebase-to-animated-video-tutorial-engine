"use client";

import React, { useEffect } from "react";
import * as Sentry from "@sentry/nextjs";
import { AlertCircle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Report unhandled client/server exception to Sentry
    console.error("Next.js Error Caught:", error);
    Sentry.captureException(error, {
      extra: { digest: error.digest },
    });
  }, [error]);

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center space-y-6">
      <div className="h-14 w-14 rounded-2xl bg-destructive/15 text-destructive flex items-center justify-center border border-destructive/30 shadow-lg">
        <AlertCircle className="h-8 w-8" />
      </div>

      <div className="max-w-md space-y-2">
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          Something went wrong
        </h2>
        <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
          An unexpected error occurred while processing this request. Our engineering team has been notified via Sentry.
        </p>
        {error.digest && (
          <p className="text-[10px] font-mono text-muted-foreground bg-secondary/80 px-2.5 py-1 rounded-md inline-block border border-border">
            Digest: {error.digest}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => reset()}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 shadow-md shadow-primary/20 transition-all"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Try Again</span>
        </button>

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-secondary text-secondary-foreground hover:bg-secondary/70 border border-border transition-colors"
        >
          <Home className="h-4 w-4" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    </div>
  );
}

