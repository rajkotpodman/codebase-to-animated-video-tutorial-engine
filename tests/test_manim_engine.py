"""Unit tests for Manim Community Animation Engine."""

import json
import py_compile
import tempfile
from pathlib import Path
import pytest

from manim_engine.models import (
    ArchitectureDiagramData,
    ConnectionModel,
    NodeModel,
    NodeType,
    SceneConfig,
)
from manim_engine.base_template import (
    ArchitectureSceneGenerator,
    LayeredLayoutEngine,
    ManimCodeSanitizer,
    ManimRenderService,
    generate_scene_script,
)


def test_architecture_diagram_data_validation():
    data = ArchitectureDiagramData(
        config=SceneConfig(title="Test Engine", theme="midnight"),
        nodes=[
            NodeModel(id="client", label="Web Client", kind=NodeType.FRONTEND, layer=0),
            NodeModel(id="server", label="API Backend", kind=NodeType.BACKEND, layer=1),
            NodeModel(id="db", label="Postgres DB", kind=NodeType.DATABASE, layer=2),
        ],
        connections=[
            ConnectionModel(source_id="client", target_id="server", label="REST /query", protocol="HTTPS"),
            ConnectionModel(source_id="server", target_id="db", label="SQL Query", protocol="TCP"),
        ],
    )
    assert len(data.nodes) == 3
    assert len(data.connections) == 2
    assert data.nodes[0].kind == NodeType.FRONTEND


def test_layered_layout_engine_positions():
    nodes = [
        NodeModel(id="fe1", label="Frontend 1", kind=NodeType.FRONTEND, layer=0),
        NodeModel(id="fe2", label="Frontend 2", kind=NodeType.FRONTEND, layer=0),
        NodeModel(id="be", label="Backend", kind=NodeType.BACKEND, layer=1),
        NodeModel(id="db", label="Database", kind=NodeType.DATABASE, layer=2),
    ]
    positions = LayeredLayoutEngine.compute_positions(nodes)
    assert len(positions) == 4
    # Layer 0 nodes should be to the left of Layer 1, which is to the left of Layer 2
    assert positions["fe1"][0] < positions["be"][0]
    assert positions["be"][0] < positions["db"][0]
    # fe1 and fe2 should have different y coordinates
    assert positions["fe1"][1] != positions["fe2"][1]


def test_generate_scene_script_and_syntax_compilation():
    sample_json_path = Path(__file__).parent.parent / "manim_engine" / "sample_architecture.json"
    assert sample_json_path.exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_script = Path(tmp_dir) / "test_scene.py"
        code, written_path = generate_scene_script(sample_json_path, out_script)

        assert written_path == out_script
        assert out_script.exists()
        assert "class ArchitectureFlowScene(Scene):" in code
        assert "MoveAlongPath" in code
        assert "ShowPassingFlash" in code

        # Compile with Python py_compile to verify syntax
        compiled = py_compile.compile(str(out_script), doraise=True)
        assert compiled is not None


def test_manim_sanitizer_and_multi_scene_detection():
    # 1. Test markdown fence stripping & obsolete method auto-corrector
    raw_ai_code = (
        "```python\n"
        "class FileTreeScene(Scene):\n"
        "    def construct(self):\n"
        "        t = Text('Hello')\n"
        "        self.play(ShowCreation(t))\n\n"
        "class ArchitectureFlowScene(Scene):\n"
        "    def construct(self):\n"
        "        pass\n\n"
        "class CoreLogicScene(Scene):\n"
        "    def construct(self):\n"
        "        pass\n\n"
        "class ConclusionScene(Scene):\n"
        "    def construct(self):\n"
        "        pass\n"
        "```"
    )

    is_valid, corrected, err = ManimCodeSanitizer.auto_correct_script(raw_ai_code)
    assert is_valid is True
    assert "from manim import *" in corrected
    assert "ShowCreation" not in corrected
    assert "Create" in corrected

    # 2. Test multi-scene detection
    scenes = ManimCodeSanitizer.detect_scene_classes(corrected)
    assert len(scenes) == 4
    assert scenes == ["FileTreeScene", "ArchitectureFlowScene", "CoreLogicScene", "ConclusionScene"]
