import { useState } from "react";
import { motion } from "framer-motion";
import { PieChart, Info, TrendingUp, TrendingDown, Building2, Activity } from "lucide-react";
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
  InsightPanel,
} from "@/components/ui";
import { useScore, useAssets } from "@/hooks";
import { useCopilotContext } from "@/contexts/CopilotContext";
import { cn } from "@/lib/utils";
import type { Asset } from "@/types";

// ── Constants ──────────────────────────────────────────────────────────

const SECTOR_BENCHMARKS: Record<string, number> = {
  Utilities: 72,
  Materials: 68,
  Industrials: 54,
  "Real Estate": 48,
  "Information Technology": 32,
  Energy: 85,
  "Consumer Discretionary": 42,
  Financials: 38,
  Healthcare: 35,
};

// ── Helpers ────────────────────────────────────────────────────────────

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

function formatEmissions(tco2e: number) {
  if (tco2e >= 1_000_000) return `${(tco2e / 1_000_000).toFixed(1)}M`;
  if (tco2e >= 1_000) return `${(tco2e / 1_000).toFixed(0)}K`;
  return tco2e.toFixed(0);
}

// ── Skeleton ───────────────────────────────────────────────────────────

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

// ── Sector Detail Panel Content ────────────────────────────────────────

interface SectorDetailData {
  sector: string;
  riskScore: number;
  allocation: number;
  benchmark: number;
  vsBenchmark: number;
  assets: Asset[];
}

