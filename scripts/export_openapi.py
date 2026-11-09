#!/usr/bin/env python3
"""Export FastAPI OpenAPI 3.1 schema to JSON.

Allows generating client SDKs, API documentation, and Postman collections
without needing a live running server instance.

Usage:
    python scripts/export_openapi.py [--output openapi.json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to Python search path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Disable external telemetry and enforce testing mode for clean schema generation
os.environ["TESTING"] = "true"
os.environ["SENTRY_DSN"] = ""
os.environ["ENABLE_METRICS"] = "true"


def export_schema(output_path: Path) -> Path:
    """Extract the OpenAPI specification from the FastAPI application and save to disk."""
    from app.main import app

    openapi_data = app.openapi()

    # Ensure parent directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Successfully exported OpenAPI schema to: {output_path} ({len(openapi_data.get('paths', {}))} endpoints)")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI JSON schema.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=PROJECT_ROOT / "openapi.json",
        help="Path where openapi.json should be written (default: ./openapi.json)",
    )
    args = parser.parse_args()
    export_schema(args.output)


if __name__ == "__main__":
    main()
