"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Loader2,
  AlertCircle,
  Volume2,
  Monitor,
  Palette,
  Subtitles,
  ArrowRight,
  Cpu,
  Sliders,
  Info,
  FileCode2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GithubIcon } from "@/components/icons";
import { JobProgress } from "@/components/JobProgress";
import { VideoPlayer } from "@/components/VideoPlayer";

// -----------------------------------------------------------------------------
// Voice Catalog Definitions
// -----------------------------------------------------------------------------

interface AIModelOption {
  id: string;
  name: string;
  badge?: string;
  description: string;
}

const AI_MODEL_OPTIONS: AIModelOption[] = [
  {
    id: "gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    badge: "Recommended",
    description: "Ultra-fast multimodal reasoning, optimal for architecture extraction",
  },
  {
    id: "gemini-2.5-pro",
    name: "Gemini 2.5 Pro",
    badge: "Deep Reasoning",
    description: "Extended context window for complex multi-package repositories",
  },
  {
    id: "gemini-2.0-flash",
    name: "Gemini 2.0 Flash",
    badge: "Next-Gen",
    description: "Structured JSON schema output with high speed",
  },
  {
    id: "gemini-1.5-pro",
    name: "Gemini 1.5 Pro",
    badge: "2M Context",
    description: "Deep dependency graph analysis for large codebases",
  },
];

interface VoiceOption {
  id: string;
  name: string;
  category: "English (US)" | "English (UK)" | "Hindi & Hinglish" | "Indian English";
  gender: "Male" | "Female";
  tone: string;
  badge?: string;
}

const VOICE_CATALOG: VoiceOption[] = [
  {
    id: "en-US-ChristopherNeural",
    name: "Christopher",
    category: "English (US)",
    gender: "Male",
    tone: "Authoritative & Technical",
    badge: "Popular",
  },
  {
    id: "en-US-GuyNeural",
    name: "Guy",
    category: "English (US)",
    gender: "Male",
    tone: "Casual & Conversational",
  },
  {
    id: "en-US-JennyNeural",
    name: "Jenny",
    category: "English (US)",
    gender: "Female",
    tone: "Clear & Articulate",
  },
  {
    id: "en-GB-RyanNeural",
    name: "Ryan",
    category: "English (UK)",
    gender: "Male",
    tone: "Refined & Professional",
  },
  {
    id: "hi-IN-MadhurNeural",
    name: "Madhur",
    category: "Hindi & Hinglish",
    gender: "Male",
    tone: "Natural Hinglish / Hindi Tech Voice",
    badge: "Desi",
  },
  {
    id: "hi-IN-SwaraNeural",
    name: "Swara",
    category: "Hindi & Hinglish",
    gender: "Female",
    tone: "Expressive & Melodic",
  },
  {
    id: "en-IN-PrabhatNeural",
    name: "Prabhat",
    category: "Indian English",
    gender: "Male",
    tone: "Indian Tech Lead Accent",
  },
  {
    id: "en-IN-NeerjaNeural",
    name: "Neerja",
    category: "Indian English",
    gender: "Female",
    tone: "Formal Indian English",
  },
];

// -----------------------------------------------------------------------------
// Theme Definitions
// -----------------------------------------------------------------------------

interface ThemeOption {
  id: "midnight" | "dark" | "cyberpunk" | "nord" | "light";
  name: string;
  description: string;
  bgHex: string;
  accentHex: string;
  borderHex: string;
}

const THEME_OPTIONS: ThemeOption[] = [
  {
    id: "midnight",
    name: "Midnight",
    description: "Deep obsidian navy with cyan laser glow",
    bgHex: "#0B0F19",
    accentHex: "#38BDF8",
    borderHex: "#1E293B",
  },
  {
    id: "dark",
    name: "Onyx Dark",
    description: "Classic high-contrast dark IDE aesthetic",
    bgHex: "#121214",
    accentHex: "#6366F1",
    borderHex: "#27272A",
  },
  {
    id: "cyberpunk",
    name: "Cyberpunk",
    description: "Neon magenta, electric cyan & emerald highlights",
    bgHex: "#0a0a14",
    accentHex: "#EC4899",
    borderHex: "#8B5CF6",
  },
  {
    id: "nord",
    name: "Nordic Frost",
    description: "Subtle arctic blues and frosty cold slate",
    bgHex: "#2E3440",
    accentHex: "#88C0D0",
    borderHex: "#4C566A",
  },
  {
    id: "light",
    name: "Clean Light",
    description: "Minimalist crisp white with slate technical lines",
    bgHex: "#FFFFFF",
    accentHex: "#2563EB",
    borderHex: "#E2E8F0",
  },
];

