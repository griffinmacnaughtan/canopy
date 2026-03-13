import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent, Skeleton } from "@/components/ui";
import { usePortfolio } from "@/hooks";
import { formatNumber, formatCurrency, cn } from "@/lib/utils";

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

export function AssetTable() {
  const { data: portfolio, isLoading, error } = usePortfolio();

  if (isLoading) {
    return <TableSkeleton />;
  }

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
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Asset
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Sector
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Region
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Revenue
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Emissions
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Green %
                  </th>
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
                      className="border-b border-border/50 hover:bg-secondary/30 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium text-foreground">
                            {asset.name}
                          </p>
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
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {asset.region}
                      </td>
                      <td className="py-3 px-4 text-right text-sm font-medium">
                        {formatCurrency(asset.revenue_usd_m)}M
                      </td>
                      <td className="py-3 px-4 text-right text-sm">
                        <span
                          className={cn(
                            "font-medium",
                            intensity > 1000
                              ? "text-destructive"
                              : intensity > 500
                                ? "text-warning"
                                : "text-success"
                          )}
                        >
                          {formatNumber(totalEmissions)}
                        </span>
                        <span className="text-muted-foreground text-xs ml-1">
                          tCO2e
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span
                          className={cn(
                            "text-sm font-medium",
                            asset.green_revenue_pct >= 20
                              ? "text-success"
                              : asset.green_revenue_pct >= 10
                                ? "text-warning"
                                : "text-muted-foreground"
                          )}
                        >
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
    </motion.div>
  );
}
