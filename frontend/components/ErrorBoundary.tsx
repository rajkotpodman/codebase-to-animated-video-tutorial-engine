"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import * as Sentry from "@sentry/nextjs";
import { AlertTriangle, RefreshCw, Home, ShieldAlert } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  componentName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  eventId: string | null;
}

/**
 * Standard Sentry-backed React Error Boundary.
 * Automatically catches unhandled rendering exceptions, reports them to Sentry with metadata,
 * and renders a resilient fallback UI.
 */
export class SentryErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    eventId: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, eventId: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error caught by SentryErrorBoundary:", error, errorInfo);

    // Report exception to Sentry with component context
    const eventId = Sentry.captureException(error, {
      extra: {
        componentStack: errorInfo.componentStack,
        componentName: this.props.componentName || "UnknownComponent",
      },
    });

    this.setState({ eventId });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, eventId: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="w-full rounded-2xl border border-destructive/40 bg-card/90 backdrop-blur-md p-6 sm:p-8 text-foreground shadow-2xl space-y-4 my-4 animate-in fade-in duration-300">
          <div className="flex items-start gap-3.5">
            <div className="h-10 w-10 rounded-xl bg-destructive/15 text-destructive flex items-center justify-center shrink-0 border border-destructive/30">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-foreground">
                  Application Rendering Exception
                </h3>
                {this.state.eventId && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-secondary text-secondary-foreground border border-border">
                    Sentry ID: {this.state.eventId.slice(0, 8)}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                An unexpected component rendering error occurred. The incident has been automatically logged for reliability analysis.
              </p>
            </div>
          </div>

          {this.state.error && (
            <div className="bg-black/40 rounded-xl p-3 font-mono text-[11px] text-destructive border border-destructive/20 overflow-x-auto">
              <code>{this.state.error.message || String(this.state.error)}</code>
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={this.handleReset}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm transition-all"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry Component</span>
            </button>

            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-secondary text-secondary-foreground hover:bg-secondary/70 border border-border transition-colors"
            >
              <span>Reload Page</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default SentryErrorBoundary;

