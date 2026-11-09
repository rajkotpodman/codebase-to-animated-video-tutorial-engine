"""Unit and integration tests for CodebaseIngestionService."""

import asyncio
import os
import tempfile
from pathlib import Path
import pytest

from app.services.ingestion_service import (
    CodebaseIngestionService,
    GitCloneError,
    IngestionError,
    IngestionOptions,
    InvalidRepositoryUrlError,
    PythonCodebasePackager,
    RepoUrlParser,
    RepomixCliRunner,
)

# -----------------------------------------------------------------------------
# RepoUrlParser Tests
# -----------------------------------------------------------------------------


def test_repo_url_parser_valid_https():
    norm_url, name, branch = RepoUrlParser.parse("https://github.com/yamadashy/repomix")
    assert norm_url == "https://github.com/yamadashy/repomix.git"
    assert name == "yamadashy/repomix"
    assert branch is None


def test_repo_url_parser_with_dot_git():
    norm_url, name, branch = RepoUrlParser.parse("https://github.com/facebook/react.git")
    assert norm_url == "https://github.com/facebook/react.git"
    assert name == "facebook/react"
    assert branch is None


def test_repo_url_parser_with_tree_branch():
    norm_url, name, branch = RepoUrlParser.parse("https://github.com/encode/fastapi/tree/feature-v2")
    assert norm_url == "https://github.com/encode/fastapi.git"
    assert name == "encode/fastapi"
    assert branch == "feature-v2"


def test_repo_url_parser_shorthand():
    norm_url, name, branch = RepoUrlParser.parse("pallets/flask")
    assert norm_url == "https://github.com/pallets/flask.git"
    assert name == "pallets/flask"
    assert branch is None


def test_repo_url_parser_rejects_command_injection():
    with pytest.raises(InvalidRepositoryUrlError):
        RepoUrlParser.parse("--upload-pack=evil")

    with pytest.raises(InvalidRepositoryUrlError):
        RepoUrlParser.parse("https://github.com/foo/bar; rm -rf /")

    with pytest.raises(InvalidRepositoryUrlError):
        RepoUrlParser.parse("")


# -----------------------------------------------------------------------------
# IngestionOptions Tests
# -----------------------------------------------------------------------------


def test_ingestion_options_default_ignores():
    opts = IngestionOptions(custom_ignore_patterns=["custom_folder/**"])
    ignores = opts.effective_ignore_patterns
    assert "node_modules/**" in ignores
    assert ".git/**" in ignores
    assert "dist/**" in ignores
    assert "__pycache__/**" in ignores
    assert "target/**" in ignores
    assert "custom_folder/**" in ignores


# -----------------------------------------------------------------------------
# PythonCodebasePackager (Fallback / Native) Tests
# -----------------------------------------------------------------------------


def test_python_codebase_packager_ignores_and_compresses():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Create valid source file
        src_dir = root / "app"
        src_dir.mkdir()
        main_py = src_dir / "service.py"
        main_py.write_text(
            '"""Module docstring."""\n\n'
            "def process_data(data: str) -> bool:\n"
            '    """Process input string."""\n'
            "    nested_var = 123\n"
            "    return True\n\n"
            "class VideoPipeline:\n"
            '    """Pipeline class."""\n'
            "    def run(self):\n"
            "        pass\n",
            encoding="utf-8",
        )

        # Create build directory that should be ignored
        nm_dir = root / "node_modules" / "some_pkg"
        nm_dir.mkdir(parents=True)
        (nm_dir / "index.js").write_text("console.log('ignore me');", encoding="utf-8")

        # Create pycache that should be ignored
        pycache = src_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "service.cpython-311.pyc").write_bytes(b"dummy bytecode")

        # Create a binary image that should be ignored
        (src_dir / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")

        out_file = root / "output.md"
        opts = IngestionOptions(compress=True)

        stats = PythonCodebasePackager.pack(root, out_file, opts)

        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")

        # Check that service.py was packed
        assert "## File: app/service.py" in content
        assert "class VideoPipeline:" in content
        assert "def process_data(data: str) -> bool:" in content

        # Check compression: internal implementation lines like nested_var should NOT be present
        assert "nested_var = 123" not in content

        # Check heavy build directories are excluded
        assert "node_modules" not in content
        assert "some_pkg" not in content
        assert "__pycache__" not in content
        assert "logo.png" not in content

        assert stats["total_files"] == 1


# -----------------------------------------------------------------------------
# Repomix CLI Runner Tests
# -----------------------------------------------------------------------------


def test_repomix_cli_runner_detection_and_execution():
    assert RepomixCliRunner.is_available() is True

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "hello.py").write_text("print('hello world')", encoding="utf-8")

        # Ignored dir
        (root / "dist").mkdir()
        (root / "dist" / "bundle.js").write_text("var x = 1;", encoding="utf-8")

        out_file = root / "repomix_out.md"
        opts = IngestionOptions(style="markdown", compress=True)

        stats = RepomixCliRunner.run(root, out_file, opts)

        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "hello.py" in content
        assert "bundle.js" not in content
        assert stats["total_files"] >= 1


# -----------------------------------------------------------------------------
# CodebaseIngestionService Tests
# -----------------------------------------------------------------------------


def test_ingest_local_directory_with_repomix():
    service = CodebaseIngestionService()
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        src = root / "src"
        src.mkdir()
        (src / "core.py").write_text("class VideoEngine:\n    def build(self):\n        pass\n", encoding="utf-8")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "unwanted_lib.js").write_text("console.log('ignored');", encoding="utf-8")

        result = service.ingest_local_directory(root, repo_name="test_engine")

        assert result.repo_name == "test_engine"
        assert result.total_files == 1
        assert "VideoEngine" in result.content
        assert "unwanted_lib.js" not in result.content
        assert "## File: node_modules" not in result.content
        assert result.directory_tree != ""
        assert "src" in result.directory_tree
        assert result.output_path.exists()

        summary = result.get_summary()
        assert "test_engine" in summary
        result.cleanup()


def test_ingest_local_directory_forced_native_engine():
    service = CodebaseIngestionService()
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "calc.py").write_text(
            'def add(a: int, b: int) -> int:\n    """Add."""\n    return a + b\n', encoding="utf-8"
        )

        opts = IngestionOptions(engine="python-native", compress=True)
        result = service.ingest_local_directory(root, options=opts, repo_name="native_test")

        assert result.engine_used == "python-native"
        assert result.total_files == 1
        assert "def add(a: int, b: int) -> int:" in result.content


@pytest.mark.asyncio
async def test_async_ingest_local_directory():
    service = CodebaseIngestionService()
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "script.py").write_text("x = 42\n", encoding="utf-8")

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: service.ingest_local_directory(root, repo_name="async_test"))
        assert result.total_files == 1
        assert "x = 42" in result.content
        result.cleanup()


def test_public_repo_cloning_and_ingestion():
    """Integration test with a real small public GitHub repo."""
    service = CodebaseIngestionService()
    opts = IngestionOptions(clone_depth=1, compress=True)

    # octocat/Hello-World is GitHub's canonical test repository (very small)
    result = service.ingest_repository("octocat/Hello-World", options=opts)

    assert result.repo_name == "octocat/Hello-World"
    assert result.branch in ("master", "main")
    assert len(result.commit_sha) == 40
    assert result.total_files >= 1
    assert "Hello World" in result.content
    assert result.output_path.exists()
    result.cleanup()
