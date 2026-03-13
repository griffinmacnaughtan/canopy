import { useState, useCallback } from "react";
import { api } from "@/api/client";

interface UseCopilotOptions {
  portfolioId?: string;
}

interface UseCopilotReturn {
  response: string;
  isStreaming: boolean;
  error: Error | null;
  sendQuestion: (question: string) => Promise<void>;
  reset: () => void;
}

export function useCopilot(options: UseCopilotOptions = {}): UseCopilotReturn {
  const [response, setResponse] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendQuestion = useCallback(
    async (question: string) => {
      if (!question.trim()) return;

      setResponse("");
      setIsStreaming(true);
      setError(null);

      try {
        for await (const chunk of api.streamCopilot(
          question,
          options.portfolioId
        )) {
          setResponse((prev) => prev + chunk);
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Unknown error"));
      } finally {
        setIsStreaming(false);
      }
    },
    [options.portfolioId]
  );

  const reset = useCallback(() => {
    setResponse("");
    setError(null);
  }, []);

  return {
    response,
    isStreaming,
    error,
    sendQuestion,
    reset,
  };
}
