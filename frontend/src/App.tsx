import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { MainLayout } from "@/components/layout";
import {
  PortfolioOverview,
  RiskNarrative,
  SectorBreakdown,
  ScenarioEngine,
  AssetTable,
  EmissionsBreakdown,
  RegulatoryReadiness,
  PortfolioInsights,
  NetZeroPathway,
  PipelineExplorer,
} from "@/components/dashboard";
import { CopilotWorkspace } from "@/components/copilot";
import { ErrorBoundary } from "@/components/ui";
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

function Dashboard() {
  const { data: portfolio } = usePortfolio();

  return (
    <div className="space-y-6">
      {/* Command Bar */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center justify-between py-2"
      >
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">
            {portfolio?.name || "Portfolio"}
          </h1>
          <p className="text-sm text-muted-foreground">
            {portfolio?.description || "Climate risk analytics and AI-powered insights"}
          </p>
        </div>
      </motion.section>

      {/* Portfolio Overview — 6 metric tiles */}
      <section>
        <ErrorBoundary name="Portfolio Overview">
          <PortfolioOverview />
        </ErrorBoundary>
      </section>

      {/* AI Copilot — Primary feature, full width */}
      <section>
        <ErrorBoundary name="AI Copilot">
          <CopilotWorkspace />
        </ErrorBoundary>
      </section>

      {/* 2-col: Portfolio Insights + Scenario Engine */}
      <section className="grid md:grid-cols-2 gap-6">
        <ErrorBoundary name="Portfolio Insights">
          <PortfolioInsights />
        </ErrorBoundary>
        <ErrorBoundary name="Scenario Engine">
          <ScenarioEngine />
        </ErrorBoundary>
      </section>

      {/* 2-col: Emissions Breakdown + Sector Breakdown */}
      <section className="grid md:grid-cols-2 gap-6">
        <ErrorBoundary name="Emissions Breakdown">
          <EmissionsBreakdown />
        </ErrorBoundary>
        <ErrorBoundary name="Sector Breakdown">
          <SectorBreakdown />
        </ErrorBoundary>
      </section>

      {/* Regulatory Readiness — full width */}
      <section id="analysis-section">
        <ErrorBoundary name="Regulatory Readiness">
          <RegulatoryReadiness />
        </ErrorBoundary>
      </section>

      {/* 2-col: Net Zero Pathway + Risk Narrative */}
      <section className="grid md:grid-cols-2 gap-6">
        <ErrorBoundary name="Net Zero Pathway">
          <NetZeroPathway />
        </ErrorBoundary>
        <ErrorBoundary name="Risk Narrative">
          <RiskNarrative />
        </ErrorBoundary>
      </section>

      {/* Asset Table — full width */}
      <section>
        <ErrorBoundary name="Asset Table">
          <AssetTable />
        </ErrorBoundary>
      </section>

      {/* Data Pipeline Explorer — infrastructure detail, bottom */}
      <section>
        <ErrorBoundary name="Pipeline Explorer">
          <PipelineExplorer />
        </ErrorBoundary>
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
