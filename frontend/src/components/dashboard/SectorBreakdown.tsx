import { motion } from "framer-motion";
import { PieChart, Info, TrendingUp, TrendingDown } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Skeleton,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui";
import { useScore, useAssets } from "@/hooks";
import { cn } from "@/lib/utils";

// Industry benchmark risk scores by sector
const SECTOR_BENCHMARKS: Record<string, number> = {
  "Utilities": 72,
  "Materials": 68,
  "Industrials": 54,
  "Real Estate": 48,
  "Information Technology": 32,
  "Energy": 85,
  "Consumer Discretionary": 42,
  "Financials": 38,
  "Healthcare": 35,
};

function getRiskColor(score: number): string {
  if (score >= 70) return "bg-destructive";
  if (score >= 50) return "bg-warning";
  return "bg-success";
}

function getRiskLabel(score: number): string {
  if (score >= 70) return "High";
  if (score >= 50) return "Medium";
  return "Low";
}

function SectorSkeleton() {
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <Skeleton className="h-5 w-40" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i}>
              <Skeleton className="h-3 w-24 mb-2" />
              <Skeleton className="h-6 w-full rounded-full" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function SectorBreakdown() {
  const { data: score, isLoading: scoreLoading } = useScore();
  const { data: assets, isLoading: assetsLoading } = useAssets();

  const isLoading = scoreLoading || assetsLoading;

  if (isLoading) {
    return <SectorSkeleton />;
  }

  if (!score || !assets) {
    return null;
  }

  // Calculate sector allocation by revenue
  const sectorRevenue = assets.reduce((acc, asset) => {
    if (!acc[asset.sector]) acc[asset.sector] = 0;
    acc[asset.sector] += asset.revenue_usd_m;
    return acc;
  }, {} as Record<string, number>);

  const totalRevenue = Object.values(sectorRevenue).reduce((a, b) => a + b, 0);

  const sectors = Object.entries(score.sector_breakdown)
    .sort(([, a], [, b]) => b - a)
    .map(([sector, riskScore]) => ({
      sector,
      riskScore,
      allocation: ((sectorRevenue[sector] || 0) / totalRevenue) * 100,
      benchmark: SECTOR_BENCHMARKS[sector] || 50,
      vsBenchmark: riskScore - (SECTOR_BENCHMARKS[sector] || 50),
    }));

  const highRiskSectors = sectors.filter((s) => s.riskScore >= 60).length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <Card className="border border-border bg-card shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <PieChart className="h-5 w-5 text-primary" />
            Sector Risk Breakdown
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Climate risk by sector with allocation weights
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Summary */}
          <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
            <div>
              <p className="text-sm text-muted-foreground">Sectors at Elevated Risk</p>
              <p className="text-2xl font-bold text-foreground">
                {highRiskSectors} <span className="text-sm font-normal text-muted-foreground">of {sectors.length}</span>
              </p>
            </div>
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="text-muted-foreground hover:text-foreground">
                    <Info className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-sm">Sectors with risk scores above 60 are considered elevated. Scores are weighted by transition and physical risk factors.</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          {/* Sector bars */}
          <div className="space-y-3">
            {sectors.map((item, index) => (
              <motion.div
                key={item.sector}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + index * 0.05 }}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{item.sector}</span>
                    <span className="text-xs text-muted-foreground">
                      ({item.allocation.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "text-xs px-1.5 py-0.5 rounded font-medium",
                        item.riskScore >= 70 && "bg-destructive/10 text-destructive",
                        item.riskScore >= 50 && item.riskScore < 70 && "bg-warning/10 text-warning",
                        item.riskScore < 50 && "bg-success/10 text-success"
                      )}
                    >
                      {getRiskLabel(item.riskScore)}
                    </span>
                    <span
                      className={cn(
                        "text-sm font-semibold tabular-nums",
                        item.riskScore >= 70
                          ? "text-destructive"
                          : item.riskScore >= 50
                            ? "text-warning"
                            : "text-success"
                      )}
                    >
                      {item.riskScore.toFixed(0)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2.5 bg-secondary rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(item.riskScore / 100) * 100}%` }}
                      transition={{ delay: 0.2 + index * 0.05, duration: 0.5 }}
                      className={cn("h-full rounded-full", getRiskColor(item.riskScore))}
                    />
                  </div>
                  {/* Benchmark comparison */}
                  <div className={cn(
                    "flex items-center gap-0.5 text-xs w-16 justify-end",
                    item.vsBenchmark > 5 && "text-destructive",
                    item.vsBenchmark < -5 && "text-success",
                    Math.abs(item.vsBenchmark) <= 5 && "text-muted-foreground"
                  )}>
                    {item.vsBenchmark > 5 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : item.vsBenchmark < -5 ? (
                      <TrendingDown className="h-3 w-3" />
                    ) : null}
                    <span>
                      {item.vsBenchmark > 0 ? "+" : ""}{item.vsBenchmark.toFixed(0)} vs avg
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center justify-center gap-4 pt-2 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded bg-success" />
              <span>Low (&lt;50)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded bg-warning" />
              <span>Medium (50-70)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded bg-destructive" />
              <span>High (&gt;70)</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
