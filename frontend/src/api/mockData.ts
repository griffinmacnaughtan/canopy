/**
 * Mock data for demo mode when backend is unavailable.
 * This allows the frontend to be deployed to GitHub Pages
 * and still demonstrate functionality.
 */

import type {
  Portfolio,
  ScoreResponse,
  ScenarioResponse,
  PipelineStats,
  EmissionsFacility,
  ClimateObservation,
  PipelineRunInfo,
  SectorInfo,
} from "@/types";

export const MOCK_PORTFOLIOS = [
  {
    id: "demo-portfolio-1",
    name: "Climate-Aligned Growth Portfolio",
    description: "Diversified portfolio with focus on climate transition leaders",
    asset_count: 8,
  },
  {
    id: "demo-portfolio-2",
    name: "High Carbon Exposure Portfolio",
    description: "Portfolio with significant fossil fuel exposure for stress testing",
    asset_count: 5,
  },
];

export const MOCK_PORTFOLIO: Portfolio = {
  id: "demo-portfolio-1",
  name: "Climate-Aligned Growth Portfolio",
  description: "Diversified portfolio with focus on climate transition leaders",
  assets: [
    {
      id: "asset-1",
      name: "Solaris Energy Corp",
      sector: "Utilities",
      region: "North America",
      revenue_usd_m: 45000,
      scope1_tco2e: 1200000,
      scope2_tco2e: 400000,
      scope3_tco2e: 5200000,
      green_revenue_pct: 42,
      controversies: 0,
    },
    {
      id: "asset-2",
      name: "TechNova Industries",
      sector: "Information Technology",
      region: "North America",
      revenue_usd_m: 120000,
      scope1_tco2e: 50000,
      scope2_tco2e: 180000,
      scope3_tco2e: 8500000,
      green_revenue_pct: 28,
      controversies: 1,
    },
    {
      id: "asset-3",
      name: "GreenBuild Materials",
      sector: "Materials",
      region: "Europe",
      revenue_usd_m: 18000,
      scope1_tco2e: 850000,
      scope2_tco2e: 220000,
      scope3_tco2e: 12000000,
      green_revenue_pct: 35,
      controversies: 0,
    },
    {
      id: "asset-4",
      name: "Coastal Properties REIT",
      sector: "Real Estate",
      region: "North America",
      revenue_usd_m: 8500,
      scope1_tco2e: 25000,
      scope2_tco2e: 95000,
      scope3_tco2e: 450000,
      green_revenue_pct: 18,
      controversies: 2,
    },
    {
      id: "asset-5",
      name: "Nordic Wind AS",
      sector: "Utilities",
      region: "Europe",
      revenue_usd_m: 6200,
      scope1_tco2e: 8000,
      scope2_tco2e: 12000,
      scope3_tco2e: 100000,
      green_revenue_pct: 92,
      controversies: 0,
    },
    {
      id: "asset-6",
      name: "GlobalTrans Logistics",
      sector: "Industrials",
      region: "Asia Pacific",
      revenue_usd_m: 32000,
      scope1_tco2e: 1800000,
      scope2_tco2e: 350000,
      scope3_tco2e: 45000000,
      green_revenue_pct: 8,
      controversies: 1,
    },
    {
      id: "asset-7",
      name: "Petrovax Energy",
      sector: "Energy",
      region: "North America",
      revenue_usd_m: 95000,
      scope1_tco2e: 4500000,
      scope2_tco2e: 800000,
      scope3_tco2e: 280000000,
      green_revenue_pct: 5,
      controversies: 3,
    },
    {
      id: "asset-8",
      name: "MediHealth Systems",
      sector: "Healthcare",
      region: "Europe",
      revenue_usd_m: 22000,
      scope1_tco2e: 45000,
      scope2_tco2e: 120000,
      scope3_tco2e: 3200000,
      green_revenue_pct: 15,
      controversies: 0,
    },
  ],
};

