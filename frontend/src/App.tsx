import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Leaf, Shield, Zap, LineChart } from "lucide-react";
import { MainLayout } from "@/components/layout";
import {
  PortfolioSignal,
  RiskNarrative,
  SectorBreakdown,
  ScenarioEngine,
  AssetTable,
  EmissionsBreakdown,
  RegulatoryReadiness,
  PortfolioInsights,
  NetZeroPathway,
  ImpactSummary,
  PipelineExplorer,
} from "@/components/dashboard";
import { CopilotWorkspace } from "@/components/copilot";
import { usePortfolio } from "@/hooks";
import { PortfolioProvider } from "@/contexts/PortfolioContext";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
    },
  },
});

const FEATURES = [
  { icon: Shield, label: "Risk Analysis" },
  { icon: Leaf, label: "ESG Scoring" },
  { icon: Zap, label: "AI Insights" },
  { icon: LineChart, label: "Scenarios" },
];

function Dashboard() {
  const { data: portfolio } = usePortfolio();

  return (
    <div className="space-y-10">
      {/* Hero Section - Enhanced */}
      <motion.section
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center py-16 relative"
      >
        {/* Background decoration */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-emerald-200/40 via-transparent to-forest-200/30 blur-3xl" />
        </div>

        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-gradient-to-r from-emerald-100 to-forest-100 text-emerald-700 text-sm font-semibold mb-8 border border-emerald-200/50 shadow-sm"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-lg shadow-emerald-500/50" />
          Live Climate Intelligence
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="text-5xl md:text-6xl lg:text-7xl font-bold font-serif text-foreground mb-6 tracking-tight"
        >
          <span className="bg-gradient-to-r from-emerald-600 via-forest-600 to-emerald-600 bg-clip-text text-transparent">
            {portfolio?.name || "Portfolio"}
          </span>
          <br />
          <span className="text-foreground">Dashboard</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed mb-10"
        >
          Transform your investment strategy with real-time climate risk analytics,
          TCFD-aligned reporting, and AI-powered recommendations.
        </motion.p>

        {/* Feature pills */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="flex flex-wrap items-center justify-center gap-3"
        >
          {FEATURES.map(({ icon: Icon, label }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 + i * 0.05 }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/80 backdrop-blur-sm border border-emerald-100 shadow-sm text-sm font-medium text-foreground hover:border-emerald-300 hover:shadow-md transition-all"
            >
              <Icon className="h-4 w-4 text-emerald-600" />
              {label}
            </motion.div>
          ))}
        </motion.div>
      </motion.section>

      {/* Impact Summary - NEW prominent placement */}
      <section>
        <ImpactSummary />
      </section>

      {/* Portfolio Signal - Key Metrics */}
      <section>
        <PortfolioSignal />
      </section>

      {/* AI Copilot - Full Width & Prominent */}
      <section>
        <CopilotWorkspace />
      </section>

      {/* Portfolio Insights */}
      <section>
        <PortfolioInsights />
      </section>

      {/* Scenario Engine - Full Width */}
      <section>
        <ScenarioEngine />
      </section>

      {/* Data Pipeline Explorer - Real EPA/Climate Data */}
      <section>
        <PipelineExplorer />
      </section>

      {/* Regulatory Readiness - Full Width */}
      <section id="analysis-section">
        <RegulatoryReadiness />
      </section>

      {/* Three Column: Emissions, Net Zero, Risk Narrative */}
      <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <EmissionsBreakdown />
        <NetZeroPathway />
        <RiskNarrative />
      </section>

      {/* Sector Breakdown */}
      <section>
        <SectorBreakdown />
      </section>

      {/* Asset Inventory Table */}
      <section>
        <AssetTable />
      </section>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <PortfolioProvider>
        <MainLayout>
          <Dashboard />
        </MainLayout>
      </PortfolioProvider>
    </QueryClientProvider>
  );
}
