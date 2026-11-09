"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Layers,
  Sparkles,
  Play,
  Palette,
  Code2,
  Cpu,
  Database,
  Globe,
  Radio,
  Server,
  Workflow,
  CheckCircle2,
  Copy,
  Check,
  Download,
  Eye,
  Settings2,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface StudioNode {
  id: string;
  label: string;
  kind: "frontend" | "backend" | "database" | "queue" | "cache" | "gateway";
  tech: string;
  layer: number;
}

interface StudioConnection {
  source_id: string;
  target_id: string;
  label: string;
  protocol: string;
  animated: boolean;
  packet_color: string;
}

const DEFAULT_NODES: StudioNode[] = [
  { id: "client", label: "Next.js Web UI", kind: "frontend", tech: "React 19 & Tailwind", layer: 0 },
  { id: "gateway", label: "FastAPI Gateway", kind: "gateway", tech: "ASGI & SlowAPI", layer: 1 },
  { id: "worker", label: "Celery Workers", kind: "backend", tech: "Python 3.11 & Manim", layer: 2 },
  { id: "redis", label: "Redis Broker & Cache", kind: "queue", tech: "Redis 7.2", layer: 2 },
  { id: "db", label: "PostgreSQL Database", kind: "database", tech: "SQLAlchemy & Supabase", layer: 3 },
  { id: "s3", label: "Cloud Object Storage", kind: "database", tech: "AWS S3 / Cloudflare R2", layer: 3 },
];

const DEFAULT_CONNECTIONS: StudioConnection[] = [
  { source_id: "client", target_id: "gateway", label: "REST & SSE", protocol: "HTTP/2", animated: true, packet_color: "#38BDF8" },
  { source_id: "gateway", target_id: "redis", label: "Dispatch Tasks", protocol: "RESP", animated: true, packet_color: "#F43F5E" },
  { source_id: "redis", target_id: "worker", label: "Consume Pipeline", protocol: "AMQP/Celery", animated: true, packet_color: "#A855F7" },
  { source_id: "worker", target_id: "db", label: "Audit Ledger", protocol: "AsyncPG", animated: false, packet_color: "#10B981" },
  { source_id: "worker", target_id: "s3", label: "Upload MP4 Artifacts", protocol: "S3 API", animated: true, packet_color: "#F59E0B" },
];

const STUDIO_THEMES = [
  { id: "midnight", name: "Midnight Obsidian", bg: "#0B0F19", accent: "#38BDF8", border: "#1E293B" },
  { id: "dark", name: "Onyx Dark", bg: "#121214", accent: "#6366F1", border: "#27272A" },
  { id: "cyberpunk", name: "Cyberpunk Neon", bg: "#0A0A14", accent: "#EC4899", border: "#8B5CF6" },
  { id: "nord", name: "Nordic Frost", bg: "#2E3440", accent: "#88C0D0", border: "#4C566A" },
  { id: "light", name: "Clean Minimalist", bg: "#F8FAFC", accent: "#2563EB", border: "#E2E8F0" },
];

