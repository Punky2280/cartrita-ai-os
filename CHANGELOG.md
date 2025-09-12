# Changelog

All notable changes to this repository will be documented here.

The format aims to follow Keep a Changelog principles (unreleased section first) while emphasizing security & quality gate modifications.

## [Unreleased]

- Placeholder for upcoming features and fixes.

### Added

- SARIF regression comparison step in Codacy workflow (`security/sarif/tooling/compare.py`) gating merges on new issues ≥ warning severity.

### Security

- Baseline diff mechanism reduces noise from legacy findings, focusing review on newly introduced code risks.

### DevEx

- Regression artifact (`regressions.json`) uploaded when new issues detected for rapid triage.

## [2025-09-11] Security & QA Hardening

### Added

- Weekly scheduled Codacy static analysis run (`cron: '23 4 * * 1'`).
- Token presence reporting step in Codacy workflow for observability.
- Artifact archival of `results.sarif` for historical diffing.
- Dedicated `markdownlint` CI job executing `npm run lint:md` to prevent documentation drift.

### Changed

- Pinned `codacy/codacy-analysis-cli-action` to a commit digest (temporary placeholder hash pending
  upstream verification) instead of floating ref.

### Security

- Supply-chain integrity improved via action pinning; reduces risk of upstream mutation.
- Early detection of doc quality regressions through continuous markdown lint enforcement.

### Notes

- Replace temporary Codacy action hash with validated official digest before tagging next release.
- Consider adding SARIF retention policy or diff tooling if volume grows.
