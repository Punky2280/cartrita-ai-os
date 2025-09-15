## Summary

Describe the change and its motivation.

## Static Analysis / SARIF

- [ ] Ran `python scripts/sarif/generate_sarif.py --output sarif/current.sarif`
- [ ] Ran comparator against baseline

### Diff Summary (paste key counts)

```text
NEW: errors=?, warnings=?, notes=?, total=?
FIXED: errors=?, warnings=?, notes=?, total=?
PERSISTED: total=?
```

### Baseline Update Requested?

- [ ] Yes (attach rationale below)
- [ ] No

If yes, justification (why findings are accepted / noise / rule changes):

```text
<reasoning>
```

## Threshold Gating (if enabled)

- [ ] Comparator exit code == 0

## Testing & Validation

List tests added/updated and any relevant performance or latency considerations.

## Checklist

- [ ] No introduction of banned substrings
- [ ] Logging/metrics unaffected or updated appropriately
- [ ] Documentation updated where necessary