// -----------------------------------------------------------------------------
// Sample Repositories for Quick Testing
// -----------------------------------------------------------------------------

const SAMPLE_REPOSITORIES = [
  {
    label: "Repomix Packaging",
    url: "https://github.com/yamadashy/repomix",
    description: "Codebase consolidation tool",
  },
  {
    label: "FastAPI Framework",
    url: "https://github.com/tiangolo/fastapi",
    description: "Modern, fast web framework for Python",
  },
  {
    label: "Helper AI (Rajkotpodman)",
    url: "https://github.com/rajkotpodman/helper-ai",
    description: "Multi-service AI assistant repository",
  },
  {
    label: "Octocat Hello-World",
    url: "https://github.com/octocat/Hello-World",
    description: "Simple starter Git repository",
  },
];

export default function DashboardPage() {
  // Form State
  const [repoUrl, setRepoUrl] = useState("");
  const [aiModel, setAiModel] = useState("gemini-2.5-flash");
  const [voice, setVoice] = useState("en-US-ChristopherNeural");
  const [resolution, setResolution] = useState<"1080p" | "720p" | "480p">("1080p");
  const [theme, setTheme] = useState<"midnight" | "dark" | "cyberpunk" | "nord" | "light">("midnight");
  const [burnSubtitles, setBurnSubtitles] = useState(true);
  const [customInstructions, setCustomInstructions] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Validation State
  const [urlTouched, setUrlTouched] = useState(false);
  const [isValidUrl, setIsValidUrl] = useState(false);

  // Job Execution & State Tracking
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<"IDLE" | "QUEUED" | "PROCESSING" | "SUCCESS" | "FAILURE">("IDLE");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [videoDuration, setVideoDuration] = useState<number | undefined>(undefined);

  // ---------------------------------------------------------------------------
  // Real-time URL Validation (supports full https, .git, branches, and shorthand)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!repoUrl.trim()) {
      setIsValidUrl(false);
      return;
    }
    const clean = repoUrl.trim();
    const githubUrlRegex = /^(https?:\/\/)?(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(\.git)?(\/.*)?$/i;
    const shorthandRegex = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
    const genericGitRegex = /^(git@|https?:\/\/).+github\.com[:/][A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(\.git)?.*$/i;
    setIsValidUrl(githubUrlRegex.test(clean) || shorthandRegex.test(clean) || genericGitRegex.test(clean));
  }, [repoUrl]);

  // ---------------------------------------------------------------------------
  // Form Submission to FastAPI
  // ---------------------------------------------------------------------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUrlTouched(true);

    if (!isValidUrl) {
      setErrorMessage("Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo or owner/repo).");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await fetch("/api/v1/generate-video", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          repo_url: repoUrl.trim(),
          voice: voice,
          resolution: resolution,
          theme: theme,
          burn_subtitles: burnSubtitles,
          custom_instructions: customInstructions.trim() ? customInstructions.trim() : null,
          gemini_model: aiModel,
          run_sync: false,
        }),
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server responded with status ${response.status}`);
      }

      const data = await response.json();
      setJobId(data.job_id);
      setJobStatus("QUEUED");
      setDownloadUrl(`/api/v1/jobs/${data.job_id}/download`);
    } catch (err: any) {
      setJobStatus("FAILURE");
      setErrorMessage(err.message || "Failed to submit video generation request. Is the backend API running?");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setJobId(null);
    setJobStatus("IDLE");
    setErrorMessage(null);
    setDownloadUrl(null);
    setVideoDuration(undefined);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* =================================================================== */}
      {/* Page Header                                                         */}
      {/* =================================================================== */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 mb-3">
            <Sparkles className="h-3.5 w-3.5 animate-pulse text-primary" />
            <span>AI Automated Video Engine</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            Codebase to Animated Tutorial
          </h1>
          <p className="mt-1.5 text-sm sm:text-base text-muted-foreground max-w-2xl">
            Transform any public GitHub repository into a cinematic architecture walkthrough
            powered by <span className="font-semibold text-foreground">Repomix</span>,{" "}
            <span className="font-semibold text-foreground">Manim Community</span>, and{" "}
            <span className="font-semibold text-foreground">Neural Voiceover</span>.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono bg-card px-3 py-1.5 rounded-lg border border-border">
          <Cpu className="h-4 w-4 text-emerald-400 animate-pulse" />
          <span>Celery Worker: Active</span>
        </div>
      </div>

      {/* =================================================================== */}
      {/* Global Error Banner                                                 */}
      {/* =================================================================== */}
      {errorMessage && !jobId && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-destructive flex items-start gap-3 shadow-sm animate-in fade-in duration-300">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-destructive" />
          <div className="flex-1 text-sm">
            <p className="font-semibold">Pipeline Submission Notice</p>
            <p className="mt-0.5 text-xs opacity-90">{errorMessage}</p>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-xs font-medium underline hover:opacity-80"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* =================================================================== */}
      {/* Active Job Progress Tracking (Modular JobProgress Component)        */}
      {/* =================================================================== */}
      {jobId && jobStatus !== "IDLE" && (
        <div className="space-y-6">
          <JobProgress
            jobId={jobId}
            pollIntervalMs={3000}
            onComplete={(data) => {
              setJobStatus("SUCCESS");
              if (data.download_url) setDownloadUrl(data.download_url);
              const dur = data.result?.duration || (data.result as any)?.duration_seconds;
              if (dur) setVideoDuration(dur);
            }}
            onError={(err) => {
              setJobStatus("FAILURE");
              setErrorMessage(err);
            }}
            onReset={handleReset}
          />

          {/* Video Result View (Modular VideoPlayer Component on SUCCESS) */}
          {jobStatus === "SUCCESS" && (
            <VideoPlayer
              jobId={jobId}
              downloadUrl={downloadUrl || `/api/v1/jobs/${jobId}/download`}
              repoUrl={repoUrl}
              resolution={resolution}
              theme={theme}
              burnSubtitles={burnSubtitles}
              duration={videoDuration}
              onReset={handleReset}
            />
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* Interactive Video Generation Configuration Form                     */}
      {/* =================================================================== */}
      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-border bg-card/80 backdrop-blur-sm p-6 sm:p-8 shadow-sm space-y-8"
      >
        {/* Section 1: GitHub Repository Input */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
              <GithubIcon className="h-4 w-4 text-primary" />
              <span>GitHub Repository URL</span>
              <span className="text-destructive">*</span>
            </label>
            <span className="text-xs text-muted-foreground">
              Public GitHub repositories supported
            </span>
          </div>

          <div className="relative">
            <input
              type="text"
              placeholder="e.g. https://github.com/yamadashy/repomix or octocat/Hello-World"
              value={repoUrl}
              onChange={(e) => {
                setRepoUrl(e.target.value);
                setUrlTouched(true);
              }}
              className={cn(
                "w-full px-4 py-3 rounded-xl border bg-background text-sm text-foreground placeholder:text-muted-foreground/60 transition-all focus:outline-none focus:ring-2",
                urlTouched && !isValidUrl && repoUrl.trim()
                  ? "border-destructive focus:ring-destructive/30"
                  : urlTouched && isValidUrl
                  ? "border-emerald-500/80 focus:ring-emerald-500/30"
                  : "border-input focus:ring-primary/40 focus:border-primary"
              )}
            />
          </div>

          {/* Quick-select Repository Samples */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <FileCode2 className="h-3 w-3" /> Quick Test Samples:
            </span>
            {SAMPLE_REPOSITORIES.map((sample) => (
              <button
                key={sample.url}
                type="button"
                onClick={() => {
                  setRepoUrl(sample.url);
                  setUrlTouched(true);
                }}
                className="text-xs px-2.5 py-1 rounded-md bg-secondary text-secondary-foreground hover:bg-primary/20 hover:text-primary transition-colors border border-border"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>

        {/* Section 2: Gemini AI Architecture Model */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span>Gemini AI Synthesis Model</span>
            </label>
            <span className="text-xs text-muted-foreground">
              Official Google GenAI SDK (Multimodal Codebase Topology)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {AI_MODEL_OPTIONS.map((m) => {
              const isSelected = aiModel === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setAiModel(m.id)}
                  className={cn(
                    "flex flex-col items-start p-3.5 rounded-xl border text-left transition-all relative group",
                    isSelected
                      ? "border-primary bg-primary/10 shadow-sm ring-1 ring-primary/40"
                      : "border-border bg-background hover:bg-secondary/40 hover:border-border/80"
                  )}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="font-semibold text-sm text-foreground">
                      {m.name}
                    </span>
                    {m.badge && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-primary/20 text-primary font-medium">
                        {m.badge}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1 line-clamp-2">
                    {m.description}
                  </p>
                  {isSelected && (
                    <div className="absolute top-2 right-2 h-2 w-2 rounded-full bg-primary" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 3: Neural Voice Selection */}
        <div className="space-y-3">
          <label className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Volume2 className="h-4 w-4 text-primary" />
            <span>Narrator Voice Selection</span>
            <span className="text-xs font-normal text-muted-foreground">(Edge TTS & Neural Synthesis)</span>
          </label>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {VOICE_CATALOG.map((v) => {
              const isSelected = voice === v.id;
              return (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => setVoice(v.id)}
                  className={cn(
                    "flex flex-col items-start p-3.5 rounded-xl border text-left transition-all relative group",
                    isSelected
                      ? "border-primary bg-primary/10 shadow-sm ring-1 ring-primary/40"
                      : "border-border bg-background hover:bg-secondary/40 hover:border-border/80"
                  )}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="font-semibold text-sm text-foreground flex items-center gap-1.5">
                      {v.name}
                      <span className="text-[10px] text-muted-foreground font-normal">
                        ({v.gender})
                      </span>
                    </span>
                    {v.badge && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-primary/20 text-primary font-medium">
                        {v.badge}
                      </span>
                    )}
                  </div>

                  <span className="text-[11px] font-medium text-primary/80">
                    {v.category}
                  </span>
                  <p className="text-[11px] text-muted-foreground mt-1 line-clamp-1">
                    {v.tone}
                  </p>

                  {isSelected && (
                    <div className="absolute top-2 right-2 h-2 w-2 rounded-full bg-primary" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 3: Resolution & Subtitle Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Resolution Toggle */}
          <div className="space-y-3">
            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Monitor className="h-4 w-4 text-primary" />
              <span>Video Resolution</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "1080p", label: "1080p Full HD", sub: "1920x1080 • 60fps" },
                { id: "720p", label: "720p HD", sub: "1280x720 • Fast" },
                { id: "480p", label: "480p Mobile", sub: "854x480 • Draft" },
              ].map((res) => {
                const isSelected = resolution === res.id;
                return (
                  <button
                    key={res.id}
                    type="button"
                    onClick={() => setResolution(res.id as any)}
                    className={cn(
                      "flex flex-col items-center justify-center py-3 px-2 rounded-xl border text-center transition-all",
                      isSelected
                        ? "border-primary bg-primary/10 shadow-sm ring-1 ring-primary/40 font-semibold text-primary"
                        : "border-border bg-background hover:bg-secondary/40 text-muted-foreground"
                    )}
                  >
                    <span className="text-sm">{res.label}</span>
                    <span className="text-[10px] opacity-75">{res.sub}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Subtitle Burn-in Checkbox */}
          <div className="space-y-3">
            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Subtitles className="h-4 w-4 text-primary" />
              <span>Subtitle & Caption Overlay</span>
            </label>
            <div
              onClick={() => setBurnSubtitles(!burnSubtitles)}
              className={cn(
                "flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer select-none transition-all",
                burnSubtitles
                  ? "border-primary/60 bg-primary/5"
                  : "border-border bg-background hover:bg-secondary/30"
              )}
            >
              <input
                type="checkbox"
                checked={burnSubtitles}
                onChange={() => {}} // Container handles toggle
                className="mt-1 h-4 w-4 rounded border-border text-primary focus:ring-primary cursor-pointer"
              />
              <div>
                <p className="text-sm font-semibold text-foreground">
                  Burn synchronized subtitles directly into video
                </p>
                <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                  Embeds high-visibility yellow/white ASS subtitle text synced millisecond-by-millisecond to the voiceover for YouTube, LinkedIn, or Twitter.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: Manim Diagram Theme Selector */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Palette className="h-4 w-4 text-primary" />
              <span>Manim Diagram Theme</span>
            </label>
            <span className="text-xs text-muted-foreground">
              Customizes architectural nodes & connection aesthetics
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {THEME_OPTIONS.map((t) => {
              const isSelected = theme === t.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTheme(t.id)}
                  className={cn(
                    "flex flex-col p-3 rounded-xl border text-left transition-all relative overflow-hidden",
                    isSelected
                      ? "border-primary bg-primary/10 ring-1 ring-primary/40 shadow-sm"
                      : "border-border bg-background hover:bg-secondary/40"
                  )}
                >
                  {/* Color Swatch Preview */}
                  <div
                    className="w-full h-8 rounded-lg mb-2 flex items-center justify-around px-2 border"
                    style={{ backgroundColor: t.bgHex, borderColor: t.borderHex }}
                  >
                    <div
                      className="h-3 w-3 rounded-full shadow"
                      style={{ backgroundColor: t.accentHex }}
                    />
                    <div
                      className="h-2 w-6 rounded-full opacity-60"
                      style={{ backgroundColor: t.accentHex }}
                    />
                  </div>

                  <span className="text-xs font-bold text-foreground">
                    {t.name}
                  </span>
                  <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-1">
                    {t.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Section 5: Advanced Options (Custom Instructions) */}
        <div className="space-y-2 border-t border-border/70 pt-4">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
          >
            <Sliders className="h-3.5 w-3.5" />
            <span>{showAdvanced ? "Hide Advanced Prompt Customization" : "Custom Instructions & Focus Prompts (Optional)"}</span>
          </button>

          {showAdvanced && (
            <div className="pt-2 animate-in fade-in duration-200">
              <textarea
                rows={3}
                placeholder="e.g. 'Focus primarily on how the Celery async worker interacts with Redis and Repomix parsing. Emphasize error recovery.'"
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-input bg-background text-xs sm:text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
              />
              <p className="text-[11px] text-muted-foreground mt-1 flex items-center gap-1">
                <Info className="h-3 w-3" />
                This prompt guides the Gemini AI technical writer to highlight specific design patterns or modules.
              </p>
            </div>
          )}
        </div>

        {/* Section 6: Submit Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
          <div className="text-xs text-muted-foreground">
            ⚡ Consumes <span className="font-semibold text-foreground">1 Credit</span> per generated tutorial
          </div>

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={isSubmitting || (jobStatus === "PROCESSING" && !errorMessage)}
              className={cn(
                "inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-bold text-sm text-primary-foreground shadow-lg transition-all",
                isSubmitting || (jobStatus === "PROCESSING" && !errorMessage)
                  ? "bg-primary/50 cursor-not-allowed opacity-75"
                  : "bg-primary hover:bg-primary/90 shadow-primary/25 hover:shadow-primary/40 active:scale-[0.99]"
              )}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Submitting to Pipeline...</span>
                </>
              ) : jobStatus === "PROCESSING" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Rendering Video...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Generate Animated Tutorial</span>
                  <ArrowRight className="h-4 w-4 ml-1" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
