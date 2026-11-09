"""Unit tests for AST codebase graph extraction and Manim flowchart mapping."""

import ast
import json
import py_compile
import tempfile
from pathlib import Path
import pytest

from app.services.graph_service import CodebaseGraph, CodebaseGraphService, GraphEdge, GraphNode
from app.services.graph_to_manim import (
    GraphToManimMapper,
    generate_manim_flowchart_scene_code,
)
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
        (api_dir / "routes.py").write_text(
            "from app.services.order_service import OrderProcessor\n"
            "from app.models.order import OrderModel\n\n"
            "class OrderApiRouter:\n"
            "    def handle_request(self):\n"
            "        pass\n",
            encoding="utf-8",
        )

        # 2. Service Layer
        svc_dir = repo_root / "app" / "services"
        svc_dir.mkdir(parents=True)
        (svc_dir / "order_service.py").write_text(
            "from app.models.order import OrderModel\n"
            "from app.workers.tasks import enqueue_order_task\n\n"
            "class OrderProcessor:\n"
            "    def process_order(self, order_id: str):\n"
            "        return True\n",
            encoding="utf-8",
        )

        # 3. Worker / Task Layer
        worker_dir = repo_root / "app" / "workers"
        worker_dir.mkdir(parents=True)
        (worker_dir / "tasks.py").write_text(
            "import redis\n\n"
            "def enqueue_order_task(payload):\n"
            "    pass\n",
            encoding="utf-8",
        )

        # 4. Database / Model Layer
        model_dir = repo_root / "app" / "models"
        model_dir.mkdir(parents=True)
        (model_dir / "order.py").write_text(
            "from pydantic import BaseModel\n\n"
            "class OrderModel(BaseModel):\n"
            "    id: str\n"
            "    amount: float\n",
            encoding="utf-8",
        )

        # 5. Frontend Client Component
        fe_dir = repo_root / "frontend" / "components"
        fe_dir.mkdir(parents=True)
        (fe_dir / "OrderView.tsx").write_text(
            "import React from 'react';\n"
            "import { OrderProcessor } from '../api';\n\n"
            "export function OrderView() {\n"
            "    return <div>Order</div>;\n"
            "}\n",
            encoding="utf-8",
        )

        yield repo_root


def test_codebase_graph_ast_extraction(mock_codebase_repo):
    service = CodebaseGraphService(max_nodes=20)
    graph = service.generate_graph(mock_codebase_repo)

    assert isinstance(graph, CodebaseGraph)
    assert graph.total_files >= 4
    assert graph.total_lines > 0
    assert len(graph.nodes) >= 4

    # Verify nodes
    labels = [n.label for n in graph.nodes]
    assert "routes.py" in labels
    assert "order_service.py" in labels
    assert "order.py" in labels
    assert "tasks.py" in labels

    # Verify classes and functions extraction
    order_node = next(n for n in graph.nodes if n.label == "order.py")
    assert "OrderModel" in order_node.classes
    assert order_node.kind == NodeType.DATABASE
    assert order_node.layer == 4

    svc_node = next(n for n in graph.nodes if n.label == "order_service.py")
    assert "OrderProcessor" in svc_node.classes
    assert "process_order" in svc_node.functions
    assert svc_node.kind == NodeType.BACKEND
    assert svc_node.layer == 2

    worker_node = next(n for n in graph.nodes if n.label == "tasks.py")
    assert "enqueue_order_task" in worker_node.functions
    assert worker_node.kind == NodeType.QUEUE
    assert worker_node.layer == 3

    # Verify edges were linked across imports
    assert len(graph.edges) >= 2
    edge_sources = [e.source_id for e in graph.edges]
    edge_targets = [e.target_id for e in graph.edges]
    assert svc_node.id in edge_sources
    assert order_node.id in edge_targets

    # Serialization test
    graph_dict = graph.model_dump()
    assert "nodes" in graph_dict
    assert "edges" in graph_dict
    assert json.loads(graph.model_dump_json())["total_files"] == graph.total_files


def test_graph_to_manim_mapping(mock_codebase_repo):
    service = CodebaseGraphService()
    graph = service.generate_graph(mock_codebase_repo)

    mapper = GraphToManimMapper(theme="midnight")
    arch_data = mapper.map_to_architecture_data(graph)

    assert isinstance(arch_data, ArchitectureDiagramData)
    assert len(arch_data.nodes) == len(graph.nodes)
    assert len(arch_data.connections) == len(graph.edges)

    # Every node must have explicit [x, y, z] coordinates
    for node in arch_data.nodes:
        assert node.position is not None
        assert len(node.position) == 3
        # Coordinates must lie within visible Manim frame boundaries
        assert -6.0 <= node.position[0] <= 6.0
        assert -3.5 <= node.position[1] <= 3.0

    # Nodes with different layers must have distinct horizontal coordinates
    node_by_label = {n.label: n for n in arch_data.nodes}
    assert node_by_label["routes.py"].position[0] < node_by_label["order_service.py"].position[0]
    assert node_by_label["order_service.py"].position[0] < node_by_label["order.py"].position[0]

    # Verify connections have animated packets and protocol labels
    for conn in arch_data.connections:
        assert conn.source_id != conn.target_id
        assert conn.animated is True
        assert conn.packet_color.startswith("#")


def test_generate_manim_flowchart_scene_code(mock_codebase_repo):
    service = CodebaseGraphService()
    graph = service.generate_graph(mock_codebase_repo)

    scene_code = generate_manim_flowchart_scene_code(graph, scene_name="TestRepoFlowchartScene")

    assert "class TestRepoFlowchartScene(Scene):" in scene_code
    assert "self.camera.background_color" in scene_code
    assert "RoundedRectangle" in scene_code
    assert "FadeIn" in scene_code
    assert "MoveAlongPath" in scene_code

    # Verify Python syntax validity with AST
    parsed_ast = ast.parse(scene_code)
    assert parsed_ast is not None

    # Verify syntax compilation with py_compile
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp_py:
        tmp_py.write(scene_code)
        tmp_py_path = tmp_py.name

    try:
        compiled = py_compile.compile(tmp_py_path, doraise=True)
        assert compiled is not None
    finally:
        if Path(tmp_py_path).exists():
            Path(tmp_py_path).unlink()

