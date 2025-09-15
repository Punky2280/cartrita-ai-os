// Test to verify that the streaming timeout error is fixed
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { StreamingService } from "@/services/streaming";
import type { ChatRequest } from "@/types";

describe("Streaming Service Timeout Fix", () => {
  let streamingService: StreamingService;

  beforeEach(() => {
    streamingService = new StreamingService("http://localhost:8003");
    // Reset fetch mock
    vi.restoreAllMocks();
  });

  afterEach(() => {
    // Clean up any running requests
    streamingService.cancelRequest();
  });

  it("should return fallback on timeout and not call onError", async () => {
    const request: ChatRequest = {
      message: "Test timeout handling",
      conversation_id: "timeout-test",
    };

    let onErrorCalled = false;
    let onCompleteCalled = false;
    let onCompletePayload: any = null;

    const options = {
      timeout: 100, // Very short timeout to trigger timeout
      onError: (_error: Error) => {
        onErrorCalled = true;
      },
      onChunk: vi.fn(),
      onComplete: (payload: any) => {
        onCompleteCalled = true;
        onCompletePayload = payload;
      },
    };

    // Mock fetch to simulate a slow response that respects AbortController
    global.fetch = vi.fn().mockImplementation((input: RequestInfo, init?: RequestInit) => {
      const signal = init?.signal as AbortSignal | undefined;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          resolve({ ok: true, body: new ReadableStream() } as any);
        }, 200);

        if (signal) {
          const onAbort = () => {
            clearTimeout(timer);
            const err = new Error("The operation was aborted.");
            (err as any).name = "AbortError";
            reject(err);
          };
          if (signal.aborted) {
            onAbort();
          } else {
            signal.addEventListener("abort", onAbort, { once: true });
          }
        }
      });
    });

    await streamingService.streamChat(request, options);

    // Verify timeout produced fallback via onComplete (not onError)
    expect(onErrorCalled).toBe(false);
    expect(onCompleteCalled).toBe(true);
    expect(onCompletePayload).toBeTruthy();
    expect(onCompletePayload.agent_type).toBe("fallback");
    expect(onCompletePayload?.metadata?.fallback_used).toBe(true);
  });

  it("should handle successful requests without timeout", async () => {
    const request: ChatRequest = {
      message: "Test successful request",
      conversation_id: "success-test",
    };

    let successCalled = false;
    let errorCalled = false;

    const options = {
      timeout: 5000, // Generous timeout
      onError: () => {
        errorCalled = true;
      },
      onChunk: vi.fn(),
      onComplete: () => {
        successCalled = true;
      },
    };

    // Mock successful fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: new ReadableStream({
        start(controller) {
          controller.enqueue(
            new TextEncoder().encode(
              'data: {"content":"test","done":false}\n\n',
            ),
          );
          controller.enqueue(
            new TextEncoder().encode('data: {"content":"","done":true}\n\n'),
          );
          controller.close();
        },
      }),
    });

    await streamingService.streamChat(request, options);

    // Should complete successfully without errors
    expect(errorCalled).toBe(false);
  });

  it("should properly cancel requests when controller is aborted", async () => {
    const request: ChatRequest = {
      message: "Test cancellation",
      conversation_id: "cancel-test",
    };

    const onError = vi.fn();
    const onComplete = vi.fn();

    const options = {
      onError,
      onChunk: vi.fn(),
      onComplete,
    };

    // Mock fetch that takes a while and supports AbortController
    global.fetch = vi.fn().mockImplementation((input: RequestInfo, init?: RequestInit) => {
      const signal = init?.signal as AbortSignal | undefined;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => resolve({ ok: true, body: new ReadableStream() } as any), 1000);
        if (signal) {
          const onAbort = () => {
            clearTimeout(timer);
            const err = new Error("The operation was aborted.");
            (err as any).name = "AbortError";
            reject(err);
          };
          if (signal.aborted) {
            onAbort();
          } else {
            signal.addEventListener("abort", onAbort, { once: true });
          }
        }
      });
    });

    // Start request
    const requestPromise = streamingService.streamChat(request, options);

    // Cancel immediately
    streamingService.cancelRequest();

  await requestPromise;

    // Should handle cancellation gracefully without invoking callbacks
    expect(onError).not.toHaveBeenCalled();
    expect(onComplete).not.toHaveBeenCalled();
  });
});
