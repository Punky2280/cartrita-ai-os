---
description: "Cartrita frontend chat mode."
tools:
  [
    "codebase",
    "usages",
    "vscodeAPI",
    "think",
    "problems",
    "changes",
    "testFailure",
    "terminalSelection",
    "terminalLastCommand",
    "openSimpleBrowser",
    "fetch",
    "findTestFiles",
    "searchResults",
    "githubRepo",
    "extensions",
    "runTests",
    "editFiles",
    "runNotebooks",
    "search",
    "new",
    "runCommands",
    "runTasks",
    "huggingfacehub",
    "codacy",
    "context7",
    "pylance mcp server",
    "copilotCodingAgent",
    "activePullRequest",
    "getPythonEnvironmentInfo",
    "getPythonExecutableCommand",
    "installPythonPackage",
    "configurePythonEnvironment",
  ]
---

{
"systemPrompt": {
"master": "You are an autonomous senior front-end engineer implementing a production Web UI for a multi-agent AI platform. Absolute Rules: No placeholders or mock logic. If any endpoint or schema is unknown, stop and ask precise clarifying questions. Integrate real multi-agent MCP events, Deepgram audio flows, GitHub repo operations, Tavily search, HuggingFace inference, OpenAI-based embeddings for RAG. Enforce banned substrings: TODO, FIXME, PLACEHOLDER, STUB, MOCK, dummy, lorem, mockAgent, fakeEvent, sampleResponse, dummyData. Use defined design tokens & agent color mapping. All components connected to actual endpoints; no hard-coded static sample lists unless test harness mocks under /**tests**/ using explicit mock factory modules. Comply with accessibility, performance, security constraints in the specification. Ask for missing schemas before implementing dependent code. Deliverable Format Per Task: 1. Confirm requirements 2. File change plan 3. Implement code (exact file paths) 4. Tests (if logic > trivial) 5. Validation (perf, a11y, no placeholder scan) 6. Next-task recommendation. Begin with Phase 1 / Task 1 if schemas sufficient; otherwise request them.",
"rules": [
"No placeholders or mock logic",
"Ask for missing schemas",
"Use design tokens",
"Enforce banned substrings",
"Provide structured task output"
],
"deliveryFormatSteps": [
"Confirm requirements",
"File change plan",
"Implementation code",
"Tests",
"Validation report",
"Next task suggestion"
]
},
"specName": "Cartrita Web Master Specification",
"version": "2025-09-04",
"format": "web_only_json",
"fileAttachments": {
"description": "Unified file attachment capability for conversations, RAG ingestion, code context, and research enrichment.",
"combinedAggregateLimitMB": 200,
"text": {
"maxFiles": 50,
"maxFileSizeMB": 20,
"aggregateSizeLimitMB": 200,
"acceptedExtensions": [
".txt", ".md", ".mdx", ".rst", ".tex", ".csv", ".tsv", ".json", ".yaml", ".yml",
".toml", ".ini", ".log", ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt",
".go", ".rs", ".rb", ".php", ".cs", ".cpp", ".cc", ".c", ".h", ".hpp", ".m",
".mm", ".swift", ".scala", ".bash", ".sh", ".zsh", ".sql", ".html", ".css",
".scss", ".xml", ".ipynb"
],
"characterEncoding": "utf-8",
"languageDetection": true,
"perFileContentHash": "sha256",
"deduplicateStrategy": "hash+path"
},
"binary": {
"acceptedTypes": {
"audio": [
"audio/mpeg",
"audio/wav",
"audio/x-wav",
"audio/ogg",
"audio/mp4",
"audio/webm"
],
"video": [
"video/mp4",
"video/webm",
"video/quicktime",
"video/x-matroska"
],
"other": [
"application/pdf",
"application/zip",
"application/x-tar",
"application/gzip"
]
},
"proposedMaxFileSizeMB": {
"audio": 100,
"video": 500,
"pdf": 50,
"archive": 200
},
"aggregateBinarySizeLimitMB": 200,
"effectiveRule": "Per-category limits apply but each upload is also constrained by remaining combinedAggregateLimitMB (global cap). A single video larger than remaining capacity is rejected even if <= video per-file max.",
"streamingIngest": {
"chunkSizeKB": 512,
"maxParallelUploads": 4,
"retryBackoff": "exponential"
},
"virusScanRequired": true,
"hashAlgorithm": "sha256",
"requiresConfirmation": true
},
"retention": {
"temporaryStorageTTLHours": 24,
"persistAfterIngestion": true,
"note": "Original binaries and normalized text derivatives retained post-ingestion subject to global storage policy."
},
"security": {
"contentScanning": [
"virus",
"malware-signature",
"sensitive-secret-heuristics"
],
"forbiddenExecutableMagic": true,
"maxLinesForInlinePreview": 8000,
"sandboxPdfParsing": true
},
"telemetry": {
"events": [
"file.attach.requested",
"file.attach.accepted",
"file.attach.rejected",
"file.ingest.started",
"file.ingest.completed",
"file.ingest.failed",
"file.deduplicated",
"file.aggregate.limit_reached"
]
},
"ragIngestion": {
"autoChunkText": true,
"chunkSizeChars": 1800,
"chunkOverlapChars": 250,
"langDetectionModel": "fasttext-lite",
"embeddingBatchSize": 32
},
"validation": {
"rejectIfOverMax": true,
"rejectIfExtensionMismatchMime": true,
"maxFilenameLength": 180,
"globalEnforcementOrder": [
"per-file-size",
"extension-mime-consistency",
"aggregate-category-limit",
"combined-aggregate-limit",
"virus-scan",
"duplicate-hash-check"
]
},
"conflictNotes": [
"A single video up to 500MB is permitted by category rule but blocked if combined remaining capacity < file size (global 200MB cap).",
"UI must surface remaining global capacity dynamically."
]
},
"meta": {
"description": "Full multi-agent, multi-integration, zero-placeholder production specification converted to structured JSON.",
"placeholderPolicy": "Banned terms must not appear in code or runtime artifacts.",
"bannedSubstrings": [
"TODO",
"FIXME",
"PLACEHOLDER",
"STUB",
"MOCK",
"dummy",
"lorem",
"mockAgent",
"fakeEvent",
"sampleResponse",
"dummyData"
],
"primaryModels": {
"supervisor": "gpt-4.1",
"subAgents": "gpt-5",
"embeddings": "openai-embeddings"
},
"coreVendors": [
"OpenAI",
"HuggingFace",
"Deepgram",
"Tavily",
"GitHub"
],
"architectureGoals": [
"No mock logic",
"Deterministic multi-agent orchestration",
"High transparency (graph, reasoning snapshot, evidence matrix)",
"Extensible tool layer",
"Streaming-first UX (SSE primary, WS fallback)"
]
},
"agents": {
"supervisor": {
"name": "Cartrita",
"model": "gpt-4.1",
"responsibilities": [
"Task decomposition",
"Sub-agent selection",
"Response fusion",
"Conflict resolution",
"Memory injection",
"Scoring & evaluation (LangSmith)",
"Reasoning trace orchestration"
]
},
"subAgents": [
{
"id": "knowledge",
"origin": "Knowledge Agent",
"implementationFile": "knowledge_agent.py",
"model": "gpt-5",
"role": "Knowledge retrieval and RAG orchestration (semantic + lexical + vector + Tavily synthesis)",
"replaces": "retrieval",
"rerankDelegatedTo": "evaluation"
},
{
"id": "code_agent",
"origin": "code_agent.py",
"model": "gpt-5",
"role": "Advanced code generation, refactor planning, patch synthesis, PR description drafting",
"replaces": "code"
},
{
"id": "research_agent",
"origin": "Research Agent",
"model": "gpt-5",
"role": "Iterative web + multi-source deep research, evidence extraction & citation mapping",
"replaces": "research"
},
{
"id": "task_agent",
"origin": "Task Agent",
"model": "gpt-5",
"role": "Multi-step task orchestration, chain assembly, adaptive tool sequencing; may reprioritize/cancel only when necessity policy triggers",
"replaces": "toolComposer",
"cancellationPolicy": {
"allowed": true,
"conditions": [
"Upstream dependency invalidated",
"Safety escalation",
"Resource budget breach",
"Redundant parallel sub-chain detected"
]
}
},
{
"id": "computer_use",
"origin": "computer_use_agent.py",
"model": "gpt-5",
"role": "System / environment interaction abstraction with file operations, screenshots, controlled command execution",
"replaces": null,
"safetyModeDefault": true
},
{
"id": "audio",
"model": "gpt-5",
"role": "Deepgram orchestration + transcript enrichment"
},
{
"id": "evaluation",
"model": "gpt-5",
"role": "Quality metrics, coherence/factuality scoring, rerank responsibilities"
},
{
"id": "memory",
"model": "gpt-5",
"role": "Summarization snapshots, entity & preference extraction"
},
{
"id": "modelSelector",
"model": "gpt-5",
"role": "Dynamic provider/model choice & ensemble gating"
},
{
"id": "safety",
"model": "gpt-5",
"role": "Policy & risk pattern detection"
}
],
"eventFrames": [
"agent_task_started",
"agent_task_progress",
"agent_task_output",
"agent_task_complete",
"orchestration_decision",
"chain_reconfigured",
"safety_flag",
"evaluation_metric",
"audio_interim",
"audio_final"
]
},
"agentReplacementNotes": {
"replacedAgents": [
{ "previous": "retrieval", "current": "knowledge" },
{ "previous": "code", "current": "code_agent" },
{ "previous": "research", "current": "research_agent" },
{ "previous": "toolComposer", "current": "task_agent" }
],
"addedAgents": [
{ "id": "computer_use", "purpose": "Operational execution & environment action layer" }
],
"remainingAgentsUnchanged": [
"audio",
"evaluation",
"memory",
"modelSelector",
"safety"
]
},
"computerUse": {
"description": "Computer interaction agent schema derived from implementation logic.",
"endpoints": [
{
"method": "POST",
"path": "/computer-use/execute",
"requestBody": "ComputerUseRequest",
"responseBody": "ComputerUseResponse",
"sseProgressEvents": true
},
{
"method": "GET",
"path": "/computer-use/status",
"responseBody": "{ status, running, safety_mode, model, version }"
},
{
"method": "POST",
"path": "/computer-use/screenshot",
"requestBody": "ScreenshotRequest",
"responseBody": "{ imageBase64, format, capturedAt }"
},
{
"method": "POST",
"path": "/computer-use/file-op",
"requestBody": "FileOperation",
"responseBody": "{ operation, path, success, result, warnings[]? }"
},
{
"method": "POST",
"path": "/computer-use/command",
"requestBody": "SystemCommand",
"responseBody": "{ command, stdout, stderr, exit_code, durationMs, blocked?: boolean }"
}
],
"actionSchemas": {
"ScreenshotRequest": {
"description": "Capture a screenshot for contextual reasoning or user confirmation.",
"fields": {
"description": "string (what to capture)",
"format": "enum[png,jpg,webp] default png",
"quality": "int 1-100 (lossy formats)"
}
},
"FileOperation": {
"description": "Controlled file system interaction.",
"fields": {
"operation": "enum[read,write,list,delete,move]",
"path": "string absolute or sandbox-relative",
"content": "string (write only, UTF-8)",
"recursive": "boolean (restricted for delete/move)"
},
"constraints": {
"maxContentBytes": 5_000_000,
"denyRecursiveOn": ["delete", "move"]
}
},
"SystemCommand": {
"description": "Execute a safe system command inside sandbox.",
"fields": {
"command": "string",
"timeout": "int 1-300s",
"working_directory": "string|null"
},
"filters": {
"denyPatterns": [
"rm -rf",
"sudo",
"su",
"passwd",
"chmod 777",
"dd ",
"mkfs",
"fdisk",
"format",
"del /f /s /q"
]
}
},
"ComputerUseRequest": {
"fields": {
"task": "string high-level description",
"screenshot_needed": "boolean",
"file_operations": "FileOperation[]",
"system_commands": "SystemCommand[]",
"safety_mode": "boolean"
}
},
"ComputerUseResponse": {
"fields": {
"result": "string summary",
"screenshot": "base64|null",
"file_results": "array",
"command_results": "array",
"safety_warnings": "string[]",
"metadata": "object"
}
}
},
"safety": {
"dangerousCommandPatterns": [
"rm -rf",
"sudo",
"su",
"passwd",
"chmod 777",
"dd ",
"mkfs",
"fdisk",
"format",
"del /f /s /q"
],
"restrictedPaths": [
"/",
"/etc",
"/usr",
"/bin",
"/sbin",
"/root",
"/home"
],
"enforcement": {
"blockRecursiveDeleteMove": true,
"sandboxRequired": true,
"stdoutStderrSizeLimitKB": 256
},
"logging": {
"auditLog": true,
"fields": [
"timestamp",
"actor",
"actionType",
"pathOrCommand",
"allowed",
"warnings[]"
]
}
},
"rateLimits": {
"executePerMinute": 10,
"fileOpPerMinute": 30,
"commandPerMinute": 20,
"burstMultiplier": 2
},
"concurrency": {
"maxConcurrentExecutions": 2,
"queueStrategy": "fifo",
"timeoutSeconds": 300
},
"telemetry": {
"events": [
"computer_use.execute.started",
"computer_use.execute.completed",
"computer_use.command.blocked",
"computer_use.file_op.blocked",
"computer_use.safety.warning",
"computer_use.screenshot.captured"
]
},
"reasoningInterface": {
"exposeIntermediatePlan": true,
"planRedaction": "safety-filtered"
}
},
"integrationImpactOfAgentSwap": {
"knowledge": {
"pipelineAdjustments": [
"Consolidate retrieval + RAG scoring",
"Direct coordination with Memory agent for context budget"
]
},
"task_agent": {
"orchestrationChanges": [
"Takes over dynamic chain assembly",
"Feeds reasoning snapshots to supervisor",
"May cancel tasks under necessity policy"
]
},
"computer_use": {
"governance": [
"Strict action schema enforced",
"Audit logging of all system-level operations"
],
"requiredSchemas": [
"ComputerUseRequest",
"ComputerUseResponse",
"FileOperation",
"SystemCommand",
"ScreenshotRequest"
]
}
},
"streaming": {
"primaryTransport": "SSE",
"fallback": "WebSocket",
"sseEvents": [
"token",
"function_call",
"tool_result",
"metrics",
"done",
"agent_task_started",
"agent_task_progress",
"agent_task_output",
"agent_task_complete",
"orchestration_decision",
"chain_reconfigured",
"safety_flag",
"evaluation_metric",
"audio_interim",
"audio_final",
"file.attach.progress",
"computer_use.execute.progress"
],
"requiredMetadata": [
"eventType",
"timestamp",
"conversationId",
"orchestrationId",
"messageId?"
],
"performanceBudgets": {
"graphRenderMs_30Nodes": 120,
"liveTranscriptLagMs": 400,
"repoTreeInitialLoadMs": 1200,
"ensembleDecisionMs": 600
}
},
"pendingConfirmation": {
"securityReview": "Optional expansion of secret scanning patterns; currently standard set only."
}
}

```

```
