"""Codebase Ingestion Service.

This module provides backend ingestion for the Codebase-to-Animated Video Tutorial Engine.
It clones public GitHub repositories locally via GitPython, executes repomix parsing
(or a high-performance native fallback) to generate clean, compressed markdown/text
representations of the codebase structure, and aggressively filters out heavy build
directories, vendor packages, binaries, and lockfiles.
"""

from __future__ import annotations

import ast
import asyncio
import dataclasses
import logging
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

logger = logging.getLogger("ingestion_service")

# Try importing GitPython with a clean diagnostic if missing
try:
    import git  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    git = None  # type: ignore[assignment]


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class IngestionError(Exception):
    """Base exception for all ingestion service operations."""

    pass


class InvalidRepositoryUrlError(IngestionError):
    """Raised when the repository URL is invalid, unsafe, or malformed."""

    pass


class GitCloneError(IngestionError):
    """Raised when repository cloning or checkout fails."""

    pass


class RepomixExecutionError(IngestionError):
    """Raised when repomix CLI execution encounters an error."""

    pass


# -----------------------------------------------------------------------------
# Configuration & Data Models
# -----------------------------------------------------------------------------

DEFAULT_BUILD_IGNORE_PATTERNS: Tuple[str, ...] = (
    # Version control
    ".git/**",
    ".github/**",
    ".gitlab/**",
    ".svn/**",
    ".hg/**",
    # JavaScript / TypeScript / Node
    "node_modules/**",
    "bower_components/**",
    "jspm_packages/**",
    ".next/**",
    ".nuxt/**",
    ".turbo/**",
    ".output/**",
    ".svelte-kit/**",
    "storybook-static/**",
    # Build & Dist output folders
    "dist/**",
    "build/**",
    "out/**",
    "_build/**",
    "target/**",
    # Python caches & virtual environments
    "__pycache__/**",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".venv/**",
    "venv/**",
    "env/**",
    ".env/**",
    "ENV/**",
    "*.egg-info/**",
    ".eggs/**",
    ".tox/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".ruff_cache/**",
    "htmlcov/**",
    ".coverage",
    # JVM / Java / Kotlin / Gradle / Maven
    ".gradle/**",
    ".idea/**",
    "*.class",
    "*.jar",
    "*.war",
    # C# / .NET
    "bin/**",
    "obj/**",
    ".vs/**",
    # C / C++ / Rust / Go
    "CMakeFiles/**",
    "CMakeCache.txt",
    "vendor/**",
    "*.o",
    "*.obj",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.a",
    "*.lib",
    # Package lockfiles (large, minimal semantic value for tutorial video scripts)
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "Cargo.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    # Binaries, Archives & Media Assets
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.svg",
    "*.mp4",
    "*.mov",
    "*.avi",
    "*.webm",
    "*.mp3",
    "*.wav",
    "*.flac",
    "*.ogg",
    "*.pdf",
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.tgz",
    "*.rar",
    "*.7z",
    "*.exe",
    "*.bin",
    "*.wasm",
    "*.ttf",
    "*.woff",
    "*.woff2",
    "*.eot",
    # OS & Editor temp files
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    ".vscode/**",
)


@dataclasses.dataclass(frozen=True)
class IngestionOptions:
    """Configuration options for cloning and packaging repositories."""

    style: Literal["markdown", "plain", "xml", "json"] = "markdown"
    compress: bool = True
    remove_comments: bool = False
    remove_empty_lines: bool = True
    clone_depth: Optional[int] = 1
    branch: Optional[str] = None
    custom_ignore_patterns: Sequence[str] = ()
    include_patterns: Sequence[str] = ()
    max_file_size_kb: int = 500
    engine: Literal["auto", "repomix-cli", "python-native"] = "auto"
    keep_cloned_repo: bool = False
    output_filename: Optional[str] = None
    output_dir: Optional[Path | str] = None

    @property
    def effective_ignore_patterns(self) -> List[str]:
        """Combine default build ignores with caller-specified patterns."""
        combined = list(DEFAULT_BUILD_IGNORE_PATTERNS)
        for pattern in self.custom_ignore_patterns:
            if pattern not in combined:
                combined.append(pattern)
        return combined


@dataclasses.dataclass
class IngestionResult:
    """Result data container for an ingested repository."""

    repo_url: str
    repo_name: str
    branch: str
    commit_sha: str
    commit_message: str
    output_path: Path
    content: str
    total_files: int
    total_tokens: Optional[int]
    total_chars: int
    directory_tree: str
    top_files: List[Dict[str, Any]]
    engine_used: str
    duration_seconds: float
    cloned_path: Optional[Path] = None
    _cleanup_dir: Optional[Path] = None

    def cleanup(self) -> None:
        """Remove any temporary workspace directories created for this result."""
        if self._cleanup_dir and self._cleanup_dir.exists():
            robust_rmtree(self._cleanup_dir)

    def save_to(self, target_path: Path | str) -> Path:
        """Save the packed codebase representation to a chosen location."""
        destination = Path(target_path).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.content, encoding="utf-8")
        return destination

    def get_summary(self) -> str:
        """Return a human-readable summary of the ingestion output."""
        return (
            f"Repository: {self.repo_name} ({self.branch}@{self.commit_sha[:7]})\n"
            f"Engine: {self.engine_used} | Duration: {self.duration_seconds:.2f}s\n"
            f"Files Packed: {self.total_files} | Total Characters: {self.total_chars:,} "
            f"| Tokens (est.): {self.total_tokens or 'N/A'}\n"
            f"Output File: {self.output_path}"
        )


# -----------------------------------------------------------------------------
# Windows-Safe Filesystem & Cleanup Helpers
# -----------------------------------------------------------------------------


def _remove_readonly(func: Any, path: str, excinfo: Any) -> None:
    """Clear the read-only attribute and retry deletion on Windows."""
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        func(path)
    except Exception as err:
        logger.warning("Failed to force-delete %s: %s", path, err)


def robust_rmtree(path: Path | str) -> None:
    """Safely remove a directory tree, resolving read-only file locks."""
    target = Path(path)
    if not target.exists():
        return
    try:
        shutil.rmtree(target, onerror=_remove_readonly)
    except Exception as err:
        logger.error("Failed to delete directory tree %s: %s", target, err)


# -----------------------------------------------------------------------------
# GitHub URL Validation & Normalization
# -----------------------------------------------------------------------------


class RepoUrlParser:
    """Validates and extracts metadata from public GitHub repository URLs."""

    # Matches https://github.com/owner/repo(.git)(/tree/branch)? or git@github.com:owner/repo.git
    HTTPS_REGEX = re.compile(
        r"^https?://github\.com/(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+?)"
        r"(?:\.git)?(?:/tree/(?P<branch>[a-zA-Z0-9_\-\./]+))?/?$"
    )
    SSH_REGEX = re.compile(r"^git@github\.com:(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+?)(?:\.git)?$")
    SHORTHAND_REGEX = re.compile(r"^(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+)$")

    @classmethod
    def parse(cls, raw_url: str) -> Tuple[str, str, Optional[str]]:
        """Normalize URL and return (normalized_clone_url, repo_identifier, embedded_branch).

        Raises:
            InvalidRepositoryUrlError: If URL format is invalid or contains forbidden injection chars.
        """
        trimmed = raw_url.strip()
        if not trimmed:
            raise InvalidRepositoryUrlError("Repository URL cannot be empty.")

        # Guard against argument injection (e.g. flags passed as URLs)
        if trimmed.startswith("-") or any(char in trimmed for char in (";", "&", "|", "`", "$")):
            raise InvalidRepositoryUrlError(f"Potentially unsafe repository URL: '{raw_url}'")

        # Try HTTPS match
        https_match = cls.HTTPS_REGEX.match(trimmed)
        if https_match:
            owner = https_match.group("owner")
            repo = https_match.group("repo")
            branch = https_match.group("branch")
            norm_url = f"https://github.com/{owner}/{repo}.git"
            return norm_url, f"{owner}/{repo}", branch

        # Try SSH match
        ssh_match = cls.SSH_REGEX.match(trimmed)
        if ssh_match:
            owner = ssh_match.group("owner")
            repo = ssh_match.group("repo")
            norm_url = f"https://github.com/{owner}/{repo}.git"
            return norm_url, f"{owner}/{repo}", None

        # Try Shorthand 'owner/repo'
        shorthand_match = cls.SHORTHAND_REGEX.match(trimmed)
        if shorthand_match:
            owner = shorthand_match.group("owner")
            repo = shorthand_match.group("repo")
            norm_url = f"https://github.com/{owner}/{repo}.git"
            return norm_url, f"{owner}/{repo}", None

        raise InvalidRepositoryUrlError(
            f"Unsupported or invalid GitHub repository URL: '{raw_url}'. "
            "Expected format: 'https://github.com/owner/repo' or 'owner/repo'."
        )


# -----------------------------------------------------------------------------
# Git Clone Service
# -----------------------------------------------------------------------------


class GitCloneService:
    """Clones public Git repositories using GitPython with shallow depth support."""

    @staticmethod
    def clone(
        repo_url: str,
        target_dir: Path,
        depth: Optional[int] = 1,
        branch: Optional[str] = None,
    ) -> Tuple[Any, Dict[str, str]]:
        """Clone repository into target_dir.

        Returns:
            Tuple of (Repo instance, metadata dict).
        """
        if git is None:
            raise IngestionError("GitPython is not installed. Please install it with 'pip install gitpython'.")

        clone_kwargs: Dict[str, Any] = {}
        if depth and depth > 0:
            clone_kwargs["depth"] = depth
        if branch:
            clone_kwargs["branch"] = branch

        target_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cloning %s into %s (depth=%s, branch=%s)", repo_url, target_dir, depth, branch)

        try:
            repo = git.Repo.clone_from(
                url=repo_url,
                to_path=str(target_dir),
                **clone_kwargs,
            )
        except git.exc.GitCommandError as exc:
            msg = f"Failed to clone repository '{repo_url}': {exc.stderr or str(exc)}"
            logger.error(msg)
            raise GitCloneError(msg) from exc
        except Exception as exc:
            msg = f"Unexpected error during git clone of '{repo_url}': {exc}"
            logger.error(msg)
            raise GitCloneError(msg) from exc

        # Extract git commit and branch metadata
        try:
            head_commit = repo.head.commit
            commit_sha = head_commit.hexsha
            commit_msg = head_commit.message.strip()
            try:
                active_branch = repo.active_branch.name
            except TypeError:
                # Detached HEAD or shallow checkout
                active_branch = branch or "HEAD"
        except Exception as meta_exc:
            logger.warning("Could not extract full git commit metadata: %s", meta_exc)
            commit_sha = "unknown"
            commit_msg = "No commit message available"
            active_branch = branch or "main"

        metadata = {
            "branch": active_branch,
            "commit_sha": commit_sha,
            "commit_message": commit_msg,
        }
        return repo, metadata


# -----------------------------------------------------------------------------
# Repomix CLI Runner
# -----------------------------------------------------------------------------


class RepomixCliRunner:
    """Discovers and executes the repomix CLI binary or npx repomix."""

    @classmethod
    def find_executable(cls) -> Optional[List[str]]:
        """Detect repomix executable or npx invocation command."""
        # 1. Direct repomix binary in PATH
        repomix_bin = shutil.which("repomix")
        if repomix_bin:
            return [repomix_bin]

        # 2. Check for Windows repomix.cmd
        if os.name == "nt":
            repomix_cmd = shutil.which("repomix.cmd")
            if repomix_cmd:
                return [repomix_cmd]

        # 3. Check for npx
        npx_bin = shutil.which("npx") or (shutil.which("npx.cmd") if os.name == "nt" else None)
        if npx_bin:
            return [npx_bin, "--yes", "repomix"]

        return None

    @classmethod
    def is_available(cls) -> bool:
        """Check if repomix can be executed in the current environment."""
        return cls.find_executable() is not None

    @classmethod
    def run(
        cls,
        target_dir: Path,
        output_file: Path,
        options: IngestionOptions,
    ) -> Dict[str, Any]:
        """Execute repomix against target_dir and write output to output_file.

        Returns parsed statistics (total_files, total_tokens, total_chars, top_files).
        """
        executable_cmd = cls.find_executable()
        if not executable_cmd:
            raise RepomixExecutionError("Neither 'repomix' CLI nor 'npx' is installed or accessible in system PATH.")

        cmd = list(executable_cmd)
        cmd.append(str(target_dir))
        cmd.extend(["--style", options.style])
        cmd.extend(["-o", str(output_file)])

        if options.compress:
            cmd.append("--compress")
        if options.remove_comments:
            cmd.append("--remove-comments")
        if options.remove_empty_lines:
            cmd.append("--remove-empty-lines")

        # Apply comprehensive ignore patterns
        ignore_patterns = options.effective_ignore_patterns
        if ignore_patterns:
            cmd.extend(["--ignore", ",".join(ignore_patterns)])

        if options.include_patterns:
            cmd.extend(["--include", ",".join(options.include_patterns)])

        logger.info("Executing repomix command: %s", " ".join(cmd))

        # Windows command shell handling
        use_shell = os.name == "nt"

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                shell=use_shell,  # nosec: B602
                stdin=subprocess.DEVNULL,
                timeout=45,  # 45-second safety timeout prevents infinite hangs
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise RepomixExecutionError("Repomix CLI process timed out after 45 seconds.")
        except Exception as err:
            raise RepomixExecutionError(f"Failed to launch repomix process: {err}") from err

        if proc.returncode != 0:
            error_output = (proc.stderr or proc.stdout or "").strip()
            raise RepomixExecutionError(f"Repomix execution failed with code {proc.returncode}:\n{error_output}")

        if not output_file.exists():
            raise RepomixExecutionError(
                f"Repomix reported success but expected output file was not found: {output_file}"
            )

        # Parse repomix stdout summary
        stats = cls._parse_repomix_output(proc.stdout)
        return stats

    @classmethod
    def _parse_repomix_output(cls, stdout: str) -> Dict[str, Any]:
        """Extract statistics from repomix console stdout."""
        stats: Dict[str, Any] = {
            "total_files": 0,
            "total_tokens": None,
            "total_chars": 0,
            "top_files": [],
        }

        # Match "Total Files: 42 files"
        files_match = re.search(r"Total Files:\s+(\d+)", stdout)
        if files_match:
            stats["total_files"] = int(files_match.group(1))

        # Match "Total Tokens: 12,345 tokens"
        tokens_match = re.search(r"Total Tokens:\s+([\d,]+)", stdout)
        if tokens_match:
            stats["total_tokens"] = int(tokens_match.group(1).replace(",", ""))

        # Match "Total Chars: 45,678 chars"
        chars_match = re.search(r"Total Chars:\s+([\d,]+)", stdout)
        if chars_match:
            stats["total_chars"] = int(chars_match.group(1).replace(",", ""))

        # Match top files list: "1.  path/to/file.py (64 tokens, 213 chars, 13.4%)"
        top_files_regex = re.compile(
            r"^\s*\d+\.\s+(?P<path>[^\(]+)\s+\((?P<tokens>[\d,]+)\s+tokens?,\s+(?P<chars>[\d,]+)\s+chars?",
            re.MULTILINE,
        )
        for match in top_files_regex.finditer(stdout):
            stats["top_files"].append(
                {
                    "path": match.group("path").strip(),
                    "tokens": int(match.group("tokens").replace(",", "")),
                    "chars": int(match.group("chars").replace(",", "")),
                }
            )

        return stats


# -----------------------------------------------------------------------------
# Pure Python Fallback Codebase Packager
# -----------------------------------------------------------------------------


class PythonCodebasePackager:
    """Zero-dependency fallback packager that produces Repomix-compatible output.

    Uses Python's AST parser to compress Python files down to signatures and docstrings,
    builds the directory hierarchy, and ignores build/cache directories.
    """

    @classmethod
    def pack(
        cls,
        target_dir: Path,
        output_file: Path,
        options: IngestionOptions,
    ) -> Dict[str, Any]:
        """Pack directory using pure Python AST and heuristics."""
        target_dir = target_dir.resolve()
        files_to_pack = cls._collect_files(target_dir, options)

        # Build directory tree
        tree_str = cls._build_directory_tree(target_dir, files_to_pack)

        # Process and pack file contents
        packed_sections: List[str] = []
        total_chars = 0
        file_stats: List[Dict[str, Any]] = []

        for rel_path, full_path in files_to_pack:
            try:
                raw_content = full_path.read_text(encoding="utf-8", errors="replace")
            except Exception as read_err:
                logger.warning("Could not read %s: %s", full_path, read_err)
                continue

            if options.compress:
                processed_content = cls._compress_content(rel_path, raw_content)
            else:
                processed_content = raw_content

            if options.remove_empty_lines:
                processed_content = "\n".join(line for line in processed_content.splitlines() if line.strip())

            lang = cls._detect_language(rel_path)
            section = f"## File: {rel_path.as_posix()}\n```{lang}\n{processed_content}\n```\n"
            packed_sections.append(section)

            c_len = len(processed_content)
            total_chars += c_len
            # Estimate tokens (~4 characters per token heuristic for code)
            est_tokens = max(1, c_len // 4)
            file_stats.append(
                {
                    "path": rel_path.as_posix(),
                    "chars": c_len,
                    "tokens": est_tokens,
                }
            )

        file_stats.sort(key=lambda item: item["chars"], reverse=True)
        top_files = file_stats[:5]
        total_tokens = sum(item["tokens"] for item in file_stats)

        # Assemble markdown output
        output_md = cls._format_markdown(
            tree_str=tree_str,
            files_count=len(files_to_pack),
            file_sections=packed_sections,
            compressed=options.compress,
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(output_md, encoding="utf-8")

        return {
            "total_files": len(files_to_pack),
            "total_tokens": total_tokens,
            "total_chars": len(output_md),
            "top_files": top_files,
            "directory_tree": tree_str,
        }

    @classmethod
    def _collect_files(
        cls,
        target_dir: Path,
        options: IngestionOptions,
    ) -> List[Tuple[Path, Path]]:
        """Collect list of (relative_path, absolute_path) skipping ignored files."""
        collected: List[Tuple[Path, Path]] = []
        ignore_patterns = options.effective_ignore_patterns
        max_bytes = options.max_file_size_kb * 1024

        for root, dirs, files in os.walk(target_dir):
            root_path = Path(root)
            rel_dir = root_path.relative_to(target_dir)

            # Prune directory search early if directory matches ignore
            pruned_dirs = []
            for d in dirs:
                dir_rel = (rel_dir / d).as_posix()
                if cls._should_ignore(dir_rel + "/", ignore_patterns):
                    continue
                pruned_dirs.append(d)
            dirs[:] = pruned_dirs

            for f in files:
                full_path = root_path / f
                rel_path = full_path.relative_to(target_dir)
                rel_str = rel_path.as_posix()

                if cls._should_ignore(rel_str, ignore_patterns):
                    continue

                # Check file size limit
                try:
                    if full_path.stat().st_size > max_bytes:
                        continue
                except OSError:
                    continue

                # Ignore binary files
                if cls._is_binary_file(full_path):
                    continue

                collected.append((rel_path, full_path))

        collected.sort(key=lambda pair: pair[0].as_posix())
        return collected

    @classmethod
    def _should_ignore(cls, relative_path: str, patterns: Sequence[str]) -> bool:
        """Check if relative_path matches any glob ignore pattern."""
        import fnmatch

        normalized = relative_path.replace("\\", "/")
        for pattern in patterns:
            pat = pattern.replace("\\", "/")
            if pat.endswith("/**"):
                base = pat[:-3]
                if normalized.startswith(base + "/") or normalized == base:
                    return True
            elif fnmatch.fnmatch(normalized, pat):
                return True
            # Also check basename match
            elif fnmatch.fnmatch(os.path.basename(normalized), pat):
                return True
        return False

    @classmethod
    def _is_binary_file(cls, path: Path) -> bool:
        """Heuristic check for binary file via null byte in initial chunk."""
        try:
            with path.open("rb") as f:
                chunk = f.read(1024)
                return b"\x00" in chunk
        except Exception:
            return True

    @classmethod
    def _build_directory_tree(
        cls,
        root_dir: Path,
        files_to_pack: Sequence[Tuple[Path, Path]],
    ) -> str:
        """Generate ASCII directory tree representation."""
        if not files_to_pack:
            return "(Empty repository)"

        lines: List[str] = []
        tree: Dict[str, Any] = {}

        for rel_path, _ in files_to_pack:
            parts = rel_path.parts
            curr = tree
            for part in parts[:-1]:
                curr = curr.setdefault(part, {})
            curr[parts[-1]] = None

        def _render(node: Dict[str, Any], indent: str = "") -> None:
            entries = sorted(node.keys())
            for idx, key in enumerate(entries):
                is_last = idx == len(entries) - 1
                marker = "└── " if is_last else "├── "
                next_indent = indent + ("    " if is_last else "│   ")
                val = node[key]
                if val is None:
                    lines.append(f"{indent}{marker}{key}")
                else:
                    lines.append(f"{indent}{marker}{key}/")
                    _render(val, next_indent)

        _render(tree)
        return "\n".join(lines)

    @classmethod
    def _compress_content(cls, path: Path, content: str) -> str:
        """Extract structural signatures using Python AST or clean text truncation."""
        ext = path.suffix.lower()
        if ext == ".py":
            return cls._compress_python(content)
        # For non-Python code, keep clean or truncate very long implementations
        return content

    @classmethod
    def _compress_python(cls, source_code: str) -> str:
        """Extract module docstrings, classes, methods, and functions without internal logic."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return source_code

        lines: List[str] = []
        docstring = ast.get_docstring(tree)
        if docstring:
            lines.append(f'"""{docstring.strip()}"""\n⋮----')

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list]
                bases = [ast.unparse(b) for b in node.bases]
                bases_str = f"({', '.join(bases)})" if bases else ""
                lines.extend(decorators)
                lines.append(f"class {node.name}{bases_str}:")
                class_doc = ast.get_docstring(node)
                if class_doc:
                    lines.append(f'    """{class_doc.strip()}"""')

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        prefix = "async def " if isinstance(item, ast.AsyncFunctionDef) else "def "
                        item_decs = [f"    @{ast.unparse(d)}" for d in item.decorator_list]
                        lines.extend(item_decs)
                        args_str = ast.unparse(item.args)
                        ret_str = f" -> {ast.unparse(item.returns)}" if item.returns else ""
                        lines.append(f"    {prefix}{item.name}({args_str}){ret_str}:")
                        fn_doc = ast.get_docstring(item)
                        if fn_doc:
                            lines.append(f'        """{fn_doc.strip()}"""')
                        lines.append("        ...")
                lines.append("⋮----")

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
                decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list]
                lines.extend(decorators)
                args_str = ast.unparse(node.args)
                ret_str = f" -> {ast.unparse(node.returns)}" if node.returns else ""
                lines.append(f"{prefix}{node.name}({args_str}){ret_str}:")
                fn_doc = ast.get_docstring(node)
                if fn_doc:
                    lines.append(f'    """{fn_doc.strip()}"""')
                lines.append("    ...")
                lines.append("⋮----")

        if not lines:
            # Fallback to compact preview if no top-level classes or functions
            return source_code[:1000]

        return "\n".join(lines)

    @classmethod
    def _detect_language(cls, path: Path) -> str:
        """Map file extension to markdown syntax highlighter tag."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".jsx": "jsx",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".cs": "csharp",
            ".sh": "bash",
            ".sql": "sql",
        }
        return ext_map.get(path.suffix.lower(), "")

    @classmethod
    def _format_markdown(
        cls,
        tree_str: str,
        files_count: int,
        file_sections: Sequence[str],
        compressed: bool,
    ) -> str:
        """Format Repomix-compatible markdown document."""
        compression_notice = (
            "The content has been processed where content has been compressed "
            "(code blocks are separated by ⋮---- delimiter).\n"
            if compressed
            else ""
        )
        header = (
            "This file is a merged representation of a subset of the codebase, "
            "containing files not matching ignore patterns, combined into a single document.\n"
            f"{compression_notice}\n"
            "# File Summary\n\n"
            "## Purpose\n"
            "This file contains a packed representation of the repository's contents "
            "designed for ingestion into AI scene planning and video tutorial generation.\n\n"
            f"## Total Files Included: {files_count}\n\n"
            "# Directory Structure\n"
            f"```\n{tree_str}\n```\n\n"
            "# Files\n\n"
        )
        return header + "\n".join(file_sections)


# -----------------------------------------------------------------------------
# Main Ingestion Service Interface
# -----------------------------------------------------------------------------


class CodebaseIngestionService:
    """Production service for ingesting and packaging codebases for video generation.

    Integrates GitPython for secure repo cloning, repomix CLI for AI-friendly
    structural packaging, and a built-in Python fallback engine.
    """

    def __init__(self, workspace_root: Optional[Path | str] = None) -> None:
        """Initialize service with optional persistent workspace directory."""
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else None
        if self.workspace_root:
            self.workspace_root.mkdir(parents=True, exist_ok=True)

    def ingest_repository(
        self,
        repo_url: str,
        options: Optional[IngestionOptions] = None,
    ) -> IngestionResult:
        """Synchronously clone a public GitHub repository and run repomix packaging.

        Args:
            repo_url: Public GitHub URL (e.g. 'https://github.com/user/repo', 'user/repo')
            options: Configuration options (depth, branch, style, compress, ignore patterns)

        Returns:
            IngestionResult containing markdown representation and metadata.
        """
        start_time = time.perf_counter()
        opts = options or IngestionOptions()

        # 1. Parse and validate GitHub repository URL
        normalized_url, repo_name, embedded_branch = RepoUrlParser.parse(repo_url)
        target_branch = opts.branch or embedded_branch

        # 2. Determine workspace and output directories
        if opts.output_dir:
            out_dir = Path(opts.output_dir).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            work_dir = Path(tempfile.mkdtemp(prefix="repomix_ingest_"))
            cleanup_dir = work_dir
        elif self.workspace_root:
            repo_slug = repo_name.replace("/", "_")
            timestamp = int(time.time() * 1000)
            work_dir = self.workspace_root / f"{repo_slug}_{timestamp}"
            work_dir.mkdir(parents=True, exist_ok=True)
            out_dir = work_dir
            cleanup_dir = None
        else:
            work_dir = Path(tempfile.mkdtemp(prefix="repomix_ingest_"))
            out_dir = work_dir
            cleanup_dir = work_dir

        clone_path = work_dir / "repo"
        output_file_name = opts.output_filename or f"codebase_pack.{cls_get_ext(opts.style)}"
        output_file_path = out_dir / output_file_name

        repo_obj = None
        try:
            # 3. Clone repository using GitPython
            repo_obj, git_meta = GitCloneService.clone(
                repo_url=normalized_url,
                target_dir=clone_path,
                depth=opts.clone_depth,
                branch=target_branch,
            )

            # 4. Execute packaging (Repomix CLI or Native Fallback)
            engine_to_use, stats = self._run_packager(
                target_dir=clone_path,
                output_file=output_file_path,
                options=opts,
            )

            content = output_file_path.read_text(encoding="utf-8")
            elapsed = time.perf_counter() - start_time

            # Extract or build tree representation
            tree_repr = stats.get("directory_tree") or self._extract_directory_tree_from_markdown(content)

            result = IngestionResult(
                repo_url=normalized_url,
                repo_name=repo_name,
                branch=git_meta["branch"],
                commit_sha=git_meta["commit_sha"],
                commit_message=git_meta["commit_message"],
                output_path=output_file_path,
                content=content,
                total_files=stats.get("total_files", 0),
                total_tokens=stats.get("total_tokens"),
                total_chars=len(content),
                directory_tree=tree_repr,
                top_files=stats.get("top_files", []),
                engine_used=engine_to_use,
                duration_seconds=elapsed,
                cloned_path=clone_path if opts.keep_cloned_repo else None,
                _cleanup_dir=cleanup_dir,
            )
            return result

        finally:
            # Ensure git repo object is closed to release file handles on Windows
            if repo_obj is not None:
                try:
                    repo_obj.close()
                except Exception as exc:
                    logger.debug("Failed closing repo_obj handle: %s", exc)

            # If keep_cloned_repo is False, delete the heavy cloned repository (.git, source files)
            # while keeping output_file_path accessible for downstream consumers
            if not opts.keep_cloned_repo and clone_path.exists():
                robust_rmtree(clone_path)

    def ingest_local_directory(
        self,
        directory_path: Path | str,
        options: Optional[IngestionOptions] = None,
        repo_name: str = "local_repository",
    ) -> IngestionResult:
        """Ingest a pre-existing local directory without cloning.

        Useful for testing or local project processing.
        """
        start_time = time.perf_counter()
        opts = options or IngestionOptions()
        dir_path = Path(directory_path).resolve()

        if not dir_path.is_dir():
            raise IngestionError(f"Directory not found: {dir_path}")

        if opts.output_dir:
            out_dir = Path(opts.output_dir).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            cleanup_dir = None
        else:
            out_dir = Path(tempfile.mkdtemp(prefix="local_pack_"))
            cleanup_dir = out_dir

        output_file_name = opts.output_filename or f"codebase_pack.{cls_get_ext(opts.style)}"
        output_file_path = out_dir / output_file_name

        try:
            engine_to_use, stats = self._run_packager(
                target_dir=dir_path,
                output_file=output_file_path,
                options=opts,
            )

            content = output_file_path.read_text(encoding="utf-8")
            elapsed = time.perf_counter() - start_time
            tree_repr = stats.get("directory_tree") or self._extract_directory_tree_from_markdown(content)

            return IngestionResult(
                repo_url=str(dir_path),
                repo_name=repo_name,
                branch="local",
                commit_sha="local",
                commit_message="Local directory ingestion",
                output_path=output_file_path,
                content=content,
                total_files=stats.get("total_files", 0),
                total_tokens=stats.get("total_tokens"),
                total_chars=len(content),
                directory_tree=tree_repr,
                top_files=stats.get("top_files", []),
                engine_used=engine_to_use,
                duration_seconds=elapsed,
                cloned_path=dir_path,
                _cleanup_dir=cleanup_dir,
            )
        except Exception:
            if cleanup_dir and cleanup_dir.exists():
                robust_rmtree(cleanup_dir)
            raise

    async def async_ingest_repository(
        self,
        repo_url: str,
        options: Optional[IngestionOptions] = None,
    ) -> IngestionResult:
        """Asynchronously clone and package repository (runs non-blocking in thread pool)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.ingest_repository(repo_url, options),
        )

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _run_packager(
        self,
        target_dir: Path,
        output_file: Path,
        options: IngestionOptions,
    ) -> Tuple[str, Dict[str, Any]]:
        """Dispatch packaging to repomix CLI or fallback engine."""
        engine = options.engine

        if engine in ("auto", "repomix-cli") and RepomixCliRunner.is_available():
            try:
                stats = RepomixCliRunner.run(target_dir, output_file, options)
                return "repomix-cli", stats
            except RepomixExecutionError as cli_err:
                if engine == "repomix-cli":
                    raise
                logger.warning("Repomix CLI failed, falling back to native packager: %s", cli_err)

        # Fallback to pure Python engine
        logger.info("Using native PythonCodebasePackager engine")
        stats = PythonCodebasePackager.pack(target_dir, output_file, options)
        return "python-native", stats

    @staticmethod
    def _extract_directory_tree_from_markdown(content: str) -> str:
        """Extract directory structure block from generated markdown if available."""
        tree_match = re.search(r"# Directory Structure\s*```[a-zA-Z]*\n([\s\S]*?)```", content)
        if tree_match:
            return tree_match.group(1).strip()
        return ""


def cls_get_ext(style: str) -> str:
    """Return default file extension for a chosen style."""
    if style == "markdown":
        return "md"
    if style == "xml":
        return "xml"
    if style == "json":
        return "json"
    return "txt"
