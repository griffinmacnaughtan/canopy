import { motion } from "framer-motion";
import { Lightbulb, TrendingUp, TrendingDown, Minus, BarChart3, Database, Target } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Skeleton,
} from "@/components/ui";
import { useScore, useAssets } from "@/hooks";
import { cn } from "@/lib/utils";

interface Insight {
  type: "positive" | "negative" | "neutral";
  title: string;
  description: string;
  metric?: string;
}

interface Benchmark {
  name: string;
  portfolioValue: number;
  benchmarkValue: number;
  unit: string;
  betterWhenLower?: boolean;
}

// Simulated benchmark data (in production, this would come from an API)
const INDUSTRY_BENCHMARKS = {
  carbonIntensity: 145, // tCO2e per $M revenue
  greenRevenue: 18, // percentage
  controversyScore: 1.8, // average
  transitionRisk: 52, // score
};

function InsightCard({ insight, delay }: { insight: Insight; delay: number }) {
  const Icon = insight.type === "positive" ? TrendingUp : insight.type === "negative" ? TrendingDown : Minus;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className={cn(
        "p-3 rounded-lg border-l-4",
        insight.type === "positive" && "bg-success/5 border-l-success",
        insight.type === "negative" && "bg-warning/5 border-l-warning",
        insight.type === "neutral" && "bg-secondary border-l-muted-foreground"
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          "p-1.5 rounded-lg mt-0.5",
          insight.type === "positive" && "bg-success/10",
          insight.type === "negative" && "bg-warning/10",
          insight.type === "neutral" && "bg-secondary"
        )}>
          <Icon className={cn(
            "h-4 w-4",
            insight.type === "positive" && "text-success",
            insight.type === "negative" && "text-warning",
            insight.type === "neutral" && "text-muted-foreground"
          )} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-foreground">{insight.title}</p>
          <p className="text-xs text-muted-foreground mt-0.5">{insight.description}</p>
          {insight.metric && (
            <p className="text-xs font-medium text-primary mt-1">{insight.metric}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function BenchmarkRow({ benchmark, delay }: { benchmark: Benchmark; delay: number }) {
  const diff = benchmark.portfolioValue - benchmark.benchmarkValue;
  const percentDiff = ((diff / benchmark.benchmarkValue) * 100).toFixed(0);
  const isBetter = benchmark.betterWhenLower ? diff < 0 : diff > 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay }}
      className="flex items-center justify-between py-2 border-b border-border last:border-0"
    >
      <span className="text-sm text-muted-foreground">{benchmark.name}</span>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <span className="text-sm font-medium text-foreground">
            {benchmark.portfolioValue.toFixed(1)}{benchmark.unit}
          </span>
          <span className="text-xs text-muted-foreground ml-1">
            vs {benchmark.benchmarkValue}{benchmark.unit}
          </span>
        </div>
        <div className={cn(
          "flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded",
          isBetter ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
        )}>
          {isBetter ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          {diff > 0 ? "+" : ""}{percentDiff}%
        </div>
      </div>
    </motion.div>
  );
}

export function PortfolioInsights() {
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
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!score || !assets) return null;

  // Calculate metrics
  const totalRevenue = assets.reduce((sum, a) => sum + a.revenue_usd_m, 0);
  const totalEmissions = assets.reduce((sum, a) => sum + a.scope1_tco2e + a.scope2_tco2e, 0);
  const carbonIntensity = totalEmissions / totalRevenue; // tCO2e per $M
  const avgGreenRevenue = assets.reduce((sum, a) => sum + a.green_revenue_pct, 0) / assets.length;
  const avgControversies = assets.reduce((sum, a) => sum + a.controversies, 0) / assets.length;

  // Calculate data quality score
  const hasAllEmissions = assets.every(a => a.scope1_tco2e > 0 && a.scope2_tco2e > 0);
  const hasAllSectors = assets.every(a => a.sector);
  const hasAllRegions = assets.every(a => a.region);
  const dataQuality = Math.round((
    (hasAllEmissions ? 40 : 20) +
    (hasAllSectors ? 30 : 15) +
    (hasAllRegions ? 30 : 15)
  ));

  // Generate insights based on data
  const insights: Insight[] = [];

  // Carbon intensity insight
  if (carbonIntensity < INDUSTRY_BENCHMARKS.carbonIntensity * 0.7) {
    insights.push({
      type: "positive",
      title: "Low Carbon Intensity",
      description: "Portfolio emissions intensity is significantly below industry average",
      metric: `${carbonIntensity.toFixed(0)} vs ${INDUSTRY_BENCHMARKS.carbonIntensity} tCO2e/$M`,
    });
  } else if (carbonIntensity > INDUSTRY_BENCHMARKS.carbonIntensity * 1.3) {
    insights.push({
      type: "negative",
      title: "High Carbon Intensity",
      description: "Consider reducing exposure to carbon-intensive assets",
      metric: `${carbonIntensity.toFixed(0)} vs ${INDUSTRY_BENCHMARKS.carbonIntensity} tCO2e/$M benchmark`,
    });
  }

  // Green revenue insight
  if (avgGreenRevenue > INDUSTRY_BENCHMARKS.greenRevenue * 1.5) {
    insights.push({
      type: "positive",
      title: "Strong Green Revenue",
      description: "Above-average exposure to sustainable revenue streams",
      metric: `${avgGreenRevenue.toFixed(0)}% green revenue`,
    });
  } else if (avgGreenRevenue < INDUSTRY_BENCHMARKS.greenRevenue * 0.5) {
    insights.push({
      type: "negative",
      title: "Limited Green Exposure",
      description: "Consider increasing allocation to sustainable business models",
    });
  }

  // Transition risk insight
  if (score.transition_risk > 60) {
    insights.push({
      type: "negative",
      title: "Elevated Transition Risk",
      description: "High exposure to policy and technology disruption",
      metric: `${score.transition_risk.toFixed(0)} risk score`,
    });
  }

  // Opportunity insight
  if (score.opportunity_score > 30) {
    insights.push({
      type: "positive",
      title: "Climate Opportunity Upside",
      description: "Well-positioned for low-carbon growth trends",
      metric: `${score.opportunity_score.toFixed(0)} opportunity score`,
    });
  }

  // Controversy insight
  if (avgControversies > 2) {
    insights.push({
      type: "negative",
      title: "ESG Controversy Exposure",
      description: "Some holdings have elevated controversy scores",
    });
  }

  // Ensure we have at least 3 insights
  if (insights.length < 3) {
    insights.push({
      type: "neutral",
      title: "Balanced Risk Profile",
      description: "Portfolio shows moderate climate risk characteristics",
    });
  }

  const benchmarks: Benchmark[] = [
    {
      name: "Carbon Intensity",
      portfolioValue: carbonIntensity,
      benchmarkValue: INDUSTRY_BENCHMARKS.carbonIntensity,
      unit: "",
      betterWhenLower: true,
    },
    {
      name: "Green Revenue",
      portfolioValue: avgGreenRevenue,
      benchmarkValue: INDUSTRY_BENCHMARKS.greenRevenue,
      unit: "%",
      betterWhenLower: false,
    },
    {
      name: "Transition Risk",
      portfolioValue: score.transition_risk,
      benchmarkValue: INDUSTRY_BENCHMARKS.transitionRisk,
      unit: "",
      betterWhenLower: true,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <Card className="shadow-sm hover:shadow-lg transition-all duration-300 border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-primary" />
            Portfolio Insights
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Key findings and peer comparison
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Data Quality Indicator */}
          <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Data Quality Score</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${dataQuality}%` }}
                  transition={{ delay: 0.3, duration: 0.5 }}
                  className={cn(
                    "h-full rounded-full",
                    dataQuality >= 80 && "bg-success",
                    dataQuality >= 50 && dataQuality < 80 && "bg-warning",
                    dataQuality < 50 && "bg-destructive"
                  )}
                />
              </div>
              <span className="text-sm font-medium text-foreground">{dataQuality}%</span>
            </div>
          </div>

          {/* Key Insights */}
          <div>
            <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
              <Target className="h-4 w-4 text-primary" />
              Key Findings
            </h4>
            <div className="space-y-2">
              {insights.slice(0, 4).map((insight, index) => (
                <InsightCard key={index} insight={insight} delay={0.1 * index} />
              ))}
            </div>
          </div>

          {/* Peer Benchmarks */}
          <div>
            <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              vs. Industry Benchmark
            </h4>
            <div>
              {benchmarks.map((benchmark, index) => (
                <BenchmarkRow key={benchmark.name} benchmark={benchmark} delay={0.1 * index} />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
