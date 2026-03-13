import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Flame,
  Zap,
  Sprout,
  Info,
} from "lucide-react";
import { Card, CardContent, Skeleton, Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui";
import { useScore } from "@/hooks";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  description: string;
  tooltip: string;
  isGood?: boolean;
  accentColor: string;
  delay?: number;
}

function MetricCard({
  label,
  value,
  icon,
  description,
  tooltip,
  isGood,
  accentColor,
  delay = 0,
}: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
    >
      <Card className={cn(
        "relative overflow-hidden bg-card/80 backdrop-blur-sm shadow-sm hover:shadow-lg transition-all duration-300",
        "border-l-4 border-border/50",
        accentColor
      )}>
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {label}
                </p>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="text-muted-foreground/50 hover:text-muted-foreground transition-colors">
                      <Info className="h-3 w-3" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <p className="text-sm">{tooltip}</p>
                  </TooltipContent>
                </Tooltip>
              </div>
              <p
                className={cn(
                  "text-4xl font-bold tracking-tight",
                  isGood === undefined
                    ? "text-foreground"
                    : isGood
                      ? "text-success"
                      : "text-warning"
                )}
              >
                {value.toFixed(1)}
              </p>
              <p className="text-sm text-muted-foreground">
                {description}
              </p>
            </div>
            <div
              className={cn(
                "p-2.5 rounded-xl",
                isGood === undefined
                  ? "bg-secondary"
                  : isGood
                    ? "bg-success/10"
                    : "bg-warning/10"
              )}
            >
              {icon}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function MetricSkeleton() {
  return (
    <Card className="border-l-4 border-muted">
      <CardContent className="p-5">
        <Skeleton className="h-3 w-20 mb-3" />
        <Skeleton className="h-10 w-20 mb-2" />
        <Skeleton className="h-4 w-28" />
      </CardContent>
    </Card>
  );
}

const METRIC_TOOLTIPS = {
  overall: "Weighted composite of all climate factors. Scores above 70 indicate strong climate resilience; below 50 suggests material portfolio risk requiring attention.",
  climate: "Aggregate exposure to climate-related financial risks based on emissions intensity, sector allocation, and regulatory vulnerability. Lower scores represent reduced risk.",
  transition: "Exposure to carbon pricing, policy shifts, and technology disruption during decarbonization. Calculated from emissions intensity and sector-specific transition pathways.",
  physical: "Vulnerability to acute climate events (floods, storms) and chronic changes (sea-level rise, heat stress). Assessed by asset geography and sector sensitivity.",
  opportunity: "Revenue potential from climate solutions, clean technology, and sustainable products. Higher scores indicate greater alignment with low-carbon growth trends.",
};

export function PortfolioSignal() {
  const { data: score, isLoading, error } = useScore();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <MetricSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error || !score) {
    return (
      <Card className="p-6 text-center text-muted-foreground shadow-sm">
        Failed to load portfolio scores
      </Card>
    );
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard
          label="Overall Score"
          value={score.overall_score}
          icon={<TrendingUp className="h-5 w-5 text-primary" />}
          description="0-100 · Higher is better"
          tooltip={METRIC_TOOLTIPS.overall}
          isGood={score.overall_score >= 70}
          accentColor="border-l-primary"
          delay={0}
        />
        <MetricCard
          label="Climate Risk"
          value={score.climate_risk}
          icon={<Flame className="h-5 w-5 text-destructive" />}
          description="0-100 · Lower is better"
          tooltip={METRIC_TOOLTIPS.climate}
          isGood={score.climate_risk <= 50}
          accentColor="border-l-destructive"
          delay={0.1}
        />
        <MetricCard
          label="Transition Risk"
          value={score.transition_risk}
          icon={<Zap className="h-5 w-5 text-warning" />}
          description="0-100 · Carbon exposure"
          tooltip={METRIC_TOOLTIPS.transition}
          isGood={score.transition_risk <= 55}
          accentColor="border-l-warning"
          delay={0.2}
        />
        <MetricCard
          label="Physical Risk"
          value={score.physical_risk}
          icon={<TrendingDown className="h-5 w-5 text-info" />}
          description="0-100 · Location risk"
          tooltip={METRIC_TOOLTIPS.physical}
          isGood={score.physical_risk <= 50}
          accentColor="border-l-info"
          delay={0.3}
        />
        <MetricCard
          label="Opportunity"
          value={score.opportunity_score}
          icon={<Sprout className="h-5 w-5 text-success" />}
          description="0-100 · Green upside"
          tooltip={METRIC_TOOLTIPS.opportunity}
          isGood={score.opportunity_score >= 20}
          accentColor="border-l-success"
          delay={0.4}
        />
      </div>
    </TooltipProvider>
  );
}
