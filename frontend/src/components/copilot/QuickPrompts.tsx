import { motion } from "framer-motion";
import {
  AlertTriangle,
  TrendingUp,
  Target,
  FileText,
  Zap,
} from "lucide-react";

interface QuickPromptsProps {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

const QUICK_PROMPTS = [
  {
    icon: AlertTriangle,
    label: "Top Risks",
    prompt: "What are the top climate risks in my portfolio and how should I prioritize them?",
  },
  {
    icon: TrendingUp,
    label: "Opportunities",
    prompt: "What green growth opportunities exist in my portfolio?",
  },
  {
    icon: Target,
    label: "SBTi Targets",
    prompt: "How should I set science-based targets for my portfolio?",
  },
  {
    icon: FileText,
    label: "TCFD Report",
    prompt: "What should I include in a TCFD-aligned climate disclosure for this portfolio?",
  },
  {
    icon: Zap,
    label: "Quick Actions",
    prompt: "What immediate actions can I take to reduce portfolio climate risk?",
  },
];

export function QuickPrompts({ onSelect, disabled }: QuickPromptsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {QUICK_PROMPTS.map((prompt, index) => (
        <motion.button
          key={prompt.label}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.04 }}
          onClick={() => onSelect(prompt.prompt)}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border text-muted-foreground bg-white hover:bg-gray-50 hover:border-gray-300 hover:text-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500/30 transition-colors disabled:opacity-50 disabled:pointer-events-none"
        >
          <prompt.icon className="h-3 w-3" />
          {prompt.label}
        </motion.button>
      ))}
    </div>
  );
}