export const MOCK_SCORE: ScoreResponse = {
  portfolio_id: "demo-portfolio-1",
  overall_score: 67.4,
  climate_risk: 48.2,
  transition_risk: 52.8,
  physical_risk: 41.5,
  opportunity_score: 35.6,
  top_risks: [
    "High exposure to carbon pricing in Energy sector (Petrovax Energy)",
    "Physical risk concentration in coastal real estate assets",
    "GlobalTrans Logistics has above-peer emissions intensity (67.2 tCO2e/$M)",
    "Limited green revenue diversification in Industrials holdings",
  ],
  quick_wins: [
    "Accelerate renewable energy procurement for TechNova data centers",
    "Set portfolio-wide science-based targets with 12-18 month milestones",
    "Engage Petrovax Energy on transition strategy and capex reallocation",
    "Deploy energy efficiency program across logistics and real assets",
  ],
  sector_breakdown: {
    Utilities: 38.5,
    "Information Technology": 22.1,
    Materials: 45.2,
    "Real Estate": 52.8,
    Industrials: 58.4,
    Energy: 78.9,
    Healthcare: 18.3,
  },
};

export const MOCK_SCENARIOS = {
  "Net Zero 2050": {
    carbon_price: 250,
    revenue_shock: -2.5,
  },
  "Delayed Transition": {
    carbon_price: 125,
    revenue_shock: -4.0,
  },
  "Current Policies": {
    carbon_price: 75,
    revenue_shock: -1.0,
  },
};

export const MOCK_SCENARIO_RESULT: ScenarioResponse = {
  portfolio_id: "demo-portfolio-1",
  scenario: "Net Zero 2050",
  impact_summary:
    "Scenario 'Net Zero 2050' applies a $250/tCO2e carbon price and -2.5% revenue shock. Estimated EBITDA impact -4.8% with emissions reduction -10.0%.",
  est_ebitda_impact_pct: -4.8,
  emissions_delta_pct: -10.0,
  hotspots: [
    "Petrovax Energy drives 47.3 tCO2e/$M revenue intensity",
    "GlobalTrans Logistics drives 67.2 tCO2e/$M revenue intensity",
    "GreenBuild Materials drives 59.4 tCO2e/$M revenue intensity",
  ],
};

export const MOCK_COPILOT_RESPONSES: Record<string, string> = {
  default: `## Key Finding

Based on the portfolio analysis, your **highest transition risk exposure** comes from the Energy and Industrials sectors, representing approximately 65% of total portfolio emissions.

## Analysis

- **Petrovax Energy** contributes 47.3 tCO2e per $M revenue, significantly above the sector average
- **GlobalTrans Logistics** shows high emissions intensity at 67.2 tCO2e/$M due to fleet operations
- **Nordic Wind AS** represents a best-in-class opportunity with 92% green revenue

## Recommendations

1. **High Priority**: Engage Petrovax Energy on transition pathway and consider position sizing
2. **Medium Priority**: Support GlobalTrans fleet electrification initiatives
3. **Opportunity**: Consider increasing allocation to Nordic Wind given strong green revenue profile

## Considerations

- Carbon pricing scenarios show -4.8% EBITDA impact under Net Zero 2050
- Physical risk exposure is concentrated in Coastal Properties REIT
- TCFD disclosure readiness varies significantly across holdings`,

  risk: `## Key Finding

The portfolio's **top climate risks** are concentrated in two areas: **transition risk** from high-carbon assets and **physical risk** from coastal real estate exposure.

## Analysis

**Transition Risks:**
- Petrovax Energy faces stranded asset risk with $95B revenue tied to fossil fuels
- Carbon pricing exposure: At $250/tCO2e, the portfolio faces ~$2.1B in annual carbon costs
- Regulatory risk: EU CSRD and SEC climate rules require enhanced disclosure by 2026

**Physical Risks:**
- Coastal Properties REIT has 40% of assets in flood-prone zones
- Climate models project 15-25% increase in extreme weather events by 2040

## Recommendations

1. Conduct asset-level physical risk assessment for Coastal Properties
2. Develop transition engagement strategy for Petrovax Energy
3. Set internal carbon price shadow pricing for investment decisions

## Considerations

- Insurance costs for physical risk mitigation are rising 8-12% annually
- Transition timeline depends heavily on policy certainty`,

  opportunity: `## Key Finding

Your portfolio has **significant green growth potential**, with Nordic Wind AS and Solaris Energy Corp positioned to capture the $4.5 trillion annual clean energy investment opportunity.

## Analysis

**Green Revenue Leaders:**
- Nordic Wind AS: 92% green revenue, positioned for European offshore wind expansion
- Solaris Energy Corp: 42% green revenue, investing in grid modernization
- GreenBuild Materials: 35% green revenue from sustainable construction materials

**Growth Catalysts:**
- IRA and EU Green Deal subsidies favor clean energy holdings
- Corporate PPA demand growing 25% YoY
- Green building codes driving Materials sector opportunity

## Recommendations

1. **Increase allocation** to Nordic Wind given strong market position
2. **Monitor** Solaris Energy's grid storage investments
3. **Engage** TechNova on renewable energy procurement (currently 28% green)

## Considerations

- Green revenue accounting standards are evolving (EU Taxonomy alignment)
- Some "green" classifications may face regulatory scrutiny`,
};

