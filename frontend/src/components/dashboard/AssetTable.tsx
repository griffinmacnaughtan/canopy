import { useState } from "react";
import { motion } from "framer-motion";
import {
  Building2,
  MapPin,
  Leaf,
  AlertTriangle,
  Activity,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, InsightPanel } from "@/components/ui";
import { usePortfolio } from "@/hooks";
import { useCopilotContext } from "@/contexts/CopilotContext";
import { formatNumber, formatCurrency, cn } from "@/lib/utils";
import type { Asset } from "@/types";

// ── Helpers ────────────────────────────────────────────────────────────

function formatEmissions(tco2e: number) {
  if (tco2e >= 1_000_000) return `${(tco2e / 1_000_000).toFixed(1)}M`;
  if (tco2e >= 1_000) return `${(tco2e / 1_000).toFixed(0)}K`;
  return tco2e.toFixed(0);
}

function intensityRating(intensity: number): { label: string; color: string } {
  if (intensity < 50) return { label: "Very Low", color: "text-emerald-600" };
  if (intensity < 145) return { label: "Low", color: "text-emerald-600" };
  if (intensity < 500) return { label: "Moderate", color: "text-amber-500" };
  if (intensity < 1000) return { label: "High", color: "text-red-500" };
  return { label: "Very High", color: "text-red-600" };
}

function controversyLabel(count: number): { label: string; color: string } {
  if (count === 0) return { label: "None", color: "text-emerald-600" };
  if (count <= 1) return { label: "Minor", color: "text-amber-500" };
  if (count <= 2) return { label: "Moderate", color: "text-amber-600" };
  return { label: "Significant", color: "text-red-500" };
}

// ── Stat row ───────────────────────────────────────────────────────────

