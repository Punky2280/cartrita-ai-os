# SARIF Baseline & Diff Strategy

## Purpose

Reduce noise from pre-existing issues so that new / regressed findings surface clearly while maintaining full historical audit trail.

## Principles

1. No deletion of historical SARIF artifacts (retain full fidelity for forensics).
1. Baseline capture occurs only once after initial triage labeling (not before triage—avoid cementing transient issues).
1. New issues fail quality gate; pre-baseline issues tracked for remediation but do not block merges.
1. Baseline file must be immutable (pinned in history) except for explicit refresh procedure.
1. Refresh allowed only after: (a) >90% of baseline issues resolved OR (b) structural ruleset change.

## Workflow Integration (Implemented Partial)

1. Initial Run: Current `results.sarif` uploaded & archived (status quo).
1. Triage Phase: Label or categorize issues externally (Codacy UI) and resolve low-hanging fixes.
1. Baseline Commit:
   - Copy most recent stable SARIF to `security/sarif/baseline.sarif`.
   - Add note in `CHANGELOG.md` under Security about baseline adoption.
1. Diff Runs (Post-Baseline):

- Workflow invokes `security/sarif/tooling/compare.py` directly after Codacy SARIF generation.
- Script arguments: `--baseline security/sarif/baseline.sarif --current results.sarif --threshold warning --output regressions.json`.
- If baseline missing: script exits 0 (bootstrap mode) and does NOT fail gate (baseline not auto-written in CI; adoption requires explicit PR).
- If new issues ≥ threshold appear: script exits 2; workflow marks `regressions=true` and quality gate fails.

1. Reporting:

- Upload `regressions.json` artifact when regressions present.
- Emit summary step (future enhancement) into job log.

## Directory Layout (Proposed)

```md
security/
  sarif/
    baseline.sarif        # committed immutable baseline
    tooling/compare.py    # comparison utility
```

## Comparison Logic Outline (`compare.py` - Implemented)

Algorithm steps:

1. Load `baseline.sarif` & new `results.sarif`.
1. Index baseline results by stable fingerprint (prefer SARIF `partialFingerprints.primaryLocationLineHash` or `ruleId` + `location` tuple fallback).
1. For each new result not in baseline index → classify as NEW.
1. For any baseline result missing now → classify as FIXED (informational; never fail gate).
1. Output JSON structure:

```json
{
  "new": [ { "ruleId": "...", "severity": "...", "location": "file:line" } ],
  "fixed": [ { "ruleId": "...", "location": "file:line" } ],
  "stats": { "new": 0, "fixed": 0, "timestamp": "ISO8601" }
}
```

1. Exit code mapping (implemented): 0 = clean / bootstrap, 2 = regressions >= threshold, 3 = parse error.

Implementation differences vs original outline:

- Uses direct list of new issues only (no explicit fixed list output) to minimize artifact size and complexity.
- Fingerprint priority: `partialFingerprints` (all keys) sorted; fallback to first location file + start line + start column.
- Severity normalization: unknown levels default to `warning` for conservative gating.

## Severity Threshold Mapping (Current Script)

Script uses SARIF `level` values: `error`, `warning`, `note`, `none` with order error > warning > note > none.

| SARIF Level | Numeric Rank | Included When Threshold=warning |
| ----------- | ------------ | -------------------------------- |
| error       | 3            | Yes                              |
| warning     | 2            | Yes                              |
| note        | 1            | No                               |
| none        | 0            | No                               |

Planned enhancement: map Codacy severities (Critical/High/Medium/Low/Info) to SARIF levels for more granular threshold selection.

## Quality Gate Step (Actual Excerpt Simplified)

```yaml
 - name: Compare SARIF against baseline
   run: |
     python security/sarif/tooling/compare.py \
       --baseline security/sarif/baseline.sarif \
       --current results.sarif \
       --threshold warning \
       --output regressions.json || STATUS=$?
     if [ "${STATUS:-0}" -eq 2 ]; then echo "regressions=true" >> $GITHUB_ENV; fi
 - name: Upload regression report
   if: steps.set-regression-output.outputs.regressions == 'true'
   uses: actions/upload-artifact@v4
   with:
     name: sarif-regressions
     path: sarif-regressions.json
```

## Refresh Procedure

1. Open PR: `refresh-sarif-baseline-YYYYMMDD`.
1. Justification section in PR body referencing remediation percentage & rule changes.
1. Replace `baseline.sarif` with latest `results.sarif` from a clean analysis.
1. Update `CHANGELOG.md` with refresh rationale.
1. Merge only if pipeline green and reviewer approves justification.

## Governance

- OWNERS: Security + Platform Engineering.
- Unauthorized baseline modifications trigger automatic PR comment (future enhancement: add CI check hashing baseline file).

## Future Enhancements

- Hash verification step to detect tampering.
- Metrics export (new vs fixed counts) to Prometheus via custom job step.
- Severity weighting score for trend dashboards.

## Next Steps

1. Approve strategy.
1. Implement directory layout + comparison script. (COMPLETED)
1. Add workflow diff step guarded by presence of `baseline.sarif`. (COMPLETED)
1. Document baseline adoption in remediation doc.
