"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Code2,
  Key,
  Copy,
  Check,
  ExternalLink,
  BookOpen,
  Webhook,
  ShieldCheck,
  Zap,
  Terminal,
  RefreshCw,
  Send,
  AlertCircle,
  FileCode,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function ApiWebhooksPage() {
  const [apiKey, setApiKey] = useState("cv_live_99f8a12e8b4a7d61c0e352");
  const [showKey, setShowKey] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("https://myapp.com/api/webhooks/codevideo");
  const [selectedLanguage, setSelectedLanguage] = useState<"curl" | "python" | "typescript">("curl");
  const [copiedSnippet, setCopiedSnippet] = useState(false);
  const [webhookTestStatus, setWebhookTestStatus] = useState<"IDLE" | "SENDING" | "SUCCESS">("IDLE");

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const handleRollKey = () => {
    const newKey = "cv_live_" + Array.from({ length: 22 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
    setApiKey(newKey);
  };

  const handleTestWebhook = () => {
    setWebhookTestStatus("SENDING");
    setTimeout(() => {
      setWebhookTestStatus("SUCCESS");
      setTimeout(() => setWebhookTestStatus("IDLE"), 3000);
    }, 1000);
  };

  const SNIPPETS = {
    curl: `curl -X POST "http://127.0.0.1:8000/api/v1/generate-video" \\
  -H "Authorization: Bearer ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "repo_url": "https://github.com/tiangolo/fastapi",
    "voice": "en-US-ChristopherNeural",
    "resolution": "1080p",
    "theme": "midnight",
    "gemini_model": "gemini-2.5-flash",
    "burn_subtitles": true
  }'`,
    python: `from codevideo_client import ApiClient, Configuration, VideoGenerationPipelineApi
from codevideo_client.models import GenerateVideoRequest

# Initialize SDK client
config = Configuration(
    host="http://127.0.0.1:8000",
    access_token="${apiKey}"
)
client = ApiClient(config)
api = VideoGenerationPipelineApi(client)

# Trigger video generation
req = GenerateVideoRequest(
    repo_url="https://github.com/tiangolo/fastapi",
    voice="en-US-ChristopherNeural",
    resolution="1080p",
    theme="midnight",
    gemini_model="gemini-2.5-flash",
    burn_subtitles=True
)
response = api.generate_video_api_v1_generate_video_post(req)
print(f"Scheduled Job ID: {response.job_id}")`,
    typescript: `import { VideoGenerationPipelineApi, Configuration } from "./src/api";

const api = new VideoGenerationPipelineApi(
  new Configuration({
    basePath: "http://127.0.0.1:8000",
    accessToken: "${apiKey}"
  })
);

// Trigger video tutorial generation
const res = await api.generateVideoApiV1GenerateVideoPost({
  generateVideoRequest: {
    repo_url: "https://github.com/tiangolo/fastapi",
    voice: "en-US-ChristopherNeural",
    resolution: "1080p",
    theme: "midnight",
    gemini_model: "gemini-2.5-flash",
    burn_subtitles: true
  }
});

console.log("Job Scheduled:", res.job_id);`,
  };

  const handleCopySnippet = () => {
    navigator.clipboard.writeText(SNIPPETS[selectedLanguage]);
    setCopiedSnippet(true);
    setTimeout(() => setCopiedSnippet(false), 2000);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-border/70">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 mb-2">
            <Code2 className="h-3.5 w-3.5 text-primary" />
            <span>Developer Platform & Integrations</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            API & Webhooks
          </h1>
          <p className="mt-1 text-sm text-muted-foreground max-w-2xl">
            Integrate codebase tutorial video generation directly into CI/CD pipelines, documentation hubs, or PR bots.
          </p>
        </div>

        {/* Quick Docs Links */}
        <div className="flex flex-wrap items-center gap-2">
          <a
            href="http://127.0.0.1:8000/scalar"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm transition-colors"
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>Scalar Interactive Reference</span>
            <ExternalLink className="h-3 w-3 opacity-70" />
          </a>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold border border-border bg-card hover:bg-secondary transition-colors"
          >
            <span>Swagger UI</span>
            <ExternalLink className="h-3 w-3 text-muted-foreground" />
          </a>
        </div>
      </div>

      {/* API Key Management */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="h-4 w-4 text-primary" />
            <h3 className="font-bold text-sm text-foreground">API Credentials</h3>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            Status: Active
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative w-full">
            <input
              type={showKey ? "text" : "password"}
              readOnly
              value={apiKey}
              className="w-full px-4 py-2.5 rounded-xl border border-input bg-background font-mono text-xs text-foreground focus:outline-none"
            />
            <button
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-2.5 text-xs text-muted-foreground hover:text-foreground"
            >
              {showKey ? "Hide" : "Show"}
            </button>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto shrink-0">
            <button
              onClick={handleCopyKey}
              className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold bg-secondary text-foreground hover:bg-secondary/80 border border-border transition-colors w-full sm:w-auto"
            >
              {copiedKey ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy Key</span>
                </>
              )}
            </button>

            <button
              onClick={handleRollKey}
              className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors w-full sm:w-auto"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Roll Key</span>
            </button>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          Include this key as a Bearer token in the <code className="font-mono text-foreground font-semibold">Authorization</code> header. Keep your key confidential.
        </p>
      </div>

      {/* Code Snippets Integration */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-primary" />
            <h3 className="font-bold text-sm text-foreground">Integration Code Samples</h3>
          </div>

          {/* Language Switcher */}
          <div className="flex items-center gap-1 bg-secondary p-1 rounded-lg border border-border self-start sm:self-auto">
            {(["curl", "python", "typescript"] as const).map((lang) => (
              <button
                key={lang}
                onClick={() => setSelectedLanguage(lang)}
                className={cn(
                  "px-3 py-1 rounded-md text-xs font-semibold transition-all capitalize",
                  selectedLanguage === lang
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {lang === "curl" ? "cURL" : lang === "python" ? "Python SDK" : "TypeScript"}
              </button>
            ))}
          </div>
        </div>

        <div className="relative">
          <pre className="p-4 rounded-xl bg-secondary/60 text-foreground font-mono text-xs overflow-x-auto border border-border/80">
            <code>{SNIPPETS[selectedLanguage]}</code>
          </pre>
          <button
            onClick={handleCopySnippet}
            className="absolute top-3 right-3 inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground bg-card/90 px-2.5 py-1.5 rounded-lg border border-border backdrop-blur-sm transition-colors"
          >
            {copiedSnippet ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Webhooks Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Webhook className="h-4 w-4 text-primary" />
            <h3 className="font-bold text-sm text-foreground">Webhook Subscriptions</h3>
          </div>
          <p className="text-xs text-muted-foreground">
            Receive automated real-time HTTP POST notifications when a video finishes rendering.
          </p>

          <div className="space-y-3">
            <div>
              <label className="text-[11px] font-semibold text-muted-foreground uppercase">
                Endpoint URL
              </label>
              <input
                type="text"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                className="w-full mt-1 px-3.5 py-2.5 rounded-xl border border-input bg-background font-mono text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase block">
                Subscribed Events
              </span>
              {["job.started", "job.progress (25%, 50%, 75%)", "job.completed (with MP4 URL)", "job.failed"].map((evt) => (
                <div key={evt} className="flex items-center gap-2 text-xs text-foreground">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  <span>{evt}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleTestWebhook}
              disabled={webhookTestStatus === "SENDING"}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-secondary hover:bg-secondary/80 border border-border transition-colors mt-2"
            >
              {webhookTestStatus === "SENDING" ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Dispatching Ping...</span>
                </>
              ) : webhookTestStatus === "SUCCESS" ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                  <span>200 OK Delivered!</span>
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  <span>Send Test Ping</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Rate Limits & Quotas */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <h3 className="font-bold text-sm text-foreground">Rate Limits & Token Bucket</h3>
          </div>
          <p className="text-xs text-muted-foreground">
            Protects your infrastructure using moving-window token bucket enforcement.
          </p>

          <div className="space-y-2.5 text-xs">
            <div className="p-3 rounded-xl bg-secondary/40 border border-border flex items-center justify-between">
              <span className="text-muted-foreground">Standard HTTP Queries</span>
              <span className="font-mono font-bold text-foreground">120 requests / min</span>
            </div>
            <div className="p-3 rounded-xl bg-secondary/40 border border-border flex items-center justify-between">
              <span className="text-muted-foreground">Video Generation Pipeline</span>
              <span className="font-mono font-bold text-primary">5 generations / min</span>
            </div>
            <div className="p-3 rounded-xl bg-secondary/40 border border-border flex items-center justify-between">
              <span className="text-muted-foreground">SSE Live Stream Sessions</span>
              <span className="font-mono font-bold text-emerald-400">Unlimited Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

