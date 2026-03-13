import { AlertTriangle, Lightbulb, Clock, ArrowRight, Shield } from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent, Skeleton } from "@/components/ui";
import { useScore, useAssets } from "@/hooks";
import { cn } from "@/lib/utils";

interface EnhancedRisk {
  title: string;
  severity: "high" | "medium" | "low";
  timeframe: string;
  action: string;
}

interface EnhancedWin {
  title: string;
  impact: string;
  effort: "low" | "medium" | "high";
}

function RiskSkeleton() {
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function RiskNarrative() {
  const { data: score, isLoading: scoreLoading } = useScore();
  const { data: assets, isLoading: assetsLoading } = useAssets();

  const isLoading = scoreLoading || assetsLoading;

  if (isLoading) {
    return <RiskSkeleton />;
  }

  if (!score || !assets) {
    return null;
  }

  // Generate enhanced risks with more context
  const enhancedRisks: EnhancedRisk[] = score.top_risks.slice(0, 3).map((risk, index) => {
    // Add contextual information based on risk content
    let severity: "high" | "medium" | "low" = "medium";
    let timeframe = "12-24 months";
    let action = "Review and monitor";

    if (risk.toLowerCase().includes("high") || risk.toLowerCase().includes("significant") || index === 0) {
      severity = "high";
      timeframe = "0-12 months";
      action = "Immediate action required";
    } else if (risk.toLowerCase().includes("moderate") || index === 2) {
      severity = "low";
      timeframe = "24-36 months";
      action = "Include in planning cycle";
    }

    return { title: risk, severity, timeframe, action };
  });

  // Generate enhanced quick wins
  const enhancedWins: EnhancedWin[] = score.quick_wins.slice(0, 3).map((win, index) => {
    let impact = "Medium impact";
    let effort: "low" | "medium" | "high" = "medium";

    if (index === 0) {
      impact = "High impact";
      effort = "low";
    } else if (index === 2) {
      impact = "Incremental gain";
      effort = "low";
    }

    return { title: win, impact, effort };
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.35 }}
    >
      <Card className="shadow-sm hover:shadow-lg transition-all duration-300 border-border/50 bg-card/80 backdrop-blur-sm h-full">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Risk & Opportunity
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Prioritized actions for your portfolio
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Top Risks */}
          <div>
            <h4 className="text-xs font-medium text-destructive uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5" />
              Priority Risks
            </h4>
            <div className="space-y-2">
              {enhancedRisks.map((risk, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * index }}
                  className={cn(
                    "p-2.5 rounded-lg border-l-2",
                    risk.severity === "high" && "bg-destructive/5 border-l-destructive",
                    risk.severity === "medium" && "bg-warning/5 border-l-warning",
                    risk.severity === "low" && "bg-secondary border-l-muted-foreground"
                  )}
                >
                  <p className="text-sm text-foreground font-medium leading-tight">
                    {risk.title}
                  </p>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                    <span className={cn(
                      "px-1.5 py-0.5 rounded font-medium",
                      risk.severity === "high" && "bg-destructive/10 text-destructive",
                      risk.severity === "medium" && "bg-warning/10 text-warning",
                      risk.severity === "low" && "bg-secondary text-muted-foreground"
                    )}>
                      {risk.severity.charAt(0).toUpperCase() + risk.severity.slice(1)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {risk.timeframe}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Quick Wins */}
          <div>
            <h4 className="text-xs font-medium text-success uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Lightbulb className="h-3.5 w-3.5" />
              Quick Wins
            </h4>
            <div className="space-y-2">
              {enhancedWins.map((win, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + 0.1 * index }}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-success/5 border-l-2 border-l-success"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground leading-tight truncate">
                      {win.title}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {win.impact} · {win.effort} effort
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-success flex-shrink-0 ml-2" />
                </motion.div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
