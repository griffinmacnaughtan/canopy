import type {
  Portfolio,
  ScoreResponse,
  Scenarios,
  ScenarioRequest,
  ScenarioResponse,
  CopilotRequest,
  CopilotResponse,
  Asset,
  HealthResponse,
  UploadResponse,
  DocumentListResponse,
  DeleteDocumentsResponse,
  PortfolioListResponse,
  CreatePortfolioRequest,
  CreatePortfolioResponse,
  PipelineStats,
  EmissionsFacility,
  ClimateObservation,
  PipelineRunInfo,
  SectorInfo,
} from "@/types";
import {
  MOCK_PORTFOLIOS,
  MOCK_PORTFOLIO,
  MOCK_SCORE,
  MOCK_SCENARIOS,
  MOCK_SCENARIO_RESULT,
  getMockCopilotResponse,
  simulateStream,
  MOCK_PIPELINE_STATS,
  MOCK_EMISSIONS_DATA,
  MOCK_CLIMATE_DATA,
  MOCK_PIPELINE_RUNS,
  MOCK_SECTORS,
} from "./mockData";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Check if we're in demo mode (no backend)
const isDemoMode = (): boolean => {
  return (
    import.meta.env.VITE_DEMO_MODE === "true" ||
    !API_BASE ||
    API_BASE === ""
  );
};

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text().catch(() => "Unknown error");
    throw new ApiError(response.status, message);
  }
  return response.json();
}

