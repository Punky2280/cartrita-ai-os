#!/usr/bin/env python3
"""SARIF baseline comparator.

Given a baseline SARIF and a current SARIF, classify results into:
  - new: present in current, absent in baseline
  - fixed: present in baseline, absent in current
  - persisted: present in both

A result identity key is constructed from (ruleId, level, message.text, primary location URI + startLine + startColumn).
This is a pragmatic heuristic; can be refined later (e.g., ignoring column, fuzzy message matching).

Outputs:
  1. JSON summary (machine-readable)
  2. Markdown report (human-readable)
  3. Exit code 0 always (non-blocking gate); future enhancement may add threshold-based exit.

Severity normalization maps tool-specific levels into: error | warning | note | none.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

SARIF_LEVELS = {"error", "warning", "note", "none"}

NORMALIZE = {
    "critical": "error",
    "high": "error",
    "major": "error",
    "medium": "warning",
    "moderate": "warning",
    "minor": "note",
    "low": "note",
    "info": "note",
    "warning": "warning",
    "error": "error",
    "note": "note",
    "none": "none",
}


def load_runs(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("runs", []) or []
    except Exception:
        return []


def extract_results(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for run in runs:
        for res in run.get("results", []) or []:
            out.append(res)
    return out


def normalize_level(level: str | None) -> str:
    if not level:
        return "note"
    return NORMALIZE.get(level.lower(), "note")


def result_key(res: Dict[str, Any], ignore_column: bool = False) -> Tuple[Any, ...]:
    rule = res.get("ruleId") or res.get("rule", {}).get("id")
    lvl = normalize_level(res.get("level"))
    msg = (res.get("message") or {}).get("text") or ""
    locs = res.get("locations") or []
    if locs:
        phys = locs[0].get("physicalLocation", {})
        uri = (phys.get("artifactLocation") or {}).get("uri")
        region = phys.get("region") or {}
        line = region.get("startLine")
        col = region.get("startColumn")
    else:
        uri = None
        line = None
        col = None
    if ignore_column:
        col = None
    return (rule, lvl, msg, uri, line, col)


def classify(baseline: List[Dict[str, Any]], current: List[Dict[str, Any]], ignore_column: bool):
    base_map = {result_key(r, ignore_column): r for r in baseline}
    curr_map = {result_key(r, ignore_column): r for r in current}

    new_keys = [k for k in curr_map.keys() if k not in base_map]
    fixed_keys = [k for k in base_map.keys() if k not in curr_map]
    persisted_keys = [k for k in curr_map.keys() if k in base_map]

    return (
        [curr_map[k] for k in new_keys],
        [base_map[k] for k in fixed_keys],
        [curr_map[k] for k in persisted_keys],
    )


def severity_counts(results: List[Dict[str, Any]]):
    counts = {"error": 0, "warning": 0, "note": 0, "none": 0}
    for r in results:
        counts[normalize_level(r.get("level"))] += 1
    return counts


def generate_markdown(summary: Dict[str, Any]) -> str:
    lines = ["# Static Analysis Diff Report", "", "## Overview", ""]
    lines.append(f"New findings: {summary['counts']['new']['total']}")
    lines.append(f"Fixed findings: {summary['counts']['fixed']['total']}")
    lines.append(f"Persisted findings: {summary['counts']['persisted']['total']}")
    lines.append("")

    def block(name: str):
        cat = summary['details'][name]
        if not cat:
            lines.append(f"### {name.capitalize()} (0)")
            lines.append("")
            return
        lines.append(f"### {name.capitalize()} ({len(cat)})")
        lines.append("")
        for r in cat[:100]:  # cap list
            k = result_key(r)
            rule, lvl, msg, uri, line, _col = k
            loc = f"{uri}:{line}" if uri else "(no location)"
            lines.append(f"- `{lvl}` `{rule}` {loc} - {msg[:140]}")
        if len(cat) > 100:
            lines.append(f"- ... ({len(cat) - 100} more omitted)")
        lines.append("")
    for section in ("new", "fixed", "persisted"):
        block(section)
    return "\n".join(lines)


def main():  # noqa: D401
    parser = argparse.ArgumentParser(description="Compare SARIF baseline vs current")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--json-output", type=Path, default=Path("sarif/diff-summary.json"))
    parser.add_argument("--md-output", type=Path, default=Path("sarif/diff-report.md"))
    parser.add_argument("--ignore-column", action="store_true", help="Ignore column when matching results")
    parser.add_argument("--fail-on-new-errors", action="store_true", help="Exit non-zero if any new 'error' level findings")
    parser.add_argument("--max-new-warnings", type=int, default=None, help="Fail if new warnings exceed this count")
    parser.add_argument("--max-new-total", type=int, default=None, help="Fail if total new findings exceed this count")
    args = parser.parse_args()

    base_runs = load_runs(args.baseline)
    curr_runs = load_runs(args.current)

    base_results = extract_results(base_runs)
    curr_results = extract_results(curr_runs)

    new, fixed, persisted = classify(base_results, curr_results, args.ignore_column)

    summary = {
        "counts": {
            "new": {"total": len(new), **severity_counts(new)},
            "fixed": {"total": len(fixed), **severity_counts(fixed)},
            "persisted": {"total": len(persisted), **severity_counts(persisted)},
        },
        "details": {"new": new, "fixed": fixed, "persisted": persisted},
    }

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = generate_markdown(summary)
    args.md_output.write_text(md, encoding="utf-8")

    print(f"Diff summary JSON written: {args.json_output}")
    print(f"Markdown report written: {args.md_output}")

    exit_code = 0
    if args.fail_on_new_errors and summary['counts']['new']['error'] > 0:
        exit_code = 2
    if args.max_new_warnings is not None and summary['counts']['new']['warning'] > args.max_new_warnings:
        exit_code = 3
    if args.max_new_total is not None and summary['counts']['new']['total'] > args.max_new_total:
        exit_code = 4

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
