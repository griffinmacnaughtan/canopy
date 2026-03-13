import { useState } from "react";
import { Leaf, ChevronDown, Plus, Sparkles } from "lucide-react";
import { useHealth } from "@/hooks";
import { usePortfolioContext } from "@/contexts/PortfolioContext";
import { PortfolioBuilder } from "@/components/portfolio";
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
  } = usePortfolioContext();
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);

  const handleSavePortfolio = async (name: string, assets: Asset[]) => {
    try {
      await createPortfolio(name, assets);
      setIsBuilderOpen(false);
    } catch (error) {
      console.error("Failed to create portfolio:", error);
    }
  };

  return (
    <header className="border-b border-emerald-200/50 bg-white/80 backdrop-blur-xl sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500 to-forest-600 shadow-lg shadow-emerald-500/25">
            <Leaf className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold font-serif tracking-tight">
              <span className="bg-gradient-to-r from-emerald-600 to-forest-600 bg-clip-text text-transparent">Canopy</span>
            </h1>
            <p className="text-xs text-emerald-600/70 font-medium">
              Climate Risk Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
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
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-600/60 pointer-events-none" />
          </div>

          {/* New Portfolio Button */}
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
                <span className={`w-2 h-2 rounded-full ${
                  isLoading
                    ? "bg-gray-400 animate-pulse"
                    : health?.status === "ok"
                      ? "bg-emerald-500 shadow-sm shadow-emerald-500/50"
                      : "bg-red-500"
                }`} />
                {isLoading ? "Connecting..." : health?.status === "ok" ? "Live" : "Offline"}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Portfolio Builder Modal */}
      <PortfolioBuilder
        isOpen={isBuilderOpen}
        onClose={() => setIsBuilderOpen(false)}
        onSave={handleSavePortfolio}
      />
    </header>
  );
}