export default function StudioPage() {
  const [activeTheme, setActiveTheme] = useState("midnight");
  const [selectedNode, setSelectedNode] = useState<StudioNode>(DEFAULT_NODES[0]);
  const [nodes, setNodes] = useState<StudioNode[]>(DEFAULT_NODES);
  const [connections] = useState<StudioConnection[]>(DEFAULT_CONNECTIONS);
  const [copiedCode, setCopiedCode] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  const selectedThemeObj = STUDIO_THEMES.find((t) => t.id === activeTheme) || STUDIO_THEMES[0];

  const pythonScript = `from manim import *
from manim_engine.models import ArchitectureDiagramData, NodeModel, ConnectionModel

class GeneratedArchitectureScene(Scene):
    def construct(self):
        # Background Canvas (${selectedThemeObj.name})
        self.camera.background_color = "${selectedThemeObj.bg}"
        
        title = Text("System Architecture Topology", font_size=28, color=WHITE).to_edge(UP, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.8)
        
        # Render ${nodes.length} Components & ${connections.length} Vector Connections
        # Theme: ${selectedThemeObj.name} (Accent: ${selectedThemeObj.accent})
        # Auto-synthesized via CodeVideo AI Engine
`;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(pythonScript);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const getNodeIcon = (kind: StudioNode["kind"]) => {
    switch (kind) {
      case "frontend":
        return Globe;
      case "gateway":
        return Radio;
      case "backend":
        return Cpu;
      case "queue":
        return Workflow;
      case "database":
        return Database;
      default:
        return Server;
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-border/70">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 mb-2">
            <Layers className="h-3.5 w-3.5 text-primary" />
            <span>Manim Community Scene Studio</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            Architecture Studio
          </h1>
          <p className="mt-1 text-sm text-muted-foreground max-w-2xl">
            Inspect, tune, and test the vector topology graphs rendered into your animated tutorial videos.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setIsSimulating(true);
              setTimeout(() => setIsSimulating(false), 1600);
            }}
            disabled={isSimulating}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-primary text-primary-foreground hover:bg-primary/90 shadow-md shadow-primary/20 transition-all disabled:opacity-60"
          >
            {isSimulating ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Compiling Topology...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Simulate Flow Scene</span>
              </>
            )}
          </button>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold border border-border bg-card hover:bg-secondary transition-colors"
          >
            <span>Back to Generator</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Grid Layout: Visual Canvas & Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Interactive Graph Canvas Preview */}
        <div className="lg:col-span-2 space-y-6">
          <div
            className="rounded-2xl border p-6 min-h-[440px] flex flex-col justify-between relative overflow-hidden transition-all shadow-xl"
            style={{
              backgroundColor: selectedThemeObj.bg,
              borderColor: selectedThemeObj.border,
            }}
          >
            {/* Canvas Header */}
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-mono text-xs text-white/80">
                  Canvas: 1920x1080 (16:9 HD Manim Output)
                </span>
              </div>
              <span className="text-[11px] font-mono text-white/60">
                Theme: {selectedThemeObj.name}
              </span>
            </div>

            {/* Simulated Nodes Layout */}
            <div className="grid grid-cols-3 gap-4 my-8">
              {nodes.map((node) => {
                const Icon = getNodeIcon(node.kind);
                const isSelected = selectedNode.id === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={cn(
                      "p-3.5 rounded-xl border cursor-pointer select-none transition-all relative group backdrop-blur-md",
                      isSelected
                        ? "border-primary bg-primary/20 ring-2 ring-primary/60 scale-[1.02]"
                        : "border-white/10 bg-white/5 hover:bg-white/10"
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <div
                        className="h-7 w-7 rounded-lg flex items-center justify-center text-white"
                        style={{ backgroundColor: selectedThemeObj.accent }}
                      >
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className="text-xs font-bold text-white truncate">
                        {node.label}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-white/60 block truncate">
                      {node.tech}
                    </span>
                    <span className="text-[9px] uppercase tracking-wider text-emerald-400 font-semibold mt-1 block">
                      Layer {node.layer} • {node.kind}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Canvas Footer */}
            <div className="pt-4 border-t border-white/10 flex items-center justify-between text-xs text-white/60">
              <span>{nodes.length} Components • {connections.length} Vector Interconnections</span>
              <span className="text-[10px] font-mono">Status: Ready for Manim compilation</span>
            </div>
          </div>

          {/* Python Scene Code Generator View */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code2 className="h-4 w-4 text-primary" />
                <h3 className="font-bold text-sm text-foreground">Generated Manim Python Script</h3>
              </div>
              <button
                onClick={handleCopyCode}
                className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground bg-secondary px-3 py-1.5 rounded-lg border border-border transition-colors"
              >
                {copiedCode ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Copy Script</span>
                  </>
                )}
              </button>
            </div>

            <pre className="p-4 rounded-xl bg-secondary/60 text-foreground font-mono text-xs overflow-x-auto border border-border/80">
              <code>{pythonScript}</code>
            </pre>
          </div>
        </div>

        {/* Right Col: Theme Customizer & Node Inspector */}
        <div className="space-y-6">
          {/* Theme Picker */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-2">
              <Palette className="h-4 w-4 text-primary" />
              <h3 className="font-bold text-sm text-foreground">Aesthetic Themes</h3>
            </div>

            <div className="space-y-2.5">
              {STUDIO_THEMES.map((theme) => {
                const isSelected = activeTheme === theme.id;
                return (
                  <div
                    key={theme.id}
                    onClick={() => setActiveTheme(theme.id)}
                    className={cn(
                      "flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all",
                      isSelected
                        ? "border-primary bg-primary/10 ring-1 ring-primary/40 font-semibold"
                        : "border-border hover:bg-secondary/40"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="h-5 w-5 rounded-full border shadow-sm"
                        style={{ backgroundColor: theme.accent, borderColor: theme.border }}
                      />
                      <span className="text-xs text-foreground">{theme.name}</span>
                    </div>
                    {isSelected && <CheckCircle2 className="h-4 w-4 text-primary" />}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Node Inspector */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-4">
            <div className="flex items-center gap-2">
              <Settings2 className="h-4 w-4 text-primary" />
              <h3 className="font-bold text-sm text-foreground">Node Inspector</h3>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[11px] font-semibold text-muted-foreground uppercase">
                  Label
                </label>
                <input
                  type="text"
                  value={selectedNode.label}
                  onChange={(e) => {
                    const newLabel = e.target.value;
                    setNodes((prev) =>
                      prev.map((n) => (n.id === selectedNode.id ? { ...n, label: newLabel } : n))
                    );
                    setSelectedNode((prev) => ({ ...prev, label: newLabel }));
                  }}
                  className="w-full mt-1 px-3 py-2 rounded-lg border border-input bg-background font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-muted-foreground uppercase">
                  Technology Stack
                </label>
                <input
                  type="text"
                  value={selectedNode.tech}
                  onChange={(e) => {
                    const newTech = e.target.value;
                    setNodes((prev) =>
                      prev.map((n) => (n.id === selectedNode.id ? { ...n, tech: newTech } : n))
                    );
                    setSelectedNode((prev) => ({ ...prev, tech: newTech }));
                  }}
                  className="w-full mt-1 px-3 py-2 rounded-lg border border-input bg-background font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <span className="text-muted-foreground block text-[11px]">Layer</span>
                  <span className="font-bold text-foreground">Level {selectedNode.layer}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Kind</span>
                  <span className="font-bold text-foreground uppercase">{selectedNode.kind}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

