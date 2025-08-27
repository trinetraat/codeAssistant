from pathlib import Path
from typing import Dict

SYSTEM_BASE = """You write single-file, runnable code. Output ONLY code (no markdown fences, no prose).
- Include all imports.
- Python/PySpark: __main__ guard + argparse.
- SQL: executable statements; include DDL if needed.
- Header comment: purpose, deps, run steps, pip installs if any.
- Prefer stdlib; justify new deps in header.
- Read large inputs from disk via provided PATHS; do not inline big files.
"""

MODE_HINTS = {
    "code": "",
    "azure-func": "Target Azure Functions (Python 3.11). Produce function.py, function.json content inline; explain in header how to place files in a Functions project. HTTP trigger default.",
    "pipeline": "Produce Azure Pipelines YAML (CI/CD) for building/testing/deploying a Python project. Include stages: build, test, package, deploy (parameterized).",
    "fabric": "Write code suitable for Microsoft Fabric ingestion/transform: pandas/pyarrow parquet, UTC datetimes, SQL for reporting. Avoid heavy deps.",
    "api": "Write a clean API client module (requests/httpx) with retries, rate-limit handling, and typed responses. No secrets in code; read from env.",
    "deploy": "Produce minimal deploy script (az CLI or bicep/yaml) with parameterization. Idempotent where possible.",
}

def build_system_prompt(mode: str) -> str:
    return SYSTEM_BASE + ("\n" + MODE_HINTS.get(mode, ""))

def build_user_brief(requirement: str, language: str, pinned_spec_head: str, hint_paths: str) -> str:
    return f"""TASK:
{requirement}

TARGET_LANG: {language}

CONSTRAINTS:
- Single, self-contained file.
- Fabric/Synapse-friendly outputs if data work (UTC, parquet via pyarrow).
- Read from disk using PATHS if needed (do not inline big JSON/CSV).
- Return ONLY code.

PINNED_SPEC (head if present):
{pinned_spec_head or "(none)"}

AVAILABLE_PATHS (non-authoritative hints for the code to read at runtime):
{hint_paths or "(none)"}"""