"""Manim Animation Engine for Codebase-to-Video Engine.

This package provides procedural animation generation for system architecture diagrams,
data flow pipelines, and codebase structural visualizations using Manim Community.
"""

from manim_engine.models import (
    ArchitectureDiagramData,
    ConnectionModel,
    NodeModel,
    NodeType,
    SceneConfig,
)
from manim_engine.base_template import (
    ArchitectureSceneGenerator,
    generate_scene_script,
    render_architecture_scene,
)

__all__ = [
    "ArchitectureDiagramData",
    "ConnectionModel",
    "NodeModel",
    "NodeType",
    "SceneConfig",
    "ArchitectureSceneGenerator",
    "generate_scene_script",
    "render_architecture_scene",
]
