"""Unit and integration test suite for Codebase Graph Service, AST extraction, and Manim mapping."""

import ast
import json
import py_compile
import tempfile
from pathlib import Path
import pytest

from app.services.graph_service import (
    CodebaseGraph,
    CodebaseGraphService,
    GraphEdge,
    GraphNode,
)
from app.services.graph_to_manim import (
    DEFAULT_CANVAS_BOUNDS,
    GraphToManimMapper,
    generate_manim_flowchart_scene_code,
)
from app.services.gemini_service import GeminiScriptService, ScriptSynthesisResult
from manim_engine.models import ArchitectureDiagramData, NodeType


@pytest.fixture
def mock_codebase_repo():
    """Create a temporary mock multi-tiered repository for AST analysis."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_root = Path(tmp_dir) / "sample_service"
        repo_root.mkdir()

        # 1. API Route Layer
        api_dir = repo_root / "app" / "api"
        api_dir.mkdir(parents=True)
        (api_dir / "orders.py").write_text(
            "from app.services.order_service import OrderProcessor\n"
            "from app.models.order import OrderRecord\n\n"
            "class OrderRouter:\n"
            "    def list_orders(self):\n"
            "        return []\n",
            encoding="utf-8",
        )

        # 2. Service Layer
        svc_dir = repo_root / "app" / "services"
        svc_dir.mkdir(parents=True)
        (svc_dir / "order_service.py").write_text(
            "from app.models.order import OrderRecord\n"
            "from app.workers.tasks import queue_job\n\n"
            "class OrderProcessor:\n"
            "    def process_payment(self, order_id: str):\n"
            "        return True\n",
            encoding="utf-8",
        )

        # 3. Worker / Task Layer
        worker_dir = repo_root / "app" / "workers"
        worker_dir.mkdir(parents=True)
        (worker_dir / "tasks.py").write_text(
            "import redis\n\n"
            "def queue_job(payload):\n"
            "    return True\n",
            encoding="utf-8",
        )

        # 4. Database / Model Layer
        model_dir = repo_root / "app" / "models"
        model_dir.mkdir(parents=True)
        (model_dir / "order.py").write_text(
            "from pydantic import BaseModel\n\n"
            "class OrderRecord(BaseModel):\n"
            "    id: str\n"
            "    total_amount: float\n",
            encoding="utf-8",
        )

        # 5. Frontend Client Component
        fe_dir = repo_root / "frontend" / "components"
        fe_dir.mkdir(parents=True)
        (fe_dir / "OrderList.tsx").write_text(
            "import React from 'react';\n"
            "import { OrderProcessor } from '../api';\n\n"
            "export function OrderList() {\n"
            "    return <div>Order Summary</div>;\n"
            "}\n",
            encoding="utf-8",
        )

        yield repo_root


def test_ast_extraction_nodes_and_layers(mock_codebase_repo):
    """Verify multi-tier AST extraction, node categorization, and class/method inspection."""
    service = CodebaseGraphService(max_nodes=20)
    graph = service.generate_graph(mock_codebase_repo, repo_name="MockOrderApp")

    assert isinstance(graph, CodebaseGraph)
    assert graph.repo_name == "MockOrderApp"
    assert graph.total_files >= 5
    assert graph.total_lines > 0
    assert len(graph.nodes) >= 5

    nodes_by_label = {n.label: n for n in graph.nodes}
    assert "orders.py" in nodes_by_label
    assert "order_service.py" in nodes_by_label
    assert "order.py" in nodes_by_label
    assert "tasks.py" in nodes_by_label
    assert "OrderList.tsx" in nodes_by_label

    # Check Gateway Layer
    gateway = nodes_by_label["orders.py"]
    assert gateway.kind == NodeType.GATEWAY
    assert gateway.layer == 1
    assert "OrderRouter" in gateway.classes
    assert "list_orders" in gateway.functions

    # Check Core Service Layer
    core = nodes_by_label["order_service.py"]
    assert core.kind == NodeType.BACKEND
    assert core.layer == 2
    assert "OrderProcessor" in core.classes
    assert "process_payment" in core.functions

    # Check Database Model Layer
    db = nodes_by_label["order.py"]
    assert db.kind == NodeType.DATABASE
    assert db.layer == 4
    assert "OrderRecord" in db.classes

    # Check Queue Layer
    queue = nodes_by_label["tasks.py"]
    assert queue.kind == NodeType.QUEUE
    assert queue.layer == 3
    assert "queue_job" in queue.functions

    # Check Frontend Layer
    fe = nodes_by_label["OrderList.tsx"]
    assert fe.kind == NodeType.FRONTEND
    assert fe.layer == 0
    assert "OrderList" in fe.functions


def test_dependency_edges_and_symbols(mock_codebase_repo):
    """Verify directed import dependency edges, symbol tracking, and in/out degrees."""
    service = CodebaseGraphService(max_nodes=20)
    graph = service.generate_graph(mock_codebase_repo)

    assert len(graph.edges) >= 3

    # Check edge connections
    edge_pairs = {(e.source_id, e.target_id) for e in graph.edges}
    assert ("node_app_api_orders", "node_app_services_order_service") in edge_pairs
    assert ("node_app_api_orders", "node_app_models_order") in edge_pairs
    assert ("node_app_services_order_service", "node_app_models_order") in edge_pairs
    assert ("node_app_services_order_service", "node_app_workers_tasks") in edge_pairs

    # Verify specific imported symbols
    for edge in graph.edges:
        if edge.source_id == "node_app_api_orders" and edge.target_id == "node_app_services_order_service":
            assert any("OrderProcessor" in s for s in edge.symbols)
            assert edge.protocol == "IMPORT"


def test_manim_mapper_architecture_data(mock_codebase_repo):
    """Verify translation of CodebaseGraph into coordinate-anchored ArchitectureDiagramData."""
    service = CodebaseGraphService(max_nodes=20)
    graph = service.generate_graph(mock_codebase_repo)

    mapper = GraphToManimMapper(theme="midnight")
    arch_data = mapper.map_to_architecture_data(
        graph,
        title="Custom Architecture",
        subtitle="AST Flowchart",
    )

    assert isinstance(arch_data, ArchitectureDiagramData)
    assert arch_data.config.title == "Custom Architecture"
    assert arch_data.config.subtitle == "AST Flowchart"
    assert len(arch_data.nodes) == len(graph.nodes)
    assert len(arch_data.connections) == len(graph.edges)

    # Check that positions fall within valid 2D Manim camera bounds
    bounds = DEFAULT_CANVAS_BOUNDS
    for node in arch_data.nodes:
        x, y, z = node.position
        assert bounds["x_min"] - 0.5 <= x <= bounds["x_max"] + 0.5
        assert bounds["y_bottom"] - 0.5 <= y <= bounds["y_top"] + 0.5
        assert z == 0.0

    # Ensure curvature is calculated for connections
    for conn in arch_data.connections:
        assert isinstance(conn.curvature, float)
        assert conn.packet_color.startswith("#")


def test_manim_flowchart_scene_code_generation(mock_codebase_repo, tmp_path):
    """Verify standalone Manim Community Scene script generation and compilation syntax."""
    service = CodebaseGraphService(max_nodes=20)
    graph = service.generate_graph(mock_codebase_repo)

    script_code = generate_manim_flowchart_scene_code(
        graph,
        scene_name="TestGeneratedFlowScene",
        theme="nord",
    )

    assert "class TestGeneratedFlowScene(Scene):" in script_code
    assert "from manim import *" in script_code
    assert "def construct(self):" in script_code

    # Syntax verification via Python's AST parser
    parsed_ast = ast.parse(script_code)
    assert parsed_ast is not None

    # Bytecode compilation verification via py_compile
    script_file = tmp_path / "test_scene.py"
    script_file.write_text(script_code, encoding="utf-8")
    compiled = py_compile.compile(str(script_file), doraise=True)
    assert compiled is not None


def test_gemini_service_graph_ingestion(mock_codebase_repo):
    """Verify that GeminiScriptService ingests CodebaseGraph and references exact tables, routes, and services."""
    service = CodebaseGraphService(max_nodes=20)
    graph = service.generate_graph(mock_codebase_repo, repo_name="podman/helper-ai")

    gemini_svc = GeminiScriptService(api_key=None)
    result = gemini_svc.synthesize_script_and_architecture(
        codebase_pack="",
        repo_name="podman/helper-ai",
        codebase_graph=graph,
    )

    assert isinstance(result, ScriptSynthesisResult)
    assert result.model_used == "heuristic-multi-scene-graph-v2"
    assert isinstance(result.architecture_data, ArchitectureDiagramData)

    # Narration must cite the genuine classes and components found in the graph
    narration = result.narration_script
    assert "[Scene 1: Repository Overview & Directory Structure]" in narration
    assert "[Scene 2: System Architecture & Data Flow]" in narration
    assert "[Scene 3: Core Implementation & Logic Deep Dive]" in narration
    assert "[Scene 4: Lifecycle Summary & Conclusion]" in narration

    # Check exact database model cited
    assert "OrderRecord" in narration
    # Check exact route / gateway cited
    assert "OrderRouter" in narration or "list_orders" in narration
    # Check exact service processor cited
    assert "OrderProcessor" in narration
    # Check exact frontend component cited
    assert "OrderList" in narration

    # Verify Manim script syntax
    assert result.manim_script is not None
    assert "class ComprehensiveTutorialScene(Scene):" in result.manim_script
    assert "SCENE 1:" in result.manim_script
    assert "SCENE 2:" in result.manim_script
    assert "SCENE 3:" in result.manim_script
    assert "SCENE 4:" in result.manim_script

    parsed_ast = ast.parse(result.manim_script)
    assert parsed_ast is not None


def test_graph_service_node_pruning_and_limits(mock_codebase_repo):
    """Verify that max_nodes correctly limits the graph and prunes disconnected edges."""
    service = CodebaseGraphService(max_nodes=2)
    graph = service.generate_graph(mock_codebase_repo)

    assert len(graph.nodes) == 2
    surviving_ids = {n.id for n in graph.nodes}
    for edge in graph.edges:
        assert edge.source_id in surviving_ids
        assert edge.target_id in surviving_ids
