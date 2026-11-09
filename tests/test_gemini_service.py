"""Unit tests for Gemini AI script and architecture synthesis service."""

import ast
import pytest
from app.services.gemini_service import GeminiScriptService, ScriptSynthesisResult
from manim_engine.models import ArchitectureDiagramData, NodeType


def test_gemini_heuristic_synthesis():
    service = GeminiScriptService(api_key=None)  # Tests heuristic mode

    sample_pack = (
        "# Directory Structure\n"
        "```\n"
        "app/\n"
        "  main.py\n"
        "  services/\n"
        "    fastapi_app.py\n"
        "    postgres_db.py\n"
        "    redis_cache.py\n"
        "```\n"
        "## File: app/main.py\n"
        "from fastapi import FastAPI\n"
        "import redis\n"
        "import asyncpg\n"
    )

    result = service.synthesize_script_and_architecture(
        codebase_pack=sample_pack,
        repo_name="my-fastapi-service",
    )

    assert isinstance(result, ScriptSynthesisResult)
    assert isinstance(result.architecture_data, ArchitectureDiagramData)
    assert len(result.architecture_data.nodes) >= 3
    assert len(result.architecture_data.connections) >= 2

    # Check that client, backend, and db nodes exist
    kinds = [n.kind for n in result.architecture_data.nodes]
    assert NodeType.FRONTEND in kinds or NodeType.CLIENT in kinds
    assert NodeType.BACKEND in kinds
    assert NodeType.DATABASE in kinds

    # Check narration script has all 4 distinct scenes
    assert "[Scene 1:" in result.narration_script
    assert "[Scene 2:" in result.narration_script
    assert "[Scene 3:" in result.narration_script
    assert "[Scene 4:" in result.narration_script

    # Check that multi-scene Manim script was generated and parses as valid Python
    assert result.manim_script is not None
    assert "class ComprehensiveTutorialScene(Scene):" in result.manim_script
    assert "SCENE 1:" in result.manim_script
    assert "SCENE 2:" in result.manim_script
    assert "SCENE 3:" in result.manim_script
    assert "SCENE 4:" in result.manim_script

    # Validate AST parsing
    parsed_ast = ast.parse(result.manim_script)
    assert parsed_ast is not None
