import { motion } from "framer-motion";
import { Shield, CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react";
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

interface Framework {
  id: string;
  name: string;
  fullName: string;
  description: string;
  score: number;
  status: "compliant" | "partial" | "gaps";
  requirements: { name: string; met: boolean }[];
}

function getStatusIcon(status: Framework["status"]) {
  switch (status) {
    case "compliant":
      return <CheckCircle2 className="h-4 w-4 text-success" />;
    case "partial":
      return <AlertTriangle className="h-4 w-4 text-warning" />;
    case "gaps":
      return <XCircle className="h-4 w-4 text-destructive" />;
  }
}

function getStatusLabel(status: Framework["status"]) {
  switch (status) {
    case "compliant":
      return "Ready";
    case "partial":
      return "Partial";
    case "gaps":
      return "Gaps";
  }
}

function FrameworkCard({ framework, delay }: { framework: Framework; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="p-4 rounded-lg border border-border bg-card hover:shadow-sm transition-shadow"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <TooltipProvider delayDuration={200}>
            <Tooltip>
              <TooltipTrigger asChild>
                <h4 className="font-semibold text-foreground flex items-center gap-1.5 cursor-help">
                  {framework.name}
                  <Info className="h-3 w-3 text-muted-foreground" />
                </h4>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="font-medium mb-1">{framework.fullName}</p>
                <p className="text-sm text-muted-foreground">{framework.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <div className={cn(
          "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
          framework.status === "compliant" && "bg-success/10 text-success",
          framework.status === "partial" && "bg-warning/10 text-warning",
          framework.status === "gaps" && "bg-destructive/10 text-destructive"
        )}>
          {getStatusIcon(framework.status)}
          {getStatusLabel(framework.status)}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-muted-foreground">Alignment Score</span>
          <span className="font-medium text-foreground">{framework.score}%</span>
        </div>
        <div className="h-2 bg-secondary rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${framework.score}%` }}
            transition={{ delay: delay + 0.2, duration: 0.5 }}
            className={cn(
              "h-full rounded-full",
              framework.score >= 80 && "bg-success",
              framework.score >= 50 && framework.score < 80 && "bg-warning",
              framework.score < 50 && "bg-destructive"
            )}
          />
        </div>
      </div>

      {/* Requirements checklist */}
      <div className="space-y-1.5">
        {framework.requirements.map((req) => (
          <div key={req.name} className="flex items-center gap-2 text-xs">
            {req.met ? (
              <CheckCircle2 className="h-3 w-3 text-success flex-shrink-0" />
            ) : (
              <XCircle className="h-3 w-3 text-muted-foreground flex-shrink-0" />
            )}
            <span className={cn(
              req.met ? "text-foreground" : "text-muted-foreground"
            )}>
              {req.name}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export function RegulatoryReadiness() {
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
          <div className="grid grid-cols-3 gap-4">
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!score || !assets) return null;

  // Calculate framework scores based on portfolio data
  const avgGreenRevenue = assets.reduce((sum, a) => sum + a.green_revenue_pct, 0) / assets.length;
  const avgControversies = assets.reduce((sum, a) => sum + a.controversies, 0) / assets.length;
  const hasEmissionsData = assets.every((a) => a.scope1_tco2e > 0);
  const hasSectorData = assets.every((a) => a.sector);

  const frameworks: Framework[] = [
    {
      id: "tcfd",
      name: "TCFD",
      fullName: "Task Force on Climate-related Financial Disclosures",
      description: "Framework for climate risk disclosure covering governance, strategy, risk management, and metrics.",
      score: Math.min(95, Math.round(60 + (hasEmissionsData ? 20 : 0) + (score.overall_score > 50 ? 15 : 0))),
      status: hasEmissionsData && score.overall_score > 50 ? "compliant" : "partial",
      requirements: [
        { name: "Governance disclosure", met: true },
        { name: "Strategy & scenarios", met: true },
        { name: "Risk management process", met: hasEmissionsData },
        { name: "Metrics & targets", met: hasEmissionsData },
      ],
    },
    {
      id: "eu-taxonomy",
      name: "EU Taxonomy",
      fullName: "EU Taxonomy for Sustainable Activities",
      description: "Classification system for environmentally sustainable economic activities in the European Union.",
      score: Math.min(100, Math.round(avgGreenRevenue * 2.5)),
      status: avgGreenRevenue > 30 ? "compliant" : avgGreenRevenue > 15 ? "partial" : "gaps",
      requirements: [
        { name: "Climate mitigation", met: avgGreenRevenue > 20 },
        { name: "Climate adaptation", met: score.physical_risk < 50 },
        { name: "Do no significant harm", met: avgControversies < 2 },
        { name: "Minimum safeguards", met: avgControversies < 3 },
      ],
    },
    {
      id: "sfdr",
      name: "SFDR",
      fullName: "Sustainable Finance Disclosure Regulation",
      description: "EU regulation requiring disclosure of sustainability risks and impacts for financial products.",
      score: Math.min(90, Math.round(50 + (hasEmissionsData ? 25 : 0) + (hasSectorData ? 15 : 0))),
      status: hasEmissionsData && hasSectorData ? "compliant" : "partial",
      requirements: [
        { name: "PAI indicators", met: hasEmissionsData },
        { name: "Article 8 alignment", met: avgGreenRevenue > 10 },
        { name: "Article 9 alignment", met: avgGreenRevenue > 40 },
        { name: "Taxonomy reporting", met: hasSectorData },
      ],
    },
  ];

  const overallReadiness = Math.round(
    frameworks.reduce((sum, f) => sum + f.score, 0) / frameworks.length
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      <Card className="shadow-sm hover:shadow-lg transition-all duration-300 border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                Regulatory Readiness
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Alignment with major climate disclosure frameworks
              </p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-foreground">{overallReadiness}%</p>
              <p className="text-xs text-muted-foreground">Overall Readiness</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            {frameworks.map((framework, index) => (
              <FrameworkCard
                key={framework.id}
                framework={framework}
                delay={0.1 * index}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
