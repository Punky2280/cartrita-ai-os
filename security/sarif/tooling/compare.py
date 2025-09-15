#!/usr/bin/env python3
"""
SARIF Baseline Comparator

Purpose:
  Compare a newly generated SARIF report against a stored baseline to determine
  whether new issues have been introduced ("regressions") while ignoring
  pre‑existing findings. Designed to integrate into CI prior to merge gating.

Behavior:
  - If no baseline file exists, exits with code 0 (bootstrap mode) and can optionally
    copy the current SARIF to become the baseline when --write-baseline is passed.
  - Parses SARIF v2.1.0 JSON, indexing results by a stable fingerprint key
    (ruleId + partialFingerprints if present else ruleId + location span tuple).
  - Filters out suppressed results (kind == "pass" or level == "note" when below threshold).
  - Severity threshold mapping: error > warning > note. Default threshold=warning means
    notes are ignored for regression gating.
  - Outputs a concise regression summary and optionally a JSON file with details.
  - Exits non‑zero (2) if any new issues at/above threshold are detected.

Exit Codes:
  0: Success / no regressions (or bootstrap with no baseline)
  1: Usage / argument error
  2: Regressions detected (block merge)
  3: SARIF parse error / unexpected structure

Usage Examples:
  python security/sarif/tooling/compare.py \
      --baseline security/sarif/baseline.sarif \
      --current codacy.sarif \
      --threshold warning \
      --output regression_report.json

  Bootstrap first baseline (after manual triage):
  python security/sarif/tooling/compare.py --baseline security/sarif/baseline.sarif \
      --current codacy.sarif --write-baseline
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

SEVERITY_ORDER = {"error": 3, "warning": 2, "note": 1, "none": 0}
# Optional Codacy category -> SARIF level normalization. If SARIF already has
# a level we keep it; otherwise map known categories heuristically.
CODACY_CATEGORY_LEVEL = {
    # High impact
    "Security": "error",
    "ErrorProne": "error",
    # Medium
    "Performance": "warning",
    "Complexity": "warning",
    "BestPractice": "warning",
    # Low / informational
    "CodeStyle": "note",
    "Documentation": "note",
    "UnusedCode": "note",
    "Compatibility": "note",
}
DEFAULT_THRESHOLD = "warning"


def load_sarif(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get("version") != "2.1.0":
            raise ValueError("Unsupported or missing SARIF version (expected 2.1.0)")
        return data
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: Failed to load SARIF '{path}': {e}", file=sys.stderr)
        sys.exit(3)


def iter_results(sarif: Dict[str, Any]) -> List[Dict[str, Any]]:
    runs = sarif.get("runs") or []
    results: List[Dict[str, Any]] = []
    for run in runs:
        for res in run.get("results", []) or []:
            if isinstance(res, dict):
                results.append(res)
    return results


def severity_of(result: Dict[str, Any]) -> str:
    # SARIF level: error | warning | note | none
    level = result.get("level") or result.get("properties", {}).get("level")
    if level in SEVERITY_ORDER:
        return level  # already normalized
    # Attempt category-based mapping from Codacy metadata if present
    props = result.get("properties") or {}
    category = props.get("category") or props.get("codacyCategory")
    if isinstance(category, str):
        mapped = CODACY_CATEGORY_LEVEL.get(category, "warning")
        return mapped
    return "warning"  # conservative default


def fingerprint_key(result: Dict[str, Any]) -> str:
    rule_id = result.get("ruleId") or "<no-rule>"
    partial = result.get("partialFingerprints") or {}
    if partial:
        # Stable ordering of keys
        pieces = [f"{k}={partial[k]}" for k in sorted(partial.keys())]
        return f"rule:{rule_id}|fp:{'|'.join(pieces)}"
    # Fallback: rule + primary location region tuple
    locs = result.get("locations") or []
    if locs:
        phys = locs[0].get("physicalLocation", {})
        artifact = phys.get("artifactLocation", {}).get("uri", "<no-uri>")
        region = phys.get("region", {})
        start_line = region.get("startLine", 0)
        start_col = region.get("startColumn", 0)
        return f"rule:{rule_id}|loc:{artifact}:{start_line}:{start_col}"
    return f"rule:{rule_id}|orph"


def filter_threshold(results: List[Dict[str, Any]], threshold: str) -> List[Dict[str, Any]]:
    min_rank = SEVERITY_ORDER.get(threshold, SEVERITY_ORDER[DEFAULT_THRESHOLD])
    return [r for r in results if SEVERITY_ORDER.get(severity_of(r), 0) >= min_rank]


def compare(baseline: List[Dict[str, Any]], current: List[Dict[str, Any]], threshold: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (regressions, fixed_issues) lists filtered by threshold."""
    base_filtered = filter_threshold(baseline, threshold)
    cur_filtered = filter_threshold(current, threshold)

    base_map: Dict[str, Dict[str, Any]] = {fingerprint_key(r): r for r in base_filtered}
    cur_map: Dict[str, Dict[str, Any]] = {fingerprint_key(r): r for r in cur_filtered}

    regressions: List[Dict[str, Any]] = []
    fixed: List[Dict[str, Any]] = []

    # New issues (present in current, absent in baseline)
    for key, r in cur_map.items():
        if key not in base_map:
            regressions.append(r)

    # Fixed issues (present in baseline, absent now)
    for key, r in base_map.items():
        if key not in cur_map:
            fixed.append(r)

    return regressions, fixed


