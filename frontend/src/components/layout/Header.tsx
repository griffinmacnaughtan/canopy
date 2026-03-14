import { useState } from "react";
import {
  Leaf, ChevronDown, Plus, Sparkles,
  Upload, Download, Trash2, Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { useHealth } from "@/hooks";
import { usePortfolioContext } from "@/contexts/PortfolioContext";
import { PortfolioBuilder, ImportCsvModal } from "@/components/portfolio";
import { api } from "@/api/client";
import type { Asset } from "@/types";

export function Header() {
  const isDemo = api.isDemoMode();
  const { data: health, isLoading } = useHealth();
  const {
    selectedPortfolioId,
    setSelectedPortfolioId,
    portfolios,
    isLoading: portfoliosLoading,
    createPortfolio,
    isCreating,
    deletePortfolio,
    isDeleting,
  } = usePortfolioContext();

  const [isBuilderOpen, setIsBuilderOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const selectedPortfolio = portfolios.find((p) => p.id === selectedPortfolioId);
  const canDelete = selectedPortfolio && !selectedPortfolio.is_sample;

  const handleSavePortfolio = async (name: string, assets: Asset[]) => {
    try {
      await createPortfolio(name, assets);
      setIsBuilderOpen(false);
      toast.success(`Portfolio "${name}" created`);
    } catch (error) {
      toast.error("Failed to create portfolio");
      console.error(error);
    }
  };

  const handleDelete = async () => {
    if (!selectedPortfolioId || !selectedPortfolio) return;
    const confirmed = window.confirm(
      `Delete "${selectedPortfolio.name}"? This cannot be undone.`
    );
    if (!confirmed) return;
    try {
      await deletePortfolio(selectedPortfolioId);
      toast.success(`Portfolio "${selectedPortfolio.name}" deleted`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Delete failed";
      toast.error(msg);
    }
  };

  const handleExport = async () => {
    if (!selectedPortfolioId) return;
    setIsExporting(true);
    try {
      const report = await api.exportPortfolio(selectedPortfolioId);
      const blob = new Blob([JSON.stringify(report, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${report.portfolio_name.replace(/\s+/g, "_")}_risk_report.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Risk report exported");
    } catch {
      toast.error("Export failed — try again");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <header className="border-b border-emerald-200/50 bg-white/80 backdrop-blur-xl sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500 to-forest-600 shadow-lg shadow-emerald-500/25">
            <Leaf className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold font-serif tracking-tight">
              <span className="bg-gradient-to-r from-emerald-600 to-forest-600 bg-clip-text text-transparent">
                Canopy
              </span>
            </h1>
            <p className="text-xs text-emerald-600/70 font-medium">
              Climate Risk Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Portfolio Selector */}
          <div className="relative">
            <select
              value={selectedPortfolioId}
              onChange={(e) => setSelectedPortfolioId(e.target.value)}
              disabled={portfoliosLoading || isCreating}
              className="appearance-none bg-emerald-50/80 backdrop-blur-sm text-foreground px-4 py-2.5 pr-10 rounded-xl border border-emerald-200/60 text-sm font-medium cursor-pointer hover:border-emerald-400 hover:bg-emerald-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              {portfolios.map((portfolio) => (
                <option key={portfolio.id} value={portfolio.id}>
                  {portfolio.name}
                  {portfolio.is_sample ? " ★" : ""}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-600/60 pointer-events-none" />
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {/* Export risk report */}
            <button
              onClick={handleExport}
              disabled={!selectedPortfolioId || isExporting}
              title="Download full risk report as JSON"
              className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl border border-emerald-200 bg-white text-emerald-700 text-xs font-semibold hover:bg-emerald-50 hover:border-emerald-300 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              {isExporting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="h-3.5 w-3.5" />
              )}
              Export
            </button>

            {/* Import from CSV */}
            <button
              onClick={() => setIsImportOpen(true)}
              title="Import portfolio from CSV spreadsheet"
              className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl border border-emerald-200 bg-white text-emerald-700 text-xs font-semibold hover:bg-emerald-50 hover:border-emerald-300 transition-all shadow-sm"
            >
              <Upload className="h-3.5 w-3.5" />
              Import
            </button>

            {/* Delete — only for custom (non-sample) portfolios */}
            {canDelete && (
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                title="Delete this portfolio"
                className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl border border-red-200 bg-white text-red-600 text-xs font-semibold hover:bg-red-50 hover:border-red-300 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
              >
                {isDeleting ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Trash2 className="h-3.5 w-3.5" />
                )}
                Delete
              </button>
            )}
          </div>

          {/* New Portfolio */}
          <button
            onClick={() => setIsBuilderOpen(true)}
            disabled={isCreating}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-forest-600 text-white text-sm font-semibold shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/30 hover:from-emerald-600 hover:to-forest-700 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus className="h-4 w-4" />
            {isCreating ? "Creating..." : "New Portfolio"}
          </button>

          {/* Connection Status */}
          <div
            className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold shadow-sm ${
              isDemo
                ? "bg-amber-100 text-amber-700 border border-amber-200"
                : isLoading
                  ? "bg-gray-100 text-gray-500"
                  : health?.status === "ok"
                    ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                    : "bg-red-100 text-red-700 border border-red-200"
            }`}
          >
            {isDemo ? (
              <>
                <Sparkles className="w-3 h-3" />
                Demo Mode
              </>
            ) : (
              <>
                <span
                  className={`w-2 h-2 rounded-full ${
                    isLoading
                      ? "bg-gray-400 animate-pulse"
                      : health?.status === "ok"
                        ? "bg-emerald-500 shadow-sm shadow-emerald-500/50"
                        : "bg-red-500"
                  }`}
                />
                {isLoading
                  ? "Connecting..."
                  : health?.status === "ok"
                    ? "Live"
                    : "Offline"}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <PortfolioBuilder
        isOpen={isBuilderOpen}
        onClose={() => setIsBuilderOpen(false)}
        onSave={handleSavePortfolio}
      />
      <ImportCsvModal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
      />
    </header>
  );
}
