import * as Sentry from "@sentry/nextjs";

// -----------------------------------------------------------------------------
// Sentry Client-side Configuration for Next.js App Router
// -----------------------------------------------------------------------------

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN || "";

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: 1.0,
    environment: process.env.NODE_ENV || "development",
    // Capture replays on unhandled errors for visual session playback
    replaysOnErrorSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    integrations: [
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
    ],
  });
}

