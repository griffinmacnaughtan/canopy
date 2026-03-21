import { motion } from "framer-motion";
import {
  TrendingUp,
  Flame,
  Zap,
  Globe,
  Leaf,
  Info,
  Activity,
} from "lucide-react";
import {
  Card,
  CardContent,
  Skeleton,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui";
import { useScore, useAssets } from "@/hooks";
import { cn } from "@/lib/utils";

interface MetricTileProps {
  label: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  tooltip: string;
  color?: "emerald" | "red" | "amber" | "blue" | "default";
  delay?: number;
}

function MetricTile({
  label,
  value,
  subtitle,
  icon,
  tooltip,
  color = "default",
  delay = 0,
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
      <Card className="border border-border bg-card shadow-sm hover:shadow-md transition-shadow duration-200">
        <CardContent className="p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-1.5">
              <span
                className={cn(
                  "inline-flex items-center justify-center w-7 h-7 rounded-lg",
                  iconBgMap[color]
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
                <button className="text-gray-300 hover:text-gray-400 transition-colors">
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

const TOOLTIPS = {
  overall:
    "Weighted composite of all climate factors. Above 70 = strong resilience; below 50 = material risk.",
  climate:
    "Aggregate climate-related financial risk based on emissions, sector allocation, and regulatory exposure.",
  transition:
    "Exposure to carbon pricing, policy shifts, and technology disruption during decarbonization.",
  intensity:
    "Portfolio carbon intensity measured as tonnes of CO2e per million dollars of revenue.",
  greenRevenue:
    "Revenue-weighted percentage of portfolio income from climate-aligned products and services.",
  emissions:
    "Total portfolio greenhouse gas emissions across Scope 1 (direct) and Scope 2 (electricity).",
};

export function PortfolioOverview() {
  const { data: score, isLoading: scoreLoading, error: scoreError } = useScore();
  const { data: assets, isLoading: assetsLoading } = useAssets();

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

  // Computed metrics from asset data
  const totalEmissions =
    assets?.reduce((sum, a) => sum + a.scope1_tco2e + a.scope2_tco2e, 0) || 0;
  const totalRevenue =
    assets?.reduce((sum, a) => sum + a.revenue_usd_m, 0) || 0;
  const emissionsIntensity =
    totalRevenue > 0 ? totalEmissions / totalRevenue : 0;
  const weightedGreenRevenue =
    assets?.reduce(
      (sum, a) => sum + (a.green_revenue_pct * a.revenue_usd_m) / 100,
      0
    ) || 0;
  const avgGreenPct =
    totalRevenue > 0 ? (weightedGreenRevenue / totalRevenue) * 100 : 0;

  const formatEmissions = (tco2e: number) => {
    if (tco2e >= 1_000_000) return `${(tco2e / 1_000_000).toFixed(1)}M`;
    if (tco2e >= 1_000) return `${(tco2e / 1_000).toFixed(0)}K`;
    return tco2e.toFixed(0);
  };

  const scoreColor = (val: number, inverse = false) => {
    if (inverse) return val <= 50 ? "emerald" as const : val <= 70 ? "amber" as const : "red" as const;
    return val >= 70 ? "emerald" as const : val >= 50 ? "amber" as const : "red" as const;
  };

  const ratingLabel = (val: number, inverse = false) => {
    if (inverse) return val <= 30 ? "Low" : val <= 60 ? "Moderate" : "High";
    return val >= 70 ? "Strong" : val >= 50 ? "Moderate" : "Weak";
  };

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
        />
        <MetricTile
          label="Climate Risk"
          value={`${score.climate_risk.toFixed(0)}/100`}
          subtitle={`${ratingLabel(score.climate_risk, true)} risk exposure`}
          icon={<Flame className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.climate}
          color={scoreColor(score.climate_risk, true)}
          delay={0.05}
        />
        <MetricTile
          label="Transition"
          value={`${score.transition_risk.toFixed(0)}/100`}
          subtitle={`${ratingLabel(score.transition_risk, true)} carbon exposure`}
          icon={<Zap className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.transition}
          color={scoreColor(score.transition_risk, true)}
          delay={0.1}
        />
        <MetricTile
          label="Intensity"
          value={emissionsIntensity.toFixed(0)}
          subtitle="tCO2e / $M revenue"
          icon={<Activity className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.intensity}
          color={emissionsIntensity < 200 ? "emerald" : emissionsIntensity < 500 ? "amber" : "red"}
          delay={0.15}
        />
        <MetricTile
          label="Green Rev"
          value={`${avgGreenPct.toFixed(0)}%`}
          subtitle="Climate-aligned income"
          icon={<Leaf className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.greenRevenue}
          color={avgGreenPct >= 20 ? "emerald" : avgGreenPct >= 10 ? "amber" : "default"}
          delay={0.2}
        />
        <MetricTile
          label="Emissions"
          value={formatEmissions(totalEmissions)}
          subtitle="tCO2e Scope 1 & 2"
          icon={<Globe className="h-3.5 w-3.5" />}
          tooltip={TOOLTIPS.emissions}
          color="default"
          delay={0.25}
        />
      </div>
    </TooltipProvider>
  );
}