function StatRow({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border/50 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <div className="text-right">
        <span className="text-sm font-medium text-foreground">{value}</span>
        {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      </div>
    </div>
  );
}

// ── Asset Detail Panel Content ─────────────────────────────────────────

function AssetDetailContent({ asset }: { asset: Asset }) {
  const totalEmissions = asset.scope1_tco2e + asset.scope2_tco2e;
  const intensity = totalEmissions / asset.revenue_usd_m;
  const iRating = intensityRating(intensity);
  const cLabel = controversyLabel(asset.controversies);
  const scope1Pct = totalEmissions > 0 ? (asset.scope1_tco2e / totalEmissions) * 100 : 0;
  const scope2Pct = totalEmissions > 0 ? (asset.scope2_tco2e / totalEmissions) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Quick stats badges */}
      <div className="flex flex-wrap gap-2">
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-secondary text-secondary-foreground">
          <Building2 className="h-3 w-3" />
          {asset.sector}
        </span>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-secondary text-secondary-foreground">
          <MapPin className="h-3 w-3" />
          {asset.region}
        </span>
        {asset.ticker && (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
            {asset.ticker}
          </span>
        )}
      </div>

      {/* Financial */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-2">Financial</h3>
        <StatRow label="Revenue" value={`${formatCurrency(asset.revenue_usd_m)}M`} />
        <StatRow
          label="Green Revenue"
          value={`${asset.green_revenue_pct}%`}
          sub={`${formatCurrency(asset.revenue_usd_m * asset.green_revenue_pct / 100)}M climate-aligned`}
        />
      </div>

      {/* Emissions */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-2">Emissions</h3>
        <StatRow label="Total Emissions" value={`${formatEmissions(totalEmissions)} tCO2e`} />
        <StatRow
          label="Scope 1 (Direct)"
          value={`${formatEmissions(asset.scope1_tco2e)} tCO2e`}
          sub={`${scope1Pct.toFixed(0)}% of total`}
        />
        <StatRow
          label="Scope 2 (Electricity)"
          value={`${formatEmissions(asset.scope2_tco2e)} tCO2e`}
          sub={`${scope2Pct.toFixed(0)}% of total`}
        />
        <div className="mt-3">
          <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden flex">
            <div className="bg-red-400 h-full" style={{ width: `${scope1Pct}%` }} />
            <div className="bg-amber-400 h-full" style={{ width: `${scope2Pct}%` }} />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>Scope 1</span>
            <span>Scope 2</span>
          </div>
        </div>
      </div>

      {/* Risk indicators */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-2">Risk Profile</h3>
        <div className="flex items-center justify-between py-2.5 border-b border-border/50">
          <span className="text-sm text-muted-foreground flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5" />
            Carbon Intensity
          </span>
          <span className={cn("text-sm font-medium", iRating.color)}>
            {formatNumber(intensity, 0)} tCO2e/$M ({iRating.label})
          </span>
        </div>
        <div className="flex items-center justify-between py-2.5 border-b border-border/50">
          <span className="text-sm text-muted-foreground flex items-center gap-1.5">
            <Leaf className="h-3.5 w-3.5" />
            Green Revenue
          </span>
          <span className={cn(
            "text-sm font-medium",
            asset.green_revenue_pct >= 50 ? "text-emerald-600" : asset.green_revenue_pct >= 20 ? "text-amber-500" : "text-muted-foreground",
          )}>
            {asset.green_revenue_pct}%
          </span>
        </div>
        <div className="flex items-center justify-between py-2.5">
          <span className="text-sm text-muted-foreground flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5" />
            Controversies
          </span>
          <span className={cn("text-sm font-medium", cLabel.color)}>
            {asset.controversies} ({cLabel.label})
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Skeleton ───────────────────────────────────────────────────────────

function TableSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Main Component ─────────────────────────────────────────────────────

export function AssetTable() {
  const { data: portfolio, isLoading, error } = usePortfolio();
  const { askCopilot } = useCopilotContext();
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

  if (isLoading) return <TableSkeleton />;

  if (error || !portfolio) {
    return (
      <Card className="p-6 text-center text-muted-foreground">
        Failed to load portfolio assets
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6 }}
    >
      <Card>
        <CardHeader>
          <CardTitle>Asset Inventory</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Asset</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Sector</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Region</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Revenue</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Emissions</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Green %</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.assets.map((asset, index) => {
                  const totalEmissions = asset.scope1_tco2e + asset.scope2_tco2e;
                  const intensity = totalEmissions / asset.revenue_usd_m;

                  return (
                    <motion.tr
                      key={asset.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.7 + index * 0.05 }}
                      className="border-b border-border/50 hover:bg-emerald-50/40 transition-colors cursor-pointer"
                      onClick={() => setSelectedAsset(asset)}
                    >
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium text-foreground">{asset.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatNumber(intensity, 0)} tCO2e/$M
                          </p>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-secondary text-secondary-foreground">
                          {asset.sector}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">{asset.region}</td>
                      <td className="py-3 px-4 text-right text-sm font-medium">
                        {formatCurrency(asset.revenue_usd_m)}M
                      </td>
                      <td className="py-3 px-4 text-right text-sm">
                        <span className={cn("font-medium", intensity > 1000 ? "text-destructive" : intensity > 500 ? "text-warning" : "text-success")}>
                          {formatNumber(totalEmissions)}
                        </span>
                        <span className="text-muted-foreground text-xs ml-1">tCO2e</span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={cn("text-sm font-medium", asset.green_revenue_pct >= 20 ? "text-success" : asset.green_revenue_pct >= 10 ? "text-warning" : "text-muted-foreground")}>
                          {asset.green_revenue_pct}%
                        </span>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Asset Detail Panel */}
      <InsightPanel
        isOpen={!!selectedAsset}
        onClose={() => setSelectedAsset(null)}
        title={selectedAsset?.name || ""}
        subtitle={selectedAsset?.ticker ? `${selectedAsset.ticker} \u00B7 ${selectedAsset.sector}` : selectedAsset?.sector}
        icon={<Building2 className="h-5 w-5" />}
        onAskCopilot={
          selectedAsset
            ? () => {
                const a = selectedAsset;
                askCopilot(
                  `Analyze ${a.name}'s climate risk profile. They have ${formatEmissions(a.scope1_tco2e + a.scope2_tco2e)} tCO2e emissions, ${a.green_revenue_pct}% green revenue, and ${a.controversies} controversies. What are the key risks, transition opportunities, and how do they compare to sector peers?`,
                );
                setSelectedAsset(null);
              }
            : undefined
        }
      >
        {selectedAsset && <AssetDetailContent asset={selectedAsset} />}
      </InsightPanel>
    </motion.div>
  );
}
