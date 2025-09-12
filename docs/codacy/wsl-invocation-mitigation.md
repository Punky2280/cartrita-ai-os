# Codacy MCP WSL Invocation Mitigation

This document records the mitigation approach for the unintended `wsl` prefix
observed in Codacy MCP analyze executions on a native Linux environment. The
objective is to guarantee deterministic, native invocation of the local Codacy
CLI wrapper (`.codacy/cli.sh`) without relying on Windows Subsystem for Linux
tooling.

## Problem Summary

- The Codacy MCP server (distributed via `@codacy/codacy-mcp`) injected a `wsl` prefix when executing analyze commands.
- On a pure Linux host, `wsl` is absent, causing immediate failures before the repository script could run.
- Repository-side adjustments alone (editing `.codacy/cli.sh`) could not intercept the failure path.

## Mitigation Strategy

1. Introduce a native MCP replacement script inside the repository
  (`scripts/mcp/codacy_mcp_native.js`).
1. Update the local MCP configuration (`mcp.json`) to replace the Codacy server
  entry:

```json
"codacy": {
  "command": "node",
  "args": ["scripts/mcp/codacy_mcp_native.js"],
  "type": "stdio",
  "env": {
    "CODACY_ACCOUNT_TOKEN": "<redacted>"
  }
}
```

1. The replacement implements the minimal JSON-RPC 2.0 surface required for
   baseline generation:

- `initialize` → capability advertisement
- `analyze` → invokes `./.codacy/cli.sh analyze [file?] --format sarif` and
  returns raw SARIF
- `shutdown` → graceful termination

1. The wrapper avoids any platform translation logic; it executes the CLI
  directly, removing the source of the erroneous `wsl` prefix.

## Usage Notes

- Ensure `.codacy/cli.sh` is executable: `chmod +x .codacy/cli.sh`.
- The wrapper searches upward from CWD to locate `.codacy/cli.sh`.
- Returned SARIF is provided in `result.sarif` for each `analyze` call and can be persisted by the caller.

## Security Considerations

- Do not commit real Codacy account tokens. Replace with environment injection outside version control.
- The wrapper returns raw SARIF output; if future sanitization is required, add a streaming filter before responding.

## Extension Path Forward

Potential future enhancements (only if needed):

- Additional Codacy tool operations (e.g., pattern listing) via extended
  methods.
- Streaming large SARIF results using chunked framing if size becomes a
  concern.
- Optional integrity hashing of SARIF for baseline tamper detection.

## Baseline Generation Workflow (Post-Mitigation)

```bash
./.codacy/cli.sh analyze --format sarif > security/sarif/results.sarif
cp security/sarif/results.sarif security/sarif/baseline.sarif
git add security/sarif/results.sarif security/sarif/baseline.sarif
git commit -m "chore(security): add initial SARIF baseline (bootstrap)"
```

After committing the baseline, the SARIF comparator
(`security/sarif/tooling/compare.py`) enforces regression gating while
surfacing fixed issue counts and normalized severities.
