import { createContext, useContext, useRef, useCallback, type ReactNode } from "react";

interface CopilotContextType {
  /** Scroll to the copilot section and pre-fill a question */
  askCopilot: (question: string) => void;
  /** Register the copilot element ref and question setter from CopilotWorkspace */
  registerCopilot: (ref: HTMLElement | null, setQuestion: (q: string) => void) => void;
}

const CopilotContext = createContext<CopilotContextType | undefined>(undefined);

export function CopilotProvider({ children }: { children: ReactNode }) {
  const copilotRef = useRef<HTMLElement | null>(null);
  const setQuestionRef = useRef<((q: string) => void) | null>(null);

  const registerCopilot = useCallback(
    (ref: HTMLElement | null, setQuestion: (q: string) => void) => {
      copilotRef.current = ref;
      setQuestionRef.current = setQuestion;
    },
    [],
  );

  const askCopilot = useCallback((question: string) => {
    if (setQuestionRef.current) {
      setQuestionRef.current(question);
    }
    if (copilotRef.current) {
      copilotRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
      // Focus the textarea after scroll completes
      setTimeout(() => {
        const textarea = copilotRef.current?.querySelector("textarea");
        textarea?.focus();
      }, 400);
    }
  }, []);

  return (
    <CopilotContext.Provider value={{ askCopilot, registerCopilot }}>
      {children}
    </CopilotContext.Provider>
  );
}

export function useCopilotContext() {
  const context = useContext(CopilotContext);
  if (!context) {
    throw new Error("useCopilotContext must be used within a CopilotProvider");
  }
  return context;
}
