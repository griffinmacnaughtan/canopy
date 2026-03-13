/**
 * Pipeline Data Explorer
 * Displays real EPA emissions and climate data from the data pipeline.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Database,
  Factory,
  Thermometer,
  TrendingUp,
  Activity,
  ChevronDown,
  MapPin,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { api } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { EmissionsFacility, SectorEmissionsSummary } from "@/types";

function formatNumber(num: number | null | undefined): string {
  if (num == null) return "N/A";
  if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)}B`;
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toFixed(0);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Never";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function PipelineExplorer() {
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [showAllEmitters, setShowAllEmitters] = useState(false);

  // Fetch pipeline stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["pipelineStats"],
    queryFn: () => api.getPipelineStats(),
    staleTime: 60_000,
  });

  // Fetch top emitters
  const { data: topEmitters, isLoading: emittersLoading } = useQuery({
    queryKey: ["topEmitters"],
    queryFn: () => api.getTopEmitters(showAllEmitters ? 20 : 8),
    staleTime: 60_000,
  });

  // Fetch emissions by sector if selected
  const { data: sectorEmissions } = useQuery({
    queryKey: ["sectorEmissions", selectedSector],
    queryFn: () => api.getEmissionsData({ sector: selectedSector || undefined, limit: 10 }),
    enabled: !!selectedSector,
    staleTime: 60_000,
  });

  // Fetch pipeline runs
  const { data: runs } = useQuery({
    queryKey: ["pipelineRuns"],
    queryFn: () => api.getPipelineRuns(5),
    staleTime: 60_000,
  });

  const isDemo = api.isDemoMode();

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/25">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-xl">Data Pipeline Explorer</CardTitle>
              <p className="text-sm text-muted-foreground mt-0.5">
                Real EPA emissions and climate data
              </p>
            </div>
          </div>
          {isDemo && (
            <span className="px-3 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">
              Demo Data
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon={Factory}
            label="Emissions Records"
            value={statsLoading ? null : stats?.total_emissions_records}
            color="blue"
          />
          <StatCard
            icon={Thermometer}
            label="Climate Records"
            value={statsLoading ? null : stats?.total_climate_records}
            color="emerald"
          />
          <StatCard
            icon={MapPin}
            label="States Covered"
            value={statsLoading ? null : stats?.states_covered}
            color="purple"
          />
          <StatCard
            icon={Calendar}
            label="Latest Year"
            value={statsLoading ? null : stats?.latest_emissions_year}
            color="amber"
            isYear
          />
        </div>

        {/* Data Sources */}
        {stats?.data_sources && stats.data_sources.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {stats.data_sources.map((source) => (
              <span
                key={source}
                className="px-3 py-1.5 text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-full"
              >
                {source}
              </span>
            ))}
          </div>
        )}

        {/* Emissions by Sector */}
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-500" />
            Emissions by Sector
          </h4>
          {statsLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {stats?.emissions_by_sector?.slice(0, 6).map((sector, idx) => (
                <SectorBar
                  key={sector.sector}
                  sector={sector}
                  maxEmissions={stats.emissions_by_sector[0].total_emissions_mt_co2e}
                  index={idx}
                  isSelected={selectedSector === sector.sector}
                  onClick={() =>
                    setSelectedSector(selectedSector === sector.sector ? null : sector.sector)
                  }
                />
              ))}
            </div>
          )}
        </div>

        {/* Sector Drill-down */}
        {selectedSector && sectorEmissions && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4"
          >
            <h5 className="text-sm font-semibold mb-3">
              Top Facilities in {selectedSector}
            </h5>
            <div className="space-y-2">
              {sectorEmissions.slice(0, 5).map((facility) => (
                <FacilityRow key={facility.facility_id} facility={facility} />
              ))}
            </div>
          </motion.div>
        )}

        {/* Top Emitters */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Factory className="h-4 w-4 text-red-500" />
              Top Emitting Facilities
            </h4>
            <button
              onClick={() => setShowAllEmitters(!showAllEmitters)}
              className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              {showAllEmitters ? "Show Less" : "Show More"}
              <ChevronDown
                className={`h-3 w-3 transition-transform ${showAllEmitters ? "rotate-180" : ""}`}
              />
            </button>
          </div>

          {emittersLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {topEmitters?.map((facility, idx) => (
                <EmitterCard key={facility.facility_id} facility={facility} rank={idx + 1} />
              ))}
            </div>
          )}
        </div>

        {/* Pipeline Runs */}
        {runs && runs.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-green-500" />
              Recent Pipeline Runs
            </h4>
            <div className="space-y-2">
              {runs.map((run) => (
                <div
                  key={run.run_id}
                  className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <RefreshCw
                      className={`h-4 w-4 ${
                        run.status === "success"
                          ? "text-green-500"
                          : run.status === "partial"
                            ? "text-amber-500"
                            : "text-red-500"
                      }`}
                    />
                    <div>
                      <p className="text-sm font-medium">{run.run_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatDate(run.started_at)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {formatNumber(run.records_loaded)} loaded
                    </p>
                    <p className="text-xs text-muted-foreground capitalize">{run.status}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Last Updated */}
        {stats?.last_updated && (
          <p className="text-xs text-muted-foreground text-center pt-2 border-t">
            Last updated: {formatDate(stats.last_updated)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// Sub-components
function StatCard({
  icon: Icon,
  label,
  value,
  color,
  isYear,
}: {
  icon: React.ElementType;
  label: string;
  value: number | null | undefined;
  color: "blue" | "emerald" | "purple" | "amber";
  isYear?: boolean;
}) {
  const colors = {
    blue: "from-blue-500 to-blue-600 shadow-blue-500/25",
    emerald: "from-emerald-500 to-emerald-600 shadow-emerald-500/25",
    purple: "from-purple-500 to-purple-600 shadow-purple-500/25",
    amber: "from-amber-500 to-amber-600 shadow-amber-500/25",
  };

  return (
    <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
      <div
        className={`w-8 h-8 rounded-lg bg-gradient-to-br ${colors[color]} flex items-center justify-center mb-2 shadow-lg`}
      >
        <Icon className="h-4 w-4 text-white" />
      </div>
      <p className="text-xs text-muted-foreground">{label}</p>
      {value == null ? (
        <Skeleton className="h-6 w-16 mt-1" />
      ) : (
        <p className="text-lg font-bold">{isYear ? value : formatNumber(value)}</p>
      )}
    </div>
  );
}

function SectorBar({
  sector,
  maxEmissions,
  index,
  isSelected,
  onClick,
}: {
  sector: SectorEmissionsSummary;
  maxEmissions: number;
  index: number;
  isSelected: boolean;
  onClick: () => void;
}) {
  const percentage = (sector.total_emissions_mt_co2e / maxEmissions) * 100;

  return (
    <motion.button
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg transition-all ${
        isSelected
          ? "bg-blue-100 dark:bg-blue-900/30 ring-1 ring-blue-500"
          : "bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800"
      }`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm font-medium truncate pr-2">{sector.sector}</span>
        <span className="text-sm font-bold text-blue-600">
          {formatNumber(sector.total_emissions_mt_co2e)} tCO2e
        </span>
      </div>
      <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, delay: index * 0.05 }}
          className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"
        />
      </div>
      <p className="text-xs text-muted-foreground mt-1">
        {sector.facility_count} facilities | Avg: {formatNumber(sector.avg_emissions_per_facility)}{" "}
        tCO2e
      </p>
    </motion.button>
  );
}

function FacilityRow({ facility }: { facility: EmissionsFacility }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-200 dark:border-slate-700 last:border-0">
      <div>
        <p className="text-sm font-medium">{facility.facility_name || "Unknown Facility"}</p>
        <p className="text-xs text-muted-foreground">
          {facility.city}, {facility.state}
        </p>
      </div>
      <span className="text-sm font-bold text-blue-600">
        {formatNumber(facility.total_emissions_mt_co2e)} tCO2e
      </span>
    </div>
  );
}

function EmitterCard({ facility, rank }: { facility: EmissionsFacility; rank: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.03 }}
      className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl"
    >
      <div className="flex items-start gap-3">
        <span
          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
            rank <= 3
              ? "bg-red-100 text-red-600 dark:bg-red-900/30"
              : "bg-slate-200 text-slate-600 dark:bg-slate-700"
          }`}
        >
          {rank}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold truncate">
            {facility.facility_name || "Unknown Facility"}
          </p>
          <p className="text-xs text-muted-foreground">
            {facility.city}, {facility.state} | {facility.sector}
          </p>
          <p className="text-sm font-bold text-red-600 mt-1">
            {formatNumber(facility.total_emissions_mt_co2e)} tCO2e
          </p>
        </div>
      </div>
    </motion.div>
  );
}
