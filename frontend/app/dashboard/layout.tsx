"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Video,
  Sparkles,
  Layers,
  Film,
  Settings,
  Zap,
  Coins,
  Bell,
  ChevronRight,
  Menu,
  X,
  Code2,
  Cpu,
  BookOpen,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: "Generate Tutorial", href: "/dashboard", icon: Sparkles, badge: "AI" },
  { name: "Video History", href: "/dashboard/history", icon: Film, badge: "8" },
  { name: "Architecture Studio", href: "/dashboard/studio", icon: Layers },
  { name: "API & Webhooks", href: "/dashboard/api", icon: Code2 },
  { name: "Settings & Billing", href: "/dashboard/billing", icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [credits, setCredits] = useState(120);

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      {/* =================================================================== */}
      {/* Desktop Sidebar                                                     */}
      {/* =================================================================== */}
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card/60 backdrop-blur-xl shrink-0">
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-border/80 gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Video className="h-5 w-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              CodeVideo AI
            </span>
            <span className="block text-[10px] text-muted-foreground uppercase font-mono tracking-wider">
              Manim + Repomix
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 py-6 px-3 space-y-1.5 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
            Platform
          </div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all group",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-md shadow-primary/25 font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/70"
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={cn(
                      "h-4 w-4 transition-transform group-hover:scale-110",
                      isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      "text-[10px] font-bold px-1.5 py-0.5 rounded-md tracking-wide",
                      isActive
                        ? "bg-white/20 text-white"
                        : "bg-secondary text-muted-foreground"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        {/* Worker Engine Status Box */}
        <div className="p-4 border-t border-border/80">
          <div className="p-3.5 rounded-xl bg-secondary/50 border border-border/60 text-xs space-y-2">
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="flex items-center gap-1.5 font-medium text-foreground">
                <Cpu className="h-3.5 w-3.5 text-emerald-400" />
                Render Engine
              </span>
              <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-semibold">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Ready
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Manim Community v0.22 with FFmpeg static encoders initialized.
            </p>
          </div>
        </div>
      </aside>

      {/* =================================================================== */}
      {/* Mobile Drawer Navigation                                            */}
      {/* =================================================================== */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative w-72 bg-card border-r border-border p-6 flex flex-col h-full z-10">
            <div className="flex items-center justify-between pb-6 border-b border-border">
              <div className="flex items-center gap-2">
                <Video className="h-5 w-5 text-primary" />
                <span className="font-bold">CodeVideo AI</span>
              </div>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="py-4 space-y-2 flex-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-secondary"
                >
                  <item.icon className="h-4 w-4" />
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* Main Content Area                                                   */}
      {/* =================================================================== */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 border-b border-border bg-card/40 backdrop-blur-md px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2 -ml-2 rounded-lg text-muted-foreground hover:text-foreground md:hidden"
              aria-label="Toggle Navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground">
              <span>Studio</span>
              <ChevronRight className="h-3.5 w-3.5" />
              <span className="text-foreground font-medium">Video Generator</span>
            </div>
          </div>

          {/* User & Credits Header Bar */}
          <div className="flex items-center gap-3 sm:gap-5">
            {/* User Credit Balance Widget */}
            <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-secondary/80 border border-border shadow-sm">
              <div className="h-6 w-6 rounded-full bg-gradient-to-tr from-amber-500 to-yellow-300 flex items-center justify-center text-black shadow-sm">
                <Coins className="h-3.5 w-3.5" />
              </div>
              <div className="flex items-baseline gap-1">
                <span className="font-bold text-sm text-foreground">{credits}</span>
                <span className="text-[11px] text-muted-foreground font-medium hidden sm:inline">
                  Credits
                </span>
              </div>
              <Link
                href="/dashboard/billing"
                className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-primary/20 text-primary hover:bg-primary/30 transition-colors ml-1"
                title="Top-up credits"
              >
                + Top-up
              </Link>
            </div>

            {/* Notifications */}
            <button className="relative p-2 rounded-full text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-primary" />
            </button>

            {/* User Avatar */}
            <div className="flex items-center gap-3 pl-2 border-l border-border">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-purple-600 to-blue-500 flex items-center justify-center font-bold text-xs text-white shadow-sm ring-2 ring-primary/20">
                AG
              </div>
              <div className="hidden lg:block text-left">
                <div className="text-xs font-semibold leading-tight">Engineer</div>
                <div className="text-[10px] text-muted-foreground">Pro Tier</div>
              </div>
            </div>
          </div>
        </header>

        {/* Responsive Body Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
