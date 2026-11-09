"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  RotateCcw,
  RefreshCw,
  Terminal,
  Cpu,
  Layers,
  ChevronRight,
  Info,
  Radio,
} from "lucide-react";
import { cn } from "@/lib/utils";

// -----------------------------------------------------------------------------
// Type Definitions
// -----------------------------------------------------------------------------

export type JobStatusType =
  | "PENDING"
  | "QUEUED"
  | "PROGRESS"
  | "PROCESSING"
  | "SUCCESS"
  | "FAILURE";

export interface JobResultData {
  final_video_path?: string;
  duration?: number;
  subtitles_burned?: boolean;
  voice?: string;
  resolution?: string;
  theme?: string;
  [key: string]: any;
}

export interface JobStatusResponseData {
  job_id: string;
  status: JobStatusType;
  progress: number;
  step?: number | null;
  step_name?: string | null;
  message?: string | null;
  result?: JobResultData | null;
  error?: string | null;
  download_url?: string | null;
}

export interface JobProgressProps {
  /** The unique Celery / FastAPI task ID */
  jobId: string;
  /** Callback triggered once job status transitions to SUCCESS */
  onComplete?: (data: JobStatusResponseData) => void;
  /** Callback triggered if job status transitions to FAILURE */
  onError?: (errorMessage: string) => void;
  /** Callback triggered when user clicks restart / reset */
  onReset?: () => void;
  /** Optional polling interval in milliseconds (defaults to 3000ms) */
  pollIntervalMs?: number;
}

// -----------------------------------------------------------------------------
// Pipeline 5-Stage Definitions
// -----------------------------------------------------------------------------

const PIPELINE_STEPS = [
  {
    step: 1,
    id: "ingestion",
    name: "Ingestion",
    title: "Repomix Ingestion",
    desc: "Cloning repository & packing source files into compressed markdown",
  },
  {
    step: 2,
    id: "gemini",
    name: "Gemini",
    title: "Gemini AI Scripting",
    desc: "Synthesizing architectural topology & technical voiceover narration",
  },
  {
    step: 3,
    id: "manim",
    name: "Manim",
    title: "Manim Animation",
    desc: "Procedurally generating & rendering high-frame-rate Manim scenes",
  },
  {
    step: 4,
    id: "tts",
    name: "TTS",
    title: "Neural Voice & SRT",
    desc: "Synthesizing studio voiceover audio & millisecond-synced subtitle cues",
  },
  {
    step: 5,
    id: "ffmpeg",
    name: "FFmpeg",
    title: "FFmpeg Assembly",
    desc: "HD scaling, audio stream synchronization & subtitle burn-in overlay",
  },
];