/**
 * Get a mock copilot response based on the question.
 * Adds variation to make responses feel more dynamic.
 */
export function getMockCopilotResponse(question: string): string {
  const q = question.toLowerCase();

  // Select base response
  let baseResponse: string;
  if (q.includes("risk") && !q.includes("opportunity")) {
    baseResponse = MOCK_COPILOT_RESPONSES.risk;
  } else if (q.includes("opportunity") || q.includes("upside") || q.includes("green")) {
    baseResponse = MOCK_COPILOT_RESPONSES.opportunity;
  } else {
    baseResponse = MOCK_COPILOT_RESPONSES.default;
  }

  // Add dynamic intro based on question to make it feel responsive
  const intros = [
    `Based on your question about "${question.slice(0, 50)}${question.length > 50 ? '...' : ''}", here's my analysis:\n\n`,
    `Analyzing your portfolio in the context of "${question.slice(0, 40)}${question.length > 40 ? '...' : ''}":\n\n`,
    `Looking at the data to address your query:\n\n`,
  ];

  const randomIntro = intros[Math.floor(Math.random() * intros.length)];

  // Add timestamp-based variation to recommendations
  const timestamp = new Date().toLocaleTimeString();
  const footer = `\n\n---\n*Analysis generated at ${timestamp} using demo portfolio data.*`;

  return randomIntro + baseResponse + footer;
}

/**
 * Simulate streaming by yielding characters with delays.
 */
export async function* simulateStream(text: string): AsyncGenerator<string> {
  const words = text.split(" ");
  for (let i = 0; i < words.length; i++) {
    // Yield word with space
    yield words[i] + (i < words.length - 1 ? " " : "");
    // Small delay to simulate streaming
    await new Promise((resolve) => setTimeout(resolve, 20 + Math.random() * 30));
  }
}

// Pipeline Mock Data
export const MOCK_PIPELINE_STATS: PipelineStats = {
  total_emissions_records: 8547,
  total_climate_records: 12834,
  emissions_by_sector: [
    { sector: "Power Plants", total_emissions_mt_co2e: 1245000000, facility_count: 1823, avg_emissions_per_facility: 682500 },
    { sector: "Petroleum and Natural Gas Systems", total_emissions_mt_co2e: 890000000, facility_count: 2156, avg_emissions_per_facility: 412800 },
    { sector: "Refineries", total_emissions_mt_co2e: 178000000, facility_count: 142, avg_emissions_per_facility: 1253521 },
    { sector: "Chemicals", total_emissions_mt_co2e: 156000000, facility_count: 456, avg_emissions_per_facility: 342105 },
    { sector: "Iron and Steel", total_emissions_mt_co2e: 98000000, facility_count: 112, avg_emissions_per_facility: 875000 },
  ],
  latest_emissions_year: 2023,
  states_covered: 50,
  data_sources: ["EPA GHGRP", "NOAA Climate Data Online", "World Bank Climate"],
  last_updated: new Date().toISOString(),
};

