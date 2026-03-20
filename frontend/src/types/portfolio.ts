export interface Asset {
  id: string;
  name: string;
  ticker?: string | null;
  sector: string;
  region: string;
  revenue_usd_m: number;
  scope1_tco2e: number;
  scope2_tco2e: number;
  green_revenue_pct: number;
  controversies: number;
}

export interface Portfolio {
  id: string;
  name: string;
  description?: string;
  assets: Asset[];
}

export interface PortfolioSummary {
  id: string;
  name: string;
  description?: string | null;
  asset_count: number;
  is_sample?: boolean;
}

// ---------------------------------------------------------------------------
// Delete
// ---------------------------------------------------------------------------

export interface DeletePortfolioResponse {
  success: boolean;
  message: string;
}

// ---------------------------------------------------------------------------
// Comparison
// ---------------------------------------------------------------------------

export interface PortfolioScoreSummary {
  portfolio_id: string;
  portfolio_name: string;
  overall_score: number;
  climate_risk: number;
  transition_risk: number;
  physical_risk: number;
  opportunity_score: number;
  asset_count: number;
  total_emissions_tco2e: number;
  avg_green_revenue_pct: number;
  sector_breakdown: Record<string, number>;
}

export interface ComparePortfoliosResponse {
  portfolio_a: PortfolioScoreSummary;
  portfolio_b: PortfolioScoreSummary;
  delta: Record<string, number>;
  recommendation: string;
}

// ---------------------------------------------------------------------------
// Export / Report
// ---------------------------------------------------------------------------

export interface ScenarioImpactItem {
  scenario: string;
  est_ebitda_impact_pct: number;
  emissions_delta_pct: number;
  hotspots: string[];
}

export interface PortfolioExportReport {
  generated_at: string;
  portfolio_id: string;
  portfolio_name: string;
  description?: string | null;
  asset_count: number;
  overall_score: number;
  climate_risk: number;
  transition_risk: number;
  physical_risk: number;
  opportunity_score: number;
  top_risks: string[];
  quick_wins: string[];
  sector_breakdown: Record<string, number>;
  assets: Record<string, unknown>[];
  scenario_impacts: ScenarioImpactItem[];
}

// ---------------------------------------------------------------------------
// CSV Import
// ---------------------------------------------------------------------------

export interface CsvImportResponse {
  success: boolean;
  portfolio: PortfolioSummary;
  rows_imported: number;
  rows_skipped: number;
  warnings: string[];
  message: string;
}

export interface PortfolioListResponse {
  portfolios: PortfolioSummary[];
}

export interface ScoreResponse {
  portfolio_id: string;
  overall_score: number;
  climate_risk: number;
  transition_risk: number;
  physical_risk: number;
  opportunity_score: number;
  top_risks: string[];
  quick_wins: string[];
  sector_breakdown: Record<string, number>;
}

export interface ScenarioRequest {
  portfolio_id: string;
  scenario: string;
  carbon_price_usd?: number;
  revenue_shock_pct?: number;
}

export interface ScenarioResponse {
  portfolio_id: string;
  scenario: string;
  impact_summary: string;
  est_ebitda_impact_pct: number;
  emissions_delta_pct: number;
  hotspots: string[];
}

export interface Scenario {
  carbon_price: number;
  revenue_shock: number;
}

export type Scenarios = Record<string, Scenario>;

export interface CopilotRequest {
  portfolio_id: string;
  question: string;
}

export interface CopilotResponse {
  portfolio_id: string;
  answer: string;
  citations: string[];
}

export interface CopilotStreamRequest {
  question: string;
  portfolio_id?: string;
}

export interface HealthResponse {
  status: string;
  version?: string;
  checks?: {
    database: boolean;
    llm: boolean;
  };
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  assets: Asset[];
}

export interface CreatePortfolioResponse {
  success: boolean;
  portfolio: PortfolioSummary;
  message: string;
}

// Pipeline Data Types
export interface EmissionsFacility {
  facility_id: string;
  facility_name: string | null;
  city: string | null;
  state: string | null;
  sector: string | null;
  reporting_year: number | null;
  total_emissions_mt_co2e: number | null;
}

export interface ClimateObservation {
  location_id: string | null;
  country_code: string | null;
  region: string | null;
  year: number | null;
  month: number | null;
  metric_name: string | null;
  value: number | null;
  unit: string | null;
  scenario: string | null;
  source: string;
}

export interface SectorEmissionsSummary {
  sector: string;
  total_emissions_mt_co2e: number;
  facility_count: number;
  avg_emissions_per_facility: number;
}

export interface PipelineStats {
  total_emissions_records: number;
  total_climate_records: number;
  emissions_by_sector: SectorEmissionsSummary[];
  latest_emissions_year: number | null;
  states_covered: number;
  data_sources: string[];
  last_updated: string | null;
}

export interface PipelineRunInfo {
  run_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  records_extracted: number;
  records_loaded: number;
}

export interface SectorInfo {
  sector: string;
  facility_count: number;
}

// ---------------------------------------------------------------------------
// Eval Framework
// ---------------------------------------------------------------------------

export interface EvalCaseResult {
  case_id: string;
  category: string;
  prompt: string;
  response: string;
  scores: Record<string, number>;
  passed: boolean;
  reasoning: string;
}

export interface EvalRunResponse {
  dataset: string;
  total_cases: number;
  passed: number;
  failed: number;
  pass_rate: number;
  avg_scores: Record<string, number>;
  results: EvalCaseResult[];
  duration_ms: number;
}

export interface EvalRunRequest {
  dataset: string;
  max_cases?: number;
}
