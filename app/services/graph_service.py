"""Codebase Graph Generation Service.

Inspired by open-source codebase knowledge graph libraries (such as blarify and graphify).
Performs multi-language Abstract Syntax Tree (AST) parsing, import analysis, and dependency
extraction across repository files to output a structured graph of components and connections.
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from manim_engine.models import NodeType

logger = logging.getLogger("graph_service")


# -----------------------------------------------------------------------------
# Graph Data Models
# -----------------------------------------------------------------------------


class GraphNode(BaseModel):
    """Represents a source file, module, or component node in the repository graph."""

    id: str = Field(..., description="Unique alphanumeric identifier (e.g. normalized module dotpath)")
    label: str = Field(..., description="Display title for the node, e.g. 'video_composer.py'")
    path: str = Field(..., description="Relative file path from the repository root")
    kind: NodeType = Field(default=NodeType.BACKEND, description="Architectural archetype classification")
    language: str = Field(default="python", description="Programming language of the source file")
    size_bytes: int = Field(default=0, description="File size on disk in bytes")
    lines_of_code: int = Field(default=0, description="Total line count")
    classes: List[str] = Field(default_factory=list, description="Top-level classes declared in the file")
    functions: List[str] = Field(default_factory=list, description="Top-level functions/methods declared")
    imports: List[str] = Field(default_factory=list, description="Raw external and internal import strings")
    layer: int = Field(default=2, description="Architectural tier index (0=Client, 1=Gateway, 2=Core, 3=Queue, 4=DB)")
    tech: Optional[str] = Field(default=None, description="Inferred technology or framework badge")
    details: List[str] = Field(default_factory=list, description="Summary highlights and responsibilities")
    in_degree: int = Field(default=0, description="Number of modules depending on this node")
    out_degree: int = Field(default=0, description="Number of modules this node depends on")


class GraphEdge(BaseModel):
    """Represents a directed import, call, or dependency connection between two nodes."""

    id: str = Field(..., description="Unique connection identifier")
    source_id: str = Field(..., description="Origin node ID (the importer)")
    target_id: str = Field(..., description="Destination node ID (the imported module)")
    label: Optional[str] = Field(default="imports", description="Human-readable edge label")
    protocol: str = Field(default="IMPORT", description="Relationship protocol badge (IMPORT, CALL, REST)")
    symbols: List[str] = Field(default_factory=list, description="Specific classes/functions imported")
    weight: int = Field(default=1, description="Connection strength / number of imported symbols")


class CodebaseGraph(BaseModel):
    """Complete root payload for an AST-extracted codebase knowledge graph."""

    repo_name: str = Field(..., description="Name or identifier of the parsed repository")
    repo_path: str = Field(..., description="Absolute or relative root path of the repository")
    total_files: int = Field(default=0, description="Total number of analyzed source files")
    total_lines: int = Field(default=0, description="Sum total of code lines across all nodes")
    nodes: List[GraphNode] = Field(default_factory=list, description="Collection of component nodes")
    edges: List[GraphEdge] = Field(default_factory=list, description="Collection of dependency edges")
    languages: Dict[str, int] = Field(default_factory=dict, description="Distribution of file count by language")
    entrypoints: List[str] = Field(default_factory=list, description="Detected entrypoint node IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Supplementary parsing metrics")


# -----------------------------------------------------------------------------
# Ignored Folders & Extensions
# -----------------------------------------------------------------------------

IGNORED_DIRECTORIES: Set[str] = {
    ".git",
    ".github",
    ".gitlab",
    ".svn",
    ".hg",
    "node_modules",
    "bower_components",
    ".next",
    ".nuxt",
    ".turbo",
    ".output",
    "dist",
    "build",
    "out",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "vendor",
    "output_artifacts",
    "manim_media",
}

LANGUAGE_EXTENSIONS: Dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript-react",
    ".js": "javascript",
    ".jsx": "javascript-react",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".sql": "sql",
}


# -----------------------------------------------------------------------------
# Codebase Graph Generation Service
# -----------------------------------------------------------------------------


class CodebaseGraphService:
    """Extracts codebase architecture graphs via AST and regex dependency parsing."""

    def __init__(self, max_nodes: int = 40) -> None:
        self.max_nodes = max_nodes

    def generate_graph(self, repo_path: Union[str, Path], repo_name: Optional[str] = None) -> CodebaseGraph:
        """Scan repository directory, perform AST parsing, and return the complete CodebaseGraph.

        Args:
            repo_path: Directory path of the cloned codebase
            repo_name: Optional repository name (defaults to directory name)

        Returns:
            CodebaseGraph model with nodes, edges, and architectural metadata.
        """
        root = Path(repo_path).resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"Repository directory does not exist: {root}")

        name = repo_name or root.name

        # 1. Discover all source files
        source_files = self._discover_source_files(root)

        # 2. Extract AST metadata from each file
        raw_nodes: List[GraphNode] = []
        node_lookup_by_rel_path: Dict[str, GraphNode] = {}
        node_lookup_by_module: Dict[str, GraphNode] = {}
        lang_counts: Dict[str, int] = {}
        total_loc = 0

        for rel_path in source_files:
            abs_path = root / rel_path
            node = self._parse_file_ast(root, rel_path, abs_path)
            raw_nodes.append(node)
            total_loc += node.lines_of_code

            # Record language counts
            lang_counts[node.language] = lang_counts.get(node.language, 0) + 1

            # Populate lookups for dependency linking
            norm_rel = rel_path.replace("\\", "/")
            node_lookup_by_rel_path[norm_rel] = node
            # Module dot-path representation (e.g. "app.services.video_composer")
            no_ext = os.path.splitext(norm_rel)[0]
            module_dot = no_ext.replace("/", ".")
            node_lookup_by_module[module_dot] = node
            node_lookup_by_module[no_ext] = node
            node_lookup_by_module[Path(norm_rel).name] = node
            node_lookup_by_module[Path(norm_rel).stem] = node

        # 3. Resolve imports and build dependency edges
        edges: List[GraphEdge] = []
        edge_set: Set[Tuple[str, str]] = set()

        for node in raw_nodes:
            for imp in node.imports:
                target_node = self._resolve_import_to_node(
                    import_str=imp,
                    current_node_path=node.path,
                    lookup_by_module=node_lookup_by_module,
                    lookup_by_path=node_lookup_by_rel_path,
                )
                if target_node and target_node.id != node.id:
                    edge_key = (node.id, target_node.id)
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        node.out_degree += 1
                        target_node.in_degree += 1
                        edge_id = f"edge_{len(edges) + 1:03d}_{node.id}_to_{target_node.id}"
                        edges.append(
                            GraphEdge(
                                id=edge_id,
                                source_id=node.id,
                                target_id=target_node.id,
                                label=f"imports {target_node.label}",
                                protocol="IMPORT",
                                symbols=[imp.split()[-1]],
                                weight=1,
                            )
                        )

        # 4. Prune/Prioritize top nodes if repository exceeds max_nodes limit
        selected_nodes, selected_edges = self._prioritize_top_nodes(raw_nodes, edges, limit=self.max_nodes)

        # 5. Detect entrypoints (nodes with out_degree > 0 and in_degree == 0, or named main/app/index)
        entrypoints: List[str] = []
        for n in selected_nodes:
            stem = Path(n.path).stem.lower()
            if stem in ("main", "app", "index", "server", "cli", "entry") or (n.layer in (0, 1) and n.out_degree > 0):
                entrypoints.append(n.id)

        return CodebaseGraph(
            repo_name=name,
            repo_path=str(root),
            total_files=len(selected_nodes),
            total_lines=total_loc,
            nodes=selected_nodes,
            edges=selected_edges,
            languages=lang_counts,
            entrypoints=entrypoints,
            metadata={
                "raw_file_count": len(raw_nodes),
                "total_edges_detected": len(edges),
                "max_nodes_configured": self.max_nodes,
                "parser": "AST+Regex MultiLanguage Engine",
            },
        )

    # -------------------------------------------------------------------------
    # File Discovery & Traversal
    # -------------------------------------------------------------------------

    def _discover_source_files(self, root: Path) -> List[str]:
        """Discover valid source files while skipping ignored folders and binary files."""
        discovered: List[str] = []
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories in-place to avoid deep traversal
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRECTORIES and not d.startswith(".")]

            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in LANGUAGE_EXTENSIONS:
                    full_p = Path(dirpath) / fn
                    try:
                        rel = str(full_p.relative_to(root)).replace("\\", "/")
                        discovered.append(rel)
                    except ValueError:
                        continue

        # Sort files deterministically
        discovered.sort()
        return discovered

    # -------------------------------------------------------------------------
    # AST Parsing by Language
    # -------------------------------------------------------------------------

    def _parse_file_ast(self, root: Path, rel_path: str, abs_path: Path) -> GraphNode:
        """Parse file content using Python AST or language regex to extract classes, functions, and imports."""
        ext = abs_path.suffix.lower()
        language = LANGUAGE_EXTENSIONS.get(ext, "unknown")
        size_bytes = abs_path.stat().st_size if abs_path.exists() else 0

        # Read text safely
        try:
            content = abs_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.debug("Could not read file %s: %s", abs_path, exc)
            content = ""

        lines = content.splitlines()
        loc = len([line for line in lines if line.strip() and not line.strip().startswith(("#", "//", "/*"))])

        classes: List[str] = []
        functions: List[str] = []
        imports: List[str] = []

        if language == "python":
            classes, functions, imports = self._parse_python_ast(content)
        elif language in ("typescript", "typescript-react", "javascript", "javascript-react"):
            classes, functions, imports = self._parse_js_ts_file(content)
        else:
            classes, functions, imports = self._parse_generic_code(content)

        # Infer architectural kind and layer
        kind, layer, tech = self._classify_architectural_role(rel_path, content, classes, functions)

        # Generate unique node ID (e.g. "node_app_services_video_composer")
        clean_rel = rel_path.replace("\\", "/").lstrip("/")
        node_id = "node_" + re.sub(r"[^A-Za-z0-9_]", "_", os.path.splitext(clean_rel)[0]).strip("_")

        # Summary details
        details: List[str] = []
        if classes:
            details.append(f"Classes: {', '.join(classes[:2])}")
        if functions:
            details.append(f"Methods: {', '.join(functions[:2])}")
        if not details:
            details.append(f"{loc} LOC")

        return GraphNode(
            id=node_id,
            label=Path(rel_path).name,
            path=rel_path,
            kind=kind,
            language=language,
            size_bytes=size_bytes,
            lines_of_code=loc,
            classes=classes[:8],
            functions=functions[:10],
            imports=imports,
            layer=layer,
            tech=tech,
            details=details,
        )

    def _parse_python_ast(self, content: str) -> Tuple[List[str], List[str], List[str]]:
        """Extract top-level classes, functions, and imports via Python's AST parser."""
        classes: List[str] = []
        functions: List[str] = []
        imports: List[str] = []

        try:
            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    # Extract class methods as well (skipping dunder methods)
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not item.name.startswith("__"):
                                functions.append(item.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    # Preserve relative import level notation
                    prefix = "." * node.level
                    full_mod = f"{prefix}{mod}"
                    for alias in node.names:
                        imports.append(f"{full_mod}.{alias.name}" if full_mod else alias.name)
        except SyntaxError:
            # Fallback to regex line parsing if AST fails
            classes, functions, imports = self._parse_python_regex_fallback(content)

        return classes, functions, imports

    @staticmethod
    def _parse_python_regex_fallback(content: str) -> Tuple[List[str], List[str], List[str]]:
        """Regex-based fallback for files with Python syntax errors."""
        classes = re.findall(r"^class\s+([A-Za-z0-9_]+)", content, re.MULTILINE)
        functions = re.findall(r"^(?:async\s+)?def\s+([A-Za-z0-9_]+)", content, re.MULTILINE)
        imports: List[str] = []

        import_lines = re.findall(r"^(?:from\s+([A-Za-z0-9_.]+)\s+import|import\s+([A-Za-z0-9_., ]+))", content, re.MULTILINE)
        for f_mod, i_mods in import_lines:
            if f_mod:
                imports.append(f_mod.strip())
            elif i_mods:
                for item in i_mods.split(","):
                    cleaned = item.strip().split()[0]
                    if cleaned:
                        imports.append(cleaned)

        return classes, functions, imports

    @staticmethod
    def _parse_js_ts_file(content: str) -> Tuple[List[str], List[str], List[str]]:
        """Extract components, functions, and imports from JS/TS codebases."""
        classes = re.findall(r"(?:export\s+)?class\s+([A-Za-z0-9_]+)", content)
        # Match standard functions and React functional components (e.g. export function VideoPlayer)
        functions = re.findall(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)", content)
        # Match const arrow components (e.g. const JobProgress = ...)
        arrow_funcs = re.findall(r"(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", content)
        functions.extend(arrow_funcs)

        # Match ES module and CommonJS imports
        imports: List[str] = []
        es_imports = re.findall(r"import\s+(?:[^'\"]+from\s+)?['\"]([^'\"]+)['\"]", content)
        imports.extend(es_imports)
        require_imports = re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content)
        imports.extend(require_imports)

        return classes, functions, imports

    @staticmethod
    def _parse_generic_code(content: str) -> Tuple[List[str], List[str], List[str]]:
        """Generic fallback for Go, Rust, Java, etc."""
        classes = re.findall(r"(?:struct|class|interface|type)\s+([A-Za-z0-9_]+)", content)
        functions = re.findall(r"(?:fn|func|def|function)\s+([A-Za-z0-9_]+)", content)
        imports = re.findall(r"(?:import|use|include)\s+['\"]?([A-Za-z0-9_./]+)['\"]?", content)
        return classes, functions, imports

    # -------------------------------------------------------------------------
    # Architectural Classification & Layer Mapping
    # -------------------------------------------------------------------------

    @staticmethod
    def _classify_architectural_role(
        rel_path: str, content: str, classes: List[str], functions: List[str]
    ) -> Tuple[NodeType, int, Optional[str]]:
        """Determine architectural archetype, horizontal layer, and technology badge."""
        path_lower = rel_path.lower()
        content_lower = content[:3000].lower()

        # 1. Database / Persistence / Models (Layer 4)
        if any(p in path_lower for p in ["models/", "db/", "schemas/", "database/", "entities/", "alembic/"]) or any(
            k in content_lower for k in ["sqlalchemy", "base.metadata", "foreignkey", "sessionmaker", "asyncpg", "basemodel"]
        ):
            tech = "SQLAlchemy ORM" if "sqlalchemy" in content_lower else ("Pydantic Model" if "basemodel" in content_lower else "Database Entity")
            return NodeType.DATABASE, 4, tech

        # 2. Message Queue / Cache / Workers (Layer 3)
        if any(p in path_lower for p in ["workers/", "tasks/", "jobs/", "queues/", "celery", "redis", "cache/"]) or any(
            k in content_lower for k in ["@celery_app", "celery", "redis", "kombu", "rabbitmq"]
        ):
            tech = "Redis / Celery" if "celery" in content_lower else "Task Worker"
            return NodeType.QUEUE, 3, tech

        # 3. API Gateway / Routing / Controllers (Layer 1)
        if any(p in path_lower for p in ["api/", "routes/", "controllers/", "endpoints/", "routers/", "gateway"]):
            tech = "REST API"
            if "fastapi" in content_lower or "router" in content_lower:
                tech = "FastAPI Router"
            elif "express" in content_lower:
                tech = "Express Router"
            return NodeType.GATEWAY, 1, tech

        if Path(rel_path).stem.lower() in ("main", "app", "server", "index") and ("fastapi" in content_lower or "uvicorn" in content_lower):
            return NodeType.GATEWAY, 1, "FastAPI Application"

        # 4. Frontend / Client UI (Layer 0)
        if any(
            p in path_lower
            for p in ["frontend/", "client/", "components/", "ui/", "views/", ".tsx", ".jsx", "pages/"]
        ) or any(k in content_lower for k in ["react", "usestate", "useeffect", "jsx", "from 'react'", 'from "react"']):
            tech = "React UI"
            if "next" in content_lower or "next" in path_lower:
                tech = "Next.js"
            elif "tailwind" in content_lower:
                tech = "Tailwind CSS"
            return NodeType.FRONTEND, 0, tech

        # 5. Core Services / Domain Logic (Layer 2)
        tech = "Python Service"
        if "fastapi" in content_lower:
            tech = "FastAPI Service"
        elif "service" in path_lower or "engine" in path_lower:
            tech = "Core Engine"

        return NodeType.BACKEND, 2, tech

    # -------------------------------------------------------------------------
    # Import Resolution to Graph Nodes
    # -------------------------------------------------------------------------

    def _resolve_import_to_node(
        self,
        import_str: str,
        current_node_path: str,
        lookup_by_module: Dict[str, GraphNode],
        lookup_by_path: Dict[str, GraphNode],
    ) -> Optional[GraphNode]:
        """Resolve a raw import statement string to a known GraphNode in the codebase."""
        clean_imp = import_str.strip()

        # Direct module lookup (e.g. "app.services.video_composer")
        if clean_imp in lookup_by_module:
            return lookup_by_module[clean_imp]

        # Handle prefix matches (e.g. "app.services.video_composer.VideoComposer" -> "app.services.video_composer")
        parts = clean_imp.split(".")
        for i in range(len(parts) - 1, 0, -1):
            sub_mod = ".".join(parts[:i])
            if sub_mod in lookup_by_module:
                return lookup_by_module[sub_mod]

        # Handle JS/TS relative imports (e.g. "../components/JobProgress" or "./utils")
        if clean_imp.startswith("."):
            current_dir = Path(current_node_path).parent
            resolved_p = (current_dir / clean_imp).resolve()
            # Normalize to relative path
            for ext in [".ts", ".tsx", ".js", ".jsx", ".py", "/index.ts", "/index.tsx", "/index.js"]:
                candidate = (clean_imp + ext).lstrip("./")
                if candidate in lookup_by_path:
                    return lookup_by_path[candidate]

            # Try matching basename
            base = Path(clean_imp).name
            if base in lookup_by_module:
                return lookup_by_module[base]

        # Check last token
        last_token = parts[-1] if parts else clean_imp
        if last_token in lookup_by_module:
            return lookup_by_module[last_token]

        return None

    # -------------------------------------------------------------------------
    # Node Prioritization & Pruning
    # -------------------------------------------------------------------------

    @staticmethod
    def _prioritize_top_nodes(
        nodes: List[GraphNode], edges: List[GraphEdge], limit: int
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """If repository exceeds limit, retain the most central nodes by in/out degree and layer spread."""
        if len(nodes) <= limit:
            return nodes, edges

        # Score nodes: degree centrality + layer diversity bonus
        scored: List[Tuple[float, GraphNode]] = []
        for n in nodes:
            degree = n.in_degree * 2.0 + n.out_degree
            # Bonus for core architectural layers
            layer_bonus = 3.0 if n.layer in (1, 2) else 1.5
            # Entrypoint bonus
            stem = Path(n.path).stem.lower()
            entry_bonus = 5.0 if stem in ("main", "app", "index", "server") else 0.0
            score = degree + layer_bonus + entry_bonus
            scored.append((score, n))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_nodes = [item[1] for item in scored[:limit]]
        top_node_ids = {n.id for n in top_nodes}

        # Filter edges to only connect retained nodes
        filtered_edges = [
            e for e in edges if e.source_id in top_node_ids and e.target_id in top_node_ids
        ]

        return top_nodes, filtered_edges