export const api = {
  // Check if in demo mode
  isDemoMode,

  // Health checks
  async health(): Promise<HealthResponse> {
    if (isDemoMode()) {
      return { status: "demo", version: "demo" };
    }
    const response = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthResponse>(response);
  },

  async healthReady(): Promise<HealthResponse> {
    if (isDemoMode()) {
      return { status: "demo", checks: { database: true, llm: true } };
    }
    const response = await fetch(`${API_BASE}/health/ready`);
    return handleResponse<HealthResponse>(response);
  },

  // Portfolios list
  async getPortfolios(): Promise<PortfolioListResponse> {
    if (isDemoMode()) {
      return { portfolios: MOCK_PORTFOLIOS };
    }
    const response = await fetch(`${API_BASE}/portfolios`);
    return handleResponse<PortfolioListResponse>(response);
  },

  // Create portfolio
  async createPortfolio(request: CreatePortfolioRequest): Promise<CreatePortfolioResponse> {
    if (isDemoMode()) {
      return {
        success: true,
        portfolio: {
          id: "demo-new",
          name: request.name,
          description: request.description || "",
          asset_count: request.assets.length,
        },
        message: "Demo mode: Portfolio created (not persisted)",
      };
    }
    const response = await fetch(`${API_BASE}/portfolios`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleResponse<CreatePortfolioResponse>(response);
  },

  // Assets
  async getAssets(portfolioId?: string): Promise<Asset[]> {
    if (isDemoMode()) {
      return MOCK_PORTFOLIO.assets;
    }
    const url = portfolioId
      ? `${API_BASE}/assets?portfolio_id=${portfolioId}`
      : `${API_BASE}/assets`;
    const response = await fetch(url);
    return handleResponse<Asset[]>(response);
  },

  // Portfolio
  async getPortfolio(portfolioId?: string): Promise<Portfolio> {
    if (isDemoMode()) {
      return MOCK_PORTFOLIO;
    }
    const url = portfolioId
      ? `${API_BASE}/portfolio?portfolio_id=${portfolioId}`
      : `${API_BASE}/portfolio`;
    const response = await fetch(url);
    return handleResponse<Portfolio>(response);
  },

  // Scoring
  async getScore(portfolioId?: string): Promise<ScoreResponse> {
    if (isDemoMode()) {
      return MOCK_SCORE;
    }
    const url = portfolioId
      ? `${API_BASE}/score?portfolio_id=${portfolioId}`
      : `${API_BASE}/score`;
    const response = await fetch(url);
    return handleResponse<ScoreResponse>(response);
  },

  // Scenarios
  async getScenarios(): Promise<Scenarios> {
    if (isDemoMode()) {
      return MOCK_SCENARIOS;
    }
    const response = await fetch(`${API_BASE}/scenarios`);
    return handleResponse<Scenarios>(response);
  },

  async runScenario(request: ScenarioRequest): Promise<ScenarioResponse> {
    if (isDemoMode()) {
      return {
        ...MOCK_SCENARIO_RESULT,
        scenario: request.scenario,
      };
    }
    const response = await fetch(`${API_BASE}/scenario`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleResponse<ScenarioResponse>(response);
  },

  // Copilot (non-streaming)
  async askCopilot(request: CopilotRequest): Promise<CopilotResponse> {
    if (isDemoMode()) {
      return {
        portfolio_id: "demo-portfolio-1",
        answer: getMockCopilotResponse(request.question),
        citations: ["Demo portfolio data", "NGFS scenarios"],
      };
    }
    const response = await fetch(`${API_BASE}/copilot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleResponse<CopilotResponse>(response);
  },

  // Copilot streaming
  async *streamCopilot(
    question: string,
    portfolioId?: string
  ): AsyncGenerator<string, void, unknown> {
    // In demo mode, simulate streaming with mock data
    if (isDemoMode()) {
      const response = getMockCopilotResponse(question);
      yield* simulateStream(response);
      return;
    }

    const response = await fetch(`${API_BASE}/copilot/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, portfolio_id: portfolioId }),
    });

    if (!response.ok) {
      throw new ApiError(response.status, "Failed to start copilot stream");
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Keep the last potentially incomplete line in the buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              return;
            }
            yield data;
          }
        }
      }

      // Process any remaining buffer
      if (buffer.startsWith("data: ")) {
        const data = buffer.slice(6);
        if (data && data !== "[DONE]") {
          yield data;
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  // Document upload
  async uploadPDF(file: File): Promise<UploadResponse> {
    if (isDemoMode()) {
      return {
        success: true,
        document: { filename: file.name, char_count: 5000 },
        message: "Demo mode: Document uploaded (not processed)",
      };
    }
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse<UploadResponse>(response);
  },

  async getDocuments(): Promise<DocumentListResponse> {
    if (isDemoMode()) {
      return { documents: [], total_chars: 0 };
    }
    const response = await fetch(`${API_BASE}/documents`);
    return handleResponse<DocumentListResponse>(response);
  },

  async clearDocuments(): Promise<DeleteDocumentsResponse> {
    if (isDemoMode()) {
      return { success: true, cleared: 0 };
    }
    const response = await fetch(`${API_BASE}/documents`, {
      method: "DELETE",
    });
    return handleResponse<DeleteDocumentsResponse>(response);
  },

  // Pipeline Data API
  async getPipelineStats(): Promise<PipelineStats> {
    if (isDemoMode()) {
      return MOCK_PIPELINE_STATS;
    }
    const response = await fetch(`${API_BASE}/pipeline/stats`);
    return handleResponse<PipelineStats>(response);
  },

  async getEmissionsData(params?: {
    sector?: string;
    state?: string;
    year?: number;
    limit?: number;
  }): Promise<EmissionsFacility[]> {
    if (isDemoMode()) {
      let data = [...MOCK_EMISSIONS_DATA];
      if (params?.sector) {
        data = data.filter((d) => d.sector === params.sector);
      }
      if (params?.state) {
        data = data.filter((d) => d.state === params.state);
      }
      return data.slice(0, params?.limit || 50);
    }
    const searchParams = new URLSearchParams();
    if (params?.sector) searchParams.set("sector", params.sector);
    if (params?.state) searchParams.set("state", params.state);
    if (params?.year) searchParams.set("year", params.year.toString());
    if (params?.limit) searchParams.set("limit", params.limit.toString());

    const url = `${API_BASE}/pipeline/emissions${searchParams.toString() ? `?${searchParams}` : ""}`;
    const response = await fetch(url);
    return handleResponse<EmissionsFacility[]>(response);
  },

  async getTopEmitters(limit: number = 10): Promise<EmissionsFacility[]> {
    if (isDemoMode()) {
      return MOCK_EMISSIONS_DATA.sort(
        (a, b) => (b.total_emissions_mt_co2e || 0) - (a.total_emissions_mt_co2e || 0)
      ).slice(0, limit);
    }
    const response = await fetch(`${API_BASE}/pipeline/emissions/top-emitters?limit=${limit}`);
    return handleResponse<EmissionsFacility[]>(response);
  },

  async getClimateData(params?: {
    country?: string;
    metric?: string;
    scenario?: string;
    limit?: number;
  }): Promise<ClimateObservation[]> {
    if (isDemoMode()) {
      let data = [...MOCK_CLIMATE_DATA];
      if (params?.scenario) {
        data = data.filter((d) => d.scenario === params.scenario);
      }
      return data.slice(0, params?.limit || 50);
    }
    const searchParams = new URLSearchParams();
    if (params?.country) searchParams.set("country", params.country);
    if (params?.metric) searchParams.set("metric", params.metric);
    if (params?.scenario) searchParams.set("scenario", params.scenario);
    if (params?.limit) searchParams.set("limit", params.limit.toString());

    const url = `${API_BASE}/pipeline/climate${searchParams.toString() ? `?${searchParams}` : ""}`;
    const response = await fetch(url);
    return handleResponse<ClimateObservation[]>(response);
  },

  async getPipelineRuns(limit: number = 10): Promise<PipelineRunInfo[]> {
    if (isDemoMode()) {
      return MOCK_PIPELINE_RUNS.slice(0, limit);
    }
    const response = await fetch(`${API_BASE}/pipeline/runs?limit=${limit}`);
    return handleResponse<PipelineRunInfo[]>(response);
  },

  async getSectors(): Promise<SectorInfo[]> {
    if (isDemoMode()) {
      return MOCK_SECTORS;
    }
    const response = await fetch(`${API_BASE}/pipeline/sectors`);
    return handleResponse<SectorInfo[]>(response);
  },
};

export { ApiError };
