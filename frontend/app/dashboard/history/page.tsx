"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  Film,
  Download,
  Share2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  Plus,
  Play,
  SlidersHorizontal,
  X,
  Monitor,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { GithubIcon } from "@/components/icons";

// -----------------------------------------------------------------------------
// Data Model
// -----------------------------------------------------------------------------

export interface VideoTutorialItem {
  id: string;
  job_id: string;
  repo_name: string;
  repo_url: string;
  status: "SUCCESS" | "FAILURE" | "PROCESSING";
  duration_seconds: number;
  resolution: string;
  theme: string;
  created_at: string;
  download_url: string;
  cloud_url?: string;
  subtitles_burned: boolean;
}

// -----------------------------------------------------------------------------
// Sample Initial Data
// -----------------------------------------------------------------------------

const INITIAL_TUTORIALS: VideoTutorialItem[] = [
  {
    id: "tut_helper_ai",
    job_id: "job_local_14f6a23b43",
    repo_name: "rajkotpodman/helper-ai",
    repo_url: "https://github.com/rajkotpodman/helper-ai",
    status: "SUCCESS",
    duration_seconds: 43,
    resolution: "1080p",
    theme: "midnight",
    created_at: new Date().toISOString(),
    download_url: "/api/v1/jobs/job_local_14f6a23b43/download",
    cloud_url: "https://codevideo-tutorials.s3.amazonaws.com/tutorials/job_local_14f6a23b43/tutorial_job_local_14f6a23b43.mp4",
    subtitles_burned: true,
  },
  {
    id: "tut_01",
    job_id: "6a3e218f-9a74-4b5d-8d4e-128a123f001a",
    repo_name: "yamadashy/repomix",
    repo_url: "https://github.com/yamadashy/repomix",
    status: "SUCCESS",
    duration_seconds: 45,
    resolution: "1080p",
    theme: "midnight",
    created_at: new Date(Date.now() - 1000 * 60 * 140).toISOString(),
    download_url: "/api/v1/jobs/6a3e218f-9a74-4b5d-8d4e-128a123f001a/download",
    cloud_url: "https://codevideo-tutorials.s3.amazonaws.com/tutorials/6a3e218f/tutorial.mp4",
    subtitles_burned: true,
  },
  {
    id: "tut_02",
    job_id: "8f12c90a-1123-4567-89ab-cdef01234567",
    repo_name: "tiangolo/fastapi",
    repo_url: "https://github.com/tiangolo/fastapi",
    status: "SUCCESS",
    duration_seconds: 72,
    resolution: "1080p",
    theme: "dark",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 26).toISOString(),
    download_url: "/api/v1/jobs/8f12c90a-1123-4567-89ab-cdef01234567/download",
    cloud_url: "https://codevideo-tutorials.s3.amazonaws.com/tutorials/8f12c90a/tutorial.mp4",
    subtitles_burned: true,
  },
  {
    id: "tut_03",
    job_id: "3b4c5d6e-7f8a-9b0c-1d2e-3f4a5b6c7d8e",
    repo_name: "ManimCommunity/manim",
    repo_url: "https://github.com/ManimCommunity/manim",
    status: "SUCCESS",
    duration_seconds: 58,
    resolution: "720p",
    theme: "cyberpunk",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 74).toISOString(),
    download_url: "/api/v1/jobs/3b4c5d6e-7f8a-9b0c-1d2e-3f4a5b6c7d8e/download",
    subtitles_burned: true,
  },
  {
    id: "tut_04",
    job_id: "44aa33bb-88cc-99dd-11ee-55ff22aa77bb",
    repo_name: "vercel/next.js",
    repo_url: "https://github.com/vercel/next.js",
    status: "PROCESSING",
    duration_seconds: 0,
    resolution: "1080p",
    theme: "nord",
    created_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
    download_url: "#",
    subtitles_burned: true,
  },
  {
    id: "tut_05",
    job_id: "99aa88bb-77cc-66dd-55ee-44ff33aa22bb",
    repo_name: "octocat/Hello-World",
    repo_url: "https://github.com/octocat/Hello-World",
    status: "SUCCESS",
    duration_seconds: 28,
    resolution: "1080p",
    theme: "midnight",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 140).toISOString(),
    download_url: "/api/v1/jobs/99aa88bb-77cc-66dd-55ee-44ff33aa22bb/download",
    subtitles_burned: true,
  },
  {
    id: "tut_06",
    job_id: "1234abcd-5678-ef90-1234-56789abcdef0",
    repo_name: "facebook/react",
    repo_url: "https://github.com/facebook/react",
    status: "FAILURE",
    duration_seconds: 0,
    resolution: "1080p",
    theme: "light",
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 200).toISOString(),
    download_url: "#",
    subtitles_burned: false,
  },
];

