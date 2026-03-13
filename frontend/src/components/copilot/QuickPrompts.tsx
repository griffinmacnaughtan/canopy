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
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          onClick={() => onSelect(prompt.prompt)}
          disabled={disabled}
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-full bg-white/90 backdrop-blur-sm border border-emerald-200/60 text-foreground hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:ring-offset-2 focus:ring-offset-background transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none shadow-sm hover:shadow-md"
        >
          <prompt.icon className="h-3.5 w-3.5 text-emerald-600" />
          {prompt.label}
        </motion.button>
      ))}
    </div>
  );
}
