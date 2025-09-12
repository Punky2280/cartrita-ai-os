# Documentation Reorganization Plan

This file outlines the planned categorization and relocation of existing documentation files under `docs/`.

## New/Confirmed Category Folders

| Category | Path | Purpose |
|----------|------|---------|
| Architecture | `architecture/` | High-level system & UI/UX specifications |
| Agents | `agents/` | Agent roles, behaviors, orchestration design |
| Implementation | `implementation/` | Concrete build/integration specs, phase plans, schema definitions |
| Research | `research/` | External/vendor research reports, comparative analyses |
| Technology | `technology/` | Technology-specific best practice pattern guides (2025) |
| Codacy | `codacy/` | Code quality & static analysis outputs |
| API Schemas | `api/` (new) | API schema JSON & protocol definitions |
| Status & Reports | `reports/` (new) | Project status, completion & progress reports |
| Streaming | `streaming/` (new) | Streaming protocol analyses & decisions |
| Security | `security/` (new) | Authentication, CSP, CORS, security patterns |
| Charts & Maps | `Charts_&_Maps/` | Comparison tables, matrices, taxonomy maps |

## File Mapping

| Current Location | File | Target Folder | Rationale |
|------------------|------|---------------|-----------|
| docs/ | api-schemas.json | api/ | Central API schema artifact |
| docs/ | build-completion-report.md | reports/ | Project completion report |
| docs/agents/ | agent-architecture.md | agents/ | Already correct |
| docs/architecture/ | README.md | architecture/ | Already correct |
| docs/architecture/ | UI_UX_DESIGN_SPECIFICATION.md | architecture/ | Already correct |
| docs/codacy/ | codacy-issues-report.md | codacy/ | Already correct |
| docs/implementation/ | IMPLEMENTATION_SUMMARY.md | implementation/ | Already correct |
| docs/implementation/ | api-wiring-specification.md | implementation/ | Already correct |
| docs/implementation/ | comprehensive-integration-report.md | implementation/ | Already correct |
| docs/implementation/ | configuration-integrity-audit.md | security/ | Security-focused audit |
| docs/implementation/ | openai-streaming-analysis.md | streaming/ | Streaming decision document |
| docs/implementation/ | phase-3-progress-report.md | reports/ | Progress reporting |
| docs/implementation/ | phase-3-validation-report.md | reports/ | Validation reporting |
| docs/implementation/ | phase-3-voice-integration-specification.md | implementation/ | Voice implementation spec |
| docs/implementation/ | phase-4-conversational-ai-research-report.md | research/ | Research oriented |
| docs/implementation/ | phase1-task1-complete-guide.md | implementation/ | Implementation guide |
| docs/implementation/ | phase2-implementation-plan.md | implementation/ | Implementation plan |
| docs/implementation/ | phase2-voice-integration-plan.md | implementation/ | Implementation plan |
| docs/implementation/ | schema-definitions.json | api/ | Schema definitions belong with API |
| docs/research/ | JSX_PARSING_ERROR_RESOLUTION.md | implementation/ | Tactical resolution guide |
| docs/research/ | UNIQUE_DIFFERENTIATING_FEATURES.md | research/ | Product/market research |
| docs/research/ | anthropic-research-report.md | research/ | Vendor research |
| docs/research/ | authentication-security-patterns.md | security/ | Security best practices |
| docs/research/ | build-completion-report.md | reports/ | Misplaced duplicate (if identical) |
| docs/research/ | deepgram-research-report.md | research/ | Vendor research |
| docs/research/ | github-research-report.md | research/ | Vendor research |
| docs/research/ | huggingface-research-report.md | research/ | Vendor research |
| docs/research/ | langsmith-research-report.md | research/ | Vendor research |
| docs/research/ | openai-research-report.md | research/ | Vendor research |
| docs/research/ | project-status-report.md | reports/ | Status reporting |
| docs/research/ | streaming-apis-comprehensive-analysis.md | streaming/ | Broader streaming analysis |
| docs/research/ | tavily-research-report.md | research/ | Vendor research |
| docs/technology/ | 2025-technology-research.md | technology/ | Already correct |
| docs/technology/ | deepgram-streaming-integration-patterns-2025.md | streaming/ | Streaming integration patterns |
| docs/technology/ | fastapi-async-patterns-best-practices-2025.md | technology/ | Backend technology patterns |
| docs/technology/ | langchain-research-report.md | research/ | Research style write-up |
| docs/technology/ | langgraph-agent-orchestration-patterns-2025.md | agents/ | Agent orchestration patterns |
| docs/technology/ | react-typescript-modern-patterns-2025.md | technology/ | Frontend technology patterns |
| docs/technology/ | tanstack-query-jotai-patterns-2025.md | technology/ | State/data patterns |
| docs/implementation/ | openai-streaming-analysis.md (duplicate listing) | streaming/ | Already mapped above |

## Comparison Tables To Generate

| Table | Description | Source Inputs | Output File |
|-------|-------------|--------------|-------------|
| Streaming Transport Comparison | SSE vs WebSocket vs Hybrid | openai-streaming-analysis.md, streaming-apis-comprehensive-analysis.md | Charts_&_Maps/streaming-transport-comparison.md |
| Vendor Research Summary | Key metrics across AI vendors | anthropic, openai, huggingface, deepgram, tavily, github research reports | Charts_&_Maps/vendor-research-summary.md |
| Security Docs Map | Security-related documents mapping | authentication-security-patterns.md, configuration-integrity-audit.md | Charts_&_Maps/security-docs-map.md |
| Implementation Phase Progress | Phase doc milestones & status | phase* docs, project-status-report.md | Charts_&_Maps/phase-progress-map.md |
| Technology Pattern Index | Quick index of technology guides | technology folder md files | Charts_&_Maps/technology-pattern-index.md |

## Next Steps

1. Create new folders (`api/`, `reports/`, `streaming/`, `security/`).
2. Move mapped files into target folders.
3. Generate comparison table markdown files.
4. Verify no orphaned duplicates remain.
5. Add an index README summarizing new structure.
