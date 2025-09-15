#!/usr/bin/env python3
"""Unified SARIF generation script.

Runs supported static analysis tools and consolidates output into a single SARIF file.
Tools attempted (auto-detected if config present):
  - ESLint (frontend)
  - Semgrep (root) if semgrep rules file exists
  - Pylint (python packages in repo)
  - Trivy (filesystem scan limited) OPTIONAL (skipped in dev for speed unless --trivy)

Exit codes:
  0 success (file written)
  1 unexpected internal error

The script is intentionally resilient: missing tools/configs yield empty SARIF runs rather than failure.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "sarif" / "current.sarif"
FRONTEND_DIR = ROOT / "frontend"
PY_PACKAGE_DIRS = [ROOT / "services", ROOT / "test_module"]

SARIF_VERSION = "2.1.0"

# Severity normalization mapping: tool severity -> SARIF level
SEVERITY_MAP = {
    "error": "error",
    "warn": "warning",
    "warning": "warning",
    "info": "note",
    "minor": "note",
    "medium": "warning",
    "major": "error",
    "critical": "error",
}


def run_cmd(cmd: List[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        cp = subprocess.CompletedProcess(cmd, returncode=127, stdout="", stderr="not found")
        return cp


def eslint_sarif() -> List[Dict[str, Any]]:
    if not (FRONTEND_DIR / "package.json").exists():
        return []
    if shutil.which("npx") is None:
        return []
    # Use npx eslint --format sarif .
    cmd = ["npx", "eslint", ".", "--format", "sarif", "--ext", ".js,.ts,.tsx"]
    proc = run_cmd(cmd, cwd=FRONTEND_DIR)
    if proc.returncode not in (0, 1):  # 1 means findings
        return []
    try:
        data = json.loads(proc.stdout)
        return data.get("runs", [])
    except json.JSONDecodeError:
        return []


def semgrep_sarif() -> List[Dict[str, Any]]:
    # Detect config
    if shutil.which("semgrep") is None:
        return []
    config_candidates = [ROOT / "semgrep.yml", ROOT / ".semgrep.yml"]
    config = next((c for c in config_candidates if c.exists()), None)
    if not config:
        return []
    cmd = ["semgrep", "--config", str(config), "--sarif", "--quiet", str(ROOT)]
    proc = run_cmd(cmd)
    if proc.returncode not in (0, 1):
        return []
    try:
        data = json.loads(proc.stdout)
        return data.get("runs", [])
    except json.JSONDecodeError:
        return []


def pylint_sarif() -> List[Dict[str, Any]]:
    if shutil.which("pylint") is None:
        return []
    # Collect python package paths
    python_targets: List[str] = []
    for base in PY_PACKAGE_DIRS:
        if base.exists():
            # naive: include .py files recursively
            python_targets.append(str(base))
    if not python_targets:
        return []
    with tempfile.NamedTemporaryFile(suffix=".json") as _:
        cmd = ["pylint", "--output-format=json", *python_targets]
        proc = run_cmd(cmd)
        if proc.returncode not in (0, 2, 4, 8, 16, 32):  # pylint uses bit-encoded rc; allow any
            return []
        try:
            issues = json.loads(proc.stdout)
        except json.JSONDecodeError:
            issues = []
        run = {
            "tool": {"driver": {"name": "pylint", "informationUri": "https://pylint.pycqa.org/", "version": "generated"}},
            "results": [
                {
                    "ruleId": i.get("symbol"),
                    "level": SEVERITY_MAP.get(i.get("type", "warning"), "warning"),
                    "message": {"text": i.get("message", "")},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": i.get("path")},
                                "region": {
                                    "startLine": i.get("line"),
                                    "startColumn": i.get("column"),
                                },
                            }
                        }
                    ],
                }
                for i in issues
            ],
        }
        return [run]


def trivy_sarif(target: Path) -> List[Dict[str, Any]]:
    if shutil.which("trivy") is None:
        return []
    cmd = ["trivy", "fs", "--format", "sarif", "--quiet", str(target)]
    proc = run_cmd(cmd)
    if proc.returncode not in (0, 1):
        return []
    try:
        data = json.loads(proc.stdout)
        return data.get("runs", [])
    except json.JSONDecodeError:
        return []


def consolidate(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"version": SARIF_VERSION, "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": runs}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate unified SARIF report")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--include-trivy", action="store_true", help="Include Trivy filesystem scan (slower)")
    args = parser.parse_args()

    runs: List[Dict[str, Any]] = []

    for producer in (eslint_sarif, semgrep_sarif, pylint_sarif):
        try:
            runs.extend(producer())
        except Exception:
            # Swallow tool-specific errors to keep pipeline resilient
            continue

    if args.include_trivy:
        try:
            runs.extend(trivy_sarif(ROOT))
        except Exception:
            pass

    # Ensure deterministic ordering by tool name
    for r in runs:
        r.setdefault("tool", {}).setdefault("driver", {}).setdefault("name", "unknown")
    runs.sort(key=lambda r: r.get("tool", {}).get("driver", {}).get("name", "zzz"))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(consolidate(runs), f, indent=2)

    print(f"Unified SARIF written to {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
