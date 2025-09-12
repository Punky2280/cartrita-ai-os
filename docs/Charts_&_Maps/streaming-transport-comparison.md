# Streaming Transport Comparison

| Criterion | Server-Sent Events (SSE) | WebSocket | Hybrid (SSE primary, WS fallback) |
|-----------|--------------------------|-----------|----------------------------------|
| Directionality | Unidirectional (server -> client) | Bidirectional | Adaptive: SSE for output, WS when input events needed |
| Browser Support | ~98% modern | ~98% modern | Matches superset |
| Simplicity | Very high (HTTP) | Moderate (handshake, state mgmt) | Conditional complexity |
| Backpressure Handling | Limited (retry, buffering) | Application-level control | Hybrid strategy |
| Best For | Token streaming, events, low overhead | Collaborative tools, realtime cursor updates | AI chat with occasional tool streaming |
| Connection Overhead | Minimal | Higher (persistent TCP, ping/pong) | Optimized by usage pattern |
| Proxy/CDN Compatibility | Excellent | Sometimes restricted | Fallback ensures reachability |
| Security Surface | Smaller | Larger (custom protocol) | Balanced via least privilege |
| Tool Invocation | Emulated via events | Native duplex calls | Escalate WS only when needed |
| Implementation Effort | Low | Medium | Medium (negotiation logic) |
| Failure Modes | Auto-reconnect built-in | Must implement heartbeat/retry | Negotiation with health metrics |

\n## Summary\n\nSSE remains the optimal default for deterministic token streaming with minimal infrastructure overhead, while WebSocket is reserved for interactive, tool-rich or bidirectional episodes. The hybrid model minimizes complexity while retaining capability.
