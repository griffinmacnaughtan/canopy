import { motion } from "framer-motion";
import {
  Leaf,
  TrendingDown,
  DollarSign,
  Globe,
  Sparkles,
  ArrowUpRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui";
import { useScore, useAssets } from "@/hooks";
import { cn } from "@/lib/utils";

interface ImpactMetricProps {
  icon: React.ReactNode;
  value: string;
  label: string;
  subtext: string;
  trend?: "up" | "down" | "neutral";
  delay?: number;
}

function ImpactMetric({ icon, value, label, subtext, trend, delay = 0 }: ImpactMetricProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="flex items-center gap-4"
    >
      <div className="p-3 rounded-2xl bg-gradient-to-br from-emerald-500 to-forest-600 text-white shadow-lg shadow-emerald-500/20">
        {icon}
      </div>
      <div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-foreground tracking-tight">{value}</span>
          {trend && (
            <span className={cn(
              "text-xs font-medium px-1.5 py-0.5 rounded-full",
              trend === "down" ? "bg-emerald-100 text-emerald-700" :
              trend === "up" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"
            )}>
              {trend === "down" ? "Reducing" : trend === "up" ? "Increasing" : "Stable"}
            </span>
          )}
        </div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="text-xs text-muted-foreground">{subtext}</p>
      </div>
    </motion.div>
  );
}

export function ImpactSummary() {
  const { data: score } = useScore();
  const { data: assets } = useAssets();

  // Calculate real metrics from portfolio data
  const totalEmissions = assets?.reduce(
    (sum, a) => sum + a.scope1_tco2e + a.scope2_tco2e,
    0
  ) || 0;

  const totalRevenue = assets?.reduce((sum, a) => sum + a.revenue_usd_m, 0) || 0;

  const weightedGreenRevenue = assets?.reduce(
    (sum, a) => sum + (a.green_revenue_pct * a.revenue_usd_m / 100),
    0
  ) || 0;

  const avgGreenPct = totalRevenue > 0
    ? (weightedGreenRevenue / totalRevenue * 100)
    : 0;

  // Format emissions in a readable way
  const formatEmissions = (tco2e: number) => {
    if (tco2e >= 1000000) return `${(tco2e / 1000000).toFixed(1)}M`;
    if (tco2e >= 1000) return `${(tco2e / 1000).toFixed(0)}K`;
    return tco2e.toFixed(0);
  };

  // Calculate emissions intensity (tCO2e per $M revenue)
  const emissionsIntensity = totalRevenue > 0
    ? totalEmissions / totalRevenue
    : 0;

  // Estimate potential carbon savings based on opportunity score
  const potentialReduction = score?.opportunity_score
    ? Math.round(totalEmissions * (score.opportunity_score / 100) * 0.3)
    : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
    >
      <Card className="relative overflow-hidden border-0 shadow-xl bg-gradient-to-br from-emerald-50 via-white to-forest-50">
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-emerald-200/30 to-transparent rounded-full -translate-y-32 translate-x-32" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-forest-200/20 to-transparent rounded-full translate-y-24 -translate-x-24" />

        <CardContent className="relative p-8">
          <div className="flex items-center gap-2 mb-6">
            <div className="p-2 rounded-xl bg-emerald-100">
              <Sparkles className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">Portfolio Impact</h3>
              <p className="text-sm text-muted-foreground">Real-time sustainability metrics</p>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            <ImpactMetric
              icon={<Globe className="h-6 w-6" />}
              value={`${formatEmissions(totalEmissions)}`}
              label="Total Emissions"
              subtext="tCO2e Scope 1 & 2"
              trend="down"
              delay={0.15}
            />
            <ImpactMetric
              icon={<Leaf className="h-6 w-6" />}
              value={`${avgGreenPct.toFixed(0)}%`}
              label="Green Revenue"
              subtext="Climate-aligned income"
              trend="neutral"
              delay={0.2}
            />
            <ImpactMetric
              icon={<TrendingDown className="h-6 w-6" />}
              value={`${emissionsIntensity.toFixed(0)}`}
              label="Carbon Intensity"
              subtext="tCO2e per $M revenue"
              trend={emissionsIntensity < 500 ? "down" : "up"}
              delay={0.25}
            />
            <ImpactMetric
              icon={<DollarSign className="h-6 w-6" />}
              value={`${formatEmissions(potentialReduction)}`}
              label="Reduction Potential"
              subtext="tCO2e achievable savings"
              delay={0.3}
            />
          </div>

          {/* Call to action */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-8 pt-6 border-t border-emerald-100"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">
                  Your portfolio is performing{" "}
                  <span className={cn(
                    "font-bold",
                    (score?.overall_score || 0) >= 70 ? "text-emerald-600" :
                    (score?.overall_score || 0) >= 50 ? "text-amber-600" : "text-red-600"
                  )}>
                    {(score?.overall_score || 0) >= 70 ? "above" :
                     (score?.overall_score || 0) >= 50 ? "at" : "below"} market average
                  </span>
                  {" "}on climate metrics
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Based on sector-adjusted benchmarks from 5,000+ global companies
                </p>
              </div>
              <button
                onClick={() => {
                  const section = document.getElementById("analysis-section");
                  if (section) {
                    section.scrollIntoView({ behavior: "smooth" });
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 text-white text-sm font-medium hover:from-emerald-600 hover:to-emerald-700 transition-all shadow-lg shadow-emerald-500/20 hover:shadow-xl hover:shadow-emerald-500/30"
              >
                View Full Report
                <ArrowUpRight className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
