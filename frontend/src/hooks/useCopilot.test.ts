import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCopilot } from "./useCopilot";

// Force demo mode so streaming uses mock data
vi.stubEnv("VITE_DEMO_MODE", "true");

describe("useCopilot", () => {
  it("initialises with empty state", () => {
    const { result } = renderHook(() => useCopilot());

    expect(result.current.response).toBe("");
    expect(result.current.lastQuestion).toBe("");
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it(
    "streams a response for a valid question",
    async () => {
      const { result } = renderHook(() => useCopilot());

      await act(async () => {
        await result.current.sendQuestion("What are the top climate risks?");
      });

      expect(result.current.response.length).toBeGreaterThan(0);
      expect(result.current.lastQuestion).toBe("What are the top climate risks?");
      expect(result.current.isStreaming).toBe(false);
      expect(result.current.error).toBeNull();
    },
    15_000 // simulateStream yields word-by-word with ~30ms delays
  );

  it("ignores empty questions", async () => {
    const { result } = renderHook(() => useCopilot());

    await act(async () => {
      await result.current.sendQuestion("   ");
    });

    expect(result.current.response).toBe("");
    expect(result.current.lastQuestion).toBe("");
  });

  it(
    "resets state correctly",
    async () => {
      const { result } = renderHook(() => useCopilot());

      // First, get a response
      await act(async () => {
        await result.current.sendQuestion("Describe transition risks");
      });
      expect(result.current.response.length).toBeGreaterThan(0);

      // Now reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.response).toBe("");
      expect(result.current.lastQuestion).toBe("");
      expect(result.current.error).toBeNull();
    },
    15_000
  );
});