export const MOCK_EMISSIONS_DATA: EmissionsFacility[] = [
  { facility_id: "1001", facility_name: "Gulf Coast Power Station", city: "Houston", state: "TX", sector: "Power Plants", reporting_year: 2023, total_emissions_mt_co2e: 8542000 },
  { facility_id: "1002", facility_name: "Midwest Energy Center", city: "Chicago", state: "IL", sector: "Power Plants", reporting_year: 2023, total_emissions_mt_co2e: 6234000 },
  { facility_id: "1003", facility_name: "Bayway Refinery", city: "Elizabeth", state: "NJ", sector: "Refineries", reporting_year: 2023, total_emissions_mt_co2e: 4521000 },
  { facility_id: "1004", facility_name: "Marcellus Gas Processing", city: "Pittsburgh", state: "PA", sector: "Petroleum and Natural Gas Systems", reporting_year: 2023, total_emissions_mt_co2e: 3890000 },
  { facility_id: "1005", facility_name: "Great Lakes Steel", city: "Detroit", state: "MI", sector: "Iron and Steel", reporting_year: 2023, total_emissions_mt_co2e: 2156000 },
  { facility_id: "1006", facility_name: "Southwest Chemical Complex", city: "Phoenix", state: "AZ", sector: "Chemicals", reporting_year: 2023, total_emissions_mt_co2e: 1890000 },
  { facility_id: "1007", facility_name: "Pacific Cement Works", city: "Los Angeles", state: "CA", sector: "Cement", reporting_year: 2023, total_emissions_mt_co2e: 1456000 },
  { facility_id: "1008", facility_name: "Appalachian Power Plant", city: "Charleston", state: "WV", sector: "Power Plants", reporting_year: 2023, total_emissions_mt_co2e: 5678000 },
];

export const MOCK_CLIMATE_DATA: ClimateObservation[] = [
  { location_id: "US-TX", country_code: "US", region: "South", year: 2024, month: 1, metric_name: "Temperature Anomaly", value: 1.2, unit: "°C", scenario: null, source: "NOAA CDO" },
  { location_id: "US-CA", country_code: "US", region: "West", year: 2024, month: 1, metric_name: "Temperature Anomaly", value: 0.8, unit: "°C", scenario: null, source: "NOAA CDO" },
  { location_id: "US-NY", country_code: "US", region: "Northeast", year: 2024, month: 1, metric_name: "Temperature Anomaly", value: 1.5, unit: "°C", scenario: null, source: "NOAA CDO" },
  { location_id: "US", country_code: "US", region: "National", year: 2050, month: null, metric_name: "Projected Temperature Rise", value: 2.4, unit: "°C", scenario: "RCP4.5", source: "World Bank Climate" },
  { location_id: "US", country_code: "US", region: "National", year: 2050, month: null, metric_name: "Projected Temperature Rise", value: 3.8, unit: "°C", scenario: "RCP8.5", source: "World Bank Climate" },
  { location_id: "US", country_code: "US", region: "National", year: 2100, month: null, metric_name: "Projected Temperature Rise", value: 3.2, unit: "°C", scenario: "RCP4.5", source: "World Bank Climate" },
];

export const MOCK_PIPELINE_RUNS: PipelineRunInfo[] = [
  { run_id: "20240301_120000", status: "success", started_at: "2024-03-01T12:00:00Z", completed_at: "2024-03-01T12:15:32Z", records_extracted: 12500, records_loaded: 12450 },
  { run_id: "20240228_120000", status: "success", started_at: "2024-02-28T12:00:00Z", completed_at: "2024-02-28T12:18:45Z", records_extracted: 11800, records_loaded: 11750 },
  { run_id: "20240227_120000", status: "partial", started_at: "2024-02-27T12:00:00Z", completed_at: "2024-02-27T12:22:10Z", records_extracted: 10500, records_loaded: 9800 },
];

export const MOCK_SECTORS: SectorInfo[] = [
  { sector: "Power Plants", facility_count: 1823 },
  { sector: "Petroleum and Natural Gas Systems", facility_count: 2156 },
  { sector: "Refineries", facility_count: 142 },
  { sector: "Chemicals", facility_count: 456 },
  { sector: "Iron and Steel", facility_count: 112 },
  { sector: "Cement", facility_count: 89 },
  { sector: "Pulp and Paper", facility_count: 234 },
  { sector: "Glass", facility_count: 67 },
];
