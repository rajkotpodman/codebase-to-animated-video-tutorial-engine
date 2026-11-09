"""AI Codebase Analysis & Video Script Synthesis Service.

Analyzes the compressed codebase representation (from Repomix Ingestion) using
the Gemini API to dynamically generate:
  1. Structured Architecture Topology (matching ArchitectureDiagramData for Manim rendering)
  2. Technical Narration Script (with scene tags and pacing for TTS voiceover)
  3. Comprehensive, multi-scene Manim Python script (File Tree, Architecture Flowchart,
     Core Logic Walkthrough, and Conclusion) lasting 60-90 seconds.

Includes intelligent heuristic extraction fallback when GEMINI_API_KEY is not set.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.services.graph_service import CodebaseGraph, GraphEdge, GraphNode
from app.schemas import resolve_language_info, LanguageInfo, SUPPORTED_LANGUAGES
from manim_engine.models import (
    ArchitectureDiagramData,
    ConnectionModel,
    NodeModel,
    NodeType,
    SceneConfig,
)

logger = logging.getLogger("gemini_service")


@dataclasses.dataclass
class ScriptSynthesisResult:
    """Output container for the AI script & animation planning stage."""

    architecture_data: ArchitectureDiagramData
    narration_script: str
    repo_name: str
    model_used: str
    manim_script: Optional[str] = None
    scenes_summary: Optional[List[str]] = None
    target_language: str = "en"


# Known supported Google Gemini models and backward-compatible aliases
SUPPORTED_GEMINI_MODELS = {
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
}

MODEL_ALIASES: Dict[str, str] = {
    "gemini-3.8-flash": "gemini-2.5-flash",
    "gemini-3.7-flash": "gemini-2.5-flash",
    "gemini-3.8": "gemini-2.5-flash",
    "gemini-3.7": "gemini-2.5-flash",
    "gemini-flash": "gemini-2.5-flash",
    "gemini-pro": "gemini-2.5-pro",
}


class GeminiScriptService:
    """Orchestrates Gemini API prompts for automated tutorial video generation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        # Resolve aliases (e.g. gemini-3.7/3.8 -> gemini-2.5-flash)
        raw_model = (model or "gemini-2.5-flash").strip().lower()
        resolved_model = MODEL_ALIASES.get(raw_model, raw_model)
        if resolved_model not in SUPPORTED_GEMINI_MODELS and not resolved_model.startswith("gemini-"):
            logger.info("Unrecognized model '%s'; defaulting to gemini-2.5-flash", model)
            resolved_model = "gemini-2.5-flash"
        self.model = resolved_model

    def synthesize_script_and_architecture(
        self,
        codebase_pack: str,
        repo_name: str,
        custom_instructions: Optional[str] = None,
        codebase_graph: Optional[Union[CodebaseGraph, Dict[str, Any], str, Path]] = None,
        target_language: Optional[str] = "en",
    ) -> ScriptSynthesisResult:
        """Generate high-level architecture diagram JSON, narration script, and multi-scene Manim script.

        Args:
            codebase_pack: Compressed Repomix markdown or text representation of the repository.
            repo_name: Identifier or title of the repository.
            custom_instructions: Optional user prompt tuning instructions.
            codebase_graph: Optional AST-extracted CodebaseGraph instance or dictionary containing
                exact components, database models, route handlers, and dependency edges.
            target_language: Target natural language for narration (e.g. 'gu', 'hi', 'mr', 'es', 'fr', 'en').
        """
        effective_lang = target_language or "en"
        if self.api_key:
            try:
                return self._call_gemini_api(
                    codebase_pack,
                    repo_name,
                    custom_instructions,
                    codebase_graph=codebase_graph,
                    target_language=effective_lang,
                )
            except Exception as exc:
                logger.warning("Gemini API call failed (%s). Falling back to heuristic synthesis.", exc)

        logger.info("Using intelligent heuristic multi-scene synthesis for %s (language: %s)", repo_name, effective_lang)
        return self._heuristic_synthesis(codebase_pack, repo_name, codebase_graph=codebase_graph, target_language=effective_lang)

    # -------------------------------------------------------------------------
    # Graph Parsing & Serialization Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _coerce_codebase_graph(
        graph_input: Optional[Union[CodebaseGraph, Dict[str, Any], str, Path]],
    ) -> Optional[CodebaseGraph]:
        """Convert varied graph input representations into a validated CodebaseGraph instance."""
        if graph_input is None:
            return None
        if isinstance(graph_input, CodebaseGraph):
            return graph_input
        if isinstance(graph_input, dict):
            try:
                return CodebaseGraph.model_validate(graph_input)
            except Exception as err:
                logger.debug("Failed validating dict as CodebaseGraph: %s", err)
                return None
        if isinstance(graph_input, (str, Path)) and os.path.exists(str(graph_input)):
            try:
                raw_text = Path(graph_input).read_text(encoding="utf-8")
                return CodebaseGraph.model_validate_json(raw_text)
            except Exception as err:
                logger.debug("Failed reading graph file: %s", err)
                return None
        if isinstance(graph_input, str):
            try:
                return CodebaseGraph.model_validate_json(graph_input)
            except Exception:
                return None
        return None

    @classmethod
    def _format_graph_for_prompt(cls, graph: CodebaseGraph) -> str:
        """Format the CodebaseGraph into an information-dense, structured JSON string for Gemini ingestion."""
        db_nodes = [n for n in graph.nodes if n.kind == NodeType.DATABASE]
        gateway_nodes = [n for n in graph.nodes if n.kind == NodeType.GATEWAY]
        frontend_nodes = [n for n in graph.nodes if n.kind in (NodeType.FRONTEND, NodeType.CLIENT)]
        backend_nodes = [n for n in graph.nodes if n.kind == NodeType.BACKEND]
        queue_nodes = [n for n in graph.nodes if n.kind == NodeType.QUEUE]

        payload = {
            "repository": graph.repo_name,
            "metrics": {
                "total_files": graph.total_files,
                "total_lines": graph.total_lines,
                "languages": graph.languages,
                "entrypoints": graph.entrypoints,
            },
            "database_models_and_tables": [
                {
                    "node_id": n.id,
                    "file_path": n.path,
                    "classes": n.classes,
                    "functions": n.functions,
                    "tech": n.tech or "Database",
                    "details": n.details,
                }
                for n in db_nodes
            ],
            "gateway_and_api_routes": [
                {
                    "node_id": n.id,
                    "file_path": n.path,
                    "classes": n.classes,
                    "functions": n.functions,
                    "tech": n.tech or "API Gateway",
                    "details": n.details,
                }
                for n in gateway_nodes
            ],
            "frontend_components": [
                {
                    "node_id": n.id,
                    "file_path": n.path,
                    "classes": n.classes,
                    "functions": n.functions,
                    "tech": n.tech or "Frontend",
                    "details": n.details,
                }
                for n in frontend_nodes
            ],
            "core_backend_services": [
                {
                    "node_id": n.id,
                    "file_path": n.path,
                    "classes": n.classes,
                    "functions": n.functions,
                    "tech": n.tech or "Core Engine",
                    "details": n.details,
                }
                for n in backend_nodes
            ],
            "queues_and_workers": [
                {
                    "node_id": n.id,
                    "file_path": n.path,
                    "classes": n.classes,
                    "functions": n.functions,
                    "tech": n.tech or "Queue Worker",
                    "details": n.details,
                }
                for n in queue_nodes
            ],
            "dependency_edges": [
                {
                    "from_node": e.source_id,
                    "to_node": e.target_id,
                    "relationship": e.label or "imports",
                    "protocol": e.protocol,
                    "symbols": e.symbols,
                }
                for e in graph.edges[:30]
            ],
        }
        return json.dumps(payload, indent=2)

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # Gemini API Implementation
    # -------------------------------------------------------------------------

    def _call_gemini_api(
        self,
        codebase_pack: str,
        repo_name: str,
        custom_instructions: Optional[str],
        codebase_graph: Optional[Union[CodebaseGraph, Dict[str, Any], str, Path]] = None,
        target_language: Optional[str] = "en",
    ) -> ScriptSynthesisResult:
        """Call official Google GenAI SDK to synthesize multi-scene architecture, narration, and Manim code."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        effective_lang = target_language or "en"
        lang_info = resolve_language_info(effective_lang)

        graph_obj = self._coerce_codebase_graph(codebase_graph)
        graph_json_prompt = ""
        graph_instruction_supplement = ""

        if graph_obj is not None:
            formatted_graph = self._format_graph_for_prompt(graph_obj)
            graph_json_prompt = (
                f"\n=== Structured Codebase Dependency Graph (AST Extracted) ===\n"
                f"{formatted_graph}\n\n"
            )
            graph_instruction_supplement = (
                "\nCRITICAL AST DEPENDENCY GRAPH INGESTION RULES:\n"
                "- You are given an AST-extracted Codebase Dependency Graph detailing exact database models/tables, "
                "API routes, frontend components, and dependency edges.\n"
                "- In 'narration_script', you MUST explicitly cite and explain the exact database models/tables, "
                "backend route handlers, and frontend components found in this graph.\n"
                "- In Scene 2 & Scene 3, describe the genuine classes and methods rather than vague generalizations.\n"
                "- In 'architecture', ensure nodes and connections match the verified graph topology.\n"
            )

        multilingual_prompt_instruction = ""
        if lang_info.code != "en":
            multilingual_prompt_instruction = (
                f"\nCRITICAL MULTILINGUAL NARRATION REQUIREMENT:\n"
                f"- Target Narration Language: {lang_info.name} ({lang_info.native_name}) [Code: {lang_info.code}].\n"
                f"- The voiceover 'narration_script' MUST be written strictly in {lang_info.name} ({lang_info.native_name}).\n"
                f"- Technical identifiers, file paths, and framework names (e.g. FastAPI, PostgreSQL, routes) should be naturally integrated.\n"
                f"- Formulate fluent, grammatically accurate spoken sentences in {lang_info.name} that sound natural when read aloud by a native text-to-speech engine.\n"
                f"- Keep scene bracket tags intact with localized names, e.g. `[Scene 1: ...]`, `[Scene 2: ...]`, `[Scene 3: ...]`, `[Scene 4: ...]`. Do not omit scene brackets.\n"
            )

        system_instruction = (
            "You are a world-class principal software architect, senior technical instructor, "
            "and Manim animation specialist. Your task is to analyze the provided Repomix codebase pack "
            "and generate a comprehensive, highly technical 60-90 second animated tutorial.\n\n"
            "CRITICAL REQUIREMENTS:\n"
            "1. Extract ACTUAL components, real folder paths, and genuine business logic from this specific repository. "
            "Do NOT output generic placeholders like 'Service A' or hardcoded templates.\n"
            "2. The video MUST consist of at least 4 DISTINCT sequential scenes:\n"
            "   - Scene 1: File Tree & Project Structure (show directory hierarchy, highlight key modules)\n"
            "   - Scene 2: Architecture Flowchart (animate components, databases, gateways, and data packets)\n"
            "   - Scene 3: Core Logic Walkthrough (animate key algorithms, request pipelines, or function calls)\n"
            "   - Scene 4: Conclusion & System Summary (recap architecture strengths, throughput, and design patterns)\n"
            "3. 'manim_script': Provide complete, executable Python code for Manim Community v0.18+. "
            "It must define `class ComprehensiveTutorialScene(Scene):` or 4 scenes `FileTreeScene`, `ArchitectureFlowScene`, "
            "`CoreLogicScene`, `ConclusionScene`. It must use multiple `self.play(...)` and `self.wait(...)` calls "
            "to pace the animation smoothly for a total duration of 60 to 90 seconds. Use modern Manim syntax "
            "(e.g., `Create`, `FadeIn`, `FadeOut`, `Transform`, `VGroup`, `Text`, `Rectangle`, `Arrow`). "
            "Avoid obsolete methods like `ShowCreation`.\n"
            "4. 'narration_script': A detailed, professional voiceover script formatted with:\n"
            "   [Scene 1: Repository Overview & Directory Structure]\n"
            "   [Scene 2: System Architecture & Data Flow]\n"
            "   [Scene 3: Core Implementation & Logic Deep Dive]\n"
            "   [Scene 4: Lifecycle Summary & Conclusion]\n"
            "   Total length must be at least 180-260 spoken words (60-90 seconds duration). "
            "Avoid markdown symbols, asterisks, or bullet points in the narration text.\n"
            "5. 'architecture': JSON topology matching ArchitectureDiagramData with 'nodes' and 'connections'.\n"
            f"{graph_instruction_supplement}\n"
            f"{multilingual_prompt_instruction}\n"
            "Respond strictly in valid JSON using this exact schema:\n"
            "{\n"
            '  "architecture": {\n'
            '    "config": {"title": "...", "subtitle": "...", "theme": "midnight"},\n'
            '    "nodes": [{"id": "...", "label": "...", "kind": "frontend|backend|database|queue|cache|gateway", "tech": "...", "layer": 0..4, "details": ["..."]}],\n'
            '    "connections": [{"source_id": "...", "target_id": "...", "label": "...", "protocol": "...", "animated": true, "packet_color": "#..."}]\n'
            "  },\n"
            '  "narration_script": "[Scene 1: ...]\\n...\\n\\n[Scene 2: ...]\\n...\\n\\n[Scene 3: ...]\\n...\\n\\n[Scene 4: ...]\\n...",\n'
            '  "manim_script": "from manim import *\\n\\nclass ComprehensiveTutorialScene(Scene):\\n    def construct(self):\\n        ...",\n'
            '  "scenes_summary": ["File Tree", "Architecture Flowchart", "Core Logic", "Conclusion"]\n'
            "}"
        )

        user_prompt = (
            f"Codebase Repository: {repo_name}\n"
            f"Target Narration Language: {lang_info.name} ({lang_info.native_name}) [Code: {lang_info.code}]\n"
            f"Custom Instructions: {custom_instructions or 'Provide an exhaustive 60-90 second multi-scene technical breakdown'}\n\n"
            f"{graph_json_prompt}"
            f"=== Codebase Pack (Repomix) ===\n{codebase_pack[:60000]}\n"
        )

        response = client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                max_output_tokens=16384,
                temperature=0.2,
            ),
        )

        raw_json = response.text or "{}"
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            # Fallback cleanup in case model wraps output in markdown code fence
            clean = re.sub(r"^```(?:json)?\s*", "", raw_json.strip())
            clean = re.sub(r"\s*```$", "", clean)
            parsed = json.loads(clean)

        arch_raw = parsed.get("architecture", {})
        arch_data = ArchitectureDiagramData.model_validate(arch_raw)
        narration = parsed.get("narration_script", "").strip()
        manim_script = parsed.get("manim_script", "").strip() or None
        scenes_summary = parsed.get("scenes_summary", ["File Tree", "Architecture Flow", "Core Logic", "Conclusion"])

        # Validate syntax of generated Manim script if present
        if manim_script:
            try:
                ast.parse(manim_script)
            except SyntaxError as err:
                logger.warning("Gemini generated Manim script has syntax error (%s). Using fallback generator.", err)
                manim_script = None

        return ScriptSynthesisResult(
            architecture_data=arch_data,
            narration_script=narration,
            repo_name=repo_name,
            model_used=self.model,
            manim_script=manim_script,
            scenes_summary=scenes_summary,
            target_language=lang_info.code,
        )

    # -------------------------------------------------------------------------
    # Intelligent Heuristic Fallback Extractor
    # -------------------------------------------------------------------------

    def _heuristic_synthesis(
        self,
        codebase_pack: str,
        repo_name: str,
        codebase_graph: Optional[Union[CodebaseGraph, Dict[str, Any], str, Path]] = None,
        target_language: Optional[str] = "en",
    ) -> ScriptSynthesisResult:
        """Synthesize architecture, multi-scene narration, and Manim code by parsing real files and components."""
        graph_obj = self._coerce_codebase_graph(codebase_graph)
        repo_display = repo_name.split("/")[-1].replace("-", " ").title() if "/" in repo_name else repo_name.title()
        effective_lang = target_language or "en"
        lang_info = resolve_language_info(effective_lang)

        if graph_obj is not None and graph_obj.nodes:
            # High-fidelity synthesis directly from AST dependency graph
            from app.services.graph_to_manim import GraphToManimMapper

            mapper = GraphToManimMapper(theme="midnight")
            arch_data = mapper.map_to_architecture_data(
                graph_obj,
                title=f"{repo_display} Architecture Walkthrough",
                subtitle="AST-Extracted Component Flow & File Hierarchy",
            )
            narration = self._build_graph_aware_narration(
                repo_name, repo_display, graph_obj, target_language=effective_lang
            )
            manim_code = self._generate_graph_aware_manim_script(repo_display, graph_obj, arch_data)

            return ScriptSynthesisResult(
                architecture_data=arch_data,
                narration_script=narration,
                repo_name=repo_name,
                model_used="heuristic-multi-scene-graph-v2",
                manim_script=manim_code,
                scenes_summary=[
                    "File Tree & Project Structure",
                    "Architecture & Service Topology",
                    "Core Logic & Data Pipelines",
                    "Lifecycle & Production Summary",
                ],
                target_language=lang_info.code,
            )

        # 1. Parse real directory structure and files from Repomix markdown
        extracted_files, dir_structure = self._extract_codebase_structure(codebase_pack)

        # 2. Derive technology stack and real component nodes
        nodes, connections, tech_stack = self._build_realistic_topology(extracted_files, repo_name, codebase_pack)

        arch_data = ArchitectureDiagramData(
            config=SceneConfig(
                title=f"{repo_display} Architecture Walkthrough",
                subtitle="End-to-End Component Flow & File Hierarchy",
                theme="midnight",
                duration_per_flow=3.0,
                intro_duration=2.0,
                outro_duration=3.0,
            ),
            nodes=nodes,
            connections=connections,
        )

        # 3. Build comprehensive 4-scene technical narration script (60-90 seconds duration)
        narration = self._build_multiscene_narration(
            repo_name, repo_display, extracted_files, tech_stack, nodes, target_language=effective_lang
        )

        # 4. Generate multi-scene Manim Community Python script (60-90 seconds duration)
        manim_code = self._generate_multiscene_manim_script(repo_display, extracted_files, nodes, connections)

        return ScriptSynthesisResult(
            architecture_data=arch_data,
            narration_script=narration,
            repo_name=repo_name,
            model_used="heuristic-multi-scene-v2",
            manim_script=manim_code,
            scenes_summary=[
                "File Tree & Project Structure",
                "Architecture & Service Topology",
                "Core Logic & Data Pipelines",
                "Lifecycle & Production Summary",
            ],
            target_language=lang_info.code,
        )

    # -------------------------------------------------------------------------
    # Codebase Parsing & Component Extraction Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_codebase_structure(codebase_pack: str) -> Tuple[List[str], List[str]]:
        """Extract genuine file paths and top-level directory hierarchy from the Repomix pack."""
        files: List[str] = []
        directories: Set[str] = set()

        # Match "## File: <path>" headers generated by Repomix
        file_matches = re.findall(r"^## File:\s*([^\r\n]+)", codebase_pack, re.MULTILINE)
        for fm in file_matches:
            cleaned = fm.strip().replace("\\", "/")
            if cleaned and cleaned not in files:
                files.append(cleaned)
                parts = cleaned.split("/")
                if len(parts) > 1:
                    directories.add(parts[0])

        # If Repomix style wasn't markdown header, inspect directory tree section
        if not files:
            tree_match = re.search(r"Directory Structure[\s\S]*?```([\s\S]*?)```", codebase_pack, re.IGNORECASE)
            if tree_match:
                tree_lines = tree_match.group(1).splitlines()
                for line in tree_lines:
                    cleaned_line = line.strip().strip("│├└─ ")
                    if cleaned_line and ("." in cleaned_line or "/" in cleaned_line):
                        files.append(cleaned_line.replace("\\", "/"))

        # Fallback if no files matched
        if not files:
            files = ["app/main.py", "app/services/core_service.py", "app/models/schema.py", "app/api/routes.py"]
            directories = {"app"}

        return files[:60], sorted(list(directories))

    @staticmethod
    def _build_realistic_topology(
        files: List[str], repo_name: str, codebase_pack: str
    ) -> Tuple[List[NodeModel], List[ConnectionModel], Dict[str, str]]:
        """Inspect actual source files and frameworks to create authentic topology nodes and edges."""
        text_lower = codebase_pack.lower()
        repo_clean = repo_name.split("/")[-1].replace("-", " ").title() if "/" in repo_name else repo_name.title()

        nodes: List[NodeModel] = []
        connections: List[ConnectionModel] = []
        tech_stack: Dict[str, str] = {}

        # 1. Client / Frontend Layer
        has_frontend = any(
            any(f.startswith(p) for p in ["frontend", "src/client", "web", "ui", "pages", "app/client"])
            or f.endswith((".tsx", ".jsx", ".vue", ".svelte", ".html"))
            for f in files
        ) or "next" in text_lower or "react" in text_lower
        fe_tech = "Next.js & React" if "next" in text_lower else ("React UI" if "react" in text_lower else "Web Client")
        tech_stack["Frontend"] = fe_tech

        fe_details = [f for f in files if any(f.endswith(ext) for ext in [".tsx", ".jsx", ".html"])]
        client_node = NodeModel(
            id="client_layer",
            label="Client Web Application",
            kind=NodeType.FRONTEND,
            tech=fe_tech,
            layer=0,
            details=fe_details[:2] if fe_details else ["User Interface", "Interactive State"],
        )
        nodes.append(client_node)

        # 2. Gateway / Router Layer
        gateway_tech = "FastAPI Router" if "fastapi" in text_lower else "API Gateway"
        tech_stack["Gateway"] = gateway_tech
        api_files = [f for f in files if "api" in f or "route" in f or "endpoint" in f or "controller" in f]
        gateway_node = NodeModel(
            id="gateway_layer",
            label="API Gateway & Routes",
            kind=NodeType.GATEWAY,
            tech=gateway_tech,
            layer=1,
            details=api_files[:2] if api_files else ["HTTP Route Dispatch", "Auth & Rate Limiting"],
        )
        nodes.append(gateway_node)
        connections.append(
            ConnectionModel(
                source_id="client_layer",
                target_id="gateway_layer",
                label="HTTPS / API Request",
                protocol="REST/JSON",
                animated=True,
                packet_color="#38BDF8",
            )
        )

        # 3. Core Backend / Services Layer
        be_tech = "Python Engine"
        if "fastapi" in text_lower:
            be_tech = "FastAPI Service"
        elif "django" in text_lower:
            be_tech = "Django Service"
        elif "flask" in text_lower:
            be_tech = "Flask Service"
        elif "express" in text_lower or "node" in text_lower:
            be_tech = "Node.js Express"
        elif "go" in text_lower or any(f.endswith(".go") for f in files):
            be_tech = "Go Microservice"
        tech_stack["Backend"] = be_tech

        service_files = [f for f in files if "service" in f or "core" in f or "worker" in f or "engine" in f]
        backend_node = NodeModel(
            id="backend_core",
            label=f"{repo_clean} Core Engine",
            kind=NodeType.BACKEND,
            tech=be_tech,
            layer=2,
            details=service_files[:2] if service_files else ["Business Logic", "Data Transformation"],
        )
        nodes.append(backend_node)
        connections.append(
            ConnectionModel(
                source_id="gateway_layer",
                target_id="backend_core",
                label="Dispatch Pipeline",
                protocol="Internal / gRPC",
                animated=True,
                packet_color="#4ADE80",
            )
        )

        # 4. Message Queue / Cache (if detected)
        has_queue = any(k in text_lower for k in ["redis", "celery", "kafka", "rabbitmq", "queue", "cache"])
        if has_queue or any("worker" in f or "task" in f for f in files):
            queue_tech = "Redis & Celery" if ("celery" in text_lower or "redis" in text_lower) else "Message Broker"
            tech_stack["Queue"] = queue_tech
            queue_node = NodeModel(
                id="queue_state",
                label="Task Queue & Cache",
                kind=NodeType.QUEUE,
                tech=queue_tech,
                layer=3,
                details=["Asynchronous Jobs", "In-Memory State"],
            )
            nodes.append(queue_node)
            connections.append(
                ConnectionModel(
                    source_id="backend_core",
                    target_id="queue_state",
                    label="Enqueue Task",
                    protocol="RESP/AMQP",
                    animated=True,
                    packet_color="#F59E0B",
                )
            )

        # 5. Database & Storage Layer
        db_tech = "PostgreSQL" if "postgres" in text_lower else ("MongoDB" if "mongo" in text_lower else "Database Store")
        tech_stack["Database"] = db_tech
        db_files = [f for f in files if "model" in f or "db" in f or "schema" in f or "migration" in f]
        db_node = NodeModel(
            id="database_layer",
            label="Relational Persistence",
            kind=NodeType.DATABASE,
            tech=db_tech,
            layer=4 if has_queue else 3,
            details=db_files[:2] if db_files else ["Relational Entities", "ACID Persistence"],
        )
        nodes.append(db_node)
        connections.append(
            ConnectionModel(
                source_id="backend_core",
                target_id="database_layer",
                label="SQL Persistence",
                protocol="Async SQL",
                animated=True,
                packet_color="#10B981",
            )
        )

        return nodes, connections, tech_stack

    @classmethod
    def _build_multiscene_narration(
        cls,
        repo_name: str,
        repo_display: str,
        files: List[str],
        tech_stack: Dict[str, str],
        nodes: List[NodeModel],
        target_language: str = "en",
    ) -> str:
        """Construct an exhaustive 4-scene technical narration script calibrated for 60-90 seconds."""
        sample_files = ", ".join(f.split("/")[-1] for f in files[:4])
        core_techs = ", ".join(f"{k} with {v}" for k, v in list(tech_stack.items())[:3])
        lang = (target_language or "en").strip().lower()

        if lang == "gu":
            scene_1 = (
                f"[Scene 1: રીપોઝીટરી માહિતી અને ફાઈલ રચના]\n"
                f"{repo_name} ના આર્કિટેક્ચરલ વિશ્લેષણમાં તમારું સ્વાગત છે. "
                f"કોડબેઝની રચના જોતાં, પ્રોજેક્ટ પોતાના ઘટકોને સ્પષ્ટ અને મોડ્યુલર સ્તરોમાં ગોઠવે છે. "
                f"મુખ્ય સોર્સ ફાઈલો જેવી કે {sample_files} આ રીપોઝીટરીનો મજબૂત પાયો રચે છે. "
                f"આ સુવ્યવસ્થિત લેઆઉટ યુઝર ઈન્ટરફેસ, એપીઆઈ ડેફિનેશન અને બેકએન્ડ સર્વિસિસને વ્યવસ્થિત રીતે વિભાજિત કરે છે."
            )
            scene_2 = (
                f"[Scene 2: સિસ્ટમ આર્કિટેક્ચર અને ડેટા પ્રવાહ]\n"
                f"એન્ડ-ટુ-એન્ડ ડેટા પ્રવાહ તપાસતાં, ક્લાયન્ટ વિનંતીઓ નેટવર્ક પરિમિતિ દ્વારા પ્રવેશી એપીઆઈ ગેટવે સુધી પહોંચે છે. "
                f"ગેટવે વિનંતીઓની ચકાસણી, પ્રમાણીકરણ અને રાઉટિંગ સંભાળીને પેલોડ્સને {repo_display} બેકએન્ડ એન્જિન તરફ મોકલે છે. "
                f"{core_techs} આસપાસ બનેલું આ માળખું આંતરિક સીમાઓમાં સુરક્ષિત અને ઝડપી ડેટા ટ્રાન્સફર સુનિશ્ચિત કરે છે."
            )
            scene_3 = (
                f"[Scene 3: મુખ્ય લોજિક અને પાઇપલાઇન વિશ્લેષણ]\n"
                f"સિસ્ટમની અંદર, કોર સર્વિસ લેયર બિઝનેસ લોજિક અને સ્ટેટ સિંક્રોનાઇઝેશનનું સંચાલન કરે છે. "
                f"વધુ પ્રોસેસિંગ માંગતા કાર્યોને બેકગ્રાઉન્ડ કતારોમાં અસિંક્રોનસ રીતે મોકલવામાં આવે છે, જેથી મુખ્ય સર્વર ક્યારેય બ્લોક થતું નથી. "
                f"એન્ટિટી મોડેલ્સ મેમરીમાં ચકાસાય છે અને ડેટાબેઝમાં સાચવવામાં આવે છે, જે સંપૂર્ણ ડેટા અખંડિતતા જાળવે છે."
            )
            scene_4 = (
                f"[Scene 4: સારાંશ અને નિષ્કર્ષ]\n"
                f"સારાંશમાં, {repo_name} ઉચ્ચ સ્કેલેબિલિટી, ઉપલબ્ધતા અને સરળ જાળવણી માટે એન્જિનિયર કરાયેલ એન્ટરપ્રાઇઝ-ગ્રેડ આર્કિટેક્ચર પ્રદાન કરે છે. "
                f"પ્રોસેસિંગ પાઇપલાઇન અને ડેટા સ્ટોરેજને અલગ રાખીને, સિસ્ટમ શ્રેષ્ઠ પ્રદર્શન પ્રાપ્ત કરે છે. "
                f"આ આર્કિટેક્ચરલ વિડીયો જોવા બદલ તમારો ખૂબ ખૂબ આભાર."
            )
        elif lang == "hi":
            scene_1 = (
                f"[Scene 1: रिपॉजिटरी अवलोकन और फ़ाइल संरचना]\n"
                f"{repo_name} के आर्किटेक्चरल विश्लेषण में आपका स्वागत है। "
                f"कोडबेस संरचना को देखने पर, प्रोजेक्ट अपने सभी घटकों को स्पष्ट और मॉड्यूलर परतों में व्यवस्थित करता है। "
                f"{sample_files} जैसी प्रमुख स्रोत फ़ाइलें इस रिपॉजिटरी की ठोस नींव तैयार करती हैं। "
                f"यह व्यवस्थित लेआउट इंटरफ़ेस, एपीआई परिभाषा और बैकएंड सेवाओं को सुव्यवस्थित डोमेन में विभाजित करता है।"
            )
            scene_2 = (
                f"[Scene 2: सिस्टम आर्किटेक्चर और डेटा प्रवाह]\n"
                f"एंड-टू-एंड डेटा प्रवाह का निरीक्षण करते हुए, क्लाइंट अनुरोध नेटवर्क परिधि से होते हुए एपीआई गेटवे तक पहुँचते हैं। "
                f"गेटवे अनुरोध सत्यापन, प्रमाणीकरण और रूटिंग का प्रबंधन करके डेटा पेलोड को {repo_display} बैकएंड इंजन को सौंपता है। "
                f"{core_techs} पर आधारित यह संरचना आंतरिक सीमाओं के पार सुरक्षित और तेज़ डेटा संचार सुनिश्चित करती है।"
            )
            scene_3 = (
                f"[Scene 3: मुख्य लॉजिक और निष्पादन प्रक्रिया]\n"
                f"सिस्टम के भीतर, कोर सर्विस लेयर बिज़नेस लॉजिक और स्टेट सिंक्रोनाइज़ेशन का संचालन करती है। "
                f"गहन गणना वाले कार्यों को एसिंक्रोनस रूप से बैकग्राउंड कतारों में भेजा जाता है, जिससे मुख्य सर्वर बिना किसी रुकावट के अत्यधिक उत्तरदायी बना रहता है। "
                f"डेटा संस्थाओं को सीधे डेटाबेस में मैप किया जाता है, जिससे डेटा अखंडता की पूर्ण गारंटी मिलती है।"
            )
            scene_4 = (
                f"[Scene 4: सारांश और निष्कर्ष]\n"
                f"संक्षेप में, {repo_name} उच्च मापनीयता, उपलब्धता और आसान रखरखाव के लिए डिज़ाइन किया गया एक एंटरप्राइज-ग्रेड आर्किटेक्चर प्रस्तुत करता है। "
                f"डेटा अंतर्ग्रहण, प्रोसेसिंग पाइपलाइन और स्टोरेज को अलग करके, यह प्रणाली भारी वर्कलोड में भी उत्कृष्ट प्रदर्शन करती है। "
                f"इस विस्तृत आर्किटेक्चरल ट्यूटोरियल को देखने के लिए आपका धन्यवाद।"
            )
        elif lang == "mr":
            scene_1 = (
                f"[Scene 1: रिपॉझिटरी विहंगावलोकन आणि फाइल रचना]\n"
                f"{repo_name} च्या आर्किटेक्चरल विश्लेषणामध्ये आपले मनःपूर्वक स्वागत आहे. "
                f"कोडबेस रचनेचा विचार करता, हा प्रकल्प सर्व घटकांना स्पष्ट आणि मॉड्यूलर स्तरांमध्ये विभागून ठेवतो. "
                f"{sample_files} सारख्या महत्त्वाच्या फाइल्स या रिपॉझिटरीचा मजबूत पाया तयार करतात. "
                f"ही रचना युझर इंटरफेस, एपीआय व्याख्या आणि सेवांची योग्य व्यवस्था सुनिश्चित करते."
            )
            scene_2 = (
                f"[Scene 2: सिस्टम आर्किटेक्चर आणि डेटा प्रवाह]\n"
                f"डेटा प्रवाहाचा मागोवा घेताना, वापरकर्त्याच्या विनंत्या एपीआय गेटवेद्वारे प्रणालीत प्रवेश करतात. "
                f"गेटवे विनंत्यांची पडताळणी आणि प्रमाणीकरण करून डेटा पेलोड्स {repo_display} बॅकएंड इंजिनकडे पाठवतो. "
                f"{core_techs} च्या आधारावर बनवलेली ही प्रणाली अंतर्गत सुरक्षित डेटा देवाणघेवाण सुनिश्चित करते."
            )
            scene_3 = (
                f"[Scene 3: मुख्य लॉजिक आणि डेटा पाइपलाइन]\n"
                f"प्रणालीच्या आत, मुख्य सेवा स्तर बिझनेस लॉजिक आणि स्थिती व्यवस्थापन कार्यक्षमतेने हाताळते. "
                f"वेळ खाणारी कामे बॅकग्राउंड टास्क रांगेत पाठवली जातात, ज्यामुळे मुख्य सर्व्हर नेहमी वेगवान राहतो. "
                f"डेटाबेस मॉडेल्स थेट सुरक्षित स्टोअरेजशी जोडलेले असून संपूर्ण डेटा सुरक्षितता राखली जाते."
            )
            scene_4 = (
                f"[Scene 4: सारांश आणि निष्कर्ष]\n"
                f"थोडक्यात सांगायचे तर, {repo_name} स्केलेबिलिटी आणि उच्च कार्यक्षमतेसाठी विकसित केलेले उत्कृष्ट आर्किटेक्चर प्रदान करते. "
                f"प्रक्रिया आणि डेटा स्टोअरेजचे स्वतंत्र नियोजन प्रणालीला अखंड गती प्रदान करते. "
                f"हा आर्किटेक्चरल व्हिडिओ पाहिल्याबद्दल धन्यवाद."
            )
        elif lang == "bn":
            scene_1 = (
                f"[Scene 1: রিপোজিটরি ওভারভিউ এবং ফাইল কাঠামো]\n"
                f"{repo_name} এর স্থাপত্য বিশ্লেষণে আপনাকে স্বাগতম। "
                f"কোডবেসের সংগঠন বিবেচনা করলে, প্রকল্পটি এর উপাদানগুলিকে পরিষ্কার মডুলার স্তরে বিন্যস্ত করেছে। "
                f"{sample_files} এর মতো গুরুত্বপূর্ণ ফাইলগুলি এই রিপোজিটরির মূল ভিত্তি স্থাপন করে। "
                f"এই সুসংগঠিত বিন্যাস ইন্টারফেস, এপিআই সংজ্ঞা এবং ব্যাকএন্ড সার্ভিসেসকে আলাদা ডোমেনে রাখে।"
            )
            scene_2 = (
                f"[Scene 2: সিস্টেম আর্কিটেকচার এবং ডেটা ফ্লো]\n"
                f"ডেটা প্রবাহ বিশ্লেষণ করলে দেখা যায় ক্লায়েন্টের অনুরোধগুলি এপিআই গেটওয়ের মাধ্যমে সিস্টেমে প্রবেশ করে। "
                f"গেটওয়ে যাচাইকরণ এবং রাউটিং সম্পন্ন করে পেলোডগুলি {repo_display} ব্যাকএন্ড ইঞ্জিনে পাঠায়। "
                f"{core_techs} এর উপর নির্মিত এই আর্কিটেকচার অভ্যন্তরীণ স্তরে দ্রুত এবং নিরাপদ ডেটা স্থানান্তর নিশ্চিত করে।"
            )
            scene_3 = (
                f"[Scene 3: কোর লজিক এবং ডেটা পাইপলাইন]\n"
                f"সিস্টেমের অভ্যন্তরে কোর সার্ভিস লেয়ার ব্যবসায়িক যুক্তি এবং স্টেট সিঙ্ক্রোনাইজেশন পরিচালনা করে। "
                f"ভারী কাজগুলি ব্যাকগ্রাউন্ড কিউতে পাঠানো হয় যাতে মূল সার্ভার নিরবচ্ছিন্নভাবে সাড়া দিতে পারে। "
                f"ডেটা মডেলগুলি ডাটাবেসে সঠিকভাবে সংরক্ষিত হয়, যা সম্পূর্ণ নির্ভরযোগ্যতা নিশ্চিত করে।"
            )
            scene_4 = (
                f"[Scene 4: সারসংক্ষেপ এবং সমাপ্তি]\n"
                f"সংক্ষেপে, {repo_name} একটি অত্যন্ত স্কেলযোগ্য এবং নির্ভরযোগ্য সফটওয়্যার আর্কিটেকচার প্রদান করে। "
                f"প্রসেসিং পাইপলাইন এবং স্টোরেজ আলাদা রাখার মাধ্যমে সিস্টেমটি সর্বোত্তম গতি ও কার্যকারিতা অর্জন করে। "
                f"এই স্থাপত্য বিশ্লেষণ ভিডিওটি দেখার জন্য আপনাকে ধন্যবাদ।"
            )
        elif lang == "ta":
            scene_1 = (
                f"[Scene 1: களஞ்சிய மேலோட்டம் மற்றும் கோப்பு அமைப்பு]\n"
                f"{repo_name} இன் கணினி கட்டமைப்பு ஆய்வுக்கு உங்களை அன்புடன் வரவேற்கிறோம். "
                f"குறியீட்டுத் தொகுப்பை நோக்கும்போது, திட்டம் அதன் அனைத்து கூறுகளையும் தெளிவான மட்டு அடுக்குகளில் ஒழுங்கமைக்கிறது. "
                f"{sample_files} போன்ற முதன்மை கோப்புகள் இந்த களஞ்சியத்தின் உறுதியான அடித்தளமாக அமைகின்றன. "
                f"இந்த ஒழுங்கமைக்கப்பட்ட தளவமைப்பு இடைமுகம், ஏபிஐ வரையறைகள் மற்றும் சேவைகளை நேர்த்தியாகப் பிரிக்கிறது."
            )
            scene_2 = (
                f"[Scene 2: கணினி கட்டமைப்பு மற்றும் தரவு ஓட்டம்]\n"
                f"முழுமையான தரவு ஓட்டத்தைக் கண்காணிக்கும் போது, வாடிக்கையாளர் கோரிக்கைகள் ஏபிஐ கேட்வே வழியாக நுழைகின்றன. "
                f"கேட்வே சரிபார்ப்பு மற்றும் வழிகாட்டுதலை நிர்வகித்து, தகவல்களை {repo_display} பின்தள இயந்திரத்திற்கு அனுப்புகிறது. "
                f"{core_techs} கொண்டு கட்டமைக்கப்பட்ட இந்த அமைப்பு உள் எல்லைகளில் பாதுகாப்பான தகவல் பரிமாற்றத்தை உறுதி செய்கிறது."
            )
            scene_3 = (
                f"[Scene 3: முக்கிய தர்க்கம் மற்றும் செயலாக்க வழிமுறை]\n"
                f"கணினியின் உள்ளே, முதன்மை சேவை அடுக்கு வணிக தர்க்கம் மற்றும் நிலை ஒத்திசைவை நிர்வகிக்கிறது. "
                f"அதிக நேரமெடுக்கும் பணிகள் பின்னணி வரிசைகளுக்கு மாற்றப்பட்டு, முதன்மை தளம் தடையின்றி இயங்க வழிவகுக்கிறது. "
                f"தரவு மாதிரிகள் நேரடியாக தரவுத்தளத்தில் இணைக்கப்பட்டு நம்பகத்தன்மை உறுதி செய்யப்படுகிறது."
            )
            scene_4 = (
                f"[Scene 4: சுருக்கம் மற்றும் முடிவுரை]\n"
                f"சுருக்கமாக, {repo_name} அதிக அளவிடக்கூடிய மற்றும் நம்பகமான மென்பொருள் கட்டமைப்பை வழங்குகிறது. "
                f"செயலாக்க குழாய் மற்றும் சேமிப்பகத்தைப் பிரிப்பதன் மூலம், கணினி சிறந்த வேகத்தை அடைகிறது. "
                f"இந்த வீடியோவைப் பார்த்ததற்கு எங்கள் மனமார்ந்த நன்றி."
            )
        elif lang == "te":
            scene_1 = (
                f"[Scene 1: రిపోజిటరీ అవలోకనం మరియు ఫైల్ నిర్మాణం]\n"
                f"{repo_name} ఆర్కిటెక్చరల్ విశ్లేషణకు స్వాగతం. "
                f"కోడ్‌బేస్ నిర్మాణాన్ని పరిశీలిస్తే, ప్రాజెక్ట్ తన భాగాలను స్పష్టమైన మాడ్యులర్ లేయర్‌లుగా నిర్వహిస్తుంది. "
                f"{sample_files} వంటి ముఖ్యమైన సోర్స్ ఫైల్స్ ఈ రిపోజిటరీకి దృఢమైన పునాదిని వేస్తాయి. "
                f"ఈ నిర్మాణాత్మక లేఅవుట్ ఇంటర్‌ఫేస్, ఏపీఐ నిర్వచనాలు మరియు బ్యాకెండ్ సేవలను విభజిస్తుంది."
            )
            scene_2 = (
                f"[Scene 2: సిస్టమ్ ఆర్కిటెక్చర్ మరియు డేటా ప్రవాహం]\n"
                f"ఎండ్-టు-ఎండ్ డేటా ప్రవాహాన్ని గమనిస్తే, క్లయింట్ అభ్యర్థనలు ఏపీఐ గేట్‌వే ద్వారా సిస్టమ్‌లోకి ప్రవేశిస్తాయి. "
                f"గేట్‌వే ధృవీకరణ మరియు రూటింగ్‌ను నిర్వహించి, డేటాను {repo_display} బ్యాకెండ్ ఇంజిన్‌కు బదిలీ చేస్తుంది. "
                f"{core_techs} ఆధారంగా నిర్మించబడిన ఈ వ్యవస్థ అంతర్గతంగా సురక్షితమైన డేటా ప్రవాహాన్ని నిర్ధారిస్తుంది."
            )
            scene_3 = (
                f"[Scene 3: కోర్ లాజిక్ మరియు డేటా పైప్‌లైన్]\n"
                f"వ్యవస్థ లోపల, కోర్ సర్వీస్ లేయర్ బిజినెస్ లాజిక్ మరియు స్థితి నిర్వహణను పర్యవేక్షిస్తుంది. "
                f"ఎక్కువ సమయం తీసుకునే కార్యకలాపాలు అసమకాలికంగా బ్యాక్‌గ్రౌండ్ క్యూలకు పంపబడతాయి. "
                f"డేటా నమూనాలు డేటాబేస్‌కు సరిగ్గా మ్యాప్ చేయబడి సంపూర్ణ స్థిరత్వాన్ని కాపాడతాయి."
            )
            scene_4 = (
                f"[Scene 4: సారాంశం మరియు ముగింపు]\n"
                f"సారాంశంగా, {repo_name} అధిక స్కేలబిలిటీ మరియు స్థిరత్వం కోసం రూపొందించబడిన ఆధునిక ఆర్కిటెక్చర్‌ను అందిస్తుంది. "
                f"ప్రాసెసింగ్ మరియు స్టోరేజ్‌లను వేరు చేయడం ద్వారా సిస్టమ్ అత్యుత్తమ పనితీరును ప్రదర్శిస్తుంది. "
                f"ఈ ఆర్కిటెక్చరల్ ట్యుటోరియల్ చూసినందుకు ధన్యవాదాలు."
            )
        elif lang == "es":
            scene_1 = (
                f"[Scene 1: Descripción del Repositorio y Estructura de Directorios]\n"
                f"Bienvenidos al análisis arquitectónico exhaustivo de {repo_name}. "
                f"Al examinar la jerarquía del código fuente, el proyecto organiza sus componentes en capas modulares limpias. "
                f"Archivos clave como {sample_files} constituyen el núcleo de este repositorio. "
                f"Esta disposición desacopla la interfaz de usuario, las definiciones de API y la lógica de negocio en dominios mantenibles."
            )
            scene_2 = (
                f"[Scene 2: Arquitectura del Sistema y Flujo de Datos]\n"
                f"Siguiendo el flujo integral de datos, las solicitudes de los clientes ingresan mediante el gateway de API. "
                f"El gateway gestiona la validación, autenticación y enrutamiento antes de despachar las cargas al motor backend de {repo_display}. "
                f"Construido alrededor de {core_techs}, los datos fluyen fluidamente a través de límites internos con contratos fuertemente tipados."
            )
            scene_3 = (
                f"[Scene 3: Implementación del Núcleo y Lógica Interna]\n"
                f"Bajo el capó, la capa de servicios central coordina la ejecución de las reglas de negocio y el estado del sistema. "
                f"Las tareas intensivas se despachan de forma asíncrona hacia colas en segundo plano, manteniendo el hilo HTTP principal no bloqueante. "
                f"Los modelos de entidades se validan y se persisten en almacenamiento transaccional, garantizando consistencia ACID."
            )
            scene_4 = (
                f"[Scene 4: Resumen del Ciclo de Vida y Conclusión]\n"
                f"En conclusión, {repo_name} ofrece una arquitectura de grado empresarial diseñada para alta disponibilidad y escalabilidad. "
                f"Al desacoplar la ingesta, los canales de procesamiento y el almacenamiento persistente, el sistema optimiza su rendimiento bajo carga. "
                f"Gracias por acompañarnos en este recorrido arquitectónico."
            )
        elif lang == "fr":
            scene_1 = (
                f"[Scene 1: Vue d'Ensemble du Référentiel et Structure des Fichiers]\n"
                f"Bienvenue dans l'exploration architecturale approfondie de {repo_name}. "
                f"En examinant la hiérarchie du code, le projet organise méthodiquement ses composants en couches modulaires distinctes. "
                f"Des fichiers sources essentiels tels que {sample_files} constituent les fondations solides de ce projet. "
                f"Cette structure sépare nettement l'interface, les définitions d'API et l'orchestration des services métier."
            )
            scene_2 = (
                f"[Scene 2: Architecture Système et Flux de Données]\n"
                f"En traçant le flux de données de bout en bout, les requêtes clientes franchissent la passerelle API centrale. "
                f"La passerelle assure la validation, l'authentification et le routage structuré vers le moteur backend {repo_display}. "
                f"Articulée autour de {core_techs}, la communication interne s'effectue avec des contrats typés et une grande résilience."
            )
            scene_3 = (
                f"[Scene 3: Implémentation du Cœur et Logique Métier]\n"
                f"Au cœur du système, la couche de services pilote les règles métier et la synchronisation des états applicatifs. "
                f"Les opérations volumineuses sont déléguées de manière asynchrone à des files d'attente dédiées, préservant la réactivité HTTP. "
                f"Les entités de données sont validées et enregistrées de façon transactionnelle dans le stockage persistant."
            )
            scene_4 = (
                f"[Scene 4: Synthèse du Cycle de Vie et Conclusion]\n"
                f"En résumé, {repo_name} fournit une architecture robuste de qualité industrielle, pensée pour la scalabilité et la maintenabilité. "
                f"Le découplage entre l'ingestion, le traitement et le stockage assure des performances optimales en production. "
                f"Merci d'avoir suivi cette présentation architecturale."
            )
        elif lang == "de":
            scene_1 = (
                f"[Scene 1: Repository-Übersicht und Dateistruktur]\n"
                f"Willkommen zur architektonischen Tiefenanalyse von {repo_name}. "
                f"Die Codebasis strukturiert ihre Komponenten in klar abgegrenzte modulare Architekturebenen. "
                f"Zentrale Quellcodedateien wie {sample_files} bilden das fundamentale Rückgrat des Projekts. "
                f"Dieses modulare Layout trennt Schnittstellen, API-Endpunkte und Service-Orchestrierung sauber voneinander."
            )
            scene_2 = (
                f"[Scene 2: Systemarchitektur und Datenfluss]\n"
                f"Beim Verfolgen des Datenflusses treffen Client-Anfragen über das API-Gateway im System ein. "
                f"Das Gateway übernimmt Validierung, Authentifizierung und Routing zur Backend-Engine von {repo_display}. "
                f"Basierend auf {core_techs} fließen die Daten mit streng typisierten Schnittstellen und resilienter Fehlerbehandlung."
            )
            scene_3 = (
                f"[Scene 3: Kernlogik und Ausführungspipeline]\n"
                f"Unter der Haube koordiniert die Kernservice-Schicht die Geschäftslogik und Zustandssynchronisation. "
                f"Rechenintensive Operationen werden asynchron an Hintergrund-Queues übergeben, wodurch der HTTP-Thread stets reaktionsschnell bleibt. "
                f"Entitätsmodelle werden im Speicher geprüft und ACID-konform in der persistenten Datenbank gespeichert."
            )
            scene_4 = (
                f"[Scene 4: Zusammenfassung und Fazit]\n"
                f"Zusammenfassend bietet {repo_name} eine hochgradig skalierbare und wartbare Enterprise-Architektur. "
                f"Durch die Entkopplung von Ingestion, Verarbeitungs-Pipelines und persistentem Speicher erzielt das System maximale Ausfallsicherheit. "
                f"Vielen Dank für Ihre Aufmerksamkeit bei dieser Architekturübersicht."
            )
        elif lang == "ja":
            scene_1 = (
                f"[Scene 1: リポジトリの概要とディレクトリ構造]\n"
                f"{repo_name} のアーキテクチャ詳細解説へようこそ。 "
                f"コードベース全体の構造を見ると、プロジェクトはコンポーネントを明確なモジュール層に整理しています。 "
                f"{sample_files} などの主要なソースファイルがリポジトリの強固な基盤を形成しています。 "
                f"この洗練されたレイアウトにより、UI、API定義、バックエンドサービスが明確に分離されています。"
            )
            scene_2 = (
                f"[Scene 2: システムアーキテクチャとデータフロー]\n"
                f"エンドツーエンドのデータフローを追跡すると、クライアントからのリクエストはAPIゲートウェイを経由して入ります。 "
                f"ゲートウェイで検証とルーティングが行われた後、ペイロードは {repo_display} バックエンドエンジンへ安全に転送されます。 "
                f"{core_techs} を核として構築され、厳密な型定義と高い耐障害性のもとでデータが流れます。"
            )
            scene_3 = (
                f"[Scene 3: コアロジックとパイプライン実装]\n"
                f"システムの内部では、コアサービス層がビジネスロジックと状態同期を統括します。 "
                f"負荷の高い処理はバックグラウンドキューに非同期ディスパッチされ、HTTPサーバーのノンブロッキングな即応性を維持します。 "
                f"エンティティはメモリ上で検証され永続ストレージにACID準拠で安全に保存されます。"
            )
            scene_4 = (
                f"[Scene 4: ライフサイクルのまとめと結論]\n"
                f"まとめとして、{repo_name} は高い拡張性と堅牢性を備えたエンタープライズグレードのアーキテクチャを提供しています。 "
                f"取り込み、パイプライン処理、永続ストレージが疎結合化されているため、高負荷下でも優れたスループットを発揮します。 "
                f"アーキテクチャ解説をご視聴いただきありがとうございました。"
            )
        elif lang == "zh":
            scene_1 = (
                f"[Scene 1: 仓库概览与目录架构]\n"
                f"欢迎来到 {repo_name} 的系统架构深度解析。 "
                f"纵观代码库的层次结构，该项目将组件清晰地划分到各个模块化分层中。 "
                f"关键源文件如 {sample_files} 构成了本仓库的核心基石。 "
                f"这种精巧的设计将用户界面、API定义与服务编排解耦为易于维护的独立领域。"
            )
            scene_2 = (
                f"[Scene 2: 系统架构与数据流转]\n"
                f"追踪端到端的数据流转，客户端请求首先到达 API 网关。 "
                f"网关在将负载分发至 {repo_display} 后端核心引擎之前，完成严格的请求校验与路由分发。 "
                f"依托于 {core_techs}，数据在内部边界之间以强类型契约与弹性容错机制平稳流动。"
            )
            scene_3 = (
                f"[Scene 3: 核心业务逻辑与数据管道]\n"
                f"深入底层架构，核心服务层负责业务逻辑的执行与系统状态同步。 "
                f"耗时操作被异步派发至后台任务队列，确保主 HTTP 线程非阻塞并具备高响应性。 "
                f"实体模型在内存中校验后持久化存储，保障了 ACID 事务与可靠的生命周期。"
            )
            scene_4 = (
                f"[Scene 4: 生命周期总结与结论]\n"
                f"总而言之，{repo_name} 呈现了具备高度可扩展性与可维护性的企业级软件架构。 "
                f"通过解耦数据接入、计算管道与持久化存储，系统在生产高负载下依然能保持卓越吞吐量。 "
                f"感谢您观看本次系统架构剖析。"
            )
        elif lang == "ar":
            scene_1 = (
                f"[Scene 1: نظرة عامة على المستودع وهيكل الدليل]\n"
                f"مرحبًا بكم في التحليل المعماري الشامل لمشروع {repo_name}. "
                f"بالنظر إلى هيكلية الكود البرمجي، ينظم المشروع مكوناته في طبقات معيارية نظيفة. "
                f"تشكل الملفات المصدرية الرئيسية مثل {sample_files} الأساس المتين لهذا المستودع. "
                f"يفصل هذا التخطيط المدروس واجهة المستخدم وتعريفات واجهة برمجة التطبيقات وإدارة الخدمات في نطاقات قابلة للصيانة بسهولة."
            )
            scene_2 = (
                f"[Scene 2: بنية النظام وتدفق البيانات]\n"
                f"بتتبع تدفق البيانات، تدخل طلبات المستخدم عبر بوابة واجهة برمجة التطبيقات. "
                f"تتولى البوابة التحقق من صحة الطلبات والتوجيه المنظم قبل تمرير البيانات إلى محرك الواجهة الخلفية {repo_display}. "
                f"مبنيًا حول {core_techs}، تتدفق البيانات بسلاسة عبر الحدود الداخلية مع عقود قوية ومقاومة للأخطاء."
            )
            scene_3 = (
                f"[Scene 3: التنفيذ الأساسي ومنطق الأعمال]\n"
                f"في جوهر النظام، تدير طبقة الخدمات المركزية تنفيذ منطق الأعمال ومزامنة الحالة. "
                f"يتم إرسال العمليات الكثيفة بشكل غير متزامن إلى قوائم الانتظار الخلفية، مما يحافظ على استجابة الخادم الفائقة. "
                f"يتم التحقق من صحة نماذج البيانات وحفظها بأمان لضمان سلامة العمليات واستقرارها."
            )
            scene_4 = (
                f"[Scene 4: ملخص دورة الحياة والخاتمة]\n"
                f"باختصار، يقدم {repo_name} بنية برمجية متطورة مصممة لقابلية التوسع والاعتمادية العالية. "
                f"من خلال فصل تدفق البيانات ومعالجتها وتخزينها، يحقق النظام أداءً فائقًا تحت الأحمال الإنتاجية. "
                f"شكرًا لمتابعتكم لهذا الشرح المعماري."
            )
        else:
            # Default to pristine English
            scene_1 = (
                f"[Scene 1: Repository Overview & Directory Structure]\n"
                f"Welcome to the architectural deep dive of {repo_name}. "
                f"Looking across the codebase hierarchy, the project organizes its components into clear modular layers. "
                f"Key source files such as {sample_files} form the foundation of the repository. "
                f"This structured layout separates interface concerns, API definitions, and service orchestration into maintainable domains."
            )
            scene_2 = (
                f"[Scene 2: System Architecture & Data Flow]\n"
                f"Tracing the end-to-end data flow, client requests enter through the network perimeter and hit the API gateway. "
                f"The gateway handles request validation, authentication, and structured routing before dispatching payloads to the {repo_display} backend engine. "
                f"Built around {core_techs}, data streams smoothly across internal boundaries with strict type contracts and resilient error handling."
            )
            scene_3 = (
                f"[Scene 3: Core Implementation & Logic Deep Dive]\n"
                f"Under the hood, the core service layer manages business logic execution and state synchronization. "
                f"Intensive operations are dispatched asynchronously to background queues, keeping the main HTTP thread non-blocking and highly responsive. "
                f"Entity models are validated in memory and committed to persistent storage, guaranteeing ACID compliance and predictable lifecycle management."
            )
            scene_4 = (
                f"[Scene 4: Lifecycle Summary & Conclusion]\n"
                f"In summary, {repo_name} delivers an enterprise-grade architecture engineered for scalability, high availability, and maintainability. "
                f"By decoupling ingestion, processing pipelines, and persistent storage, the system achieves optimal throughput under load. "
                f"Thank you for watching this architectural walkthrough."
            )

        return f"{scene_1}\n\n{scene_2}\n\n{scene_3}\n\n{scene_4}"

    @classmethod
    def _build_graph_aware_narration(
        cls,
        repo_name: str,
        repo_display: str,
        graph: CodebaseGraph,
        target_language: str = "en",
    ) -> str:
        """Construct an exhaustive 4-scene technical narration script grounded in AST-extracted components."""
        db_nodes = [n for n in graph.nodes if n.kind == NodeType.DATABASE]
        route_nodes = [n for n in graph.nodes if n.kind == NodeType.GATEWAY]
        fe_nodes = [n for n in graph.nodes if n.kind in (NodeType.FRONTEND, NodeType.CLIENT)]
        core_nodes = [n for n in graph.nodes if n.kind == NodeType.BACKEND]
        queue_nodes = [n for n in graph.nodes if n.kind == NodeType.QUEUE]

        sample_files = ", ".join(Path(n.path).name for n in graph.nodes[:5])

        # Exact database models
        db_models = [c for n in db_nodes for c in n.classes]
        db_desc = f"database models such as {', '.join(db_models[:3])}" if db_models else "relational database persistence"

        # Exact routes / gateway handlers
        route_items = []
        for n in route_nodes:
            if n.classes:
                route_items.extend(n.classes[:2])
            elif n.functions:
                route_items.extend(f"{fn}()" for fn in n.functions[:2])
        route_desc = f"API entrypoints such as {', '.join(route_items[:3])}" if route_items else "the API gateway and route handlers"

        # Exact frontend components
        fe_items = []
        for n in fe_nodes:
            if n.classes:
                fe_items.extend(n.classes[:2])
            elif n.functions:
                fe_items.extend(n.functions[:2])
        fe_desc = f"frontend components including {', '.join(fe_items[:3])}" if fe_items else "the client user interface layer"

        # Exact core services & functions
        core_items = []
        for n in core_nodes:
            if n.classes:
                core_items.extend(n.classes[:2])
            if n.functions:
                core_items.extend(f"{fn}()" for fn in n.functions[:2])
        core_desc = f"core business logic managed by {', '.join(core_items[:3])}" if core_items else f"the {repo_display} backend engine"

        # Dependencies summary
        dep_summaries = []
        for e in graph.edges[:3]:
            symbols_str = f" using {', '.join(e.symbols)}" if e.symbols else ""
            dep_summaries.append(f"{e.source_id} imports {e.target_id}{symbols_str}")
        dep_text = f"Key module dependencies include {', '.join(dep_summaries)}. " if dep_summaries else ""

        lang = (target_language or "en").strip().lower()

        if lang == "gu":
            scene_1 = (
                f"[Scene 1: રીપોઝીટરી માહિતી અને ડિરેક્ટરી રચના]\n"
                f"{repo_name} ના આર્કિટેક્ચરલ વિશ્લેષણમાં તમારું સ્વાગત છે. "
                f"આ કોડબેઝમાં કુલ {graph.total_files} વિશ્લેષિત ફાઈલો અને {graph.total_lines} લાઈન કોડ શામેલ છે. "
                f"મુખ્ય મોડ્યુલ્સ જેવા કે {sample_files} રીપોઝીટરીને સ્પષ્ટ સ્તરોમાં વહેંચે છે. "
                f"{fe_desc} થી લઈને બેકએન્ડ કંટ્રોલર્સ સુધી, દરેક ડિરેક્ટરી સ્વતંત્ર કાર્યક્ષમતા પ્રદાન કરે છે."
            )
            scene_2 = (
                f"[Scene 2: સિસ્ટમ આર્કિટેક્ચર અને ડેટા પ્રવાહ]\n"
                f"સિસ્ટમ ટોપોલોજી અને કોમ્યુનિકેશન ફ્લો તપાસતાં, વિનંતીઓ {route_desc} દ્વારા મોકલવામાં આવે છે. "
                f"આવતા ટ્રાફિકનું પ્રમાણીકરણ કરી તેને {core_desc} તરફ આગળ ધપાવવામાં આવે છે. "
                f"{dep_text}"
                f"આંતરિક ઘટકો વચ્ચે ડેટા નિયંત્રિત નિયમો અને ટાઈપ્ડ કોન્ટ્રાક્ટ્સ દ્વારા વહે છે."
            )
            scene_3 = (
                f"[Scene 3: મુખ્ય અમલીકરણ અને લોજિક વિશ્લેષણ]\n"
                f"કોર એક્ઝિક્યુશન પાઇપલાઇનમાં ઊંડા ઉતરતાં, ડોમેન લોજિક સ્ટેટ સંચાલન અને વેલિડેશનને નિયંત્રિત કરે છે. "
                f"એન્ટિટીઓ સીધી રીતે {db_desc} સાથે જોડાયેલ છે, જે સંપૂર્ણ ડેટા સુસંગતતા પૂરી પાડે છે. "
                + (f"લાંબા સમયના કાર્યો {queue_nodes[0].label} ને સોંપવામાં આવે છે. " if queue_nodes else "સર્વિસ હેન્ડલર્સ નોન-બ્લોકિંગ કામગીરી જાળવી રાખે છે. ")
                + f"આ સ્વચ્છ આર્કિટેક્ચર સિસ્ટમમાં ભૂલો અટકાવે છે."
            )
            scene_4 = (
                f"[Scene 4: સારાંશ અને નિષ્કર્ષ]\n"
                f"સારાંશમાં, {repo_name} અત્યંત વિશ્વસનીય અને જાળવી શકાય તેવું સોફ્ટવેર માળખું પ્રદાન કરે છે. "
                f"{route_desc}, ડિસપ્લડ સેવાઓ અને {db_desc} નું સંયોજન સિસ્ટમને પ્રોડક્શનમાં અવિરત ગતિ આપે છે. "
                f"આ આર્કિટેક્ચરલ વિડીયો જોવા બદલ આભાર."
            )
        elif lang == "hi":
            scene_1 = (
                f"[Scene 1: रिपॉजिटरी अवलोकन और डायरेक्टरी संरचना]\n"
                f"{repo_name} के आर्किटेक्चरल विश्लेषण में आपका स्वागत है। "
                f"इस कोडबेस में कुल {graph.total_files} विश्लेषित फ़ाइलें और {graph.total_lines} लाइन्स ऑफ़ कोड शामिल हैं। "
                f"{sample_files} जैसे प्रमुख मॉड्यूल्स रिपॉजिटरी को स्वच्छ वास्तुकला स्तरों में व्यवस्थित करते हैं। "
                f"{fe_desc} से लेकर बैकएंड कंट्रोलर तक, प्रत्येक डायरेक्टरी अपनी विशिष्ट ज़िम्मेदारी संभालती है।"
            )
            scene_2 = (
                f"[Scene 2: सिस्टम आर्किटेक्चर और डेटा प्रवाह]\n"
                f"सिस्टम टोपोलॉजी और संचार प्रवाह का विश्लेषण करते हुए, क्लाइंट अनुरोध {route_desc} के माध्यम से रूट होते हैं। "
                f"आने वाले ट्रैफ़िक को मान्य करके {core_desc} को सौंपा जाता है। "
                f"{dep_text}"
                f"आंतरिक सीमाओं के पार डेटा प्रकार-सुरक्षित अनुबंधों और निर्भरता इंजेक्शन के माध्यम से प्रवाहित होता है।"
            )
            scene_3 = (
                f"[Scene 3: मुख्य लॉजिक और निष्पादन प्रक्रिया]\n"
                f"कोर निष्पादन पाइपलाइन में, डोमेन लॉजिक स्टेट ट्रांज़िशन और डेटा सत्यापन का समन्वय करता है। "
                f"एंटिटीज को सीधे {db_desc} में मैप किया जाता है, जो एसिड अनुपालन और डेटा निरंतरता सुनिश्चित करता है। "
                + (f"लंबे समय तक चलने वाले कार्यों को {queue_nodes[0].label} को सौंपा जाता है। " if queue_nodes else "अनुरोध प्रसंस्करण गैर-अवरोधक बना रहता है। ")
                + f"यह स्पष्ट अलगाव पूरे सिस्टम को उच्च विश्वसनीयता प्रदान करता है।"
            )
            scene_4 = (
                f"[Scene 4: सारांश और निष्कर्ष]\n"
                f"संक्षेप में, {repo_name} एक मजबूत और अत्यधिक स्केलेबल सॉफ़्टवेयर आर्किटेक्चर प्रदान करता है। "
                f"{route_desc}, डिकपल्ड सेवाओं और {db_desc} का संयोजन उत्पादन में निरंतर प्रदर्शन सुनिश्चित करता है। "
                f"इस आर्किटेक्चरल ट्यूटोरियल को देखने के लिए आपका धन्यवाद।"
            )
        elif lang == "mr":
            scene_1 = (
                f"[Scene 1: रिपॉझिटरी विहंगावलोकन आणि डिरेक्टरी रचना]\n"
                f"{repo_name} च्या आर्किटेक्चरल विश्लेषणामध्ये आपले स्वागत आहे. "
                f"या कोडबेसमध्ये एकूण {graph.total_files} विश्लेषित फाइल्स आणि {graph.total_lines} ओळींचा कोड आहे. "
                f"{sample_files} सारखे मुख्य मॉड्यूल्स रिपॉझिटरीला सुव्यवस्थित स्तरांमध्ये विभागतात. "
                f"{fe_desc} पासून बॅकएंड कंट्रोलर्सपर्यंत, प्रत्येक डिरेक्टरी स्वतंत्र जबाबदारी पार पाडते."
            )
            scene_2 = (
                f"[Scene 2: सिस्टम आर्किटेक्चर आणि डेटा प्रवाह]\n"
                f"सिस्टम टोपोलॉजी आणि संवाद प्रवाह तपासताना, क्लायंटच्या विनंत्या {route_desc} द्वारे पाठवल्या जातात. "
                f"येणारा ट्रॅफिक प्रमाणित करून {core_desc} कडे पाठवला जातो. "
                f"{dep_text}"
                f"डेटा अंतर्गत सीमांमध्ये सुरक्षितपणे आणि नियंत्रित नियमांनुसार वाहतो."
            )
            scene_3 = (
                f"[Scene 3: मुख्य लॉजिक आणि डेटा पाइपलाइन]\n"
                f"कोर एक्झिक्युशन पाइपलाइनमध्ये डोमेन लॉजिक स्टेट व्यवस्थापन आणि डेटा पडताळणी हाताळते. "
                f"मॉडेल्स थेट {db_desc} शी जोडलेले आहेत, ज्यामुळे डेटा सातत्य राखले जाते. "
                + (f"मोठी कामे {queue_nodes[0].label} कडे पाठवली जातात. " if queue_nodes else "सर्व्हिस हँडलर्स विनाव्यत्यय काम करतात. ")
                + f"ही रचना संपूर्ण प्रणालीची विश्वासार्हता वाढवते."
            )
            scene_4 = (
                f"[Scene 4: सारांश आणि निष्कर्ष]\n"
                f"थोडक्यात सांगायचे तर, {repo_name} अत्यंत स्केलेबल आणि विश्वासार्ह सॉफ्टवेअर आर्किटेक्चर प्रदान करते. "
                f"{route_desc} आणि {db_desc} चे सुयोग्य संयोजन प्रणालीची कार्यक्षमता वाढवते. "
                f"हा आर्किटेक्चरल व्हिडिओ पाहिल्याबद्दल मनःपूर्वक धन्यवाद."
            )
        elif lang == "bn":
            scene_1 = (
                f"[Scene 1: রিপোজিটরি ওভারভিউ এবং ডিরেক্টরি কাঠামো]\n"
                f"{repo_name} এর স্থাপত্য বিশ্লেষণে আপনাকে স্বাগতম। "
                f"এই কোডবেসে {graph.total_files} টি ফাইল এবং {graph.total_lines} লাইন কোড বিশ্লেষণ করা হয়েছে। "
                f"{sample_files} এর মতো গুরুত্বপূর্ণ মডিউলগুলি সংগ্রহস্থলটিকে সুসংগঠিত স্তরে সাজিয়েছে। "
                f"{fe_desc} থেকে শুরু করে ব্যাকএন্ড কন্ট্রোলার পর্যন্ত প্রতিটি ডিরেক্টরি নির্দিষ্ট দায়িত্ব পালন করে।"
            )
            scene_2 = (
                f"[Scene 2: সিস্টেম আর্কিটেকচার এবং ডেটা ফ্লো]\n"
                f"সিস্টেম যোগাযোগ প্রবাহ অনুসরণ করে ক্লায়েন্টের অনুরোধগুলি {route_desc} এর মাধ্যমে পাঠানো হয়। "
                f"ইনকামিং ট্র্যাফিক যাচাই করে {core_desc} এ প্রেরণ করা হয়। "
                f"{dep_text}"
                f"অভ্যন্তরীণ সীমানা জুড়ে ডেটা নিয়ন্ত্রিত চুক্তির মাধ্যমে নিরাপদে প্রবাহিত হয়।"
            )
            scene_3 = (
                f"[Scene 3: কোর লজিক এবং ডেটা পাইপলাইন]\n"
                f"কোর এক্সিকিউশন পাইপলাইনে ডোমেন লজিক স্টেট ট্রানজিশন নিয়ন্ত্রণ করে। "
                f"সত্ত্বাগুলি সরাসরি {db_desc} এর সাথে ম্যাপ করা হয়েছে, যা নির্ভরযোগ্য ডেটা স্থায়িত্ব নিশ্চিত করে। "
                + (f"দীর্ঘমেয়াদী কাজগুলি {queue_nodes[0].label} এ পাঠানো হয়। " if queue_nodes else "অনুরোধ প্রক্রিয়াকরণ সম্পূর্ণ প্রতিক্রিয়াশীল থাকে। ")
                + f"এই পরিষ্কার নকশা পুরো সিস্টেমকে সুরক্ষিত রাখে।"
            )
            scene_4 = (
                f"[Scene 4: সারসংক্ষেপ এবং উপসংহার]\n"
                f"সংক্ষেপে, {repo_name} একটি অত্যন্ত স্কেলযোগ্য এবং শক্তিশালী সফটওয়্যার আর্কিটেকচার প্রদান করে। "
                f"{route_desc} এবং {db_desc} এর সমন্বয় সিস্টেমের কর্মক্ষমতা বজায় রাখে। "
                f"এই স্থাপত্য বিশ্লেষণ ভিডিওটি দেখার জন্য আপনাকে ধন্যবাদ।"
            )
        elif lang == "ta":
            scene_1 = (
                f"[Scene 1: களஞ்சிய மேலோட்டம் மற்றும் அடைவு அமைப்பு]\n"
                f"{repo_name} இன் மென்பொருள் கட்டமைப்பு பகுப்பாய்விற்கு வரவேற்கிறோம். "
                f"இந்த குறியீட்டுத் தொகுப்பில் {graph.total_files} கோப்புகள் மற்றும் {graph.total_lines} வரிகள் உள்ளன. "
                f"{sample_files} போன்ற முக்கிய தொகுதிகள் திட்டத்தை நேர்த்தியாக ஒழுங்கமைக்கின்றன. "
                f"{fe_desc} முதல் பின்தள கன்ட்ரோலர்கள் வரை ஒவ்வொன்றும் தெளிவான எல்லைகளைக் கொண்டுள்ளன."
            )
            scene_2 = (
                f"[Scene 2: கணினி கட்டமைப்பு மற்றும் தரவு ஓட்டம்]\n"
                f"கணினி தொடர்பு பாதையைக் கண்காணிக்கும் போது, கோரிக்கைகள் {route_desc} மூலம் செலுத்தப்படுகின்றன. "
                f"உள்வரும் தகவல்கள் சரிபார்க்கப்பட்டு {core_desc} க்கு அனுப்பப்படுகின்றன. "
                f"{dep_text}"
                f"தரவு பாதுகாப்பான நெறிமுறைகள் மூலம் உள் எல்லைகளில் சீராகப் பயணிக்கிறது."
            )
            scene_3 = (
                f"[Scene 3: முதன்மை தர்க்கம் மற்றும் செயலாக்கப் பாதை]\n"
                f"முக்கிய செயல்பாட்டுப் பிரிவில் வணிக தர்க்கம் நிலைகளை நிர்வகிக்கிறது. "
                f"தரவுகள் நேரடியாக {db_desc} உடன் இணைக்கப்பட்டு முழுமையான நிலைத்தன்மையை உறுதி செய்கின்றன. "
                + (f"நீண்ட பணிகள் {queue_nodes[0].label} வரிசைக்கு மாற்றப்படுகின்றன. " if queue_nodes else "சேவை கையாளுபவர்கள் தடையின்றி இயங்குகின்றனர். ")
                + f"இந்த தெளிவான கட்டமைப்பு கணினியின் செயல்திறனை உயர்த்துகிறது."
            )
            scene_4 = (
                f"[Scene 4: சுருக்கம் மற்றும் முடிவு]\n"
                f"சுருக்கமாக, {repo_name} அளவிடக்கூடிய மற்றும் நம்பகமான மென்பொருள் கட்டமைப்பை வழங்குகிறது. "
                f"{route_desc} மற்றும் {db_desc} இன் ஒருங்கிணைப்பு சிறந்த செயல்திறனை அளிக்கிறது. "
                f"இந்த வீடியோவைப் பார்த்ததற்கு நன்றி."
            )
        elif lang == "te":
            scene_1 = (
                f"[Scene 1: రిపోజిటరీ అవలోకనం మరియు డైరెక్టరీ నిర్మాణం]\n"
                f"{repo_name} ఆర్కిటెక్చరల్ విశ్లేషణకు స్వాగతం. "
                f"ఈ కోడ్‌బేస్‌లో {graph.total_files} ఫైళ్లు మరియు {graph.total_lines} కోడ్ లైన్లు విశ్లేషించబడ్డాయి. "
                f"{sample_files} వంటి ముఖ్యమైన మాడ్యూల్స్ ప్రాజెక్ట్‌ను స్పష్టమైన లేయర్‌లుగా అమర్చుతాయి. "
                f"{fe_desc} నుండి బ్యాకెండ్ కంట్రోలర్ల వరకు ప్రతి డైరెక్టరీ నిర్దిష్ట బాధ్యతలను నిర్వహిస్తుంది."
            )
            scene_2 = (
                f"[Scene 2: సిస్టమ్ ఆర్కిటెక్చర్ మరియు డేటా ప్రవాహం]\n"
                f"సిస్టమ్ కమ్యూనికేషన్ ఫ్లోను పరిశీలిస్తే, క్లయింట్ అభ్యర్థనలు {route_desc} ద్వారా రూట్ చేయబడతాయి. "
                f"ఇన్‌కమింగ్ ట్రాఫిక్ ధృవీకరించబడి {core_desc}కి పంపబడుతుంది. "
                f"{dep_text}"
                f"డేటా అంతర్గతంగా సురక్షితమైన ఒప్పందాల ద్వారా ప్రవహిస్తుంది."
            )
            scene_3 = (
                f"[Scene 3: కోర్ లాజిక్ మరియు డేటా పైప్‌లైన్]\n"
                f"కోర్ ఎగ్జిక్యూషన్ పైప్‌లైన్‌లో బిజినెస్ లాజిక్ స్టేట్ ట్రాన్సిషన్‌లను నిర్వహిస్తుంది. "
                f"డేటా నేరుగా {db_desc}కి మ్యాప్ చేయబడి స్థిరత్వాన్ని అందిస్తుంది. "
                + (f"ఎక్కువ సమయం పట్టే పనులు {queue_nodes[0].label} కి బదిలీ చేయబడతాయి. " if queue_nodes else "ప్రాసెసింగ్ వేగవంతంగా సాగుతుంది. ")
                + f"ఈ స్పష్టమైన విభజన సిస్టమ్‌ను పటిష్టంగా ఉంచుతుంది."
            )
            scene_4 = (
                f"[Scene 4: సారాంశం మరియు ముగింపు]\n"
                f"సారాంశంగా, {repo_name} అత్యంత స్కేలబుల్ మరియు నమ్మదగిన సాఫ్ట్‌వేర్ ఆర్కిటెక్చర్‌ను అందిస్తుంది. "
                f"{route_desc} మరియు {db_desc} కలయిక సిస్టమ్ పనితీరును వేగవంతం చేస్తుంది. "
                f"ఈ ఆర్కిటెక్చరల్ వీడియోను వీక్షించినందుకు ధన్యవాదాలు."
            )
        elif lang == "es":
            scene_1 = (
                f"[Scene 1: Descripción del Repositorio y Estructura de Directorios]\n"
                f"Bienvenidos al análisis arquitectónico detallado de {repo_name}. "
                f"El código base contiene {graph.total_files} archivos analizados con {graph.total_lines} líneas de código. "
                f"Módulos clave como {sample_files} organizan el repositorio en capas arquitectónicas limpiamente separadas. "
                f"Desde {fe_desc} hasta los controladores backend, cada directorio establece límites claros de responsabilidad."
            )
            scene_2 = (
                f"[Scene 2: Arquitectura del Sistema y Flujo de Datos]\n"
                f"Al trazar la topología y el flujo de comunicación, las solicitudes se enrutan a través de {route_desc}. "
                f"El tráfico entrante se autentica, se valida y se entrega a {core_desc}. "
                f"{dep_text}"
                f"Los datos atraviesan los límites internos utilizando contratos tipados e inyección de dependencias."
            )
            scene_3 = (
                f"[Scene 3: Implementación del Núcleo y Lógica Interna]\n"
                f"Profundizando en la canalización de ejecución principal, la lógica de dominio coordina el estado y la validación. "
                f"Las entidades se asignan directamente a {db_desc}, garantizando cumplimiento ACID y consistencia transaccional. "
                + (f"Las tareas prolongadas se delegan a {queue_nodes[0].label} de forma asíncrona. " if queue_nodes else "El procesamiento permanece no bloqueante con manejadores desacoplados. ")
                + f"Esta clara separación de responsabilidades previene fallos en cascada en los subsistemas."
            )
            scene_4 = (
                f"[Scene 4: Resumen del Ciclo de Vida y Conclusión]\n"
                f"En resumen, {repo_name} ofrece una arquitectura de software robusta y altamente mantenible. "
                f"Al combinar {route_desc}, orquestación de servicios desacoplada y {db_desc}, el sistema escala con solvencia en producción. "
                f"Gracias por acompañarnos en este recorrido arquitectónico."
            )
        elif lang == "fr":
            scene_1 = (
                f"[Scene 1: Vue d'Ensemble du Référentiel et Structure des Répertoires]\n"
                f"Bienvenue dans l'analyse architecturale approfondie de {repo_name}. "
                f"La base de code comprend {graph.total_files} fichiers analysés totalisant {graph.total_lines} lignes de code. "
                f"Des modules clés comme {sample_files} organisent le dépôt en couches logiques bien délimitées. "
                f"De {fe_desc} aux contrôleurs d'arrière-plan, chaque répertoire assume un rôle précis."
            )
            scene_2 = (
                f"[Scene 2: Architecture Système et Flux de Données]\n"
                f"En suivant la topologie du système, les requêtes entrantes sont acheminées via {route_desc}. "
                f"Le trafic est authentifié, validé puis transmis à {core_desc}. "
                f"{dep_text}"
                f"Les données franchissent les frontières internes grâce à des contrats typés et à l'injection de dépendances."
            )
            scene_3 = (
                f"[Scene 3: Implémentation du Cœur et Logique Métier]\n"
                f"Au sein de la chaîne d'exécution, la logique métier gère les transitions d'état et la validation des données. "
                f"Les entités sont directement reliées à {db_desc}, garantissant l'intégrité transactionnelle ACID. "
                + (f"Les tâches lourdes sont confiées à la file {queue_nodes[0].label}. " if queue_nodes else "Le traitement des requêtes reste fluide et non-bloquant. ")
                + f"Cette séparation préserve la robustesse de l'ensemble du système."
            )
            scene_4 = (
                f"[Scene 4: Synthèse du Cycle de Vie et Conclusion]\n"
                f"En résumé, {repo_name} propose une architecture logicielle robuste et particulièrement maintenable. "
                f"En associant {route_desc}, des services découplés et {db_desc}, le système évolue efficacement en production. "
                f"Merci d'avoir regardé cette présentation architecturale."
            )
        else:
            scene_1 = (
                f"[Scene 1: Repository Overview & Directory Structure]\n"
                f"Welcome to the architectural deep dive of {repo_name}. "
                f"The codebase contains {graph.total_files} analyzed files spanning {graph.total_lines} lines of code. "
                f"Key modules including {sample_files} organize the repository into cleanly separated architectural tiers. "
                f"From {fe_desc} to backend controllers, each directory establishes distinct boundaries of responsibility."
            )
            scene_2 = (
                f"[Scene 2: System Architecture & Data Flow]\n"
                f"Tracing the system topology and communication flow, client requests are routed through {route_desc}. "
                f"Incoming traffic is authenticated, validated, and passed down to {core_desc}. "
                f"{dep_text}"
                f"Data traverses internal boundaries using typed contracts and explicit dependency injection."
            )
            scene_3 = (
                f"[Scene 3: Core Implementation & Logic Deep Dive]\n"
                f"Diving deeper into the core execution pipeline, domain logic coordinates state transitions and data validation. "
                f"Entities are mapped directly to {db_desc}, ensuring ACID compliance and consistent lifecycle transactions. "
                + (f"Long-running tasks are dispatched to {queue_nodes[0].label} for asynchronous execution, preserving real-time throughput. " if queue_nodes else "Request processing remains non-blocking with decoupled service handlers. ")
                + f"This clean separation of concerns prevents cascading failures across subsystems."
            )
            scene_4 = (
                f"[Scene 4: Lifecycle Summary & Conclusion]\n"
                f"In summary, {repo_name} provides a robust and maintainable software architecture. "
                f"By combining {route_desc}, decoupled service orchestration, and {db_desc}, the system scales reliably under production workloads. "
                f"Thank you for watching this architectural walkthrough."
            )

        return f"{scene_1}\n\n{scene_2}\n\n{scene_3}\n\n{scene_4}"

    @staticmethod
    def _generate_multiscene_manim_script(
        repo_display: str,
        files: List[str],
        nodes: List[NodeModel],
        connections: List[ConnectionModel],
    ) -> str:
        """Generate a complete, modern Manim script containing all 4 scenes, lasting 60-90s."""
        # Top files to render in File Tree scene
        sample_file_lines = []
        for i, f in enumerate(files[:6]):
            short = f.replace("\\", "/")
            sample_file_lines.append(f'            Text("📄 {short}", font_size=16, color="#94A3B8"),')
        file_items_code = "\n".join(sample_file_lines)

        script = f'''"""Multi-Scene Manim Community Animation Script for {repo_display}."""

from manim import *

class ComprehensiveTutorialScene(Scene):
    def construct(self):
        # Configuration
        self.camera.background_color = "#0A0E17"

        # =====================================================================
        # SCENE 1: Repository Overview & File Tree Hierarchy (~18 seconds)
        # =====================================================================
        title_s1 = Text("{repo_display} Architecture", font_size=32, color="#38BDF8", weight=BOLD)
        subtitle_s1 = Text("Scene 1: Codebase Hierarchy & Project Structure", font_size=18, color="#94A3B8")
        header_group_s1 = VGroup(title_s1, subtitle_s1).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header_group_s1.to_corner(UL, buff=0.6)

        self.play(FadeIn(header_group_s1, shift=DOWN * 0.3), run_time=1.2)
        self.wait(1.5)

        # File Tree Visual Card
        tree_box = RoundedRectangle(corner_radius=0.2, width=8.5, height=4.2, color="#1E293B", fill_color="#111827", fill_opacity=0.9)
        tree_box.shift(DOWN * 0.4)

        tree_header = Text("📁 Repository Source Modules", font_size=20, color="#F8FAFC", weight=SEMIBOLD)
        tree_header.next_to(tree_box.get_top(), DOWN, buff=0.25)

        files_group = VGroup(
{file_items_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        files_group.next_to(tree_header, DOWN, buff=0.3)

        self.play(Create(tree_box), FadeIn(tree_header), run_time=1.5)
        self.play(LaggedStart(*[FadeIn(f, shift=RIGHT * 0.2) for f in files_group], lag_ratio=0.18), run_time=3.0)
        self.wait(8.0)

        # Clean transition to Scene 2
        self.play(
            FadeOut(header_group_s1),
            FadeOut(tree_box),
            FadeOut(tree_header),
            FadeOut(files_group),
            run_time=1.2
        )
        self.wait(0.8)

        # =====================================================================
        # SCENE 2: Architectural Component Topology (~25 seconds)
        # =====================================================================
        title_s2 = Text("System Topology & Data Flow", font_size=30, color="#4ADE80", weight=BOLD)
        subtitle_s2 = Text("Scene 2: Service Communication & Distributed Routing", font_size=18, color="#94A3B8")
        header_group_s2 = VGroup(title_s2, subtitle_s2).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header_group_s2.to_corner(UL, buff=0.6)

        self.play(FadeIn(header_group_s2, shift=DOWN * 0.3), run_time=1.2)

        # Create Architecture Node Cards
        node_cards = []
        node_positions = [
            [-4.8, 0.0, 0],   # Client
            [-2.4, 0.0, 0],   # Gateway
            [0.0, 0.0, 0],    # Backend Core
            [2.4, 1.2, 0],    # Queue/State
            [4.5, -0.8, 0],   # Database
        ]
        node_colors = ["#38BDF8", "#A855F7", "#6366F1", "#F59E0B", "#10B981"]
        node_labels = ["Client App", "API Gateway", "Core Engine", "Task Queue", "Database"]
        node_subtexts = ["Next.js / UI", "HTTP Routing", "Business Logic", "Async Broker", "PostgreSQL"]

        card_mobjects = []
        for idx in range(min(len(node_positions), 5)):
            pos = node_positions[idx]
            col = node_colors[idx]
            lbl = node_labels[idx]
            sub = node_subtexts[idx]

            card = RoundedRectangle(corner_radius=0.15, width=2.1, height=1.6, color=col, fill_color="#0F172A", fill_opacity=0.92)
            card.move_to(pos)
            txt_title = Text(lbl, font_size=15, color="#FFFFFF", weight=SEMIBOLD).move_to(card.get_top() + DOWN * 0.4)
            txt_sub = Text(sub, font_size=12, color=col).next_to(txt_title, DOWN, buff=0.15)
            group = VGroup(card, txt_title, txt_sub)
            card_mobjects.append(group)

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in card_mobjects], lag_ratio=0.2), run_time=2.5)
        self.wait(2.0)

        # Connect nodes with animated arrows and pulsing data packets
        arrows = []
        arrow_specs = [(0, 1), (1, 2), (2, 3), (2, 4)]
        for src, tgt in arrow_specs:
            if src < len(card_mobjects) and tgt < len(card_mobjects):
                arr = Arrow(
                    card_mobjects[src].get_right(),
                    card_mobjects[tgt].get_left(),
                    buff=0.1,
                    color="#64748B",
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.2
                )
                arrows.append(arr)

        if arrows:
            self.play(*[Create(a) for a in arrows], run_time=2.0)
            self.wait(1.5)

            # Animate data packet flows across connections
            packets = [Dot(radius=0.1, color="#38BDF8").move_to(a.get_start()) for a in arrows]
            self.play(*[FadeIn(p) for p in packets], run_time=0.5)
            self.play(
                *[p.animate.move_to(a.get_end()) for p, a in zip(packets, arrows)],
                run_time=3.0,
                rate_func=linear
            )
            self.play(*[FadeOut(p) for p in packets], run_time=0.5)

        self.wait(8.0)

        # Clean transition to Scene 3
        self.play(
            FadeOut(header_group_s2),
            *[FadeOut(c) for c in card_mobjects],
            *[FadeOut(a) for a in arrows],
            run_time=1.2
        )
        self.wait(0.8)

        # =====================================================================
        # SCENE 3: Core Implementation & Logic Deep Dive (~25 seconds)
        # =====================================================================
        title_s3 = Text("Core Implementation & Execution Flow", font_size=30, color="#F59E0B", weight=BOLD)
        subtitle_s3 = Text("Scene 3: Asynchronous Pipeline & State Synchronization", font_size=18, color="#94A3B8")
        header_group_s3 = VGroup(title_s3, subtitle_s3).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header_group_s3.to_corner(UL, buff=0.6)

        self.play(FadeIn(header_group_s3, shift=DOWN * 0.3), run_time=1.2)

        # Execution Lifecycle Steps Box
        exec_box = RoundedRectangle(corner_radius=0.2, width=9.2, height=4.3, color="#1E293B", fill_color="#0F172A", fill_opacity=0.9)
        exec_box.shift(DOWN * 0.35)

        step_1 = Text("1. Incoming payload validation & schema parsing via Pydantic/Zod", font_size=16, color="#F8FAFC")
        step_2 = Text("2. Route dispatch with token-bucket rate limiting & telemetry tracking", font_size=16, color="#38BDF8")
        step_3 = Text("3. Async worker task offloading via Redis broker to preserve throughput", font_size=16, color="#4ADE80")
        step_4 = Text("4. ACID entity persistence & transactional model write to primary DB", font_size=16, color="#F59E0B")
        step_5 = Text("5. Real-time progress broadcasting via Server-Sent Events (SSE)", font_size=16, color="#A855F7")

        steps_group = VGroup(step_1, step_2, step_3, step_4, step_5).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        steps_group.move_to(exec_box.get_center())

        self.play(Create(exec_box), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.3) for s in steps_group], lag_ratio=0.3), run_time=3.5)
        self.wait(10.0)

        # Clean transition to Scene 4
        self.play(
            FadeOut(header_group_s3),
            FadeOut(exec_box),
            FadeOut(steps_group),
            run_time=1.2
        )
        self.wait(0.8)

        # =====================================================================
        # SCENE 4: Architecture Conclusion & Production Strengths (~15 seconds)
        # =====================================================================
        title_s4 = Text("Production Architecture Summary", font_size=32, color="#38BDF8", weight=BOLD)
        subtitle_s4 = Text("Scene 4: Reliability, Scalability & Modular Separation", font_size=18, color="#94A3B8")
        header_group_s4 = VGroup(title_s4, subtitle_s4).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header_group_s4.to_corner(UL, buff=0.6)

        self.play(FadeIn(header_group_s4, shift=DOWN * 0.3), run_time=1.2)

        # Summary Metrics Badges
        b1 = RoundedRectangle(corner_radius=0.15, width=2.6, height=2.2, color="#10B981", fill_color="#064E3B", fill_opacity=0.6)
        t1_top = Text("High", font_size=24, color="#10B981", weight=BOLD)
        t1_sub = Text("Throughput", font_size=14, color="#A7F3D0")
        t1_desc = Text("Non-blocking IO", font_size=11, color="#6EE7B7")
        g1 = VGroup(b1, VGroup(t1_top, t1_sub, t1_desc).arrange(DOWN, buff=0.15).move_to(b1))

        b2 = RoundedRectangle(corner_radius=0.15, width=2.6, height=2.2, color="#38BDF8", fill_color="#0C4A6E", fill_opacity=0.6)
        t2_top = Text("Modular", font_size=24, color="#38BDF8", weight=BOLD)
        t2_sub = Text("Boundaries", font_size=14, color="#BAE6FD")
        t2_desc = Text("Decoupled services", font_size=11, color="#7DD3FC")
        g2 = VGroup(b2, VGroup(t2_top, t2_sub, t2_desc).arrange(DOWN, buff=0.15).move_to(b2))

        b3 = RoundedRectangle(corner_radius=0.15, width=2.6, height=2.2, color="#A855F7", fill_color="#581C87", fill_opacity=0.6)
        t3_top = Text("Robust", font_size=24, color="#A855F7", weight=BOLD)
        t3_sub = Text("Persistence", font_size=14, color="#E9D5FF")
        t3_desc = Text("ACID Compliance", font_size=11, color="#D8B4FE")
        g3 = VGroup(b3, VGroup(t3_top, t3_sub, t3_desc).arrange(DOWN, buff=0.15).move_to(b3))

        badges_group = VGroup(g1, g2, g3).arrange(RIGHT, buff=0.5).shift(DOWN * 0.35)

        self.play(LaggedStart(*[FadeIn(g, shift=UP * 0.3) for g in badges_group], lag_ratio=0.25), run_time=2.2)
        # Final hold sequence: keeps badges cleanly on screen to prevent black screen
        self.wait(8.0)
'''
        return script

    @staticmethod
    def _generate_graph_aware_manim_script(
        repo_display: str,
        graph: CodebaseGraph,
        arch_data: ArchitectureDiagramData,
    ) -> str:
        """Generate a Manim script with all 4 scenes driven by the CodebaseGraph and ArchitectureDiagramData."""
        # Top files to render in File Tree scene
        sample_file_lines = []
        for n in graph.nodes[:6]:
            short = n.path.replace("\\", "/")
            sample_file_lines.append(f'            Text("📄 {short}", font_size=16, color="#94A3B8"),')
        file_items_code = "\n".join(sample_file_lines)

        # Build cards for Scene 2
        card_items = []
        for n in arch_data.nodes[:5]:
            lbl = n.label.replace('"', '\\"')
            sub = (n.tech or n.kind.value.title()).replace('"', '\\"')
            col = n.color or "#38BDF8"
            pos = [round(float(p), 2) for p in n.position]
            card_items.append((lbl, sub, col, pos))

        # Build arrow pairs
        node_id_to_idx = {n.id: i for i, n in enumerate(arch_data.nodes[:5])}
        arrow_specs = []
        for c in arch_data.connections:
            if c.source_id in node_id_to_idx and c.target_id in node_id_to_idx:
                s_idx = node_id_to_idx[c.source_id]
                t_idx = node_id_to_idx[c.target_id]
                if s_idx != t_idx:
                    arrow_specs.append((s_idx, t_idx))

        if not arrow_specs and len(card_items) > 1:
            arrow_specs = [(i, i + 1) for i in range(len(card_items) - 1)]

        # Scene 3 Execution Steps grounded in genuine classes
        db_classes = [c for n in graph.nodes if n.kind == NodeType.DATABASE for c in n.classes]
        route_classes = [c for n in graph.nodes if n.kind == NodeType.GATEWAY for c in (n.classes or n.functions)]
        core_classes = [c for n in graph.nodes if n.kind == NodeType.BACKEND for c in (n.classes or n.functions)]
        queue_names = [n.label for n in graph.nodes if n.kind == NodeType.QUEUE]

        route_label = f" via {route_classes[0]}" if route_classes else ""
        model_label = f" ({db_classes[0]})" if db_classes else ""
        core_label = f" within {core_classes[0]}" if core_classes else ""
        queue_label = f" via {queue_names[0]}" if queue_names else " to async worker pool"

        script = f'''"""Multi-Scene Manim Community Animation Script for {repo_display}."""

from manim import *

class ComprehensiveTutorialScene(Scene):
    def construct(self):
        # Configuration
        self.camera.background_color = "#0A0E17"

        # =====================================================================
        # SCENE 1: Repository Overview & File Tree Hierarchy (~18 seconds)
        # =====================================================================
        title_s1 = Text("{repo_display} Architecture", font_size=32, color="#38BDF8", weight=BOLD)
        subtitle_s1 = Text("Scene 1: Codebase Hierarchy & Project Structure", font_size=18, color="#94A3B8")
        header_group_s1 = VGroup(title_s1, subtitle_s1).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header_group_s1.to_corner(UL, buff=0.6)

        self.play(FadeIn(header_group_s1, shift=DOWN * 0.3), run_time=1.2)
        self.wait(1.5)

        # File Tree Visual Card
        tree_box = RoundedRectangle(corner_radius=0.2, width=8.5, height=4.2, color="#1E293B", fill_color="#111827", fill_opacity=0.9)
        tree_box.shift(DOWN * 0.4)

        tree_header = Text("📁 Repository Source Modules ({graph.total_files} files)", font_size=20, color="#F8FAFC", weight=SEMIBOLD)
        tree_header.next_to(tree_box.get_top(), DOWN, buff=0.25)

        files_group = VGroup(
{file_items_code}
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        files_group.next_to(tree_header, DOWN, buff=0.3)

        self.play(Create(tree_box), FadeIn(tree_header), run_time=1.5)
        self.play(LaggedStart(*[FadeIn(f, shift=RIGHT * 0.2) for f in files_group], lag_ratio=0.18), run_time=3.0)
        self.wait(8.0)

        # Clean transition to Scene 2
        self.play(
            FadeOut(header_group_s1),
            FadeOut(tree_box),
            FadeOut(tree_header),
            FadeOut(files_group),
            run_time=1.2
        )
        self.wait(0.8)

        # =====================================================================
        # SCENE 2: Architectural Component Topology (~25 seconds)
        # =====================================================================
        title_s2 = Text("System Topology & Data Flow", font_size=30, color="#4ADE80", weight=BOLD)
        subtitle_s2 = Text("Scene 2: Service Communication & Distributed Routing", font_size=18, color="#94A3B8")
        header_group_s2 = VGroup(title_s2, subtitle_s2).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header_group_s2.to_corner(UL, buff=0.6)

        self.play(FadeIn(header_group_s2, shift=DOWN * 0.3), run_time=1.2)

        # Create Architecture Node Cards from AST Graph
        card_mobjects = []
        card_data = {card_items}
        for lbl, sub, col, pos in card_data:
            card = RoundedRectangle(corner_radius=0.15, width=2.1, height=1.6, color=col, fill_color="#0F172A", fill_opacity=0.92)
            card.move_to(pos)
            txt_title = Text(lbl, font_size=14, color="#FFFFFF", weight=SEMIBOLD).move_to(card.get_top() + DOWN * 0.4)
            txt_sub = Text(sub, font_size=11, color=col).next_to(txt_title, DOWN, buff=0.15)
            group = VGroup(card, txt_title, txt_sub)
            card_mobjects.append(group)

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in card_mobjects], lag_ratio=0.2), run_time=2.5)
        self.wait(2.0)

        # Connect nodes with animated arrows and pulsing data packets
        arrows = []
        arrow_specs = {arrow_specs}
        for src, tgt in arrow_specs:
            if src < len(card_mobjects) and tgt < len(card_mobjects):
                arr = Arrow(
                    card_mobjects[src].get_right(),
                    card_mobjects[tgt].get_left(),
                    buff=0.1,
                    color="#64748B",
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.2
                )
                arrows.append(arr)

        if arrows:
            self.play(*[Create(a) for a in arrows], run_time=2.0)
            self.wait(1.5)

            packets = [Dot(radius=0.1, color="#38BDF8").move_to(a.get_start()) for a in arrows]
            self.play(*[FadeIn(p) for p in packets], run_time=0.5)
            self.play(
                *[p.animate.move_to(a.get_end()) for p, a in zip(packets, arrows)],
                run_time=3.0,
                rate_func=linear
            )
            self.play(*[FadeOut(p) for p in packets], run_time=0.5)

        self.wait(8.0)

        # Clean transition to Scene 3
        self.play(
            FadeOut(header_group_s2),
            *[FadeOut(c) for c in card_mobjects],
            *[FadeOut(a) for a in arrows],
            run_time=1.2
        )
        self.wait(0.8)

        # =====================================================================
        # SCENE 3: Core Implementation & Logic Deep Dive (~25 seconds)
        # =====================================================================
        title_s3 = Text("Core Implementation & Execution Flow", font_size=30, color="#F59E0B", weight=BOLD)
        subtitle_s3 = Text("Scene 3: Asynchronous Pipeline & State Synchronization", font_size=18, color="#94A3B8")
        header_group_s3 = VGroup(title_s3, subtitle_s3).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header_group_s3.to_corner(UL, buff=0.6)

        self.play(FadeIn(header_group_s3, shift=DOWN * 0.3), run_time=1.2)

        # Execution Lifecycle Steps Box
        exec_box = RoundedRectangle(corner_radius=0.2, width=9.2, height=4.3, color="#1E293B", fill_color="#0F172A", fill_opacity=0.9)
        exec_box.shift(DOWN * 0.35)

        step_1 = Text("1. Incoming payload schema validation{model_label}", font_size=16, color="#F8FAFC")
        step_2 = Text("2. Route dispatch & token-bucket throttling{route_label}", font_size=16, color="#38BDF8")
        step_3 = Text("3. Core business logic execution{core_label}", font_size=16, color="#4ADE80")
        step_4 = Text("4. Asynchronous worker task offloading{queue_label}", font_size=16, color="#F59E0B")
        step_5 = Text("5. ACID entity persistence & transactional model write", font_size=16, color="#A855F7")

        steps_group = VGroup(step_1, step_2, step_3, step_4, step_5).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        steps_group.move_to(exec_box.get_center())

        self.play(Create(exec_box), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.3) for s in steps_group], lag_ratio=0.3), run_time=3.5)
        self.wait(10.0)

        # Clean transition to Scene 4
        self.play(
            FadeOut(header_group_s3),
            FadeOut(exec_box),
            FadeOut(steps_group),
            run_time=1.2
        )
        self.wait(0.8)

        # =====================================================================
        # SCENE 4: Architecture Conclusion & Production Strengths (~15 seconds)
        # =====================================================================
        title_s4 = Text("Production Architecture Summary", font_size=32, color="#38BDF8", weight=BOLD)
        subtitle_s4 = Text("Scene 4: Reliability, Scalability & Modular Separation", font_size=18, color="#94A3B8")
        header_group_s4 = VGroup(title_s4, subtitle_s4).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        header_group_s4.to_corner(UL, buff=0.6)

        self.play(FadeIn(header_group_s4, shift=DOWN * 0.3), run_time=1.2)

        # Summary Metrics Badges
        b1 = RoundedRectangle(corner_radius=0.15, width=2.6, height=2.2, color="#10B981", fill_color="#064E3B", fill_opacity=0.6)
        t1_top = Text("High", font_size=24, color="#10B981", weight=BOLD)
        t1_sub = Text("Throughput", font_size=14, color="#A7F3D0")
        t1_desc = Text("Non-blocking IO", font_size=11, color="#6EE7B7")
        g1 = VGroup(b1, VGroup(t1_top, t1_sub, t1_desc).arrange(DOWN, buff=0.15).move_to(b1))

        b2 = RoundedRectangle(corner_radius=0.15, width=2.6, height=2.2, color="#38BDF8", fill_color="#0C4A6E", fill_opacity=0.6)
        t2_top = Text("Modular", font_size=24, color="#38BDF8", weight=BOLD)
        t2_sub = Text("Boundaries", font_size=14, color="#BAE6FD")
        t2_desc = Text("Decoupled services", font_size=11, color="#7DD3FC")
        g2 = VGroup(b2, VGroup(t2_top, t2_sub, t2_desc).arrange(DOWN, buff=0.15).move_to(b2))

        b3 = RoundedRectangle(corner_radius=0.15, width=2.6, height=2.2, color="#A855F7", fill_color="#581C87", fill_opacity=0.6)
        t3_top = Text("Robust", font_size=24, color="#A855F7", weight=BOLD)
        t3_sub = Text("Persistence", font_size=14, color="#E9D5FF")
        t3_desc = Text("ACID Compliance", font_size=11, color="#D8B4FE")
        g3 = VGroup(b3, VGroup(t3_top, t3_sub, t3_desc).arrange(DOWN, buff=0.15).move_to(b3))

        badges_group = VGroup(g1, g2, g3).arrange(RIGHT, buff=0.5).shift(DOWN * 0.35)

        self.play(LaggedStart(*[FadeIn(g, shift=UP * 0.3) for g in badges_group], lag_ratio=0.25), run_time=2.2)
        # Final hold sequence: keeps badges cleanly on screen to prevent black screen
        self.wait(8.0)
'''
        return script
