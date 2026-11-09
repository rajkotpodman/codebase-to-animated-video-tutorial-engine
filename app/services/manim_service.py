"""Manim Video Rendering Service for Multi-Scene Codebase Walkthroughs.

Provides high-resolution rendering, syntax auto-correction, and fallback execution
for Gemini-generated multi-scene Manim Python scripts and architectural models.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union

from manim_engine.base_template import (
    ManimCodeSanitizer,
    ManimRenderService,
    generate_scene_script,
    render_architecture_scene,
)
from manim_engine.models import ArchitectureDiagramData

logger = logging.getLogger("manim_service")

__all__ = [
    "ManimRenderService",
    "ManimCodeSanitizer",
    "render_architecture_scene",
    "generate_scene_script",
]

