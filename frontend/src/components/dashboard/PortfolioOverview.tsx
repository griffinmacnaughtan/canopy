import { useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Flame,
  Zap,
  Globe,
  Leaf,
  Info,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import {
  Card,
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

// ── Types ──────────────────────────────────────────────────────────────

interface MetricTileProps {
  label: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  tooltip: string;
  color?: "emerald" | "red" | "amber" | "blue" | "default";
  delay?: number;
  onClick?: () => void;
}

interface MetricDetail {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  explanation: string;
  copilotQuestion: string;
  contributors: {
    name: string;
    value: string;
    isPositive: boolean;
  }[];
  breakdown?: { label: string; value: string; pct: number; color: string }[];
}

// ── MetricTile ─────────────────────────────────────────────────────────

function MetricTile({
  label,
  value,
  subtitle,
  icon,
  tooltip,
  color = "default",
  delay = 0,
  onClick,
}: MetricTileProps) {
  const colorMap = {
    emerald: "text-emerald-600",
    red: "text-red-500",
    amber: "text-amber-500",
    blue: "text-blue-500",
    default: "text-foreground",
  };

  const iconBgMap = {
    emerald: "bg-emerald-50 text-emerald-600",
    red: "bg-red-50 text-red-500",
    amber: "bg-amber-50 text-amber-500",
    blue: "bg-blue-50 text-blue-500",
    default: "bg-gray-50 text-gray-500",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
    >
      <Card
        className={cn(
          "border border-border bg-card shadow-sm hover:shadow-md transition-all duration-200",
          onClick && "cursor-pointer hover:border-emerald-300 active:scale-[0.98]",
        )}
        onClick={onClick}
      >
        <CardContent className="p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-1.5">
              <span
                className={cn(
                  "inline-flex items-center justify-center w-7 h-7 rounded-lg",
                  iconBgMap[color],
                )}
              >
                {icon}
              </span>
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                {label}
              </span>
            </div>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  className="text-gray-300 hover:text-gray-400 transition-colors"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Info className="h-3.5 w-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="text-sm">{tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </div>
          <p className={cn("text-2xl font-bold tracking-tight", colorMap[color])}>
            {value}
          </p>
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function MetricSkeleton() {
  return (
    <Card className="border border-border">
      <CardContent className="p-5">
        <Skeleton className="h-4 w-16 mb-3" />
        <Skeleton className="h-8 w-20 mb-1" />
        <Skeleton className="h-3 w-24" />
      </CardContent>
    </Card>
  );
}

// ── Detail panel sub-components ────────────────────────────────────────

function ContributorRow({
  name,
  value,
  isPositive,
}: {
  name: string;
  value: string;
  isPositive: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
      <span className="text-sm text-foreground">{name}</span>
      <div className="flex items-center gap-1.5">
        {isPositive ? (
          <ArrowDownRight className="h-3 w-3 text-emerald-500" />
        ) : (
          <ArrowUpRight className="h-3 w-3 text-red-500" />
        )}
        <span
          className={cn(
            "text-sm font-medium tabular-nums",
            isPositive ? "text-emerald-600" : "text-red-500",
          )}
        >
          {value}
        </span>
      </div>
    </div>
  );
}

function BreakdownBar({
  label,
  value,
  pct,
  color,
}: {
  label: string;
  value: string;
  pct: number;
  color: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium text-foreground">{value}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}

// ── Helpers ─────────────────────────────────────────────────────────────

function formatEmissions(tco2e: number) {
  if (tco2e >= 1_000_000) return `${(tco2e / 1_000_000).toFixed(1)}M`;
  if (tco2e >= 1_000) return `${(tco2e / 1_000).toFixed(0)}K`;
  return tco2e.toFixed(0);
}

function buildMetricDetails(
  score: {
    overall_score: number;
    climate_risk: number;
    transition_risk: number;
    physical_risk: number;
    opportunity_score: number;
    sector_breakdown: Record<string, number>;
  },
  assets: Asset[],
): Record<string, MetricDetail> {
  const totalEmissions = assets.reduce(
    (sum, a) => sum + a.scope1_tco2e + a.scope2_tco2e,
    0,
  );
  const totalRevenue = assets.reduce((sum, a) => sum + a.revenue_usd_m, 0);

  const byIntensity = [...assets]
    .map((a) => ({
      ...a,
      intensity: (a.scope1_tco2e + a.scope2_tco2e) / a.revenue_usd_m,
    }))
    .sort((a, b) => b.intensity - a.intensity);

  const byGreen = [...assets].sort(
    (a, b) => b.green_revenue_pct - a.green_revenue_pct,
  );

  const byEmissions = [...assets].sort(
    (a, b) =>
      b.scope1_tco2e + b.scope2_tco2e - (a.scope1_tco2e + a.scope2_tco2e),
  );

  return {
    overall: {
      title: "Overall Score",
      subtitle: `${score.overall_score.toFixed(0)}/100`,
      icon: <TrendingUp className="h-5 w-5" />,
      explanation:
        "Composite score: 100 \u2212 climate_risk + (opportunity \u00D7 0.35). Scores above 70 indicate strong climate resilience; below 50 signals material risk requiring action.",
      copilotQuestion:
        "Break down my portfolio's overall climate resilience score. What factors are helping and hurting it most?",
      contributors: byIntensity.slice(0, 5).map((a) => ({
        name: a.name,
        value: `${a.intensity.toFixed(0)} tCO2e/$M`,
        isPositive: a.intensity < 100,
      })),
      breakdown: [
        {
          label: "Climate Risk (penalty)",
          value: `${score.climate_risk.toFixed(0)}/100`,
          pct: score.climate_risk,
          color: score.climate_risk > 60 ? "bg-red-400" : "bg-amber-400",
        },
        {
          label: "Opportunity (+35% uplift)",
          value: `${score.opportunity_score.toFixed(0)}/100`,
          pct: score.opportunity_score,
          color: "bg-emerald-400",
        },
      ],
    },
    climate: {
      title: "Climate Risk",
      subtitle: `${score.climate_risk.toFixed(0)}/100`,
      icon: <Flame className="h-5 w-5" />,
      explanation:
        "Blended risk: 60% transition + 40% physical. Follows NGFS consensus weighting for 2030-horizon stress tests. Lower is better.",
      copilotQuestion:
        "Analyze my portfolio's climate risk score. Which holdings have the highest transition and physical risk exposure?",
      contributors: Object.entries(score.sector_breakdown)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([sector, risk]) => ({
          name: sector,
          value: `${risk.toFixed(0)}/100`,
          isPositive: risk < 50,
        })),
      breakdown: [
        {
          label: "Transition Risk (60% weight)",
          value: `${score.transition_risk.toFixed(0)}/100`,
          pct: score.transition_risk,
          color: score.transition_risk > 60 ? "bg-red-400" : score.transition_risk > 40 ? "bg-amber-400" : "bg-emerald-400",
        },
        {
          label: "Physical Risk (40% weight)",
          value: `${score.physical_risk.toFixed(0)}/100`,
          pct: score.physical_risk,
          color: score.physical_risk > 60 ? "bg-red-400" : score.physical_risk > 40 ? "bg-amber-400" : "bg-emerald-400",
        },
      ],
    },
    transition: {
      title: "Transition Risk",
      subtitle: `${score.transition_risk.toFixed(0)}/100`,
      icon: <Zap className="h-5 w-5" />,
      explanation:
        "Exposure to carbon pricing, policy shifts, and technology disruption. Based on emissions intensity \u00D7 sector weight (Energy: 0.9, Materials: 0.75, Utilities: 0.7).",
      copilotQuestion:
        "Which holdings in my portfolio have the highest transition risk and why? What actions could reduce this exposure?",
      contributors: byIntensity.slice(0, 5).map((a) => ({
        name: a.name,
        value: `${a.intensity.toFixed(0)} tCO2e/$M`,
        isPositive: a.intensity < 100,
      })),
    },
    intensity: {
      title: "Carbon Intensity",
      subtitle: `${totalRevenue > 0 ? (totalEmissions / totalRevenue).toFixed(0) : 0} tCO2e/$M`,
      icon: <Activity className="h-5 w-5" />,
      explanation:
        "Total emissions \u00F7 total revenue. Industry benchmark is ~145 tCO2e/$M. Lower means more revenue per unit of carbon emitted.",
      copilotQuestion:
        "How does my portfolio's carbon intensity compare to industry benchmarks? Which companies are the most and least carbon-efficient?",
      contributors: byIntensity.slice(0, 5).map((a) => ({
        name: a.name,
        value: `${a.intensity.toFixed(0)} tCO2e/$M`,
        isPositive: a.intensity < 145,
      })),
      breakdown: [
        {
          label: "Scope 1 (Direct)",
          value: formatEmissions(assets.reduce((s, a) => s + a.scope1_tco2e, 0)),
          pct: (assets.reduce((s, a) => s + a.scope1_tco2e, 0) / totalEmissions) * 100,
          color: "bg-red-400",
        },
        {
          label: "Scope 2 (Electricity)",
          value: formatEmissions(assets.reduce((s, a) => s + a.scope2_tco2e, 0)),
          pct: (assets.reduce((s, a) => s + a.scope2_tco2e, 0) / totalEmissions) * 100,
          color: "bg-amber-400",
        },
      ],
    },
    greenRevenue: {
      title: "Green Revenue",
      subtitle: `${totalRevenue > 0 ? ((assets.reduce((s, a) => s + (a.green_revenue_pct * a.revenue_usd_m) / 100, 0) / totalRevenue) * 100).toFixed(0) : 0}%`,
      icon: <Leaf className="h-5 w-5" />,
      explanation:
        "Revenue-weighted share of income from climate-aligned products/services. Industry benchmark: ~18%. Higher signals better positioning for the energy transition.",
      copilotQuestion:
        "Analyze the green revenue composition of my portfolio. Which holdings are leaders in climate-aligned revenue and which are lagging?",
      contributors: byGreen.slice(0, 5).map((a) => ({
        name: a.name,
        value: `${a.green_revenue_pct}%`,
        isPositive: a.green_revenue_pct >= 20,
      })),
    },
    emissions: {
      title: "Total Emissions",
      subtitle: `${formatEmissions(totalEmissions)} tCO2e`,
      icon: <Globe className="h-5 w-5" />,
      explanation:
        "Sum of Scope 1 (direct) and Scope 2 (electricity) emissions. Does not include Scope 3 (supply chain), which would significantly increase totals for tech and financial companies.",
      copilotQuestion:
        "Which companies contribute the most to my portfolio's total emissions? What would be the impact of divesting the top 3 emitters?",
      contributors: byEmissions.slice(0, 5).map((a) => ({
        name: a.name,
        value: `${formatEmissions(a.scope1_tco2e + a.scope2_tco2e)} tCO2e`,
        isPositive: a.scope1_tco2e + a.scope2_tco2e < totalEmissions * 0.1,
      })),
      breakdown: [
        {
          label: "Scope 1 (Direct)",
          value: formatEmissions(assets.reduce((s, a) => s + a.scope1_tco2e, 0)),
          pct: (assets.reduce((s, a) => s + a.scope1_tco2e, 0) / totalEmissions) * 100,
          color: "bg-red-400",
        },
        {
          label: "Scope 2 (Electricity)",
          value: formatEmissions(assets.reduce((s, a) => s + a.scope2_tco2e, 0)),
          pct: (assets.reduce((s, a) => s + a.scope2_tco2e, 0) / totalEmissions) * 100,
          color: "bg-amber-400",
        },
      ],
    },
  };
}

// ── Tooltips ───────────────────────────────────────────────────────────

const TOOLTIPS = {
  overall: "Weighted composite of all climate factors. Above 70 = strong resilience; below 50 = material risk.",
  climate: "Aggregate climate-related financial risk based on emissions, sector allocation, and regulatory exposure.",
  transition: "Exposure to carbon pricing, policy shifts, and technology disruption during decarbonization.",
  intensity: "Portfolio carbon intensity measured as tonnes of CO2e per million dollars of revenue.",
  greenRevenue: "Revenue-weighted percentage of portfolio income from climate-aligned products and services.",
  emissions: "Total portfolio greenhouse gas emissions across Scope 1 (direct) and Scope 2 (electricity).",
};

// ── Main Component ─────────────────────────────────────────────────────

export function PortfolioOverview() {
  const { data: score, isLoading: scoreLoading, error: scoreError } = useScore();
  const { data: assets, isLoading: assetsLoading } = useAssets();
  const { askCopilot } = useCopilotContext();
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  const isLoading = scoreLoading || assetsLoading;

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <MetricSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (scoreError || !score) {
    return (
      <Card className="p-6 text-center text-muted-foreground border border-border">
        Failed to load portfolio scores
      </Card>
    );
  }

  const totalEmissions =
    assets?.reduce((sum, a) => sum + a.scope1_tco2e + a.scope2_tco2e, 0) || 0;
  const totalRevenue =
    assets?.reduce((sum, a) => sum + a.revenue_usd_m, 0) || 0;
  const emissionsIntensity =
    totalRevenue > 0 ? totalEmissions / totalRevenue : 0;
  const weightedGreenRevenue =
    assets?.reduce(
      (sum, a) => sum + (a.green_revenue_pct * a.revenue_usd_m) / 100,
      0,
    ) || 0;
  const avgGreenPct =
    totalRevenue > 0 ? (weightedGreenRevenue / totalRevenue) * 100 : 0;

  const scoreColor = (val: number, inverse = false) => {
    if (inverse)
      return val <= 50 ? ("emerald" as const) : val <= 70 ? ("amber" as const) : ("red" as const);
    return val >= 70 ? ("emerald" as const) : val >= 50 ? ("amber" as const) : ("red" as const);
  };

  const ratingLabel = (val: number, inverse = false) => {
    if (inverse) return val <= 30 ? "Low" : val <= 60 ? "Moderate" : "High";
    return val >= 70 ? "Strong" : val >= 50 ? "Moderate" : "Weak";
  };

  const metricDetails = assets ? buildMetricDetails(score, assets) : null;
  const detail = selectedMetric && metricDetails ? metricDetails[selectedMetric] : null;

  return (
    <TooltipProvider delayDuration={200}>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricTile
          label="Overall"
          value={`${score.overall_score.toFixed(0)}/100`}
          subtitle={`${ratingLabel(score.overall_score)} climate resilience`}
          icon={<TrendingUp className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.overall}
          color={scoreColor(score.overall_score)}
          delay={0}
          onClick={() => setSelectedMetric("overall")}
        />
        <MetricTile
          label="Climate Risk"
          value={`${score.climate_risk.toFixed(0)}/100`}
          subtitle={`${ratingLabel(score.climate_risk, true)} risk exposure`}
          icon={<Flame className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.climate}
          color={scoreColor(score.climate_risk, true)}
          delay={0.05}
          onClick={() => setSelectedMetric("climate")}
        />
        <MetricTile
          label="Transition"
          value={`${score.transition_risk.toFixed(0)}/100`}
          subtitle={`${ratingLabel(score.transition_risk, true)} carbon exposure`}
          icon={<Zap className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.transition}
          color={scoreColor(score.transition_risk, true)}
          delay={0.1}
          onClick={() => setSelectedMetric("transition")}
        />
        <MetricTile
          label="Intensity"
          value={emissionsIntensity.toFixed(0)}
          subtitle="tCO2e / $M revenue"
          icon={<Activity className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.intensity}
          color={emissionsIntensity < 200 ? "emerald" : emissionsIntensity < 500 ? "amber" : "red"}
          delay={0.15}
          onClick={() => setSelectedMetric("intensity")}
        />
        <MetricTile
          label="Green Rev"
          value={`${avgGreenPct.toFixed(0)}%`}
          subtitle="Climate-aligned income"
          icon={<Leaf className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.greenRevenue}
          color={avgGreenPct >= 20 ? "emerald" : avgGreenPct >= 10 ? "amber" : "default"}
          delay={0.2}
          onClick={() => setSelectedMetric("greenRevenue")}
        />
        <MetricTile
          label="Emissions"
          value={formatEmissions(totalEmissions)}
          subtitle="tCO2e Scope 1 & 2"
          icon={<Globe className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.emissions}
          color="default"
          delay={0.25}
          onClick={() => setSelectedMetric("emissions")}
        />
      </div>

      {/* Metric Insight Panel */}
      <InsightPanel
        isOpen={!!detail}
        onClose={() => setSelectedMetric(null)}
        title={detail?.title || ""}
        subtitle={detail?.subtitle}
        icon={detail?.icon}
        onAskCopilot={
          detail
            ? () => {
                askCopilot(detail.copilotQuestion);
                setSelectedMetric(null);
              }
            : undefined
        }
      >
        {detail && (
          <div className="space-y-6">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-muted-foreground leading-relaxed">
                {detail.explanation}
              </p>
            </div>

            {detail.breakdown && (
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3">Score Breakdown</h3>
                <div className="space-y-3">
                  {detail.breakdown.map((b) => (
                    <BreakdownBar key={b.label} {...b} />
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="text-sm font-semibold text-foreground mb-2">Top Contributors</h3>
              <div>
                {detail.contributors.map((c) => (
                  <ContributorRow key={c.name} {...c} />
                ))}
              </div>
            </div>
          </div>
        )}
      </InsightPanel>
    </TooltipProvider>
  );
}
