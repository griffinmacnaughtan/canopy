import { describe, it, expect, vi } from "vitest";

/**
 * API client unit tests.
 *
 * These exercise demo-mode fallback logic and the fetchWithTimeout
 * helper without hitting a real backend.
 */

// Force demo mode so every api.* call returns mock data
// (VITE_DEMO_MODE is checked at module load time)
vi.stubEnv("VITE_DEMO_MODE", "true");

// Dynamic import AFTER env is stubbed
const { api, ApiError } = await import("./client");

describe("api — demo mode", () => {
  it("reports demo mode when VITE_DEMO_MODE is set", () => {
    expect(api.isDemoMode()).toBe(true);
  });

  it("health() returns demo status", async () => {
    const h = await api.health();
    expect(h.status).toBe("demo");
  });

  it("getPortfolios() returns a non-empty list", async () => {
    const { portfolios } = await api.getPortfolios();
    expect(portfolios.length).toBeGreaterThan(0);
    expect(portfolios[0]).toHaveProperty("id");
    expect(portfolios[0]).toHaveProperty("name");
  });

  it("getPortfolio() returns a portfolio with assets", async () => {
    const portfolio = await api.getPortfolio();
    expect(portfolio).toHaveProperty("name");
    expect(portfolio.assets.length).toBeGreaterThan(0);
    expect(portfolio.assets[0]).toHaveProperty("name");
  });

  it("getScore() returns numeric scores", async () => {
    const score = await api.getScore();
    expect(score.overall_score).toBeGreaterThanOrEqual(0);
    expect(score.overall_score).toBeLessThanOrEqual(100);
    expect(score).toHaveProperty("climate_risk");
    expect(score).toHaveProperty("transition_risk");
  });

  it("getScenarios() returns scenario definitions keyed by name", async () => {
    const scenarios = await api.getScenarios();
    // Mock data returns scenarios as a keyed object, e.g. { "Net Zero 2050": {...} }
    expect(Object.keys(scenarios).length).toBeGreaterThan(0);
    const first = Object.values(scenarios)[0];
    expect(first.carbon_price).toBeDefined();
  });

  it("runEvals() returns eval results with pass rate", async () => {
    const result = await api.runEvals({ dataset: "standard" });
    expect(result.total_cases).toBeGreaterThan(0);
    expect(result.pass_rate).toBeGreaterThanOrEqual(0);
    expect(result.pass_rate).toBeLessThanOrEqual(1);
    expect(result.results.length).toBe(result.total_cases);
  });

  it("getPipelineStats() returns pipeline statistics", async () => {
    const stats = await api.getPipelineStats();
    expect(stats).toHaveProperty("total_emissions_records");
    expect(stats).toHaveProperty("total_climate_records");
    expect(stats.total_emissions_records).toBeGreaterThan(0);
  });

  it("createPortfolio() returns success", async () => {
    const result = await api.createPortfolio({
      name: "Test Portfolio",
      assets: [
        {
          id: "test-1",
          name: "Apple Inc",
          sector: "Technology",
          region: "North America",
          revenue_usd_m: 383_000,
          scope1_tco2e: 55_000,
          scope2_tco2e: 22_000,
          scope3_tco2e: 25_100_000,
          green_revenue_pct: 0,
          controversies: 1,
        },
      ],
    });
    expect(result.success).toBe(true);
    expect(result.portfolio.name).toBe("Test Portfolio");
  });

  it(
    "streamCopilot() yields text chunks",
    async () => {
      const chunks: string[] = [];
      for await (const chunk of api.streamCopilot("What are the top risks?")) {
        chunks.push(chunk);
      }
      expect(chunks.length).toBeGreaterThan(0);
      // Joined chunks should form a coherent response string
      const full = chunks.join("");
      expect(full.length).toBeGreaterThan(10);
    },
    15_000 // simulateStream yields word-by-word with ~30ms delays
  );

  it("getEmissionsData() returns facility records", async () => {
    const data = await api.getEmissionsData();
    expect(data.length).toBeGreaterThan(0);
    expect(data[0]).toHaveProperty("facility_name");
    expect(data[0]).toHaveProperty("sector");
  });

  it("exportPortfolio() returns a report object", async () => {
    const report = await api.exportPortfolio("demo-portfolio-1");
    expect(report).toHaveProperty("portfolio_name");
    expect(report).toHaveProperty("overall_score");
    expect(report).toHaveProperty("assets");
  });
});

describe("ApiError", () => {
  it("creates error with status code and message", () => {
    const err = new ApiError(404, "Not found");
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe("ApiError");
    expect(err.status).toBe(404);
    expect(err.message).toBe("Not found");
  });

  it("408 timeout error has correct properties", () => {
    const err = new ApiError(408, "Request timed out after 30s");
    expect(err.status).toBe(408);
    expect(err.message).toContain("timed out");
  });
});
