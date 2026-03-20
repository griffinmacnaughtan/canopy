import { motion } from "framer-motion";
import { Target, TrendingDown, Calendar, AlertTriangle, CheckCircle2 } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Skeleton,
} from "@/components/ui";
import { useScore, useAssets } from "@/hooks";
import { cn } from "@/lib/utils";

interface Milestone {
  year: number;
  target: number;
  description: string;
  status: "achieved" | "on-track" | "at-risk" | "future";
}

export function NetZeroPathway() {
  const { data: score, isLoading: scoreLoading } = useScore();
  const { data: assets, isLoading: assetsLoading } = useAssets();

  const isLoading = scoreLoading || assetsLoading;

  if (isLoading) {
    return (
      <Card className="shadow-sm">
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!score || !assets) return null;

  // Calculate current emissions and projected pathway
  const totalEmissions = assets.reduce((sum, a) => sum + a.scope1_tco2e + a.scope2_tco2e, 0);
  const avgGreenRevenue = assets.reduce((sum, a) => sum + a.green_revenue_pct, 0) / assets.length;

  // Simulate baseline (2020) and current progress
  const baseline2020 = totalEmissions * 1.15; // Assume 15% higher in 2020
  const currentReduction = ((baseline2020 - totalEmissions) / baseline2020) * 100;

  // Project based on portfolio characteristics
  const annualReductionRate = avgGreenRevenue > 30 ? 5.5 : avgGreenRevenue > 15 ? 4.2 : 3.0;
  const isOnTrack = annualReductionRate >= 4.2; // Need ~4.2% annually for 1.5°C

  const milestones: Milestone[] = [
    {
      year: 2020,
      target: 0,
      description: "Baseline year",
      status: "achieved",
    },
    {
      year: 2025,
      target: 25,
      description: "Near-term target",
      status: currentReduction >= 20 ? "on-track" : "at-risk",
    },
    {
      year: 2030,
      target: 50,
      description: "Paris-aligned interim",
      status: "future",
    },
    {
      year: 2040,
      target: 75,
      description: "Deep decarbonization",
      status: "future",
    },
    {
      year: 2050,
      target: 100,
      description: "Net zero target",
      status: "future",
    },
  ];

  // Calculate projected 2030 reduction
  const yearsTo2030 = 2030 - 2025;
  const projected2030Reduction = currentReduction + (annualReductionRate * yearsTo2030);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.45 }}
    >
      <Card className="border border-border bg-card shadow-sm">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-primary" />
                Net Zero Pathway
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Portfolio decarbonization trajectory
              </p>
            </div>
            <div className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium",
              isOnTrack ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
            )}>
              {isOnTrack ? (
                <CheckCircle2 className="h-3.5 w-3.5" />
              ) : (
                <AlertTriangle className="h-3.5 w-3.5" />
              )}
              {isOnTrack ? "On Track for 1.5°C" : "Action Needed"}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Progress summary */}
          <div className="grid grid-cols-3 gap-4 p-4 bg-secondary/30 rounded-lg">
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">
                {currentReduction.toFixed(0)}%
              </p>
              <p className="text-xs text-muted-foreground">Reduced since 2020</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">
                {annualReductionRate.toFixed(1)}%
              </p>
              <p className="text-xs text-muted-foreground">Annual reduction rate</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">
                {projected2030Reduction.toFixed(0)}%
              </p>
              <p className="text-xs text-muted-foreground">Projected by 2030</p>
            </div>
          </div>

          {/* Visual pathway */}
          <div className="relative pt-2">
            {/* Progress line */}
            <div className="absolute top-6 left-0 right-0 h-1 bg-secondary rounded-full" />
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(currentReduction, 100) / 100 * 25}%` }}
              transition={{ delay: 0.3, duration: 0.8 }}
              className="absolute top-6 left-0 h-1 bg-primary rounded-full"
            />

            {/* Milestones */}
            <div className="relative flex justify-between">
              {milestones.map((milestone, index) => (
                <motion.div
                  key={milestone.year}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 * index }}
                  className="flex flex-col items-center"
                  style={{ width: "18%" }}
                >
                  <div className={cn(
                    "w-4 h-4 rounded-full border-2 z-10 mb-2",
                    milestone.status === "achieved" && "bg-primary border-primary",
                    milestone.status === "on-track" && "bg-success border-success",
                    milestone.status === "at-risk" && "bg-warning border-warning",
                    milestone.status === "future" && "bg-card border-border"
                  )} />
                  <p className="text-sm font-medium text-foreground">{milestone.year}</p>
                  <p className="text-xs text-muted-foreground text-center">
                    {milestone.target > 0 ? `-${milestone.target}%` : "Base"}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Action items */}
          <div className="space-y-2 pt-2">
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Recommended Actions
            </h4>
            <div className="space-y-1.5">
              {!isOnTrack && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-2 text-sm text-warning"
                >
                  <TrendingDown className="h-4 w-4 flex-shrink-0" />
                  <span>Increase annual reduction rate to 4.2% for Paris alignment</span>
                </motion.div>
              )}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="flex items-center gap-2 text-sm text-muted-foreground"
              >
                <Calendar className="h-4 w-4 flex-shrink-0 text-primary" />
                <span>Set science-based targets for high-emission holdings</span>
              </motion.div>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="flex items-center gap-2 text-sm text-muted-foreground"
              >
                <Target className="h-4 w-4 flex-shrink-0 text-primary" />
                <span>Engage top 5 emitters on transition plans</span>
              </motion.div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
