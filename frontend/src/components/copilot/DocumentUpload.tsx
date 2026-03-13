import { useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, X, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui";
import { useDocuments } from "@/hooks/useDocuments";

interface DocumentUploadProps {
  disabled?: boolean;
}

export function DocumentUpload({ disabled }: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const {
    documents,
    totalChars,
    uploadFile,
    isUploading,
    uploadError,
    clearDocuments,
    isClearing,
  } = useDocuments();

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await uploadFile(file);
    } catch {
      // Error is handled by the hook
    }

    // Reset input so the same file can be uploaded again if needed
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleClear = async () => {
    try {
      await clearDocuments();
    } catch {
      // Error is handled by the hook
    }
  };

  const formatCharCount = (count: number) => {
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}k`;
    }
    return count.toString();
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled || isUploading}
        />

        <Button
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isUploading}
          className="gap-2"
        >
          {isUploading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Upload className="h-3 w-3" />
          )}
          {isUploading ? "Uploading..." : "Upload PDF"}
        </Button>

        {documents.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            disabled={disabled || isClearing}
            className="gap-2 text-muted-foreground hover:text-destructive"
          >
            {isClearing ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <X className="h-3 w-3" />
            )}
            Clear all
          </Button>
        )}
      </div>

      {/* Error display */}
      <AnimatePresence>
        {uploadError && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-2 p-2 rounded-lg bg-destructive/10 text-destructive text-xs"
          >
            <AlertCircle className="h-3 w-3 flex-shrink-0" />
            <span>
              {uploadError instanceof Error
                ? uploadError.message
                : "Upload failed"}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Document list */}
      <AnimatePresence>
        {documents.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-1"
          >
            <div className="text-xs text-muted-foreground mb-1">
              {documents.length} document{documents.length !== 1 ? "s" : ""} ({formatCharCount(totalChars)} chars)
            </div>
            {documents.map((doc, index) => (
              <motion.div
                key={doc.filename}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center gap-2 text-xs text-muted-foreground bg-secondary/50 rounded px-2 py-1"
              >
                <FileText className="h-3 w-3 flex-shrink-0" />
                <span className="truncate">{doc.filename}</span>
                <span className="text-muted-foreground/60 ml-auto">
                  {formatCharCount(doc.char_count)}
                </span>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
