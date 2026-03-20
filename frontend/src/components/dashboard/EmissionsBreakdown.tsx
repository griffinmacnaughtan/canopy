import { motion } from "framer-motion";
import { Factory, Info } from "lucide-react";
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
import { useAssets } from "@/hooks";

interface EmissionBar {
  sector: string;
  scope1: number;
  scope2: number;
  total: number;
  percentage: number;
}

function EmissionsBarChart({ data }: { data: EmissionBar[] }) {
  const maxTotal = Math.max(...data.map((d) => d.total));

  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <motion.div
          key={item.sector}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-foreground">{item.sector}</span>
            <span className="text-xs text-muted-foreground">
              {(item.total / 1000000).toFixed(1)}M tCO2e ({item.percentage.toFixed(0)}%)
            </span>
          </div>
          <div className="h-6 bg-secondary rounded-full overflow-hidden flex">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(item.scope1 / maxTotal) * 100}%` }}
              transition={{ delay: index * 0.1 + 0.2, duration: 0.5 }}
              className="bg-destructive/80 h-full"
              title={`Scope 1: ${(item.scope1 / 1000000).toFixed(2)}M tCO2e`}
            />
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(item.scope2 / maxTotal) * 100}%` }}
              transition={{ delay: index * 0.1 + 0.3, duration: 0.5 }}
              className="bg-warning/80 h-full"
              title={`Scope 2: ${(item.scope2 / 1000000).toFixed(2)}M tCO2e`}
            />
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export function EmissionsBreakdown() {
  const { data: assets, isLoading } = useAssets();

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

  if (!assets || assets.length === 0) {
    return null;
  }

  // Aggregate emissions by sector
  const sectorEmissions = assets.reduce((acc, asset) => {
    if (!acc[asset.sector]) {
      acc[asset.sector] = { scope1: 0, scope2: 0 };
    }
    acc[asset.sector].scope1 += asset.scope1_tco2e;
    acc[asset.sector].scope2 += asset.scope2_tco2e;
    return acc;
  }, {} as Record<string, { scope1: number; scope2: number }>);

  const totalEmissions = Object.values(sectorEmissions).reduce(
    (sum, s) => sum + s.scope1 + s.scope2,
    0
  );

  const chartData: EmissionBar[] = Object.entries(sectorEmissions)
    .map(([sector, emissions]) => ({
      sector,
      scope1: emissions.scope1,
      scope2: emissions.scope2,
      total: emissions.scope1 + emissions.scope2,
      percentage: ((emissions.scope1 + emissions.scope2) / totalEmissions) * 100,
    }))
    .sort((a, b) => b.total - a.total);

  const totalScope1 = chartData.reduce((sum, d) => sum + d.scope1, 0);
  const totalScope2 = chartData.reduce((sum, d) => sum + d.scope2, 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <Card className="border border-border bg-card shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2">
            <Factory className="h-5 w-5 text-primary" />
            Emissions Breakdown
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Scope 1 & 2 greenhouse gas emissions by sector
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4 p-3 bg-secondary/30 rounded-lg">
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">
                {(totalEmissions / 1000000).toFixed(1)}M
              </p>
              <p className="text-xs text-muted-foreground">Total tCO2e</p>
            </div>
            <TooltipProvider delayDuration={200}>
              <div className="text-center">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="cursor-help">
                      <p className="text-2xl font-bold text-destructive">
                        {((totalScope1 / totalEmissions) * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                        Scope 1 <Info className="h-3 w-3" />
                      </p>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">Direct emissions from owned or controlled sources (e.g., fuel combustion, company vehicles)</p>
                  </TooltipContent>
                </Tooltip>
              </div>
              <div className="text-center">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="cursor-help">
                      <p className="text-2xl font-bold text-warning">
                        {((totalScope2 / totalEmissions) * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
                        Scope 2 <Info className="h-3 w-3" />
                      </p>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">Indirect emissions from purchased electricity, steam, heating, and cooling</p>
                  </TooltipContent>
                </Tooltip>
              </div>
            </TooltipProvider>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-destructive/80" />
              <span className="text-muted-foreground">Scope 1 (Direct)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded bg-warning/80" />
              <span className="text-muted-foreground">Scope 2 (Indirect)</span>
            </div>
          </div>

          {/* Chart */}
          <EmissionsBarChart data={chartData} />
        </CardContent>
      </Card>
    </motion.div>
  );
}