// -----------------------------------------------------------------------------
// Format Helpers
// -----------------------------------------------------------------------------

function formatDuration(sec: number) {
  if (!sec || sec <= 0) return "--";
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s < 10 ? "0" : ""}${s}`;
}

function formatDate(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

// -----------------------------------------------------------------------------
// Main Component
// -----------------------------------------------------------------------------

export default function HistoryPage() {
  const [data, setData] = useState<VideoTutorialItem[]>(INITIAL_TUTORIALS);
  const [sorting, setSorting] = useState<SortingState>([
    { id: "created_at", desc: true },
  ]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Copy Job ID or Link
  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // ---------------------------------------------------------------------------
  // Shadcn UI Column Definitions
  // ---------------------------------------------------------------------------
  const columns = useMemo<ColumnDef<VideoTutorialItem>[]>(
    () => [
      {
        accessorKey: "repo_name",
        header: ({ column }) => {
          return (
            <button
              onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              className="flex items-center gap-1.5 font-semibold text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>Repository Name</span>
              {column.getIsSorted() === "asc" ? (
                <ArrowUp className="h-3 w-3 text-primary" />
              ) : column.getIsSorted() === "desc" ? (
                <ArrowDown className="h-3 w-3 text-primary" />
              ) : (
                <ArrowUpDown className="h-3 w-3 opacity-60" />
              )}
            </button>
          );
        },
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="flex items-start gap-3 py-1">
              <div className="h-9 w-9 rounded-xl bg-secondary flex items-center justify-center shrink-0 border border-border mt-0.5">
                <GithubIcon className="h-4 w-4 text-foreground" />
              </div>
              <div>
                <a
                  href={item.repo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-bold text-sm text-foreground hover:text-primary transition-colors flex items-center gap-1.5 group"
                >
                  <span>{item.repo_name}</span>
                  <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                </a>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono text-[10px] text-muted-foreground bg-secondary/80 px-2 py-0.5 rounded border border-border">
                    {item.job_id.slice(0, 8)}...
                  </span>
                  <button
                    onClick={() => handleCopy(item.job_id, item.id)}
                    className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                    title="Copy Job ID"
                  >
                    {copiedId === item.id ? (
                      <Check className="h-3 w-3 text-emerald-400" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </button>
                  <span className="text-[10px] text-muted-foreground capitalize">
                    • Theme: {item.theme}
                  </span>
                </div>
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
          const status = row.getValue("status") as string;
          return (
            <div>
              {status === "SUCCESS" && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Success</span>
                </span>
              )}
              {status === "PROCESSING" && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/30 animate-pulse">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Processing</span>
                </span>
              )}
              {status === "FAILURE" && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                  <AlertCircle className="h-3.5 w-3.5" />
                  <span>Failure</span>
                </span>
              )}
            </div>
          );
        },
        filterFn: (row, id, value) => {
          if (!value || value === "ALL") return true;
          return row.getValue(id) === value;
        },
      },
      {
        accessorKey: "duration_seconds",
        header: ({ column }) => {
          return (
            <button
              onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              className="flex items-center gap-1.5 font-semibold text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>Duration & Resolution</span>
              {column.getIsSorted() === "asc" ? (
                <ArrowUp className="h-3 w-3 text-primary" />
              ) : column.getIsSorted() === "desc" ? (
                <ArrowDown className="h-3 w-3 text-primary" />
              ) : (
                <ArrowUpDown className="h-3 w-3 opacity-60" />
              )}
            </button>
          );
        },
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 font-mono text-xs text-foreground font-semibold">
                <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                <span>{formatDuration(item.duration_seconds)}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-secondary text-secondary-foreground border border-border">
                  {item.resolution}
                </span>
                {item.subtitles_burned && (
                  <span className="text-[10px] text-muted-foreground">
                    CC Subtitles
                  </span>
                )}
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "created_at",
        header: ({ column }) => {
          return (
            <button
              onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
              className="flex items-center gap-1.5 font-semibold text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>Created Date</span>
              {column.getIsSorted() === "asc" ? (
                <ArrowUp className="h-3 w-3 text-primary" />
              ) : column.getIsSorted() === "desc" ? (
                <ArrowDown className="h-3 w-3 text-primary" />
              ) : (
                <ArrowUpDown className="h-3 w-3 opacity-60" />
              )}
            </button>
          );
        },
        cell: ({ row }) => {
          const iso = row.getValue("created_at") as string;
          return (
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {formatDate(iso)}
            </span>
          );
        },
      },
      {
        id: "actions",
        header: () => <span className="text-right block pr-4">Action</span>,
        cell: ({ row }) => {
          const item = row.original;
          if (item.status !== "SUCCESS") {
            return (
              <div className="text-right pr-4 text-xs text-muted-foreground font-mono">
                {item.status === "PROCESSING" ? "Rendering..." : "Unavailable"}
              </div>
            );
          }

          return (
            <div className="flex items-center justify-end gap-2 pr-4">
              <a
                href={item.download_url}
                download={`tutorial_${item.job_id}.mp4`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm transition-all"
                title="Download MP4 Tutorial Video"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download</span>
              </a>

              <button
                onClick={() => handleCopy(item.cloud_url || item.download_url, `share_${item.id}`)}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary border border-border transition-colors"
                title="Copy Video Stream Link"
              >
                {copiedId === `share_${item.id}` ? (
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <Share2 className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
          );
        },
      },
    ],
    [copiedId]
  );

  // ---------------------------------------------------------------------------
  // TanStack Table Instance
  // ---------------------------------------------------------------------------
  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    initialState: {
      pagination: {
        pageSize: 5,
      },
    },
  });

  const searchValue =
    (table.getColumn("repo_name")?.getFilterValue() as string) ?? "";

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* =================================================================== */}
      {/* Header Bar                                                          */}
      {/* =================================================================== */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 mb-3">
            <Film className="h-3.5 w-3.5 text-primary" />
            <span>Tutorial Archives</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            Video Generation History
          </h1>
          <p className="mt-1.5 text-sm sm:text-base text-muted-foreground max-w-2xl">
            Browse and download all your previously generated codebase architecture tutorials, inspect durations, and copy cloud stream links.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-primary text-primary-foreground hover:bg-primary/90 shadow-md shadow-primary/25 transition-all"
          >
            <Plus className="h-4 w-4" />
            <span>Generate New Tutorial</span>
          </Link>
        </div>
      </div>

      {/* =================================================================== */}
      {/* Filter and Search Controls (Shadcn UI Toolbar)                      */}
      {/* =================================================================== */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Search by Repository Name */}
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search repositories (e.g. repomix, fastapi)..."
            value={searchValue}
            onChange={(e) => table.getColumn("repo_name")?.setFilterValue(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-input bg-card text-xs sm:text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
          />
          <Search className="h-4 w-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
        </div>

        {/* Status Dropdown Filter */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-xs text-muted-foreground">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => {
              const val = e.target.value;
              setStatusFilter(val);
              table.getColumn("status")?.setFilterValue(val === "ALL" ? "" : val);
            }}
            className="px-3 py-1.5 rounded-lg border border-input bg-card text-xs text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="ALL">All Statuses</option>
            <option value="SUCCESS">Success Only</option>
            <option value="PROCESSING">Processing</option>
            <option value="FAILURE">Failed</option>
          </select>
        </div>
      </div>

      {/* =================================================================== */}
      {/* Responsive Shadcn UI Data Table (TanStack Table)                    */}
      {/* =================================================================== */}
      <div className="rounded-2xl border border-border bg-card/90 backdrop-blur-sm overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-secondary/40 text-muted-foreground font-semibold uppercase tracking-wider border-b border-border/80">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th key={header.id} className="py-3.5 px-6 font-semibold">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-border/60">
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="hover:bg-secondary/20 transition-colors"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="py-4 px-6">
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="h-36 text-center text-muted-foreground"
                  >
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <Film className="h-8 w-8 opacity-40" />
                      <p className="text-sm font-semibold">No video tutorials found</p>
                      <p className="text-xs opacity-75">
                        Try adjusting your search filter or generate a new animated video tutorial.
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* =================================================================== */}
        {/* Pagination & Status Bar                                             */}
        {/* =================================================================== */}
        <div className="p-4 border-t border-border/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-secondary/10 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <span>Showing</span>
            <span className="font-semibold text-foreground">
              {table.getState().pagination.pageIndex *
                table.getState().pagination.pageSize +
                1}
            </span>
            <span>to</span>
            <span className="font-semibold text-foreground">
              {Math.min(
                (table.getState().pagination.pageIndex + 1) *
                  table.getState().pagination.pageSize,
                table.getFilteredRowModel().rows.length
              )}
            </span>
            <span>of</span>
            <span className="font-semibold text-foreground">
              {table.getFilteredRowModel().rows.length}
            </span>
            <span>tutorials</span>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border bg-card text-foreground hover:bg-secondary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              <span>Previous</span>
            </button>

            <span className="px-2 font-mono text-foreground font-semibold">
              Page {table.getState().pagination.pageIndex + 1} of{" "}
              {table.getPageCount() || 1}
            </span>

            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border bg-card text-foreground hover:bg-secondary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span>Next</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