def summarize(regressions: List[Dict[str, Any]], fixed: List[Dict[str, Any]]) -> str:
    if not regressions:
        base = "No new issues above threshold."
    else:
        lines = ["New issues (regressions) detected:"]
        for r in regressions[:50]:  # cap output
            key = fingerprint_key(r)
            level = severity_of(r)
            message = (r.get("message") or {}).get("text") or "<no message>"
            lines.append(f"- {level.upper()} {r.get('ruleId')} :: {message[:140]} :: {key}")
        if len(regressions) > 50:
            lines.append(f"... (+{len(regressions) - 50} more)")
        base = "\n".join(lines)
    if fixed:
        base += f"\nFixed issues count: {len(fixed)}"
    return base


def write_json(path: Path, regressions: List[Dict[str, Any]], fixed: List[Dict[str, Any]], threshold: str) -> None:
    data = {
        "threshold": threshold,
        "regression_count": len(regressions),
        "fixed_count": len(fixed),
        "regressions": regressions,
        "fixed": fixed,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare current SARIF vs baseline to find new issues.")
    p.add_argument("--baseline", required=True, help="Path to baseline SARIF file.")
    p.add_argument("--current", required=True, help="Path to newly generated SARIF file.")
    p.add_argument("--threshold", default=DEFAULT_THRESHOLD, choices=list(SEVERITY_ORDER.keys()), help="Minimum severity considered for regressions.")
    p.add_argument("--output", help="Optional path to write JSON regression report.")
    p.add_argument("--write-baseline", action="store_true", help="If no baseline exists, write current as new baseline (bootstrap).")
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    baseline_path = Path(args.baseline)
    current_path = Path(args.current)

    if not current_path.exists():
        print(f"ERROR: Current SARIF file not found: {current_path}", file=sys.stderr)
        return 1

    if not baseline_path.exists():
        print(f"INFO: Baseline not found at {baseline_path} (bootstrap mode)")
        if args.write_baseline:
            try:
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                data = current_path.read_text(encoding="utf-8")
                baseline_path.write_text(data, encoding="utf-8")
                print(f"INFO: Wrote new baseline from current ({current_path} -> {baseline_path})")
            except Exception as e:  # noqa: BLE001
                print(f"ERROR: Failed to write baseline: {e}", file=sys.stderr)
                return 3
        return 0

    baseline_sarif = load_sarif(baseline_path)
    current_sarif = load_sarif(current_path)

    baseline_results = iter_results(baseline_sarif)
    current_results = iter_results(current_sarif)

    regressions, fixed = compare(baseline_results, current_results, args.threshold)

    print(summarize(regressions, fixed))

    if args.output:
        try:
            write_json(Path(args.output), regressions, fixed, args.threshold)
            print(f"INFO: Regression report written to {args.output}")
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: Failed writing output report: {e}", file=sys.stderr)

    if len(regressions) > 0:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
