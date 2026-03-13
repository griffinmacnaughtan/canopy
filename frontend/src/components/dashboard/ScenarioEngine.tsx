import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, AlertCircle, TrendingDown, Factory, Info, FlaskConical } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Skeleton,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui";
import { useScenarios, useRunScenario, usePortfolio } from "@/hooks";
import type { ScenarioResponse } from "@/types";

const SCENARIO_DESCRIPTIONS: Record<string, { description: string; carbonPrice: string; impact: string }> = {
  "Orderly Net Zero 2050": {
    description: "Global cooperation achieves net-zero by 2050 through gradual, well-planned policies.",
    carbonPrice: "$120/tCO2e",
    impact: "Lower transition risk, manageable adjustments",
  },
  "Delayed Transition": {
    description: "Climate action is postponed until 2030, requiring aggressive catch-up measures.",
    carbonPrice: "$180/tCO2e",
    impact: "High transition risk, sudden policy shifts",
  },
  "Hot House World": {
    description: "Limited climate action leads to severe physical risks from unchecked warming.",
    carbonPrice: "$40/tCO2e",
    impact: "Extreme physical risks, asset damage",
  },
};

function ScenarioSkeleton() {
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <Skeleton className="h-5 w-36" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-10 w-full mb-4" />
        <Skeleton className="h-10 w-24" />
      </CardContent>
    </Card>
  );
}

function ResultCard({ result }: { result: ScenarioResponse }) {
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="mt-4 pt-4 border-t border-border"
    >
      <div className="grid grid-cols-2 gap-4 mb-4">
        <TooltipProvider delayDuration={200}>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-destructive/10">
              <TrendingDown className="h-4 w-4 text-destructive" />
            </div>
            <div>
              <div className="flex items-center gap-1">
                <p className="text-xs text-muted-foreground">EBITDA Impact</p>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="text-muted-foreground/50 hover:text-muted-foreground">
                      <Info className="h-3 w-3" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <p className="text-sm">Estimated impact on earnings before interest, taxes, depreciation, and amortization from carbon pricing and revenue shocks.</p>
                  </TooltipContent>
                </Tooltip>
              </div>
              <p className="text-xl font-bold text-destructive">
                {result.est_ebitda_impact_pct.toFixed(2)}%
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-success/10">
              <Factory className="h-4 w-4 text-success" />
            </div>
            <div>
              <div className="flex items-center gap-1">
                <p className="text-xs text-muted-foreground">Emissions Change</p>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="text-muted-foreground/50 hover:text-muted-foreground">
                      <Info className="h-3 w-3" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <p className="text-sm">Projected change in portfolio emissions under this scenario, driven by carbon pricing incentives and policy requirements.</p>
                  </TooltipContent>
                </Tooltip>
              </div>
              <p className="text-xl font-bold text-success">
                {result.emissions_delta_pct.toFixed(2)}%
              </p>
            </div>
          </div>
        </TooltipProvider>
      </div>

      <div>
        <div className="flex items-center gap-1 mb-2">
          <p className="text-xs text-muted-foreground uppercase tracking-wider">
            Hotspots
          </p>
          <TooltipProvider delayDuration={200}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="text-muted-foreground/50 hover:text-muted-foreground">
                  <Info className="h-3 w-3" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="text-sm">Assets or sectors in your portfolio most vulnerable to this climate scenario.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <ul className="space-y-1.5">
          {result.hotspots.map((hotspot, index) => (
            <li
              key={index}
              className="text-sm text-muted-foreground flex items-center gap-2"
            >
              <AlertCircle className="h-3.5 w-3.5 text-warning flex-shrink-0" />
              {hotspot}
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}

export function ScenarioEngine() {
  const { data: scenarios, isLoading: scenariosLoading } = useScenarios();
  const { data: portfolio } = usePortfolio();
  const runScenario = useRunScenario();
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [result, setResult] = useState<ScenarioResponse | null>(null);

  if (scenariosLoading) {
    return <ScenarioSkeleton />;
  }

  const handleRun = async () => {
    if (!selectedScenario || !portfolio) return;

    try {
      const response = await runScenario.mutateAsync({
        portfolio_id: portfolio.id,
        scenario: selectedScenario,
      });
      setResult(response);
    } catch (error) {
      console.error("Scenario failed:", error);
    }
  };

  const scenarioNames = scenarios ? Object.keys(scenarios) : [];
  const selectedInfo = selectedScenario ? SCENARIO_DESCRIPTIONS[selectedScenario] : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      <Card className="shadow-sm hover:shadow-lg transition-all duration-300 border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-primary" />
            Scenario Engine
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Stress test your portfolio against NGFS climate scenarios to understand potential financial impacts under different transition pathways.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Select value={selectedScenario} onValueChange={setSelectedScenario}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Select a climate scenario..." />
              </SelectTrigger>
              <SelectContent>
                {scenarioNames.map((name) => (
                  <SelectItem key={name} value={name}>
                    {name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              onClick={handleRun}
              disabled={!selectedScenario || runScenario.isPending}
              className="bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-sm"
            >
              <Play className="h-4 w-4 mr-2" />
              {runScenario.isPending ? "Running..." : "Run"}
            </Button>
          </div>

          {/* Selected scenario description */}
          <AnimatePresence>
            {selectedInfo && !result && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="p-3 rounded-lg bg-secondary/50 border border-border"
              >
                <p className="text-sm text-foreground mb-2">{selectedInfo.description}</p>
                <div className="flex gap-4 text-xs text-muted-foreground">
                  <span><strong className="text-foreground">Carbon Price:</strong> {selectedInfo.carbonPrice}</span>
                  <span><strong className="text-foreground">Expected:</strong> {selectedInfo.impact}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>{result && <ResultCard result={result} />}</AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}
