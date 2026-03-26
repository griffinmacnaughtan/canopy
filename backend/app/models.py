from typing import Any

from pydantic import BaseModel, Field, field_validator


class Asset(BaseModel):
    id: str
    name: str
    ticker: str | None = None
    sector: str
    region: str
    revenue_usd_m: float = Field(..., gt=0, description="Annual revenue in USD millions")
    scope1_tco2e: float = Field(..., ge=0, description="Scope 1 emissions in tCO2e")
    scope2_tco2e: float = Field(..., ge=0, description="Scope 2 emissions in tCO2e")
    scope3_tco2e: float = Field(0, ge=0, description="Scope 3 emissions in tCO2e (value chain)")
    green_revenue_pct: float = Field(
        ..., ge=0, le=100, description="Percentage of green revenue (0-100)"
    )
    controversies: int = Field(0, ge=0, le=5, description="ESG controversy score (0-5)")


class Portfolio(BaseModel):
    id: str
    name: str
    description: str | None = None
    assets: list[Asset]


class PortfolioSummary(BaseModel):
    """Summary of a portfolio without asset details."""

    id: str
    name: str
    description: str | None = None
    asset_count: int
    is_sample: bool = False


class PortfolioListResponse(BaseModel):
    """Response listing all available portfolios."""

    portfolios: list[PortfolioSummary]


class ScoreResponse(BaseModel):
    portfolio_id: str
    overall_score: float
    climate_risk: float
    transition_risk: float
    physical_risk: float
    opportunity_score: float
    top_risks: list[str]
    quick_wins: list[str]
    sector_breakdown: dict[str, float]


class ScenarioRequest(BaseModel):
    portfolio_id: str | None = None
    scenario: str
    carbon_price_usd: float | None = Field(None, gt=0)
    revenue_shock_pct: float | None = Field(None, ge=-100, le=100)


class ScenarioResponse(BaseModel):
    portfolio_id: str
    scenario: str
    impact_summary: str
    est_ebitda_impact_pct: float
    emissions_delta_pct: float
    hotspots: list[str]


class CopilotRequest(BaseModel):
    portfolio_id: str | None = None
    question: str = Field(..., min_length=3, max_length=2000)


class CopilotResponse(BaseModel):
    portfolio_id: str
    answer: str
    citations: list[str]
    confidence: float | None = Field(
        None, ge=0, le=1, description="Response confidence score (0-1)"
    )
    sources: list[dict[str, Any]] | None = Field(
        None,
        description="Chunk-level source references from SEC filing retrieval",
    )


class CopilotStreamRequest(BaseModel):
    """Request for streaming copilot endpoint."""

    question: str = Field(..., min_length=3, max_length=2000)
    portfolio_id: str | None = None


class DocumentInfo(BaseModel):
    """Information about an uploaded document."""

    filename: str
    char_count: int


class UploadResponse(BaseModel):
    """Response from document upload."""

    success: bool
    document: DocumentInfo
    message: str


class DocumentListResponse(BaseModel):
    """Response listing all uploaded documents."""

    documents: list[DocumentInfo]
    total_chars: int


class CreatePortfolioRequest(BaseModel):
    """Request to create a custom portfolio."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    assets: list[Asset] = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Portfolio name cannot be blank")
        return v.strip()


class CreatePortfolioResponse(BaseModel):
    """Response after creating a portfolio."""

    success: bool
    portfolio: PortfolioSummary
    message: str


class DeletePortfolioResponse(BaseModel):
    """Response after deleting a portfolio."""

    success: bool
    message: str


# ---------------------------------------------------------------------------
# Portfolio Comparison
# ---------------------------------------------------------------------------


class PortfolioScoreSummary(BaseModel):
    """Compact score summary used in comparisons."""

    portfolio_id: str
    portfolio_name: str
    overall_score: float
    climate_risk: float
    transition_risk: float
    physical_risk: float
    opportunity_score: float
    asset_count: int
    total_emissions_tco2e: float
    avg_green_revenue_pct: float
    sector_breakdown: dict[str, float]


class ComparePortfoliosResponse(BaseModel):
    """Side-by-side comparison of two portfolios."""

    portfolio_a: PortfolioScoreSummary
    portfolio_b: PortfolioScoreSummary
    delta: dict[str, float]  # portfolio_b minus portfolio_a for numeric fields
    recommendation: str


# ---------------------------------------------------------------------------
# Portfolio Export / Report
# ---------------------------------------------------------------------------


class ScenarioImpactItem(BaseModel):
    scenario: str
    est_ebitda_impact_pct: float
    emissions_delta_pct: float
    hotspots: list[str]


class PortfolioExportReport(BaseModel):
    """Comprehensive risk report exported from a portfolio."""

    generated_at: str  # ISO-8601 timestamp
    portfolio_id: str
    portfolio_name: str
    description: str | None
    asset_count: int
    # Scores
    overall_score: float
    climate_risk: float
    transition_risk: float
    physical_risk: float
    opportunity_score: float
    # Narrative
    top_risks: list[str]
    quick_wins: list[str]
    sector_breakdown: dict[str, float]
    # Holdings
    assets: list[dict[str, Any]]
    # Scenarios
    scenario_impacts: list[ScenarioImpactItem]


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------


class CsvImportResponse(BaseModel):
    """Response after importing a portfolio from CSV."""

    success: bool
    portfolio: PortfolioSummary
    rows_imported: int
    rows_skipped: int
    warnings: list[str]
    message: str


# ---------------------------------------------------------------------------
# Agentic AI
# ---------------------------------------------------------------------------


class AgentRequest(BaseModel):
    """Request to the agentic climate analyst."""

    query: str = Field(..., min_length=3, max_length=4000)
    portfolio_id: str | None = None
    max_iterations: int = Field(8, ge=1, le=15)


class AgentStepResponse(BaseModel):
    """A single step in the agent's reasoning trace."""

    thought: str
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    observation: str | None = None


class AgentResponse(BaseModel):
    """Response from the agentic analyst."""

    answer: str
    steps: list[AgentStepResponse]
    tool_calls: int
    iterations: int
    duration_ms: float


# ---------------------------------------------------------------------------
# Eval Framework
# ---------------------------------------------------------------------------


class EvalRunRequest(BaseModel):
    """Request to run the LLM evaluation suite."""

    dataset: str = Field("climate_copilot", description="Dataset name to evaluate")
    max_cases: int | None = Field(None, ge=1, le=100)


class EvalCaseResult(BaseModel):
    """Result of a single eval case."""

    case_id: str
    category: str
    prompt: str
    response: str
    scores: dict[str, float]
    passed: bool
    reasoning: str


class EvalRunResponse(BaseModel):
    """Aggregated results from an eval run."""

    dataset: str
    total_cases: int
    passed: int
    failed: int
    pass_rate: float
    avg_scores: dict[str, float]
    results: list[EvalCaseResult]
    duration_ms: float