export function JobProgress({
  jobId,
  onComplete,
  onError,
  onReset,
  pollIntervalMs = 3000,
}: JobProgressProps) {
  const [jobData, setJobData] = useState<JobStatusResponseData>({
    job_id: jobId,
    status: "QUEUED",
    progress: 5,
    step: 1,
    step_name: "Repomix Ingestion",
    message: "Video task queued in Celery worker...",
  });

  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [pollCount, setPollCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [networkWarning, setNetworkWarning] = useState<string | null>(null);
  const [isSseConnected, setIsSseConnected] = useState<boolean>(true);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const stopwatchRef = useRef<NodeJS.Timeout | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const isTerminalRef = useRef(false);

  // Normalize status for badge mapping
  const normalizedStatus: "QUEUED" | "PROCESSING" | "SUCCESS" | "FAILURE" =
    jobData.status === "SUCCESS"
      ? "SUCCESS"
      : jobData.status === "FAILURE"
      ? "FAILURE"
      : jobData.status === "PROGRESS" || jobData.status === "PROCESSING"
      ? "PROCESSING"
      : "QUEUED";

  // ---------------------------------------------------------------------------
  // Stopwatch Counter
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (normalizedStatus === "QUEUED" || normalizedStatus === "PROCESSING") {
      stopwatchRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (stopwatchRef.current) clearInterval(stopwatchRef.current);
    }

    return () => {
      if (stopwatchRef.current) clearInterval(stopwatchRef.current);
    };
  }, [normalizedStatus]);

  // ---------------------------------------------------------------------------
  // Unified Data Handler (Used by both SSE and Polling Fallback)
  // ---------------------------------------------------------------------------
  const handleIncomingJobData = useCallback(
    (data: JobStatusResponseData) => {
      setNetworkWarning(null);

      // Map progress percentage and steps
      const currentStepNum =
        data.step ??
        (data.progress > 80
          ? 5
          : data.progress > 60
          ? 4
          : data.progress > 40
          ? 3
          : data.progress > 20
          ? 2
          : 1);

      setJobData({
        ...data,
        step: currentStepNum,
      });

      if (data.status === "SUCCESS") {
        isTerminalRef.current = true;
        if (pollingRef.current) clearInterval(pollingRef.current);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
        if (onComplete) onComplete(data);
      } else if (data.status === "FAILURE") {
        isTerminalRef.current = true;
        if (pollingRef.current) clearInterval(pollingRef.current);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
        const err = data.error || data.message || "Video generation pipeline failed.";
        if (onError) onError(err);
      }
    },
    [onComplete, onError]
  );

  // ---------------------------------------------------------------------------
  // Polling Fallback Function
  // ---------------------------------------------------------------------------
  const pollJobStatus = useCallback(async () => {
    if (isTerminalRef.current) return;

    try {
      const response = await fetch(`/api/v1/jobs/${jobId}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Job status returned HTTP ${response.status}`);
      }

      const data: JobStatusResponseData = await response.json();
      setPollCount((p) => p + 1);
      handleIncomingJobData(data);
    } catch (err: any) {
      console.warn("Poll job status exception:", err);
      setNetworkWarning("Reconnecting to background task service...");
    }
  }, [jobId, handleIncomingJobData]);

  // ---------------------------------------------------------------------------
  // Real-Time Server-Sent Events (SSE) Stream Setup with Fallback
  // ---------------------------------------------------------------------------
  useEffect(() => {
    isTerminalRef.current = false;

    // 1. Start immediate polling so progress tracker responds instantly regardless of SSE proxy buffering
    pollJobStatus();
    if (!pollingRef.current) {
      pollingRef.current = setInterval(pollJobStatus, pollIntervalMs || 2500);
    }

    // 2. Connect via browser EventSource for real-time SSE push updates
    if (typeof window !== "undefined" && "EventSource" in window) {
      try {
        const es = new EventSource(`/api/v1/jobs/${jobId}/stream`);
        eventSourceRef.current = es;

        es.addEventListener("progress", (event) => {
          try {
            const data: JobStatusResponseData = JSON.parse(event.data);
            handleIncomingJobData(data);
          } catch (err) {
            console.error("Failed to parse SSE progress event:", err);
          }
        });

        es.addEventListener("complete", (event) => {
          try {
            const data: JobStatusResponseData = JSON.parse(event.data);
            handleIncomingJobData(data);
          } catch (err) {
            console.error("Failed to parse SSE complete event:", err);
          }
        });

        es.addEventListener("error", () => {
          setIsSseConnected(false);
        });

        es.onopen = () => {
          setIsSseConnected(true);
          setNetworkWarning(null);
        };
      } catch (err) {
        console.warn("Could not establish EventSource, HTTP polling active:", err);
        setIsSseConnected(false);
      }
    } else {
      setIsSseConnected(false);
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [jobId, pollIntervalMs, handleIncomingJobData, pollJobStatus]);

  // Manual retry trigger
  const handleManualPoll = async () => {
    setIsRetrying(true);
    await pollJobStatus();
    setIsRetrying(false);
  };

  // Format stopwatch elapsed seconds
  const formatTime = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="w-full rounded-2xl border border-border bg-card/95 backdrop-blur-md p-6 sm:p-8 shadow-xl space-y-6 animate-in fade-in duration-300">
      {/* =================================================================== */}
      {/* Top Header: Title, Status Badge, Elapsed Time                       */}
      {/* =================================================================== */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/80">
        <div className="flex items-center gap-3.5">
          {/* Animated Icon Avatar */}
          <div
            className={cn(
              "h-11 w-11 rounded-xl flex items-center justify-center font-bold text-white shadow-md transition-all duration-300",
              normalizedStatus === "SUCCESS"
                ? "bg-emerald-500 shadow-emerald-500/25 ring-2 ring-emerald-500/30"
                : normalizedStatus === "FAILURE"
                ? "bg-rose-500 shadow-rose-500/25 ring-2 ring-rose-500/30"
                : normalizedStatus === "PROCESSING"
                ? "bg-blue-600 shadow-blue-500/25 ring-2 ring-blue-500/30 animate-pulse"
                : "bg-amber-500/90 shadow-amber-500/20 ring-2 ring-amber-500/30"
            )}
          >
            {normalizedStatus === "SUCCESS" ? (
              <CheckCircle2 className="h-6 w-6" />
            ) : normalizedStatus === "FAILURE" ? (
              <AlertCircle className="h-6 w-6" />
            ) : normalizedStatus === "PROCESSING" ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <Clock className="h-6 w-6" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-lg font-bold text-foreground">
                {normalizedStatus === "SUCCESS"
                  ? "Tutorial Video Generation Complete"
                  : normalizedStatus === "FAILURE"
                  ? "Video Generation Failed"
                  : normalizedStatus === "PROCESSING"
                  ? "Rendering Animated Tutorial..."
                  : "Video Task Queued"}
              </h2>

              {/* Status Badge */}
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border",
                  normalizedStatus === "SUCCESS"
                    ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                    : normalizedStatus === "FAILURE"
                    ? "bg-rose-500/15 text-rose-400 border-rose-500/30"
                    : normalizedStatus === "PROCESSING"
                    ? "bg-blue-500/15 text-blue-400 border-blue-500/30 animate-pulse"
                    : "bg-amber-500/15 text-amber-400 border-amber-500/30"
                )}
              >
                {normalizedStatus === "PROCESSING" && (
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-ping" />
                )}
                {normalizedStatus}
              </span>
            </div>

            <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-2">
              <span className="font-mono text-foreground/80">Job: {jobId}</span>
              {networkWarning && (
                <span className="text-amber-400 text-[11px] flex items-center gap-1">
                  • {networkWarning}
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Right Info Controls */}
        <div className="flex items-center gap-3">
          {/* Real-time SSE / Polling Stream Indicator */}
          <div
            className={cn(
              "hidden sm:flex items-center gap-1.5 text-xs font-mono px-2.5 py-1.5 rounded-lg border",
              isSseConnected
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-slate-800 text-slate-400 border-slate-700"
            )}
            title={
              isSseConnected
                ? "Connected to real-time Server-Sent Events stream"
                : "Operating in standard HTTP polling fallback mode"
            }
          >
            <Radio className={cn("h-3 w-3", isSseConnected && "animate-pulse text-emerald-400")} />
            <span>{isSseConnected ? "Live SSE" : "Polling"}</span>
          </div>

          {/* Elapsed Timer */}
          <div className="flex items-center gap-1.5 text-xs font-mono text-muted-foreground bg-secondary/80 px-3 py-1.5 rounded-lg border border-border">
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>Elapsed: {formatTime(elapsedSeconds)}</span>
          </div>

          {/* Manual Refresh / Retry */}
          {normalizedStatus !== "SUCCESS" && normalizedStatus !== "FAILURE" && (
            <button
              onClick={handleManualPoll}
              disabled={isRetrying}
              title="Force status check"
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary border border-border transition-colors disabled:opacity-50"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", isRetrying && "animate-spin")} />
            </button>
          )}

          {/* Reset / Restart Button */}
          {onReset && (
            <button
              onClick={onReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-secondary text-secondary-foreground hover:bg-secondary/70 transition-colors border border-border"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>{normalizedStatus === "FAILURE" ? "Retry" : "New Task"}</span>
            </button>
          )}
        </div>
      </div>

      {/* =================================================================== */}
      {/* Live Animated Progress Bar                                          */}
      {/* =================================================================== */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-xs font-medium">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Overall Completion</span>
            {jobData.message && (
              <span className="text-foreground/90 font-normal truncate max-w-md hidden sm:inline">
                — {jobData.message}
              </span>
            )}
          </div>
          <span className="font-mono text-foreground font-bold text-sm">
            {jobData.progress}%
          </span>
        </div>

        <div className="w-full bg-secondary rounded-full h-3.5 overflow-hidden p-0.5 border border-border">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-700 ease-out bg-gradient-to-r shadow-sm",
              normalizedStatus === "SUCCESS"
                ? "from-emerald-500 via-teal-400 to-emerald-300"
                : normalizedStatus === "FAILURE"
                ? "from-rose-500 via-red-500 to-orange-400"
                : "from-blue-600 via-indigo-500 to-cyan-400"
            )}
            style={{ width: `${Math.max(jobData.progress, 5)}%` }}
          />
        </div>
      </div>

      {/* =================================================================== */}
      {/* 5-Stage Step Indicators: Ingestion -> Gemini -> Manim -> TTS -> FFmpeg */}
      {/* =================================================================== */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground font-semibold uppercase tracking-wider">
          <span>Pipeline Stages</span>
          <span>Stage {jobData.step || 1} of 5</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          {PIPELINE_STEPS.map((s, idx) => {
            const stepNum = s.step;
            const currentStepNum = jobData.step || 1;

            const isDone =
              normalizedStatus === "SUCCESS" || stepNum < currentStepNum;
            const isCurrent =
              normalizedStatus === "PROCESSING" && stepNum === currentStepNum;
            const isFailed =
              normalizedStatus === "FAILURE" && stepNum === currentStepNum;

            return (
              <div
                key={s.id}
                className={cn(
                  "p-3 rounded-xl border text-xs transition-all flex flex-col justify-between relative",
                  isDone
                    ? "border-emerald-500/40 bg-emerald-500/5 text-emerald-400 shadow-sm"
                    : isCurrent
                    ? "border-primary bg-primary/10 text-primary ring-1 ring-primary/40 shadow-md"
                    : isFailed
                    ? "border-rose-500/50 bg-rose-500/10 text-rose-400 ring-1 ring-rose-500/30"
                    : "border-border/60 bg-secondary/30 text-muted-foreground opacity-70"
                )}
              >
                <div>
                  <div className="flex items-center justify-between font-bold mb-1.5">
                    <span className="flex items-center gap-1.5">
                      <span className="text-[10px] opacity-75">{s.step}.</span>
                      <span>{s.name}</span>
                    </span>

                    {/* Step Status Icon */}
                    {isDone ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    ) : isCurrent ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                    ) : isFailed ? (
                      <AlertCircle className="h-4 w-4 text-rose-400" />
                    ) : (
                      <span className="text-[10px] text-muted-foreground font-normal">
                        Waiting
                      </span>
                    )}
                  </div>

                  <p className="text-[11px] font-medium text-foreground line-clamp-1 mb-1">
                    {s.title}
                  </p>
                  <p className="text-[10px] text-muted-foreground leading-relaxed line-clamp-2">
                    {s.desc}
                  </p>
                </div>

                {/* Arrow Connector between steps for large screens */}
                {idx < PIPELINE_STEPS.length - 1 && (
                  <div className="hidden sm:block absolute -right-2 top-1/2 -translate-y-1/2 z-10">
                    <ChevronRight className="h-4 w-4 text-border" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* =================================================================== */}
      {/* Detailed Failure Alert Box                                          */}
      {/* =================================================================== */}
      {normalizedStatus === "FAILURE" && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-5 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-bold text-rose-300">
                Pipeline Execution Failed
              </h4>
              <p className="text-xs text-rose-200/90 mt-1 leading-relaxed">
                {jobData.error ||
                  jobData.message ||
                  "The background worker encountered an unexpected failure during video processing."}
              </p>
            </div>
          </div>

          <div className="bg-black/40 rounded-lg p-3 font-mono text-[11px] text-rose-300/90 border border-rose-500/20 overflow-x-auto">
            <div className="flex items-center gap-2 mb-1 text-muted-foreground text-[10px] uppercase font-bold">
              <Terminal className="h-3 w-3" /> Diagnostic Log
            </div>
            <code>
              {jobData.error
                ? jobData.error
                : `Job [${jobId}] failed at Stage ${jobData.step || "unknown"}. Please verify Git repository URL accessibility, Redis availability, or Manim engine dependencies.`}
            </code>
          </div>

          {onReset && (
            <div className="pt-1 flex items-center gap-3">
              <button
                onClick={onReset}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-md shadow-rose-600/20 transition-all"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Try Again / Change Parameters</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default JobProgress;

