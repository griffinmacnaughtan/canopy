import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, RefreshCw, AlertCircle, Paperclip, FileText, X, Loader2, Sparkles } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent, Button, Skeleton } from "@/components/ui";
import { useCopilot, usePortfolio } from "@/hooks";
import { useDocuments } from "@/hooks/useDocuments";
import { StreamingResponse } from "./StreamingResponse";
import { QuickPrompts } from "./QuickPrompts";
import { api } from "@/api/client";

function CopilotSkeleton() {
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <Skeleton className="h-6 w-40" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-24 w-full mb-4" />
        <Skeleton className="h-10 w-full" />
      </CardContent>
    </Card>
  );
}

export function CopilotWorkspace() {
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolio();
  const { response, isStreaming, error, sendQuestion, reset } = useCopilot({
    portfolioId: portfolio?.id,
  });
  const {
    documents,
    uploadFile,
    isUploading,
    uploadError,
    clearDocuments,
    isClearing,
  } = useDocuments();

  const [question, setQuestion] = useState("");
  const isBusy = isStreaming || isUploading;
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [question]);

  if (portfolioLoading) {
    return <CopilotSkeleton />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isBusy) return;

    await sendQuestion(question);
    setQuestion("");
  };

  const handleQuickPrompt = async (prompt: string) => {
    setQuestion(prompt);
    await sendQuestion(prompt);
    setQuestion("");
  };

  const handleReset = () => {
    reset();
    setQuestion("");
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await uploadFile(file);
    } catch {
      // Error handled by hook
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const formatCharCount = (count: number) => {
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}k`;
    }
    return count.toString();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <Card className="relative overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300 border-emerald-200/50 bg-white/90 backdrop-blur-sm">
        {/* Premium gradient accent bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-emerald-500 via-forest-500 to-emerald-400" />

        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500 to-forest-600 shadow-md shadow-emerald-500/20">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="text-foreground font-semibold">Canopy AI</span>
              {api.isDemoMode() ? (
                <p className="text-xs text-amber-600 font-medium mt-0.5 flex items-center gap-1">
                  <Sparkles className="h-3 w-3" />
                  Demo Mode - Run locally for live AI
                </p>
              ) : (
                <p className="text-xs text-emerald-600/70 font-medium mt-0.5">
                  Powered by Claude
                </p>
              )}
            </div>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Quick prompts */}
          <QuickPrompts onSelect={handleQuickPrompt} disabled={isBusy} />

          {/* Uploaded documents display */}
          <AnimatePresence>
            {documents.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="flex flex-wrap items-center gap-2"
              >
                {documents.map((doc) => (
                  <motion.div
                    key={doc.filename}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex items-center gap-2 text-xs bg-emerald-100 text-emerald-700 rounded-full px-3 py-1.5 border border-emerald-200"
                  >
                    <FileText className="h-3 w-3" />
                    <span className="max-w-[150px] truncate font-medium">{doc.filename}</span>
                    <span className="text-emerald-600/70">({formatCharCount(doc.char_count)})</span>
                  </motion.div>
                ))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => clearDocuments()}
                  disabled={isClearing || isBusy}
                  className="h-7 px-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                >
                  {isClearing ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <X className="h-3 w-3" />
                  )}
                </Button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Upload error */}
          <AnimatePresence>
            {uploadError && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-xs border border-destructive/20"
              >
                <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
                <span>
                  {uploadError instanceof Error ? uploadError.message : "Upload failed"}
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Question input with integrated upload button */}
          <form onSubmit={handleSubmit}>
            <div className="relative">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
                disabled={isBusy}
              />

              <textarea
                ref={textareaRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about your portfolio's climate risks, opportunities, or regulatory readiness..."
                className="w-full min-h-[100px] max-h-[200px] p-4 pl-12 pr-14 rounded-xl bg-emerald-50/50 border border-emerald-200/60 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-400 resize-none transition-all duration-200"
                disabled={isBusy}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />

              {/* Attachment button - bottom left */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isBusy}
                className="absolute bottom-3 left-3 p-2 rounded-lg text-emerald-600/60 hover:text-emerald-600 hover:bg-emerald-100 transition-colors disabled:opacity-50 disabled:pointer-events-none"
                title="Attach PDF"
              >
                {isUploading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Paperclip className="h-4 w-4" />
                )}
              </button>

              {/* Send button - bottom right */}
              <Button
                type="submit"
                size="icon"
                disabled={!question.trim() || isBusy}
                className="absolute bottom-3 right-3 bg-gradient-to-r from-emerald-500 to-forest-600 hover:from-emerald-600 hover:to-forest-700 shadow-lg shadow-emerald-500/25"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </form>

          {/* Error display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm border border-destructive/20"
            >
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error.message}</span>
            </motion.div>
          )}

          {/* Streaming response */}
          <StreamingResponse content={response} isStreaming={isStreaming} />

          {/* Reset button */}
          {response && !isStreaming && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-end"
            >
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="text-muted-foreground hover:text-foreground"
              >
                <RefreshCw className="h-3 w-3 mr-2" />
                New Question
              </Button>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
