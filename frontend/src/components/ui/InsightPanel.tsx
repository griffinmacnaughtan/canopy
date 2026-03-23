import { useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

interface InsightPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  onAskCopilot?: () => void;
}

export function InsightPanel({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  children,
  onAskCopilot,
}: InsightPanelProps) {
  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen, handleEscape]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className={cn(
              "fixed right-0 top-0 h-full w-full sm:w-[480px] z-50",
              "bg-white border-l border-border shadow-2xl",
              "flex flex-col",
            )}
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-border">
              <div className="flex items-center gap-3 min-w-0">
                {icon && (
                  <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 shrink-0">
                    {icon}
                  </div>
                )}
                <div className="min-w-0">
                  <h2 className="text-lg font-bold text-foreground truncate">
                    {title}
                  </h2>
                  {subtitle && (
                    <p className="text-sm text-muted-foreground mt-0.5 truncate">
                      {subtitle}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-gray-400 hover:text-foreground hover:bg-gray-100 transition-colors shrink-0 ml-2"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {children}
            </div>

            {/* Ask Copilot Footer */}
            {onAskCopilot && (
              <div className="border-t border-border p-4">
                <button
                  onClick={onAskCopilot}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
                >
                  <Bot className="h-4 w-4" />
                  Ask Copilot About This
                </button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
