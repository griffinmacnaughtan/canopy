import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FlaskConical,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronRight,
  Loader2,
  Clock,
  BarChart3,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui";
import { api } from "@/api/client";
import type { EvalRunResponse, EvalCaseResult } from "@/types";

const CATEGORY_CONFIG: Record<
  string,
  { label: string; color: string; icon: React.ReactNode }
> = {
  good_prompt: {
    label: "Good Prompts",
    color: "text-emerald-600 bg-emerald-50 border-emerald-200",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  bad_prompt: {
    label: "Bad Prompts",
    color: "text-amber-600 bg-amber-50 border-amber-200",
    icon: <XCircle className="h-3 w-3" />,
  },
  adversarial: {
    label: "Adversarial",
    color: "text-red-600 bg-red-50 border-red-200",
    icon: <Shield className="h-3 w-3" />,
  },
  edge_case: {
    label: "Edge Cases",
    color: "text-blue-600 bg-blue-50 border-blue-200",
    icon: <BarChart3 className="h-3 w-3" />,
  },
};

function ScoreBar({ score, max = 5 }: { score: number; max?: number }) {
  const pct = (score / max) * 100;
  const color =
    pct >= 80
      ? "bg-emerald-500"
      : pct >= 60
        ? "bg-amber-500"
        : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <span className="text-xs font-mono text-muted-foreground w-8">
        {score.toFixed(1)}
      </span>
    </div>
  );
}

function CaseRow({ result }: { result: EvalCaseResult }) {
  const [expanded, setExpanded] = useState(false);
  const cat = CATEGORY_CONFIG[result.category] || CATEGORY_CONFIG.edge_case;

  return (
    <div className="border border-gray-100 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50/50 transition-colors"
      >
        {result.passed ? (
          <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
        ) : (
          <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
        )}
        <span
          className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${cat.color} flex-shrink-0`}
        >
          {result.case_id}
        </span>
        <span className="text-xs text-foreground truncate flex-1">
          {result.prompt || "(empty prompt)"}
        </span>
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
        )}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-100"
          >
            <div className="px-3 py-2 space-y-2 bg-gray-50/30">
              <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1">
                  Scores
                </p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                  {Object.entries(result.scores).map(([dim, score]) => (
                    <div key={dim} className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground capitalize">
                        {dim}
                      </span>
                      <ScoreBar score={score} />
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1">
                  Reasoning
                </p>
                <p className="text-xs text-foreground/80">{result.reasoning}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function EvalPanel() {
  const [evalResult, setEvalResult] = useState<EvalRunResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataset, setDataset] = useState("climate_copilot");

  const runEvals = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const result = await api.runEvals({ dataset });
      setEvalResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Eval run failed");
    } finally {
      setIsRunning(false);
    }
  };

  // Group results by category
  const grouped: Record<string, EvalCaseResult[]> = {};
  if (evalResult) {
    for (const r of evalResult.results) {
      (grouped[r.category] ||= []).push(r);
    }
  }

  return (
    <div className="space-y-4">
      {/* Run controls */}
      <div className="flex items-center gap-3">
        <select
          value={dataset}
          onChange={(e) => setDataset(e.target.value)}
          className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
          disabled={isRunning}
        >
          <option value="climate_copilot">Climate Copilot</option>
          <option value="safety">Safety & Adversarial</option>
          <option value="all">All Datasets</option>
        </select>
        <Button
          size="sm"
          onClick={runEvals}
          disabled={isRunning}
          className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
        >
          {isRunning ? (
            <>
              <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <FlaskConical className="h-3 w-3 mr-1.5" />
              Run Evals
            </>
          )}
        </Button>
      </div>

      {error && (
        <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Results */}
      {evalResult && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {/* Summary bar */}
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-gray-50 rounded-lg px-3 py-2 text-center">
              <p className="text-lg font-bold text-foreground">
                {evalResult.total_cases}
              </p>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                Cases
              </p>
            </div>
            <div className="bg-emerald-50 rounded-lg px-3 py-2 text-center">
              <p className="text-lg font-bold text-emerald-600">
                {evalResult.passed}
              </p>
              <p className="text-[10px] text-emerald-600/70 uppercase tracking-wider">
                Passed
              </p>
            </div>
            <div className="bg-red-50 rounded-lg px-3 py-2 text-center">
              <p className="text-lg font-bold text-red-600">
                {evalResult.failed}
              </p>
              <p className="text-[10px] text-red-600/70 uppercase tracking-wider">
                Failed
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg px-3 py-2 text-center">
              <p className="text-lg font-bold text-blue-600">
                {(evalResult.pass_rate * 100).toFixed(0)}%
              </p>
              <p className="text-[10px] text-blue-600/70 uppercase tracking-wider">
                Pass Rate
              </p>
            </div>
          </div>

          {/* Average scores */}
          <div className="bg-gray-50/50 rounded-lg px-3 py-2">
            <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Average Scores by Dimension
            </p>
            <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
              {Object.entries(evalResult.avg_scores).map(([dim, score]) => (
                <div key={dim} className="flex items-center justify-between">
                  <span className="text-xs text-foreground capitalize">
                    {dim}
                  </span>
                  <ScoreBar score={score} />
                </div>
              ))}
            </div>
          </div>

          {/* Duration */}
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            Completed in {(evalResult.duration_ms / 1000).toFixed(1)}s
          </div>

          {/* Results by category */}
          {Object.entries(grouped).map(([category, results]) => {
            const cat =
              CATEGORY_CONFIG[category] || CATEGORY_CONFIG.edge_case;
            const passed = results.filter((r) => r.passed).length;
            return (
              <div key={category} className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-medium px-2 py-0.5 rounded-full border flex items-center gap-1 ${cat.color}`}
                  >
                    {cat.icon}
                    {cat.label}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {passed}/{results.length} passed
                  </span>
                </div>
                <div className="space-y-1">
                  {results.map((r) => (
                    <CaseRow key={r.case_id} result={r} />
                  ))}
                </div>
              </div>
            );
          })}
        </motion.div>
      )}

      {/* Empty state */}
      {!evalResult && !isRunning && (
        <div className="text-center py-6 text-muted-foreground">
          <FlaskConical className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="text-xs">
            Run the evaluation suite to test LLM response quality
          </p>
          <p className="text-[10px] mt-1 opacity-70">
            Tests good prompts, bad prompts, adversarial inputs, and edge cases
          </p>
        </div>
      )}
    </div>
  );
}
