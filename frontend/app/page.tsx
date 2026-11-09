"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Play,
  Pause,
  CheckCircle2,
  Sparkles,
  Code2,
  Layers,
  Volume2,
  Zap,
  ArrowRight,
  ShieldCheck,
  Terminal,
  Film,
  ExternalLink,
  Star,
  Clock,
  CreditCard,
  ChevronRight,
  Cpu,
  GitBranch,
  Sliders,
  Download,
  MonitorPlay,
  Flame,
  QrCode,
} from "lucide-react";
import { GithubIcon } from "@/components/icons";

export default function LandingPage() {
  const [isPlayingDemo, setIsPlayingDemo] = useState(true);

  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background radial gradient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[550px] bg-gradient-to-b from-indigo-600/15 via-emerald-500/10 to-transparent blur-3xl pointer-events-none -z-10" />

      {/* ----------------------------------------------------------------------- */}
      {/* 1. Navigation Header                                                    */}
      {/* ----------------------------------------------------------------------- */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-400 p-[1px] shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition">
              <div className="h-full w-full bg-slate-950 rounded-[11px] flex items-center justify-center">
                <Film className="h-4 w-4 text-emerald-400 group-hover:scale-110 transition-transform" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-base tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Codebase<span className="text-emerald-400">2</span>Video
              </span>
              <span className="text-[10px] text-slate-400 font-mono tracking-widest uppercase">
                Studio Engine
              </span>
            </div>
          </Link>

          {/* Center Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-emerald-400 transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-emerald-400 transition-colors">
              How It Works
            </a>
            <a href="#pricing" className="hover:text-emerald-400 transition-colors">
              Pricing
            </a>
            <a href="#faq" className="hover:text-emerald-400 transition-colors">
              FAQ
            </a>
          </nav>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 border border-slate-800 hover:border-slate-700 hover:text-white transition"
            >
              <GithubIcon className="h-3.5 w-3.5" />
              <span>Open Source</span>
            </a>

            <Link
              href="/login"
              className="text-xs sm:text-sm font-medium text-slate-300 hover:text-white px-3 py-1.5 transition"
            >
              Sign In
            </Link>

            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-4 py-2 rounded-lg shadow-sm shadow-emerald-500/25 transition active:scale-95"
            >
              <span>Get Started</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* ----------------------------------------------------------------------- */}
      {/* 2. Hero Section                                                         */}
      {/* ----------------------------------------------------------------------- */}
      <section className="relative pt-16 sm:pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
        {/* Release Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-medium mb-8 backdrop-blur-sm shadow-inner shadow-indigo-500/20">
          <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
          <span>v1.0 Powered by Repomix, Manim & Google Gemini</span>
          <ChevronRight className="h-3 w-3 text-indigo-400" />
        </div>

        {/* Main Title */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight max-w-4xl mx-auto leading-[1.1] text-white">
          Transform Any Codebase into{" "}
          <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
            Animated Video Tutorials
          </span>
        </h1>

        {/* Subtitle */}
        <p className="mt-6 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Autonomous end-to-end engine that packages GitHub repositories with Repomix,
          synthesizes architectural diagrams with Gemini, renders smooth vector animations with Manim,
          and voices over with neural TTS.
        </p>

        {/* CTAs */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 text-base font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-8 py-3.5 rounded-xl shadow-lg shadow-emerald-500/25 transition-all hover:scale-[1.02] active:scale-95"
          >
            <Sparkles className="h-4 w-4" />
            <span>Generate Video Tutorial</span>
            <ArrowRight className="h-4 w-4" />
          </Link>

          <a
            href="#how-it-works"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 text-base font-medium text-slate-300 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 px-6 py-3.5 rounded-xl transition"
          >
            <Play className="h-4 w-4 text-emerald-400" />
            <span>See How It Works</span>
          </a>
        </div>

        {/* Trust Badges */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>100% Autonomous Pipeline</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>Full HD 1080p 60fps</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>Synced .SRT Subtitle Burn-In</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>$9 Pay-As-You-Go Credits</span>
          </div>
        </div>

        {/* ------------------------------------------------------------------- */}
        {/* Demo Video Mockup Window                                            */}
        {/* ------------------------------------------------------------------- */}
        <div className="mt-14 max-w-5xl mx-auto rounded-2xl border border-slate-800 bg-slate-900/50 p-2 sm:p-3 shadow-2xl shadow-indigo-950/50 backdrop-blur-sm">
          <div className="rounded-xl border border-slate-800/80 bg-slate-950 overflow-hidden shadow-inner">
            {/* Window Title Bar */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 bg-slate-900/60">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-rose-500/80 inline-block" />
                <span className="h-3 w-3 rounded-full bg-amber-500/80 inline-block" />
                <span className="h-3 w-3 rounded-full bg-emerald-500/80 inline-block" />
                <span className="ml-3 font-mono text-xs text-slate-400 hidden sm:inline-block">
                  https://github.com/fastapi/fastapi ➔ generated_tutorial.mp4
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono text-[11px] border border-emerald-500/20">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  1080p 60fps
                </span>
                <span className="font-mono text-xs text-slate-500 hidden sm:inline-block">
                  Manim Community v0.18.0
                </span>
              </div>
            </div>

            {/* Video Canvas Mockup */}
            <div className="relative aspect-video w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 flex flex-col justify-between p-4 sm:p-8 select-none">
              {/* Scene Watermark / Chapter Header */}
              <div className="flex items-center justify-between text-xs sm:text-sm">
                <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-lg backdrop-blur-md">
                  <Cpu className="h-4 w-4 text-emerald-400" />
                  <span className="font-medium text-slate-200">
                    Scene 2: Core Microservices & Celery Queue Topology
                  </span>
                </div>
                <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-900/60 border border-slate-800 px-2.5 py-1 rounded">
                  <span>Theme: Midnight</span>
                </div>
              </div>

              {/* Animated Architecture Diagram Visual */}
              <div className="my-auto py-6 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8">
                {/* Node 1: Public Repo */}
                <div className="flex flex-col items-center p-4 rounded-xl border border-indigo-500/30 bg-indigo-950/30 w-44 shadow-lg shadow-indigo-950/50">
                  <div className="h-10 w-10 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center mb-2">
                    <Code2 className="h-5 w-5 text-indigo-400" />
                  </div>
                  <span className="text-xs font-bold text-white">GitHub Repo</span>
                  <span className="text-[10px] font-mono text-indigo-300">Repomix AST Extract</span>
                </div>

                {/* Animated Flow Arrow 1 */}
                <div className="flex flex-col items-center justify-center text-slate-500">
                  <div className="h-0.5 w-8 sm:w-16 bg-gradient-to-r from-indigo-500 via-emerald-400 to-teal-400 relative">
                    <div className="absolute -top-1 right-0 h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                  </div>
                  <span className="text-[9px] font-mono mt-1 text-slate-400">AST Analysis</span>
                </div>

                {/* Node 2: Gemini LLM Reasoner */}
                <div className="flex flex-col items-center p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 w-48 shadow-lg shadow-emerald-950/50">
                  <div className="h-10 w-10 rounded-lg bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center mb-2">
                    <Sparkles className="h-5 w-5 text-emerald-400" />
                  </div>
                  <span className="text-xs font-bold text-white">Gemini 2.5 Flash</span>
                  <span className="text-[10px] font-mono text-emerald-300">Topology & Scripting</span>
                </div>

                {/* Animated Flow Arrow 2 */}
                <div className="flex flex-col items-center justify-center text-slate-500">
                  <div className="h-0.5 w-8 sm:w-16 bg-gradient-to-r from-emerald-400 via-teal-400 to-indigo-500 relative">
                    <div className="absolute -top-1 right-0 h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
                  </div>
                  <span className="text-[9px] font-mono mt-1 text-slate-400">Vector Math</span>
                </div>

                {/* Node 3: Manim Renderer */}
                <div className="flex flex-col items-center p-4 rounded-xl border border-teal-500/30 bg-teal-950/30 w-44 shadow-lg shadow-teal-950/50">
                  <div className="h-10 w-10 rounded-lg bg-teal-600/20 border border-teal-500/40 flex items-center justify-center mb-2">
                    <Film className="h-5 w-5 text-teal-400" />
                  </div>
                  <span className="text-xs font-bold text-white">Manim Engine</span>
                  <span className="text-[10px] font-mono text-teal-300">Smooth 60fps Curves</span>
                </div>
              </div>

              {/* Real Subtitle Overlay (FastStart Demo) */}
              <div className="max-w-2xl mx-auto w-full text-center">
                <div className="inline-block px-4 py-2 rounded-lg bg-black/80 border border-slate-800/80 backdrop-blur-md shadow-lg">
                  <p className="text-xs sm:text-sm font-medium text-slate-100 tracking-wide">
                    &ldquo;In this architecture, incoming requests are parsed by the FastAPI gateway,
                    which dispatches asynchronous animation tasks to Celery and Redis.&rdquo;
                  </p>
                </div>
              </div>

              {/* Scrubbing & Controls Bar */}
              <div className="mt-4 pt-3 border-t border-slate-800/70 flex items-center justify-between gap-3 text-xs text-slate-400">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsPlayingDemo(!isPlayingDemo)}
                    className="h-8 w-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-white flex items-center justify-center transition"
                  >
                    {isPlayingDemo ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                  </button>
                  <span className="font-mono text-[11px] text-slate-300">01:24 / 03:45</span>
                </div>

                {/* Timeline Bar */}
                <div className="flex-1 mx-2 sm:mx-4 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full w-2/5 bg-gradient-to-r from-emerald-500 to-indigo-500 rounded-full" />
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-slate-800 font-mono text-[10px] text-slate-300">
                    CC ON
                  </span>
                  <Volume2 className="h-4 w-4 text-slate-400" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------------- */}
      {/* 3. Tech Stack Open-Source Foundation                                   */}
      {/* ----------------------------------------------------------------------- */}
      <section className="py-12 border-y border-slate-800/60 bg-slate-900/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs font-semibold uppercase tracking-wider text-slate-400 mb-6">
            Powered by Leading Open-Source Engines & Developer Platforms
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-6 items-center justify-items-center opacity-85">
            <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
              <Layers className="h-4 w-4 text-indigo-400" />
              <span>Repomix</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
              <Film className="h-4 w-4 text-teal-400" />
              <span>Manim Community</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
              <Sparkles className="h-4 w-4 text-emerald-400" />
              <span>Google Gemini</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
              <Volume2 className="h-4 w-4 text-amber-400" />
              <span>Edge-TTS</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
              <Zap className="h-4 w-4 text-rose-400" />
              <span>FFmpeg</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
              <Terminal className="h-4 w-4 text-cyan-400" />
              <span>Celery & Redis</span>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------------- */}
      {/* 4. Features Breakdown                                                  */}
      {/* ----------------------------------------------------------------------- */}
      <section id="features" className="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-semibold text-emerald-400 tracking-wider uppercase">
            Built for Developer Experience
          </h2>
          <p className="mt-2 text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Everything Required to Turn Complex Code into Engaging Video
          </p>
          <p className="mt-4 text-base text-slate-400">
            From raw Git commits to final rendered MP4, our automated pipeline eliminates manual video production overhead.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1: Repomixing */}
          <div className="group rounded-2xl border border-slate-800 bg-slate-900/40 p-8 hover:border-indigo-500/50 hover:bg-slate-900/70 transition-all duration-300 relative overflow-hidden">
            <div className="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Layers className="h-6 w-6 text-indigo-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">
              Intelligent Repomix Ingestion
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Clones any public GitHub repository into an isolated sandbox. Filters out
              bloated dependencies (<code className="text-xs text-indigo-300 bg-indigo-950/60 px-1 py-0.5 rounded">node_modules</code>, binaries, lockfiles)
              and packages the entire codebase into a clean, token-compressed AST map.
            </p>
            <ul className="mt-6 space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400" />
                Automatic directory topology scanning
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400" />
                Language & framework detection
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400" />
                Token-efficient Markdown packaging
              </li>
            </ul>
          </div>

          {/* Feature 2: Manim Community Vector Animations */}
          <div className="group rounded-2xl border border-slate-800 bg-slate-900/40 p-8 hover:border-emerald-500/50 hover:bg-slate-900/70 transition-all duration-300 relative overflow-hidden">
            <div className="h-12 w-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Film className="h-6 w-6 text-emerald-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">
              Manim Architectural Animations
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Dynamically synthesizes Python Manim scene scripts rendering mathematical
              vector diagrams. Visualizes data flow through backend microservices, Redis queues,
              and databases with glowing connectors and camera motion.
            </p>
            <ul className="mt-6 space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                Smooth 60fps vector animations
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                Midnight, Cyberpunk & Nord themes
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                Dynamic camera zooms & node highlights
              </li>
            </ul>
          </div>

          {/* Feature 3: TTS Voiceover & Subtitles */}
          <div className="group rounded-2xl border border-slate-800 bg-slate-900/40 p-8 hover:border-teal-500/50 hover:bg-slate-900/70 transition-all duration-300 relative overflow-hidden">
            <div className="h-12 w-12 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Volume2 className="h-6 w-6 text-teal-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">
              Neural Voiceover & Synced Subtitles
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Transforms Gemini-synthesized technical narration into human-like voiceover audio.
              Generates word-level timestamped <code className="text-xs text-teal-300 bg-teal-950/60 px-1 py-0.5 rounded">.srt</code> subtitles
              burned directly into the video stream for seamless clarity.
            </p>
            <ul className="mt-6 space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-400" />
                Multiple regional neural voice models
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-400" />
                Sub-second audio-video duration sync
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-teal-400" />
                Permanent burned-in subtitle overlay
              </li>
            </ul>
          </div>
        </div>

        {/* Secondary Feature Row */}
        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/80 bg-slate-900/20">
            <Zap className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-white">FFmpeg FastStart</h4>
              <p className="text-xs text-slate-400 mt-1">
                Optimized MP4 container moov atom placement for instant web streaming without full video download.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/80 bg-slate-900/20">
            <ShieldCheck className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-white">Cloud S3 Storage</h4>
              <p className="text-xs text-slate-400 mt-1">
                Secure signed download links powered by AWS S3 / Cloudinary for fast, distributed global delivery.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 rounded-xl border border-slate-800/80 bg-slate-900/20">
            <Terminal className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-white">Prometheus & Sentry</h4>
              <p className="text-xs text-slate-400 mt-1">
                Complete system observability with Prometheus /metrics for Grafana and automated Sentry error capture.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------------- */}
      {/* 5. How It Works (Step-by-Step)                                          */}
      {/* ----------------------------------------------------------------------- */}
      <section id="how-it-works" className="py-20 border-t border-slate-800/60 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-xs font-semibold text-indigo-400 tracking-wider uppercase">
              Workflow
            </h2>
            <p className="mt-2 text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              From Git URL to Video in 4 Steps
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Step 1 */}
            <div className="relative p-6 rounded-2xl border border-slate-800 bg-slate-900/40">
              <span className="text-3xl font-extrabold text-indigo-500/40 font-mono mb-4 block">
                01
              </span>
              <h3 className="text-base font-bold text-white mb-2">Paste Repository</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Enter any public GitHub URL (e.g. <span className="font-mono text-slate-300">octocat/Hello-World</span>). No repo access tokens needed.
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative p-6 rounded-2xl border border-slate-800 bg-slate-900/40">
              <span className="text-3xl font-extrabold text-emerald-500/40 font-mono mb-4 block">
                02
              </span>
              <h3 className="text-base font-bold text-white mb-2">Customize Studio</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Choose your narrator voice model, resolution (1080p/720p), visual theme (Midnight, Cyberpunk), and custom focus notes.
              </p>
            </div>

            {/* Step 3 */}
            <div className="relative p-6 rounded-2xl border border-slate-800 bg-slate-900/40">
              <span className="text-3xl font-extrabold text-teal-500/40 font-mono mb-4 block">
                03
              </span>
              <h3 className="text-base font-bold text-white mb-2">Autonomous Render</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Watch the live 5-stage progress bar in real time as Repomix, Gemini, Manim, and FFmpeg compose the tutorial.
              </p>
            </div>

            {/* Step 4 */}
            <div className="relative p-6 rounded-2xl border border-slate-800 bg-slate-900/40">
              <span className="text-3xl font-extrabold text-amber-500/40 font-mono mb-4 block">
                04
              </span>
              <h3 className="text-base font-bold text-white mb-2">Download & Share</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Stream the generated tutorial in your browser or download the full broadcast-quality HD MP4 with commercial license.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------------- */}
      {/* 6. Pricing Table ($9/video Credit Tier)                                 */}
      {/* ----------------------------------------------------------------------- */}
      <section id="pricing" className="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-semibold text-emerald-400 tracking-wider uppercase">
            Transparent Pricing
          </h2>
          <p className="mt-2 text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Pay Only for Videos You Generate
          </p>
          <p className="mt-4 text-base text-slate-400">
            No recurring hidden subscriptions. Buy video credits on-demand via Binance Pay (1 USDT) or Stripe checkout.
          </p>
        </div>

        {/* Binance Pay Special Callout */}
        <div className="mb-12 rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-500/15 via-amber-500/5 to-slate-900/60 p-6 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xl shadow-amber-500/5">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center shrink-0">
              <QrCode className="h-6 w-6 text-amber-400" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/40 mb-1">
                Crypto Special • 1 USDT = 1 Video
              </div>
              <h3 className="text-base sm:text-lg font-bold text-white">
                Pay with Binance Pay for Just 1 USDT
              </h3>
              <p className="text-xs text-slate-300">
                Scan the official Binance QR code to pay 1 USDT. 1 video tutorial credit is deposited automatically upon payment.
              </p>
            </div>
          </div>

          <Link
            href="/dashboard/billing"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-bold text-xs bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-md shadow-amber-500/25 transition-all hover:scale-[1.02] active:scale-95 shrink-0"
          >
            <QrCode className="h-4 w-4" />
            <span>Pay 1 USDT on Binance</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch">
          {/* Tier 1: Pay-as-you-go ($9) */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">Single Tutorial</h3>
                <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  Pay-As-You-Go
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-6">
                Perfect for open-source maintainers announcing a new feature or releasing a library.
              </p>

              <div className="mb-6 flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-white">$9</span>
                <span className="text-xs text-slate-400">/ video tutorial</span>
              </div>

              <div className="space-y-3 text-xs text-slate-300 pt-6 border-t border-slate-800">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>1 Full HD (1080p 60fps) Tutorial Video</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Repomix Ingestion & AST Topology Map</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Manim Vector Architecture Animation</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Neural Voiceover + Burned-in Subtitles</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Full Commercial & YouTube Publishing Rights</span>
                </div>
              </div>
            </div>

            <Link
              href="/dashboard/billing"
              className="mt-8 block w-full text-center py-3 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition"
            >
              Buy 1 Video Credit ($9)
            </Link>
          </div>

          {/* Tier 2: Pro Bundle ($39 for 5 - Most Popular) */}
          <div className="rounded-2xl border-2 border-emerald-500 bg-slate-900/80 p-8 flex flex-col justify-between shadow-xl shadow-emerald-500/10 relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-emerald-500 text-slate-950 font-bold text-[10px] tracking-wider uppercase">
              Most Popular • Save 15%
            </div>

            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">Pro Creator Bundle</h3>
                <span className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                  5 Videos
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-6">
                Designed for developer educators, tech bloggers, and active software agencies.
              </p>

              <div className="mb-6 flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-white">$39</span>
                <span className="text-xs text-slate-400">/ 5 video credits ($7.80/video)</span>
              </div>

              <div className="space-y-3 text-xs text-slate-300 pt-6 border-t border-slate-800">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Everything in Single Tier</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Priority Celery Queue Processing</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Choice of 12+ Neural Voice Models</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Custom Gemini Script Focus Instructions</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Extended 30-Day S3 Cloud Video Retention</span>
                </div>
              </div>
            </div>

            <Link
              href="/dashboard/billing"
              className="mt-8 block w-full text-center py-3 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-md shadow-emerald-500/20 transition active:scale-95"
            >
              Get Pro Bundle ($39)
            </Link>
          </div>

          {/* Tier 3: Team Tier ($99 for 15) */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">DevRel & Team</h3>
                <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  15 Videos
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-6">
                For developer relations teams automating product walkthroughs and onboarding docs.
              </p>

              <div className="mb-6 flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-white">$99</span>
                <span className="text-xs text-slate-400">/ 15 video credits ($6.60/video)</span>
              </div>

              <div className="space-y-3 text-xs text-slate-300 pt-6 border-t border-slate-800">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Everything in Pro Bundle</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Unlimited S3 Cloud Storage Retention</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Webhook Notifications on Job Completion</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Custom Organization Branding / Watermark</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Prometheus Metrics Export & Dedicated Worker</span>
                </div>
              </div>
            </div>

            <Link
              href="/dashboard/billing"
              className="mt-8 block w-full text-center py-3 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition"
            >
              Get Team Bundle ($99)
            </Link>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------------- */}
      {/* 7. Frequently Asked Questions                                           */}
      {/* ----------------------------------------------------------------------- */}
      <section id="faq" className="py-20 border-t border-slate-800/60 bg-slate-950">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-xs font-semibold text-emerald-400 tracking-wider uppercase">
              Frequently Asked Questions
            </h2>
            <p className="mt-2 text-3xl font-extrabold text-white tracking-tight">
              Got Questions? We’ve Got Answers.
            </p>
          </div>

          <div className="space-y-6">
            <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/40">
              <h3 className="text-sm sm:text-base font-semibold text-white mb-2">
                How does Repomix prevent bloated files from blowing up LLM context?
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Repomix includes comprehensive ignore patterns that strip heavy build artifacts,
                minified bundles, package lockfiles, binaries, images, and virtual environment directories.
                Only essential architecture and entry-point source files are parsed and compressed.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/40">
              <h3 className="text-sm sm:text-base font-semibold text-white mb-2">
                Can I publish the generated videos on YouTube or monetize them?
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Yes! Every video generated through your credits comes with full commercial rights.
                You are free to upload the videos to YouTube, embed them in your product documentation,
                or use them in marketing campaigns.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/40">
              <h3 className="text-sm sm:text-base font-semibold text-white mb-2">
                What if video rendering fails due to an invalid repo?
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Our pipeline features automated validation. If a job fails during cloning or rendering,
                your credits are automatically restored to your balance, and Sentry captures the error
                for quick resolution.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/40">
              <h3 className="text-sm sm:text-base font-semibold text-white mb-2">
                How long does it take to render a typical video?
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Most tutorials complete in 60 to 90 seconds. The Celery worker processes all 5 stages in parallel
                batches: AST ingestion (5s) ➔ Gemini synthesis (10s) ➔ Manim animation rendering (25s) ➔
                TTS audio (5s) ➔ FFmpeg composition (15s).
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------------- */}
      {/* 8. Bottom High-Converting CTA Banner                                    */}
      {/* ----------------------------------------------------------------------- */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="relative rounded-3xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/60 via-slate-900 to-emerald-950/60 p-8 sm:p-14 overflow-hidden text-center shadow-2xl shadow-indigo-950/50">
          <div className="absolute top-0 right-0 -translate-y-12 translate-x-12 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

          <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight max-w-2xl mx-auto">
            Ready to Turn Your Codebase into an Animated Video?
          </h2>
          <p className="mt-4 text-slate-300 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
            Stop recording manual screencasts. Generate broadcast-ready architecture walkthroughs in minutes.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 text-sm sm:text-base font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-8 py-3.5 rounded-xl shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 active:scale-95"
            >
              <Sparkles className="h-4 w-4" />
              <span>Launch Studio Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/dashboard/billing"
              className="inline-flex items-center gap-2 text-sm sm:text-base font-medium text-slate-300 bg-slate-900/90 hover:bg-slate-800 border border-slate-700 px-6 py-3.5 rounded-xl transition"
            >
              <CreditCard className="h-4 w-4 text-emerald-400" />
              <span>Buy $9 Credits</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------------- */}
      {/* 9. Footer                                                               */}
      {/* ----------------------------------------------------------------------- */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-12 text-slate-400 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="h-6 w-6 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
              <Film className="h-3.5 w-3.5 text-emerald-400" />
            </div>
            <span className="font-semibold text-slate-200">
              Codebase2Video Studio
            </span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-500">© 2026 Open Source Project</span>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-slate-400">
            <Link href="/dashboard" className="hover:text-emerald-400 transition">
              Dashboard
            </Link>
            <Link href="/dashboard/billing" className="hover:text-emerald-400 transition">
              Billing
            </Link>
            <Link href="/dashboard/history" className="hover:text-emerald-400 transition">
              History
            </Link>
            <a href="/metrics" target="_blank" className="hover:text-emerald-400 transition">
              Metrics
            </a>
            <a href="https://github.com" target="_blank" rel="noreferrer" className="hover:text-emerald-400 transition flex items-center gap-1">
              <GithubIcon className="h-3.5 w-3.5" />
              <span>GitHub</span>
            </a>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] text-slate-400">All Systems Operational</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
