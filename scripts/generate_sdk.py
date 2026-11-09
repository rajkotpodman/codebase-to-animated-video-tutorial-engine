#!/usr/bin/env python3
"""Unified SDK Generator for CodeVideo AI (FastAPI -> TypeScript & Python).

Extracts the latest FastAPI OpenAPI 3.1 specification and runs the open-source
openapi-generator-cli tool to produce type-safe client SDKs.

Usage:
    python scripts/generate_sdk.py [--target {typescript,python,all}]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
OPENAPI_SPEC_PATH = PROJECT_ROOT / "openapi.json"
TS_OUTPUT_DIR = FRONTEND_DIR / "src" / "api"
PY_OUTPUT_DIR = PROJECT_ROOT / "sdk" / "python"


def export_openapi() -> Path:
    """Invokes scripts/export_openapi.py to extract openapi.json from FastAPI."""
    print("--> Step 1: Exporting FastAPI OpenAPI schema...")
    export_script = PROJECT_ROOT / "scripts" / "export_openapi.py"
    subprocess.run(
        [sys.executable, str(export_script), "--output", str(OPENAPI_SPEC_PATH)],
        check=True,
    )
    if not OPENAPI_SPEC_PATH.exists():
        raise FileNotFoundError(f"Expected OpenAPI spec was not generated at: {OPENAPI_SPEC_PATH}")
    return OPENAPI_SPEC_PATH


def resolve_npx() -> str:
    """Finds npx executable across platforms (npx.cmd on Windows, npx on POSIX)."""
    npx_bin = shutil.which("npx")
    if not npx_bin:
        raise RuntimeError("Node.js / npx is not installed or not in PATH. Please install Node.js 18+.")
    return npx_bin


def generate_typescript_sdk(spec_path: Path):
    """Generates modern type-safe TypeScript Fetch client in frontend/src/api."""
    print(f"--> Step 2a: Generating TypeScript SDK into {TS_OUTPUT_DIR}...")
    npx_bin = resolve_npx()

    cmd = [
        npx_bin,
        "openapi-generator-cli",
        "generate",
        "-i",
        str(spec_path),
        "-g",
        "typescript-fetch",
        "-o",
        str(TS_OUTPUT_DIR),
        "--additional-properties=supportsES6=true,typescriptThreePlus=true,useSingleRequestParameter=true,modelPropertyNaming=original",
    ]

    subprocess.run(cmd, cwd=str(FRONTEND_DIR), check=True, shell=(os.name == "nt"))  # nosec: B602
    print(f"TypeScript client SDK generated successfully in: {TS_OUTPUT_DIR}")


def generate_python_sdk(spec_path: Path):
    """Generates typed Python client SDK in sdk/python."""
    print(f"--> Step 2b: Generating Python SDK into {PY_OUTPUT_DIR}...")
    npx_bin = resolve_npx()

    cmd = [
        npx_bin,
        "openapi-generator-cli",
        "generate",
        "-i",
        str(spec_path),
        "-g",
        "python",
        "-o",
        str(PY_OUTPUT_DIR),
        "--additional-properties=packageName=codevideo_client,projectName=codevideo-client-sdk,packageVersion=0.1.0",
    ]

    subprocess.run(cmd, cwd=str(FRONTEND_DIR), check=True, shell=(os.name == "nt"))  # nosec: B602
    print(f"Python client SDK generated successfully in: {PY_OUTPUT_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Generate client SDKs from FastAPI OpenAPI schema.")
    parser.add_argument(
        "--target",
        "-t",
        choices=["typescript", "python", "all"],
        default="all",
        help="Target language client SDK to generate (default: all)",
    )
    args = parser.parse_args()

    spec = export_openapi()

    if args.target in ("typescript", "all"):
        generate_typescript_sdk(spec)

    if args.target in ("python", "all"):
        generate_python_sdk(spec)

    print("\nAll target SDKs generated successfully!")


if __name__ == "__main__":
    main()
