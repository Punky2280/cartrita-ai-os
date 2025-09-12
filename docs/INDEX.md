# Cartrita AI OS Documentation Index

## Top-Level Categories

- Architecture (`architecture/`)
- Agents (`agents/`)
- API Schemas (`api/`)
- Implementation Specs (`implementation/`)
- Research & Vendor Reports (`research/`)
- Streaming Analyses (`streaming/`)
- Security & Audits (`security/`)
- Reports / Phase Status (`reports/`)
- Comparison Charts & Maps (`Charts_&_Maps/`)
- Technology Patterns (`technology/`)
- Codacy Reports (`codacy/`)

## Key Files by Category

### API

- `api/api-schemas.json` (canonical schemas)
- `api/schema-definitions.json`

### Security

- `security/configuration-integrity-audit.md`

### Reports

- `reports/phase-3-progress-report.md`
- `reports/project-status-report.md`
- `build-completion-report.md` (final completion report)

### Streaming

- `streaming/openai-streaming-analysis.md`
- `streaming/streaming-apis-comprehensive-analysis.md`
- `streaming/deepgram-research-report.md`
- `streaming/openai-research-report.md`
- `streaming/github-research-report.md`

### Comparison & Mapping (Charts_&_Maps)

- `Charts_&_Maps/streaming-transport-comparison.md`
- `Charts_&_Maps/vendor-research-summary.md`
- `Charts_&_Maps/security-docs-map.md`
- `Charts_&_Maps/phase-progress-map.md`
- `Charts_&_Maps/technology-pattern-index.md`
- `Charts_&_Maps/documentation-reorganization-plan.md`

### Implementation

- `implementation/api-wiring-specification.md`
- `implementation/comprehensive-integration-report.md`
- `implementation/phase-3-validation-report.md`
- `implementation/phase-3-voice-integration-specification.md`
- `implementation/phase-4-conversational-ai-research-report.md`
- `implementation/phase1-task1-complete-guide.md`
- `implementation/phase2-implementation-plan.md`
- `implementation/phase2-voice-integration-plan.md`
- `implementation/IMPLEMENTATION_SUMMARY.md`

### Research Remaining

- `research/anthropic-research-report.md`
- `research/authentication-security-patterns.md`
- `research/huggingface-research-report.md`
- `research/langsmith-research-report.md`
- `research/tavily-research-report.md`
- `research/UNIQUE_DIFFERENTIATING_FEATURES.md`
- `research/JSX_PARSING_ERROR_RESOLUTION.md`

### Technology

- `technology/deepgram-streaming-integration-patterns-2025.md`
- `2025-technology-research.md`

## Change Log (Reorganization)

| Action | Source | Destination |
|--------|--------|-------------|
| Migrated | api-schemas.json | api/api-schemas.json |
| Migrated | schema-definitions.json | api/schema-definitions.json |
| Moved | configuration-integrity-audit.md | security/configuration-integrity-audit.md |
| Moved | phase-3-progress-report.md | reports/phase-3-progress-report.md |
| Moved | project-status-report.md | reports/project-status-report.md |
| Deduplicated | build-completion-report.md (research copy) | Removed duplicate |

## Pending / Verification Checklist

- [ ] Confirm no remaining duplicates in `research/` vs other folders
- [ ] Run lint/format pass on all new/modified markdown
- [ ] Update any internal links in moved markdown files (future step)

---
*Index auto-generated during reorganization (September 2025).*
