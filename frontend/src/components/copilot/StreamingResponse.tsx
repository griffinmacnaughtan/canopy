import { useMemo, ReactNode } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";

interface StreamingResponseProps {
  content: string;
  isStreaming: boolean;
}

interface MarkdownComponentProps {
  children?: ReactNode;
}

function preprocessMarkdown(text: string): string {
  if (!text) return "";

  let processed = text;

  // Normalize line endings
  processed = processed.replace(/\r\n/g, "\n");

  // Ensure headers have blank lines before them
  processed = processed.replace(/([^\n])\n(#{1,6}\s)/g, "$1\n\n$2");

  // Ensure bold section titles have blank lines before them
  // Match patterns like "**Title**:" or "**Title**\n"
  processed = processed.replace(/([^\n])\n(\*\*[A-Z][^*\n]+\*\*)/g, "$1\n\n$2");

  // Fix cases where bold markers run together without spaces
  processed = processed.replace(/\*\*\*\*/g, "**\n\n**");

  // Ensure bullet points have proper formatting
  processed = processed.replace(/([^\n])\n([-•]\s)/g, "$1\n\n$2");

  // Remove any null bytes or weird characters that might break parsing
  processed = processed.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, "");

  return processed;
}

export function StreamingResponse({
  content,
  isStreaming,
}: StreamingResponseProps) {
  const processedContent = useMemo(() => {
    return preprocessMarkdown(content);
  }, [content]);

  if (!content && !isStreaming) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 p-4 rounded-lg bg-secondary/50 border border-border"
    >
      <div className="prose prose-sm max-w-none [&>*:first-child]:mt-0">
        <ReactMarkdown
          components={{
            h1: ({ children }: MarkdownComponentProps) => (
              <h1 className="text-xl font-bold text-foreground mt-6 mb-3 first:mt-0">
                {children}
              </h1>
            ),
            h2: ({ children }: MarkdownComponentProps) => (
              <h2 className="text-lg font-semibold text-foreground mt-5 mb-2 first:mt-0">
                {children}
              </h2>
            ),
            h3: ({ children }: MarkdownComponentProps) => (
              <h3 className="text-base font-semibold text-foreground mt-4 mb-2 first:mt-0">
                {children}
              </h3>
            ),
            p: ({ children }: MarkdownComponentProps) => (
              <p className="text-foreground/90 my-2 leading-relaxed">{children}</p>
            ),
            strong: ({ children }: MarkdownComponentProps) => (
              <strong className="font-semibold text-primary">{children}</strong>
            ),
            ul: ({ children }: MarkdownComponentProps) => (
              <ul className="list-disc list-outside ml-4 my-2 space-y-1">{children}</ul>
            ),
            ol: ({ children }: MarkdownComponentProps) => (
              <ol className="list-decimal list-outside ml-4 my-2 space-y-1">{children}</ol>
            ),
            li: ({ children }: MarkdownComponentProps) => (
              <li className="text-foreground/90">{children}</li>
            ),
            code: ({ children }: MarkdownComponentProps) => (
              <code className="bg-secondary px-1.5 py-0.5 rounded text-accent text-sm">
                {children}
              </code>
            ),
            blockquote: ({ children }: MarkdownComponentProps) => (
              <blockquote className="border-l-2 border-primary pl-4 my-3 text-muted-foreground italic">
                {children}
              </blockquote>
            ),
          }}
        >
          {processedContent}
        </ReactMarkdown>
        {isStreaming && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{
              repeat: Infinity,
              repeatType: "reverse",
              duration: 0.5,
            }}
            className="inline-block w-2 h-4 ml-1 bg-primary align-middle"
          />
        )}
      </div>
    </motion.div>
  );
}
