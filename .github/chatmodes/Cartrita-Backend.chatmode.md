---
description: 'A chat mode for backend development tasks, focusing on server-side logic, API development, database interactions, and performance optimization.'
tools: ['codebase', 'usages', 'vscodeAPI', 'think', 'problems', 'changes', 'testFailure', 'terminalSelection', 'terminalLastCommand', 'openSimpleBrowser', 'fetch', 'findTestFiles', 'searchResults', 'githubRepo', 'extensions', 'runTests', 'editFiles', 'runNotebooks', 'search', 'new', 'runCommands', 'runTasks', 'github', 'huggingface', 'pylance mcp server', 'copilotCodingAgent', 'activePullRequest', 'getPythonEnvironmentInfo', 'getPythonExecutableCommand', 'installPythonPackage', 'configurePythonEnvironment']
---json
{
  "systemPrompt": {
    "master": "You are an autonomous senior front-end  and back-end engineer implementing a production Web UI for a multi-agent AI platform. Absolute Rules: No placeholders or mock logic. If any endpoint or schema is unknown, stop and ask precise clarifying questions. Integrate real multi-agent MCP events, Deepgram audio flows, GitHub repo operations, Tavily search, HuggingFace inference, OpenAI-based embeddings for RAG. Enforce banned substrings: TODO, FIXME, PLACEHOLDER, STUB, MOCK, dummy, lorem, mockAgent, fakeEvent, sampleResponse, dummyData. Use defined design tokens & agent color mapping. All components connected to actual endpoints; no hard-coded static sample lists unless test harness mocks under /__tests__/ using explicit mock factory modules. Comply with accessibility, performance, security constraints in the specification. Ask for missing schemas before implementing dependent code. Deliverable Format Per Task: 1. Confirm requirements 2. File change plan 3. Implement code (exact file paths) 4. Tests (if logic > trivial) 5. Validation (perf, a11y, no placeholder scan) 6. Next-task recommendation. Begin with Phase 1 / Task 1 if schemas sufficient; otherwise request them.",
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
}      "description": "The system prompt that defines the behavior of the assistant."
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/master_backend_chat_mode.schema.json",
  "title": "Master Backend Chat Mode Specification (Prompt + Config + Augmentations)",
  "type": "object",
  "required": [
    "systemPrompt",
    "modeConfig",
    "openapiAugmentation",
    "asyncapiSpec",
    "testAutoGenerationPolicy",
    "sdkGeneration",
    "ci",
    "version"
  ],
  "additionalProperties": false,
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
      "description": "Version of the master spec bundle"
    },
    "systemPrompt": {
      "type": "string",
      "description": "Primary system / architect instruction prompt placed verbatim at top for agent bootstrap."
    },
    "modeConfig": {
      "type": "object",
      "description": "Core operational configuration (previous chat mode config).",
      "required": [
        "name",
        "version",
        "description",
        "tools",
        "streaming",
        "endpoints",
        "observability",
        "performanceTargets",
        "security",
        "providerAbstraction",
        "testing",
        "executionLoop",
        "guardrails"
      ],
      "additionalProperties": false,
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
        "description": { "type": "string", "minLength": 1 },
        "primaryPurpose": { "type": "string" },
        "tools": {
            "type": "array",
            "items": { "type": "string", "minLength": 1 },
            "minItems": 1,
            "uniqueItems": true
        },
        "principles": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "sseFirst": { "type": "boolean" },
            "webSocketFallback": { "type": "boolean" },
            "noSecrets": { "type": "boolean" },
            "asyncOnlyForIOBound": { "type": "boolean" },
            "rejectExtraFields": { "type": "boolean" },
            "structuredErrors": { "type": "boolean" }
          }
        },
        "streaming": {
          "type": "object",
          "required": ["priorityOrder", "negotiation", "sse", "websocket"],
          "additionalProperties": false,
          "properties": {
            "priorityOrder": {
              "type": "array",
              "items": { "enum": ["sse", "websocket"] },
              "minItems": 1
            },
            "negotiation": {
              "type": "object",
              "required": [
                "sseDefault",
                "fallbackConditions",
                "headersTriggeringWebSocket",
                "retryGuidanceSeconds"
              ],
              "additionalProperties": false,
              "properties": {
                "sseDefault": { "type": "boolean" },
                "fallbackConditions": {
                  "type": "array",
                  "items": {
                    "enum": [
                      "client_header_requests_websocket",
                      "multiple_sse_failures",
                      "need_bidirectional_tool_calls"
                    ]
                  },
                  "minItems": 1
                },
                "headersTriggeringWebSocket": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": ["header", "value"],
                    "additionalProperties": false,
                    "properties": {
                      "header": { "type": "string", "minLength": 1 },
                      "value": { "type": "string", "minLength": 1 }
                    }
                  }
                },
                "queryFallbackParam": { "type": "string" },
                "retryGuidanceSeconds": {
                  "type": "array",
                  "items": { "type": "number", "exclusiveMinimum": 0 },
                  "minItems": 1
                }
              }
            },
            "sse": {
              "type": "object",
              "required": ["endpoint", "events", "tokenPayloadMinFields", "sanitizePerToken"],
              "additionalProperties": false,
              "properties": {
                "endpoint": {
                  "type": "object",
                  "required": ["path", "method", "mediaType"],
                  "additionalProperties": false,
                  "properties": {
                    "path": { "type": "string", "pattern": "^/" },
                    "method": { "const": "POST" },
                    "mediaType": { "const": "text/event-stream" }
                  }
                },
                "events": {
                  "type": "object",
                  "required": ["orderedSequence", "eventNames", "heartbeat", "dataShapes"],
                  "additionalProperties": false,
                  "properties": {
                    "orderedSequence": {
                      "type": "array",
                      "items": { "type": "string" },
                      "minItems": 1
                    },
                    "eventNames": {
                      "type": "array",
                      "items": { "enum": ["start", "token", "usage", "end", "error"] },
                      "uniqueItems": true
                    },
                    "heartbeat": {
                      "type": "object",
                      "required": ["enabled", "format", "idleSeconds"],
                      "additionalProperties": false,
                      "properties": {
                        "enabled": { "type": "boolean" },
                        "format": { "type": "string" },
                        "idleSeconds": { "type": "integer", "minimum": 5 }
                      }
                    },
                    "dataShapes": {
                      "type": "object",
                      "additionalProperties": { "type": "object" }
                    }
                  }
                },
                "tokenPayloadMinFields": {
                  "type": "array",
                  "items": { "type": "string" },
                  "minItems": 1
                },
                "sanitizePerToken": { "type": "boolean" }
              }
            },
            "websocket": {
              "type": "object",
              "required": [
                "endpoint",
                "frameTypes",
                "frameSchemas",
                "bidirectionalSupport",
                "authenticateOnConnect"
              ],
              "additionalProperties": false,
              "properties": {
                "endpoint": {
                  "type": "object",
                  "required": ["path"],
                  "additionalProperties": false,
                  "properties": {
                    "path": { "type": "string", "pattern": "^/" },
                    "subprotocol": { "type": ["string", "null"] }
                  }
                },
                "frameTypes": {
                  "type": "array",
                  "items": { "enum": ["start", "token", "end", "error"] },
                  "uniqueItems": true
                },
                "frameSchemas": {
                  "type": "object",
                  "additionalProperties": { "type": "object" }
                },
                "bidirectionalSupport": { "type": "boolean" },
                "authenticateOnConnect": { "type": "boolean" }
              }
            }
          }
        },
        "schemas": {
          "type": "object",
          "additionalProperties": true
        },
        "endpoints": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["path", "method", "purpose"],
            "additionalProperties": true,
            "properties": {
              "path": { "type": "string", "pattern": "^/" },
              "method": { "type": "string", "minLength": 2 },
              "purpose": { "type": "string", "minLength": 1 },
              "authRequired": { "type": "boolean" },
              "rateLimited": { "type": "boolean" },
              "streaming": { "type": "boolean" },
              "transport": { "enum": ["sse", "websocket", null] }
            }
          }
        },
        "observability": {
          "type": "object",
            "required": ["logging", "metrics"],
          "additionalProperties": false,
          "properties": {
            "logging": {
              "type": "object",
              "required": ["structured", "traceIdHeader", "includeLatencyMs"],
              "additionalProperties": false,
              "properties": {
                "structured": { "type": "boolean" },
                "traceIdHeader": { "type": "string" },
                "includeLatencyMs": { "type": "boolean" }
              }
            },
            "metrics": {
              "type": "object",
              "required": ["counters", "histograms", "labels"],
              "additionalProperties": false,
              "properties": {
                "counters": {
                  "type": "array",
                  "items": { "type": "string" },
                  "minItems": 1
                },
                "histograms": {
                  "type": "array",
                  "items": { "type": "string" }
                },
                "labels": {
                  "type": "array",
                  "items": { "type": "string" }
                }
              }
            }
          }
        },
        "performanceTargets": {
          "type": "object",
          "required": ["p95FirstTokenMsSse", "p95FirstTokenMsWebsocket", "p95NonStreamMs"],
          "additionalProperties": false,
          "properties": {
            "p95FirstTokenMsSse": { "type": "integer", "minimum": 1 },
            "p95FirstTokenMsWebsocket": { "type": "integer", "minimum": 1 },
            "p95NonStreamMs": { "type": "integer", "minimum": 1 }
          }
        },
        "resilience": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "httpClientTimeoutSeconds": { "type": "integer", "minimum": 1 },
            "retryBackoffSeconds": {
              "type": "array",
              "items": { "type": "number", "exclusiveMinimum": 0 },
              "minItems": 1
            },
            "circuitBreakerPlaceholder": { "type": "boolean" },
            "gracefulShutdownSeconds": { "type": "integer", "minimum": 1 }
          }
        },
        "security": {
          "type": "object",
          "required": [
            "authDependency",
            "rejectExtraFields",
            "payloadSizeLimitBytes",
            "rateLimitPlaceholder",
            "bannedTermsEnvVar",
            "sanitizeStreamingOutput"
          ],
          "additionalProperties": false,
          "properties": {
            "authDependency": { "type": "string" },
            "rejectExtraFields": { "type": "boolean" },
            "payloadSizeLimitBytes": { "type": "integer", "minimum": 1 },
            "rateLimitPlaceholder": { "type": "boolean" },
            "bannedTermsEnvVar": { "type": "string" },
            "sanitizeStreamingOutput": { "type": "boolean" }
          }
        },
        "bannedSubstringFilter": {
          "type": "object",
          "required": ["strategy", "maxRedactionsBeforeAbort", "abortErrorCode"],
          "additionalProperties": false,
          "properties": {
            "strategy": { "enum": ["sanitize", "reject"] },
            "maxRedactionsBeforeAbort": { "type": "integer", "minimum": 1 },
            "abortErrorCode": { "type": "string" }
          }
        },
        "providerAbstraction": {
          "type": "object",
          "required": ["registryModule", "baseInterface", "fallbackLoggingLevel", "noSilentFallback"],
          "additionalProperties": false,
          "properties": {
            "registryModule": { "type": "string" },
            "baseInterface": {
              "type": "object",
              "required": ["methods"],
              "additionalProperties": false,
              "properties": {
                "methods": {
                  "type": "array",
                  "items": { "type": "string" },
                  "minItems": 1
                }
              }
            },
            "fallbackLoggingLevel": { "enum": ["INFO", "WARN", "ERROR", "DEBUG"] },
            "noSilentFallback": { "type": "boolean" }
          }
        },
        "testing": {
          "type": "object",
          "required": ["coverageTargetPercent", "tests", "performance"],
          "additionalProperties": false,
          "properties": {
            "coverageTargetPercent": { "type": "integer", "minimum": 0, "maximum": 100 },
            "tests": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["name", "focus"],
                "additionalProperties": false,
                "properties": {
                  "name": { "type": "string" },
                  "focus": {
                    "type": "array",
                    "items": { "type": "string" },
                    "minItems": 1
                  }
                }
              }
            },
            "performance": {
              "type": "object",
              "required": ["enableSmoke", "skipIfCI"],
              "additionalProperties": false,
              "properties": {
                "enableSmoke": { "type": "boolean" },
                "skipIfCI": { "type": "boolean" }
              }
            }
          }
        },
        "executionLoop": {
          "type": "object",
          "required": ["phases", "onFailure"],
          "additionalProperties": false,
          "properties": {
            "phases": {
              "type": "array",
              "items": {
                "enum": ["clarify", "plan", "implement", "test", "summarize", "recommend_next_action"]
              },
              "minItems": 1
            },
            "onFailure": { "type": "string" }
          }
        },
        "guardrails": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1
        },
        "completionCriteria": {
          "type": "object",
          "required": ["baseline"],
          "additionalProperties": false,
          "properties": {
            "baseline": {
              "type": "array",
              "items": { "type": "string" },
              "minItems": 1
            }
          }
        },
        "futureEnhancements": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "openapiAugmentation": {
      "type": "object",
      "description": "OpenAPI 3.x augmentation snippet (SSE + WS fallback) with vendor extensions.",
      "required": ["paths", "components", "x-metadata"],
      "additionalProperties": false,
      "properties": {
        "x-metadata": {
          "type": "object",
          "additionalProperties": true,
          "properties": {
            "streamingPriority": { "type": "array", "items": { "enum": ["sse","websocket"] } },
            "description": { "type": "string" }
          }
        },
        "paths": {
          "type": "object",
          "required": ["/api/chat/stream","/ws/chat"],
          "additionalProperties": true
        },
        "components": {
          "type": "object",
          "required": ["schemas"],
          "additionalProperties": true,
          "properties": {
            "schemas": { "type": "object", "additionalProperties": { "type": "object" } }
          }
        }
      }
    },
    "asyncapiSpec": {
      "type": "object",
      "description": "AsyncAPI 2.6.0 (or compatible) document capturing WebSocket channel semantics.",
      "required": ["asyncapi", "info", "channels", "components"],
      "additionalProperties": true,
      "properties": {
        "asyncapi": { "type": "string", "const": "2.6.0" },
        "info": {
          "type": "object",
          "required": ["title","version"],
          "properties": {
            "title": { "type": "string" },
            "version": { "type": "string" },
            "description": { "type": "string" }
          }
        },
        "defaultContentType": { "type": "string" },
        "channels": {
          "type": "object",
          "required": ["/ws/chat"],
          "additionalProperties": true
        },
        "components": {
          "type": "object",
          "properties": {
            "messages": { "type": "object", "additionalProperties": true },
            "schemas": { "type": "object", "additionalProperties": true }
          }
        }
      }
    },
    "testAutoGenerationPolicy": {
      "type": "object",
      "description": "Policy + structured definitions for automatic pytest generation from modeConfig.",
      "required": [
        "generationSteps",
        "testCategories",
        "fileLayout",
        "regeneration",
        "namingConventions",
        "performanceTolerancePct"
      ],
      "additionalProperties": false,
      "properties": {
        "generationSteps": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1
        },
        "testCategories": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id","description","enabled"],
            "additionalProperties": false,
            "properties": {
              "id": { "type": "string" },
              "description": { "type": "string" },
              "enabled": { "type": "boolean" }
            }
          }
        },
        "fileLayout": {
          "type": "object",
          "required": ["generatedDir","files"],
          "additionalProperties": false,
          "properties": {
            "generatedDir": { "type": "string" },
            "files": {
              "type": "array",
              "items": { "type": "string" },
              "minItems": 1
            }
          }
        },
        "regeneration": {
          "type": "object",
          "required": ["command","ciEnforced","gitDiffCheck"],
          "additionalProperties": false,
          "properties": {
            "command": { "type": "string" },
            "ciEnforced": { "type": "boolean" },
            "gitDiffCheck": { "type": "boolean" }
          }
        },
        "namingConventions": {
          "type": "object",
          "required": ["endpointTestPrefix","sseTestPrefix","wsTestPrefix"],
          "additionalProperties": false,
          "properties": {
            "endpointTestPrefix": { "type": "string" },
            "sseTestPrefix": { "type": "string" },
            "wsTestPrefix": { "type": "string" }
          }
        },
        "performanceTolerancePct": { "type": "number", "minimum": 0, "maximum": 100 },
        "fixturesSummary": { "type": "string" }
      }
    },
    "sdkGeneration": {
      "type": "object",
      "description": "TypeScript SDK generator configuration derived from schemas.",
      "required": [
        "language",
        "packageName",
        "outputDir",
        "targets",
        "httpClient",
        "streamingSupport",
        "scripts",
        "exportedTypes",
        "versioning"
      ],
      "additionalProperties": false,
      "properties": {
        "language": { "type": "string", "const": "TypeScript" },
        "packageName": { "type": "string" },
        "outputDir": { "type": "string" },
        "targets": {
          "type": "array",
          "items": { "enum": ["esm","cjs","types"] },
          "minItems": 1,
          "uniqueItems": true
        },
        "httpClient": {
          "type": "object",
          "required": ["implementation","retryStrategy"],
          "additionalProperties": false,
          "properties": {
            "implementation": { "enum": ["fetch","axios","undici"] },
            "retryStrategy": { "type": "string" },
            "timeoutMs": { "type": "integer", "minimum": 1 }
          }
        },
        "streamingSupport": {
          "type": "object",
          "required": ["sse","websocket","negotiation"],
          "additionalProperties": false,
          "properties": {
            "sse": { "type": "boolean" },
            "websocket": { "type": "boolean" },
            "negotiation": { "type": "boolean" }
          }
        },
        "scripts": {
          "type": "object",
          "required": ["build","lint","typecheck","bundle"],
          "additionalProperties": false,
          "properties": {
            "build": { "type": "string" },
            "lint": { "type": "string" },
            "typecheck": { "type": "string" },
            "bundle": { "type": "string" }
          }
        },
        "exportedTypes": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1
        },
        "versioning": {
          "type": "object",
          "required": ["strategy","initialVersion"],
          "additionalProperties": false,
          "properties": {
            "strategy": { "enum": ["semver","date"] },
            "initialVersion": { "type": "string" }
          }
        },
        "codegenTemplates": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        },
        "postGenerationNotes": { "type": "string" }
      }
    },
    "ci": {
      "type": "object",
      "description": "CI/CD workflow templates & latency smoke configuration.",
      "required": [
        "githubActions",
        "latencyThresholds",
        "regenerateTestsJob",
        "performanceJob",
        "matrix"
      ],
      "additionalProperties": false,
      "properties": {
        "githubActions": {
          "type": "object",
          "required": ["workflows"],
          "additionalProperties": false,
          "properties": {
            "workflows": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["name","on","jobs"],
                "additionalProperties": true
              },
              "minItems": 1
            }
          }
        },
        "latencyThresholds": {
          "type": "object",
          "required": ["sseFirstTokenMs","wsFirstTokenMs"],
          "additionalProperties": false,
          "properties": {
            "sseFirstTokenMs": { "type": "integer", "minimum": 1 },
            "wsFirstTokenMs": { "type": "integer", "minimum": 1 }
          }
        },
        "regenerateTestsJob": { "type": "string" },
        "performanceJob": { "type": "string" },
        "matrix": {
          "type": "object",
          "required": ["python","os"],
          "additionalProperties": false,
          "properties": {
            "python": {
              "type": "array",
              "items": { "type": "string" },
              "minItems": 1
            },
            "os": {
              "type": "array",
              "items": { "type": "string" },
              "minItems": 1
            }
          }
        }
      }
    }
  },
  "examples": [
    {
      "version": "1.0.0",
      "systemPrompt": "You are a Backend Specialist Architect specializing in FastAPI, async Python, and platform architecture. Deliver robust, observable, secure, and high‑performance chat & search capabilities. PRIORITIZE SSE (Server-Sent Events) for streaming responses; provide WebSocket fallback only when SSE is unsupported or true bidirectional messaging is required. Use Grok Code Fast for rapid iteration.",
      "modeConfig": {
        "name": "backend_dev_chat_mode",
        "version": "1.0.0",
        "description": "Backend development chat mode",
        "tools": ["codebase","usages"],
        "principles": {
          "sseFirst": true,
          "webSocketFallback": true,
          "noSecrets": true,
          "asyncOnlyForIOBound": true,
          "rejectExtraFields": true,
          "structuredErrors": true
        },
        "streaming": {
          "priorityOrder": ["sse","websocket"],
          "negotiation": {
            "sseDefault": true,
            "fallbackConditions": [
              "client_header_requests_websocket",
              "multiple_sse_failures",
              "need_bidirectional_tool_calls"
            ],
            "headersTriggeringWebSocket": [
              {"header":"X-Stream-Protocol","value":"websocket"}
            ],
            "queryFallbackParam": "transport=ws",
            "retryGuidanceSeconds": [1,2,5]
          },
          "sse": {
            "endpoint": {
              "path": "/api/chat/stream",
              "method": "POST",
              "mediaType": "text/event-stream"
            },
            "events": {
              "orderedSequence": ["start","token*","usage?","end"],
              "eventNames": ["start","token","usage","end","error"],
              "heartbeat": {
                "enabled": true,
                "format": ":heartbeat\\n\\n",
                "idleSeconds": 15
              },
              "dataShapes": {
                "start": {},
                "token": {},
                "usage": {},
                "end": {},
                "error": {}
              }
            },
            "tokenPayloadMinFields": ["delta"],
            "sanitizePerToken": true
          },
          "websocket": {
            "endpoint": { "path": "/ws/chat", "subprotocol": null },
            "frameTypes": ["start","token","end","error"],
            "frameSchemas": {
              "start": {},
              "token": {},
              "end": {},
              "error": {}
            },
            "bidirectionalSupport": true,
            "authenticateOnConnect": true
          }
        },
        "schemas": {},
        "endpoints": [
          {"path":"/api/chat","method":"POST","purpose":"Non-stream","authRequired":true,"rateLimited":true,"streaming":false},
          {"path":"/api/chat/stream","method":"POST","purpose":"SSE stream","authRequired":true,"rateLimited":true,"streaming":true,"transport":"sse"},
          {"path":"/ws/chat","method":"WEBSOCKET","purpose":"Fallback","authRequired":true,"rateLimited":true,"streaming":true,"transport":"websocket"}
        ],
        "observability": {
          "logging": {
            "structured": true,
            "traceIdHeader": "X-Request-ID",
            "includeLatencyMs": true
          },
          "metrics": {
            "counters": [
              "sse_connections_total",
              "websocket_connections_total"
            ],
            "histograms": [
              "first_token_latency_ms"
            ],
            "labels": ["transport","model"]
          }
        },
        "performanceTargets": {
          "p95FirstTokenMsSse": 350,
          "p95FirstTokenMsWebsocket": 400,
          "p95NonStreamMs": 1200
        },
        "resilience": {
          "httpClientTimeoutSeconds": 30,
          "retryBackoffSeconds": [0.25,0.5,1],
          "circuitBreakerPlaceholder": true,
          "gracefulShutdownSeconds": 20
        },
        "security": {
          "authDependency": "verify_auth",
          "rejectExtraFields": true,
          "payloadSizeLimitBytes": 1048576,
          "rateLimitPlaceholder": true,
          "bannedTermsEnvVar": "BANNED_TERMS",
          "sanitizeStreamingOutput": true
        },
        "bannedSubstringFilter": {
          "strategy": "sanitize",
          "maxRedactionsBeforeAbort": 5,
          "abortErrorCode": "BANNED_CONTENT_EXCEEDED"
        },
        "providerAbstraction": {
          "registryModule": "backend.services.provider_registry",
          "baseInterface": {
            "methods": [
              "async generate(request)",
              "async stream(request)"
            ]
          },
          "fallbackLoggingLevel": "WARN",
          "noSilentFallback": true
        },
        "testing": {
          "coverageTargetPercent": 80,
          "tests": [
            {"name":"test_chat_stream_sse","focus":["SSE ordering"]},
            {"name":"test_chat_stream_ws","focus":["WS fallback"]}
          ],
          "performance": {
            "enableSmoke": true,
            "skipIfCI": true
          }
        },
        "executionLoop": {
          "phases": ["clarify","plan","implement","test","summarize","recommend_next_action"],
          "onFailure": "capture_trace -> root_cause -> fix_plan -> re-edit"
        },
        "guardrails": [
          "Do not reverse SSE/WebSocket priority"
        ],
        "completionCriteria": {
          "baseline": [
            "SSE streaming endpoint operational",
            "WebSocket fallback stub present"
          ]
        },
        "futureEnhancements": [
          "adaptive_transport_selection"
        ]
      },
      "openapiAugmentation": {
        "x-metadata": {
          "streamingPriority": ["sse","websocket"],
          "description": "Augmented OpenAPI elements for streaming."
        },
        "paths": {
          "/api/chat/stream": {
            "post": {
              "x-streaming": true,
              "x-transport-priority": ["sse","websocket"]
            }
          },
          "/ws/chat": {
            "get": {
              "x-websocket": true
            }
          }
        },
        "components": {
          "schemas": {
            "ChatRequest": { "type":"object" }
          }
        }
      },
      "asyncapiSpec": {
        "asyncapi": "2.6.0",
        "info": {
          "title": "Chat WebSocket Fallback",
          "version": "1.0.0",
          "description": "AsyncAPI spec for /ws/chat channel."
        },
        "defaultContentType": "application/json",
        "channels": {
          "/ws/chat": {
            "description": "WebSocket fallback channel (SSE-first architecture).",
            "publish": {
              "summary": "Client sends initial request & tool messages.",
              "message": {
                "oneOf": [
                  { "$ref": "#/components/messages/ClientInit" }
                ]
              }
            },
            "subscribe": {
              "summary": "Server emits streaming frames.",
              "message": {
                "oneOf": [
                  { "$ref": "#/components/messages/StartFrame" },
                  { "$ref": "#/components/messages/TokenFrame" },
                  { "$ref": "#/components/messages/EndFrame" },
                  { "$ref": "#/components/messages/ErrorFrame" }
                ]
              }
            }
          }
        },
        "components": {
          "schemas": {
            "BaseFrame": {
              "type": "object",
              "required": ["type"],
              "properties": {
                "type": { "type": "string" }
              }
            },
            "TokenFrame": {
              "allOf": [
                { "$ref": "#/components/schemas/BaseFrame" },
                {
                  "type": "object",
                  "required": ["delta"],
                  "properties": {
                    "type": { "const": "token" },
                    "delta": { "type": "string" },
                    "index": { "type": "integer" }
                  }
                }
              ]
            }
          },
          "messages": {
            "ClientInit": {
              "name": "ClientInit",
              "payload": {
                "type": "object",
                "required": ["messages","model"],
                "properties": {
                  "messages": { "type": "array" },
                  "model": { "type": "string" }
                }
              }
            },
            "StartFrame": {
              "name": "StartFrame",
              "payload": {
                "type": "object",
                "required": ["type"],
                "properties": { "type": { "const": "start" } }
              }
            },
            "TokenFrame": {
              "name": "TokenFrame",
              "payload": { "$ref": "#/components/schemas/TokenFrame" }
            },
            "EndFrame": {
              "name": "EndFrame",
              "payload": {
                "type": "object",
                "required": ["type"],
                "properties": {
                  "type": { "const": "end" },
                  "usage": { "type":"object" }
                }
              }
            },
            "ErrorFrame": {
              "name": "ErrorFrame",
              "payload": {
                "type": "object",
                "required": ["type","message"],
                "properties": {
                  "type": { "const":"error" },
                  "code": { "type":"string" },
                  "message": { "type":"string" }
                }
              }
            }
          }
        }
      },
      "testAutoGenerationPolicy": {
        "generationSteps": [
          "validate_config",
          "derive_endpoint_tests",
          "derive_streaming_tests",
          "derive_negotiation_tests",
          "derive_banned_filter_tests",
          "derive_performance_tests",
          "derive_metrics_tests",
          "write_files"
        ],
        "testCategories": [
          {"id":"structure","description":"Endpoint reachability","enabled":true},
            {"id":"sse","description":"SSE sequence & heartbeats","enabled":true},
            {"id":"ws","description":"WebSocket fallback frames","enabled":true},
            {"id":"performance","description":"Latency targets","enabled":true}
        ],
        "fileLayout": {
          "generatedDir": "tests/generated",
          "files": [
            "test_generated_endpoints.py",
            "test_generated_streaming.py"
          ]
        },
        "regeneration": {
          "command": "python scripts/generate_tests.py",
          "ciEnforced": true,
          "gitDiffCheck": true
        },
        "namingConventions": {
          "endpointTestPrefix": "test_ep_",
          "sseTestPrefix": "test_sse_",
          "wsTestPrefix": "test_ws_"
        },
        "performanceTolerancePct": 10,
        "fixturesSummary": "Fixtures: client, auth_headers, mock_provider_stream, metrics_client."
      },
      "sdkGeneration": {
        "language": "TypeScript",
        "packageName": "@acme/chat-backend-sdk",
        "outputDir": "sdk/ts",
        "targets": ["esm","types"],
        "httpClient": {
          "implementation": "fetch",
          "retryStrategy": "exponential",
          "timeoutMs": 30000
        },
        "streamingSupport": {
          "sse": true,
          "websocket": true,
          "negotiation": true
        },
        "scripts": {
          "build": "tsc -p tsconfig.json",
          "lint": "eslint 'src/**/*.{ts,tsx}'",
          "typecheck": "tsc --noEmit",
          "bundle": "tsup src/index.ts --dts --format esm"
        },
        "exportedTypes": [
          "ChatRequest",
          "ChatMessage",
          "SSEEvent",
          "WSFrame"
        ],
        "versioning": {
          "strategy": "semver",
          "initialVersion": "0.1.0"
        },
        "codegenTemplates": {
          "sseClient": "templates/sseClient.mustache"
        },
        "postGenerationNotes": "Run npm publish after version bump."
      },
      "ci": {
        "githubActions": {
          "workflows": [
            {
              "name": "ci",
              "on": {
                "push": { "branches": ["main"] },
                "pull_request": { "branches": ["main"] }
              },
              "jobs": {
                "generate-tests": {
                  "runs-on": "ubuntu-latest",
                  "steps": [
                    {"name":"Checkout","uses":"actions/checkout@v4"},
                    {"name":"Setup Python","uses":"actions/setup-python@v5","with":{"python-version":"3.11"}},
                    {"name":"Install deps","run":"pip install -r requirements.txt"},
                    {"name":"Generate tests","run":"python scripts/generate_tests.py"},
                    {"name":"Check diff","run":"git diff --exit-code || (echo 'Generated tests out of date' && exit 1)"}
                  ]
                },
                "tests": {
                  "runs-on": "ubuntu-latest",
                  "needs": ["generate-tests"],
                  "strategy": { "matrix": { "python": ["3.11"], "os": ["ubuntu-latest"] } },
                  "steps": [
                    {"name":"Checkout","uses":"actions/checkout@v4"},
                    {"name":"Setup Python","uses":"actions/setup-python@v5","with":{"python-version":"3.11"}},
                    {"name":"Install deps","run":"pip install -r requirements.txt"},
                    {"name":"Run tests","run":"pytest -q --maxfail=1"}
                  ]
                },
                "latency-smoke": {
                  "runs-on": "ubuntu-latest",
                  "if": "github.ref == 'refs/heads/main'",
                  "needs": ["tests"],
                  "steps": [
                    {"name":"Checkout","uses":"actions/checkout@v4"},
                    {"name":"Setup Python","uses":"actions/setup-python@v5","with":{"python-version":"3.11"}},
                    {"name":"Install deps","run":"pip install -r requirements.txt"},
                    {"name":"Run latency smoke","run":"pytest -q -k performance --maxfail=1"}
                  ]
                }
              }
            }
          ]
        },
        "latencyThresholds": {
          "sseFirstTokenMs": 350,
          "wsFirstTokenMs": 400
        },
        "regenerateTestsJob": "generate-tests",
        "performanceJob": "latency-smoke",
        "matrix": {
          "python": ["3.11"],
          "os": ["ubuntu-latest"]
        }
      }
    }
  ]
}
```