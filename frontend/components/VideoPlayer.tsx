"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Film,
  Download,
  Share2,
  Check,
  Play,
  Pause,
  RotateCcw,
  Maximize2,
  Volume2,
  Sparkles,
  ExternalLink,
  Layers,
  Subtitles,
  Info,
  AlertTriangle,
  Monitor,
} from "lucide-react";
import { cn } from "@/lib/utils";

// -----------------------------------------------------------------------------
// Component Props
// -----------------------------------------------------------------------------

export interface VideoPlayerProps {
  /** Celery / FastAPI task ID */
  jobId: string;
  /** Explicit download/stream URL (defaults to /api/v1/jobs/{jobId}/download) */
  downloadUrl?: string;
  /** GitHub repository or project name */
  repoUrl?: string;
  /** Target resolution (e.g. 1080p, 720p, 480p) */
  resolution?: string;
  /** Manim color theme applied */
  theme?: string;
  /** Whether subtitles are burned into the video stream */
  burnSubtitles?: boolean;
  /** Optional video duration in seconds */
  duration?: number;
  /** Optional callback to create another video / restart */
  onReset?: () => void;
}

export function VideoPlayer({
  jobId,
  downloadUrl,
  repoUrl,
  resolution = "1080p",
  theme = "midnight",
  burnSubtitles = true,
  duration,
  onReset,
}: VideoPlayerProps) {
  const streamUrl = downloadUrl || `/api/v1/jobs/${jobId}/download`;

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [videoDuration, setVideoDuration] = useState<number>(duration || 0);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [isCopied, setIsCopied] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isBuffering, setIsBuffering] = useState(false);
  const [videoDimensions, setVideoDimensions] = useState<{ width: number; height: number } | null>(null);

  // Sync duration if provided as prop
  useEffect(() => {
    if (duration && duration > 0) {
      setVideoDuration(duration);
    }
  }, [duration]);

  // ---------------------------------------------------------------------------
  // Video Event Handlers
  // ---------------------------------------------------------------------------
  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setVideoDuration(videoRef.current.duration);
      setVideoDimensions({
        width: videoRef.current.videoWidth,
        height: videoRef.current.videoHeight,
      });
      setLoadError(null);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handlePlayState = () => {
    if (videoRef.current) {
      setIsPlaying(!videoRef.current.paused);
    }
  };

  const handleVideoError = () => {
    setLoadError(
      "The video stream could not be loaded. Please ensure the backend server is running and the video file exists."
    );
    setIsBuffering(false);
  };

  const handleWaiting = () => {
    setIsBuffering(true);
  };

  const handlePlaying = () => {
    setIsBuffering(false);
    setIsPlaying(true);
  };

  // Fullscreen toggle
  const handleToggleFullscreen = async () => {
    if (!containerRef.current) return;
    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (err) {
      console.warn("Fullscreen request failed:", err);
    }
  };

  // ---------------------------------------------------------------------------
  // Share Handler (Web Share API with Clipboard Fallback)
  // ---------------------------------------------------------------------------
  const handleShare = async () => {
    const fullShareUrl =
      typeof window !== "undefined"
        ? `${window.location.origin}${streamUrl}`
        : streamUrl;

    const shareData = {
      title: "Animated Codebase Architecture Tutorial",
      text: `Check out this animated architecture walkthrough generated for ${repoUrl || "GitHub repository"}!`,
      url: fullShareUrl,
    };

    if (typeof navigator !== "undefined" && navigator.share && navigator.canShare && navigator.canShare(shareData)) {
      try {
        await navigator.share(shareData);
        return;
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.warn("Web Share API error, falling back to clipboard:", err);
        } else {
          return;
        }
      }
    }

    // Fallback: Copy link to clipboard
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(fullShareUrl);
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2500);
      } catch (err) {
        console.error("Clipboard copy failed:", err);
      }
    }
  };

  // Format seconds to mm:ss
  const formatTime = (seconds: number) => {
    if (isNaN(seconds) || seconds < 0) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div
      ref={containerRef}
      className="w-full rounded-2xl border border-border bg-card/95 backdrop-blur-md p-6 sm:p-8 shadow-2xl space-y-6 animate-in fade-in zoom-in-95 duration-400"
    >
      {/* =================================================================== */}
      {/* Header: Title, Badges, and Action Bar                               */}
      {/* =================================================================== */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/80">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-2">
            <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
            <span>Render Complete • FastStart MP4</span>
          </div>

          <h3 className="text-xl font-extrabold tracking-tight text-foreground flex items-center gap-2.5">
            <Film className="h-5 w-5 text-blue-400" />
            <span>Animated Video Tutorial</span>
          </h3>

          {repoUrl && (
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1.5 font-mono">
              <span>Source:</span>
              <span className="text-foreground font-semibold">{repoUrl}</span>
            </p>
          )}
        </div>

        {/* Primary Action Buttons */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Prominent Download Button */}
          <a
            href={streamUrl}
            download={`tutorial_${jobId}.mp4`}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/25 hover:shadow-primary/40 active:scale-[0.98] transition-all"
            title="Download full HD MP4 video file"
          >
            <Download className="h-4 w-4" />
            <span>Download MP4 Tutorial</span>
          </a>

          {/* Share Link / Web Share Button */}
          <button
            onClick={handleShare}
            className={cn(
              "inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-xs sm:text-sm border transition-all active:scale-[0.98]",
              isCopied
                ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-400"
                : "bg-secondary text-secondary-foreground border-border hover:bg-secondary/70 hover:text-foreground"
            )}
            title="Share video link or copy URL"
          >
            {isCopied ? (
              <>
                <Check className="h-4 w-4 text-emerald-400" />
                <span>Link Copied!</span>
              </>
            ) : (
              <>
                <Share2 className="h-4 w-4" />
                <span>Share</span>
              </>
            )}
          </button>

          {/* Create Another Tutorial */}
          {onReset && (
            <button
              onClick={onReset}
              className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-secondary/80 text-muted-foreground hover:text-foreground hover:bg-secondary border border-border transition-colors"
              title="Create another tutorial video"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">New Video</span>
            </button>
          )}
        </div>
      </div>

      {/* =================================================================== */}
      {/* HTML5 Video Player Container                                        */}
      {/* =================================================================== */}
      <div className="relative aspect-video rounded-xl overflow-hidden border border-border/90 bg-neutral-950 shadow-inner group">
        {/* Native HTML5 Video Element with FastStart Optimization */}
        <video
          ref={videoRef}
          controls
          playsInline
          preload="metadata"
          onLoadedMetadata={handleLoadedMetadata}
          onTimeUpdate={handleTimeUpdate}
          onPlay={handlePlayState}
          onPause={handlePlayState}
          onWaiting={handleWaiting}
          onPlaying={handlePlaying}
          onError={handleVideoError}
          className="w-full h-full object-contain bg-black"
        >
          <source src={streamUrl} type="video/mp4" />
          Your browser does not support the video tag. Please use the Download MP4 button to view the video.
        </video>

        {/* Buffering Indicator */}
        {isBuffering && (
          <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center pointer-events-none">
            <div className="flex items-center gap-2 bg-black/80 text-white px-4 py-2 rounded-xl border border-white/10 text-xs font-medium">
              <span className="h-3.5 w-3.5 rounded-full border-2 border-white/20 border-t-white animate-spin" />
              <span>Buffering media stream...</span>
            </div>
          </div>
        )}

        {/* Video Load Error Banner */}
        {loadError && (
          <div className="absolute inset-0 bg-neutral-950/90 flex flex-col items-center justify-center p-6 text-center space-y-3">
            <AlertTriangle className="h-10 w-10 text-rose-500" />
            <div className="max-w-md">
              <h4 className="text-sm font-bold text-white">Media Playback Notice</h4>
              <p className="text-xs text-neutral-400 mt-1">{loadError}</p>
            </div>
            <a
              href={streamUrl}
              download
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download Directly</span>
            </a>
          </div>
        )}
      </div>

      {/* =================================================================== */}
      {/* Video Metadata & Technical Specs Bar                                */}
      {/* =================================================================== */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
        {/* Resolution */}
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-secondary/40 border border-border text-xs">
          <Monitor className="h-4 w-4 text-primary shrink-0" />
          <div>
            <span className="text-[10px] text-muted-foreground uppercase font-bold block">
              Resolution
            </span>
            <span className="font-semibold text-foreground">
              {videoDimensions
                ? `${videoDimensions.width}x${videoDimensions.height}`
                : `${resolution} HD`}
            </span>
          </div>
        </div>

        {/* Duration */}
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-secondary/40 border border-border text-xs">
          <Film className="h-4 w-4 text-emerald-400 shrink-0" />
          <div>
            <span className="text-[10px] text-muted-foreground uppercase font-bold block">
              Duration
            </span>
            <span className="font-semibold text-foreground">
              {videoDuration > 0 ? formatTime(videoDuration) : "Calculating..."}
            </span>
          </div>
        </div>

        {/* Theme Aesthetic */}
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-secondary/40 border border-border text-xs">
          <Layers className="h-4 w-4 text-cyan-400 shrink-0" />
          <div>
            <span className="text-[10px] text-muted-foreground uppercase font-bold block">
              Theme
            </span>
            <span className="font-semibold text-foreground capitalize">
              {theme}
            </span>
          </div>
        </div>

        {/* Subtitles Status */}
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-secondary/40 border border-border text-xs">
          <Subtitles className="h-4 w-4 text-amber-400 shrink-0" />
          <div>
            <span className="text-[10px] text-muted-foreground uppercase font-bold block">
              Subtitles
            </span>
            <span className="font-semibold text-foreground">
              {burnSubtitles ? "Burned-in ASS" : "None"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default VideoPlayer;