function SectorDetailContent({ data }: { data: SectorDetailData }) {
  const totalSectorEmissions = data.assets.reduce(
    (s, a) => s + a.scope1_tco2e + a.scope2_tco2e,
    0,
  );
  const totalSectorRevenue = data.assets.reduce((s, a) => s + a.revenue_usd_m, 0);
  const avgGreenRev =
    totalSectorRevenue > 0
      ? (data.assets.reduce(
          (s, a) => s + (a.green_revenue_pct * a.revenue_usd_m) / 100,
          0,
        ) /
          totalSectorRevenue) *
        100
      : 0;

  const sorted = [...data.assets].sort(
    (a, b) =>
      (b.scope1_tco2e + b.scope2_tco2e) / b.revenue_usd_m -
      (a.scope1_tco2e + a.scope2_tco2e) / a.revenue_usd_m,
  );

  return (
    <div className="space-y-6">
      {/* Risk score bar */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-muted-foreground">Risk Score</span>
          <span
            className={cn(
              "text-lg font-bold",
              data.riskScore >= 70
                ? "text-red-500"
                : data.riskScore >= 50
                  ? "text-amber-500"
                  : "text-emerald-600",
            )}
          >
            {data.riskScore.toFixed(0)}/100
          </span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full", getRiskColor(data.riskScore))}
            style={{ width: `${data.riskScore}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-xs text-muted-foreground">
          <span>Benchmark: {data.benchmark}</span>
          <span
            className={cn(
              data.vsBenchmark > 5 && "text-red-500",
              data.vsBenchmark < -5 && "text-emerald-600",
            )}
          >
            {data.vsBenchmark > 0 ? "+" : ""}
            {data.vsBenchmark.toFixed(0)} vs avg
          </span>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Allocation</p>
          <p className="text-lg font-bold text-foreground">{data.allocation.toFixed(0)}%</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Holdings</p>
          <p className="text-lg font-bold text-foreground">{data.assets.length}</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Emissions</p>
          <p className="text-lg font-bold text-foreground">{formatEmissions(totalSectorEmissions)}</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-xs text-muted-foreground">Green Rev</p>
          <p className="text-lg font-bold text-foreground">{avgGreenRev.toFixed(0)}%</p>
        </div>
      </div>

      {/* Holdings in this sector */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">Holdings</h3>
        <div className="space-y-2">
          {sorted.map((asset) => {
            const emissions = asset.scope1_tco2e + asset.scope2_tco2e;
            const intensity = emissions / asset.revenue_usd_m;
            return (
              <div
                key={asset.id}
                className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{asset.name}</p>
                  <p className="text-xs text-muted-foreground">{asset.region}</p>
                </div>
                <div className="text-right shrink-0 ml-3">
                  <p className="text-sm font-medium text-foreground flex items-center gap-1">
                    <Activity className="h-3 w-3 text-muted-foreground" />
                    {intensity.toFixed(0)} tCO2e/$M
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {asset.green_revenue_pct}% green
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────

export function SectorBreakdown() {
  const { data: score, isLoading: scoreLoading } = useScore();
  const { data: assets, isLoading: assetsLoading } = useAssets();
  const { askCopilot } = useCopilotContext();
  const [selectedSector, setSelectedSector] = useState<SectorDetailData | null>(null);

  const isLoading = scoreLoading || assetsLoading;

  if (isLoading) return <SectorSkeleton />;
  if (!score || !assets) return null;

  // Calculate sector allocation by revenue
  const sectorRevenue = assets.reduce(
    (acc, asset) => {
      if (!acc[asset.sector]) acc[asset.sector] = 0;
      acc[asset.sector] += asset.revenue_usd_m;
      return acc;
    },
    {} as Record<string, number>,
  );

  const totalRevenue = Object.values(sectorRevenue).reduce((a, b) => a + b, 0);

  const sectors = Object.entries(score.sector_breakdown)
    .sort(([, a], [, b]) => b - a)
    .map(([sector, riskScore]) => ({
      sector,
      riskScore,
      allocation: ((sectorRevenue[sector] || 0) / totalRevenue) * 100,
      benchmark: SECTOR_BENCHMARKS[sector] || 50,
      vsBenchmark: riskScore - (SECTOR_BENCHMARKS[sector] || 50),
      assets: assets.filter((a) => a.sector === sector),
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
                {highRiskSectors}{" "}
                <span className="text-sm font-normal text-muted-foreground">of {sectors.length}</span>
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
                  <p className="text-sm">
                    Sectors with risk scores above 60 are considered elevated. Click a sector to see holdings and details.
                  </p>
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
                className="cursor-pointer rounded-lg p-2 -mx-2 hover:bg-emerald-50/40 transition-colors"
                onClick={() => setSelectedSector(item)}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{item.sector}</span>
                    <span className="text-xs text-muted-foreground">({item.allocation.toFixed(0)}%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "text-xs px-1.5 py-0.5 rounded font-medium",
                        item.riskScore >= 70 && "bg-destructive/10 text-destructive",
                        item.riskScore >= 50 && item.riskScore < 70 && "bg-warning/10 text-warning",
                        item.riskScore < 50 && "bg-success/10 text-success",
                      )}
                    >
                      {getRiskLabel(item.riskScore)}
                    </span>
                    <span
                      className={cn(
                        "text-sm font-semibold tabular-nums",
                        item.riskScore >= 70 ? "text-destructive" : item.riskScore >= 50 ? "text-warning" : "text-success",
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
                  <div
                    className={cn(
                      "flex items-center gap-0.5 text-xs w-16 justify-end",
                      item.vsBenchmark > 5 && "text-destructive",
                      item.vsBenchmark < -5 && "text-success",
                      Math.abs(item.vsBenchmark) <= 5 && "text-muted-foreground",
                    )}
                  >
                    {item.vsBenchmark > 5 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : item.vsBenchmark < -5 ? (
                      <TrendingDown className="h-3 w-3" />
                    ) : null}
                    <span>
                      {item.vsBenchmark > 0 ? "+" : ""}
                      {item.vsBenchmark.toFixed(0)} vs avg
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

      {/* Sector Detail Panel */}
      <InsightPanel
        isOpen={!!selectedSector}
        onClose={() => setSelectedSector(null)}
        title={selectedSector?.sector || ""}
        subtitle={`${selectedSector?.assets.length || 0} holdings \u00B7 ${selectedSector?.allocation.toFixed(0) || 0}% allocation`}
        icon={<Building2 className="h-5 w-5" />}
        onAskCopilot={
          selectedSector
            ? () => {
                askCopilot(
                  `Analyze the ${selectedSector.sector} sector in my portfolio. It has a risk score of ${selectedSector.riskScore.toFixed(0)}/100 (benchmark: ${selectedSector.benchmark}) with ${selectedSector.assets.length} holdings. What are the key drivers of risk in this sector and what actions would you recommend?`,
                );
                setSelectedSector(null);
              }
            : undefined
        }
      >
        {selectedSector && <SectorDetailContent data={selectedSector} />}
      </InsightPanel>
    </motion.div>
  );
}
